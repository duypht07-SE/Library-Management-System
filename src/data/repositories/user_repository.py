import sqlite3
from datetime import datetime

from data.repositories.base_repository import BaseRepository
from config import now
from models import Role, User, UserFactory, UserStatus


class UserRepository(BaseRepository):
    """Reads and writes accounts (Store D1)."""

    def find_by_id(self, user_id: int) -> User | None:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?", (user_id,))
        return UserFactory.from_row(row) if row else None

    def find_by_email(self, email: str) -> User | None:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE lower(email) = lower(?)", (email,))
        return UserFactory.from_row(row) if row else None

    def find_by_card_code(self, card_code: str) -> User | None:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE lower(card_code) = lower(?)",
            (card_code,))
        return UserFactory.from_row(row) if row else None

    def find_by_role(self, role: Role) -> list[User]:
        rows = self.db.fetch_all(
            "SELECT * FROM users WHERE role = ? ORDER BY user_id",
            (role.value,))
        return [UserFactory.from_row(r) for r in rows]

    def find_readers(self) -> list[User]:
        rows = self.db.fetch_all(
            "SELECT * FROM users WHERE role = 'READER'"
            " ORDER BY CASE status WHEN 'PENDING' THEN 0 ELSE 1 END, user_id")
        return [UserFactory.from_row(r) for r in rows]

    def create(self, user: User, password_hash: str) -> User:
        """Insert a new account and put the new id on the object."""
        card_code = getattr(user, "card_code", None)
        user.password_hash = password_hash
        with self.db.transaction() as conn:
            cursor = conn.execute(
                "INSERT INTO users (role, card_code, student_id, full_name,"
                " email, phone, password_hash, status, avatar_path, created_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (user.role.value, card_code, user.student_id, user.full_name,
                 user.email, user.phone, password_hash, user.status.value,
                 user.avatar_path, now().isoformat(sep=" ")))
            user.user_id = cursor.lastrowid
        return user

    def update_profile(self, user: User) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE users SET full_name = ?, email = ?, phone = ?,"
                " student_id = ?, avatar_path = ? WHERE user_id = ?",
                (user.full_name, user.email, user.phone, user.student_id,
                 user.avatar_path, user.user_id))

    def update_password(self, user_id: int, password_hash: str) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE users SET password_hash = ?, failed_logins = 0,"
                " locked_until = NULL WHERE user_id = ?",
                (password_hash, user_id))

    def update_status(self, user_id: int, status: UserStatus) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE users SET status = ?, failed_logins = 0,"
                " locked_until = NULL WHERE user_id = ?",
                (status.value, user_id))

    def update_card_code(self, user_id: int, card_code: str) -> None:
        with self.db.transaction() as conn:
            conn.execute("UPDATE users SET card_code = ? WHERE user_id = ?",
                         (card_code, user_id))

    def activate_reader(self, user_id: int, card_code: str) -> None:
        """Approve a card in one step: status plus card barcode (FR-LIB-10)."""
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE users SET status = 'ACTIVE', card_code = ?,"
                " failed_logins = 0, locked_until = NULL WHERE user_id = ?",
                (card_code, user_id))

    def record_failed_login(self, user_id: int, failed_logins: int,
                            locked_until: datetime | None) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE users SET failed_logins = ?, locked_until = ?"
                " WHERE user_id = ?",
                (failed_logins,
                 locked_until.isoformat() if locked_until else None, user_id))

    def reset_failed_logins(self, user_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute(
                "UPDATE users SET failed_logins = 0, locked_until = NULL"
                " WHERE user_id = ?", (user_id,))

    def email_exists(self, email: str, exclude_id: int | None = None) -> bool:
        return self._exists("email", email, exclude_id)

    def phone_exists(self, phone: str, exclude_id: int | None = None) -> bool:
        return self._exists("phone", phone, exclude_id)

    def student_id_exists(self, student_id: str,
                          exclude_id: int | None = None) -> bool:
        return self._exists("student_id", student_id, exclude_id)

    def _exists(self, column: str, value: str,
                exclude_id: int | None) -> bool:
        sql = (f"SELECT 1 FROM users WHERE lower({column}) = lower(?)")
        params: list[object] = [value]
        if exclude_id is not None:
            sql += " AND user_id <> ?"
            params.append(exclude_id)
        return self.db.fetch_one(sql, tuple(params)) is not None

    def count_by_role(self, role: Role) -> int:
        row = self.db.fetch_one(
            "SELECT COUNT(*) AS total FROM users WHERE role = ?",
            (role.value,))
        return int(row["total"])


def is_unique_error(error: sqlite3.IntegrityError) -> bool:
    """True when an INSERT hit a UNIQUE column (email, phone, id)."""
    return "UNIQUE" in str(error).upper()
