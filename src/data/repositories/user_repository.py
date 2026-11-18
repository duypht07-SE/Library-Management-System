from data.repositories.base_repository import BaseRepository
from models import Role, User, UserFactory


class UserRepository(BaseRepository):
    """Reads accounts (Store D1) and returns the right User subclass."""

    def find_by_id(self, user_id: int) -> User | None:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE user_id = ?", (user_id,))
        return UserFactory.from_row(row) if row else None

    def find_by_email(self, email: str) -> User | None:
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE lower(email) = lower(?)", (email,))
        return UserFactory.from_row(row) if row else None

    def find_by_role(self, role: Role) -> list[User]:
        rows = self.db.fetch_all(
            "SELECT * FROM users WHERE role = ? ORDER BY user_id",
            (role.value,))
        return [UserFactory.from_row(r) for r in rows]
