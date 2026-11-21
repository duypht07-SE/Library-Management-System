"""Back up (FR-ADM-06) and restore (FR-ADM-07) the database."""
import io

import pytest

from business.backup_service import BackupService
from common.exceptions import ValidationError
from data.database import is_sqlite_backup
from data.repositories import UserRepository
from web_helpers import post_form, signin, text


@pytest.fixture
def backups(database, tmp_path):
    return BackupService(database, tmp_path / "backups")


@pytest.fixture
def admin(database):
    return UserRepository(database).find_by_id(1)


def count_books(database):
    return database.fetch_one("SELECT COUNT(*) AS n FROM books")["n"]


def test_backup_then_restore_brings_data_back(backups, admin, database):
    backup = backups.create(admin)
    assert is_sqlite_backup(backups.path_of(backup.name))
    with database.transaction() as conn:
        conn.execute("INSERT INTO books (isbn, ddc_code, title, author,"
                     " category) VALUES ('X1', '000', 'New', 'A', 'Other')")
    assert count_books(database) == 21
    safety = backups.restore(admin, backup.name)
    assert count_books(database) == 20
    assert safety.name.endswith("-auto.db")    # undo point
    backups.restore(admin, safety.name)
    assert count_books(database) == 21


def test_backups_are_listed_newest_first(backups, admin):
    first = backups.create(admin)
    second = backups.create(admin)
    assert [b.name for b in backups.backups()] == [second.name, first.name]


@pytest.mark.parametrize("name", [
    "../library.db", "library.db", "library-20261121-090000.db",
    "library-20261121-090000.db; rm -rf /", ""])
def test_unknown_or_unsafe_names_are_rejected(backups, admin, name):
    with pytest.raises(ValidationError):
        backups.restore(admin, name)


@pytest.mark.parametrize("data", [b"", b"not a database",
                                  b"SQLite format 3\x00" + b"0" * 100],
                         ids=["empty", "text", "broken-sqlite"])
def test_invalid_upload_is_rejected(backups, admin, data, database):
    with pytest.raises(ValidationError):
        backups.restore_upload(admin, data)
    assert count_books(database) == 20


def test_restore_upload(backups, admin, database):
    data = backups.path_of(backups.create(admin).name).read_bytes()
    with database.transaction() as conn:
        conn.execute("DELETE FROM notifications")
    backups.restore_upload(admin, data)
    assert database.fetch_one(
        "SELECT COUNT(*) AS n FROM notifications")["n"] == 2


def test_backup_pages(client, library_app):
    signin(client, "admin@library.test")
    page = post_form(client, "/admin/backups", "/admin/backups")
    assert "Backup created" in text(page)
    name = library_app.backup_service.backups()[0].name
    download = client.get(f"/admin/backups/{name}/download")
    assert download.data.startswith(b"SQLite format 3")
    restored = post_form(client, "/admin/backups",
                         f"/admin/backups/{name}/restore")
    assert "Database restored from" in text(restored)
    bad = post_form(client, "/admin/backups", "/admin/backups/upload",
                    {"file": (io.BytesIO(b"junk"), "x.db")},
                    content_type="multipart/form-data")
    assert "not a library database backup" in text(bad)


def test_backup_pages_are_admin_only(client):
    signin(client, "librarian@library.test")
    assert client.get("/admin/backups").status_code == 403
