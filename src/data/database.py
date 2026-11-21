import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence

from common.security import PasswordHasher

DATA_DIR = Path(__file__).resolve().parent
SCHEMA_FILE = DATA_DIR / "schema.sql"
SEED_FILE = DATA_DIR / "seed.sql"
SAMPLE_PASSWORD = "Library@123"
SQLITE_HEADER = b"SQLite format 3\x00"

PERMISSIONS = {
    "CIRCULATION": "Check out and check in books",
    "READER_CARDS": "Approve, reject, lock, and unlock reader cards",
    "CATALOG": "Manage books, copies, e-books, and inventory checks",
    "FINES": "Record fines and cash payments",
}
DEFAULT_ROLES = {
    1: ("Full Librarian", "Every Librarian function",
        tuple(PERMISSIONS)),
    2: ("Circulation Desk", "Borrowing, returning, reader cards, and fines",
        ("CIRCULATION", "READER_CARDS", "FINES")),
    3: ("Catalog Librarian", "Book catalog, e-books, and inventory only",
        ("CATALOG",)),
}

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
            fresh = not self.is_initialized()
            if not fresh:
                self._add_missing_columns(conn)
            conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
            if fresh and seed:
                Seeder(conn).run()
            self._add_reference_data(conn)
        finally:
            conn.close()

    def _add_missing_columns(self, conn: sqlite3.Connection) -> None:
        """Small 0.2.0 migration for databases created by version 0.1.0."""
        existing = {row["name"] for row in
                    conn.execute("PRAGMA table_info(users)")}
        additions = {
            "student_id": "VARCHAR(30)",
            "avatar_path": "VARCHAR(255)",
            "created_at": "DATETIME",
            "staff_role_id": "INTEGER",
            "must_change_password": "INTEGER NOT NULL DEFAULT 0",
        }
        for name, sql_type in additions.items():
            if name not in existing:
                conn.execute(f"ALTER TABLE users ADD COLUMN {name} {sql_type}")
        if "created_at" not in existing:
            conn.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP "
                         "WHERE created_at IS NULL")

    @staticmethod
    def _add_reference_data(conn: sqlite3.Connection) -> None:
        """Permissions and the default staff roles (FR-ADM-02)."""
        conn.execute("BEGIN")
        conn.executemany(
            "INSERT OR IGNORE INTO permissions VALUES (?, ?)",
            PERMISSIONS.items())
        if conn.execute("SELECT COUNT(*) FROM staff_roles").fetchone()[0]:
            conn.execute("COMMIT")
            return
        for role_id, (name, description, codes) in DEFAULT_ROLES.items():
            conn.execute("INSERT INTO staff_roles VALUES (?, ?, ?)",
                         (role_id, name, description))
            conn.executemany(
                "INSERT INTO role_permissions VALUES (?, ?)",
                [(role_id, code) for code in codes])
        conn.execute("UPDATE users SET staff_role_id = 1"
                     " WHERE role = 'LIBRARIAN' AND staff_role_id IS NULL")
        conn.execute("COMMIT")

    def backup_to(self, target: Path) -> None:
        """Copy the whole database into a new file (FR-ADM-06)."""
        target.parent.mkdir(parents=True, exist_ok=True)
        source = self.connect()
        copy = sqlite3.connect(target)
        try:
            source.backup(copy)
        finally:
            copy.close()
            source.close()

    def restore_from(self, source_file: Path) -> None:
        """Replace every table with the backup content (FR-ADM-07)."""
        if not is_sqlite_backup(source_file):
            raise ValueError("The file is not a library database backup.")
        source = sqlite3.connect(source_file)
        target = self.connect()
        try:
            source.backup(target)
        finally:
            target.close()
            source.close()
        self.initialize(seed=False)

    def reset(self, seed: bool = True) -> None:
        if self.path.exists():
            self.path.unlink()
        self.initialize(seed)


def is_sqlite_backup(path: Path) -> bool:
    """True for an SQLite file that has the library tables."""
    try:
        with open(path, "rb") as file:
            if file.read(len(SQLITE_HEADER)) != SQLITE_HEADER:
                return False
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            names = {row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'")}
        finally:
            conn.close()
    except (OSError, sqlite3.DatabaseError):
        return False
    return {"users", "books", "book_copies", "borrow_records"} <= names


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
