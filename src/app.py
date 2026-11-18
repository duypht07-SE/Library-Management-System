"""Run:  python src/app.py              start the web server
      python src/app.py --reset-db   recreate the database with sample data"""
import argparse

from flask import Flask

from config import SRC_DIR, Config
from data.database import Database
from data.repositories import (BookRepository, ConfigRepository,
                               UserRepository)
from business.catalog_service import CatalogService
from business.rule_service import RuleService
from presentation.error_controller import ErrorController
from presentation.guest_controller import GuestController


class LibraryApp:
    """Wires the layers: presentation -> business -> data (NFR-MNT-01)."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.database = Database(self.config.DATABASE_PATH)

        self.users = UserRepository(self.database)
        self.books = BookRepository(self.database)
        self.configs = ConfigRepository(self.database)

        self.catalog_service = CatalogService(self.books)
        self.rule_service = RuleService(self.configs)

        presentation = SRC_DIR / "presentation"
        self.flask = Flask(
            __name__,
            template_folder=str(presentation / "templates"),
            static_folder=str(presentation / "static"),
        )
        self.flask.config.from_object(self.config)
        self.flask.extensions["lms"] = self

        self.database.initialize(seed=self.config.SEED_SAMPLE_DATA)
        self._register_controllers()

    def _register_controllers(self) -> None:
        guest = GuestController(self.catalog_service, self.rule_service)
        guest.register(self.flask)
        ErrorController().register(self.flask)

        @self.flask.context_processor
        def layout_data():
            return {"categories": self.catalog_service.categories()}

    def run(self) -> None:
        self.flask.run(host=self.config.HOST, port=self.config.PORT,
                       debug=self.config.DEBUG)


def create_app(config: Config | None = None) -> Flask:
    return LibraryApp(config).flask


def main() -> None:
    parser = argparse.ArgumentParser(description="Library Management System")
    parser.add_argument("--reset-db", action="store_true",
                        help="recreate the database with sample data")
    args = parser.parse_args()

    config = Config()
    if args.reset_db:
        Database(config.DATABASE_PATH).reset(seed=config.SEED_SAMPLE_DATA)
        print(f"Database reset: {config.DATABASE_PATH}")
        return
    LibraryApp(config).run()


if __name__ == "__main__":
    main()
