from flask import (flash, redirect, render_template, request, session,
                   url_for)

from business.audit_service import AuditService
from business.auth_service import AuthService
from business.password_reset_service import PasswordResetService
from common.exceptions import AuthenticationError, ValidationError
from presentation.access import current_user
from presentation.base_controller import BaseController

RESET_SENT = ("If the email address and phone number match an account, the "
              "request has been sent to the Administrator. Collect your "
              "temporary password at the library desk.")


class AuthController(BaseController):
    """Sign In, Create Account, and passwords (FR-GST-01/04/05)."""

    name = "auth"

    def __init__(self, auth: AuthService,
                 resets: PasswordResetService | None = None,
                 audit: AuditService | None = None) -> None:
        super().__init__()
        self.auth = auth
        self.resets = resets
        self.audit = audit

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/signin", "signin", self.signin,
                        methods=["GET", "POST"])
        bp.add_url_rule("/signout", "signout", self.signout,
                        methods=["POST"])
        bp.add_url_rule("/register", "register", self.register_page,
                        methods=["GET", "POST"])
        bp.add_url_rule("/forgot-password", "forgot_password",
                        self.forgot_password, methods=["GET", "POST"])
        bp.add_url_rule("/account/password", "change_password",
                        self.change_password, methods=["GET", "POST"])

    def signin(self):
        if current_user() is not None:
            return redirect(url_for("guest.home"))
        form = {"email": ""}
        if request.method == "POST":
            form["email"] = request.form.get("email", "").strip()
            try:
                user = self.auth.authenticate(
                    form["email"], request.form.get("password", ""))
            except AuthenticationError as error:
                self._log(None, "SIGN_IN_FAILED",
                          f"{form['email'][:100]}: {error.message}")
                flash(error.message, "error")
                return render_template("auth/signin.html", form=form), 401
            session.clear()
            session["user_id"] = user.user_id
            session.permanent = True  # NFR-SEC-05: 30-minute idle timeout
            self._log(user, "SIGN_IN", f"{user.role.value.title()} signed in")
            if user.must_change_password:
                flash("You signed in with a temporary password. Please "
                      "choose a new password.", "success")
                return redirect(url_for("auth.change_password"))
            flash(f"Welcome back, {user.full_name}.", "success")
            target = request.args.get("next", "")
            if target.startswith("/") and not target.startswith("//"):
                return redirect(target)
            return redirect(url_for("guest.home"))
        return render_template("auth/signin.html", form=form)

    def signout(self):
        user = current_user()
        if user is not None:
            user.logout()
        session.clear()
        flash("You have signed out.", "success")
        return redirect(url_for("guest.home"))

    def register_page(self):
        if current_user() is not None:
            return redirect(url_for("guest.home"))
        form = {"full_name": "", "student_id": "", "email": "", "phone": ""}
        if request.method == "POST":
            for field in form:
                form[field] = request.form.get(field, "").strip()
            try:
                reader = self.auth.register(
                    full_name=form["full_name"],
                    student_id=form["student_id"],
                    email=form["email"],
                    phone=form["phone"],
                    password=request.form.get("password", ""),
                    confirmation=request.form.get("confirmation", ""),
                )
            except ValidationError as error:
                flash(error.message, "error")
                return render_template("auth/register.html", form=form), 400
            flash(
                f"Account created for {reader.full_name}. A librarian will "
                "approve your card before you can borrow books.", "success")
            return redirect(url_for("auth.signin"))
        return render_template("auth/register.html", form=form)

    def forgot_password(self):
        if current_user() is not None:
            return redirect(url_for("auth.change_password"))
        form = {"email": "", "phone": ""}
        if request.method == "POST" and self.resets is not None:
            for field in form:
                form[field] = request.form.get(field, "").strip()
            try:
                user = self.resets.request_reset(form["email"],
                                                 form["phone"])
            except ValidationError as error:
                flash(error.message, "error")
                return render_template("auth/forgot_password.html",
                                       form=form), 400
            if user is not None:
                self._log(user, "PASSWORD_RESET_REQUEST",
                          f"Reset requested for {user.email}")
            flash(RESET_SENT, "success")
            return redirect(url_for("auth.signin"))
        return render_template("auth/forgot_password.html", form=form)

    def change_password(self):
        user = current_user()
        if user is None:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("auth.signin", next=request.path))
        if request.method == "POST":
            try:
                self.auth.change_password(
                    user,
                    current=request.form.get("current_password", ""),
                    new=request.form.get("new_password", ""),
                    confirmation=request.form.get("confirmation", ""))
            except (AuthenticationError, ValidationError) as error:
                flash(error.message, "error")
                return render_template("auth/change_password.html"), 400
            flash("Your password has been changed.", "success")
            return redirect(url_for(user.home_endpoint))
        return render_template("auth/change_password.html")

    def _log(self, user, action: str, details: str) -> None:
        if self.audit is not None:
            self.audit.record(user, action, details, request.remote_addr)
