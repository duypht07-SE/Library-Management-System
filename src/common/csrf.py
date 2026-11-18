"""CSRF token for every form (NFR-SEC-07).

The token is kept in the session and must come back in the `csrf_token` field
of every POST/PUT/PATCH/DELETE request. No extra package is needed.
"""
import hmac
import secrets

from flask import abort, request, session

FIELD_NAME = "csrf_token"
SESSION_KEY = "_csrf_token"


def generate_token() -> str:
    token = session.get(SESSION_KEY)
    if not token:
        token = secrets.token_urlsafe(32)
        session[SESSION_KEY] = token
    return token


def _submitted_token() -> str:
    return (request.form.get(FIELD_NAME)
            or request.headers.get("X-CSRF-Token")
            or "")


def check_request() -> None:
    """Stop the request with 400 when the token is missing or wrong."""
    if request.method in {"GET", "HEAD", "OPTIONS", "TRACE"}:
        return
    expected = session.get(SESSION_KEY) or ""
    submitted = _submitted_token()
    if not expected or not submitted or not hmac.compare_digest(
            expected, submitted):
        abort(400, description="The form has expired. Reload the page.")


def init_app(app) -> None:
    app.jinja_env.globals["csrf_token"] = generate_token
