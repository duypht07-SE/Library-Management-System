import sqlite3
from datetime import datetime

from data.repositories.base_repository import BaseRepository
from models import Ebook, EbookFormat


class EbookRepository(BaseRepository):
    """E-books and digital course materials (FR-LIB-14, FR-RDR-07)."""

    SELECT = ("SELECT e.*, b.title AS book_title FROM ebooks e"
              " JOIN books b ON b.book_id = e.book_id")

    def for_book(self, book_id: int) -> list[Ebook]:
        rows = self.db.fetch_all(
            self.SELECT + " WHERE e.book_id = ? ORDER BY e.ebook_id",
            (book_id,))
        return [self._from_row(r) for r in rows]

    def all(self) -> list[Ebook]:
        rows = self.db.fetch_all(self.SELECT + " ORDER BY b.title, e.title")
        return [self._from_row(r) for r in rows]

    def find_by_id(self, ebook_id: int) -> Ebook | None:
        row = self.db.fetch_one(self.SELECT + " WHERE e.ebook_id = ?",
                                (ebook_id,))
        return self._from_row(row) if row else None

    def add(self, ebook: Ebook) -> Ebook:
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO ebooks (book_id, title, file_format, file_path,"
                " file_size, uploaded_by, uploaded_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?)",
                (ebook.book_id, ebook.title, ebook.file_format.value,
                 ebook.file_path, ebook.file_size, ebook.uploaded_by,
                 ebook.uploaded_at.isoformat(sep=" ")))
            ebook.ebook_id = cursor.lastrowid
        return ebook

    def update(self, ebook: Ebook) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE ebooks SET title = ?, file_format = ?, file_path = ?,"
                " file_size = ?, uploaded_by = ?, uploaded_at = ?"
                " WHERE ebook_id = ?",
                (ebook.title, ebook.file_format.value, ebook.file_path,
                 ebook.file_size, ebook.uploaded_by,
                 ebook.uploaded_at.isoformat(sep=" "), ebook.ebook_id))

    def delete(self, ebook_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM ebooks WHERE ebook_id = ?", (ebook_id,))

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Ebook:
        return Ebook(row["ebook_id"], row["book_id"], row["title"],
                     EbookFormat(row["file_format"]), row["file_path"],
                     row["file_size"], row["uploaded_by"],
                     datetime.fromisoformat(str(row["uploaded_at"])),
                     row["book_title"])
