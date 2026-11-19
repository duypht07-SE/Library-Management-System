from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Mapping

from common.exceptions import AuthenticationError
from models.book import Book, BookCopy
from models.circulation import BorrowRecord, Fine, Reservation
from models.enums import (BorrowStatus, CopyCondition, CopyStatus,
                          FineReason, Role, RuleKey, UserStatus)


@dataclass
class User(ABC):
    """Base class for every account (Section 5)."""

    user_id: int | None
    full_name: str
    email: str
    phone: str
    password_hash: str
    status: UserStatus = UserStatus.PENDING
    failed_logins: int = 0
    locked_until: datetime | None = None
    student_id: str | None = None
    avatar_path: str | None = None

    @property
    @abstractmethod
    def role(self) -> Role:
        ...

    @property
    @abstractmethod
    def home_endpoint(self) -> str:
        ...

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE

    def is_login_locked(self, at: datetime) -> bool:
        return self.locked_until is not None and self.locked_until > at

    def has_role(self, *roles: Role) -> bool:
        return self.role in roles

    def login(self, at: datetime) -> None:
        """Raise AuthenticationError when this account may not sign in."""
        if self.status == UserStatus.PENDING:
            raise AuthenticationError(
                "Your library card is waiting for approval by a librarian.")
        if self.status == UserStatus.REJECTED:
            raise AuthenticationError(
                "Your registration was rejected. Please contact the library "
                "desk.")
        if self.status == UserStatus.LOCKED:
            raise AuthenticationError(
                "This account is locked. Please contact the library desk.")
        if self.is_login_locked(at):
            raise AuthenticationError(
                "Too many wrong passwords. Try again after "
                f"{self.locked_until:%H:%M}.")

    def logout(self) -> None:
        """The Flask session is cleared by the controller (FR-GST-04)."""
        return None

    def update_profile(self, full_name: str | None = None,
                       email: str | None = None, phone: str | None = None,
                       student_id: str | None = None,
                       avatar_path: str | None = None) -> None:
        """Copy the values that the profile form changed (FR-RDR-02)."""
        if full_name is not None:
            self.full_name = full_name
        if email is not None:
            self.email = email
        if phone is not None:
            self.phone = phone
        if student_id is not None:
            self.student_id = student_id
        if avatar_path is not None:
            self.avatar_path = avatar_path

    def update_password(self, password_hash: str) -> None:
        self.password_hash = password_hash
        self.failed_logins = 0
        self.locked_until = None


@dataclass
class Reader(User):
    card_code: str | None = None

    @property
    def role(self) -> Role:
        return Role.READER

    @property
    def home_endpoint(self) -> str:
        return "reader.profile"

    def view_fines(self, fines: list[Fine]) -> list[Fine]:
        """Return this Reader's fines; the repository scopes them by owner."""
        return fines

    def view_borrow_history(
            self, records: list[BorrowRecord]) -> list[BorrowRecord]:
        return records

    def reserve_book(self, book: Book, at: datetime) -> Reservation:
        if not self.is_active:
            raise ValueError("Your card must be active to reserve a book.")
        if book.is_available:
            raise ValueError("This book still has available copies.")
        if book.copies and not any(
                c.status != CopyStatus.CANCELED for c in book.copies):
            raise ValueError("No usable copy remains for this book.")
        return Reservation(None, self.user_id, book.book_id, at)

    def request_renewal(self, loan: BorrowRecord, max_renew: int,
                        max_days: int) -> bool:
        return self.is_active and loan.renew(max_renew, max_days)


