import sqlite3
import threading
from datetime import datetime, timedelta

from business.audit_service import AuditService
from business.backup_service import BackupService
from business.rule_service import RuleService
from common.exceptions import ValidationError
from config import now
from data.repositories import CirculationRepository, NotificationRepository
from models import BorrowRecord


class DailyJobService:
    def __init__(self, circulation: CirculationRepository,
                 notifications: NotificationRepository,
                 rules: RuleService,
                 backups: BackupService | None = None,
                 audit: AuditService | None = None) -> None:
        self.circulation = circulation
        self.notifications = notifications
        self.rules = rules
        self.backups = backups
        self.audit = audit

    def run(self, at: datetime | None = None) -> dict[str, int]:
        ts = at or now()
        ts_str = ts.isoformat(sep=" ")
        rules = self.rules.current_rules()
        marked_overdue = 0
        due_soon = 0
        expired_holds = 0
        promoted_holds = 0

        with self.circulation.db.transaction() as conn:
            overdue_rows = conn.execute(
                "SELECT br.borrow_id, br.reader_id, b.title AS book_title "
                "FROM borrow_records br "
                "JOIN book_copies c ON c.copy_id = br.copy_id "
                "JOIN books b ON b.book_id = c.book_id "
                "WHERE br.status = 'BORROWED' AND br.return_date IS NULL "
                "AND br.due_date < ?", (ts_str,)).fetchall()
            for row in overdue_rows:
                conn.execute(
                    "UPDATE borrow_records SET status = 'OVERDUE' "
                    "WHERE borrow_id = ?", (row["borrow_id"],))
                marked_overdue += 1
                msg = (f"{row['book_title']} is overdue. "
                       "Please return it to the library desk.")
                if not self.notifications.exists_message(
                        row["reader_id"], msg, conn=conn):
                    self.notifications.create_sent(
                        row["reader_id"], msg, ts, conn=conn)

            upcoming = conn.execute(
                "SELECT br.*, b.title AS book_title "
                "FROM borrow_records br "
                "JOIN book_copies c ON c.copy_id = br.copy_id "
                "JOIN books b ON b.book_id = c.book_id "
                "WHERE br.status = 'BORROWED' AND br.return_date IS NULL "
                "AND br.due_date >= ?", (ts_str,)).fetchall()
            for row in upcoming:
                rec = BorrowRecord.from_row(row)
                days_left = (rec.due_date.date() - ts.date()).days
                if 0 <= days_left <= 2:
                    msg = (f"{row['book_title']} is due on "
                           f"{rec.due_date:%d/%m/%Y}. "
                           "Please return or renew it soon.")
                    if not self.notifications.exists_message(
                            rec.reader_id, msg, conn=conn):
                        self.notifications.create_sent(
                            rec.reader_id, msg, ts, conn=conn)
                        due_soon += 1

            expired = conn.execute(
                "SELECT r.reservation_id, r.book_id, r.copy_id, "
                "b.title AS book_title "
                "FROM reservations r "
                "JOIN books b ON b.book_id = r.book_id "
                "WHERE r.status = 'READY' AND r.expire_date IS NOT NULL "
                "AND r.expire_date < ?", (ts_str,)).fetchall()
            for row in expired:
                conn.execute(
                    "UPDATE reservations SET status = 'CANCELED' "
                    "WHERE reservation_id = ?", (row["reservation_id"],))
                expired_holds += 1
                copy_id = row["copy_id"]
                if copy_id is None:
                    continue
                nxt = self.circulation.next_waiting(row["book_id"], conn)
                if nxt is not None:
                    expire = ts + timedelta(days=rules.hold_days)
                    conn.execute(
                        "UPDATE reservations "
                        "SET status = 'READY', copy_id = ?, expire_date = ? "
                        "WHERE reservation_id = ?",
                        (copy_id, expire.isoformat(sep=" "),
                         nxt.reservation_id))
                    self.notifications.create_sent(
                        nxt.reader_id,
                        f"{row['book_title']} is ready for pickup. Please "
                        f"collect it within {rules.hold_days} days.",
                        ts, conn=conn)
                    promoted_holds += 1
                else:
                    conn.execute(
                        "UPDATE book_copies SET status = 'AVAILABLE' "
                        "WHERE copy_id = ? AND status = 'RESERVED'", (copy_id,))

            pending_sent = self.notifications.send_pending(ts, conn=conn)

        backups_created, backups_copied = self._run_daily_backup()

        return {
            "marked_overdue": marked_overdue,
            "due_soon_notified": due_soon,
            "expired_holds": expired_holds,
            "promoted_holds": promoted_holds,
            "pending_sent": pending_sent,
            "backups_created": backups_created,
            "backups_copied": backups_copied,
        }

    def run_safely(self, at: datetime | None = None) -> dict | None:
        """Run the job but never stop the scheduler (NFR-REL-06)."""
        try:
            return self.run(at)
        except Exception as error:  # noqa: BLE001 - keep the thread alive
            self._log("DAILY_JOB_FAILED", f"Daily job failed: {error}")
            return None

    def _run_daily_backup(self) -> tuple[int, int]:
        """One backup per day, also kept in a second folder (NFR-REL-04)."""
        if self.backups is None:
            return 0, 0
        created = 0
        copied = 0
        try:
            name = self.backups.daily_backup_for(self.backups.clock().date())
            if name is None:  # a restart on the same day adds no backup
                name = self.backups.create(label="daily").name
                created = 1
                self.backups.prune_daily(self.backups.backup_dir)
        except (OSError, sqlite3.Error) as error:
            self._log("DAILY_BACKUP_FAILED", f"Daily backup failed: {error}")
            return created, copied

        copy_dir = self.backups.copy_dir
        if copy_dir is not None and not (copy_dir / name).is_file():
            try:
                self.backups.copy_backup(name)
                copied = 1
                self.backups.prune_daily(copy_dir)
            except (OSError, ValidationError) as error:
                self._log("DAILY_BACKUP_COPY_FAILED",
                          f"Daily backup copy failed: {error}")
        return created, copied

    def _log(self, action: str, details: str) -> None:
        if self.audit is None:
            return
        try:
            self.audit.record(None, action, details)
        except sqlite3.Error:
            pass  # the database itself is failing; nothing more to do

    def start_scheduler(self) -> threading.Thread:
        stop = threading.Event()

        def _loop() -> None:
            while True:
                current = now()
                midnight = (current + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0)
                if stop.wait(max(1.0, (midnight - current).total_seconds())):
                    break
                self.run_safely()

        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()
        return thread
