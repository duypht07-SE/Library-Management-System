"""Opaque, revocable server-side sessions (NFR-SEC-05)."""
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Callable

from config import local_aware, now_aware
from data.repositories.session_repository import SessionRepository

SESSION_ID_KEY = "sid"
TOKEN_BYTES = 32
MAX_TOKEN_LENGTH = 128


@dataclass(frozen=True)
class SessionRecord:
    user_id: int
    expires_at: datetime
    revoked_at: datetime | None


class SessionService:
    """Create, validate, rotate, expire, and revoke login sessions."""

    def __init__(self, sessions: SessionRepository,
                 lifetime: timedelta,
                 clock: Callable[[], datetime] = now_aware) -> None:
        self.sessions = sessions
        self.lifetime = lifetime
        self.clock = clock

    @staticmethod
    def _digest(session_id: str) -> str:
        return hashlib.sha256(session_id.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse(value: datetime | str) -> datetime:
        if isinstance(value, datetime):
            return local_aware(value)
        return local_aware(datetime.fromisoformat(str(value)))

    def _now(self) -> datetime:
        return local_aware(self.clock())

    def create(self, user_id: int) -> str:
        """Return a new opaque id and persist only its digest."""
        session_id = secrets.token_urlsafe(TOKEN_BYTES)
        at = self._now()
        self.sessions.create(self._digest(session_id), user_id, at,
                             at + self.lifetime)
        return session_id

    def replace(self, old_session_id: str | None, user_id: int) -> str:
        """Revoke any previous id, then create a fresh one."""
        if old_session_id:
            self.revoke(old_session_id)
        return self.create(user_id)

    def validate(self, session_id: str | None) -> SessionRecord | None:
        """Return session metadata only for a live, unrevoked id."""
        if (not session_id or not isinstance(session_id, str)
                or len(session_id) > MAX_TOKEN_LENGTH):
            return None
        row = self.sessions.find(self._digest(session_id))
        if row is None:
            return None
        at = self._now()
        expires_at = self._parse(row["expires_at"])
        revoked_at = (self._parse(row["revoked_at"])
                      if row["revoked_at"] is not None else None)
        if revoked_at is not None or expires_at <= at:
            return None
        # Sliding 30-minute window: activity extends this session only.
        self.sessions.touch(self._digest(session_id), at,
                            at + self.lifetime)
        return SessionRecord(int(row["user_id"]), expires_at, revoked_at)

    def revoke(self, session_id: str | None) -> bool:
        """Revoke one session; unknown ids are a harmless no-op."""
        if not session_id or not isinstance(session_id, str):
            return False
        return self.sessions.revoke(self._digest(session_id), self._now())

    def purge_expired(self) -> int:
        """Bound table growth without touching still-live sessions."""
        return self.sessions.purge_expired(self._now())
