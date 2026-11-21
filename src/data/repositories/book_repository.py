from data.repositories.base_repository import BaseRepository
from models import Book, BookCopy, ShelfCopy

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

    def search(self, keyword: str = "", category: str = "", *,
               limit: int | None = None, offset: int = 0) -> list[Book]:
        clauses = []
        params = []
        if keyword:
            clauses.append("(b.title LIKE ? COLLATE NOCASE OR "
                           "b.author LIKE ? COLLATE NOCASE OR "
                           "b.isbn LIKE ? COLLATE NOCASE OR "
                           "b.category LIKE ? COLLATE NOCASE)")
            params.extend([f"%{keyword}%"] * 4)
        if category:
            clauses.append("b.category = ? COLLATE NOCASE")
            params.append(category)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = (_BOOK_WITH_AVAILABLE + where
               + " ORDER BY b.title COLLATE NOCASE, b.book_id")
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params.extend([limit, offset])
        rows = self.db.fetch_all(sql, params)
        return [Book.from_row(row) for row in rows]

    def save_book(self, values: dict, book_id: int | None = None) -> int:
        with self.db.transaction() as conn:
            if book_id is None:
                cursor = conn.execute(
                    "INSERT INTO books (isbn, ddc_code, title, author, "
                    "category) VALUES (?, ?, ?, ?, ?)",
                    tuple(values[key] for key in
                          ("isbn", "ddc_code", "title", "author", "category")))
                return int(cursor.lastrowid)
            cursor = conn.execute(
                "UPDATE books SET isbn=?, ddc_code=?, title=?, author=?, "
                "category=? WHERE book_id=?",
                (*[values[key] for key in
                   ("isbn", "ddc_code", "title", "author", "category")],
                 book_id))
            if cursor.rowcount != 1:
                raise ValueError("Book was not found.")
            return book_id

    def save_copy(self, book_id: int, barcode: str, shelf_location: str,
                  copy_id: int | None = None) -> int:
        with self.db.transaction() as conn:
            if copy_id is None:
                cursor = conn.execute(
                    "INSERT INTO book_copies (book_id, barcode, shelf_location)"
                    " VALUES (?, ?, ?)", (book_id, barcode, shelf_location))
                return int(cursor.lastrowid)
            cursor = conn.execute(
                "UPDATE book_copies SET barcode=?, shelf_location=? "
                "WHERE copy_id=? AND book_id=?",
                (barcode, shelf_location, copy_id, book_id))
            if cursor.rowcount != 1:
                raise ValueError("Book copy was not found.")
            return copy_id

    def retire_copy(self, copy_id: int) -> tuple[int, list[int]]:
        with self.db.transaction() as conn:
            row = conn.execute(
                "SELECT book_id, status FROM book_copies WHERE copy_id=?",
                (copy_id,)).fetchone()
            if row is None:
                raise ValueError("Book copy was not found.")
            if row["status"] != "AVAILABLE":
                raise ValueError("Only an available copy can be retired.")
            book_id = row["book_id"]
            conn.execute("UPDATE book_copies SET status='CANCELED' "
                         "WHERE copy_id=?", (copy_id,))
            usable = conn.execute(
                "SELECT COUNT(*) FROM book_copies WHERE book_id=? "
                "AND status != 'CANCELED'", (book_id,)).fetchone()[0]
            reader_ids = []
            if usable == 0:
                reader_ids = [r[0] for r in conn.execute(
                    "SELECT reader_id FROM reservations WHERE book_id=? "
                    "AND status='WAITING'", (book_id,)).fetchall()]
                conn.execute(
                    "UPDATE reservations SET status='CANCELED' WHERE book_id=? "
                    "AND status='WAITING'", (book_id,))
                for reader_id in reader_ids:
                    conn.execute(
                        "INSERT INTO notifications (reader_id, message) "
                        "VALUES (?, ?)",
                        (reader_id, "Your book reservation was canceled "
                                    "because no usable copy remains."))
            return book_id, reader_ids

    def all_books(self) -> list[Book]:
        rows = self.db.fetch_all(
            _BOOK_WITH_AVAILABLE + " ORDER BY b.title COLLATE NOCASE")
        books = [Book.from_row(row) for row in rows]
        for book in books:
            book.copies = self.find_copies(book.book_id)
        return books

    def book_count(self) -> int:
        return self.db.fetch_one("SELECT COUNT(*) AS n FROM books")["n"]

    def count(self) -> int:
        return self.db.fetch_one("SELECT COUNT(*) AS n FROM books")["n"]

    def shelf_locations(self) -> list[str]:
        rows = self.db.fetch_all(
            "SELECT DISTINCT shelf_location FROM book_copies"
            " WHERE status <> 'CANCELED' ORDER BY shelf_location")
        return [r["shelf_location"] for r in rows]

    def shelf_copies(self, shelf: str = "") -> list[ShelfCopy]:
        """Copies the catalog expects on the shelf (FR-LIB-12)."""
        sql = _SHELF_COPY + " WHERE c.status = 'AVAILABLE'"
        params: tuple = ()
        if shelf:
            sql += " AND c.shelf_location = ?"
            params = (shelf,)
        return [_shelf_copy(r) for r in
                self.db.fetch_all(sql + " ORDER BY c.barcode", params)]

    def copies_by_barcodes(self, barcodes: list[str]) -> dict[str, ShelfCopy]:
        if not barcodes:
            return {}
        marks = ", ".join("?" for _ in barcodes)
        rows = self.db.fetch_all(
            _SHELF_COPY + f" WHERE upper(c.barcode) IN ({marks})",
            tuple(barcodes))
        return {r["barcode"].upper(): _shelf_copy(r) for r in rows}


_SHELF_COPY = ("SELECT c.barcode, c.book_id, b.title, c.shelf_location,"
               " c.status FROM book_copies c JOIN books b USING (book_id)")


def _shelf_copy(row) -> ShelfCopy:
    return ShelfCopy(row["barcode"].upper(), row["book_id"], row["title"],
                     row["shelf_location"], row["status"])
