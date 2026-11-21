"""Unit tests for validation and account rules (Section 1, Section 5)."""
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from common.exceptions import AuthenticationError, ValidationError
from common.validation import (validate_email, validate_password,
                               validate_phone, validate_student_id)
from config import TestConfig as AppTestConfig
from models import (Administrator, Librarian, Reader, Role, RuleKey,
                    UserFactory, UserStatus)


def test_session_and_upload_limits_nfr_sec_05():
    config = AppTestConfig(Path("unused.db"))
    assert config.PERMANENT_SESSION_LIFETIME == timedelta(minutes=30)
    assert config.SESSION_COOKIE_HTTPONLY is True
    assert config.SESSION_COOKIE_SAMESITE == "Lax"
    assert config.MAX_CONTENT_LENGTH == 100 * 1024 * 1024  # e-books, backups


def test_every_role_has_its_own_home_page():
    common = dict(user_id=1, full_name="A", email="a@b.test", phone="0900",
                  password_hash="h")
    assert Reader(**common).home_endpoint == "reader.profile"
    assert Librarian(**common).home_endpoint == "librarian.index"
    assert Administrator(**common).home_endpoint == "admin.librarians"


def test_email_is_trimmed_and_lowercased():
    assert validate_email("  An@Example.COM ") == "an@example.com"


@pytest.mark.parametrize("value",
                         ["", "abc", "a@b", "a b@c.test", "a@@b.test"])
def test_invalid_email_is_rejected(value):
    with pytest.raises(ValidationError):
        validate_email(value)


@pytest.mark.parametrize("value", ["0900000001", "+84900000001", "123456789"])
def test_valid_phone_is_accepted(value):
    assert validate_phone(value)


@pytest.mark.parametrize("value", ["", "12345", "abc123456", "0" * 16])
def test_invalid_phone_is_rejected(value):
    with pytest.raises(ValidationError):
        validate_phone(value)


@pytest.mark.parametrize("value", ["22520001", "SV-2022.01", "STF_01"])
def test_valid_student_id_is_accepted(value):
    assert validate_student_id(value) == value


@pytest.mark.parametrize("value", ["", "ab", "has space", "a" * 31])
def test_invalid_student_id_is_rejected(value):
    with pytest.raises(ValidationError):
        validate_student_id(value)


def test_password_needs_eight_characters_a_letter_and_a_digit():
    with pytest.raises(ValidationError):
        validate_password("Abc1234")        # 7 characters (boundary)
    with pytest.raises(ValidationError):
        validate_password("abcdefgh")       # no digit
    with pytest.raises(ValidationError):
        validate_password("12345678")       # no letter
    with pytest.raises(ValidationError):
        validate_password("A1" + "x" * 71)  # over 72 bytes for bcrypt
    assert validate_password("Secret123") == "Secret123"


def test_active_reader_can_login():
    reader = Reader(user_id=1, full_name="A", email="a@b.test", phone="0900",
                    password_hash="h", status=UserStatus.ACTIVE)
    reader.login(datetime(2026, 1, 1, 8, 0))


@pytest.mark.parametrize("status, message", [
    (UserStatus.PENDING, "waiting for approval"),
    (UserStatus.REJECTED, "rejected"),
    (UserStatus.LOCKED, "locked"),
])
def test_inactive_reader_cannot_login(status, message):
    reader = Reader(user_id=1, full_name="A", email="a@b.test", phone="0900",
                    password_hash="h", status=status)
    with pytest.raises(AuthenticationError, match=message):
        reader.login(datetime(2026, 1, 1, 8, 0))


def test_temporary_login_lock_uses_the_clock():
    at = datetime(2026, 1, 1, 8, 0)
    reader = Reader(user_id=1, full_name="A", email="a@b.test", phone="0900",
                    password_hash="h", status=UserStatus.ACTIVE,
                    locked_until=at + timedelta(minutes=15))
    with pytest.raises(AuthenticationError, match="15|08:15"):
        reader.login(at)
    reader.login(at + timedelta(minutes=15))  # boundary: lock has ended


def test_update_password_clears_failed_attempts():
    reader = Reader(user_id=1, full_name="A", email="a@b.test", phone="0900",
                    password_hash="old", status=UserStatus.ACTIVE,
                    failed_logins=4,
                    locked_until=datetime(2026, 1, 1, 8, 0))
    reader.update_password("new")
    assert reader.password_hash == "new"
    assert reader.failed_logins == 0
    assert reader.locked_until is None


def test_librarian_card_and_reader_actions():
    librarian = Librarian(user_id=2, full_name="L", email="l@b.test",
                          phone="0901", password_hash="h",
                          status=UserStatus.ACTIVE)
    reader = Reader(user_id=3, full_name="R", email="r@b.test", phone="0902",
                    password_hash="h", status=UserStatus.PENDING)
    librarian.approve_card(reader, "RD-0003")
    assert reader.status == UserStatus.ACTIVE
    assert reader.card_code == "RD-0003"
    librarian.lock_reader(reader)
    assert reader.status == UserStatus.LOCKED
    librarian.unlock_reader(reader)
    assert reader.status == UserStatus.ACTIVE
    librarian.reject_card(reader)
    assert reader.status == UserStatus.REJECTED


def test_administrator_manages_librarian_and_rules():
    admin = Administrator(user_id=1, full_name="A", email="a@b.test",
                          phone="0900", password_hash="h",
                          status=UserStatus.ACTIVE)
    librarian = Librarian(user_id=2, full_name="L", email="l@b.test",
                          phone="0901", password_hash="h",
                          status=UserStatus.ACTIVE)
    admin.manage_librarian(librarian, "lock")
    assert librarian.status == UserStatus.LOCKED
    admin.manage_librarian(librarian, "unlock")
    assert librarian.status == UserStatus.ACTIVE
    with pytest.raises(ValueError):
        admin.manage_librarian(librarian, "delete")

    rules = admin.configure_rules({
        RuleKey.MAX_BOOKS.value: 5, RuleKey.MAX_DAYS.value: 14,
        RuleKey.MAX_RENEW.value: 1, RuleKey.HOLD_DAYS.value: 3,
        RuleKey.DAILY_FINE.value: 5000,
    })
    assert rules["MAX_BOOKS"] == 5
    with pytest.raises(ValueError):
        admin.configure_rules({"MAX_BOOKS": 0})
    with pytest.raises(ValueError):
        admin.configure_rules({"NOT_A_RULE": 1})


def test_factory_reads_the_new_profile_columns():
    user = UserFactory.from_row({
        "user_id": 3, "role": "READER", "card_code": "RD-0003",
        "student_id": "22520001", "full_name": "R", "email": "r@b.test",
        "phone": "0902", "password_hash": "h", "status": "ACTIVE",
        "failed_logins": 0, "locked_until": None, "avatar_path": "a.png",
    })
    assert isinstance(user, Reader)
    assert user.role == Role.READER
    assert user.student_id == "22520001"
    assert user.avatar_path == "a.png"
