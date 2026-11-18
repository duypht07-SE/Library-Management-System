"""Component tests for accounts, login rules, and library rules."""
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from business.account_service import AccountService
from business.auth_service import AuthService
from business.rule_service import RuleService
from common.exceptions import AuthenticationError, ValidationError
from common.security import PasswordHasher
from data.database import Database
from data.repositories import ConfigRepository, UserRepository
from models import Administrator, Librarian, Reader, Role, UserStatus

PASSWORD = "Library@123"
NEW_PASSWORD = "Another456"


@pytest.fixture
def hasher():
    return PasswordHasher(4)  # low cost keeps the tests fast


@pytest.fixture
def users(database):
    return UserRepository(database)


@pytest.fixture
def auth(users, hasher):
    return AuthService(users, hasher)


@pytest.fixture
def accounts(users, hasher):
    return AccountService(users, hasher)


def register(auth, **overrides):
    fields = dict(full_name="New Reader", student_id="22529999",
                  email="new@library.test", phone="0912345678",
                  password=PASSWORD, confirmation=PASSWORD)
    fields.update(overrides)
    return auth.register(**fields)


def reader_actor(users):
    actor = users.find_by_id(2)
    assert isinstance(actor, Librarian)
    return actor


def admin_actor(users):
    actor = users.find_by_id(1)
    return actor


# --- Registration ---------------------------------------------------------
def test_register_creates_pending_reader_with_hashed_password(auth, users):
    reader = register(auth)
    assert isinstance(reader, Reader)
    assert reader.status == UserStatus.PENDING
    assert reader.card_code is None
    assert reader.student_id == "22529999"
    assert reader.password_hash.startswith("$2")
    assert users.find_by_email("new@library.test").user_id == reader.user_id


def test_register_rejects_duplicate_email(auth):
    with pytest.raises(ValidationError, match="email"):
        register(auth, email="reader@library.test")


def test_register_rejects_duplicate_phone(auth):
    with pytest.raises(ValidationError, match="phone"):
        register(auth, phone="0900000003")


def test_register_rejects_duplicate_student_id(auth):
    with pytest.raises(ValidationError, match="Student/Staff ID"):
        register(auth, student_id="22520001")


def test_register_rejects_mismatched_passwords(auth):
    with pytest.raises(ValidationError, match="do not match"):
        register(auth, confirmation="Different123")


# --- Sign in --------------------------------------------------------------
def test_authenticate_returns_the_right_role(auth):
    assert isinstance(
        auth.authenticate("reader@library.test", PASSWORD), Reader)
    assert isinstance(auth.authenticate("admin@library.test", PASSWORD),
                      Administrator)


def test_authenticate_rejects_wrong_email(auth):
    with pytest.raises(AuthenticationError, match="Invalid email or password"):
        auth.authenticate("nobody@library.test", PASSWORD)


def test_wrong_password_is_counted(auth, users):
    with pytest.raises(AuthenticationError):
        auth.authenticate("reader@library.test", "wrong")
    assert users.find_by_email("reader@library.test").failed_logins == 1


def test_five_wrong_passwords_lock_for_15_minutes(users, hasher):
    now = datetime(2026, 1, 1, 8, 0)
    auth = AuthService(users, hasher, clock=lambda: now)
    for _ in range(4):
        with pytest.raises(AuthenticationError):
            auth.authenticate("reader3@library.test", "wrong")
    with pytest.raises(AuthenticationError, match="15 minutes"):
        auth.authenticate("reader3@library.test", "wrong")

    user = users.find_by_email("reader3@library.test")
    assert user.locked_until == now + timedelta(minutes=15)
    assert user.failed_logins == 0
    with pytest.raises(AuthenticationError, match="Try again after 08:15"):
        auth.authenticate("reader3@library.test", PASSWORD)


def test_login_works_again_after_the_lock_expires(users, hasher):
    moment = [datetime(2026, 1, 1, 8, 0)]
    auth = AuthService(users, hasher, clock=lambda: moment[0])
    for _ in range(5):
        with pytest.raises(AuthenticationError):
            auth.authenticate("reader3@library.test", "wrong")
    moment[0] += timedelta(minutes=15)
    assert auth.authenticate("reader3@library.test", PASSWORD)


def test_pending_reader_cannot_sign_in(auth):
    with pytest.raises(AuthenticationError, match="waiting for approval"):
        auth.authenticate("pending@library.test", PASSWORD)


def test_locked_account_cannot_sign_in(auth):
    with pytest.raises(AuthenticationError, match="account is locked"):
        auth.authenticate("locked@library.test", PASSWORD)


def test_successful_login_resets_failed_count(auth, users):
    with pytest.raises(AuthenticationError):
        auth.authenticate("reader@library.test", "wrong")
    auth.authenticate("reader@library.test", PASSWORD)
    assert users.find_by_email("reader@library.test").failed_logins == 0


# --- Profile and password -------------------------------------------------
def test_reader_updates_own_profile(auth, users):
    reader = users.find_by_email("reader@library.test")
    auth.update_profile(reader, full_name="Nguyen Van Binh",
                        email="binh@library.test", phone="0911111111")
    saved = users.find_by_email("binh@library.test")
    assert saved.full_name == "Nguyen Van Binh"
    assert saved.phone == "0911111111"


