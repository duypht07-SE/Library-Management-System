"""Shared helpers for the system tests that drive the pages."""
import io
import re
import zipfile

PASSWORD = "Library@123"
TOKEN_PATTERN = re.compile(r'name="csrf_token"\s+value="([^"]+)"')
PDF = b"%PDF-1.4\n1 0 obj << >> endobj\ntrailer << >>\n%%EOF\n"


def epub_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as book:
        book.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip")
        book.writestr("META-INF/container.xml", "<container/>")
    return buffer.getvalue()


def csrf_token(client, url: str) -> str:
    page = client.get(url).get_data(as_text=True)
    match = TOKEN_PATTERN.search(page)
    assert match, f"no CSRF token on {url}"
    return match.group(1)


def signin(client, email: str, password: str = PASSWORD):
    return client.post("/signin", data={
        "csrf_token": csrf_token(client, "/signin"),
        "email": email, "password": password})


def post_form(client, token_url: str, action: str, data: dict | None = None,
              follow_redirects: bool = True, **kwargs):
    payload = {"csrf_token": csrf_token(client, token_url)}
    payload.update(data or {})
    return client.post(action, data=payload,
                       follow_redirects=follow_redirects, **kwargs)


def text(response) -> str:
    return response.get_data(as_text=True)
