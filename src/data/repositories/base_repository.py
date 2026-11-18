from data.database import Database


class BaseRepository:
    """Base class for all repositories: holds the database."""

    def __init__(self, db: Database) -> None:
        self.db = db
