"""Search tool tests (Phase 03)."""

from __future__ import annotations

import asyncio
from pathlib import Path

from wecoder.safety import DefaultPolicy
from wecoder.tools.base import ToolContext, ToolLimits
from wecoder.tools.search import SearchText
from wecoder.workspace.workspace import Workspace


def _ctx(ws: Workspace, **limits) -> ToolContext:
    return ToolContext(workspace=ws, policy=DefaultPolicy(), limits=ToolLimits(**limits))


def _run(coro):
    return asyncio.run(coro)


def _make_ws(tmp_path: Path) -> Workspace:
    (tmp_path / "project").mkdir()
    return Workspace.open(tmp_path / "project")


def test_search_finds_match(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "a.py").write_text("def foo():\n    return 'TARGET'\n")
    (ws.root / "b.py").write_text("no match here\n")
    res = _run(SearchText().execute({"query": "TARGET"}, _ctx(ws)))
    assert res.ok
    assert res.data["matches"]
    assert res.data["matches"][0]["path"] == "a.py"
    assert res.data["matches"][0]["line"] == 2


def test_search_skips_ignored(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "node_modules").mkdir()
    (ws.root / "node_modules" / "pkg.js").write_text("TARGET\n")
    (ws.root / "main.py").write_text("TARGET\n")
    res = _run(SearchText().execute({"query": "TARGET"}, _ctx(ws)))
    assert res.ok
    paths = [m["path"] for m in res.data["matches"]]
    assert "main.py" in paths
    assert all("node_modules" not in p for p in paths)


def test_search_skips_secrets(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / ".env").write_text("SECRET_KEY=TARGET\n")
    (ws.root / "main.py").write_text("TARGET\n")
    res = _run(SearchText().execute({"query": "TARGET"}, _ctx(ws)))
    assert res.ok
    paths = [m["path"] for m in res.data["matches"]]
    assert ".env" not in paths
    assert "main.py" in paths


def test_search_skips_binary(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "blob.bin").write_bytes(b"TARGET\x00\x01")
    (ws.root / "main.py").write_text("TARGET\n")
    res = _run(SearchText().execute({"query": "TARGET"}, _ctx(ws)))
    assert res.ok
    paths = [m["path"] for m in res.data["matches"]]
    assert "blob.bin" not in paths
    assert "main.py" in paths


def test_search_caps_matches(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    for i in range(10):
        (ws.root / f"f{i}.py").write_text("NEEDLE\n")
    res = _run(
        SearchText().execute({"query": "NEEDLE"}, _ctx(ws, max_search_matches=3))
    )
    assert res.ok
    assert len(res.data["matches"]) == 3
    assert res.data["capped"] is True


def test_search_empty_query_fails(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(SearchText().execute({"query": ""}, _ctx(ws)))
    assert not res.ok


def test_search_scoped_to_subdir(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "sub").mkdir()
    (ws.root / "sub" / "a.py").write_text("NEEDLE\n")
    (ws.root / "b.py").write_text("NEEDLE\n")
    res = _run(SearchText().execute({"query": "NEEDLE", "path": "sub"}, _ctx(ws)))
    assert res.ok
    paths = [m["path"] for m in res.data["matches"]]
    assert "sub/a.py" in paths
    assert "b.py" not in paths
