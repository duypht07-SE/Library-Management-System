from datetime import datetime

from data.repositories.base_repository import BaseRepository
from models import Book, BookCopy, BorrowRecord, Reservation


class CirculationRepository(BaseRepository):
    def find_open_loans(self) -> list[dict]:
        rows = self.db.fetch_all(
            "SELECT br.*, u.full_name AS reader_name, u.card_code, "
            "c.barcode, b.book_id, b.title AS book_title "
            "FROM borrow_records br "
            "JOIN users u ON u.user_id = br.reader_id "
            "JOIN book_copies c ON c.copy_id = br.copy_id "
            "JOIN books b ON b.book_id = c.book_id "
            "WHERE br.status IN ('BORROWED', 'OVERDUE') "
            "AND br.return_date IS NULL "
            "ORDER BY br.due_date ASC, br.borrow_id ASC")
        return [dict(r) for r in rows]

    def find_loans_for_reader(self, reader_id: int) -> list[dict]:
        rows = self.db.fetch_all(
            "SELECT br.*, c.barcode, b.book_id, b.title AS book_title, "
            "(SELECT COUNT(*) FROM reservations r "
            " WHERE r.book_id = b.book_id AND r.status = 'WAITING') "
            "AS waiting_count "
            "FROM borrow_records br "
            "JOIN book_copies c ON c.copy_id = br.copy_id "
            "JOIN books b ON b.book_id = c.book_id "
            "WHERE br.reader_id = ? "
            "ORDER BY CASE WHEN br.status = 'RETURNED' THEN 1 ELSE 0 END, "
            "br.borrow_date DESC, br.borrow_id DESC",
            (reader_id,))
        return [dict(r) for r in rows]

    def find_borrow_records(self, reader_id: int) -> list[BorrowRecord]:
        rows = self.db.fetch_all(
            "SELECT * FROM borrow_records WHERE reader_id = ? "
            "ORDER BY borrow_date DESC, borrow_id DESC",
            (reader_id,))
        return [BorrowRecord.from_row(r) for r in rows]

    def find_reservations_for_reader(self, reader_id: int) -> list[dict]:
        rows = self.db.fetch_all(
            "SELECT r.*, b.title AS book_title, c.barcode "
            "FROM reservations r "
            "JOIN books b ON b.book_id = r.book_id "
            "LEFT JOIN book_copies c ON c.copy_id = r.copy_id "
            "WHERE r.reader_id = ? "
            "ORDER BY CASE r.status WHEN 'READY' THEN 0 WHEN 'WAITING' THEN 1 "
            "ELSE 2 END, r.reserve_date DESC, r.reservation_id DESC",
            (reader_id,))
        return [dict(r) for r in rows]

    def find_loan_by_id(self, borrow_id: int) -> BorrowRecord | None:
        row = self.db.fetch_one(
            "SELECT * FROM borrow_records WHERE borrow_id = ?", (borrow_id,))
        return BorrowRecord.from_row(row) if row else None

    def find_reservation_by_id(
            self, reservation_id: int, conn=None) -> Reservation | None:
        sql = "SELECT * FROM reservations WHERE reservation_id = ?"
        if conn is not None:
            row = conn.execute(sql, (reservation_id,)).fetchone()
        else:
            row = self.db.fetch_one(sql, (reservation_id,))
        return Reservation.from_row(row) if row else None

    def find_open_loan(self, conn, barcode: str = "",
                       borrow_id: int | None = None):
        base = (
            "SELECT br.*, c.book_id, c.barcode, c.shelf_location, "
            "c.status AS copy_status, c.copy_condition, b.title AS book_title "
            "FROM borrow_records br "
            "JOIN book_copies c ON c.copy_id = br.copy_id "
            "JOIN books b ON b.book_id = c.book_id "
            "WHERE br.status IN ('BORROWED', 'OVERDUE') "
            "AND br.return_date IS NULL "
        )
        if borrow_id is not None:
            return conn.execute(
                base + "AND br.borrow_id = ?", (borrow_id,)).fetchone()
        return conn.execute(
            base + "AND lower(c.barcode) = lower(?) "
            "ORDER BY br.borrow_id DESC LIMIT 1", (barcode,)).fetchone()

    def find_copy_by_barcode(self, barcode: str, conn) -> BookCopy | None:
        row = conn.execute(
            "SELECT * FROM book_copies WHERE lower(barcode) = lower(?)",
            (barcode,)).fetchone()
        return BookCopy.from_row(row) if row else None

    def find_book_with_copies(self, book_id: int, conn) -> Book | None:
        row = conn.execute(
            "SELECT * FROM books WHERE book_id = ?", (book_id,)).fetchone()
        if row is None:
            return None
        book = Book.from_row(row)
        copies = conn.execute(
            "SELECT * FROM book_copies WHERE book_id = ? ORDER BY copy_id",
            (book_id,)).fetchall()
        book.copies = [BookCopy.from_row(c) for c in copies]
        return book

    def count_open_loans(self, reader_id: int, conn) -> int:
        row = conn.execute(
            "SELECT COUNT(*) AS n FROM borrow_records "
            "WHERE reader_id = ? AND status IN ('BORROWED', 'OVERDUE') "
            "AND return_date IS NULL", (reader_id,)).fetchone()
        return int(row["n"])

    def has_overdue_loan(self, reader_id: int, at: datetime, conn) -> bool:
        row = conn.execute(
            "SELECT 1 FROM borrow_records "
            "WHERE reader_id = ? AND return_date IS NULL "
            "AND (status = 'OVERDUE' "
            "OR (status = 'BORROWED' AND due_date < ?)) "
            "LIMIT 1", (reader_id, at.isoformat(sep=" "))).fetchone()
        return row is not None

    def has_unpaid_fine(self, reader_id: int, conn) -> bool:
        row = conn.execute(
            "SELECT 1 FROM fines f "
            "JOIN borrow_records b ON b.borrow_id = f.borrow_id "
            "WHERE b.reader_id = ? AND f.is_paid = 0 LIMIT 1",
            (reader_id,)).fetchone()
        return row is not None

    def find_ready_for_copy(self, copy_id: int, conn) -> Reservation | None:
        row = conn.execute(
            "SELECT * FROM reservations "
            "WHERE copy_id = ? AND status = 'READY' "
            "ORDER BY reservation_id ASC LIMIT 1", (copy_id,)).fetchone()
        return Reservation.from_row(row) if row else None

    def next_waiting(self, book_id: int, conn) -> Reservation | None:
        row = conn.execute(
            "SELECT * FROM reservations "
            "WHERE book_id = ? AND status = 'WAITING' "
            "ORDER BY reserve_date ASC, reservation_id ASC LIMIT 1",
            (book_id,)).fetchone()
        return Reservation.from_row(row) if row else None

    def has_active_reservation(
            self, reader_id: int, book_id: int, conn) -> bool:
        row = conn.execute(
            "SELECT 1 FROM reservations "
            "WHERE reader_id = ? AND book_id = ? "
            "AND status IN ('WAITING', 'READY') LIMIT 1",
            (reader_id, book_id)).fetchone()
        return row is not None

    def is_borrowing_book(self, reader_id: int, book_id: int, conn) -> bool:
        row = conn.execute(
            "SELECT 1 FROM borrow_records r"
            " JOIN book_copies c ON c.copy_id = r.copy_id"
            " WHERE r.reader_id = ? AND c.book_id = ?"
            " AND r.status IN ('BORROWED', 'OVERDUE') LIMIT 1",
            (reader_id, book_id)).fetchone()
        return row is not None
