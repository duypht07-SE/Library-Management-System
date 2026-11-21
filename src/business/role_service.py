from common.exceptions import ValidationError
from data.repositories import StaffRoleRepository, UserRepository
from models import Administrator, Librarian, StaffRole, User


class RoleService:
    """Staff roles and permissions (FR-ADM-02, FR-SYS-04)."""

    def __init__(self, roles: StaffRoleRepository,
                 users: UserRepository) -> None:
        self.roles = roles
        self.users = users

    def all_roles(self) -> list[StaffRole]:
        return self.roles.all()

    def member_counts(self) -> dict[int, int]:
        return self.roles.member_counts()

    def permissions(self):
        return self.roles.permissions()

    def find(self, role_id: int) -> StaffRole:
        role = self.roles.find_by_id(role_id)
        if role is None:
            raise ValidationError("Staff role not found.")
        return role

    def attach(self, user: User | None) -> User | None:
        """Load the role of a signed-in Librarian for permission checks."""
        if isinstance(user, Librarian):
            user.staff_role = self.roles.find_by_id(user.staff_role_id)
        return user

    def save_role(self, admin: Administrator, name: str, description: str,
                  codes: list[str], role_id: int | None = None) -> StaffRole:
        role = self.find(role_id) if role_id else StaffRole(None, "")
        try:
            admin.manage_role(role, name, description, codes)
        except ValueError as error:
            raise ValidationError(str(error)) from error
        if self.roles.name_exists(role.name, role.role_id):
            raise ValidationError("A role with this name already exists.")
        return self.roles.save(role)

    def delete_role(self, admin: Administrator, role_id: int) -> StaffRole:
        role = self.find(role_id)
        if self.roles.member_counts().get(role_id):
            raise ValidationError(
                "Move the Librarians to another role before deleting it.")
        self.roles.delete(role_id)
        return role

    def assign_role(self, admin: Administrator, librarian_id: int,
                    role_id: int) -> Librarian:
        librarian = self.users.find_by_id(librarian_id)
        if not isinstance(librarian, Librarian):
            raise ValidationError("Librarian not found.")
        admin.assign_role(librarian, self.find(role_id))
        self.users.assign_staff_role(librarian_id, role_id)
        return librarian
