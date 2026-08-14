"""Shell tool tests (Phase 03).

Covers command execution, stdout/stderr capture, non-zero exits, timeouts,
jailed cwd, and external-cwd rejection.  No shell=True is ever used.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from wecoder.safety import DefaultPolicy
from wecoder.tools.base import ToolContext, ToolLimits
from wecoder.tools.shell import RunCommand
from wecoder.workspace.workspace import Workspace


def _ctx(ws: Workspace, **limits) -> ToolContext:
    return ToolContext(workspace=ws, policy=DefaultPolicy(), limits=ToolLimits(**limits))


def _run(coro):
    return asyncio.run(coro)


def _make_ws(tmp_path: Path) -> Workspace:
    (tmp_path / "project").mkdir()
    return Workspace.open(tmp_path / "project")


def test_run_command_captures_stdout(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        RunCommand().execute(
            {"argv": [sys.executable, "-c", "print('hello-out')"]}, _ctx(ws)
        )
    )
    assert res.ok
    assert res.data["exit_code"] == 0
    assert "hello-out" in res.data["stdout"]


def test_run_command_captures_stderr(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        RunCommand().execute(
            {
                "argv": [sys.executable, "-c", "import sys; sys.stderr.write('err-msg')"],
            },
            _ctx(ws),
        )
    )
    assert res.ok
    assert "err-msg" in res.data["stderr"]


def test_run_command_nonzero_exit_is_result_not_exception(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        RunCommand().execute(
            {"argv": [sys.executable, "-c", "import sys; sys.exit(3)"]},
            _ctx(ws),
        )
    )
    assert not res.ok
    assert res.data["exit_code"] == 3
    assert res.error_type == "CommandFailedError"


def test_run_command_timeout(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        RunCommand().execute(
            {
                "argv": [sys.executable, "-c", "import time; time.sleep(60)"],
                "timeout": 1,
            },
            _ctx(ws),
        )
    )
    assert not res.ok
    assert res.error_type == "CommandTimeoutError"
    assert res.data["timeout"] == 1


def test_run_command_jailed_relative_cwd(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    (ws.root / "sub").mkdir()
    res = _run(
        RunCommand().execute(
            {"argv": [sys.executable, "-c", "import os; print(os.getcwd())"], "cwd": "sub"},
            _ctx(ws),
        )
    )
    assert res.ok
    assert "sub" in res.data["stdout"]


def test_run_command_rejects_external_cwd(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    # An absolute external path is rejected by the jail.
    res = _run(
        RunCommand().execute(
            {
                "argv": [sys.executable, "-c", "print('x')"],
                "cwd": str(tmp_path),
            },
            _ctx(ws),
        )
    )
    assert not res.ok
    assert res.error_type == "PathEscapeError"


def test_run_command_rejects_root_cwd(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        RunCommand().execute(
            {"argv": [sys.executable, "-c", "print('x')"], "cwd": "/"},
            _ctx(ws),
        )
    )
    assert not res.ok
    assert res.error_type == "PathEscapeError"


def test_run_command_rejects_empty_argv(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(RunCommand().execute({"argv": []}, _ctx(ws)))
    assert not res.ok


def test_run_command_redacts_aws_key_in_output(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        RunCommand().execute(
            {
                "argv": [
                    sys.executable,
                    "-c",
                    "print('AKIAIOSFODNN7EXAMPLE leaked')",
                ],
            },
            _ctx(ws),
        )
    )
    assert res.ok
    assert "AKIAIOSFODNN7EXAMPLE" not in res.data["stdout"]
    assert "REDACTED" in res.data["stdout"]


def test_run_command_env_does_not_inherit_arbitrary_vars(tmp_path: Path, monkeypatch) -> None:
    ws = _make_ws(tmp_path)
    monkeypatch.setenv("WECODER_LEAK_TEST", "super-secret-value")
    res = _run(
        RunCommand().execute(
            {
                "argv": [
                    sys.executable,
                    "-c",
                    "import os; print(os.environ.get('WECODER_LEAK_TEST','none'))",
                ],
            },
            _ctx(ws),
        )
    )
    assert res.ok
    assert "super-secret-value" not in res.data["stdout"]
    assert "none" in res.data["stdout"]


def test_run_command_command_not_found(tmp_path: Path) -> None:
    ws = _make_ws(tmp_path)
    res = _run(
        RunCommand().execute(
            {"argv": ["this-command-does-not-exist-xyz"]}, _ctx(ws)
        )
    )
    assert not res.ok
    assert res.error_type == "CommandFailedError"
