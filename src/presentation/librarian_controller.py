import sqlite3

from flask import flash, g, redirect, render_template, request, url_for

from business.account_service import AccountService
from business.catalog_service import CatalogService
from business.circulation_service import CirculationService
from business.ebook_service import EbookService
from business.fine_service import FineService
from business.inventory_service import InventoryService
from config import now
from common.exceptions import ValidationError
from models import Permission
from presentation.access import permission_required, roles_required
from presentation.base_controller import BaseController

LIBRARIAN = "LIBRARIAN"
READER_ACTIONS = {"approve", "reject", "lock", "unlock"}
FIRST_PAGE = [(Permission.CIRCULATION, "librarian.checkout"),
              (Permission.READER_CARDS, "librarian.readers"),
              (Permission.CATALOG, "librarian.books"),
              (Permission.FINES, "librarian.fines")]


class LibrarianController(BaseController):
    """Reader card approval and locks (FR-LIB-10, FR-LIB-11)."""

    name = "librarian"
    url_prefix = "/librarian"

    def __init__(self, accounts: AccountService,
                 catalog: CatalogService | None = None,
                 fines: FineService | None = None,
                 circulation: CirculationService | None = None,
                 inventory: InventoryService | None = None,
                 ebooks: EbookService | None = None) -> None:
        super().__init__()
        self.accounts = accounts
        self.catalog = catalog
        self.fines = fines
        self.circulation = circulation
        self.inventory = inventory
        self.ebooks = ebooks

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/", "index", self.index)
        bp.add_url_rule("/checkout", "checkout", self.checkout,
                        methods=["GET", "POST"])
        bp.add_url_rule("/checkin", "checkin", self.checkin,
                        methods=["GET", "POST"])
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
        bp.add_url_rule("/inventory", "inventory", self.inventory_page,
                        methods=["GET", "POST"])
        bp.add_url_rule("/books/<int:book_id>/ebooks", "upload_ebook",
                        self.upload_ebook, methods=["POST"])
        bp.add_url_rule("/ebooks/<int:ebook_id>/edit", "update_ebook",
                        self.update_ebook, methods=["POST"])
        bp.add_url_rule("/ebooks/<int:ebook_id>/delete", "delete_ebook",
                        self.delete_ebook, methods=["POST"])

    @roles_required(LIBRARIAN)
    def index(self):
        """Open the first screen that the staff role allows."""
        for permission, endpoint in FIRST_PAGE:
            if g.user.can(permission):
                return redirect(url_for(endpoint))
        return render_template("librarian/no_permission.html")

    @permission_required(Permission.CIRCULATION)
    def checkout(self):
        if self.circulation is None:
            return render_template("errors/404.html"), 404
        form = {"card_code": "", "barcode": ""}
        if request.method == "POST":
            form = {
                "card_code": request.form.get("card_code", "").strip(),
                "barcode": request.form.get("barcode", "").strip(),
            }
            try:
                rec = self.circulation.check_out(
                    g.user, form["card_code"], form["barcode"])
                flash(f"Book checked out. Due date: {rec.due_date:%d/%m/%Y}.",
                      "success")
                return redirect(url_for("librarian.checkout"))
            except ValidationError as error:
                flash(error.message, "error")
                return render_template(
                    "librarian/checkout.html",
                    open_loans=self.circulation.open_loans(),
                    form=form), 400
        return render_template(
            "librarian/checkout.html",
            open_loans=self.circulation.open_loans(),
            form=form)

    @permission_required(Permission.CIRCULATION)
    def checkin(self):
        if self.circulation is None:
            return render_template("errors/404.html"), 404
        form = {"barcode": "", "borrow_id": "", "condition": "INTACT",
                "damage_amount": ""}
        if request.method == "POST":
            form = {
                "barcode": request.form.get("barcode", "").strip(),
                "borrow_id": request.form.get("borrow_id", "").strip(),
                "condition": request.form.get("condition", "INTACT").strip(),
                "damage_amount": request.form.get("damage_amount", "").strip(),
            }
            try:
                borrow_id = (int(form["borrow_id"])
                             if form["borrow_id"] else None)
                amount = (int(form["damage_amount"])
                          if form["damage_amount"] else None)
                _, created = self.circulation.check_in(
                    g.user, form["condition"], form["barcode"],
                    borrow_id, amount)
                if created:
                    total = sum(f.amount for f in created)
                    flash(f"Book checked in. Total fine: {total:,} VND.",
                          "success")
                else:
                    flash("Book checked in.", "success")
                return redirect(url_for("librarian.checkin"))
            except ValidationError as error:
                flash(error.message, "error")
                return render_template(
                    "librarian/checkin.html",
                    open_loans=self.circulation.open_loans(),
                    form=form), 400
            except ValueError:
                flash("Enter valid numbers for loan and fine amount.", "error")
                return render_template(
                    "librarian/checkin.html",
                    open_loans=self.circulation.open_loans(),
                    form=form), 400
        return render_template(
            "librarian/checkin.html",
            open_loans=self.circulation.open_loans(),
            form=form)

    @permission_required(Permission.READER_CARDS)
    def readers(self):
        return render_template("librarian/readers.html",
                               readers=self.accounts.readers())

    @permission_required(Permission.CATALOG)
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

    @permission_required(Permission.CATALOG)
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
        ebooks = self.ebooks.for_book(book_id) if self.ebooks else []
        return render_template("librarian/book_edit.html", book=book,
                               ebooks=ebooks)

    @permission_required(Permission.CATALOG)
    def inventory_page(self):
        """Batch barcode scan against the catalog (FR-LIB-12)."""
        form = {"shelf": request.form.get("shelf", ""),
                "barcodes": request.form.get("barcodes", "")}
        result = None
        status = 200
        if request.method == "POST":
            try:
                result = self.inventory.check(g.user, form["shelf"],
                                              form["barcodes"])
            except ValidationError as error:
                flash(error.message, "error")
                status = 400
        return render_template("librarian/inventory.html", form=form,
                               shelves=self.inventory.shelves(),
                               result=result), status

    @permission_required(Permission.CATALOG)
    def upload_ebook(self, book_id: int):
        """Upload a PDF or EPUB for a book (FR-LIB-14)."""
        upload = request.files.get("file")
        try:
            ebook = self.ebooks.upload(
                g.user, book_id, request.form.get("title", ""),
                upload.read() if upload else b"")
            flash(f"E-book uploaded: {ebook.title}.", "success")
        except ValidationError as error:
            flash(error.message, "error")
        return redirect(url_for("librarian.edit_book", book_id=book_id))

    @permission_required(Permission.CATALOG)
    def update_ebook(self, ebook_id: int):
        upload = request.files.get("file")
        data = upload.read() if upload and upload.filename else None
        try:
            ebook = self.ebooks.update(g.user, ebook_id,
                                       request.form.get("title", ""), data)
            flash(f"E-book updated: {ebook.title}.", "success")
            book_id = ebook.book_id
        except ValidationError as error:
            flash(error.message, "error")
            book_id = self._ebook_book(ebook_id)
        return self._back_to_book(book_id)

    @permission_required(Permission.CATALOG)
    def delete_ebook(self, ebook_id: int):
        try:
            ebook = self.ebooks.remove(g.user, ebook_id)
            flash(f"E-book removed: {ebook.title}.", "success")
            book_id = ebook.book_id
        except ValidationError as error:
            flash(error.message, "error")
            book_id = None
        return self._back_to_book(book_id)

    def _ebook_book(self, ebook_id: int) -> int | None:
        ebook = self.ebooks.ebooks.find_by_id(ebook_id)
        return ebook.book_id if ebook else None

    @staticmethod
    def _back_to_book(book_id: int | None):
        if book_id is None:
            return redirect(url_for("librarian.books"))
        return redirect(url_for("librarian.edit_book", book_id=book_id))

    @permission_required(Permission.CATALOG)
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

    @permission_required(Permission.CATALOG)
    def edit_copy(self, copy_id: int):
        if self.catalog is None:
            return render_template("errors/404.html"), 404
        try:
            book_id = int(request.form.get("book_id", ""))
            self.catalog.manage_book(g.user, "edit_copy",
                                     request.form.to_dict(),
                                     book_id=book_id, copy_id=copy_id)
            flash("Copy details updated.", "success")
        except (ValueError, ValidationError, sqlite3.IntegrityError) as error:
            flash(getattr(error, "message", "Barcode already exists."),
                  "error")
        return redirect(url_for("librarian.books"))

    @permission_required(Permission.CATALOG)
    def retire_copy(self, copy_id: int):
        if self.catalog is None:
            return render_template("errors/404.html"), 404
        try:
            self.catalog.manage_book(g.user, "retire_copy", {}, copy_id=copy_id)
            flash("Book copy retired.", "success")
        except ValidationError as error:
            flash(error.message, "error")
        return redirect(url_for("librarian.books"))

    @permission_required(Permission.FINES)
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

    @permission_required(Permission.FINES)
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

    @permission_required(Permission.READER_CARDS)
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
