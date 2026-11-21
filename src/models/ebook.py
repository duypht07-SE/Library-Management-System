from dataclasses import dataclass
from datetime import datetime

from models.enums import EbookFormat

PDF_MAGIC = b"%PDF-"
ZIP_MAGIC = b"PK\x03\x04"
EPUB_MIMETYPE = b"application/epub+zip"


@dataclass
class Ebook:
    """A digital copy (PDF or EPUB) of a book title (FR-LIB-14)."""

    ebook_id: int | None
    book_id: int
    title: str
    file_format: EbookFormat
    file_path: str
    file_size: int
    uploaded_by: int
    uploaded_at: datetime
    book_title: str | None = None

    @property
    def can_read_online(self) -> bool:
        return self.file_format == EbookFormat.PDF

    @property
    def mimetype(self) -> str:
        if self.file_format == EbookFormat.PDF:
            return "application/pdf"
        return "application/epub+zip"

    @property
    def size_label(self) -> str:
        if self.file_size >= 1024 * 1024:
            return f"{self.file_size / (1024 * 1024):.1f} MB"
        return f"{max(1, self.file_size // 1024)} KB"

    @staticmethod
    def detect_format(data: bytes) -> EbookFormat | None:
        """Check the file content, not only the file name."""
        if data.startswith(PDF_MAGIC):
            return EbookFormat.PDF
        if (data.startswith(ZIP_MAGIC) and data[30:38] == b"mimetype"
                and EPUB_MIMETYPE in data[38:120]):
            return EbookFormat.EPUB
        return None
