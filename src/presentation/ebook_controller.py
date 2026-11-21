from flask import abort, g, render_template, send_file

from business.ebook_service import EbookService
from common.exceptions import ValidationError
from presentation.access import roles_required
from presentation.base_controller import BaseController


class EbookController(BaseController):
    """Read online or download e-books (FR-RDR-07)."""

    name = "ebooks"
    url_prefix = "/ebooks"

    def __init__(self, ebooks: EbookService) -> None:
        super().__init__()
        self.ebooks = ebooks

    def add_routes(self) -> None:
        bp = self.blueprint
        bp.add_url_rule("/", "index", self.index)
        bp.add_url_rule("/<int:ebook_id>/read", "read", self.read)
        bp.add_url_rule("/<int:ebook_id>/download", "download",
                        self.download)

    @roles_required("READER")
    def index(self):
        return render_template("reader/ebooks.html",
                               ebooks=self.ebooks.all())

    @roles_required("READER", "LIBRARIAN")
    def read(self, ebook_id: int):
        ebook, path = self._file(ebook_id)
        if not ebook.can_read_online:
            abort(404)
        return send_file(path, mimetype=ebook.mimetype, as_attachment=False,
                         download_name=self._name(ebook))

    @roles_required("READER", "LIBRARIAN")
    def download(self, ebook_id: int):
        ebook, path = self._file(ebook_id)
        return send_file(path, mimetype=ebook.mimetype, as_attachment=True,
                         download_name=self._name(ebook))

    def _file(self, ebook_id: int):
        try:
            return self.ebooks.file_for(g.user, ebook_id)
        except ValidationError:
            abort(404)

    @staticmethod
    def _name(ebook) -> str:
        safe = "".join(c if c.isalnum() else "-" for c in ebook.title)
        stem = "-".join(part for part in safe.split("-") if part)[:80]
        return f"{stem or 'ebook'}.{ebook.file_format.value.lower()}"
