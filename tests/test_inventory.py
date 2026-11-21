"""Inventory check by batch barcode scan (FR-LIB-12)."""
import pytest

from business.inventory_service import InventoryService
from common.exceptions import ValidationError
from data.repositories import BookRepository, UserRepository
from models import InventoryCheck, ShelfCopy
from web_helpers import post_form, signin, text


def copy(code, book=1, title="Clean Code", shelf="A01-1",
         status="AVAILABLE"):
    return ShelfCopy(code, book, title, shelf, status)


# --- Unit: InventoryCheck --------------------------------------------------
@pytest.mark.parametrize("raw, parsed", [
    ("", []),                                   # zero length
    ("lib-1", ["LIB-1"]),                       # single value
    ("LIB-1\nLIB-2, LIB-3;LIB-4  LIB-5",
     ["LIB-1", "LIB-2", "LIB-3", "LIB-4", "LIB-5"]),
])
def test_parse_barcodes(raw, parsed):
    assert InventoryCheck.parse(raw) == parsed


def test_compare_finds_missing_unexpected_unknown_duplicates():
    expected = [copy("LIB-1"), copy("LIB-2"), copy("LIB-3", 2, "B")]
    known = {c.barcode: c for c in expected}
    known["LIB-9"] = copy("LIB-9", 3, "C", "Z9", "BORROWED")
    check = InventoryCheck("A01-1", expected,
                           ["LIB-1", "LIB-3", "LIB-3", "LIB-9", "BAD"],
                           known)
    assert [c.barcode for c in check.found] == ["LIB-1", "LIB-3"]
    assert [c.barcode for c in check.missing] == ["LIB-2"]
    assert [c.barcode for c in check.unexpected] == ["LIB-9"]
    assert check.unknown == ["BAD"]
    assert check.duplicates == ["LIB-3"]
    assert not check.is_match
    assert check.by_book()[1] == {"title": "Clean Code", "recorded": 2,
                                  "counted": 1, "difference": -1}


def test_exact_shelf_is_a_match():
    expected = [copy("LIB-1")]
    check = InventoryCheck("A01-1", expected, ["LIB-1"],
                           {"LIB-1": expected[0]})
    assert check.is_match


# --- Component: InventoryService -------------------------------------------
@pytest.fixture
def inventory(database):
    return InventoryService(BookRepository(database))


@pytest.fixture
def librarian(database):
    return UserRepository(database).find_by_id(2)


def test_check_one_shelf_against_catalog(inventory, librarian):
    result = inventory.check(librarian, "A06-1", "lib-00061")
    assert result.is_match
    assert result.by_book() == [{"title": result.expected[0].title,
                                 "recorded": 1, "counted": 1,
                                 "difference": 0}]


def test_borrowed_copy_on_shelf_is_unexpected(inventory, librarian):
    result = inventory.check(librarian, "A06-1", "LIB-00061\nLIB-00011")
    assert [c.barcode for c in result.unexpected] == ["LIB-00011"]
    assert result.unexpected[0].status == "BORROWED"


def test_whole_library_check_counts_all_available(inventory, librarian):
    result = inventory.check(librarian, "", "LIB-00061")
    # 40 copies - 4 on loan - 1 held for a Reader = 35 on the shelves
    assert len(result.expected) == 35
    assert len(result.missing) == 34


@pytest.mark.parametrize("shelf, scanned, message", [
    ("A06-1", "", "at least one barcode"),     # zero scans
    ("NO-SHELF", "LIB-00061", "Choose a shelf"),
])
def test_invalid_check(inventory, librarian, shelf, scanned, message):
    with pytest.raises(ValidationError, match=message):
        inventory.check(librarian, shelf, scanned)


def test_too_many_scans(inventory, librarian):
    with pytest.raises(ValidationError, match="at most"):
        inventory.check(librarian, "", "X " * 5001)


# --- System -------------------------------------------------------------------
def test_inventory_page(client):
    signin(client, "librarian@library.test")
    page = post_form(client, "/librarian/inventory", "/librarian/inventory",
                     {"shelf": "A06-1", "barcodes": "LIB-00061\nLIB-99999"})
    body = text(page)
    assert "The shelf does not match the catalog" in body
    assert "LIB-99999" in body


def test_inventory_needs_catalog_permission(client, library_app):
    library_app.users.assign_staff_role(2, 2)     # Circulation Desk
    signin(client, "librarian@library.test")
    assert client.get("/librarian/inventory").status_code == 403
