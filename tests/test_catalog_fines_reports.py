"""System tests for books, fines, and reports (0.3.0)."""
import re

import pytest

from models import Fine, FineReason

PASSWORD = "Library@123"
TOKEN_PATTERN = re.compile(r'name="csrf_token"\s+value="([^"]+)"')


def csrf_token(client, url: str) -> str:
    response = client.get(url)
    match = TOKEN_PATTERN.search(response.get_data(as_text=True))
    assert match, f"no CSRF token on {url}"
    return match.group(1)


def sign_in(client, email: str) -> None:
    client.post("/signin", data={
        "csrf_token": csrf_token(client, "/signin"),
        "email": email,
        "password": PASSWORD,
    })


def post(client, token_url: str, url: str, data: dict):
    payload = {"csrf_token": csrf_token(client, token_url), **data}
    return client.post(url, data=payload)


@pytest.mark.parametrize(("query", "expected"), [
    ("q=Software+Engineering", "Software Engineering"),
    ("q=Robert+C.+Martin", "Clean Code"),
    ("q=9780132350884", "Clean Code"),
    ("category=Law", "Civil Law Basics"),
])
def test_guest_searches_books_by_title_author_isbn_or_category(client, query,
                                                          expected):
    response = client.get(f"/search?{query}")
    assert response.status_code == 200
    assert expected in response.get_data(as_text=True)


def test_book_details_show_derived_available_copy_count(client):
    page = client.get("/books/2").get_data(as_text=True)
    assert "Software Engineering" in page
    assert "Available copies" in page
    assert "<dd>1</dd>" in page
    assert "LIB-00022" in page


def test_librarian_can_add_edit_classify_and_retire_book_and_copy(
        client, library_app):
    sign_in(client, "librarian@library.test")
    book_form = {
        "isbn": "9780000000001", "ddc_code": "005.2",
        "title": "New Catalog Book", "author": "A. Author",
        "category": "Computer Science",
    }
    response = post(client, "/librarian/books", "/librarian/books",
                    book_form)
    assert response.status_code == 302
    book = library_app.books.search("9780000000001")[0]

    response = post(
        client, "/librarian/books", f"/librarian/books/{book.book_id}/copies",
        {"barcode": "NEW-COPY-1", "shelf_location": "B01-1"})
    assert response.status_code == 302
    copy = next(c for c in library_app.books.find_copies(book.book_id)
                if c.barcode == "NEW-COPY-1")

    edited = {**book_form, "title": "Updated Catalog Book",
              "ddc_code": "005.3", "category": "Mathematics"}
    response = post(
        client, f"/librarian/books/{book.book_id}/edit",
        f"/librarian/books/{book.book_id}/edit", edited)
    assert response.status_code == 302

    response = post(
        client, "/librarian/books",
        f"/librarian/copies/{copy.copy_id}/edit",
        {"book_id": str(book.book_id), "barcode": "NEW-COPY-1",
         "shelf_location": "B02-4"})
    assert response.status_code == 302

    response = post(
        client, "/librarian/books",
        f"/librarian/copies/{copy.copy_id}/retire", {})
    assert response.status_code == 302

    updated = library_app.books.find_by_id(book.book_id)
    retired = next(c for c in updated.copies if c.copy_id == copy.copy_id)
    assert updated.title == "Updated Catalog Book"
    assert updated.ddc_code == "005.3"
    assert updated.category == "Mathematics"
    assert retired.shelf_location == "B02-4"
    assert retired.status.value == "CANCELED"


def test_retiring_a_borrowed_copy_is_rejected(client, library_app):
    sign_in(client, "librarian@library.test")
    response = post(
        client, "/librarian/books", "/librarian/copies/1/retire", {})
    assert response.status_code == 302
    copy = next(c for c in library_app.books.find_copies(1)
                if c.copy_id == 1)
    assert copy.status.value == "BORROWED"


