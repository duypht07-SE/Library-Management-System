"""HTTPS settings (NFR-SEC-02)."""
from pathlib import Path

import pytest

from app import LibraryApp
from config import Config
from config import TestConfig as AppTestConfig
from config import ssl_context


@pytest.fixture
def pem_files(tmp_path: Path) -> tuple[str, str]:
    cert = tmp_path / "cert.pem"
    key = tmp_path / "key.pem"
    cert.write_text("certificate", encoding="utf-8")
    key.write_text("private key", encoding="utf-8")
    return str(cert), str(key)


def test_no_certificate_means_plain_http():
    assert ssl_context("", "") is None
    assert ssl_context("  ", "  ") is None


def test_certificate_and_key_turn_on_https(pem_files):
    assert ssl_context(*pem_files) == pem_files


@pytest.mark.parametrize("which", ["cert only", "key only"])
def test_both_files_are_required(pem_files, which):
    cert, key = pem_files
    args = (cert, "") if which == "cert only" else ("", key)
    with pytest.raises(ValueError, match="Set both"):
        ssl_context(*args)


def test_missing_file_is_reported(pem_files, tmp_path):
    with pytest.raises(ValueError, match="LMS_SSL_KEY file was not found"):
        ssl_context(pem_files[0], str(tmp_path / "missing.pem"))


def test_config_reads_environment(monkeypatch, pem_files):
    monkeypatch.setenv("LMS_SSL_CERT", pem_files[0])
    monkeypatch.setenv("LMS_SSL_KEY", pem_files[1])
    monkeypatch.setenv("LMS_SESSION_COOKIE_SECURE", "0")
    config = Config()
    assert config.SSL_CONTEXT == pem_files
    assert config.SESSION_COOKIE_SECURE is True     # forced on with HTTPS
    assert config.PREFERRED_URL_SCHEME == "https"


def test_config_without_certificate(monkeypatch):
    monkeypatch.delenv("LMS_SSL_CERT", raising=False)
    monkeypatch.delenv("LMS_SSL_KEY", raising=False)
    assert Config().SSL_CONTEXT is None


def build(tmp_path: Path, https: tuple[str, str] | None) -> LibraryApp:
    config = AppTestConfig(tmp_path / "app.db")
    config.SSL_CONTEXT = https
    return LibraryApp(config)


def test_run_passes_certificate_to_the_server(tmp_path, pem_files):
    library = build(tmp_path, pem_files)
    calls = {}
    library.flask.run = lambda **kwargs: calls.update(kwargs)
    library.run()
    assert calls["ssl_context"] == pem_files


def test_hsts_header_only_with_https(tmp_path, pem_files):
    secure = build(tmp_path / "a", pem_files).flask.test_client()
    plain = build(tmp_path / "b", None).flask.test_client()
    assert "max-age" in secure.get("/").headers["Strict-Transport-Security"]
    assert "Strict-Transport-Security" not in plain.get("/").headers
