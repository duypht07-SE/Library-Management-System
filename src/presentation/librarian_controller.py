from flask import flash, g, redirect, render_template, request, url_for

from business.account_service import AccountService
from common.exceptions import ValidationError
from presentation.access import roles_required
from presentation.base_controller import BaseController

LIBRARIAN = "LIBRARIAN"
READER_ACTIONS = {"approve", "reject", "lock", "unlock"}


class LibrarianController(BaseController):
    """Reader card approval and locks (FR-LIB-10, FR-LIB-11)."""

    name = "librarian"
    url_prefix = "/librarian"

    def __init__(self, accounts: AccountService) -> None:
        super().__init__()
        self.accounts = accounts

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/", "index", self.index)
        bp.add_url_rule("/readers", "readers", self.readers)
        bp.add_url_rule("/readers/<int:reader_id>/<action>", "reader_action",
                        self.reader_action, methods=["POST"])

    @roles_required(LIBRARIAN)
    def index(self):
        return redirect(url_for("librarian.readers"))

    @roles_required(LIBRARIAN)
    def readers(self):
        return render_template("librarian/readers.html",
                               readers=self.accounts.readers())

    @roles_required(LIBRARIAN)
    def reader_action(self, reader_id: int, action: str):
        if action not in READER_ACTIONS:
            return render_template("errors/404.html"), 404
        try:
            reader = self._run_action(g.user, reader_id, action)
        except ValidationError as error:
            flash(error.message, "error")
            return redirect(url_for("librarian.readers"))
        messages = {
            "approve": f"Card {reader.card_code} approved for "
                       f"{reader.full_name}.",
            "reject": f"Registration rejected for {reader.full_name}.",
            "lock": f"Card locked for {reader.full_name}.",
            "unlock": f"Card unlocked for {reader.full_name}.",
        }
        flash(messages[action], "success")
        return redirect(url_for("librarian.readers"))

    def _run_action(self, actor, reader_id: int, action: str):
        if action == "approve":
            return self.accounts.approve_reader(actor, reader_id)
        if action == "reject":
            return self.accounts.reject_reader(actor, reader_id)
        if action == "lock":
            return self.accounts.lock_reader(actor, reader_id)
        return self.accounts.unlock_reader(actor, reader_id)
