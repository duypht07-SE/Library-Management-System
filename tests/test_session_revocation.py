"""NFR-SEC-05: opaque server-side sessions and logout revocation."""
import sqlite3
from datetime import datetime, timedelta, timezone

from app import LibraryApp
from business.session_service import SESSION_ID_KEY, SessionService
from config import TestConfig as AppTestConfig
from config import local_aware, now_aware
from data.database import Database
from data.repositories import SessionRepository
from web_helpers import PASSWORD, post_form, signin, text

LOCAL_TZ = timezone(timedelta(hours=7))
NOW = datetime(2026, 11, 22, 9, 0, tzinfo=LOCAL_TZ)
LIFETIME = timedelta(minutes=30)


def service(database, clock, lifetime=LIFETIME) -> SessionService:
    return SessionService(SessionRepository(database), lifetime, clock)


def cookie_value(client) -> str:
    cookie = client.get_cookie("session")
    assert cookie is not None, "no session cookie was issued"
    return cookie.value


def replay_client(library_app, cookie: str):
    client = library_app.flask.test_client()
    client.set_cookie("session", cookie)
    return client


# --- Unit: opaque IDs, rotation, expiry, cleanup -----------------------------
def test_session_ids_are_opaque_and_only_digests_are_stored(database):
    sessions = service(database, lambda: NOW)
    ids = [sessions.create(3) for _ in range(50)]
    assert len(set(ids)) == 50
    assert all(len(value) >= 32 for value in ids)
    assert all(PASSWORD not in value and "reader@" not in value
               for value in ids)
    row = database.fetch_one(
        "SELECT session_id_hash FROM user_sessions WHERE user_id = 3")
    assert row is not None
    assert row["session_id_hash"] != ids[0]
    assert len(row["session_id_hash"]) == 64


def test_login_replaces_the_previous_session_id(database):
    sessions = service(database, lambda: NOW)
    first = sessions.create(3)
    second = sessions.replace(first, 3)
    assert second != first
    assert sessions.validate(first) is None
    assert sessions.validate(second).user_id == 3


def test_session_expiry_boundary_and_sliding_window(database):
    current = [NOW]
    sessions = service(database, lambda: current[0])

    sliding = sessions.create(3)
    at_deadline = sessions.create(4)
    current[0] = NOW + timedelta(minutes=29, seconds=59)
    assert sessions.validate(sliding) is not None
    current[0] = NOW + LIFETIME
    assert sessions.validate(at_deadline) is None   # exactly 30 minutes
    assert sessions.validate(sliding) is not None   # extended by activity
    current[0] = NOW + timedelta(minutes=60)
    assert sessions.validate(sliding) is None


def test_unknown_and_revoked_ids_are_rejected(database):
    sessions = service(database, lambda: NOW)
    valid = sessions.create(3)
    assert sessions.validate("not-a-real-session-id") is None
    assert sessions.validate(None) is None
    assert sessions.revoke(valid)
    assert sessions.validate(valid) is None
    assert not sessions.revoke(valid)                 # idempotent


def test_expired_records_are_purged_without_touching_new_ones(database):
    current = [NOW]
    sessions = service(database, lambda: current[0])
    sessions.create(3)
    current[0] = NOW + timedelta(minutes=31)
    assert sessions.purge_expired() == 1
    fresh = sessions.create(3)
    assert sessions.validate(fresh) is not None
    assert sessions.purge_expired() == 0


def test_schema_upgrade_adds_session_registry(tmp_path):
    path = tmp_path / "legacy.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE users (user_id INTEGER PRIMARY KEY, role TEXT,"
        " full_name TEXT, email TEXT, phone TEXT, password_hash TEXT,"
        " status TEXT, failed_logins INTEGER, locked_until TEXT,"
        " must_change_password INTEGER DEFAULT 1);"
        "INSERT INTO users VALUES (2, 'LIBRARIAN', 'Lan', 'l@x.test',"
        " '0900000002', 'h', 'ACTIVE', 0, NULL, 1);")
    conn.close()

    database = Database(path)
    database.initialize(seed=False)
    columns = {row["name"] for row in
               database.fetch_all("PRAGMA table_info(users)")}
    assert "temp_password_issued_at" in columns
    issued = database.fetch_one(
        "SELECT temp_password_issued_at FROM users WHERE user_id = 2")
    assert issued["temp_password_issued_at"] is not None
    names = {row["name"] for row in database.fetch_all(
        "SELECT name FROM sqlite_master WHERE type IN ('table', 'index')")}
    assert {"user_sessions", "idx_session_user", "idx_session_expiry"} <= names


