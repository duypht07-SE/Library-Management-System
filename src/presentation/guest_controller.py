from flask import render_template, request

from presentation.access import current_user

from business.catalog_service import CatalogService
from business.rule_service import RuleService
from presentation.base_controller import BaseController


class GuestController(BaseController):
    """Pages for visitors who have not signed in."""

    name = "guest"

    def __init__(self, catalog: CatalogService, rules: RuleService,
                 ebooks=None, circulation=None) -> None:
        super().__init__()
        self.catalog = catalog
        self.rules = rules
        self.ebooks = ebooks
        self.circulation = circulation

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/", "home", self.home)
        bp.add_url_rule("/policies", "policies", self.policies)
        bp.add_url_rule("/help", "help", self.help)
        bp.add_url_rule("/search", "search", self.search)
        bp.add_url_rule("/books/<int:book_id>", "book_detail",
                        self.book_detail)

    def home(self):
        return render_template("guest/home.html",
                               new_books=self.catalog.new_books())

    def policies(self):
        return render_template("guest/policies.html",
                               rules=self.rules.current_rules())

    def help(self):
        return render_template("guest/help.html")

    def search(self):
        keyword = request.args.get("q", "").strip()
        category = request.args.get("category", "")
        page_size = 25
        page = max(1, request.args.get("page", 1, type=int))
        offset = (page - 1) * page_size
        books = [] if offset > 2**63 - 1 else self.catalog.search(
            keyword, category, limit=page_size + 1, offset=offset)
        return render_template(
            "guest/search.html", keyword=keyword, category=category,
            books=books[:page_size], page=page, has_next=len(books) > page_size,
        )

    def book_detail(self, book_id: int):
        book = self.catalog.books.find_by_id(book_id)
        if book is None:
            return render_template("errors/404.html"), 404
        ebooks = self.ebooks.for_book(book_id) if self.ebooks else []
        user = current_user()
        reader_status = ""
        if (self.circulation is not None and user is not None
                and user.role.value == "READER"):
            reader_status = self.circulation.reader_status_for_book(
                user, book_id)
        return render_template("guest/book_detail.html", book=book,
                               ebooks=ebooks, reader_status=reader_status)
