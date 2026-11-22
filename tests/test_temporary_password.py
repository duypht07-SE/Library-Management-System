"""NFR-SEC-05: 24-hour temporary passwords and the first-login change."""
import re
from datetime import datetime, timedelta, timezone

import pytest

from app import LibraryApp
from business.auth_service import AuthService
from business.password_reset_service import PasswordResetService
from common.exceptions import AuthenticationError, TemporaryPasswordExpiredError
from common.security import PasswordHasher
from config import TestConfig as AppTestConfig
from config import local_aware
from data.repositories import PasswordResetRepository, UserRepository
from models import Reader
from web_helpers import csrf_token, post_form, signin, text

LOCAL_TZ = timezone(timedelta(hours=7))
NOW = datetime(2026, 11, 22, 9, 0, tzinfo=LOCAL_TZ)
DAY = timedelta(hours=24)


def issued_at(database, user_id: int = 3) -> datetime:
    row = database.fetch_one(
        "SELECT temp_password_issued_at FROM users WHERE user_id = ?",
        (user_id,))
    return local_aware(datetime.fromisoformat(row["temp_password_issued_at"]))


def issue_temporary_password(client, library_app,
                             email: str = "reader@library.test") -> str:
    """Issue through the admin page, then sign the admin out."""
    signin(client, "admin@library.test")
    response = post_form(client, "/admin/password-resets",
                         "/admin/password-resets", {"email": email})
    match = re.search(r'class="temp-password">([^<]+)<', text(response))
    assert match, "temporary password was not displayed"
    post_form(client, "/admin/roles", "/signout", {})
    return match.group(1)


# --- Unit boundary -----------------------------------------------------------
@pytest.mark.parametrize("offset, expired", [
    (DAY - timedelta(seconds=1), False),
    (DAY, True),                       # exactly 24 hours is already expired
    (DAY + timedelta(seconds=1), True),
])
def test_temporary_password_expiry_boundary(offset, expired):
    user = Reader(3, "R", "r@library.test", "0900000003", "hash",
                  must_change_password=True, temporary_password_issued_at=NOW)
    assert user.temporary_password_expired(NOW + offset) is expired


def test_permanent_password_has_no_expiry():
    user = Reader(3, "R", "r@library.test", "0900000003", "hash",
                  must_change_password=False,
                  temporary_password_issued_at=NOW - timedelta(days=10))
    assert not user.temporary_password_expired(NOW + timedelta(days=10))


# --- Component ---------------------------------------------------------------
def test_reissue_resets_issuance_timestamp(database):
    users = UserRepository(database)
    clocks = iter([NOW, NOW + timedelta(hours=3)])
    resets = PasswordResetService(users, PasswordResetRepository(database),
                                  PasswordHasher(4), lambda: next(clocks))
    admin = users.find_by_id(1)

    user, first = resets.reset_by_email(admin, "reader@library.test")
    first_at = issued_at(database, user.user_id)
    assert PasswordHasher(4).verify(first, users.find_by_id(user.user_id).password_hash)

    user, second = resets.reset_by_email(admin, "reader@library.test")
    second_at = issued_at(database, user.user_id)
    assert second_at == NOW + timedelta(hours=3)
    assert second_at > first_at
    assert first != second
    stored = users.find_by_id(user.user_id)
    assert PasswordHasher(4).verify(second, stored.password_hash)
    assert not PasswordHasher(4).verify(first, stored.password_hash)


def test_authentication_errors_are_distinct(database):
    users = UserRepository(database)
    hasher = PasswordHasher(4)
    _, temporary = PasswordResetService(
        users, PasswordResetRepository(database), hasher,
        lambda: NOW).reset_by_email(users.find_by_id(1),
                                    "reader@library.test")
    expired_auth = AuthService(users, hasher, lambda: NOW + DAY)

    with pytest.raises(TemporaryPasswordExpiredError, match="expired"):
        expired_auth.authenticate("reader@library.test", temporary)
    with pytest.raises(AuthenticationError) as wrong:
        expired_auth.authenticate("reader@library.test", "not-the-password")
    assert not isinstance(wrong.value, TemporaryPasswordExpiredError)
    assert "Invalid email or password" in wrong.value.message

    valid_auth = AuthService(users, hasher, lambda: NOW)
    assert valid_auth.authenticate("reader@library.test", temporary).user_id == 3

    with users.db.transaction() as conn:
        conn.execute("UPDATE users SET status = 'PENDING' WHERE user_id = 3")
    with pytest.raises(AuthenticationError, match="approval"):
        valid_auth.authenticate("reader@library.test", temporary)

    with users.db.transaction() as conn:
        conn.execute("UPDATE users SET status = 'LOCKED' WHERE user_id = 3")
    with pytest.raises(AuthenticationError, match="locked"):
        valid_auth.authenticate("reader@library.test", temporary)

    with users.db.transaction() as conn:
        conn.execute(
            "UPDATE users SET status = 'ACTIVE',"
            " locked_until = ? WHERE user_id = 3",
            ((NOW + timedelta(minutes=5)).isoformat(sep=" "),))
    with pytest.raises(AuthenticationError, match="Try again after"):
        valid_auth.authenticate("reader@library.test", temporary)


