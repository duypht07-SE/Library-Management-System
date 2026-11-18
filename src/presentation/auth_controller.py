from flask import (flash, redirect, render_template, request, session,
                   url_for)

from business.auth_service import AuthService
from common.exceptions import AuthenticationError, ValidationError
from presentation.access import current_user
from presentation.base_controller import BaseController


class AuthController(BaseController):
    """Sign In and Create Account pages (FR-GST-01, FR-GST-04)."""

    name = "auth"

    def __init__(self, auth: AuthService) -> None:
        super().__init__()
        self.auth = auth

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/signin", "signin", self.signin,
                        methods=["GET", "POST"])
        bp.add_url_rule("/signout", "signout", self.signout,
                        methods=["POST"])
        bp.add_url_rule("/register", "register", self.register_page,
                        methods=["GET", "POST"])

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
                flash(error.message, "error")
                return render_template("auth/signin.html", form=form), 401
            session.clear()
            session["user_id"] = user.user_id
            session.permanent = True  # NFR-SEC-05: 30-minute idle timeout
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
