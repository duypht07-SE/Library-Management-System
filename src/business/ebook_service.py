import secrets
from datetime import datetime
from pathlib import Path
from typing import Callable

from common.exceptions import ValidationError
from common.validation import clean_text
from config import now
from data.repositories import BookRepository, EbookRepository
from models import Ebook, EbookFormat, Librarian, User

MAX_EBOOK_BYTES = 20 * 1024 * 1024


class EbookService:
    """Upload, update, remove (FR-LIB-14) and read e-books (FR-RDR-07)."""

    def __init__(self, ebooks: EbookRepository, books: BookRepository,
                 storage_dir: Path,
                 clock: Callable[[], datetime] = now) -> None:
        self.ebooks = ebooks
        self.books = books
        self.storage_dir = Path(storage_dir)
        self.clock = clock

    def all(self) -> list[Ebook]:
        return self.ebooks.all()

    def for_book(self, book_id: int) -> list[Ebook]:
        return self.ebooks.for_book(book_id)

    def upload(self, librarian: Librarian, book_id: int, title: str,
               data: bytes) -> Ebook:
        if self.books.find_by_id(book_id) is None:
            raise ValidationError("Book was not found.")
        title = clean_text(title, "E-book title", 255)
        file_format = self._check_file(data)
        ebook = Ebook(None, book_id, title, file_format,
                      self._store(data, file_format.value.lower()),
                      len(data), librarian.user_id, self.clock())
        return self.ebooks.add(ebook)

    def update(self, librarian: Librarian, ebook_id: int, title: str,
               data: bytes | None = None) -> Ebook:
        ebook = self.find(ebook_id)
        ebook.title = clean_text(title, "E-book title", 255)
        old_path = None
        if data:
            ebook.file_format = self._check_file(data)
            old_path = ebook.file_path
            ebook.file_path = self._store(data,
                                          ebook.file_format.value.lower())
            ebook.file_size = len(data)
        ebook.uploaded_by = librarian.user_id
        ebook.uploaded_at = self.clock()
        self.ebooks.update(ebook)
        if old_path:
            self._delete_file(old_path)
        return ebook

    def remove(self, librarian: Librarian, ebook_id: int) -> Ebook:
        ebook = self.find(ebook_id)
        self.ebooks.delete(ebook_id)
        self._delete_file(ebook.file_path)
        return ebook

    def find(self, ebook_id: int) -> Ebook:
        ebook = self.ebooks.find_by_id(ebook_id)
        if ebook is None:
            raise ValidationError("E-book not found.")
        return ebook

    def file_for(self, user: User, ebook_id: int) -> tuple[Ebook, Path]:
        """Only an active Reader or a catalog Librarian gets the file."""
        if not (user.is_active and (user.role.value == "READER"
                                    or user.can("CATALOG"))):
            raise ValidationError("Your account cannot open e-books.")
        ebook = self.find(ebook_id)
        path = self._path(ebook.file_path)
        if not path.is_file():
            raise ValidationError("The e-book file is missing.")
        return ebook, path

    @staticmethod
    def _check_file(data: bytes) -> EbookFormat:
        if not data:
            raise ValidationError("Choose a PDF or EPUB file to upload.")
        if len(data) > MAX_EBOOK_BYTES:
            raise ValidationError("The file must be 20 MB or smaller.")
        file_format = Ebook.detect_format(data)
        if file_format is None:
            raise ValidationError("The file must be a real PDF or EPUB.")
        return file_format

    def _store(self, data: bytes, extension: str) -> str:
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        name = f"ebook-{secrets.token_hex(12)}.{extension}"
        (self.storage_dir / name).write_bytes(data)
        return name

    def _path(self, name: str) -> Path:
        path = (self.storage_dir / name).resolve()
        if path.parent != self.storage_dir.resolve():
            raise ValidationError("Invalid e-book file name.")
        return path

    def _delete_file(self, name: str) -> None:
        path = self._path(name)
        if path.exists():
            path.unlink()
