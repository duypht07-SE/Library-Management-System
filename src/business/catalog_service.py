from data.repositories import BookRepository
from models import Book

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
