import bcrypt


class PasswordHasher:
    """Salted Bcrypt hashes (NFR-SEC-01)."""

    def __init__(self, rounds: int = 12) -> None:
        self.rounds = rounds

    def hash(self, password: str) -> str:
        salt = bcrypt.gensalt(self.rounds)
        return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"),
                                  password_hash.encode("utf-8"))
        except ValueError:
            return False
