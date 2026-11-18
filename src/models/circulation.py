from dataclasses import dataclass
from datetime import datetime, timedelta

from models.enums import (BorrowStatus, CopyCondition, FineReason,
                          NotificationChannel, NotificationStatus,
                          ReservationStatus)


@dataclass
class BorrowRecord:
    """One loan of one copy to one Reader."""

    borrow_id: int | None
    reader_id: int
    copy_id: int
    librarian_id: int
    borrow_date: datetime
    due_date: datetime
    return_date: datetime | None = None
    return_condition: CopyCondition | None = None
    renew_count: int = 0
    status: BorrowStatus = BorrowStatus.BORROWED

    @property
    def is_open(self) -> bool:
        return (self.return_date is None
                and self.status != BorrowStatus.RETURNED)

    def is_overdue(self, at: datetime) -> bool:
        return self.is_open and at > self.due_date

    def renew(self, max_renew: int, max_days: int) -> bool:
        if not self.is_open or self.renew_count >= max_renew:
            return False
        self.due_date += timedelta(days=max_days)
        self.renew_count += 1
        return True

    def days_late(self, at: datetime) -> int:
        end = self.return_date or at
        return max(0, (end.date() - self.due_date.date()).days)


@dataclass
class Reservation:
    """A place in the waiting queue for a book title."""

    reservation_id: int | None
    reader_id: int
    book_id: int
    reserve_date: datetime
    copy_id: int | None = None
    expire_date: datetime | None = None
    status: ReservationStatus = ReservationStatus.WAITING

    def is_hold_expired(self, at: datetime) -> bool:
        return (self.status == ReservationStatus.READY
                and self.expire_date is not None and at > self.expire_date)

    def cancel(self) -> None:
        if self.status in (ReservationStatus.COMPLETED,
                           ReservationStatus.CANCELED):
            raise ValueError("This reservation is already closed")
        self.status = ReservationStatus.CANCELED


@dataclass
class Fine:
    """A fine for a loan, paid in cash at the counter."""

    fine_id: int | None
    borrow_id: int
    reason: FineReason
    amount: int  # whole VND (NFR-COM-03)
    is_paid: bool = False
    paid_at: datetime | None = None

    def __post_init__(self) -> None:
        if self.amount <= 0:
            raise ValueError("A fine amount must be greater than 0")

    def mark_paid(self, at: datetime) -> None:
        if self.is_paid:
            raise ValueError("This fine is already paid")
        self.is_paid = True
        self.paid_at = at


@dataclass
class Notification:
    """An in-app reminder for a Reader."""

    notification_id: int | None
    reader_id: int
    message: str
    channel: NotificationChannel = NotificationChannel.IN_APP
    status: NotificationStatus = NotificationStatus.PENDING
    sent_at: datetime | None = None

    def send(self, at: datetime) -> bool:
        if self.status == NotificationStatus.SENT:
            return False
        self.status = NotificationStatus.SENT
        self.sent_at = at
        return True