# --- System: cookie lifecycle ------------------------------------------------
def test_login_creates_a_live_server_side_session(client, library_app):
    signin(client, "reader@library.test")
    with client.session_transaction() as flask_session:
        session_id = flask_session[SESSION_ID_KEY]
    assert PASSWORD not in session_id
    record = library_app.session_service.validate(session_id)
    assert record is not None and record.user_id == 3
    assert client.get("/profile").status_code == 200


def test_copied_cookie_is_rejected_after_logout(client, library_app):
    signin(client, "reader@library.test")
    assert client.get("/profile").status_code == 200
    stolen_cookie = cookie_value(client)

    replay = replay_client(library_app, stolen_cookie)
    assert replay.get("/profile").status_code == 200  # valid before logout

    post_form(client, "/", "/signout", {})
    assert client.get("/profile").status_code == 302

    denied = replay.get("/profile")
    assert denied.status_code == 302
    assert "/signin" in denied.headers["Location"]
    assert replay.get("/admin/rules").status_code == 302
    assert "Sign In" in text(replay.get("/"))


def test_revoked_cookie_stays_rejected_after_restart(client, library_app):
    signin(client, "reader@library.test")
    stolen_cookie = cookie_value(client)
    post_form(client, "/", "/signout", {})

    restarted = LibraryApp(AppTestConfig(library_app.config.DATABASE_PATH))
    replay = replay_client(restarted, stolen_cookie)
    denied = replay.get("/profile")
    assert denied.status_code == 302
    assert "/signin" in denied.headers["Location"]


def test_expired_session_is_rejected(client, library_app):
    signin(client, "reader@library.test")
    assert client.get("/profile").status_code == 200
    library_app.session_service.clock = lambda: (
        local_aware(now_aware()) + timedelta(minutes=31))
    denied = client.get("/profile")
    assert denied.status_code == 302
    assert "/signin" in denied.headers["Location"]


def test_unknown_session_id_is_rejected(client):
    with client.session_transaction() as flask_session:
        flask_session[SESSION_ID_KEY] = "unknown-opaque-id"
    denied = client.get("/profile")
    assert denied.status_code == 302
    assert "/signin" in denied.headers["Location"]


def test_tampered_cookie_is_rejected(client, library_app):
    signin(client, "reader@library.test")
    original = cookie_value(client)
    changed = original[:-1] + ("A" if original[-1] != "A" else "B")
    replay = replay_client(library_app, changed)
    denied = replay.get("/profile")
    assert denied.status_code == 302
    assert "/signin" in denied.headers["Location"]


def test_concurrent_sessions_are_independent(client, library_app):
    second = library_app.flask.test_client()
    assert signin(client, "reader@library.test").status_code == 302
    assert signin(second, "reader@library.test").status_code == 302
    assert client.get("/profile").status_code == 200
    assert second.get("/profile").status_code == 200

    post_form(client, "/", "/signout", {})
    assert client.get("/profile").status_code == 302
    assert second.get("/profile").status_code == 200

    post_form(second, "/", "/signout", {})
    assert second.get("/profile").status_code == 302


def test_password_change_rotates_the_session(client, library_app):
    signin(client, "reader@library.test")
    old_cookie = cookie_value(client)
    post_form(client, "/profile", "/profile/password", {
        "current_password": PASSWORD, "new_password": "Changed456",
        "confirmation": "Changed456"})
    assert client.get("/profile").status_code == 200

    replay = replay_client(library_app, old_cookie)
    assert replay.get("/profile").status_code == 302


def test_role_checks_still_apply_after_session_validation(client,
                                                          library_app):
    signin(client, "reader@library.test")
    assert client.get("/admin/rules").status_code == 403

    admin_client = library_app.flask.test_client()
    signin(admin_client, "admin@library.test")
    assert admin_client.get("/admin/rules").status_code == 200


def test_account_lock_still_blocks_a_live_session(client, library_app):
    signin(client, "reader@library.test")
    assert client.get("/profile").status_code == 200
    with library_app.database.transaction() as conn:
        conn.execute("UPDATE users SET status = 'LOCKED' WHERE user_id = 3")
    denied = client.get("/profile")
    assert denied.status_code == 302
    assert "/signin" in denied.headers["Location"]
