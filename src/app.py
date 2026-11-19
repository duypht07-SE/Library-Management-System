"""Run:  python src/app.py              start the web server
      python src/app.py --reset-db   recreate the database with sample data"""
import argparse

from flask import Flask

from business.account_service import AccountService
from business.auth_service import AuthService
from business.catalog_service import CatalogService
from business.circulation_service import CirculationService
from business.daily_job_service import DailyJobService
from business.fine_service import FineService
from business.report_service import ReportService
from business.rule_service import RuleService
from common import csrf
from common.security import PasswordHasher
from config import SRC_DIR, Config
from data.database import Database
from data.repositories import (BookRepository, CirculationRepository,
                               ConfigRepository, FineRepository,
                               NotificationRepository, ReportRepository,
                               UserRepository)
from presentation.access import current_user, load_user
from presentation.admin_controller import AdminController
from presentation.auth_controller import AuthController
from presentation.error_controller import ErrorController
from presentation.guest_controller import GuestController
from presentation.librarian_controller import LibrarianController
from presentation.reader_controller import ReaderController


class LibraryApp:
    """Wires the layers: presentation -> business -> data (NFR-MNT-01)."""

    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config()
        self.database = Database(self.config.DATABASE_PATH)

        self.users = UserRepository(self.database)
        self.books = BookRepository(self.database)
        self.configs = ConfigRepository(self.database)
        self.fines = FineRepository(self.database)
        self.reports = ReportRepository(self.database)
        self.circulation = CirculationRepository(self.database)
        self.notifications = NotificationRepository(self.database)
        self.hasher = PasswordHasher(self.config.BCRYPT_ROUNDS)

        self.catalog_service = CatalogService(self.books)
        self.fine_service = FineService(self.fines)
        self.report_service = ReportService(self.reports)
        self.rule_service = RuleService(self.configs)
        self.auth_service = AuthService(self.users, self.hasher)
        self.account_service = AccountService(self.users, self.hasher)
        self.circulation_service = CirculationService(
            self.circulation, self.rule_service,
            self.fine_service, self.notifications)
        self.daily_job_service = DailyJobService(
            self.circulation, self.notifications, self.rule_service)

        presentation = SRC_DIR / "presentation"
        self.flask = Flask(
            __name__,
            template_folder=str(presentation / "templates"),
            static_folder=str(presentation / "static"),
        )
        self.flask.config.from_object(self.config)
        self.flask.extensions["lms"] = self

        self.database.initialize(seed=self.config.SEED_SAMPLE_DATA)
        csrf.init_app(self.flask)
        self.flask.before_request(csrf.check_request)
        self.flask.before_request(load_user(self.users))
        self._register_controllers()

    def _register_controllers(self) -> None:
        GuestController(self.catalog_service, self.rule_service).register(
            self.flask)
        AuthController(self.auth_service).register(self.flask)
        ReaderController(self.auth_service, self.rule_service,
                         self.config, self.fine_service,
                         self.circulation_service).register(self.flask)
        LibrarianController(self.account_service, self.catalog_service,
                            self.fine_service,
                            self.circulation_service).register(self.flask)
        AdminController(self.account_service, self.rule_service,
                        self.report_service).register(self.flask)
        ErrorController().register(self.flask)

        @self.flask.context_processor
        def layout_data():
            return {"categories": self.catalog_service.categories(),
                    "current_user": current_user()}

    def run(self) -> None:
        if not self.config.TESTING:
            self.daily_job_service.start_scheduler()
        self.flask.run(host=self.config.HOST, port=self.config.PORT,
                       debug=self.config.DEBUG)


def create_app(config: Config | None = None) -> Flask:
    return LibraryApp(config).flask


def main() -> None:
    parser = argparse.ArgumentParser(description="Library Management System")
    parser.add_argument("--reset-db", action="store_true",
                        help="recreate the database with sample data")
    parser.add_argument("--run-daily-jobs", action="store_true",
                        help="run overdue scan, reminders, and hold expiry")
    args = parser.parse_args()

    config = Config()
    if args.reset_db:
        Database(config.DATABASE_PATH).reset(seed=config.SEED_SAMPLE_DATA)
        print(f"Database reset: {config.DATABASE_PATH}")
        return
    app = LibraryApp(config)
    if args.run_daily_jobs:
        print(app.daily_job_service.run())
        return
    app.run()


if __name__ == "__main__":
    main()
