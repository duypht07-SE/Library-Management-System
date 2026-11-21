import sqlite3
from datetime import datetime

from data.repositories.base_repository import BaseRepository
from models import PasswordResetRequest, ResetStatus


class PasswordResetRepository(BaseRepository):
    """Forgotten-password requests (FR-GST-05, FR-ADM-03)."""

    def create(self, user_id: int, at: datetime) -> bool:
        """Add a request; False when one is already waiting."""
        with self.db.transaction() as conn:
            exists = conn.execute(
                "SELECT 1 FROM password_reset_requests"
                " WHERE user_id = ? AND status = 'PENDING'",
                (user_id,)).fetchone()
            if exists is not None:
                return False
            conn.execute(
                "INSERT INTO password_reset_requests (user_id, requested_at)"
                " VALUES (?, ?)", (user_id, at.isoformat(sep=" ")))
            return True

    def pending(self) -> list[sqlite3.Row]:
        return self.db.fetch_all(
            "SELECT r.*, u.full_name, u.email, u.role"
            " FROM password_reset_requests r JOIN users u USING (user_id)"
            " WHERE r.status = 'PENDING' ORDER BY r.requested_at")

    def find_by_id(self, request_id: int) -> PasswordResetRequest | None:
        row = self.db.fetch_one(
            "SELECT * FROM password_reset_requests WHERE request_id = ?",
            (request_id,))
        if row is None:
            return None
        return PasswordResetRequest(
            row["request_id"], row["user_id"],
            datetime.fromisoformat(str(row["requested_at"])),
            ResetStatus(row["status"]))

    def close(self, request: PasswordResetRequest,
              conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE password_reset_requests SET status = ?, handled_by = ?,"
            " handled_at = ? WHERE request_id = ?",
            (request.status.value, request.handled_by,
             request.handled_at.isoformat(sep=" "), request.request_id))

    def close_all_for(self, user_id: int, admin_id: int, at: datetime,
                      conn: sqlite3.Connection) -> None:
        conn.execute(
            "UPDATE password_reset_requests SET status = 'COMPLETED',"
            " handled_by = ?, handled_at = ?"
            " WHERE user_id = ? AND status = 'PENDING'",
            (admin_id, at.isoformat(sep=" "), user_id))
