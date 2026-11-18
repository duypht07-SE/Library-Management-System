import os
import secrets
from pathlib import Path

from flask import (flash, g, redirect, render_template, request,
                   send_from_directory, url_for)

from business.auth_service import AuthService
from business.fine_service import FineService
from business.rule_service import RuleService
from common.exceptions import AuthenticationError, ValidationError
from config import Config
from presentation.access import roles_required
from presentation.base_controller import BaseController

READER = "READER"
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # FR-RDR-02


def _image_extension(data: bytes) -> str | None:
    """Accept only real PNG, JPEG, GIF, or WebP images."""
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return None


class ReaderController(BaseController):
    """Profile and password screens for a Reader (FR-RDR-02)."""

    name = "reader"

    def __init__(self, auth: AuthService, rules: RuleService,
                 config: Config, fines: FineService | None = None) -> None:
        super().__init__()
        self.auth = auth
        self.rules = rules
        self.config = config
        self.fines = fines

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/profile", "profile", self.profile,
                        methods=["GET", "POST"])
        bp.add_url_rule("/profile/password", "change_password",
                        self.change_password, methods=["POST"])
        bp.add_url_rule("/profile/avatar", "upload_avatar",
                        self.upload_avatar, methods=["POST"])
        bp.add_url_rule("/avatar/<path:filename>", "avatar", self.avatar)
        bp.add_url_rule("/fines", "fines", self.fines_page)

    @roles_required(READER)
    def profile(self):
        user = g.user
        if request.method == "POST":
            try:
                self.auth.update_profile(
                    user,
                    full_name=request.form.get("full_name", ""),
                    email=request.form.get("email", ""),
                    phone=request.form.get("phone", ""),
                    student_id=request.form.get("student_id", ""),
                )
            except ValidationError as error:
                flash(error.message, "error")
                return render_template("reader/profile.html", user=user), 400
            flash("Your profile has been updated.", "success")
            return redirect(url_for("reader.profile"))
        return render_template("reader/profile.html", user=user)

    @roles_required(READER)
    def fines_page(self):
        if self.fines is None:
            return render_template("errors/404.html"), 404
        return render_template("reader/fines.html",
                               fines=self.fines.view_fines(g.user))

    @roles_required(READER)
    def change_password(self):
        try:
            self.auth.change_password(
                g.user,
                current=request.form.get("current_password", ""),
                new=request.form.get("new_password", ""),
                confirmation=request.form.get("confirmation", ""),
            )
        except (AuthenticationError, ValidationError) as error:
            flash(str(getattr(error, "message", error)), "error")
            return redirect(url_for("reader.profile"))
        flash("Your password has been changed.", "success")
        return redirect(url_for("reader.profile"))

    @roles_required(READER)
    def upload_avatar(self):
        upload = request.files.get("avatar")
        if upload is None or not upload.filename:
            flash("Choose an image before uploading.", "error")
            return redirect(url_for("reader.profile"))
        data = upload.read(MAX_AVATAR_BYTES + 1)
        if len(data) > MAX_AVATAR_BYTES:
            flash("The avatar must be 2 MB or smaller.", "error")
            return redirect(url_for("reader.profile"))
        extension = _image_extension(data)
        if extension is None:
            flash("The avatar must be a PNG, JPEG, GIF, or WebP image.",
                  "error")
            return redirect(url_for("reader.profile"))

        avatar_dir = Path(self.config.AVATAR_DIR)
        avatar_dir.mkdir(parents=True, exist_ok=True)
        name = f"user-{g.user.user_id}-{secrets.token_hex(8)}{extension}"
        (avatar_dir / name).write_bytes(data)
        old_name = g.user.avatar_path
        self.auth.update_avatar(g.user, name)
        if old_name:
            old_path = (avatar_dir / old_name).resolve()
            if old_path.parent == avatar_dir.resolve() and old_path.exists():
                old_path.unlink()
        flash("Your avatar has been updated.", "success")
        return redirect(url_for("reader.profile"))

    @roles_required(READER)
    def avatar(self, filename: str):
        if (os.path.basename(filename) != filename
                or filename != g.user.avatar_path):
            return "", 404
        return send_from_directory(self.config.AVATAR_DIR, filename)
