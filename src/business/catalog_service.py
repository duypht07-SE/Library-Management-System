from data.repositories import BookRepository
from common.exceptions import ValidationError
from models import Book
from models import Librarian

CATEGORIES = [
    "Computer Science", "Mathematics", "Economics", "Law", "Languages",
    "Literature", "History", "Children's books", "Other",
]


class CatalogService:
    """Book catalog for the Guest pages (FR-GST-02, FR-GST-03)."""

    def __init__(self, books: BookRepository) -> None:
        self.books = books

    def categories(self) -> list[str]:
        return CATEGORIES

    def new_books(self, limit: int = 5) -> list[Book]:
        return self.books.find_featured(limit)

    def search(self, keyword: str = "", category: str = "") -> list[Book]:
        return self.books.search(keyword.strip()[:100], category.strip()[:100])

    def manage_book(self, librarian: Librarian, action: str,
                    values: dict, book_id: int | None = None,
                    copy_id: int | None = None) -> int:
        """Validate and persist Librarian catalog operations (FR-LIB-01:05)."""
        operation = librarian.manage_book(action, **values)
        action = operation["action"]
        if action in {"add_book", "edit_book"}:
            clean = {}
            limits = {"isbn": 20, "ddc_code": 20, "title": 255,
                      "author": 150, "category": 100}
            for field, limit in limits.items():
                value = str(values.get(field, "")).strip()
                if not value or len(value) > limit:
                    raise ValidationError(
                        f"Enter a valid {field.replace('_', ' ')} "
                        f"(up to {limit} characters).")
                clean[field] = value
            if action == "edit_book" and book_id is None:
                raise ValidationError("Choose a book to edit.")
            try:
                return self.books.save_book(
                    clean, book_id if action == "edit_book" else None)
            except ValueError as error:
                raise ValidationError(str(error)) from error
        if action in {"add_copy", "edit_copy"}:
            book_id = book_id or self._positive_id(values.get("book_id"))
            barcode = str(values.get("barcode", "")).strip()
            location = str(values.get("shelf_location", "")).strip()
            if not barcode or len(barcode) > 50:
                raise ValidationError("Barcode is required (up to 50 characters).")
            if not location or len(location) > 50:
                raise ValidationError("Shelf location is required (up to 50 characters).")
            if self.books.find_by_id(book_id) is None:
                raise ValidationError("Book was not found.")
            try:
                return self.books.save_copy(
                    book_id, barcode, location,
                    copy_id if action == "edit_copy" else None)
            except ValueError as error:
                raise ValidationError(str(error)) from error
        if action == "retire_copy":
            copy_id = copy_id or self._positive_id(values.get("copy_id"))
            try:
                self.books.retire_copy(copy_id)
            except ValueError as error:
                raise ValidationError(str(error)) from error
            return copy_id
        raise ValidationError("Unknown book action.")

    @staticmethod
    def _positive_id(value) -> int:
        try:
            number = int(value)
        except (TypeError, ValueError) as error:
            raise ValidationError("Select a valid book or copy.") from error
        if number < 1:
            raise ValidationError("Select a valid book or copy.")
        return number
