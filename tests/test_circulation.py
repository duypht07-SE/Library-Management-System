import re
from datetime import datetime, timedelta

import pytest

from common.exceptions import ValidationError
from models import (Book, BookCopy, BorrowStatus, CopyCondition, CopyStatus,
                    FineReason, Librarian, Reader, ReservationStatus,
                    UserStatus)

PASSWORD = "Library@123"
TOKEN_PATTERN = re.compile(r'name="csrf_token"\s+value="([^"]+)"')
NOW = datetime(2026, 11, 19, 10, 0, 0)


def csrf_token(client, url: str) -> str:
    match = TOKEN_PATTERN.search(client.get(url).get_data(as_text=True))
    assert match
    return match.group(1)


def sign_in(client, email: str) -> None:
    client.post("/signin", data={
        "csrf_token": csrf_token(client, "/signin"),
        "email": email,
        "password": PASSWORD,
    })


def post(client, token_url: str, url: str, data: dict,
         follow_redirects: bool = False):
    payload = {"csrf_token": csrf_token(client, token_url), **data}
    return client.post(url, data=payload, follow_redirects=follow_redirects)


def test_model_methods():
    reader = Reader(3, "An", "an@test", "0900", "h", UserStatus.ACTIVE,
                    card_code="RD-0001")
    librarian = Librarian(2, "Lan", "lan@test", "0901", "h", UserStatus.ACTIVE)
    copy = BookCopy(10, 5, "LIB-00051", "A05-1", CopyStatus.AVAILABLE)

    rec = librarian.check_out(copy, reader.user_id, NOW, 14)
    assert copy.status == CopyStatus.BORROWED
    assert rec.due_date == NOW + timedelta(days=14)
    assert reader.view_borrow_history([rec]) == [rec]
    assert reader.request_renewal(rec, 1, 14) is True
    assert reader.request_renewal(rec, 1, 14) is False

    book = Book(5, "isbn", "005", "Java", "Author", "CS", copies=[copy])
    assert reader.reserve_book(book, NOW).status == ReservationStatus.WAITING

    librarian.check_in(copy, rec, CopyCondition.INTACT, NOW, has_waiting=True)
    assert rec.status == BorrowStatus.RETURNED
    assert copy.status == CopyStatus.RESERVED


def test_checkout_available_copy(client, library_app):
    sign_in(client, "librarian@library.test")
    res = post(client, "/librarian/checkout", "/librarian/checkout",
               {"card_code": "RD-0004", "barcode": "LIB-00061"})
    assert res.status_code == 302
    copy = next(c for c in library_app.books.find_copies(6)
                if c.barcode == "LIB-00061")
    assert copy.status == CopyStatus.BORROWED


def test_checkout_ready_reservation(library_app):
    librarian = library_app.users.find_by_id(2)
    with library_app.database.transaction() as conn:
        conn.execute(
            "UPDATE fines SET is_paid = 1, paid_at = ? WHERE fine_id = 1",
            (NOW.isoformat(sep=" "),))
    rec = library_app.circulation_service.check_out(
        librarian, "RD-0001", "LIB-00052", at=NOW)
    assert rec.borrow_id is not None
    assert (library_app.circulation.find_reservation_by_id(1).status
            == ReservationStatus.COMPLETED)


def test_checkout_validation_rules(library_app):
    librarian = library_app.users.find_by_id(2)
    with pytest.raises(ValidationError, match="unpaid fines"):
        library_app.circulation_service.check_out(
            librarian, "RD-0001", "LIB-00061", at=NOW)
    with pytest.raises(ValidationError, match="overdue"):
        library_app.circulation_service.check_out(
            librarian, "RD-0002", "LIB-00061", at=NOW)
    with pytest.raises(ValidationError, match="not active"):
        library_app.circulation_service.check_out(
            librarian, "RD-0003", "LIB-00061", at=NOW)
    with pytest.raises(ValidationError, match="another reader"):
        library_app.circulation_service.check_out(
            librarian, "RD-0004", "LIB-00052", at=NOW)
    with library_app.database.transaction() as conn:
        conn.execute(
            "UPDATE system_configs SET config_value = '1' "
            "WHERE config_key = 'MAX_BOOKS'")
    with pytest.raises(ValidationError, match="limit of 1"):
        library_app.circulation_service.check_out(
            librarian, "RD-0004", "LIB-00061", at=NOW)


