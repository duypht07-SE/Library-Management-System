from data.repositories import ConfigRepository
from models import LibraryRules


class RuleService:
    """Reads the library rules (FR-ADM-04)."""

    def __init__(self, configs: ConfigRepository) -> None:
        self.configs = configs

    def current_rules(self) -> LibraryRules:
        return LibraryRules.from_configs(self.configs.find_all())
