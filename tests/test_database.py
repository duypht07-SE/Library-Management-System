"""Component tests for the data layer (Section 6)."""
import sqlite3

import pytest

from common.security import PasswordHasher
from data.database import SAMPLE_PASSWORD
from data.repositories import (BookRepository, ConfigRepository,
                               UserRepository)
from models import Administrator, Reader, Role

TABLES = {"users", "books", "book_copies", "borrow_records", "reservations",
          "fines", "system_configs", "notifications"}


def insert(database, sql):
    with database.transaction() as conn:
        conn.execute(sql)


def test_schema_has_8_tables(database):
    rows = database.fetch_all(
        "SELECT name FROM sqlite_master WHERE type = 'table'")
    assert TABLES <= {r["name"] for r in rows}


def test_seed_has_users_for_each_role(database):
    users = UserRepository(database)
    assert isinstance(users.find_by_email("admin@library.test"),
                      Administrator)
    assert isinstance(users.find_by_email("READER@library.test"), Reader)
    for role in Role:
        assert users.find_by_role(role)


def test_unknown_email_returns_none(database):
    assert UserRepository(database).find_by_email("x@y.test") is None


def test_seed_passwords_are_bcrypt_hashes_nfr_sec_01(database):
    user = UserRepository(database).find_by_email("reader@library.test")
    hasher = PasswordHasher()
    assert user.password_hash.startswith("$2")
    assert hasher.verify(SAMPLE_PASSWORD, user.password_hash)
    assert not hasher.verify("wrong", user.password_hash)
    assert not hasher.verify("", user.password_hash)


def test_broken_hash_is_rejected():
    assert not PasswordHasher().verify("x", "not-a-bcrypt-hash")


def test_available_copies_are_counted(database):
    books = BookRepository(database)
    assert books.count() == 20
    book1 = books.find_by_id(1)
    assert len(book1.copies) == 2
    assert book1.available_copies == 0
    assert books.find_by_id(6).available_copies == 2
    assert books.find_by_id(999) is None


def test_rules_are_seeded(database):
    keys = {c.config_key.value
            for c in ConfigRepository(database).find_all()}
    assert keys == {"MAX_BOOKS", "MAX_DAYS", "MAX_RENEW", "HOLD_DAYS",
                    "DAILY_FINE"}


def test_transaction_rolls_back_on_error_nfr_rel_02(database):
    with pytest.raises(RuntimeError):
        with database.transaction() as conn:
            conn.execute("UPDATE book_copies SET status = 'CANCELED'"
                         " WHERE copy_id = 6")
            raise RuntimeError("fail halfway")
    row = database.fetch_one(
        "SELECT status FROM book_copies WHERE copy_id = 6")
    assert row["status"] == "AVAILABLE"


@pytest.mark.parametrize("sql", [
    # foreign key: book 999 does not exist
    "INSERT INTO book_copies (book_id, barcode, shelf_location)"
    " VALUES (999, 'X', 'A')",
    # amount must be > 0 (boundary 0)
    "INSERT INTO fines (borrow_id, reason, amount)"
    " VALUES (1, 'LATE_RETURN', 0)",
    # status outside the allowed values
    "UPDATE book_copies SET status = 'SOLD' WHERE copy_id = 6",
    # barcode must be unique
    "INSERT INTO book_copies (book_id, barcode, shelf_location)"
    " VALUES (1, 'LIB-00011', 'A')",
    # email must be unique
    "INSERT INTO users (role, full_name, email, phone, password_hash)"
    " VALUES ('READER', 'X', 'reader@library.test', '0999', 'h')",
])
def test_database_rejects_invalid_data(database, sql):
    with pytest.raises(sqlite3.IntegrityError):
        insert(database, sql)


def test_reset_recreates_database(database):
    insert(database, "DELETE FROM notifications")
    database.reset()
    count = database.fetch_one("SELECT COUNT(*) AS n FROM notifications")
    assert count["n"] == 2
