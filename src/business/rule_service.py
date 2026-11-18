from config import now
from data.repositories import ConfigRepository
from models import Administrator, LibraryRules


class RuleService:
    """Reads and updates the library rules (FR-ADM-04, NFR-MNT-02)."""

    def __init__(self, configs: ConfigRepository) -> None:
        self.configs = configs

    def current_rules(self) -> LibraryRules:
        return LibraryRules.from_configs(self.configs.find_all())

    def update_rules(self, admin: Administrator,
                     values: dict[str, int]) -> LibraryRules:
        clean = admin.configure_rules(values)
        self.configs.update_values(clean, admin.user_id, now())
        return self.current_rules()