def test_failed_password_change_keeps_temporary_status(database):
    users = UserRepository(database)
    hasher = PasswordHasher(4)
    _, temporary = PasswordResetService(
        users, PasswordResetRepository(database), hasher,
        lambda: NOW).reset_by_email(users.find_by_id(1),
                                    "reader@library.test")
    auth = AuthService(users, hasher, lambda: NOW)
    user = auth.authenticate("reader@library.test", temporary)
    original = issued_at(database, user.user_id)

    with pytest.raises(AuthenticationError, match="current password"):
        auth.change_password(user, "wrong", "NewPass123", "NewPass123")
    with pytest.raises(Exception, match="at least 8 characters"):
        auth.change_password(user, temporary, "short", "short")

    stored = users.find_by_id(user.user_id)
    assert stored.must_change_password
    assert issued_at(database, user.user_id) == original
    assert PasswordHasher(4).verify(temporary, stored.password_hash)


# --- System: 24-hour boundary ------------------------------------------------
@pytest.mark.parametrize("offset, accepted", [
    (timedelta(hours=23, minutes=59, seconds=59), True),
    (DAY, False),
    (DAY + timedelta(seconds=1), False),
])
def test_sign_in_boundary(client, library_app, offset, accepted):
    temporary = issue_temporary_password(client, library_app)
    at = issued_at(library_app.database)
    library_app.auth_service.clock = lambda: at + offset

    response = signin(client, "reader@library.test", temporary)
    if accepted:
        assert response.status_code == 302
        assert response.headers["Location"].endswith("/account/password")
    else:
        assert response.status_code == 401
        assert "temporary password has expired" in text(response)


def test_expired_temporary_password_is_rejected_on_alternative_query(client,
                                                                     library_app):
    temporary = issue_temporary_password(client, library_app)
    library_app.auth_service.clock = lambda: issued_at(library_app.database) + DAY
    token = csrf_token(client, "/signin")
    response = client.post("/signin?next=/profile", data={
        "csrf_token": token, "email": "reader@library.test",
        "password": temporary})
    assert response.status_code == 401
    assert "temporary password has expired" in text(response)


def test_expiry_survives_application_restart(client, library_app):
    temporary = issue_temporary_password(client, library_app)
    at = issued_at(library_app.database)

    restarted = LibraryApp(AppTestConfig(library_app.config.DATABASE_PATH))
    restarted_client = restarted.flask.test_client()
    restarted.auth_service.clock = lambda: at + timedelta(minutes=1)
    assert signin(restarted_client, "reader@library.test",
                  temporary).status_code == 302

    post_form(restarted_client, "/account/password", "/signout", {})
    restarted.auth_service.clock = lambda: at + DAY
    expired = signin(restarted_client, "reader@library.test", temporary)
    assert expired.status_code == 401
    assert "temporary password has expired" in text(expired)


def test_expiry_ends_an_already_open_session(client, library_app):
    temporary = issue_temporary_password(client, library_app)
    at = issued_at(library_app.database)
    library_app.auth_service.clock = lambda: at + timedelta(minutes=1)
    assert signin(client, "reader@library.test", temporary).status_code == 302

    library_app.auth_service.clock = lambda: at + DAY
    for url in ["/account/password", "/my-books"]:
        response = client.get(url)
        assert response.status_code == 302
        assert "/signin" in response.headers["Location"]


def test_permanent_password_ignores_the_expiry_clock(client, library_app):
    library_app.auth_service.clock = lambda: (
        datetime.now(LOCAL_TZ) + timedelta(days=365))
    response = signin(client, "reader2@library.test")
    assert response.status_code == 302
    assert client.get("/my-books").status_code == 200


def test_password_change_clears_status_and_old_password(client, library_app):
    temporary = issue_temporary_password(client, library_app)
    assert signin(client, "reader@library.test", temporary).headers[
        "Location"].endswith("/account/password")
    assert client.get("/my-books").headers["Location"].endswith(
        "/account/password")

    failed = post_form(client, "/account/password", "/account/password", {
        "current_password": "wrong", "new_password": "NewPass123",
        "confirmation": "NewPass123"})
    assert "current password is incorrect" in text(failed)
    assert library_app.users.find_by_id(3).must_change_password
    assert client.get("/my-books").headers["Location"].endswith(
        "/account/password")

    changed = post_form(client, "/account/password", "/account/password", {
        "current_password": temporary, "new_password": "NewPass123",
        "confirmation": "NewPass123"})
    assert "Your password has been changed" in text(changed)
    stored = library_app.users.find_by_id(3)
    assert not stored.must_change_password
    assert stored.temporary_password_issued_at is None
    assert client.get("/my-books").status_code == 200

    post_form(client, "/", "/signout", {})
    assert signin(client, "reader@library.test", temporary).status_code == 401
    assert signin(client, "reader@library.test", "NewPass123").status_code == 302


def test_new_password_is_validated_before_temporary_status_is_cleared(
        client, library_app):
    temporary = issue_temporary_password(client, library_app)
    signin(client, "reader@library.test", temporary)
    response = post_form(client, "/account/password", "/account/password", {
        "current_password": temporary, "new_password": "weak",
        "confirmation": "weak"})
    assert response.status_code == 400
    assert "at least 8 characters" in text(response)
    stored = library_app.users.find_by_id(3)
    assert stored.must_change_password
    assert stored.temporary_password_issued_at is not None
