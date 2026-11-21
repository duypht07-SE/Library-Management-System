import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable

from common.exceptions import ValidationError
from config import now
from data.database import Database, is_sqlite_backup
from models import Administrator

NAME_PATTERN = re.compile(r"^library-\d{8}-\d{6}(-\d+)?(-[a-z]+)?\.db$")
MAX_BACKUP_BYTES = 100 * 1024 * 1024


@dataclass(frozen=True)
class BackupFile:
    name: str
    size: int
    created_at: datetime

    @property
    def size_label(self) -> str:
        return f"{max(1, self.size // 1024):,} KB"


class BackupService:
    """Back up (FR-ADM-06) and restore (FR-ADM-07) the database."""

    def __init__(self, database: Database, backup_dir: Path,
                 clock: Callable[[], datetime] = now) -> None:
        self.database = database
        self.backup_dir = Path(backup_dir)
        self.clock = clock

    def backups(self) -> list[BackupFile]:
        if not self.backup_dir.is_dir():
            return []
        files = [p for p in self.backup_dir.iterdir()
                 if p.is_file() and NAME_PATTERN.match(p.name)]
        files.sort(key=lambda p: (p.stat().st_mtime_ns, p.name),
                   reverse=True)
        return [BackupFile(p.name, p.stat().st_size,
                           datetime.fromtimestamp(p.stat().st_mtime))
                for p in files]

    def create(self, admin: Administrator, label: str = "") -> BackupFile:
        target = self._new_path(label)
        self.database.backup_to(target)
        return BackupFile(target.name, target.stat().st_size, self.clock())

    def restore(self, admin: Administrator, name: str) -> BackupFile:
        source = self.path_of(name)
        safety = self.create(admin, "auto")  # undo point before restoring
        try:
            self.database.restore_from(source)
        except ValueError as error:
            raise ValidationError(str(error)) from error
        return safety

    def restore_upload(self, admin: Administrator,
                       data: bytes) -> BackupFile:
        if not data:
            raise ValidationError("Choose a backup file to upload.")
        if len(data) > MAX_BACKUP_BYTES:
            raise ValidationError("The backup file is too large.")
        uploaded = self._new_path("upload")
        uploaded.write_bytes(data)
        if not is_sqlite_backup(uploaded):
            uploaded.unlink()
            raise ValidationError(
                "The file is not a library database backup.")
        return self.restore(admin, uploaded.name)

    def path_of(self, name: str) -> Path:
        if not NAME_PATTERN.match(name or ""):
            raise ValidationError("Backup not found.")
        path = self.backup_dir / name
        if not path.is_file():
            raise ValidationError("Backup not found.")
        return path

    def _new_path(self, label: str) -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = self.clock().strftime("%Y%m%d-%H%M%S")
        suffix = f"-{label}" if label else ""
        path = self.backup_dir / f"library-{stamp}{suffix}.db"
        number = 2
        while path.exists():
            path = self.backup_dir / f"library-{stamp}-{number}{suffix}.db"
            number += 1
        return path