def test_checkin_intact_promotes_waiting_queue(library_app):
    librarian = library_app.users.find_by_id(2)
    rec, fines = library_app.circulation_service.check_in(
        librarian, "INTACT", barcode="LIB-00011", at=NOW)
    assert rec.status == BorrowStatus.RETURNED
    assert fines == []
    copy = next(c for c in library_app.books.find_copies(1) if c.copy_id == 1)
    assert copy.status == CopyStatus.RESERVED
    res = library_app.circulation.find_reservation_by_id(2)
    assert res.status == ReservationStatus.READY and res.copy_id == 1
    assert any("ready for pickup" in n.message
               for n in library_app.notifications.find_for_reader(4))


def test_checkin_intact_without_queue_sets_available(library_app):
    librarian = library_app.users.find_by_id(2)
    rec, fines = library_app.circulation_service.check_in(
        librarian, "INTACT", barcode="LIB-00051", at=NOW)
    assert rec.status == BorrowStatus.RETURNED and fines == []
    copy = next(c for c in library_app.books.find_copies(5) if c.copy_id == 5)
    assert copy.status == CopyStatus.AVAILABLE


def test_checkin_late_and_damaged_creates_two_fines(library_app):
    librarian = library_app.users.find_by_id(2)
    rec, fines = library_app.circulation_service.check_in(
        librarian, "DAMAGED", borrow_id=2, damage_amount=30000, at=NOW)
    assert rec.return_condition == CopyCondition.DAMAGED
    assert {f.reason for f in fines} == {
        FineReason.LATE_RETURN, FineReason.DAMAGED}
    copy = next(c for c in library_app.books.find_copies(2) if c.copy_id == 2)
    assert copy.status == CopyStatus.CANCELED


def test_checkin_lost_last_copy_cancels_waiting_queue(library_app):
    librarian = library_app.users.find_by_id(2)
    library_app.circulation_service.check_in(
        librarian, "DAMAGED", borrow_id=6, damage_amount=20000, at=NOW)
    rec, fines = library_app.circulation_service.check_in(
        librarian, "LOST", borrow_id=1, damage_amount=50000, at=NOW)
    assert rec.return_condition == CopyCondition.LOST
    assert any(f.reason == FineReason.LOST and f.amount == 50000 for f in fines)
    assert (library_app.circulation.find_reservation_by_id(2).status
            == ReservationStatus.CANCELED)
    assert any("no usable copy remains" in n.message
               for n in library_app.notifications.find_for_reader(4))


def test_checkin_invalid_amount_rolls_back(library_app):
    librarian = library_app.users.find_by_id(2)
    with pytest.raises(ValidationError, match="greater than 0"):
        library_app.circulation_service.check_in(
            librarian, "DAMAGED", barcode="LIB-00051",
            damage_amount=0, at=NOW)
    copy = next(c for c in library_app.books.find_copies(5) if c.copy_id == 5)
    assert copy.status == CopyStatus.BORROWED


def test_reserve_and_cancel_via_web(client, library_app):
    # book 5: copy 5 is on loan and copy 25 is held for another Reader
    sign_in(client, "reader3@library.test")
    assert "Reserve Book" in client.get("/books/5").get_data(as_text=True)

    res = post(client, "/books/5", "/books/5/reserve", {},
               follow_redirects=True)
    assert "Book reserved" in res.get_data(as_text=True)

    rows = library_app.circulation.find_reservations_for_reader(7)
    created = next(r for r in rows if r["book_id"] == 5)
    assert created["status"] == "WAITING"

    dup = post(client, "/books/5", "/books/5/reserve", {},
               follow_redirects=True)
    assert "already have an active reservation" in dup.get_data(as_text=True)

    cancel = post(
        client, "/my-books",
        f"/reservations/{created['reservation_id']}/cancel", {},
        follow_redirects=True)
    assert "Reservation canceled" in cancel.get_data(as_text=True)
    assert (library_app.circulation.find_reservation_by_id(
        created["reservation_id"]).status == ReservationStatus.CANCELED)


