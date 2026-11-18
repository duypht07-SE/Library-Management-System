"""Unit tests for the domain classes (Section 5)."""
from datetime import datetime, timedelta

import pytest

from models import (Administrator, Book, BookCopy, BorrowRecord, CopyStatus,
                    Fine, FineReason, Librarian, LibraryRules, Reader,
                    Reservation, ReservationStatus, Role, RuleKey,
                    Notification, NotificationStatus, SystemConfig,
                    UserFactory, UserStatus)

NOW = datetime(2026, 11, 17, 10, 0, 0)


def user_row(role, **extra):
    row = dict(user_id=1, role=role, card_code=None, full_name="A",
               email="a@x.test", phone="1", password_hash="h",
               status="ACTIVE", failed_logins=0, locked_until=None)
    row.update(extra)
    return row


def copy(status):
    return BookCopy(1, 1, "B1", "A1", status)


def loan(due_in_days, returned_in_days=None):
    due = NOW + timedelta(days=due_in_days)
    returned = (None if returned_in_days is None
                else NOW + timedelta(days=returned_in_days))
    return BorrowRecord(1, 3, 1, 2, due - timedelta(days=14), due,
                        return_date=returned)


# --- User hierarchy -------------------------------------------------------

@pytest.mark.parametrize("role, cls", [
    ("READER", Reader), ("LIBRARIAN", Librarian), ("ADMIN", Administrator)])
def test_factory_creates_subclass_for_role(role, cls):
    user = UserFactory.from_row(user_row(role))
    assert isinstance(user, cls)
    assert user.role == Role(role)


def test_factory_rejects_unknown_role():
    with pytest.raises(ValueError):
        UserFactory.from_row(user_row("GUEST"))


def test_reader_keeps_card_code():
    reader = UserFactory.from_row(user_row("READER", card_code="RD-1"))
    assert reader.card_code == "RD-1"


@pytest.mark.parametrize("status, active", [
    ("ACTIVE", True), ("PENDING", False), ("LOCKED", False),
    ("REJECTED", False)])
def test_only_active_status_is_active(status, active):
    user = UserFactory.from_row(user_row("READER", status=status))
    assert user.is_active is active
    assert user.status == UserStatus(status)


@pytest.mark.parametrize("locked_until, locked", [
    (None, False),                        # never locked
    ("2026-11-17 10:10:00", True),        # 10 minutes left
    ("2026-11-17 10:00:00", False),       # boundary: lock ends now
    ("2026-11-17 09:59:59", False),       # lock already ended
])
def test_login_lock_nfr_sec_06(locked_until, locked):
    user = UserFactory.from_row(
        user_row("READER", locked_until=locked_until))
    assert user.is_login_locked(NOW) is locked


# --- Book and BookCopy ----------------------------------------------------

@pytest.mark.parametrize("statuses, expected", [
    ([], 0),                                              # no copies
    ([CopyStatus.BORROWED, CopyStatus.CANCELED], 0),      # none on shelf
    ([CopyStatus.AVAILABLE], 1),                          # single copy
    ([CopyStatus.AVAILABLE, CopyStatus.RESERVED,
      CopyStatus.AVAILABLE], 2),
])
def test_available_copies_are_counted(statuses, expected):
    book = Book(1, "isbn", "005", "T", "A", "Computer Science",
                copies=[copy(s) for s in statuses])
    assert book.available_copies == expected
    assert book.is_available is (expected > 0)


@pytest.mark.parametrize("status, can_retire", [
    (CopyStatus.AVAILABLE, True), (CopyStatus.BORROWED, False),
    (CopyStatus.RESERVED, False), (CopyStatus.CANCELED, False)])
def test_only_copy_on_shelf_can_retire_fr_lib_05(status, can_retire):
    assert copy(status).can_retire is can_retire


# --- BorrowRecord ---------------------------------------------------------

@pytest.mark.parametrize("due_in, returned_in, past_due, days_late", [
    (3, None, False, 0),     # not due yet
    (0, None, False, 0),     # boundary: due right now
    (-1, None, True, 1),     # one day late
    (-6, None, True, 6),
    (-6, -8, False, 0),      # returned before the due date
    (-6, -2, False, 4),      # returned 4 days late
])
def test_loan_lateness_fr_lib_09(due_in, returned_in, past_due, days_late):
    record = loan(due_in, returned_in)
    assert record.is_overdue(NOW) is past_due
    assert record.days_late(NOW) == days_late


