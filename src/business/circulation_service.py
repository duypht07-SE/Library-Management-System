from datetime import datetime, timedelta

from business.fine_service import FineService
from business.rule_service import RuleService
from common.exceptions import ValidationError
from config import now
from data.repositories import (CirculationRepository, NotificationRepository)
from models import (BookCopy, BorrowRecord, CopyCondition, CopyStatus, Fine,
                    Librarian, Notification, Reader, Reservation,
                    ReservationStatus, Role, UserFactory, UserStatus)


class CirculationService:
    def __init__(self, circulation: CirculationRepository,
                 rules: RuleService, fines: FineService,
                 notifications: NotificationRepository) -> None:
        self.circulation = circulation
        self.rules = rules
        self.fines = fines
        self.notifications = notifications

    def reader_status_for_book(self, reader: Reader, book_id: int) -> str:
        """'borrowing', 'reserved', or '' for the Reserve Book button."""
        with self.circulation.db.transaction() as conn:
            if self.circulation.is_borrowing_book(reader.user_id, book_id,
                                                  conn):
                return "borrowing"
            if self.circulation.has_active_reservation(reader.user_id,
                                                       book_id, conn):
                return "reserved"
        return ""

    def open_loans(self) -> list[dict]:
        return self.circulation.find_open_loans()

    def notifications_for_reader(self, reader: Reader) -> list[Notification]:
        if reader.user_id is None:
            return []
        return self.notifications.find_for_reader(reader.user_id)

    def view_borrow_history(self, reader: Reader) -> dict:
        rules = self.rules.current_rules()
        if reader.user_id is None:
            return {"active_loans": [], "returned_loans": [],
                    "reservations": [], "fines": [], "notifications": [],
                    "rules": rules}
        records = reader.view_borrow_history(
            self.circulation.find_borrow_records(reader.user_id))
        by_id = {r.borrow_id: r for r in records}
        at = now()
        active_loans, returned_loans = [], []
        for row in self.circulation.find_loans_for_reader(reader.user_id):
            rec = by_id.get(row["borrow_id"])
            if row["status"] == "RETURNED":
                returned_loans.append(row)
            else:
                row["can_renew"] = (
                    reader.is_active
                    and rec is not None
                    and row["status"] == "BORROWED"
                    and not rec.is_overdue(at)
                    and row["renew_count"] < rules.max_renew
                    and row["waiting_count"] == 0
                )
                active_loans.append(row)
        return {
            "active_loans": active_loans,
            "returned_loans": returned_loans,
            "reservations": self.circulation.find_reservations_for_reader(
                reader.user_id),
            "fines": self.fines.view_fines(reader),
            "notifications": self.notifications_for_reader(reader),
            "rules": rules,
        }

    def check_out(self, librarian: Librarian, card_code: str, barcode: str,
                  at: datetime | None = None) -> BorrowRecord:
        card = (card_code or "").strip()
        code = (barcode or "").strip()
        if not card:
            raise ValidationError("Reader card code is required.")
        if not code:
            raise ValidationError("Book copy barcode is required.")
        ts = at or now()
        rules = self.rules.current_rules()

        with self.circulation.db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE lower(card_code) = lower(?) "
                "AND role = ?", (card, Role.READER.value)).fetchone()
            if row is None:
                raise ValidationError("Reader card was not found.")
            reader = UserFactory.from_row(row)
            if reader.status != UserStatus.ACTIVE:
                raise ValidationError("Reader card is not active.")
            if self.circulation.has_overdue_loan(reader.user_id, ts, conn):
                raise ValidationError("Reader has overdue books.")
            if self.circulation.has_unpaid_fine(reader.user_id, conn):
                raise ValidationError("Reader has unpaid fines.")
            open_loans = self.circulation.count_open_loans(
                reader.user_id, conn)
            if open_loans >= rules.max_books:
                raise ValidationError(
                    f"Reader reached the limit of {rules.max_books} books.")

            copy = self.circulation.find_copy_by_barcode(code, conn)
            if copy is None:
                raise ValidationError("Book copy was not found.")

            hold = None
            if copy.status == CopyStatus.RESERVED:
                hold = self.circulation.find_ready_for_copy(copy.copy_id, conn)
                if hold is None or hold.reader_id != reader.user_id:
                    raise ValidationError(
                        "This copy is reserved for another reader.")
                if hold.is_hold_expired(ts):
                    raise ValidationError("This reservation hold has expired.")
            elif copy.status != CopyStatus.AVAILABLE:
                raise ValidationError("This copy is not available.")

            try:
                record = librarian.check_out(
                    copy, reader.user_id, ts, rules.max_days)
            except ValueError as err:
                raise ValidationError(str(err)) from err

            cur = conn.execute(
                "INSERT INTO borrow_records "
                "(reader_id, copy_id, librarian_id, borrow_date, due_date, "
                "renew_count, status) VALUES (?, ?, ?, ?, ?, 0, 'BORROWED')",
                (record.reader_id, record.copy_id, record.librarian_id,
                 record.borrow_date.isoformat(sep=" "),
                 record.due_date.isoformat(sep=" ")))
            record.borrow_id = int(cur.lastrowid)
            conn.execute("UPDATE book_copies SET status = ? WHERE copy_id = ?",
                         (copy.status.value, copy.copy_id))
            if hold is not None:
                conn.execute(
                    "UPDATE reservations SET status = 'COMPLETED' "
                    "WHERE reservation_id = ?", (hold.reservation_id,))
            return record

    def check_in(self, librarian: Librarian, condition: str,
                 barcode: str = "", borrow_id: int | None = None,
                 damage_amount: int | None = None,
                 at: datetime | None = None) -> tuple[BorrowRecord, list[Fine]]:
        cond = (condition or "INTACT").strip().upper()
        if cond not in {"INTACT", "DAMAGED", "LOST"}:
            raise ValidationError("Choose a valid book condition.")
        if (cond in {"DAMAGED", "LOST"}
                and (not damage_amount or damage_amount < 1)):
            raise ValidationError(
                "Enter a fine amount greater than 0 VND for a damaged or "
                "lost book.")
        code = (barcode or "").strip()
        if borrow_id is None and not code:
            raise ValidationError("Enter a barcode or choose an active loan.")

        ts = at or now()
        rules = self.rules.current_rules()

        with self.circulation.db.transaction() as conn:
            row = self.circulation.find_open_loan(conn, code, borrow_id)
            if row is None:
                raise ValidationError("Open borrowing record was not found.")
            record = BorrowRecord.from_row(row)
            copy = BookCopy(
                row["copy_id"], row["book_id"], row["barcode"],
                row["shelf_location"], CopyStatus(row["copy_status"]),
                CopyCondition(row["copy_condition"]))
            title = row["book_title"]

            waiting = (self.circulation.next_waiting(copy.book_id, conn)
                       if cond == "INTACT" else None)
            try:
                librarian.check_in(copy, record, cond, ts, waiting is not None)
            except ValueError as err:
                raise ValidationError(str(err)) from err

            conn.execute(
                "UPDATE borrow_records "
                "SET return_date = ?, return_condition = ?, "
                "status = 'RETURNED' "
                "WHERE borrow_id = ?",
                (record.return_date.isoformat(sep=" "),
                 record.return_condition.value, record.borrow_id))
            conn.execute(
                "UPDATE book_copies SET status = ?, copy_condition = ? "
                "WHERE copy_id = ?",
                (copy.status.value, copy.copy_condition.value, copy.copy_id))

            if waiting is not None:
                expire = ts + timedelta(days=rules.hold_days)
                conn.execute(
                    "UPDATE reservations "
                    "SET status = 'READY', copy_id = ?, expire_date = ? "
                    "WHERE reservation_id = ?",
                    (copy.copy_id, expire.isoformat(sep=" "),
                     waiting.reservation_id))
                self.notifications.create_sent(
                    waiting.reader_id,
                    f"{title} is ready for pickup. Please collect it within "
                    f"{rules.hold_days} days.", ts, conn=conn)
            elif cond in {"DAMAGED", "LOST"}:
                usable = conn.execute(
                    "SELECT COUNT(*) FROM book_copies "
                    "WHERE book_id = ? AND status != 'CANCELED'",
                    (copy.book_id,)).fetchone()[0]
                if usable == 0:
                    readers = [r[0] for r in conn.execute(
                        "SELECT reader_id FROM reservations "
                        "WHERE book_id = ? AND status = 'WAITING'",
                        (copy.book_id,)).fetchall()]
                    conn.execute(
                        "UPDATE reservations SET status = 'CANCELED' "
                        "WHERE book_id = ? AND status = 'WAITING'",
                        (copy.book_id,))
                    for reader_id in readers:
                        self.notifications.create_sent(
                            reader_id,
                            f"Your reservation for {title} was canceled "
                            "because no usable copy remains.", ts, conn=conn)

            created = self.fines.create_return_fines(
                record.borrow_id, record.days_late(ts), rules.daily_fine,
                cond, damage_amount, conn=conn)
            return record, created

    def reserve_book(self, reader: Reader, book_id: int,
                     at: datetime | None = None) -> Reservation:
        ts = at or now()
        with self.circulation.db.transaction() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND role = ?",
                (reader.user_id, Role.READER.value)).fetchone()
            if row is None:
                raise ValidationError("Reader account was not found.")
            current = UserFactory.from_row(row)
            book = self.circulation.find_book_with_copies(book_id, conn)
            if book is None:
                raise ValidationError("Book was not found.")
            try:
                res = current.reserve_book(book, ts)
            except ValueError as err:
                raise ValidationError(str(err)) from err
            if self.circulation.has_active_reservation(
                    current.user_id, book_id, conn):
                raise ValidationError(
                    "You already have an active reservation for this book.")
            if self.circulation.is_borrowing_book(
                    current.user_id, book_id, conn):
                raise ValidationError(
                    "You are already borrowing this book.")
            cur = conn.execute(
                "INSERT INTO reservations "
                "(reader_id, book_id, copy_id, reserve_date, expire_date,"
                " status) VALUES (?, ?, NULL, ?, NULL, 'WAITING')",
                (res.reader_id, res.book_id,
                 res.reserve_date.isoformat(sep=" ")))
            res.reservation_id = int(cur.lastrowid)
            return res

    def cancel_reservation(self, reader: Reader, reservation_id: int,
                           at: datetime | None = None) -> Reservation:
        ts = at or now()
        rules = self.rules.current_rules()
        with self.circulation.db.transaction() as conn:
            res = self.circulation.find_reservation_by_id(
                reservation_id, conn=conn)
            if res is None or res.reader_id != reader.user_id:
                raise ValidationError("Reservation was not found.")
            was_ready = res.status == ReservationStatus.READY
            held_copy = res.copy_id
            try:
                res.cancel()
            except ValueError as err:
                raise ValidationError(str(err)) from err
            conn.execute(
                "UPDATE reservations SET status = 'CANCELED' "
                "WHERE reservation_id = ?", (res.reservation_id,))
            if was_ready and held_copy is not None:
                self._reassign_or_release(res.book_id, held_copy,
                                          rules.hold_days, ts, conn)
            return res

    def request_renewal(self, reader: Reader, borrow_id: int,
                        at: datetime | None = None) -> BorrowRecord:
        ts = at or now()
        rules = self.rules.current_rules()
        with self.circulation.db.transaction() as conn:
            u_row = conn.execute(
                "SELECT * FROM users WHERE user_id = ? AND role = ?",
                (reader.user_id, Role.READER.value)).fetchone()
            if u_row is None:
                raise ValidationError("Reader account was not found.")
            current = UserFactory.from_row(u_row)
            if not current.is_active:
                raise ValidationError(
                    "Your card must be active to renew a book.")

            row = conn.execute(
                "SELECT br.*, c.book_id FROM borrow_records br "
                "JOIN book_copies c ON c.copy_id = br.copy_id "
                "WHERE br.borrow_id = ? AND br.reader_id = ?",
                (borrow_id, current.user_id)).fetchone()
            if row is None:
                raise ValidationError("Borrowing record was not found.")
            record = BorrowRecord.from_row(row)
            if not record.is_open:
                raise ValidationError("Returned books cannot be renewed.")
            if record.status.value == "OVERDUE" or record.is_overdue(ts):
                raise ValidationError("Overdue books cannot be renewed.")
            if self.circulation.has_overdue_loan(current.user_id, ts, conn):
                raise ValidationError(
                    "Cannot renew while you have overdue books.")
            if self.circulation.has_unpaid_fine(current.user_id, conn):
                raise ValidationError(
                    "Cannot renew while you have unpaid fines.")
            if record.renew_count >= rules.max_renew:
                raise ValidationError("Renewal limit has been reached.")
            if self.circulation.next_waiting(row["book_id"], conn) is not None:
                raise ValidationError(
                    "Another reader is waiting in the queue for this book.")
            if not current.request_renewal(record, rules.max_renew,
                                           rules.max_days):
                raise ValidationError("This loan cannot be renewed.")

            conn.execute(
                "UPDATE borrow_records SET due_date = ?, renew_count = ? "
                "WHERE borrow_id = ?",
                (record.due_date.isoformat(sep=" "), record.renew_count,
                 record.borrow_id))
            return record

    def _reassign_or_release(self, book_id: int, copy_id: int,
                             hold_days: int, ts: datetime, conn) -> None:
        nxt = self.circulation.next_waiting(book_id, conn)
        if nxt is not None:
            expire = ts + timedelta(days=hold_days)
            conn.execute(
                "UPDATE reservations "
                "SET status = 'READY', copy_id = ?, expire_date = ? "
                "WHERE reservation_id = ?",
                (copy_id, expire.isoformat(sep=" "), nxt.reservation_id))
            row = conn.execute(
                "SELECT title FROM books WHERE book_id = ?",
                (book_id,)).fetchone()
            title = row["title"] if row else "Book"
            self.notifications.create_sent(
                nxt.reader_id,
                f"{title} is ready for pickup. Please collect it within "
                f"{hold_days} days.", ts, conn=conn)
        else:
            conn.execute(
                "UPDATE book_copies SET status = 'AVAILABLE' "
                "WHERE copy_id = ? AND status = 'RESERVED'", (copy_id,))