def test_reserve_rejected_if_available_and_cancel_ready_releases_copy(
        library_app):
    reader3 = library_app.users.find_by_id(7)
    with pytest.raises(ValidationError, match="available copies"):
        library_app.circulation_service.reserve_book(reader3, 6, at=NOW)

    reader1 = library_app.users.find_by_id(3)
    library_app.circulation_service.cancel_reservation(reader1, 1, at=NOW)
    copy = next(c for c in library_app.books.find_copies(5) if c.copy_id == 25)
    assert copy.status == CopyStatus.AVAILABLE


def test_renewal_and_limits(library_app):
    librarian = library_app.users.find_by_id(2)
    reader3 = library_app.users.find_by_id(7)
    loan = library_app.circulation_service.check_out(
        librarian, "RD-0004", "LIB-00061", at=NOW)

    renewed = library_app.circulation_service.request_renewal(
        reader3, loan.borrow_id, at=NOW + timedelta(days=2))
    assert renewed.renew_count == 1
    assert renewed.due_date == loan.due_date + timedelta(days=14)

    with pytest.raises(ValidationError, match="limit"):
        library_app.circulation_service.request_renewal(
            reader3, loan.borrow_id, at=NOW + timedelta(days=3))
    with pytest.raises(ValidationError, match="waiting"):
        library_app.circulation_service.request_renewal(reader3, 6, at=NOW)
    with pytest.raises(ValidationError, match="unpaid fines"):
        library_app.circulation_service.request_renewal(
            library_app.users.find_by_id(3), 1, at=NOW)
    with pytest.raises(ValidationError, match="overdue"):
        library_app.circulation_service.request_renewal(
            library_app.users.find_by_id(4), 5, at=NOW)


def test_daily_job_overdue_due_soon_and_hold_expiry(library_app):
    with library_app.database.transaction() as conn:
        conn.execute(
            "UPDATE borrow_records SET due_date = ? WHERE borrow_id = 1",
            ((NOW - timedelta(days=1)).isoformat(sep=" "),))
        conn.execute(
            "UPDATE borrow_records SET due_date = ? WHERE borrow_id = 6",
            ((NOW + timedelta(days=2)).isoformat(sep=" "),))
        conn.execute(
            "UPDATE reservations SET expire_date = ? WHERE reservation_id = 1",
            ((NOW - timedelta(hours=2)).isoformat(sep=" "),))
        conn.execute(
            "INSERT INTO reservations (reader_id, book_id, copy_id, "
            "reserve_date, expire_date, status) "
            "VALUES (7, 5, NULL, ?, NULL, 'WAITING')",
            ((NOW - timedelta(days=2)).isoformat(sep=" "),))

    summary = library_app.daily_job_service.run(at=NOW)
    assert summary["marked_overdue"] == 1
    assert summary["due_soon_notified"] == 1
    assert summary["expired_holds"] == 1
    assert summary["promoted_holds"] == 1
    loan = library_app.circulation.find_loan_by_id(1)
    assert loan.status == BorrowStatus.OVERDUE
    assert (library_app.circulation.find_reservation_by_id(1).status
            == ReservationStatus.CANCELED)
    assert library_app.daily_job_service.run(at=NOW)["due_soon_notified"] == 0


def test_my_books_notifications_and_access(client):
    sign_in(client, "reader@library.test")
    page = client.get("/my-books").get_data(as_text=True)
    assert "Clean Code" in page and "15,000 VND" in page
    page = client.get("/notifications").get_data(as_text=True)
    assert "ready for pickup" in page
    assert client.get("/librarian/checkout").status_code == 403
    assert client.get("/librarian/checkin").status_code == 403


@pytest.mark.parametrize(("email", "url"), [
    ("librarian@library.test", "/my-books"),
    ("librarian@library.test", "/notifications"),
    ("admin@library.test", "/librarian/checkout"),
    ("admin@library.test", "/librarian/checkin"),
    ("admin@library.test", "/my-books"),
])
def test_role_access_0_4(client, email, url):
    sign_in(client, email)
    assert client.get(url).status_code == 403


def test_csrf_required_0_4(client):
    sign_in(client, "librarian@library.test")
    assert client.post("/librarian/checkout", data={
        "card_code": "RD-0004", "barcode": "LIB-00061"}).status_code == 400
    assert client.post("/librarian/checkin", data={
        "barcode": "LIB-00051", "condition": "INTACT"}).status_code == 400
