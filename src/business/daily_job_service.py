import threading
from datetime import datetime, timedelta

from business.rule_service import RuleService
from config import now
from data.repositories import CirculationRepository, NotificationRepository
from models import BorrowRecord


class DailyJobService:
    def __init__(self, circulation: CirculationRepository,
                 notifications: NotificationRepository,
                 rules: RuleService) -> None:
        self.circulation = circulation
        self.notifications = notifications
        self.rules = rules

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
                        (copy_id, expire.isoformat(sep=" "), nxt.reservation_id))
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

        return {
            "marked_overdue": marked_overdue,
            "due_soon_notified": due_soon,
            "expired_holds": expired_holds,
            "promoted_holds": promoted_holds,
            "pending_sent": pending_sent,
        }

    def start_scheduler(self) -> threading.Thread:
        stop = threading.Event()

        def _loop() -> None:
            while True:
                current = now()
                midnight = (current + timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0)
                if stop.wait(max(1.0, (midnight - current).total_seconds())):
                    break
                self.run()

        thread = threading.Thread(target=_loop, daemon=True)
        thread.start()
        return thread
