from common.exceptions import ValidationError
from data.repositories import BookRepository
from models import InventoryCheck, Librarian

MAX_SCANS = 5000


class InventoryService:
    """Batch barcode scan against the catalog (FR-LIB-12)."""

    def __init__(self, books: BookRepository) -> None:
        self.books = books

    def shelves(self) -> list[str]:
        return self.books.shelf_locations()

    def check(self, librarian: Librarian, shelf: str,
              scanned_text: str) -> InventoryCheck:
        shelf = (shelf or "").strip()
        if shelf and shelf not in self.shelves():
            raise ValidationError("Choose a shelf from the list.")
        scanned = InventoryCheck.parse(scanned_text or "")
        if len(scanned) > MAX_SCANS:
            raise ValidationError(
                f"Scan at most {MAX_SCANS:,} barcodes in one check.")
        expected = self.books.shelf_copies(shelf)
        known = self.books.copies_by_barcodes(sorted(set(scanned)))
        try:
            return librarian.check_inventory(shelf, expected, scanned, known)
        except ValueError as error:
            raise ValidationError(str(error)) from error
