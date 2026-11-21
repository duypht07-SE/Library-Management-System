from dataclasses import dataclass, field


@dataclass(frozen=True)
class ShelfCopy:
    """A copy that the catalog says is on the shelf."""

    barcode: str
    book_id: int
    title: str
    shelf_location: str
    status: str


@dataclass
class InventoryCheck:
    """Compare scanned barcodes with the catalog (FR-LIB-12)."""

    shelf: str
    expected: list[ShelfCopy]
    scanned: list[str]
    known: dict[str, ShelfCopy] = field(default_factory=dict)

    @staticmethod
    def parse(text: str) -> list[str]:
        codes = text.replace(",", " ").replace(";", " ").split()
        return [code.strip().upper() for code in codes if code.strip()]

    @property
    def scanned_set(self) -> set[str]:
        return set(self.scanned)

    @property
    def duplicates(self) -> list[str]:
        seen: set[str] = set()
        repeated: list[str] = []
        for code in self.scanned:
            if code in seen and code not in repeated:
                repeated.append(code)
            seen.add(code)
        return repeated

    @property
    def found(self) -> list[ShelfCopy]:
        return [c for c in self.expected if c.barcode in self.scanned_set]

    @property
    def missing(self) -> list[ShelfCopy]:
        return [c for c in self.expected
                if c.barcode not in self.scanned_set]

    @property
    def unexpected(self) -> list[ShelfCopy]:
        """Scanned copies that the catalog does not expect here."""
        expected = {c.barcode for c in self.expected}
        return [self.known[code] for code in sorted(self.scanned_set)
                if code in self.known and code not in expected]

    @property
    def unknown(self) -> list[str]:
        return sorted(code for code in self.scanned_set
                      if code not in self.known)

    def by_book(self) -> list[dict]:
        """Recorded and counted copies for each title on the shelf."""
        rows: dict[int, dict] = {}
        for copy in self.expected:
            row = rows.setdefault(copy.book_id, {
                "title": copy.title, "recorded": 0, "counted": 0})
            row["recorded"] += 1
            if copy.barcode in self.scanned_set:
                row["counted"] += 1
        for row in rows.values():
            row["difference"] = row["counted"] - row["recorded"]
        return sorted(rows.values(), key=lambda r: r["title"])

    @property
    def is_match(self) -> bool:
        return not (self.missing or self.unexpected or self.unknown)
