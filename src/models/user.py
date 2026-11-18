from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping

from models.enums import Role, UserStatus


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


@dataclass
class Reader(User):
    card_code: str | None = None

    @property
    def role(self) -> Role:
        return Role.READER

    @property
    def home_endpoint(self) -> str:
        return "reader.my_books"


@dataclass
class Librarian(User):
    @property
    def role(self) -> Role:
        return Role.LIBRARIAN

    @property
    def home_endpoint(self) -> str:
        return "librarian.checkout"


@dataclass
class Administrator(User):
    @property
    def role(self) -> Role:
        return Role.ADMIN

    @property
    def home_endpoint(self) -> str:
        return "admin.librarians"


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
        )
        if role == Role.READER:
            fields["card_code"] = row["card_code"]
        return cls._classes[role](**fields)


def _parse_datetime(value: Any) -> datetime | None:
    if value is None or isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))
