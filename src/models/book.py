from dataclasses import dataclass, field
from typing import Any, Mapping

from models.enums import CopyCondition, CopyStatus


@dataclass
class BookCopy:
    """A physical copy with its own barcode."""

    copy_id: int | None
    book_id: int
    barcode: str
    shelf_location: str
    status: CopyStatus = CopyStatus.AVAILABLE
    copy_condition: CopyCondition = CopyCondition.INTACT

    @property
    def is_available(self) -> bool:
        return self.status == CopyStatus.AVAILABLE

    @property
    def can_retire(self) -> bool:
        return self.status == CopyStatus.AVAILABLE

    def update_status(self, status: CopyStatus) -> None:
        self.status = CopyStatus(status)

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "BookCopy":
        return cls(
            copy_id=row["copy_id"],
            book_id=row["book_id"],
            barcode=row["barcode"],
            shelf_location=row["shelf_location"],
            status=CopyStatus(row["status"]),
            copy_condition=CopyCondition(row["copy_condition"]),
        )


@dataclass
class Book:
    """A book title. It is made of one or more copies (composition)."""

    book_id: int | None
    isbn: str
    ddc_code: str
    title: str
    author: str
    category: str
    copies: list[BookCopy] = field(default_factory=list)
    # derived /availableCopies, not stored
    available_count: int | None = None

    @property
    def available_copies(self) -> int:
        if self.available_count is not None:
            return self.available_count
        return sum(1 for c in self.copies if c.is_available)

    @property
    def is_available(self) -> bool:
        return self.available_copies > 0

    def matches(self, keyword: str) -> bool:
        key = keyword.strip().lower()
        return any(key in v.lower() for v in
                   (self.title, self.author, self.isbn, self.category))

    @staticmethod
    def search(books: list["Book"], keyword: str) -> list["Book"]:
        return [b for b in books if b.matches(keyword)]

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> "Book":
        keys = row.keys()
        return cls(
            book_id=row["book_id"],
            isbn=row["isbn"],
            ddc_code=row["ddc_code"],
            title=row["title"],
            author=row["author"],
            category=row["category"],
            available_count=(row["available_copies"]
                             if "available_copies" in keys else None),
        )