def test_profile_cannot_take_another_account_email(auth, users):
    reader = users.find_by_email("reader@library.test")
    with pytest.raises(ValidationError, match="email"):
        auth.update_profile(reader, full_name=reader.full_name,
                            email="reader2@library.test", phone=reader.phone)


def test_reader_can_keep_their_own_email(auth, users):
    reader = users.find_by_email("reader@library.test")
    auth.update_profile(reader, full_name=reader.full_name,
                        email="READER@library.test", phone=reader.phone)
    assert users.find_by_id(reader.user_id).email == "reader@library.test"


def test_change_password_checks_the_current_password(auth, users):
    reader = users.find_by_email("reader@library.test")
    with pytest.raises(AuthenticationError, match="current password"):
        auth.change_password(reader, "wrong", NEW_PASSWORD, NEW_PASSWORD)
    auth.change_password(reader, PASSWORD, NEW_PASSWORD, NEW_PASSWORD)
    assert auth.authenticate("reader@library.test", NEW_PASSWORD)


def test_change_password_rejects_a_weak_new_password(auth, users):
    reader = users.find_by_email("reader@library.test")
    with pytest.raises(ValidationError):
        auth.change_password(reader, PASSWORD, "short", "short")


# --- Reader cards ---------------------------------------------------------
def test_librarian_approves_a_pending_card(accounts, users):
    reader = accounts.approve_reader(reader_actor(users), 5)
    assert reader.status == UserStatus.ACTIVE
    assert reader.card_code == "RD-0005"
    saved = users.find_by_id(5)
    assert saved.status == UserStatus.ACTIVE
    assert saved.card_code == "RD-0005"


def test_approving_twice_is_rejected(accounts, users):
    actor = reader_actor(users)
    accounts.approve_reader(actor, 5)
    with pytest.raises(ValidationError, match="pending"):
        accounts.approve_reader(actor, 5)


def test_librarian_rejects_a_pending_card(accounts, users):
    accounts.reject_reader(reader_actor(users), 5)
    assert users.find_by_id(5).status == UserStatus.REJECTED


def test_librarian_locks_and_unlocks_a_reader(accounts, users):
    actor = reader_actor(users)
    accounts.lock_reader(actor, 3)
    assert users.find_by_id(3).status == UserStatus.LOCKED
    accounts.unlock_reader(actor, 3)
    assert users.find_by_id(3).status == UserStatus.ACTIVE


def test_only_an_active_reader_can_be_locked(accounts, users):
    with pytest.raises(ValidationError, match="active"):
        accounts.lock_reader(reader_actor(users), 5)


# --- Librarian accounts ---------------------------------------------------
def test_administrator_creates_a_librarian(accounts, users):
    librarian = accounts.create_librarian(
        admin_actor(users), "New Staff", "staff@library.test", "0987654321",
        PASSWORD, "STF-0099")
    assert librarian.role == Role.LIBRARIAN
    assert librarian.status == UserStatus.ACTIVE
    saved = users.find_by_email("staff@library.test")
    assert saved.student_id == "STF-0099"


def test_administrator_cannot_duplicate_an_email(accounts, users):
    with pytest.raises(ValidationError, match="email"):
        accounts.create_librarian(
            admin_actor(users), "New Staff", "admin@library.test",
            "0987654321", PASSWORD)


def test_administrator_edits_a_librarian(accounts, users):
    accounts.update_librarian(admin_actor(users), 2, "Tran Thi Mai",
                              "librarian@library.test", "0900000002")
    saved = users.find_by_id(2)
    assert saved.full_name == "Tran Thi Mai"


def test_administrator_locks_and_unlocks_a_librarian(accounts, users):
    actor = admin_actor(users)
    accounts.set_librarian_status(actor, 2, "lock")
    assert users.find_by_id(2).status == UserStatus.LOCKED
    accounts.set_librarian_status(actor, 2, "unlock")
    assert users.find_by_id(2).status == UserStatus.ACTIVE


# --- Rules ----------------------------------------------------------------
def test_administrator_changes_the_five_rules(database, users):
    service = RuleService(ConfigRepository(database))
    values = {"MAX_BOOKS": 8, "MAX_DAYS": 21, "MAX_RENEW": 2,
              "HOLD_DAYS": 4, "DAILY_FINE": 7000}
    rules = service.update_rules(admin_actor(users), values)
    assert rules.max_books == 8
    assert rules.max_days == 21
    assert rules.daily_fine == 7000
    assert service.current_rules().max_renew == 2


# --- Migration ------------------------------------------------------------
def test_initialize_adds_the_0_2_0_columns_to_an_old_database(tmp_path):
    path = Path(tmp_path) / "old.db"
    conn = sqlite3.connect(path)
    conn.execute(
        "CREATE TABLE users (user_id INTEGER PRIMARY KEY, role TEXT,"
        " card_code TEXT, full_name TEXT, email TEXT, phone TEXT,"
        " password_hash TEXT, status TEXT, failed_logins INTEGER,"
        " locked_until TEXT)")
    conn.commit()
    conn.close()

    Database(path).initialize(seed=False)
    columns = {row["name"] for row in
               Database(path).fetch_all("PRAGMA table_info(users)")}
    assert {"student_id", "avatar_path"} <= columns
