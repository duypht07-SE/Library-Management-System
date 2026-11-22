import sqlite3
from datetime import datetime

from data.repositories.base_repository import BaseRepository


class SessionRepository(BaseRepository):
    """Server-side session registry (NFR-SEC-05).

    Only the SHA-256 digest of the opaque cookie id is stored, so a database
    read alone cannot be replayed as a valid session cookie.
    """

    def create(self, digest: str, user_id: int, created_at: datetime,
               expires_at: datetime) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO user_sessions (session_id_hash, user_id,"
                " created_at, last_seen_at, expires_at)"
                " VALUES (?, ?, ?, ?, ?)",
                (digest, user_id, created_at.isoformat(sep=" "),
                 created_at.isoformat(sep=" "),
                 expires_at.isoformat(sep=" ")))

    def find(self, digest: str) -> sqlite3.Row | None:
        return self.db.fetch_one(
            "SELECT user_id, expires_at, revoked_at FROM user_sessions"
            " WHERE session_id_hash = ?", (digest,))

    def touch(self, digest: str, seen_at: datetime,
              expires_at: datetime) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE user_sessions SET last_seen_at = ?, expires_at = ?"
                " WHERE session_id_hash = ? AND revoked_at IS NULL",
                (seen_at.isoformat(sep=" "),
                 expires_at.isoformat(sep=" "), digest))

    def revoke(self, digest: str, at: datetime) -> bool:
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "UPDATE user_sessions SET revoked_at = ?"
                " WHERE session_id_hash = ? AND revoked_at IS NULL",
                (at.isoformat(sep=" "), digest))
            return cursor.rowcount > 0

    def purge_expired(self, at: datetime) -> int:
        """Delete sessions whose inactivity window has ended."""
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "DELETE FROM user_sessions WHERE expires_at <= ?",
                (at.isoformat(sep=" "),))
            return cursor.rowcount
