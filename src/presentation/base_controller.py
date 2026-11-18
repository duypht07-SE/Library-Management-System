from abc import ABC, abstractmethod

from flask import Blueprint, Flask


class BaseController(ABC):
    """Base class for controllers: one Blueprint per group of pages."""

    name: str = ""
    url_prefix: str = ""

    def __init__(self) -> None:
        self.blueprint = Blueprint(self.name, __name__,
                                   url_prefix=self.url_prefix or None)

    @abstractmethod
    def add_routes(self) -> None:
        ...

    def register(self, app: Flask) -> None:
        self.add_routes()
        app.register_blueprint(self.blueprint)
