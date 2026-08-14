"""Workspace path-jail tests (Phase 03).

Covers every escape vector mandated by the Phase 03 contract:
``../``, ``../../``, absolute external paths, symlink escape, and valid
nested relative paths.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from wecoder.errors import DeniedSecretError, PathEscapeError
from wecoder.workspace.workspace import Workspace


def test_root_is_absolute_and_resolved(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    ws = Workspace.open(tmp_path / "project")
    assert ws.root == (tmp_path / "project").resolve()
    assert ws.root.is_absolute()


def test_default_root_is_cwd(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "project").mkdir()
    monkeypatch.chdir(tmp_path / "project")
    ws = Workspace.open()
    assert ws.root == (tmp_path / "project").resolve()


def test_resolve_normal_relative_path(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / "main.py").write_text("print('hi')\n")
    ws = Workspace.open(tmp_path / "project")
    resolved = ws.resolve("main.py")
    assert resolved == (tmp_path / "project" / "main.py").resolve()


def test_resolve_nested_relative_path(tmp_path: Path) -> None:
    (tmp_path / "project" / "src" / "pkg").mkdir(parents=True)
    ws = Workspace.open(tmp_path / "project")
    resolved = ws.resolve("src/pkg/mod.py")
    assert resolved == (tmp_path / "project" / "src" / "pkg" / "mod.py").resolve()


def test_resolve_rejects_parent_traversal(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "outside.txt").write_text("nope")
    ws = Workspace.open(tmp_path / "project")
    with pytest.raises(PathEscapeError):
        ws.resolve("../outside.txt")


def test_resolve_rejects_deep_parent_traversal(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "outside.txt").write_text("nope")
    ws = Workspace.open(tmp_path / "project")
    with pytest.raises(PathEscapeError):
        ws.resolve("../../outside.txt")


def test_resolve_rejects_absolute_external_path(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "outside.txt").write_text("nope")
    ws = Workspace.open(tmp_path / "project")
    with pytest.raises(PathEscapeError):
        ws.resolve(str(tmp_path / "outside.txt"))


@pytest.mark.skipif(
    sys.platform == "win32", reason="symlink semantics differ on Windows"
)
def test_resolve_rejects_symlink_escape(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "outside.txt").write_text("secret")
    link = tmp_path / "project" / "escape"
    os.symlink(tmp_path / "outside.txt", link)
    ws = Workspace.open(tmp_path / "project")
    with pytest.raises(PathEscapeError):
        ws.resolve("escape")


@pytest.mark.skipif(
    sys.platform == "win32", reason="symlink semantics differ on Windows"
)
def test_resolve_allows_symlink_inside_workspace(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    target = tmp_path / "project" / "real.txt"
    target.write_text("ok")
    link = tmp_path / "project" / "link.txt"
    os.symlink(target, link)
    ws = Workspace.open(tmp_path / "project")
    resolved = ws.resolve("link.txt")
    assert resolved == target.resolve()


def test_resolve_for_read_enforces_secret_denylist(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / ".env").write_text("SECRET=1")
    ws = Workspace.open(tmp_path / "project")
    with pytest.raises(DeniedSecretError):
        ws.resolve_for_read(".env")


def test_resolve_for_write_enforces_secret_denylist(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    ws = Workspace.open(tmp_path / "project")
    with pytest.raises(DeniedSecretError):
        ws.resolve_for_write("id_rsa")


def test_env_example_is_not_denied(tmp_path: Path) -> None:
    (tmp_path / "project").mkdir()
    (tmp_path / "project" / ".env.example").write_text("# docs")
    ws = Workspace.open(tmp_path / "project")
    # Should not raise.
    resolved = ws.resolve_for_read(".env.example")
    assert resolved.exists()


def test_open_rejects_nonexistent_root(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        Workspace.open(tmp_path / "does-not-exist")


def test_open_rejects_file_as_root(tmp_path: Path) -> None:
    f = tmp_path / "file"
    f.write_text("x")
    with pytest.raises(NotADirectoryError):
        Workspace.open(f)
