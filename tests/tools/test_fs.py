"""Filesystem tool tests (Phase 03).

Covers list_dir, read_file, write_file, edit_file — including ignore rules,
the secret denylist, binary refusal, size limits, and edit mismatch cases.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from wecoder.safety import DefaultPolicy
from wecoder.tools.base import ToolContext, ToolLimits
from wecoder.tools.fs import EditFile, ListDir, ReadFile, WriteFile
from wecoder.workspace.workspace import Workspace


def _ctx(ws: Workspace, **limits) -> ToolContext:
    return ToolContext(workspace=ws, policy=DefaultPolicy(), limits=ToolLimits(**limits))


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro) if False else asyncio.run(coro)


def _make_ws(tmp_path: Path) -> Workspace:
    (tmp_path / "project").mkdir()
    return Workspace.open(tmp_path / "project")


# --- list_dir ---------------------------------------------------------------


def test_list_dir_lists_files(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "a.py").write_text("x")
    (ws.root / "b.txt").write_text("y")
    (ws.root / "sub").mkdir()
    res = _run(ListDir().execute({}, _ctx(ws)))
    assert res.ok
    assert "a.py" in res.output
    assert "sub" in res.output
    assert res.data["entries"]


def test_list_dir_respects_ignore(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "real.py").write_text("x")
    (ws.root / "node_modules").mkdir()
    (ws.root / "node_modules" / "pkg").write_text("{}")
    res = _run(ListDir().execute({}, _ctx(ws)))
    assert res.ok
    assert "real.py" in res.output
    assert "node_modules" not in res.output
    assert res.data["ignored"] >= 1


def test_list_dir_caps_entries(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    for i in range(10):
        (ws.root / f"f{i}.py").write_text("x")
    res = _run(
        ListDir().execute({}, _ctx(ws, max_list_dir_entries=3))
    )
    assert res.ok
    assert len(res.data["entries"]) == 3
    assert res.data["truncated"] is True


# --- read_file --------------------------------------------------------------


def test_read_file_returns_text(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "main.py").write_text("print('hello')\n")
    res = _run(ReadFile().execute({"path": "main.py"}, _ctx(ws)))
    assert res.ok
    assert "print('hello')" in res.output


def test_read_file_refuses_secret(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / ".env").write_text("SECRET=1")
    res = _run(ReadFile().execute({"path": ".env"}, _ctx(ws)))
    assert not res.ok
    assert "secret" in res.output.lower() or "DeniedSecret" in (res.error_type or "")


def test_read_file_refuses_pem(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "cert.pem").write_text("-----BEGIN PRIVATE KEY-----\n")
    res = _run(ReadFile().execute({"path": "cert.pem"}, _ctx(ws)))
    assert not res.ok


def test_read_file_env_example_allowed(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / ".env.example").write_text("# docs only")
    res = _run(ReadFile().execute({"path": ".env.example"}, _ctx(ws)))
    assert res.ok
    assert "docs only" in res.output


def test_read_file_refuses_binary(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "blob.bin").write_bytes(b"\x00\x01\x02\x00\x04")
    res = _run(ReadFile().execute({"path": "blob.bin"}, _ctx(ws)))
    assert not res.ok
    assert res.data["binary"] is True


def test_read_file_enforces_size_limit(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "big.txt").write_text("a" * 500)
    res = _run(
        ReadFile().execute({"path": "big.txt"}, _ctx(ws, max_read_file_bytes=100))
    )
    assert not res.ok
    assert res.error_type == "FileTooLargeError"


def test_read_file_missing(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(ReadFile().execute({"path": "nope.py"}, _ctx(ws)))
    assert not res.ok


def test_read_file_rejects_escape(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(ReadFile().execute({"path": "../outside.txt"}, _ctx(ws)))
    assert not res.ok
    assert res.error_type == "PathEscapeError"


# --- write_file -------------------------------------------------------------


def test_write_file_creates_content(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(WriteFile().execute({"path": "new.py", "content": "x = 1\n"}, _ctx(ws)))
    assert res.ok
    assert (ws.root / "new.py").read_text() == "x = 1\n"


def test_write_file_creates_parents(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        WriteFile().execute(
            {"path": "src/pkg/mod.py", "content": "y = 2"}, _ctx(ws)
        )
    )
    assert res.ok
    assert (ws.root / "src" / "pkg" / "mod.py").read_text() == "y = 2"


def test_write_file_refuses_secret(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        WriteFile().execute({"path": "id_rsa", "content": "key"}, _ctx(ws))
    )
    assert not res.ok
    assert not (ws.root / "id_rsa").exists()


def test_write_file_enforces_size_limit(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        WriteFile().execute(
            {"path": "big.py", "content": "a" * 500}, _ctx(ws, max_write_file_bytes=100)
        )
    )
    assert not res.ok
    assert res.error_type == "FileTooLargeError"


def test_write_file_rejects_escape(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        WriteFile().execute({"path": "../x.py", "content": "x"}, _ctx(ws))
    )
    assert not res.ok
    assert res.error_type == "PathEscapeError"


# --- edit_file --------------------------------------------------------------


def test_edit_file_replaces_unique_match(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "m.py").write_text("foo\nbar\nfoo\n")
    res = _run(
        EditFile().execute(
            {"path": "m.py", "old_text": "bar", "new_text": "baz"}, _ctx(ws)
        )
    )
    assert res.ok
    assert (ws.root / "m.py").read_text() == "foo\nbaz\nfoo\n"


def test_edit_file_fails_on_zero_match(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "m.py").write_text("foo\nbar\n")
    res = _run(
        EditFile().execute(
            {"path": "m.py", "old_text": "zzz", "new_text": "x"}, _ctx(ws)
        )
    )
    assert not res.ok
    assert res.error_type == "EditMismatchError"


def test_edit_file_fails_on_multiple_match(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "m.py").write_text("foo\nfoo\n")
    res = _run(
        EditFile().execute(
            {"path": "m.py", "old_text": "foo", "new_text": "x"}, _ctx(ws)
        )
    )
    assert not res.ok
    assert res.error_type == "EditMismatchError"


def test_edit_file_replace_all(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "m.py").write_text("foo\nfoo\nfoo\n")
    res = _run(
        EditFile().execute(
            {
                "path": "m.py",
                "old_text": "foo",
                "new_text": "x",
                "replace_all": True,
            },
            _ctx(ws),
        )
    )
    assert res.ok
    assert (ws.root / "m.py").read_text() == "x\nx\nx\n"
    assert res.data["replacements"] == 3


def test_edit_file_refuses_secret(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / ".env").write_text("SECRET=1\nSECRET=1\n")
    res = _run(
        EditFile().execute(
            {"path": ".env", "old_text": "SECRET=1", "new_text": "x"}, _ctx(ws)
        )
    )
    assert not res.ok
