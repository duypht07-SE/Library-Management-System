import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from common.security import PasswordHasher

DATA_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = DATA_DIR / "schema.sql"
SEED_FILE = DATA_DIR / "seed.sql"
SAMPLE_PASSWORD = "Library@123"

Params = Sequence[Any]


class Database:
    """SQLite connection, queries, and transactions."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        # NFR-REL-02, NFR-REL-03: lock, then commit or roll back as one unit
        conn = self.connect()
        try:
            conn.execute("BEGIN IMMEDIATE")
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        finally:
            conn.close()

    def fetch_all(self, sql: str, params: Params = ()) -> list[sqlite3.Row]:
        conn = self.connect()
        try:
            return conn.execute(sql, params).fetchall()
        finally:
            conn.close()

    def fetch_one(self, sql: str, params: Params = ()) -> sqlite3.Row | None:
        conn = self.connect()
        try:
            return conn.execute(sql, params).fetchone()
        finally:
            conn.close()

    def is_initialized(self) -> bool:
        row = self.fetch_one(
            "SELECT name FROM sqlite_master"
            " WHERE type = 'table' AND name = 'users'")
        return row is not None

    def initialize(self, seed: bool = True) -> None:
        conn = self.connect()
        try:
            if self.is_initialized():
                self._add_missing_columns(conn)
                return
            conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
            if seed:
                Seeder(conn).run()
        finally:
            conn.close()

    def _add_missing_columns(self, conn: sqlite3.Connection) -> None:
        """Small 0.2.0 migration for databases created by version 0.1.0."""
        existing = {row["name"] for row in
                    conn.execute("PRAGMA table_info(users)")}
        additions = {
            "student_id": "VARCHAR(30)",
            "avatar_path": "VARCHAR(255)",
        }
        for name, sql_type in additions.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE users ADD COLUMN {name} {sql_type}")

    def reset(self, seed: bool = True) -> None:
        if self.path.exists():
            self.path.unlink()
        self.initialize(seed)


class Seeder:
    """Loads seed.sql with a real password hash."""

    def __init__(self, conn: sqlite3.Connection,
                 hasher: PasswordHasher | None = None) -> None:
        self.conn = conn
        self.hasher = hasher or PasswordHasher()

    def run(self) -> None:
        sql = SEED_FILE.read_text(encoding="utf-8")
        password_hash = self.hasher.hash(SAMPLE_PASSWORD)
        sql = sql.replace("{{PASSWORD_HASH}}", password_hash)
        self.conn.executescript("BEGIN;\n" + sql + "\nCOMMIT;")