def test_duplicate_isbn_and_barcode_are_not_saved(client):
    sign_in(client, "librarian@library.test")
    existing_book = {
        "isbn": "9780132350884", "ddc_code": "005.1",
        "title": "Duplicate ISBN", "author": "A. Author",
        "category": "Computer Science",
    }
    response = post(client, "/librarian/books", "/librarian/books",
                    existing_book)
    assert "ISBN already exists" in response.get_data(as_text=True)

    response = post(
        client, "/librarian/books", "/librarian/books/1/copies",
        {"barcode": "LIB-00011", "shelf_location": "B01-1"})
    response = client.get(response.location)
    assert "Barcode already exists" in response.get_data(as_text=True)


def test_reader_only_sees_their_own_fines(client, library_app):
    library_app.fines.save(Fine(None, 2, FineReason.DAMAGED, 98765))
    sign_in(client, "reader@library.test")
    response = client.get("/fines")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "15,000 VND" in page
    assert "98,765 VND" not in page


def test_librarian_records_fine_and_cash_payment(client, library_app):
    sign_in(client, "librarian@library.test")
    response = post(
        client, "/librarian/fines", "/librarian/fines",
        {"action": "fine", "borrow_id": "3", "reason": "DAMAGED",
         "amount": "25000"})
    assert "Fine recorded" in response.get_data(as_text=True)
    fine = library_app.fines.find_for_reader(3)
    recorded = next(f for f in fine if f.amount == 25000)

    response = post(
        client, "/librarian/fines", "/librarian/fines",
        {"action": "payment", "fine_id": str(recorded.fine_id)})
    assert "Cash payment recorded" in response.get_data(as_text=True)
    paid = library_app.fines.find_by_id(recorded.fine_id)
    assert paid.is_paid is True
    assert paid.paid_at is not None

    response = post(
        client, "/librarian/fines", "/librarian/fines",
        {"action": "payment", "fine_id": str(recorded.fine_id)})
    assert "already paid" in response.get_data(as_text=True)


def test_return_service_creates_separate_late_and_damage_fines(library_app):
    fines = library_app.fine_service.create_return_fines(
        borrow_id=6, days_late=2, daily_rate=5000,
        condition="DAMAGED", damage_amount=20000)
    assert [(fine.reason, fine.amount) for fine in fines] == [
        (FineReason.LATE_RETURN, 10000), (FineReason.DAMAGED, 20000)]


def test_return_service_supports_lost_fine_and_rejects_invalid_amount(
        library_app):
    fines = library_app.fine_service.create_return_fines(
        borrow_id=6, days_late=0, daily_rate=5000,
        condition="LOST", damage_amount=40000)
    assert [(fine.reason, fine.amount) for fine in fines] == [
        (FineReason.LOST, 40000)]
    with pytest.raises(ValueError, match="greater than 0"):
        library_app.fine_service.create_return_fines(
            borrow_id=6, days_late=0, daily_rate=5000,
            condition="DAMAGED", damage_amount=0)


def test_administrator_views_monthly_yearly_reports_and_csv(client):
    sign_in(client, "admin@library.test")
    monthly = client.get("/admin/reports?period=month&value=2026-11")
    page = monthly.get_data(as_text=True)
    assert monthly.status_code == 200
    for label in ["Borrowings", "Overdue loans", "Fines collected",
                  "Book titles", "Available copies", "New Readers"]:
        assert label in page

    yearly = client.get("/admin/reports?period=year&value=2026")
    assert "2026" in yearly.get_data(as_text=True)

    export = client.get(
        "/admin/reports?period=month&value=2026-11&format=csv")
    assert export.status_code == 200
    assert export.mimetype == "text/csv"
    assert "Fines collected (VND)" in export.get_data(as_text=True)


@pytest.mark.parametrize(("email", "url"), [
    ("reader@library.test", "/librarian/books"),
    ("librarian@library.test", "/admin/reports"),
    ("admin@library.test", "/fines"),
])
def test_0_3_pages_enforce_role_access(client, email, url):
    sign_in(client, email)
    assert client.get(url).status_code == 403


