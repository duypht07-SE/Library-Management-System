import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SRC_DIR.parent
DEFAULT_DB_PATH = PROJECT_DIR / "instance" / "library.db"
LOCAL_TZ = timezone(timedelta(hours=7))  # NFR-COM-03


def now() -> datetime:
    return datetime.now(LOCAL_TZ).replace(tzinfo=None, microsecond=0)


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
        # NFR-SEC-05
        self.PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"
        self.TESTING = False


class TestConfig(Config):
    """Settings for pytest: a separate database file."""

    def __init__(self, database_path: Path) -> None:
        super().__init__()
        self.SECRET_KEY = "test-secret"
        self.DATABASE_PATH = Path(database_path)
        self.TESTING = True
