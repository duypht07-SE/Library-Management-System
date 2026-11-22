from datetime import datetime, timedelta
from pathlib import Path

from app import LibraryApp
from config import Config
from config import TestConfig as AppTestConfig


def _build_app(tmp_path: Path) -> LibraryApp:
    config = AppTestConfig(tmp_path / "library.db")
    return LibraryApp(config)


def test_daily_job_creates_backup_in_two_folders(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    result = app.daily_job_service.run(at=datetime(2026, 11, 22, 0, 0, 0))

    assert result["backups_created"] == 1
    assert result["backups_copied"] == 1
    primary = list(app.config.BACKUP_DIR.glob("*-daily.db"))
    secondary = list(app.config.BACKUP_COPY_DIR.glob("*-daily.db"))
    assert len(primary) == 1
    assert len(secondary) == 1
    assert primary[0].name == secondary[0].name
    assert primary[0].read_bytes() == secondary[0].read_bytes()


def test_daily_job_keeps_30_daily_and_preserves_manual_and_auto(
        tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    manual = app.backup_service.create()
    auto = app.backup_service.create(label="auto")
    app.backup_service.copy_backup(manual.name)
    app.backup_service.copy_backup(auto.name)

    start = datetime(2026, 10, 1, 0, 0, 0)
    for day in range(31):
        current = start + timedelta(days=day)
        app.backup_service.clock = lambda c=current: c
        app.daily_job_service.run(at=current)

    primary_daily = sorted(
        p.name for p in app.config.BACKUP_DIR.glob("*-daily.db"))
    copy_daily = sorted(
        p.name for p in app.config.BACKUP_COPY_DIR.glob("*-daily.db"))
    assert len(primary_daily) == 30
    assert len(copy_daily) == 30
    assert primary_daily == copy_daily
    assert "library-20261001-000000-daily.db" not in primary_daily
    assert "library-20261031-000000-daily.db" in primary_daily

    assert (app.config.BACKUP_DIR / manual.name).is_file()
    assert (app.config.BACKUP_DIR / auto.name).is_file()
    assert (app.config.BACKUP_COPY_DIR / manual.name).is_file()
    assert (app.config.BACKUP_COPY_DIR / auto.name).is_file()


def test_failed_copy_logs_audit_and_keeps_daily_tasks_running(
        tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    blocked = tmp_path / "blocked_path"
    blocked.write_text("not a directory", encoding="utf-8")
    app.backup_service.copy_dir = blocked

    result = app.daily_job_service.run(at=datetime(2026, 11, 22, 0, 0, 0))

    assert result["backups_created"] == 1
    assert result["backups_copied"] == 0
    assert "marked_overdue" in result
    logs = app.audit_service.recent(action="DAILY_BACKUP_COPY_FAILED")
    assert len(logs) == 1
    assert "Daily backup copy failed" in logs[0].details


def test_config_reads_backup_copy_dir_env(monkeypatch, tmp_path: Path) -> None:
    target = tmp_path / "custom_copy"
    monkeypatch.setenv("LMS_BACKUP_COPY_DIR", str(target))
    cfg = Config()
    assert cfg.BACKUP_COPY_DIR == target

def test_sqlite_error_in_backup_does_not_stop_daily_job(
        tmp_path: Path) -> None:
    """Defect T1: a locked database used to crash the whole daily job."""
    import sqlite3

    app = _build_app(tmp_path)

    def locked(target):
        raise sqlite3.OperationalError("database is locked")

    app.database.backup_to = locked
    result = app.daily_job_service.run(at=datetime(2026, 11, 22, 0, 0, 0))

    assert result["backups_created"] == 0
    assert "marked_overdue" in result
    logs = app.audit_service.recent(action="DAILY_BACKUP_FAILED")
    assert "database is locked" in logs[0].details


def test_run_safely_keeps_scheduler_alive(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    def broken(at=None):
        raise RuntimeError("unexpected")

    app.daily_job_service.run = broken
    assert app.daily_job_service.run_safely() is None
    logs = app.audit_service.recent(action="DAILY_JOB_FAILED")
    assert "unexpected" in logs[0].details


def test_restart_on_same_day_adds_no_daily_backup(tmp_path: Path) -> None:
    """Defect T2: every start-up used to add one more daily backup."""
    app = _build_app(tmp_path)
    day = datetime(2026, 11, 22, 0, 0, 0)
    app.backup_service.clock = lambda: day
    results = [app.daily_job_service.run(at=day) for _ in range(3)]

    assert [r["backups_created"] for r in results] == [1, 0, 0]
    assert len(list(app.config.BACKUP_DIR.glob("*-daily.db"))) == 1
    assert len(list(app.config.BACKUP_COPY_DIR.glob("*-daily.db"))) == 1


def test_missing_copy_is_made_on_the_next_run(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    day = datetime(2026, 11, 22, 0, 0, 0)
    app.backup_service.clock = lambda: day
    good_copy_dir = app.backup_service.copy_dir
    blocked = tmp_path / "blocked_path"
    blocked.write_text("not a directory", encoding="utf-8")
    app.backup_service.copy_dir = blocked
    first = app.daily_job_service.run(at=day)
    app.backup_service.copy_dir = good_copy_dir
    second = app.daily_job_service.run(at=day)

    assert (first["backups_created"], first["backups_copied"]) == (1, 0)
    assert (second["backups_created"], second["backups_copied"]) == (0, 1)
    assert len(list(good_copy_dir.glob("*-daily.db"))) == 1
