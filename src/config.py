import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SRC_DIR.parent
DEFAULT_DB_PATH = PROJECT_DIR / "instance" / "library.db"
DEFAULT_AVATAR_DIR = PROJECT_DIR / "instance" / "avatars"
DEFAULT_EBOOK_DIR = PROJECT_DIR / "instance" / "ebooks"
DEFAULT_BACKUP_DIR = PROJECT_DIR / "instance" / "backups"
DEFAULT_BACKUP_COPY_DIR = PROJECT_DIR / "instance" / "backups_copy"
LOCAL_TZ = timezone(timedelta(hours=7))  # NFR-COM-03


def now_aware() -> datetime:
    """Current local time with an explicit UTC+7 offset."""
    return datetime.now(LOCAL_TZ).replace(microsecond=0)


def local_aware(value: datetime) -> datetime:
    """Return ``value`` as an explicit UTC+7 datetime.

    Legacy rows contain naive local timestamps; new security timestamps
    are stored with an offset. Both are normalized here before comparison.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=LOCAL_TZ)
    return value.astimezone(LOCAL_TZ)


def now() -> datetime:
    """Legacy naive local time, kept for existing date fields."""
    return now_aware().replace(tzinfo=None)


class Config:
    """Settings read from environment variables."""

    def __init__(self) -> None:
        env = os.environ.get
        self.SECRET_KEY = env("LMS_SECRET_KEY") or secrets.token_hex(32)
        self.DEBUG = env("LMS_DEBUG", "0") == "1"
        self.HOST = env("LMS_HOST", "127.0.0.1")
        self.PORT = int(env("LMS_PORT", "5000"))
        self.DATABASE_PATH = Path(env("LMS_DB_PATH", DEFAULT_DB_PATH))
        self.SEED_SAMPLE_DATA = env("LMS_SEED", "1") == "1"
        self.AVATAR_DIR = Path(env("LMS_AVATAR_DIR", DEFAULT_AVATAR_DIR))
        self.EBOOK_DIR = Path(env("LMS_EBOOK_DIR", DEFAULT_EBOOK_DIR))
        self.BACKUP_DIR = Path(env("LMS_BACKUP_DIR", DEFAULT_BACKUP_DIR))
        self.BACKUP_COPY_DIR = Path(
            env("LMS_BACKUP_COPY_DIR", DEFAULT_BACKUP_COPY_DIR))
        self.BCRYPT_ROUNDS = int(env("LMS_BCRYPT_ROUNDS", "12"))
        # avatars stay at 2 MB (FR-RDR-02); e-books and backups are larger
        self.MAX_CONTENT_LENGTH = 100 * 1024 * 1024
        # NFR-SEC-05
        self.PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"
        self.SESSION_COOKIE_SECURE = (
            env("LMS_SESSION_COOKIE_SECURE", "0") == "1")
        self.TESTING = False


class TestConfig(Config):
    """Settings for pytest: a separate database file and fast hashing."""

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.SECRET_KEY = "test-secret"
        self.DATABASE_PATH = Path(database_path)
        self.AVATAR_DIR = Path(database_path).parent / "avatars"
        self.EBOOK_DIR = Path(database_path).parent / "ebooks"
        self.BACKUP_DIR = Path(database_path).parent / "backups"
        self.BACKUP_COPY_DIR = Path(database_path).parent / "backups_copy"
        self.BCRYPT_ROUNDS = 4
        self.TESTING = True