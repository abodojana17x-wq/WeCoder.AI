"""Ignore-matcher tests (Phase 03).

Verifies built-in defaults (.git, node_modules, __pycache__) and the
workspace's own .gitignore are honoured.
"""

from __future__ import annotations

from pathlib import Path

from wecoder.workspace.ignore import BUILTIN_IGNORES
from wecoder.workspace.workspace import Workspace


def _ws(tmp_path: Path) -> Workspace:
    (tmp_path / "project").mkdir()
    return Workspace.open(tmp_path / "project")


def test_builtin_ignore_list_contains_required_dirs() -> None:
    text = "\n".join(BUILTIN_IGNORES)
    assert ".git/" in text
    assert "node_modules/" in text
    assert "__pycache__/" in text
    assert "*.pyc" in text


def test_git_dir_is_ignored(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws.root / ".git").mkdir()
    (ws.root / ".git" / "config").write_text("x")
    assert ws.ignore.is_ignored(ws.root / ".git" / "config")


def test_node_modules_is_ignored(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws.root / "node_modules").mkdir()
    (ws.root / "node_modules" / "pkg").write_text("{}")
    assert ws.ignore.is_ignored(ws.root / "node_modules" / "pkg")


def test_pycache_is_ignored(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws.root / "__pycache__").mkdir()
    assert ws.ignore.is_ignored(ws.root / "__pycache__" / "mod.cpython-311.pyc")


def test_real_source_is_not_ignored(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws.root / "main.py").write_text("print('hi')")
    assert not ws.ignore.is_ignored(ws.root / "main.py")


def test_gitignore_is_honoured(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws.root / ".gitignore").write_text("secrets/\n*.log\n")
    (ws.root / "secrets").mkdir()
    (ws.root / "secrets" / "db.txt").write_text("x")
    (ws.root / "app.log").write_text("log")
    assert ws.ignore.is_ignored(ws.root / "secrets" / "db.txt")
    assert ws.ignore.is_ignored(ws.root / "app.log")


def test_path_outside_workspace_is_not_ignored(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("x")
    # Outside the workspace entirely; the matcher returns False (not its job).
    assert not ws.ignore.is_ignored(outside)
