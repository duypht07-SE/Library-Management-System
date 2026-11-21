from config import now
from data.repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    """Aggregates catalog, circulation, fine, and account reports."""

    def monthly(self, start: str, end: str) -> dict:
        return {
            "borrowings": self.db.fetch_one(
                "SELECT COUNT(*) n FROM borrow_records "
                "WHERE borrow_date >= ? AND borrow_date < ?", (start, end))["n"],
            "overdue": self.db.fetch_one(
                "SELECT COUNT(*) n FROM borrow_records "
                "WHERE due_date >= ? AND due_date < ? "
                "AND COALESCE(return_date, ?) > due_date",
                (start, end, now().isoformat(sep=" ")))["n"],
            "fines_collected": self.db.fetch_one(
                "SELECT COALESCE(SUM(amount), 0) n FROM fines "
                "WHERE is_paid=1 AND paid_at >= ? AND paid_at < ?",
                (start, end))["n"],
            "book_titles": self.db.fetch_one(
                "SELECT COUNT(*) n FROM books")["n"],
            "available_copies": self.db.fetch_one(
                "SELECT COUNT(*) n FROM book_copies WHERE status='AVAILABLE'")["n"],
            "new_readers": self.db.fetch_one(
                "SELECT COUNT(*) n FROM users WHERE role='READER' "
                "AND created_at >= ? AND created_at < ?", (start, end))["n"],
        }
