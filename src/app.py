"""Run:  python src/app.py              start the web server
      python src/app.py --reset-db   recreate the database with sample data"""
import argparse
import os
from datetime import date, datetime

from flask import Flask

from business.account_service import AccountService
from business.audit_service import AuditService
from business.auth_service import AuthService
from business.backup_service import BackupService
from business.catalog_service import CatalogService
from business.circulation_service import CirculationService
from business.daily_job_service import DailyJobService
from business.ebook_service import EbookService
from business.fine_service import FineService
from business.inventory_service import InventoryService
from business.password_reset_service import PasswordResetService
from business.report_service import ReportService
from business.role_service import RoleService
from business.rule_service import RuleService
from business.session_service import SessionService
from common import csrf
from common.security import PasswordHasher
from config import SRC_DIR, Config
from data.database import Database
from data.repositories import (AuditRepository, BookRepository,
                               CirculationRepository, ConfigRepository,
                               EbookRepository, FineRepository,
                               NotificationRepository,
                               PasswordResetRepository, ReportRepository,
                               SessionRepository, StaffRoleRepository,
                               UserRepository)
from presentation.access import (current_user, load_user,
                                 require_password_change)
from presentation.admin_controller import AdminController
from presentation.audit import audit_staff_actions
from presentation.auth_controller import AuthController
from presentation.ebook_controller import EbookController
from presentation.error_controller import ErrorController
from presentation.guest_controller import GuestController
from presentation.librarian_controller import LibrarianController
from presentation.reader_controller import ReaderController
from presentation.system_controller import SystemController


def format_date_vn(value, include_time: bool = False) -> str:
    """Format date values as DD/MM/YYYY, optionally including HH:MM."""
    if value is None or value == "":
        return ""
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return ""
    pattern = "%d/%m/%Y %H:%M" if include_time else "%d/%m/%Y"
    return parsed.strftime(pattern)


def add_hsts_header(response):
    """NFR-SEC-02: browsers keep using HTTPS for this site."""
    response.headers["Strict-Transport-Security"] = "max-age=31536000"
    return response


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
        self.staff_roles = StaffRoleRepository(self.database)
        self.audit_logs = AuditRepository(self.database)
        self.password_resets = PasswordResetRepository(self.database)
        self.session_repo = SessionRepository(self.database)
        self.ebooks = EbookRepository(self.database)
        self.hasher = PasswordHasher(self.config.BCRYPT_ROUNDS)
        self.session_service = SessionService(
            self.session_repo, self.config.PERMANENT_SESSION_LIFETIME)

        self.catalog_service = CatalogService(self.books)
        self.fine_service = FineService(self.fines)
        self.report_service = ReportService(self.reports)
        self.rule_service = RuleService(self.configs)
        self.auth_service = AuthService(self.users, self.hasher)
        self.account_service = AccountService(self.users, self.hasher)
        self.circulation_service = CirculationService(
            self.circulation, self.rule_service,
            self.fine_service, self.notifications)
        self.role_service = RoleService(self.staff_roles, self.users)
        self.audit_service = AuditService(self.audit_logs)
        self.password_reset_service = PasswordResetService(
            self.users, self.password_resets, self.hasher)
        self.inventory_service = InventoryService(self.books)
        self.ebook_service = EbookService(self.ebooks, self.books,
                                          self.config.EBOOK_DIR)
        self.backup_service = BackupService(
            self.database, self.config.BACKUP_DIR,
            copy_dir=self.config.BACKUP_COPY_DIR)
        self.daily_job_service = DailyJobService(
            self.circulation, self.notifications, self.rule_service,
            self.backup_service, self.audit_service)

        presentation = SRC_DIR / "presentation"
        self.flask = Flask(
            __name__,
            template_folder=str(presentation / "templates"),
            static_folder=str(presentation / "static"),
        )
        self.flask.config.from_object(self.config)
        self.flask.add_template_filter(format_date_vn, "date_vn")
        self.flask.extensions["lms"] = self

        self.database.initialize(seed=self.config.SEED_SAMPLE_DATA)
        self.session_service.purge_expired()
        csrf.init_app(self.flask)
        self.flask.before_request(csrf.check_request)
        self.flask.before_request(load_user(
            self.users, self.role_service, self.session_service,
            lambda: self.auth_service.clock()))
        self.flask.before_request(require_password_change)
        self.flask.after_request(audit_staff_actions(self.audit_service))
        if self.config.SSL_CONTEXT is not None:
            self.flask.after_request(add_hsts_header)
        self._register_controllers()

    def _register_controllers(self) -> None:
        GuestController(self.catalog_service, self.rule_service,
                        self.ebook_service,
                        self.circulation_service).register(self.flask)
        AuthController(self.auth_service, self.password_reset_service,
                       self.audit_service,
                       self.session_service).register(self.flask)
        ReaderController(self.auth_service, self.rule_service,
                         self.config, self.fine_service,
                         self.circulation_service,
                         self.session_service).register(self.flask)
        LibrarianController(self.account_service, self.catalog_service,
                            self.fine_service, self.circulation_service,
                            self.inventory_service,
                            self.ebook_service).register(self.flask)
        EbookController(self.ebook_service).register(self.flask)
        SystemController(self.role_service, self.password_reset_service,
                         self.audit_service,
                         self.backup_service).register(self.flask)
        AdminController(self.account_service, self.rule_service,
                        self.report_service,
                        self.role_service).register(self.flask)
        ErrorController().register(self.flask)

        @self.flask.context_processor
        def layout_data():
            return {"categories": self.catalog_service.categories(),
                    "current_user": current_user()}

    def run(self) -> None:
        # With the debug reloader the code runs twice; start the daily
        # job only in the process that serves requests.
        serving = (not self.config.DEBUG
                   or os.environ.get("WERKZEUG_RUN_MAIN") == "true")
        if serving and not self.config.TESTING:
            self.daily_job_service.run_safely()  # catch up a missed run
            self.daily_job_service.start_scheduler()
        self.flask.run(host=self.config.HOST, port=self.config.PORT,
                       debug=self.config.DEBUG,
                       ssl_context=self.config.SSL_CONTEXT)


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
