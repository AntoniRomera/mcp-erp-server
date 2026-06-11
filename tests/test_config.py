"""Tests for settings loading and CLI override precedence."""

from __future__ import annotations

import pytest

from mcp_server.config import Settings, build_settings


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch, tmp_path):
    """Isolate from a developer .env file and stray BACKEND_* env vars."""
    for var in (
        "BACKEND_URL",
        "READONLY",
        "DEMO",
        "BACKEND_API_KEY",
        "BACKEND_USERNAME",
        "BACKEND_PASSWORD",
        "BACKEND_DATABASE",
        "REQUEST_TIMEOUT",
    ):
        monkeypatch.delenv(var, raising=False)
    # Run from a directory with no .env so defaults are deterministic.
    monkeypatch.chdir(tmp_path)


def test_defaults():
    s = Settings()
    assert s.backend_url == "http://localhost:8069"
    assert s.readonly is True
    assert s.demo is False
    assert s.backend_api_key is None
    assert s.request_timeout == 30.0


def test_env_vars_override_defaults(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "https://erp.example/jsonrpc")
    monkeypatch.setenv("READONLY", "false")
    monkeypatch.setenv("DEMO", "true")
    s = Settings()
    assert s.backend_url == "https://erp.example/jsonrpc"
    assert s.readonly is False
    assert s.demo is True


def test_cli_overrides_take_precedence_over_env(monkeypatch):
    monkeypatch.setenv("DEMO", "false")
    monkeypatch.setenv("BACKEND_URL", "https://from-env.example")
    s = build_settings({"demo": True, "backend_url": "https://from-cli.example"})
    assert s.demo is True
    assert s.backend_url == "https://from-cli.example"


def test_cli_none_values_fall_through_to_env(monkeypatch):
    monkeypatch.setenv("BACKEND_URL", "https://from-env.example")
    # Unset CLI flags arrive as None and must not clobber env values.
    s = build_settings({"demo": None, "backend_url": None, "readonly": None})
    assert s.backend_url == "https://from-env.example"


def test_build_settings_without_overrides_returns_defaults():
    s = build_settings(None)
    assert s.backend_url == "http://localhost:8069"
    assert s.readonly is True