def test_overdue_by_due_period_survives_return(library_app, monkeypatch):
    from datetime import datetime
    from data.repositories import report_repository

    monkeypatch.setattr(report_repository, "now", lambda: datetime(2010, 2, 15))
    rows = [
        ("2010-02-01 00:00:00", "2010-03-01 00:00:00", "RETURNED"),
        ("2010-02-02 00:00:00", None, "BORROWED"),
        ("2010-02-03 00:00:00", "2010-02-03 00:00:00", "RETURNED"),
        ("2010-02-15 00:00:00", None, "BORROWED"),
        ("2010-03-01 00:00:00", "2010-03-02 00:00:00", "RETURNED"),
    ]
    with library_app.database.transaction() as conn:
        conn.executemany(
            "INSERT INTO borrow_records (reader_id,copy_id,librarian_id,"
            "borrow_date,due_date,return_date,status) "
            "VALUES (3,1,2,'2010-01-01',?,?,?)", rows)
    report = library_app.reports.monthly("2010-02-01 00:00:00",
                                         "2010-03-01 00:00:00")
    assert report["overdue"] == 2


def test_tc40_last_usable_copy_cancels_queue_and_notifies(client, library_app):
    db = library_app.database
    sign_in(client, "librarian@library.test")
    with db.transaction() as conn:
        conn.execute("UPDATE book_copies SET status='CANCELED'"
                     " WHERE copy_id=40")
        conn.executemany(
            "INSERT INTO reservations (reader_id,book_id,reserve_date) "
            "VALUES (?,20,CURRENT_TIMESTAMP)", [(3,), (7,)])
        last_notice = conn.execute(
            "SELECT MAX(notification_id) FROM notifications").fetchone()[0]
    response = post(client, "/librarian/books",
                    "/librarian/copies/20/retire", {})
    assert response.status_code == 302
    copy_status = db.fetch_one(
        "SELECT status FROM book_copies WHERE copy_id=20")[0]
    assert copy_status == "CANCELED"
    queue = db.fetch_all("SELECT reader_id,status FROM reservations"
                         " WHERE book_id=20 ORDER BY reader_id")
    assert [tuple(row) for row in queue] == [(3, "CANCELED"), (7, "CANCELED")]
    notices = db.fetch_all("SELECT reader_id,message FROM notifications "
                           "WHERE notification_id>? ORDER BY reader_id",
                           (last_notice,))
    assert [row["reader_id"] for row in notices] == [3, 7]
    assert all("reservation was canceled" in row["message"] for row in notices)
    other = db.fetch_one(
        "SELECT status FROM reservations WHERE reservation_id=2")[0]
    assert other == "WAITING"


def test_search_at_100000_titles(client, library_app):
    from time import perf_counter

    db = library_app.database
    missing = 100000 - library_app.books.book_count()
    with db.transaction() as conn:
        conn.executemany(
            "INSERT INTO books (isbn,ddc_code,title,author,category) "
            "VALUES (?, '001', ?, 'Scale Author', 'Other')",
            ((f"load-{i}", f"Scale {i:06d}") for i in range(missing)))
        conn.execute("INSERT INTO book_copies (book_id,barcode,shelf_location) "
                     "SELECT book_id,isbn,'A' FROM books"
                     " WHERE isbn LIKE 'load-%'")
    assert library_app.books.book_count() == 100000
    for query, expected in [
        ("q=Scale&category=Other", "Scale 000000"),
        ("q=Scale&category=Other&page=2", "Scale 000025"),
        (f"q=load-{missing-1}", f"Scale {missing-1:06d}"),
        ("q=NoSuchTitle", "No matching books"),
    ]:
        start = perf_counter()
        response = client.get("/search?" + query)
        html = response.get_data(as_text=True)
        elapsed = perf_counter() - start
        print(f"{query}: {elapsed:.3f}s")
        assert response.status_code == 200 and expected in html
        assert elapsed <= 2.0
        if "category" in query:
            assert html.count("1 available") == 25
            assert 'rel="next"' in html and "category=Other" in html
        if "page=2" in query:
            assert "Scale 000000" not in html and 'rel="prev"' in html
