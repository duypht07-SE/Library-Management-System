from dataclasses import dataclass
from datetime import datetime

from models.enums import RuleKey


@dataclass
class SystemConfig:
    """One row of system_configs."""

    config_key: RuleKey
    config_value: str
    updated_by: int
    updated_at: datetime


@dataclass(frozen=True)
class LibraryRules:
    """The 5 library rules as numbers (FR-ADM-04)."""

    max_books: int = 5
    max_days: int = 14
    max_renew: int = 1
    hold_days: int = 3
    daily_fine: int = 5000

    @classmethod
    def from_configs(cls, configs: list[SystemConfig]) -> "LibraryRules":
        values = {c.config_key: int(c.config_value) for c in configs}
        default = cls()
        return cls(
            max_books=values.get(RuleKey.MAX_BOOKS, default.max_books),
            max_days=values.get(RuleKey.MAX_DAYS, default.max_days),
            max_renew=values.get(RuleKey.MAX_RENEW, default.max_renew),
            hold_days=values.get(RuleKey.HOLD_DAYS, default.hold_days),
            daily_fine=values.get(RuleKey.DAILY_FINE, default.daily_fine),
        )
