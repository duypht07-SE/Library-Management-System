from functools import wraps
from typing import Callable

from flask import abort, flash, g, redirect, request, session, url_for

from data.repositories import UserRepository
from models import User


def load_user(users: UserRepository) -> Callable[[], None]:
    """Put the signed-in account in g.user on every request (NFR-SEC-05)."""

    def before_request() -> None:
        g.user = None
        user_id = session.get("user_id")
        if user_id is None:
            return
        user = users.find_by_id(user_id)
        if user is None or not user.is_active:
            session.clear()
            flash("Your session has ended. Please sign in again.", "error")
            return
        g.user = user

    return before_request


def current_user() -> User | None:
    return getattr(g, "user", None)


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
