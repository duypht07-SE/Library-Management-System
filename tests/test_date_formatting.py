from datetime import date, datetime
import re


def test_date_vn_formats_datetime_text_date_and_empty_values(library_app):
    date_vn = library_app.flask.jinja_env.filters["date_vn"]

    assert date_vn(datetime(2026, 11, 16, 10, 5)) == "16/11/2026"
    assert date_vn("2026-11-16 10:05:00") == "16/11/2026"
    assert date_vn("2026-11-16T10:05:00", True) == "16/11/2026 10:05"
    assert date_vn(date(2026, 11, 16)) == "16/11/2026"
    assert date_vn(None) == ""
    assert date_vn("") == ""
    assert date_vn("not a date") == ""


def test_my_books_displays_dates_in_vietnamese_format(client):
    token_page = client.get("/signin").get_data(as_text=True)
    token = re.search(r'name="csrf_token"\s+value="([^"]+)"', token_page)
    assert token
    client.post("/signin", data={
        "csrf_token": token.group(1),
        "email": "reader@library.test",
        "password": "Library@123",
    })
    page = client.get("/my-books").get_data(as_text=True)

    assert "Borrow date" in page
    assert re.search(r"\b\d{2}/\d{2}/\d{4}\b", page)
    assert "2026-11-" not in page
