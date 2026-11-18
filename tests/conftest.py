import pytest

from app import LibraryApp
from config import TestConfig
from data.database import Database


@pytest.fixture
def database(tmp_path):
    db = Database(tmp_path / "test.db")
    db.initialize(seed=True)
    return db


@pytest.fixture
def library_app(tmp_path):
    return LibraryApp(TestConfig(tmp_path / "app.db"))


@pytest.fixture
def client(library_app):
    return library_app.flask.test_client()
