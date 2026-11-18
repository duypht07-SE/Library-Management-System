from datetime import datetime

from data.repositories.base_repository import BaseRepository
from models import RuleKey, SystemConfig


class ConfigRepository(BaseRepository):
    """Reads the library rules in system_configs."""

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
