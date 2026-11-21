"""Status values stored in the database (Section 6.4)."""
from enum import Enum


class Role(str, Enum):
    READER = "READER"
    LIBRARIAN = "LIBRARIAN"
    ADMIN = "ADMIN"


class UserStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    LOCKED = "LOCKED"
    REJECTED = "REJECTED"


class CopyStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    BORROWED = "BORROWED"
    RESERVED = "RESERVED"   # on hold for a Reader
    CANCELED = "CANCELED"   # retired, damaged, or lost


class CopyCondition(str, Enum):
    INTACT = "INTACT"
    DAMAGED = "DAMAGED"
    LOST = "LOST"


class BorrowStatus(str, Enum):
    BORROWED = "BORROWED"
    OVERDUE = "OVERDUE"
    RETURNED = "RETURNED"


class ReservationStatus(str, Enum):
    WAITING = "WAITING"
    READY = "READY"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class FineReason(str, Enum):
    LATE_RETURN = "LATE_RETURN"
    DAMAGED = "DAMAGED"
    LOST = "LOST"


class NotificationChannel(str, Enum):
    IN_APP = "IN_APP"


class NotificationStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class RuleKey(str, Enum):
    MAX_BOOKS = "MAX_BOOKS"
    MAX_DAYS = "MAX_DAYS"
    MAX_RENEW = "MAX_RENEW"
    HOLD_DAYS = "HOLD_DAYS"
    DAILY_FINE = "DAILY_FINE"


class Permission(str, Enum):
    """Permissions that an Administrator gives to a staff role."""

    CIRCULATION = "CIRCULATION"
    READER_CARDS = "READER_CARDS"
    CATALOG = "CATALOG"
    FINES = "FINES"


class ResetStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"


class EbookFormat(str, Enum):
    PDF = "PDF"
    EPUB = "EPUB"
