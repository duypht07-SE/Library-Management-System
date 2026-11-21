from flask import Response, request, session

from business.audit_service import AuditService
from presentation.access import current_user

STAFF_ROLES = {"LIBRARIAN", "ADMIN"}


def audit_staff_actions(audit: AuditService):
    """Log every successful POST by a Librarian or Admin (FR-SYS-04).

    A successful action ends with a redirect and a "success" message, so
    the message itself becomes the log details.
    """

    def after_request(response: Response) -> Response:
        user = current_user()
        if (request.method != "POST" or user is None
                or user.role.value not in STAFF_ROLES
                or response.status_code != 302):
            return response
        flashes = session.get("_flashes") or []
        messages = [text for category, text in flashes
                    if category == "success"]
        if messages:
            audit.record(user, request.endpoint or "unknown", messages[-1],
                         request.remote_addr)
        return response

    return after_request
