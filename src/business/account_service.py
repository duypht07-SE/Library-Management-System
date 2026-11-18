import sqlite3

from common.exceptions import PermissionDenied, ValidationError
from common.security import PasswordHasher
from common.validation import (validate_email, validate_full_name,
                               validate_password, validate_phone,
                               validate_student_id)
from data.repositories.user_repository import UserRepository, is_unique_error
from models import Administrator, Librarian, Reader, Role, UserStatus


class AccountService:
    """Reader cards and Librarian accounts (FR-LIB-10/11, FR-ADM-01)."""

    def __init__(self, users: UserRepository, hasher: PasswordHasher) -> None:
        self.users = users
        self.hasher = hasher

    # --- Reader cards -----------------------------------------------------
    def readers(self) -> list[Reader]:
        return [u for u in self.users.find_readers()
                if isinstance(u, Reader)]

    def approve_reader(self, actor: Librarian, reader_id: int) -> Reader:
        reader = self._reader(reader_id)
        if reader.status != UserStatus.PENDING:
            raise ValidationError("Only a pending card can be approved.")
        card_code = self._next_card_code(reader)
        actor.approve_card(reader, card_code)
        self.users.activate_reader(reader.user_id, card_code)
        return reader

    def reject_reader(self, actor: Librarian, reader_id: int) -> Reader:
        reader = self._reader(reader_id)
        if reader.status != UserStatus.PENDING:
            raise ValidationError("Only a pending card can be rejected.")
        actor.reject_card(reader)
        self.users.update_status(reader.user_id, UserStatus.REJECTED)
        return reader

    def lock_reader(self, actor: Librarian, reader_id: int) -> Reader:
        reader = self._reader(reader_id)
        if reader.status != UserStatus.ACTIVE:
            raise ValidationError("Only an active card can be locked.")
        actor.lock_reader(reader)
        self.users.update_status(reader.user_id, UserStatus.LOCKED)
        return reader

    def unlock_reader(self, actor: Librarian, reader_id: int) -> Reader:
        reader = self._reader(reader_id)
        if reader.status != UserStatus.LOCKED:
            raise ValidationError("Only a locked card can be unlocked.")
        actor.unlock_reader(reader)
        self.users.update_status(reader.user_id, UserStatus.ACTIVE)
        return reader

    def _reader(self, reader_id: int) -> Reader:
        user = self.users.find_by_id(reader_id)
        if not isinstance(user, Reader):
            raise ValidationError("Reader not found.")
        return user

    def _next_card_code(self, reader: Reader) -> str:
        base = f"RD-{reader.user_id:04d}"
        code = base
        suffix = 2
        while self.users.find_by_card_code(code) is not None:
            code = f"{base}-{suffix}"
            suffix += 1
        return code

    # --- Librarian accounts ----------------------------------------------
    def librarians(self) -> list[Librarian]:
        return [u for u in self.users.find_by_role(Role.LIBRARIAN)
                if isinstance(u, Librarian)]

    def create_librarian(self, actor: Administrator, full_name: str,
                         email: str, phone: str, password: str,
                         student_id: str | None = None) -> Librarian:
        full_name = validate_full_name(full_name)
        email = validate_email(email)
        phone = validate_phone(phone)
        validate_password(password)
        student_id = (validate_student_id(student_id)
                      if student_id not in (None, "") else None)
        if self.users.email_exists(email):
            raise ValidationError("This email address is already registered.")
        if self.users.phone_exists(phone):
            raise ValidationError("This phone number is already registered.")
        if student_id and self.users.student_id_exists(student_id):
            raise ValidationError(
                "This Student/Staff ID is already registered.")
        librarian = Librarian(
            user_id=None, full_name=full_name, email=email, phone=phone,
            password_hash="", status=UserStatus.ACTIVE, student_id=student_id)
        try:
            return self.users.create(librarian, self.hasher.hash(password))
        except sqlite3.IntegrityError as error:
            if is_unique_error(error):
                raise ValidationError(
                    "Email, phone number, or Staff ID is already "
                    "registered.") from error
            raise

    def update_librarian(self, actor: Administrator, librarian_id: int,
                         full_name: str, email: str, phone: str,
                         student_id: str | None = None) -> Librarian:
        librarian = self._librarian(librarian_id)
        full_name = validate_full_name(full_name)
        email = validate_email(email)
        phone = validate_phone(phone)
        student_id = (validate_student_id(student_id)
                      if student_id not in (None, "")
                      else librarian.student_id)
        if self.users.email_exists(email, librarian_id):
            raise ValidationError("This email address is already registered.")
        if self.users.phone_exists(phone, librarian_id):
            raise ValidationError("This phone number is already registered.")
        if (student_id and
                self.users.student_id_exists(student_id, librarian_id)):
            raise ValidationError(
                "This Student/Staff ID is already registered.")
        librarian.update_profile(full_name=full_name, email=email,
                                 phone=phone, student_id=student_id)
        try:
            self.users.update_profile(librarian)
        except sqlite3.IntegrityError as error:
            if is_unique_error(error):
                raise ValidationError(
                    "Email, phone number, or Staff ID is already "
                    "registered.") from error
            raise
        return librarian

    def set_librarian_status(self, actor: Administrator, librarian_id: int,
                             action: str) -> Librarian:
        librarian = self._librarian(librarian_id)
        if action == "lock" and librarian.status != UserStatus.ACTIVE:
            raise ValidationError("Only an active account can be locked.")
        if action == "unlock" and librarian.status != UserStatus.LOCKED:
            raise ValidationError("Only a locked account can be unlocked.")
        if action not in {"lock", "unlock"}:
            raise PermissionDenied("Unknown account action.")
        actor.manage_librarian(librarian, action)
        self.users.update_status(librarian.user_id, librarian.status)
        return librarian

    def _librarian(self, librarian_id: int) -> Librarian:
        user = self.users.find_by_id(librarian_id)
        if not isinstance(user, Librarian):
            raise ValidationError("Librarian not found.")
        return user
