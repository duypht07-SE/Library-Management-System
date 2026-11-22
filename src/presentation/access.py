from functools import wraps
from typing import Callable

from flask import abort, flash, g, redirect, request, session, url_for

from business.session_service import SESSION_ID_KEY, SessionService
from config import now_aware
from data.repositories import UserRepository
from models import User


PASSWORD_PAGES = {"auth.change_password", "auth.signout", "static"}


def load_user(users: UserRepository,
              roles=None,
              sessions: SessionService | None = None,
              clock=None) -> Callable[[], None]:
    """Validate the server-side session and set g.user (NFR-SEC-05)."""

    active_clock = clock or now_aware

    def clear_session(message: str, session_id: str | None = None) -> None:
        if sessions is not None and session_id:
            sessions.revoke(session_id)
        session.clear()
        flash(message, "error")

    def before_request() -> None:
        g.user = None
        if "user_id" in session:  # cookie from before server-side sessions
            clear_session("Your session has ended. Please sign in again.",
                          session.get(SESSION_ID_KEY))
            return
        session_id = session.get(SESSION_ID_KEY)
        if session_id is None:
            return
        if sessions is None:
            clear_session("Your session has ended. Please sign in again.",
                          session_id)
            return
        record = sessions.validate(session_id)
        if record is None:
            clear_session("Your session has ended. Please sign in again.",
                          session_id)
            return
        user = users.find_by_id(record.user_id)
        if user is None or not user.is_active:
            clear_session("Your session has ended. Please sign in again.",
                          session_id)
            return
        if user.temporary_password_expired(active_clock()):
            clear_session(
                "Your temporary password has expired. Please sign in again.",
                session_id)
            return
        g.user = roles.attach(user) if roles is not None else user

    return before_request


def current_user() -> User | None:
    return getattr(g, "user", None)


def rotate_current_session(sessions: SessionService | None,
                           user_id: int) -> None:
    """Replace the current session id after a privilege change."""
    if sessions is None:
        return
    old_session_id = session.get(SESSION_ID_KEY)
    session[SESSION_ID_KEY] = sessions.replace(old_session_id, user_id)


def require_password_change():
    """FR-ADM-03: a temporary password must be changed before anything."""
    user = current_user()
    if (user is not None and user.must_change_password
            and request.endpoint not in PASSWORD_PAGES):
        flash("Please change your temporary password before you continue.",
              "error")
        return redirect(url_for("auth.change_password"))
    return None


def permission_required(permission: str):
    """Check the staff role permission on every action (FR-SYS-04)."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                flash("Please sign in to continue.", "error")
                return redirect(url_for("auth.signin", next=request.path))
            if not user.can(permission):
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator


def roles_required(*roles: str):
    """Allow only the listed roles; typed URLs get 403 (NFR-SEC-03)."""

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            user = current_user()
            if user is None:
                flash("Please sign in to continue.", "error")
                return redirect(url_for("auth.signin", next=request.path))
            if roles and user.role.value not in roles:
                abort(403)
            return view(*args, **kwargs)

        return wrapper

    return decorator
