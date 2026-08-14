"""Existing tests for the mini-app fixture."""

from app import app


def test_app_default() -> None:
    assert app() == "mini-app"
