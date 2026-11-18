"""System tests for the Guest pages (Section 7.1)."""
import pytest


def html(client, url):
    return client.get(url).get_data(as_text=True)


@pytest.mark.parametrize("url, text", [
    ("/", "New Books"),
    ("/policies", "Library Policies"),
    ("/help", "How to borrow a book"),
    ("/search?q=clean", "Search Results"),
    ("/search?q=", "Search Results"),          # empty keyword
    ("/search?category=Law", "Search Results"),
])
def test_guest_pages_load(client, url, text):
    response = client.get(url)
    assert response.status_code == 200
    assert text in response.get_data(as_text=True)


def test_layout_has_header_and_categories(client):
    page = html(client, "/")
    for text in ["LIBRARY", "Sign In", "Hotline:", "Computer Science",
                 "Children&#39;s books"]:
        assert text in page


def test_home_shows_books_from_database_fr_gst_03(client):
    page = html(client, "/")
    assert "Clean Code" in page
    assert "Robert C. Martin" in page
    assert page.count('class="book-card"') == 5


def test_policies_use_rules_from_database_nfr_mnt_02(client, library_app):
    with library_app.database.transaction() as conn:
        conn.execute("UPDATE system_configs SET config_value = '7'"
                     " WHERE config_key = 'MAX_BOOKS'")
    page = html(client, "/policies")
    assert "Up to 7 books" in page
    assert "5,000 VND per day" in page
    assert "renewed once" in page


def test_search_keeps_keyword_in_header(client):
    assert 'value="clean code"' in html(client, "/search?q=clean+code")


def test_search_keyword_is_escaped_nfr_sec_07(client):
    page = html(client, "/search?q=<script>alert(1)</script>")
    assert "<script>alert(1)</script>" not in page


def test_unknown_page_returns_404(client):
    response = client.get("/does-not-exist")
    page = response.get_data(as_text=True)
    assert response.status_code == 404
    assert "Page Not Found" in page
    assert "Go to Home" in page
    assert "Search Books" not in page


def test_server_error_shows_error_page(library_app):
    app = library_app.flask
    app.config["PROPAGATE_EXCEPTIONS"] = False

    @app.route("/boom")
    def boom():
        raise RuntimeError("test")

    response = app.test_client().get("/boom")
    assert response.status_code == 500
    assert "Something Went Wrong" in response.get_data(as_text=True)


def test_static_files_are_served(client):
    for url in ["/static/css/style.css", "/static/js/main.js",
                "/static/img/banner.jpg"]:
        assert client.get(url).status_code == 200
