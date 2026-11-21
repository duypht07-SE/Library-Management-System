"""E-books: manage (FR-LIB-14) and read or download (FR-RDR-07)."""
import io

import pytest

from business.ebook_service import MAX_EBOOK_BYTES, EbookService
from common.exceptions import ValidationError
from data.repositories import BookRepository, EbookRepository, UserRepository
from models import Ebook, EbookFormat
from web_helpers import PDF, epub_bytes, post_form, signin, text


# --- Unit: Ebook.detect_format ------------------------------------------------
@pytest.mark.parametrize("data, expected", [
    (PDF, EbookFormat.PDF),
    (epub_bytes(), EbookFormat.EPUB),
    (b"PK\x03\x04" + b"0" * 60, None),          # a zip that is not EPUB
    (b"\x89PNG\r\n\x1a\n", None),
    (b"", None),
], ids=["pdf", "epub", "zip", "png", "empty"])
def test_detect_format(data, expected):
    assert Ebook.detect_format(data) == expected


def test_only_pdf_can_be_read_online():
    assert EbookFormat.PDF.value == "PDF"
    pdf = Ebook(1, 1, "T", EbookFormat.PDF, "a.pdf", 10, 2, None)
    epub = Ebook(2, 1, "T", EbookFormat.EPUB, "a.epub", 10, 2, None)
    assert pdf.can_read_online and not epub.can_read_online


# --- Component: EbookService ---------------------------------------------
@pytest.fixture
def service(database, tmp_path):
    return EbookService(EbookRepository(database), BookRepository(database),
                        tmp_path / "ebooks")


@pytest.fixture
def librarian(database):
    return UserRepository(database).find_by_id(2)


def test_upload_update_remove(service, librarian):
    ebook = service.upload(librarian, 1, "Clean Code (PDF)", PDF)
    path = service.storage_dir / ebook.file_path
    assert path.read_bytes() == PDF
    updated = service.update(librarian, ebook.ebook_id, "Clean Code EPUB",
                             epub_bytes())
    assert updated.file_format == EbookFormat.EPUB
    assert not path.exists()                   # the old file is removed
    service.remove(librarian, ebook.ebook_id)
    assert service.for_book(1) == []
    assert list(service.storage_dir.iterdir()) == []


@pytest.mark.parametrize("data, message", [
    (b"", "Choose a PDF or EPUB"),
    (b"plain text", "real PDF or EPUB"),
    (b"%PDF-" + b"0" * MAX_EBOOK_BYTES, "20 MB or smaller"),
], ids=["empty", "not-pdf", "20mb-plus-5-bytes"])
def test_invalid_upload(service, librarian, data, message):
    with pytest.raises(ValidationError, match=message):
        service.upload(librarian, 1, "Title", data)


def test_largest_allowed_file(service, librarian):
    data = b"%PDF-" + b"0" * (MAX_EBOOK_BYTES - 5)   # exactly 20 MB
    assert service.upload(librarian, 1, "Big", data).file_size == \
        MAX_EBOOK_BYTES


def test_upload_for_unknown_book(service, librarian):
    with pytest.raises(ValidationError, match="Book was not found"):
        service.upload(librarian, 999, "Title", PDF)


def test_pending_reader_cannot_open_file(service, librarian, database):
    ebook = service.upload(librarian, 1, "T", PDF)
    pending = UserRepository(database).find_by_id(5)
    with pytest.raises(ValidationError):
        service.file_for(pending, ebook.ebook_id)


# --- System --------------------------------------------------------------
def upload(client, book_id=1, data=PDF, name="book.pdf"):
    return post_form(client, f"/librarian/books/{book_id}/edit",
                     f"/librarian/books/{book_id}/ebooks",
                     {"title": "Clean Code e-book",
                      "file": (io.BytesIO(data), name)},
                     content_type="multipart/form-data")


def test_librarian_uploads_and_reader_reads(client, library_app):
    signin(client, "librarian@library.test")
    assert "E-book uploaded" in text(upload(client))
    ebook = library_app.ebook_service.for_book(1)[0]
    post_form(client, "/librarian/books", "/signout")

    assert "Sign in to read" in text(client.get("/books/1"))
    signin(client, "reader@library.test")
    assert "Clean Code e-book" in text(client.get("/ebooks/"))
    read = client.get(f"/ebooks/{ebook.ebook_id}/read")
    assert read.status_code == 200
    assert read.mimetype == "application/pdf"
    assert "inline" in read.headers["Content-Disposition"]
    download = client.get(f"/ebooks/{ebook.ebook_id}/download")
    assert "attachment" in download.headers["Content-Disposition"]
    assert download.data == PDF


def test_epub_is_download_only(client, library_app):
    signin(client, "librarian@library.test")
    upload(client, data=epub_bytes(), name="book.epub")
    ebook = library_app.ebook_service.for_book(1)[0]
    post_form(client, "/librarian/books", "/signout")
    signin(client, "reader@library.test")
    assert client.get(f"/ebooks/{ebook.ebook_id}/read").status_code == 404
    assert client.get(
        f"/ebooks/{ebook.ebook_id}/download").status_code == 200


def test_fake_pdf_is_rejected(client):
    signin(client, "librarian@library.test")
    page = upload(client, data=b"<script>alert(1)</script>", name="x.pdf")
    assert "real PDF or EPUB" in text(page)


def test_guest_cannot_download(client, library_app):
    signin(client, "librarian@library.test")
    upload(client)
    ebook = library_app.ebook_service.for_book(1)[0]
    post_form(client, "/librarian/books", "/signout")
    response = client.get(f"/ebooks/{ebook.ebook_id}/download")
    assert response.status_code == 302
    assert "/signin" in response.headers["Location"]


def test_reader_cannot_manage_ebooks(client):
    signin(client, "reader@library.test")
    response = post_form(client, "/my-books", "/librarian/books/1/ebooks",
                         {"title": "x"}, follow_redirects=False)
    assert response.status_code == 403
