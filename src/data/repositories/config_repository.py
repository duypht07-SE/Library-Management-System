from datetime import datetime

from data.repositories.base_repository import BaseRepository
from models import RuleKey, SystemConfig


class ConfigRepository(BaseRepository):
    """Reads and writes the library rules in system_configs."""

    def find_all(self) -> list[SystemConfig]:
        rows = self.db.fetch_all(
            "SELECT * FROM system_configs ORDER BY config_key")
        return [
            SystemConfig(
                config_key=RuleKey(r["config_key"]),
                config_value=r["config_value"],
                updated_by=r["updated_by"],
                updated_at=datetime.fromisoformat(r["updated_at"]),
            )
            for r in rows
        ]

    def update_values(self, values: dict[str, int], updated_by: int,
                      at: datetime) -> None:
        """Save all five rules as one transaction (NFR-REL-02)."""
        with self.db.transaction() as conn:
            for key, value in values.items():
                cursor = conn.execute(
                    "UPDATE system_configs SET config_value = ?,"
                    " updated_by = ?, updated_at = ? WHERE config_key = ?",
                    (str(value), updated_by, at.isoformat(), key))
                if cursor.rowcount == 0:
                    conn.execute(
                        "INSERT INTO system_configs"
                        " (config_key, config_value, updated_by, updated_at)"
                        " VALUES (?, ?, ?, ?)",
                        (key, str(value), updated_by, at.isoformat()))