@dataclass
class Librarian(User):
    @property
    def role(self) -> Role:
        return Role.LIBRARIAN

    @property
    def home_endpoint(self) -> str:
        return "librarian.readers"

    def manage_book(self, action: str, **values) -> dict:
        """Describe a validated catalog operation for the catalog service."""
        if action not in {"add_book", "edit_book", "add_copy", "edit_copy",
                          "retire_copy"}:
            raise ValueError("Unknown book action.")
        return {"action": action, **values}

    def check_out(self, copy: BookCopy, reader_id: int,
                  borrow_date: datetime, max_days: int) -> BorrowRecord:
        if copy.status not in (CopyStatus.AVAILABLE, CopyStatus.RESERVED):
            raise ValueError("This copy cannot be checked out.")
        copy.update_status(CopyStatus.BORROWED)
        return BorrowRecord(
            None, reader_id, copy.copy_id, self.user_id,
            borrow_date, borrow_date + timedelta(days=max_days),
            status=BorrowStatus.BORROWED)

    def check_in(self, copy: BookCopy, record: BorrowRecord,
                 condition: CopyCondition | str, at: datetime,
                 has_waiting: bool = False) -> BorrowRecord:
        if copy.status != CopyStatus.BORROWED or not record.is_open:
            raise ValueError("This copy is not currently borrowed.")
        cond = CopyCondition(condition)
        record.return_date = at
        record.return_condition = cond
        record.status = BorrowStatus.RETURNED
        copy.copy_condition = cond
        if cond == CopyCondition.INTACT:
            copy.update_status(CopyStatus.RESERVED if has_waiting
                               else CopyStatus.AVAILABLE)
        else:
            copy.update_status(CopyStatus.CANCELED)
        return record

    def record_fine(self, borrow_id: int, reason: FineReason | str,
                    amount: int) -> Fine:
        """Create a fine entry for a recorded loan violation (FR-LIB-09)."""
        return Fine(None, borrow_id, FineReason(reason), int(amount))

    def record_payment(self, fine: Fine, at: datetime) -> Fine:
        """Mark a counter cash payment (FR-LIB-13)."""
        fine.mark_paid(at)
        return fine

    def approve_card(self, reader: Reader, card_code: str) -> None:
        """Approve a pending reader and give the card its barcode."""
        reader.status = UserStatus.ACTIVE
        reader.card_code = card_code
        reader.failed_logins = 0
        reader.locked_until = None

    def reject_card(self, reader: Reader) -> None:
        reader.status = UserStatus.REJECTED

    def lock_reader(self, reader: Reader) -> None:
        """Lock a reader who broke the library rules (FR-LIB-11)."""
        reader.status = UserStatus.LOCKED

    def unlock_reader(self, reader: Reader) -> None:
        reader.status = UserStatus.ACTIVE


@dataclass
class Administrator(User):
    @property
    def role(self) -> Role:
        return Role.ADMIN

    @property
    def home_endpoint(self) -> str:
        return "admin.librarians"

    def view_reports(self, reports: dict) -> dict:
        """Return report data prepared by the report service (FR-ADM-05)."""
        return reports

    def manage_librarian(self, librarian: Librarian, action: str) -> None:
        """Create, lock, or unlock a staff account (FR-ADM-01)."""
        if action == "lock":
            librarian.status = UserStatus.LOCKED
        elif action == "unlock":
            librarian.status = UserStatus.ACTIVE
        else:
            raise ValueError(f"Unknown action: {action}")

    def configure_rules(self, values: Mapping[str, int]) -> dict[str, int]:
        """Check the five rules before they are saved (FR-ADM-04)."""
        clean: dict[str, int] = {}
        for key, value in values.items():
            try:
                rule_key = RuleKey(key)
            except ValueError as error:
                raise ValueError("Unknown library rule.") from error
            try:
                number = int(value)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    f"{rule_key.value} must be a whole number.") from error
            if number < 1:
                raise ValueError("A rule value must be a whole number above 0")
            clean[rule_key.value] = number
        return clean


class UserFactory:
    """Creates the right User subclass from a users row."""

    _classes: dict[Role, type[User]] = {
        Role.READER: Reader,
        Role.LIBRARIAN: Librarian,
        Role.ADMIN: Administrator,
    }

    @classmethod
    def from_row(cls, row: Mapping[str, Any]) -> User:
        role = Role(row["role"])
        fields = dict(
            user_id=row["user_id"],
            full_name=row["full_name"],
            email=row["email"],
            phone=row["phone"],
            password_hash=row["password_hash"],
            status=UserStatus(row["status"]),
            failed_logins=row["failed_logins"],
            locked_until=_parse_datetime(row["locked_until"]),
            student_id=_column(row, "student_id"),
            avatar_path=_column(row, "avatar_path"),
        )
        if role == Role.READER:
            fields["card_code"] = row["card_code"]
        return cls._classes[role](**fields)


def _column(row: Mapping[str, Any], name: str) -> Any:
    """Reads a column that older databases do not have yet."""
    return row[name] if name in row.keys() else None


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
