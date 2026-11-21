from flask import (flash, g, redirect, render_template, request, send_file,
                   url_for)

from business.audit_service import AuditService
from business.backup_service import BackupService
from business.password_reset_service import PasswordResetService
from business.role_service import RoleService
from common.exceptions import ValidationError
from presentation.access import roles_required
from presentation.base_controller import BaseController

ADMIN = "ADMIN"


class SystemController(BaseController):
    """Roles, password resets, audit log, backup (FR-ADM-02/03/06/07/08)."""

    name = "system"
    url_prefix = "/admin"

    def __init__(self, roles: RoleService, resets: PasswordResetService,
                 audit: AuditService, backups: BackupService) -> None:
        super().__init__()
        self.roles = roles
        self.resets = resets
        self.audit = audit
        self.backups = backups

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/roles", "roles", self.roles_page,
                        methods=["GET", "POST"])
        bp.add_url_rule("/roles/<int:role_id>/edit", "edit_role",
                        self.edit_role, methods=["GET", "POST"])
        bp.add_url_rule("/roles/<int:role_id>/delete", "delete_role",
                        self.delete_role, methods=["POST"])
        bp.add_url_rule("/password-resets", "password_resets",
                        self.password_resets, methods=["GET", "POST"])
        bp.add_url_rule("/password-resets/<int:request_id>/<action>",
                        "reset_action", self.reset_action, methods=["POST"])
        bp.add_url_rule("/audit-log", "audit_log", self.audit_log)
        bp.add_url_rule("/backups", "backups", self.backups_page,
                        methods=["GET", "POST"])
        bp.add_url_rule("/backups/upload", "upload_backup",
                        self.upload_backup, methods=["POST"])
        bp.add_url_rule("/backups/<name>/restore", "restore_backup",
                        self.restore_backup, methods=["POST"])
        bp.add_url_rule("/backups/<name>/download", "download_backup",
                        self.download_backup)

    # --- Roles (FR-ADM-02) ------------------------------------------------
    @roles_required(ADMIN)
    def roles_page(self):
        form = self._role_form()
        if request.method == "POST":
            try:
                role = self.roles.save_role(g.user, **form)
            except ValidationError as error:
                flash(error.message, "error")
                return self._render_roles(form), 400
            flash(f"Role created: {role.name}.", "success")
            return redirect(url_for("system.roles"))
        return self._render_roles(form)

    @roles_required(ADMIN)
    def edit_role(self, role_id: int):
        try:
            role = self.roles.find(role_id)
        except ValidationError:
            return render_template("errors/404.html"), 404
        if request.method == "POST":
            form = self._role_form()
            try:
                role = self.roles.save_role(g.user, role_id=role_id, **form)
            except ValidationError as error:
                flash(error.message, "error")
                return render_template(
                    "admin/role_form.html", role=role, form=form,
                    permissions=self.roles.permissions()), 400
            flash(f"Role updated: {role.name}.", "success")
            return redirect(url_for("system.roles"))
        form = {"name": role.name, "description": role.description,
                "codes": [p.value for p in role.permissions]}
        return render_template("admin/role_form.html", role=role, form=form,
                               permissions=self.roles.permissions())

    @roles_required(ADMIN)
    def delete_role(self, role_id: int):
        try:
            role = self.roles.delete_role(g.user, role_id)
            flash(f"Role deleted: {role.name}.", "success")
        except ValidationError as error:
            flash(error.message, "error")
        return redirect(url_for("system.roles"))

    def _render_roles(self, form: dict):
        return render_template("admin/roles.html",
                               roles=self.roles.all_roles(),
                               members=self.roles.member_counts(),
                               permissions=self.roles.permissions(),
                               form=form)

    @staticmethod
    def _role_form() -> dict:
        return {"name": request.form.get("name", "").strip(),
                "description": request.form.get("description", "").strip(),
                "codes": request.form.getlist("permissions")}

    # --- Password resets (FR-ADM-03) --------------------------------------
    @roles_required(ADMIN)
    def password_resets(self):
        issued = None
        status = 200
        if request.method == "POST":
            try:
                user, password = self.resets.reset_by_email(
                    g.user, request.form.get("email", ""))
                issued = self._issued(user, password)
            except ValidationError as error:
                flash(error.message, "error")
                status = 400
        return self._render_resets(issued), status

    @roles_required(ADMIN)
    def reset_action(self, request_id: int, action: str):
        if action not in {"reset", "reject"}:
            return render_template("errors/404.html"), 404
        try:
            if action == "reject":
                self.resets.reject_request(g.user, request_id)
                flash("Password reset request rejected.", "success")
                return redirect(url_for("system.password_resets"))
            user, password = self.resets.reset_for_request(g.user,
                                                           request_id)
        except ValidationError as error:
            flash(error.message, "error")
            return redirect(url_for("system.password_resets"))
        return self._render_resets(self._issued(user, password))

    def _issued(self, user, password: str) -> dict:
        # the password is shown once and never written to the audit log
        self.audit.record(g.user, "system.password_reset",
                          f"Temporary password issued to {user.email}",
                          request.remote_addr)
        return {"name": user.full_name, "email": user.email,
                "password": password}

    def _render_resets(self, issued: dict | None):
        return render_template("admin/password_resets.html",
                               requests=self.resets.pending(), issued=issued)

    # --- Audit log (FR-ADM-08) --------------------------------------------
    @roles_required(ADMIN)
    def audit_log(self):
        action = request.args.get("action", "")
        return render_template("admin/audit_log.html",
                               logs=self.audit.recent(action=action),
                               actions=self.audit.actions(), action=action)

    # --- Backup and restore (FR-ADM-06, FR-ADM-07) -------------------------
    @roles_required(ADMIN)
    def backups_page(self):
        if request.method == "POST":
            backup = self.backups.create(g.user)
            flash(f"Backup created: {backup.name}.", "success")
            return redirect(url_for("system.backups"))
        return render_template("admin/backups.html",
                               backups=self.backups.backups())

    @roles_required(ADMIN)
    def restore_backup(self, name: str):
        try:
            safety = self.backups.restore(g.user, name)
        except ValidationError as error:
            flash(error.message, "error")
            return redirect(url_for("system.backups"))
        flash(f"Database restored from {name}. The data before the restore "
              f"was saved as {safety.name}.", "success")
        return redirect(url_for("system.backups"))

    @roles_required(ADMIN)
    def upload_backup(self):
        upload = request.files.get("file")
        try:
            safety = self.backups.restore_upload(
                g.user, upload.read() if upload else b"")
        except ValidationError as error:
            flash(error.message, "error")
            return redirect(url_for("system.backups"))
        flash("Database restored from the uploaded file. The data before "
              f"the restore was saved as {safety.name}.", "success")
        return redirect(url_for("system.backups"))

    @roles_required(ADMIN)
    def download_backup(self, name: str):
        try:
            path = self.backups.path_of(name)
        except ValidationError:
            return render_template("errors/404.html"), 404
        return send_file(path, as_attachment=True, download_name=name,
                         mimetype="application/vnd.sqlite3")
