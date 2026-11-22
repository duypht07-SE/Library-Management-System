import sqlite3
from datetime import datetime, timedelta
from typing import Callable

from common.exceptions import (AuthenticationError,
                               TemporaryPasswordExpiredError, ValidationError)
from common.security import PasswordHasher
from common.validation import (validate_email, validate_full_name,
                               validate_password,
                               validate_password_confirmation,
                               validate_phone, validate_student_id)
from config import now
from data.repositories.user_repository import UserRepository, is_unique_error
from models import Reader, User, UserStatus


class AuthService:
    """Sign up, sign in, profile, and password changes (FR-GST-01/04)."""

    MAX_ATTEMPTS = 5       # NFR-SEC-06
    LOCK_MINUTES = 15      # NFR-SEC-06

    def __init__(self, users: UserRepository, hasher: PasswordHasher,
                 clock: Callable[[], datetime] = now) -> None:
        self.users = users
        self.hasher = hasher
        self.clock = clock

    def register(self, full_name: str, student_id: str, email: str,
                 phone: str, password: str,
                 confirmation: str) -> Reader:
        """Create a Reader with PENDING status (FR-GST-01)."""
        full_name = validate_full_name(full_name)
        student_id = validate_student_id(student_id)
        email = validate_email(email)
        phone = validate_phone(phone)
        validate_password(password)
        validate_password_confirmation(password, confirmation)
        self._check_duplicates(email, phone, student_id)

        reader = Reader(
            user_id=None,
            full_name=full_name,
            email=email,
            phone=phone,
            password_hash="",
            status=UserStatus.PENDING,
            student_id=student_id,
        )
        try:
            return self.users.create(reader, self.hasher.hash(password))
        except sqlite3.IntegrityError as error:
            if is_unique_error(error):
                raise ValidationError(
                    "Email, phone number, or Student/Staff ID is already "
                    "registered.") from error
            raise

    def authenticate(self, email: str, password: str) -> User:
        """Check the password, the account status, and the 5-try lock."""
        at = self.clock()
        user = self.users.find_by_email((email or "").strip())
        if user is None:
            raise AuthenticationError("Invalid email or password.")
        if user.is_login_locked(at):
            raise AuthenticationError(
                "Too many wrong passwords. Try again after "
                f"{user.locked_until:%H:%M}.")
        if not self.hasher.verify(password or "", user.password_hash):
            if self._record_failure(user, at):
                raise AuthenticationError(
                    "Too many wrong passwords. The account is locked for "
                    f"{self.LOCK_MINUTES} minutes.")
            raise AuthenticationError("Invalid email or password.")

        user.login(at)  # FR-GST-04: status checks with a clear message
        if user.temporary_password_expired(at):  # NFR-SEC-05
            raise TemporaryPasswordExpiredError(
                "This temporary password has expired. Please ask the library "
                "for a new one.")
        self.users.reset_failed_logins(user.user_id)
        user.failed_logins = 0
        user.locked_until = None
        return user

    def _record_failure(self, user: User, at: datetime) -> bool:
        """Count one wrong password; True means the account is now locked."""
        attempts = user.failed_logins + 1
        if attempts >= self.MAX_ATTEMPTS:
            until = at + timedelta(minutes=self.LOCK_MINUTES)
            self.users.record_failed_login(user.user_id, 0, until)
            user.failed_logins = 0
            user.locked_until = until
            return True
        self.users.record_failed_login(user.user_id, attempts, None)
        user.failed_logins = attempts
        return False

    def update_profile(self, user: User, full_name: str, email: str,
                       phone: str, student_id: str | None = None) -> User:
        """Update the user's own details (FR-RDR-02, NFR-SEC-04)."""
        full_name = validate_full_name(full_name)
        email = validate_email(email)
        phone = validate_phone(phone)
        student_id = (validate_student_id(student_id)
                      if student_id not in (None, "") else user.student_id)
        self._check_duplicates(email, phone, student_id,
                               exclude_id=user.user_id)
        user.update_profile(full_name=full_name, email=email, phone=phone,
                            student_id=student_id)
        try:
            self.users.update_profile(user)
        except sqlite3.IntegrityError as error:
            if is_unique_error(error):
                raise ValidationError(
                    "Email, phone number, or Student/Staff ID is already "
                    "used by another account.") from error
            raise
        return user

    def update_avatar(self, user: User, stored_name: str) -> None:
        user.update_profile(avatar_path=stored_name)
        self.users.update_profile(user)

    def change_password(self, user: User, current: str, new: str,
                        confirmation: str) -> None:
        """FR-RDR-02: the Reader can change their own password."""
        if user.temporary_password_expired(self.clock()):
            raise TemporaryPasswordExpiredError(
                "This temporary password has expired. Please ask the library "
                "for a new one.")
        if not self.hasher.verify(current or "", user.password_hash):
            raise AuthenticationError("The current password is incorrect.")
        validate_password(new, "New password")
        validate_password_confirmation(new, confirmation)
        password_hash = self.hasher.hash(new)
        self.users.update_password(user.user_id, password_hash)
        user.update_password(password_hash)

    def _check_duplicates(self, email: str, phone: str, student_id: str,
                          exclude_id: int | None = None) -> None:
        if self.users.email_exists(email, exclude_id):
            raise ValidationError("This email address is already registered.",
                                  "email")
        if self.users.phone_exists(phone, exclude_id):
            raise ValidationError("This phone number is already registered.",
                                  "phone")
        if self.users.student_id_exists(student_id, exclude_id):
            raise ValidationError(
                "This Student/Staff ID is already registered.", "student_id")
