from flask import flash, g, redirect, render_template, request, url_for

from business.account_service import AccountService
from business.rule_service import RuleService
from common.exceptions import ValidationError
from presentation.access import roles_required
from presentation.base_controller import BaseController

ADMIN = "ADMIN"
RULE_FIELDS = {
    "MAX_BOOKS": ("max_books", "Maximum books per Reader"),
    "MAX_DAYS": ("max_days", "Maximum loan period (days)"),
    "MAX_RENEW": ("max_renew", "Maximum renewals per loan"),
    "HOLD_DAYS": ("hold_days", "Days a reserved book is held"),
    "DAILY_FINE": ("daily_fine", "Daily fine (VND)"),
}


class AdminController(BaseController):
    """Librarian accounts and library rules (FR-ADM-01, FR-ADM-04)."""

    name = "admin"
    url_prefix = "/admin"

    def __init__(self, accounts: AccountService, rules: RuleService) -> None:
        super().__init__()
        self.accounts = accounts
        self.rules = rules

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/", "index", self.index)
        bp.add_url_rule("/librarians", "librarians", self.librarians,
                        methods=["GET", "POST"])
        bp.add_url_rule("/librarians/<int:librarian_id>/edit",
                        "edit_librarian",
                        self.edit_librarian, methods=["GET", "POST"])
        bp.add_url_rule("/librarians/<int:librarian_id>/<action>",
                        "librarian_action", self.librarian_action,
                        methods=["POST"])
        bp.add_url_rule("/rules", "rules", self.rules_page,
                        methods=["GET", "POST"])

    @roles_required(ADMIN)
    def index(self):
        return redirect(url_for("admin.librarians"))

    @roles_required(ADMIN)
    def librarians(self):
        if request.method == "POST":
            form = self._librarian_form()
            try:
                librarian = self.accounts.create_librarian(
                    g.user,
                    full_name=form["full_name"], email=form["email"],
                    phone=form["phone"], password=form["password"],
                    student_id=form["student_id"])
            except ValidationError as error:
                flash(error.message, "error")
                return render_template(
                    "admin/librarians.html",
                    librarians=self.accounts.librarians(),
                    form=form), 400
            flash(f"Librarian account created for {librarian.full_name}.",
                  "success")
            return redirect(url_for("admin.librarians"))
        return render_template("admin/librarians.html",
                               librarians=self.accounts.librarians(),
                               form=self._empty_form())

    @roles_required(ADMIN)
    def edit_librarian(self, librarian_id: int):
        librarian = next(
            (u for u in self.accounts.librarians()
             if u.user_id == librarian_id), None)
        if librarian is None:
            return render_template("errors/404.html"), 404
        if request.method == "POST":
            form = self._librarian_form(include_password=False)
            try:
                self.accounts.update_librarian(
                    g.user, librarian_id,
                    full_name=form["full_name"], email=form["email"],
                    phone=form["phone"], student_id=form["student_id"])
            except ValidationError as error:
                flash(error.message, "error")
                return render_template(
                    "admin/librarian_form.html", librarian=librarian,
                    form=form), 400
            flash("Librarian information updated.", "success")
            return redirect(url_for("admin.librarians"))
        form = {
            "full_name": librarian.full_name,
            "email": librarian.email,
            "phone": librarian.phone,
            "student_id": librarian.student_id or "",
        }
        return render_template("admin/librarian_form.html",
                               librarian=librarian, form=form)

    @roles_required(ADMIN)
    def librarian_action(self, librarian_id: int, action: str):
        if action not in {"lock", "unlock"}:
            return render_template("errors/404.html"), 404
        try:
            librarian = self.accounts.set_librarian_status(
                g.user, librarian_id, action)
        except ValidationError as error:
            flash(error.message, "error")
            return redirect(url_for("admin.librarians"))
        flash(f"Account {action}ed for {librarian.full_name}.", "success")
        return redirect(url_for("admin.librarians"))

    @roles_required(ADMIN)
    def rules_page(self):
        if request.method == "POST":
            values = {}
            for key in RULE_FIELDS:
                values[key] = request.form.get(key, "")
            try:
                rules = self.rules.update_rules(g.user, values)
            except (ValidationError, ValueError) as error:
                message = getattr(error, "message", str(error))
                flash(message, "error")
                return render_template(
                    "admin/rules.html",
                    rules=self.rules.current_rules(),
                    fields=RULE_FIELDS), 400
            flash("Library rules saved. They apply immediately.", "success")
            return render_template("admin/rules.html", rules=rules,
                                   fields=RULE_FIELDS)
        return render_template("admin/rules.html",
                               rules=self.rules.current_rules(),
                               fields=RULE_FIELDS)

    def _librarian_form(self, include_password: bool = True) -> dict:
        form = {
            "full_name": request.form.get("full_name", "").strip(),
            "email": request.form.get("email", "").strip(),
            "phone": request.form.get("phone", "").strip(),
            "student_id": request.form.get("student_id", "").strip(),
            "password": "",
        }
        if include_password:
            form["password"] = request.form.get("password", "")
        return form

    @staticmethod
    def _empty_form() -> dict:
        return {"full_name": "", "email": "", "phone": "",
                "student_id": "", "password": ""}
