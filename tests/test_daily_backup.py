from datetime import datetime, timedelta
from pathlib import Path

from app import LibraryApp
from config import Config, TestConfig


def _build_app(tmp_path: Path) -> LibraryApp:
    config = TestConfig(tmp_path / "library.db")
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