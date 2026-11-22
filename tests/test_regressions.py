"""Regression tests for the defects found in release testing (1.0.0)."""
import sqlite3

from data.database import Database
from web_helpers import post_form, signin, text


def test_bug1_check_in_shows_the_real_error(client):
    """Unknown barcode showed 'Enter valid numbers...' (ValidationError
    is a ValueError and was caught by the wrong except block)."""
    signin(client, "librarian@library.test")
    page = post_form(client, "/librarian/checkin", "/librarian/checkin",
                     {"barcode": "LIB-99999", "condition": "INTACT"})
    assert "Enter valid numbers" not in text(page)


def test_bug1_letters_in_fine_amount_still_get_number_message(client):
    signin(client, "librarian@library.test")
    page = post_form(client, "/librarian/checkin", "/librarian/checkin",
                     {"barcode": "LIB-00011", "condition": "DAMAGED",
                      "damage_amount": "abc"})
    assert "Enter valid numbers" in text(page)


def test_bug2_reader_cannot_reserve_a_book_they_borrow(client):
    """reader@ borrows copy LIB-00011 of book 1 (loan 1)."""
    signin(client, "reader@library.test")
    page = post_form(client, "/books/1", "/books/1/reserve")
    assert "already borrowing this book" in text(page)


def test_reserve_button_hidden_for_own_loan_or_reservation(client):
    """The button led to the D2 error; now a note is shown instead."""
    signin(client, "reader@library.test")
    page = text(client.get("/books/1"))            # borrows LIB-00011
    assert "You are borrowing this book" in page
    assert "Reserve Book" not in page
    post_form(client, "/books/1", "/signout")
    signin(client, "reader3@library.test")
    assert "Reserve Book" in text(client.get("/books/5"))
    post_form(client, "/books/5", "/books/5/reserve")
    page = text(client.get("/books/5"))
    assert "You have already reserved this book" in page
    assert "Reserve Book" not in page


def test_old_database_is_upgraded(tmp_path):
    """A 0.4.0 database gets the 1.0.0 tables and columns on start."""
    path = tmp_path / "old.db"
    conn = sqlite3.connect(path)
    conn.executescript(
        "CREATE TABLE users (user_id INTEGER PRIMARY KEY, role TEXT,"
        " card_code TEXT, full_name TEXT, email TEXT, phone TEXT,"
        " password_hash TEXT, status TEXT, failed_logins INTEGER,"
        " locked_until TEXT);"
        "INSERT INTO users VALUES (2, 'LIBRARIAN', NULL, 'Lan',"
        " 'l@x.test', '0900000002', 'h', 'ACTIVE', 0, NULL);")
    conn.close()
    database = Database(path)
    database.initialize(seed=False)
    row = database.fetch_one("SELECT staff_role_id, must_change_password"
                             " FROM users WHERE user_id = 2")
    assert row["staff_role_id"] == 1 and row["must_change_password"] == 0
    tables = {r["name"] for r in database.fetch_all(
        "SELECT name FROM sqlite_master WHERE type = 'table'")}
    assert {"staff_roles", "role_permissions", "ebooks", "audit_logs",
            "password_reset_requests"} <= tables


def test_ui2_check_out_errors_say_what_to_do_nfr_usa_03(client):
    """Errors name the problem and the next step (NFR-USA-03)."""
    signin(client, "librarian@library.test")
    cases = [
        ("RD-0001", "LIB-00071", "Reader has unpaid fines of 15,000 VND. "
         "Record the cash payment on the Fines page first."),
        ("RD-0002", "LIB-00071", "Check them in before lending"),
        ("RD-0003", "LIB-00071", "Reader card is locked. Approve or unlock"),
        ("RD-9999", "LIB-00071", "Check the card code and scan it again"),
        ("RD-0004", "LIB-99999", "Check the barcode and scan it again"),
    ]
    for card, barcode, message in cases:
        page = post_form(client, "/librarian/checkout", "/librarian/checkout",
                         {"card_code": card, "barcode": barcode})
        assert message in text(page), card


def test_ui4_temporary_password_has_no_look_alike_characters():
    from business.password_reset_service import make_temporary_password

    for _ in range(200):
        assert not set(make_temporary_password()) & set("0Oo1lI")
