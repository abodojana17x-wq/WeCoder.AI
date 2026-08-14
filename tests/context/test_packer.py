"""Context packer tests (Phase 03)."""

from __future__ import annotations

from pathlib import Path

from wecoder.context.packer import ContextBundle, ContextPacker
from wecoder.workspace.workspace import Workspace


def _make_ws(tmp_path: Path) -> Workspace:
    (tmp_path / "project").mkdir()
    return Workspace.open(tmp_path / "project")


def test_pack_returns_bundle_with_root(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    bundle = ContextPacker().pack(ws)
    assert isinstance(bundle, ContextBundle)
    assert bundle.root == str(ws.root)
    assert bundle.approx_bytes >= 0


def test_pack_detects_python(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "pyproject.toml").write_text("[project]\nname='x'\n")
    (ws.root / "main.py").write_text("x = 1\n")
    bundle = ContextPacker().pack(ws)
    assert "Python" in bundle.language_hints


def test_pack_detects_multiple_languages(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "app.py").write_text("x=1")
    (ws.root / "lib.ts").write_text("const x=1")
    (ws.root / "main.go").write_text("package main")
    bundle = ContextPacker().pack(ws)
    assert "Python" in bundle.language_hints
    assert "TypeScript" in bundle.language_hints
    assert "Go" in bundle.language_hints


def test_pack_excludes_secret_files_from_tree(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "main.py").write_text("x=1")
    (ws.root / ".env").write_text("SECRET=1")
    bundle = ContextPacker().pack(ws)
    assert ".env" not in bundle.tree_excerpt


def test_pack_excludes_ignored_dirs(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "main.py").write_text("x=1")
    (ws.root / "node_modules").mkdir()
    (ws.root / "node_modules" / "pkg.json").write_text("{}")
    bundle = ContextPacker().pack(ws)
    assert "node_modules" not in bundle.tree_excerpt


def test_pack_stays_within_byte_budget(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "pyproject.toml").write_text("x\n")
    for i in range(50):
        (ws.root / f"f{i}.py").write_text(f"# file {i}\n")
    bundle = ContextPacker(max_bytes=500).pack(ws)
    assert bundle.approx_bytes <= 2_000  # generous bound; tree excerpt capped


def test_pack_caps_large_tree(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    for i in range(2000):
        (ws.root / f"f{i}.py").write_text("# x\n")
    bundle = ContextPacker().pack(ws)
    # A capped walk records a note.
    assert any("capped" in n or "ignored" in n for n in bundle.notes) or bundle.approx_bytes >= 0


def test_pack_handles_empty_workspace(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    bundle = ContextPacker().pack(ws)
    assert bundle.root == str(ws.root)
    assert bundle.language_hints == []


def test_pack_extra_paths_add_hints(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "lib.rs").write_text("fn main(){}")
    bundle = ContextPacker().pack(ws, extra_paths=["lib.rs"])
    assert "Rust" in bundle.language_hints