# --- Reservation ----------------------------------------------------------

@pytest.mark.parametrize("status, expire_in_hours, expired", [
    (ReservationStatus.READY, -1, True),
    (ReservationStatus.READY, 1, False),
    (ReservationStatus.WAITING, -1, False),   # only READY holds expire
])
def test_hold_expiry_fr_sys_03(status, expire_in_hours, expired):
    hold = Reservation(1, 3, 5, NOW - timedelta(days=4), copy_id=25,
                       expire_date=NOW + timedelta(hours=expire_in_hours),
                       status=status)
    assert hold.is_hold_expired(NOW) is expired


# --- Fine -----------------------------------------------------------------

@pytest.mark.parametrize("amount", [-5000, -1, 0])
def test_fine_amount_must_be_positive(amount):
    with pytest.raises(ValueError):
        Fine(None, 1, FineReason.LATE_RETURN, amount)


def test_smallest_fine_is_accepted():
    assert Fine(None, 1, FineReason.LATE_RETURN, 1).amount == 1


# --- LibraryRules ---------------------------------------------------------

def test_rules_from_configs_fr_adm_04():
    configs = [SystemConfig(RuleKey.MAX_BOOKS, "3", 1, NOW),
               SystemConfig(RuleKey.DAILY_FINE, "2000", 1, NOW)]
    rules = LibraryRules.from_configs(configs)
    assert rules.max_books == 3
    assert rules.daily_fine == 2000
    assert rules.max_days == 14


def test_rules_use_defaults_when_table_is_empty():
    assert LibraryRules.from_configs([]) == LibraryRules()


# --- Class diagram methods ------------------------------------------------

@pytest.mark.parametrize("renew_count, returned_in, renewed", [
    (0, None, True),
    (1, None, False),      # limit reached (boundary)
    (0, -1, False),        # already returned
])
def test_renew_fr_rdr_05(renew_count, returned_in, renewed):
    record = loan(3, returned_in)
    record.renew_count = renew_count
    old_due = record.due_date
    assert record.renew(max_renew=1, max_days=14) is renewed
    assert (record.due_date - old_due).days == (14 if renewed else 0)


def test_reservation_cancel_fr_rdr_03():
    hold = Reservation(1, 3, 5, NOW)
    hold.cancel()
    assert hold.status == ReservationStatus.CANCELED
    with pytest.raises(ValueError):
        hold.cancel()


def test_fine_mark_paid_fr_lib_13():
    fine = Fine(1, 1, FineReason.LATE_RETURN, 5000)
    fine.mark_paid(NOW)
    assert fine.is_paid and fine.paid_at == NOW
    with pytest.raises(ValueError):
        fine.mark_paid(NOW)


def test_notification_send_fr_sys_02():
    note = Notification(1, 3, "Your book is late")
    assert note.send(NOW) is True
    assert note.status == NotificationStatus.SENT
    assert note.send(NOW) is False


def test_copy_update_status():
    item = copy(CopyStatus.AVAILABLE)
    item.update_status(CopyStatus.BORROWED)
    assert item.status == CopyStatus.BORROWED
    with pytest.raises(ValueError):
        item.update_status("SOLD")


@pytest.mark.parametrize("value, ok", [("7", True), ("1", True),
                                       ("0", False), ("-1", False),
                                       ("abc", False), ("", False)])
def test_config_update_fr_adm_04(value, ok):
    config = SystemConfig(RuleKey.MAX_BOOKS, "5", 1, NOW)
    if ok:
        config.update(value, by=2, at=NOW)
        assert config.config_value == value and config.updated_by == 2
    else:
        with pytest.raises(ValueError):
            config.update(value, by=2, at=NOW)


def test_book_search_fr_gst_02():
    books = [Book(1, "978-1", "005", "Clean Code", "Robert C. Martin", "IT"),
             Book(2, "978-2", "340", "Civil Law", "Nguyen A", "Law")]
    assert [b.book_id for b in Book.search(books, "  CLEAN ")] == [1]
    assert [b.book_id for b in Book.search(books, "law")] == [2]
    assert Book.search(books, "zzz") == []
