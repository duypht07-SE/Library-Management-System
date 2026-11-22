import secrets
import string
from datetime import datetime
from typing import Callable

from common.exceptions import ValidationError
from common.security import PasswordHasher
from common.validation import validate_email, validate_phone
from config import local_aware, now
from data.repositories import PasswordResetRepository, UserRepository
from models import Administrator, Role, User

TEMP_PASSWORD_LENGTH = 10


def make_temporary_password() -> str:
    """Random letters and digits that pass validate_password."""
    alphabet = string.ascii_letters + string.digits
    while True:
        password = "".join(secrets.choice(alphabet)
                           for _ in range(TEMP_PASSWORD_LENGTH))
        if (any(c.isalpha() for c in password)
                and any(c.isdigit() for c in password)):
            return password


class PasswordResetService:
    """Forgotten passwords (FR-GST-05) and temporary ones (FR-ADM-03)."""

    def __init__(self, users: UserRepository,
                 resets: PasswordResetRepository, hasher: PasswordHasher,
                 clock: Callable[[], datetime] = now) -> None:
        self.users = users
        self.resets = resets
        self.hasher = hasher
        self.clock = clock

    def request_reset(self, email: str, phone: str) -> User | None:
        """Save a request when email and phone match a Reader/Librarian.

        The page shows the same message either way, so nobody can find
        out which emails are registered.
        """
        email = validate_email(email)
        phone = validate_phone(phone)
        user = self.users.find_by_email_and_phone(email, phone)
        if user is None or user.role == Role.ADMIN:
            return None
        self.resets.create(user.user_id, self.clock())
        return user

    def pending(self):
        return self.resets.pending()

    def reset_for_request(self, admin: Administrator,
                          request_id: int) -> tuple[User, str]:
        request = self.resets.find_by_id(request_id)
        if request is None or not request.is_pending:
            raise ValidationError("This request has already been handled.")
        return self._reset(admin, request.user_id)

    def reset_by_email(self, admin: Administrator,
                       email: str) -> tuple[User, str]:
        user = self.users.find_by_email(validate_email(email))
        if user is None:
            raise ValidationError("No account uses this email address.")
        return self._reset(admin, user.user_id)

    def reject_request(self, admin: Administrator, request_id: int) -> None:
        request = self.resets.find_by_id(request_id)
        if request is None:
            raise ValidationError("Request not found.")
        try:
            request.reject(admin.user_id, self.clock())
        except ValueError as error:
            raise ValidationError(str(error)) from error
        with self.users.db.transaction() as conn:
            self.resets.close(request, conn)

    def _reset(self, admin: Administrator, user_id: int) -> tuple[User, str]:
        user = self.users.find_by_id(user_id)
        if user is None:
            raise ValidationError("Account not found.")
        password = make_temporary_password()
        password_hash = self.hasher.hash(password)
        at = self.clock()
        issued_at = local_aware(at)
        try:
            admin.reset_password(user, password_hash, issued_at=issued_at)
        except ValueError as error:
            raise ValidationError(str(error)) from error
        with self.users.db.transaction() as conn:  # NFR-REL-02
            self.users.set_temporary_password(user_id, password_hash,
                                              issued_at, conn)
            self.resets.close_all_for(user_id, admin.user_id, at, conn)
        return user, password
