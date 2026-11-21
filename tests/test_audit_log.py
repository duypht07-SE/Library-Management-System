"""Audit log of sign-ins and staff actions (FR-SYS-04, FR-ADM-08)."""
from datetime import datetime

from business.audit_service import AuditService
from data.repositories import AuditRepository, UserRepository
from web_helpers import post_form, signin, text


def test_record_and_filter(database):
    audit = AuditService(AuditRepository(database),
                         lambda: datetime(2026, 11, 21, 8, 0))
    admin = UserRepository(database).find_by_id(1)
    audit.record(admin, "SIGN_IN", "Admin signed in", "10.0.0.1")
    audit.record(None, "SIGN_IN_FAILED", "x@y.test: Invalid", None)
    assert [log.action for log in audit.recent()] == [
        "SIGN_IN_FAILED", "SIGN_IN"]
    only = audit.recent(action="SIGN_IN")
    assert len(only) == 1 and only[0].user_name == "Nguyen Thanh Admin"
    assert audit.actions() == ["SIGN_IN", "SIGN_IN_FAILED"]


def test_long_details_are_cut_to_column_size(database):
    audit = AuditService(AuditRepository(database))
    audit.record(None, "A" * 80, "x" * 400)
    log = audit.recent()[0]
    assert len(log.action) == 50 and len(log.details) == 255


def test_sign_ins_are_logged(client, library_app):
    signin(client, "reader@library.test", "wrong-password")
    signin(client, "reader@library.test")
    actions = [log.action for log in library_app.audit_service.recent()]
    assert actions[:2] == ["SIGN_IN", "SIGN_IN_FAILED"]


def test_librarian_action_is_logged(client, library_app):
    signin(client, "librarian@library.test")
    post_form(client, "/librarian/readers", "/librarian/readers/5/approve")
    log = library_app.audit_service.recent()[0]
    assert log.action == "librarian.reader_action"
    assert "approved for Pham Minh Chau" in log.details
    assert log.user_id == 2


def test_failed_action_is_not_logged_as_success(client, library_app):
    signin(client, "librarian@library.test")
    before = len(library_app.audit_service.recent())
    post_form(client, "/librarian/readers", "/librarian/readers/3/approve")
    assert len(library_app.audit_service.recent()) == before


def test_reader_edits_are_not_staff_actions(client, library_app):
    signin(client, "reader3@library.test")
    before = len(library_app.audit_service.recent())
    post_form(client, "/books/5", "/books/5/reserve")
    assert len(library_app.audit_service.recent()) == before


def test_audit_page_is_admin_only(client):
    signin(client, "admin@library.test")
    page = text(client.get("/admin/audit-log"))
    assert "Audit Log" in page and "SIGN_IN" in page
    post_form(client, "/admin/audit-log", "/signout")
    signin(client, "librarian@library.test")
    assert client.get("/admin/audit-log").status_code == 403
