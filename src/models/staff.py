from dataclasses import dataclass, field
from datetime import datetime

from models.enums import Permission, ResetStatus


@dataclass
class StaffRole:
    """A named set of permissions for Librarians (FR-ADM-02)."""

    role_id: int | None
    name: str
    description: str = ""
    permissions: set[Permission] = field(default_factory=set)

    def has(self, permission: Permission | str) -> bool:
        return Permission(permission) in self.permissions

    def set_permissions(self, codes: list[str]) -> None:
        chosen = {Permission(code) for code in codes}
        if not chosen:
            raise ValueError("Choose at least one permission for the role.")
        self.permissions = chosen


@dataclass
class PasswordResetRequest:
    """A forgotten-password request waiting for an Administrator."""

    request_id: int | None
    user_id: int
    requested_at: datetime
    status: ResetStatus = ResetStatus.PENDING
    handled_by: int | None = None
    handled_at: datetime | None = None

    @property
    def is_pending(self) -> bool:
        return self.status == ResetStatus.PENDING

    def complete(self, admin_id: int, at: datetime) -> None:
        self._close(ResetStatus.COMPLETED, admin_id, at)

    def reject(self, admin_id: int, at: datetime) -> None:
        self._close(ResetStatus.REJECTED, admin_id, at)

    def _close(self, status: ResetStatus, admin_id: int,
               at: datetime) -> None:
        if not self.is_pending:
            raise ValueError("This request has already been handled.")
        self.status = status
        self.handled_by = admin_id
        self.handled_at = at


@dataclass
class AuditLog:
    """One recorded staff action or sign-in (FR-SYS-04, FR-ADM-08)."""

    log_id: int | None
    user_id: int | None
    action: str
    details: str
    created_at: datetime
    ip_address: str | None = None
    user_name: str | None = None
