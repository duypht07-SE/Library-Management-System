from datetime import datetime

from data.repositories.base_repository import BaseRepository
from models import AuditLog


class AuditRepository(BaseRepository):
    """Sign-ins and staff actions (FR-SYS-04, FR-ADM-08)."""

    def add(self, user_id: int | None, action: str, details: str,
            ip_address: str | None, at: datetime) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "INSERT INTO audit_logs (user_id, action, details,"
                " ip_address, created_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, action[:50], details[:255], ip_address,
                 at.isoformat(sep=" ")))

    def recent(self, limit: int = 200, user_id: int | None = None,
               action: str = "") -> list[AuditLog]:
        sql = ("SELECT a.*, u.full_name FROM audit_logs a"
               " LEFT JOIN users u ON u.user_id = a.user_id WHERE 1 = 1")
        params: list[object] = []
        if user_id:
            sql += " AND a.user_id = ?"
            params.append(user_id)
        if action:
            sql += " AND a.action = ?"
            params.append(action)
        sql += " ORDER BY a.log_id DESC LIMIT ?"
        params.append(limit)
        return [AuditLog(r["log_id"], r["user_id"], r["action"],
                         r["details"],
                         datetime.fromisoformat(str(r["created_at"])),
                         r["ip_address"], r["full_name"])
                for r in self.db.fetch_all(sql, tuple(params))]

    def actions(self) -> list[str]:
        rows = self.db.fetch_all(
            "SELECT DISTINCT action FROM audit_logs ORDER BY action")
        return [r["action"] for r in rows]
