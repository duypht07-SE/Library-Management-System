from data.repositories.base_repository import BaseRepository
from models import Book, BookCopy

_BOOK_WITH_AVAILABLE = """
    SELECT b.*,
           (SELECT COUNT(*) FROM book_copies c
             WHERE c.book_id = b.book_id
               AND c.status = 'AVAILABLE') AS available_copies
      FROM books b
"""


class BookRepository(BaseRepository):
    """Reads books and copies (Store D2)."""

    def find_by_id(self, book_id: int) -> Book | None:
        row = self.db.fetch_one(
            _BOOK_WITH_AVAILABLE + " WHERE b.book_id = ?", (book_id,))
        if row is None:
            return None
        book = Book.from_row(row)
        book.copies = self.find_copies(book_id)
        return book

    def find_copies(self, book_id: int) -> list[BookCopy]:
        rows = self.db.fetch_all(
            "SELECT * FROM book_copies WHERE book_id = ? ORDER BY copy_id",
            (book_id,))
        return [BookCopy.from_row(r) for r in rows]

    def find_featured(self, limit: int) -> list[Book]:
        rows = self.db.fetch_all(
            _BOOK_WITH_AVAILABLE + " ORDER BY b.book_id LIMIT ?", (limit,))
        return [Book.from_row(r) for r in rows]

    def count(self) -> int:
        return self.db.fetch_one("SELECT COUNT(*) AS n FROM books")["n"]
