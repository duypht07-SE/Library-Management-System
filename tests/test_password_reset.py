"""Forgotten passwords (FR-GST-05) and temporary passwords (FR-ADM-03)."""
import re
from datetime import datetime

import pytest

from business.password_reset_service import (PasswordResetService,
                                             make_temporary_password)
from common.exceptions import ValidationError
from common.security import PasswordHasher
from common.validation import validate_password
from data.repositories import PasswordResetRepository, UserRepository
from models import (Administrator, PasswordResetRequest, Reader,
                    ResetStatus)
from web_helpers import post_form, signin, text

NOW = datetime(2026, 11, 21, 9, 0)


@pytest.fixture
def resets(database):
    return PasswordResetService(UserRepository(database),
                                PasswordResetRepository(database),
                                PasswordHasher(4), lambda: NOW)


@pytest.fixture
def admin(database):
    return UserRepository(database).find_by_id(1)


# --- Unit --------------------------------------------------------------------
def test_temporary_password_is_valid_and_random():
    passwords = {make_temporary_password() for _ in range(50)}
    assert len(passwords) == 50
    for password in passwords:
        assert validate_password(password) == password


def test_request_can_be_handled_only_once():
    request = PasswordResetRequest(1, 3, NOW)
    request.complete(1, NOW)
    assert request.status == ResetStatus.COMPLETED
    with pytest.raises(ValueError):
        request.reject(1, NOW)


def test_admin_password_cannot_be_reset_here():
    admin = Administrator(1, "A", "a@x.test", "0900000001", "h")
    with pytest.raises(ValueError):
        admin.reset_password(admin, "new-hash")


def test_reset_sets_must_change_and_clears_lock():
    admin = Administrator(1, "A", "a@x.test", "0900000001", "h")
    reader = Reader(3, "R", "r@x.test", "0900000003", "old",
                    failed_logins=4, locked_until=NOW)
    admin.reset_password(reader, "new-hash")
    assert reader.must_change_password
    assert reader.failed_logins == 0 and reader.locked_until is None


# --- Component ---------------------------------------------------------------
@pytest.mark.parametrize("email, phone, saved", [
    ("reader@library.test", "0900000003", True),
    ("READER@library.test", "0900 000 003", True),   # case and spaces
    ("reader@library.test", "0999999999", False),    # wrong phone
    ("nobody@library.test", "0900000003", False),    # unknown email
    ("admin@library.test", "0900000001", False),     # Admin is excluded
])
def test_request_reset_partitions(resets, email, phone, saved):
    resets.request_reset(email, phone)
    assert bool(resets.pending()) is saved


def test_bad_email_format_is_reported(resets):
    with pytest.raises(ValidationError):
        resets.request_reset("not-an-email", "0900000003")


def test_same_user_gets_one_pending_request(resets):
    resets.request_reset("reader@library.test", "0900000003")
    resets.request_reset("reader@library.test", "0900000003")
    assert len(resets.pending()) == 1


def test_reset_for_request_gives_working_password(resets, admin, database):
    resets.request_reset("reader@library.test", "0900000003")
    request_id = resets.pending()[0]["request_id"]
    user, password = resets.reset_for_request(admin, request_id)
    stored = UserRepository(database).find_by_id(user.user_id)
    assert PasswordHasher(4).verify(password, stored.password_hash)
    assert stored.must_change_password
    assert resets.pending() == []
    with pytest.raises(ValidationError):
        resets.reset_for_request(admin, request_id)   # handled already


def test_reject_request(resets, admin):
    resets.request_reset("librarian@library.test", "0900000002")
    request_id = resets.pending()[0]["request_id"]
    resets.reject_request(admin, request_id)
    assert resets.pending() == []


def test_reset_by_email_unknown_account(resets, admin):
    with pytest.raises(ValidationError, match="No account"):
        resets.reset_by_email(admin, "ghost@library.test")


# --- System --------------------------------------------------------------
def test_full_reset_flow_through_pages(client):
    page = post_form(client, "/forgot-password", "/forgot-password", {
        "email": "reader@library.test", "phone": "0900000003"})
    assert "request has been sent" in text(page)

    signin(client, "admin@library.test")
    resets_page = text(client.get("/admin/password-resets"))
    assert "reader@library.test" in resets_page
    request_id = re.search(r"/admin/password-resets/(\d+)/reset",
                           resets_page).group(1)
    issued = post_form(client, "/admin/password-resets",
                       f"/admin/password-resets/{request_id}/reset")
    password = re.search(r'class="temp-password">([^<]+)<',
                         text(issued)).group(1)
    log = text(client.get("/admin/audit-log"))
    assert "Temporary password issued to reader@library.test" in log
    assert password not in log                    # never stored in the log
    post_form(client, "/admin/roles", "/signout")

    response = signin(client, "reader@library.test", password)
    assert response.headers["Location"].endswith("/account/password")
    blocked = client.get("/my-books")
    assert blocked.headers["Location"].endswith("/account/password")
    changed = post_form(client, "/account/password", "/account/password", {
        "current_password": password, "new_password": "NewPass123",
        "confirmation": "NewPass123"})
    assert "Your password has been changed" in text(changed)
    assert client.get("/my-books").status_code == 200


def test_unknown_account_gets_the_same_message(client):
    page = post_form(client, "/forgot-password", "/forgot-password", {
        "email": "ghost@library.test", "phone": "0900000003"})
    assert "request has been sent" in text(page)


def test_signin_page_links_to_forgot_password(client):
    assert "/forgot-password" in text(client.get("/signin"))


def test_staff_can_change_own_password(client):
    signin(client, "librarian@library.test")
    page = post_form(client, "/account/password", "/account/password", {
        "current_password": "wrong", "new_password": "NewPass123",
        "confirmation": "NewPass123"})
    assert "current password is incorrect" in text(page)
