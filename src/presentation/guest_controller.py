from flask import render_template, request

from business.catalog_service import CatalogService
from business.rule_service import RuleService
from presentation.base_controller import BaseController


class GuestController(BaseController):
    """Pages for visitors who have not signed in."""

    name = "guest"

    def __init__(self, catalog: CatalogService, rules: RuleService) -> None:
        super().__init__()
        self.catalog = catalog
        self.rules = rules

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/", "home", self.home)
        bp.add_url_rule("/policies", "policies", self.policies)
        bp.add_url_rule("/help", "help", self.help)
        bp.add_url_rule("/search", "search", self.search)

    def home(self):
        return render_template("guest/home.html",
                               new_books=self.catalog.new_books())

    def policies(self):
        return render_template("guest/policies.html",
                               rules=self.rules.current_rules())

    def help(self):
        return render_template("guest/help.html")

    def search(self):
        # TODO(0.3.0, Sang): load and show the matching books
        return render_template(
            "guest/search.html",
            keyword=request.args.get("q", "").strip(),
            category=request.args.get("category", ""),
        )
