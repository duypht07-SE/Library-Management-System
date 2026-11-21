from datetime import datetime
from typing import Callable

from config import now
from data.repositories import AuditRepository
from models import AuditLog, User


class AuditService:
    """Records and shows the audit log (FR-SYS-04, FR-ADM-08)."""

    def __init__(self, audit: AuditRepository,
                 clock: Callable[[], datetime] = now) -> None:
        self.audit = audit
        self.clock = clock

    def record(self, user: User | None, action: str, details: str,
               ip_address: str | None = None) -> None:
        user_id = user.user_id if user is not None else None
        self.audit.add(user_id, action, details, ip_address, self.clock())

    def recent(self, user_id: int | None = None, action: str = "",
               limit: int = 200) -> list[AuditLog]:
        return self.audit.recent(limit, user_id, action)

    def actions(self) -> list[str]:
        return self.audit.actions()
