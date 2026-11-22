"""Errors that a page can show to the user (NFR-USA-03)."""


class ValidationError(ValueError):
    """Input from a form is not valid."""

    def __init__(self, message: str, field: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.field = field


class AuthenticationError(Exception):
    """The account cannot sign in or the password is wrong."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class TemporaryPasswordExpiredError(AuthenticationError):
    """The temporary password was valid but its 24-hour window has ended."""


class PermissionDenied(Exception):
    """The signed-in user does not have the role for this action."""
