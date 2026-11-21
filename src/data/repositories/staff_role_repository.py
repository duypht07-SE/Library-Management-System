import sqlite3

from data.repositories.base_repository import BaseRepository
from models import Permission, StaffRole


class StaffRoleRepository(BaseRepository):
    """Staff roles and their permissions (FR-ADM-02)."""

    def permissions(self) -> list[sqlite3.Row]:
        return self.db.fetch_all(
            "SELECT * FROM permissions ORDER BY permission_code")

    def all(self) -> list[StaffRole]:
        codes = self._codes()
        return [self._from_row(row, codes.get(row["role_id"], set()))
                for row in self.db.fetch_all(
                    "SELECT * FROM staff_roles ORDER BY role_id")]

    def member_counts(self) -> dict[int, int]:
        rows = self.db.fetch_all(
            "SELECT staff_role_id, COUNT(*) AS n FROM users"
            " WHERE staff_role_id IS NOT NULL GROUP BY staff_role_id")
        return {r["staff_role_id"]: r["n"] for r in rows}

    def find_by_id(self, role_id: int | None) -> StaffRole | None:
        if role_id is None:
            return None
        row = self.db.fetch_one(
            "SELECT * FROM staff_roles WHERE role_id = ?", (role_id,))
        if row is None:
            return None
        return self._from_row(row, self._codes(role_id).get(role_id, set()))

    def name_exists(self, name: str, exclude_id: int | None = None) -> bool:
        row = self.db.fetch_one(
            "SELECT 1 FROM staff_roles WHERE lower(name) = lower(?)"
            " AND role_id <> ?", (name, exclude_id or 0))
        return row is not None

    def save(self, role: StaffRole) -> StaffRole:
        with self.db.transaction() as conn:
            if role.role_id is None:
                cursor = conn.execute(
                    "INSERT INTO staff_roles (name, description)"
                    " VALUES (?, ?)", (role.name, role.description))
                role.role_id = cursor.lastrowid
            else:
                conn.execute(
                    "UPDATE staff_roles SET name = ?, description = ?"
                    " WHERE role_id = ?",
                    (role.name, role.description, role.role_id))
                conn.execute("DELETE FROM role_permissions WHERE role_id = ?",
                             (role.role_id,))
            conn.executemany(
                "INSERT INTO role_permissions VALUES (?, ?)",
                [(role.role_id, p.value) for p in sorted(role.permissions)])
        return role

    def delete(self, role_id: int) -> None:
        with self.db.transaction() as conn:
            conn.execute("DELETE FROM role_permissions WHERE role_id = ?",
                         (role_id,))
            conn.execute("DELETE FROM staff_roles WHERE role_id = ?",
                         (role_id,))

    def _codes(self, role_id: int | None = None) -> dict[int, set]:
        sql = "SELECT role_id, permission_code FROM role_permissions"
        params: tuple = ()
        if role_id is not None:
            sql += " WHERE role_id = ?"
            params = (role_id,)
        codes: dict[int, set] = {}
        for row in self.db.fetch_all(sql, params):
            codes.setdefault(row["role_id"], set()).add(
                Permission(row["permission_code"]))
        return codes

    @staticmethod
    def _from_row(row: sqlite3.Row, codes: set) -> StaffRole:
        return StaffRole(row["role_id"], row["name"], row["description"],
                         set(codes))
