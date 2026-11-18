import sqlite3

from flask import flash, g, redirect, render_template, request, url_for

from business.account_service import AccountService
from business.catalog_service import CatalogService
from business.fine_service import FineService
from config import now
from common.exceptions import ValidationError
from presentation.access import roles_required
from presentation.base_controller import BaseController

LIBRARIAN = "LIBRARIAN"
READER_ACTIONS = {"approve", "reject", "lock", "unlock"}


class LibrarianController(BaseController):
    """Reader card approval and locks (FR-LIB-10, FR-LIB-11)."""

    name = "librarian"
    url_prefix = "/librarian"

    def __init__(self, accounts: AccountService,
                 catalog: CatalogService | None = None,
                 fines: FineService | None = None) -> None:
        super().__init__()
        self.accounts = accounts
        self.catalog = catalog
        self.fines = fines

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/", "index", self.index)
        bp.add_url_rule("/readers", "readers", self.readers)
        bp.add_url_rule("/readers/<int:reader_id>/<action>", "reader_action",
                        self.reader_action, methods=["POST"])
        bp.add_url_rule("/books", "books", self.books,
                        methods=["GET", "POST"])
        bp.add_url_rule("/books/<int:book_id>/edit", "edit_book",
                        self.edit_book, methods=["GET", "POST"])
        bp.add_url_rule("/books/<int:book_id>/copies", "add_copy",
                        self.add_copy, methods=["POST"])
        bp.add_url_rule("/copies/<int:copy_id>/edit", "edit_copy",
                        self.edit_copy, methods=["POST"])
        bp.add_url_rule("/copies/<int:copy_id>/retire", "retire_copy",
                        self.retire_copy, methods=["POST"])
        bp.add_url_rule("/fines", "fines", self.fines_page,
                        methods=["GET", "POST"])
        bp.add_url_rule("/fines/<int:fine_id>/payment", "fine_payment",
                        self.fine_payment, methods=["POST"])

    @roles_required(LIBRARIAN)
    def index(self):
        return redirect(url_for("librarian.readers"))

    @roles_required(LIBRARIAN)
    def readers(self):
        return render_template("librarian/readers.html",
                               readers=self.accounts.readers())

    @roles_required(LIBRARIAN)
    def books(self):
        if self.catalog is None:
            return render_template("errors/404.html"), 404
        if request.method == "POST":
            try:
                self.catalog.manage_book(g.user, "add_book", self._book_form())
                flash("Book added to the catalog.", "success")
                return redirect(url_for("librarian.books"))
            except (ValidationError, sqlite3.IntegrityError) as error:
                message = getattr(error, "message", "ISBN already exists.")
                flash(message, "error")
        return render_template("librarian/books.html",
                               books=self.catalog.books.all_books(),
                               form=self._book_form())

    @roles_required(LIBRARIAN)
    def edit_book(self, book_id: int):
        if self.catalog is None:
            return render_template("errors/404.html"), 404
        book = self.catalog.books.find_by_id(book_id)
        if book is None:
            return render_template("errors/404.html"), 404
        if request.method == "POST":
            try:
                self.catalog.manage_book(g.user, "edit_book",
                                         self._book_form(), book_id=book_id)
                flash("Book information updated.", "success")
                return redirect(url_for("librarian.books"))
            except (ValidationError, sqlite3.IntegrityError) as error:
                flash(getattr(error, "message", "ISBN already exists."),
                      "error")
        return render_template("librarian/book_edit.html", book=book)

    @roles_required(LIBRARIAN)
    def add_copy(self, book_id: int):
        if self.catalog is None:
            return render_template("errors/404.html"), 404
        try:
            self.catalog.manage_book(g.user, "add_copy", request.form.to_dict(),
                                     book_id=book_id)
            flash("Book copy added.", "success")
        except (ValidationError, sqlite3.IntegrityError) as error:
            flash(getattr(error, "message", "Barcode already exists."),
                  "error")
        return redirect(url_for("librarian.books"))

    @roles_required(LIBRARIAN)
    def edit_copy(self, copy_id: int):
        if self.catalog is None:
            return render_template("errors/404.html"), 404
        try:
            book_id = int(request.form.get("book_id", ""))
            self.catalog.manage_book(g.user, "edit_copy", request.form.to_dict(),
                                     book_id=book_id, copy_id=copy_id)
            flash("Copy details updated.", "success")
        except (ValueError, ValidationError, sqlite3.IntegrityError) as error:
            flash(getattr(error, "message", "Barcode already exists."),
                  "error")
        return redirect(url_for("librarian.books"))

    @roles_required(LIBRARIAN)
    def retire_copy(self, copy_id: int):
        if self.catalog is None:
            return render_template("errors/404.html"), 404
        try:
            self.catalog.manage_book(g.user, "retire_copy", {}, copy_id=copy_id)
            flash("Book copy retired.", "success")
        except ValidationError as error:
            flash(error.message, "error")
        return redirect(url_for("librarian.books"))

    @roles_required(LIBRARIAN)
    def fines_page(self):
        if self.fines is None:
            return render_template("errors/404.html"), 404
        if request.method == "POST":
            try:
                if request.form.get("action") == "payment":
                    self.fines.record_payment(
                        g.user, int(request.form.get("fine_id", "")), now())
                    flash("Cash payment recorded.", "success")
                else:
                    amount = int(request.form.get("amount", ""))
                    self.fines.record_fine(
                        g.user, int(request.form.get("borrow_id", "")),
                        request.form.get("reason", ""), amount)
                    flash("Fine recorded.", "success")
            except (ValueError, ValidationError) as error:
                flash(getattr(error, "message", "Enter valid fine details."),
                      "error")
        return render_template("librarian/fines.html",
                               fines=self.fines.all_fines())

    @roles_required(LIBRARIAN)
    def fine_payment(self, fine_id: int):
        if self.fines is None:
            return render_template("errors/404.html"), 404
        try:
            self.fines.record_payment(g.user, fine_id, now())
            flash("Cash payment recorded.", "success")
        except ValidationError as error:
            flash(error.message, "error")
        return redirect(url_for("librarian.fines"))

    @staticmethod
    def _book_form() -> dict:
        return {key: request.form.get(key, "") for key in
                ("isbn", "ddc_code", "title", "author", "category")}

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
