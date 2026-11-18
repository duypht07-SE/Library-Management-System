from data.repositories.base_repository import BaseRepository
from models import Fine


class FineRepository(BaseRepository):
    """Stores fines and cash payments (Store D4)."""

    def find_for_reader(self, reader_id: int) -> list[Fine]:
        rows = self.db.fetch_all(
            "SELECT f.* FROM fines f JOIN borrow_records b "
            "ON b.borrow_id=f.borrow_id WHERE b.reader_id=? "
            "ORDER BY f.is_paid, f.fine_id DESC", (reader_id,))
        return [Fine.from_row(row) for row in rows]

    def find_by_id(self, fine_id: int) -> Fine | None:
        row = self.db.fetch_one("SELECT * FROM fines WHERE fine_id=?",
                                (fine_id,))
        return Fine.from_row(row) if row else None

    def find_all(self) -> list[dict]:
        rows = self.db.fetch_all(
            "SELECT f.*, b.reader_id, u.full_name AS reader_name "
            "FROM fines f JOIN borrow_records b ON b.borrow_id=f.borrow_id "
            "JOIN users u ON u.user_id=b.reader_id "
            "ORDER BY f.is_paid, f.fine_id DESC")
        return [dict(row) for row in rows]

    def loan_exists(self, borrow_id: int) -> bool:
        return self.db.fetch_one(
            "SELECT 1 FROM borrow_records WHERE borrow_id=?", (borrow_id,)) is not None

    def save(self, fine: Fine) -> Fine:
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO fines (borrow_id, reason, amount, is_paid, paid_at)"
                " VALUES (?, ?, ?, 0, NULL)",
                (fine.borrow_id, fine.reason.value, fine.amount))
            fine.fine_id = int(cursor.lastrowid)
        return fine

    def save_many(self, fines: list[Fine]) -> list[Fine]:
        with self.db.transaction() as conn:
            for fine in fines:
                cursor = conn.execute(
                    "INSERT INTO fines (borrow_id, reason, amount, is_paid)"
                    " VALUES (?, ?, ?, 0)",
                    (fine.borrow_id, fine.reason.value, fine.amount))
                fine.fine_id = int(cursor.lastrowid)
        return fines

    def mark_paid(self, fine_id: int, paid_at: str) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "UPDATE fines SET is_paid=1, paid_at=? "
                "WHERE fine_id=? AND is_paid=0", (paid_at, fine_id))
            return cursor.rowcount == 1

