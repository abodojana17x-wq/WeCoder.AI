"""Agent loop integration tests (Phase 04 MVP).

All tests are offline, using :class:`ToolFakeModel`.  They verify the
scripted tool-calling scenario, budget enforcement, secret denial, and
accurate changed-file / command tracking from actual tool results.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest
from tests.agent.fakes import ToolFakeModel, response
from wecoder.agent.loop import DeveloperAgent
from wecoder.agent.session import Session
from wecoder.workspace.workspace import Workspace


def _run(coro):
    return asyncio.run(coro)


def _ws(tmp_path: Path) -> Workspace:
    (tmp_path / "project").mkdir()
    return Workspace.open(tmp_path / "project")


def _write_call(path: str, content: str) -> dict:
    return {
        "name": "write_file",
        "arguments": json.dumps({"path": path, "content": content}),
    }


def _edit_call(path: str, old: str, new: str) -> dict:
    return {
        "name": "edit_file",
        "arguments": json.dumps({"path": path, "old_text": old, "new_text": new}),
    }


def _read_call(path: str) -> dict:
    return {"name": "read_file", "arguments": json.dumps({"path": path})}


def _cmd_call(argv: list[str]) -> dict:
    return {"name": "run_command", "arguments": json.dumps({"argv": argv})}


def test_scripted_write_edit_then_finish(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    model = ToolFakeModel(
        [
            # Turn 1: a short plan, no tools.
            response("PLAN:\nCreate greet() in app/hello.py and add a test."),
            # Turn 2: create the file.
            response(
                "Creating the file.",
                tool_calls=[
                    _write_call(
                        "app/hello.py",
                        "def greet(name):\n    return f'hello {name}'\n",
                    )
                ],
            ),
            # Turn 3: add a test file.
            response(
                "Adding a test.",
                tool_calls=[
                    _write_call(
                        "app/test_hello.py",
                        "from app.hello import greet\n\n"
                        "def test_greet():\n    assert greet('x') == 'hello x'\n",
                    )
                ],
            ),
            # Turn 4: final summary.
            response("Done. Added greet() and a passing test."),
        ]
    )
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("Add greet(name)", session, max_turns=10))

    assert result.status == "succeeded"
    assert result.stop_reason == "final_message"
    # File exists on disk with the right content.
    hello = (ws.root / "app" / "hello.py").read_text()
    assert "def greet(name)" in hello
    # changed_files derived from actual write_file calls, not prose.
    assert "app/hello.py" in result.changed_files
    assert "app/test_hello.py" in result.changed_files
    # Usage accumulated across the 4 model turns.
    assert result.usage.input_tokens == 4
    assert result.usage.output_tokens == 4
    # Plan was extracted from the first assistant message.
    assert result.plan is not None
    assert "greet" in result.plan.lower()


def test_changed_files_from_edit_file(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws.root / "mod.py").write_text("old = 1\n")
    model = ToolFakeModel(
        [
            response("PLAN: edit mod.py"),
            response(
                "editing",
                tool_calls=[_edit_call("mod.py", "old = 1", "new = 2")],
            ),
            response("Done."),
        ]
    )
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("update mod.py", session, max_turns=10))

    assert result.status == "succeeded"
    assert "mod.py" in result.changed_files
    assert (ws.root / "mod.py").read_text() == "new = 2\n"


def test_command_tracking(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    model = ToolFakeModel(
        [
            response("PLAN: run echo"),
            response(
                "running",
                tool_calls=[_cmd_call(["echo", "hello"])],
            ),
            response("Done."),
        ]
    )
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("run echo", session, max_turns=10))

    assert result.status == "succeeded"
    assert len(result.commands) == 1
    assert result.commands[0].argv == ["echo", "hello"]
    assert result.commands[0].exit_code == 0


def test_budget_exceeded_on_max_turns(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    # A model that ALWAYS requests a tool, never finishing.
    model = ToolFakeModel(
        [
            response("PLAN: keep working"),
            response("working", tool_calls=[_write_call("a.txt", "x")]),
            response("working", tool_calls=[_write_call("b.txt", "x")]),
            response("working", tool_calls=[_write_call("c.txt", "x")]),
        ]
    )
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("never-ending task", session, max_turns=1))

    assert result.status == "budget_exceeded"
    assert result.stop_reason == "max_turns"
    # The loop terminated — no infinite loop.


def test_budget_exceeded_no_infinite_loop_with_one_turn(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    model = ToolFakeModel(
        [response("PLAN: x", tool_calls=[_write_call("a.txt", "x")])]
    )
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("task", session, max_turns=1))

    # max_turns=1 means one model call; if it requests a tool, budget is hit.
    assert result.status == "budget_exceeded"


def test_secret_denial_never_exposes_contents(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    secret = "SUPER_SECRET_VALUE_12345"
    (ws.root / ".env").write_text(f"KEY={secret}")

    model = ToolFakeModel(
        [
            response("PLAN: read .env"),
            # The model tries to read the secret file.
            response("reading env", tool_calls=[_read_call(".env")]),
            # After the denial, the model gives a final answer.
            response("Could not read .env; finishing without it."),
        ]
    )
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("read env config", session, max_turns=10))

    # The secret contents must never appear anywhere in the result or messages.
    assert secret not in result.summary
    assert secret not in (result.plan or "")
    for msg in session.messages:
        assert secret not in msg.content
    # The tool result message should be a denial, not the file contents.
    tool_msgs = [m for m in session.messages if m.role == "tool"]
    assert tool_msgs
    assert "secret" in tool_msgs[0].content.lower() or "denied" in tool_msgs[0].content.lower()
    # .env must not appear in changed_files.
    assert ".env" not in result.changed_files


def test_secret_denial_no_blind_retry(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    (ws.root / ".env").write_text("SECRET=1")
    # Model tries .env, then tries .env again — agent must not loop forever.
    model = ToolFakeModel(
        [
            response("PLAN: read env", tool_calls=[_read_call(".env")]),
            response("retry", tool_calls=[_read_call(".env")]),
            response("giving up"),
        ]
    )
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("read env", session, max_turns=10))

    # Terminates (no infinite loop). Both .env reads were denied.
    assert result.status in ("succeeded", "budget_exceeded")
    assert ".env" not in result.changed_files


def test_empty_task_returns_failure_no_model_call(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    model = ToolFakeModel([])
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    result = _run(agent.run("   ", session, max_turns=5))

    assert result.status == "failed"
    assert result.stop_reason == "empty_task"
    # No model call was made.
    assert model.requests == []


def test_provider_without_tool_calling_fails_fast(tmp_path: Path) -> None:
    from tests.models.fakes import FakeModel
    from wecoder.models.types import CompletionResponse, Message, Usage

    ws = _ws(tmp_path)
    # FakeModel advertises tool_calling=False.
    fake = FakeModel(
        [CompletionResponse(Message("assistant", "x"), Usage(), "stop", "fake", "fake")]
    )
    agent = DeveloperAgent(model=fake)  # type: ignore[arg-type]
    session = Session(workspace=ws)
    with pytest.raises(Exception) as excinfo:
        _run(agent.run("task", session, max_turns=5))
    assert "tool calling" in str(excinfo.value).lower()


def test_tool_schemas_passed_to_model(tmp_path: Path) -> None:
    ws = _ws(tmp_path)
    model = ToolFakeModel([response("PLAN: done"), response("Done.")])
    agent = DeveloperAgent(model=model)
    session = Session(workspace=ws)
    _run(agent.run("task", session, max_turns=5))

    # The model received tool specs in the request.
    assert model.requests
    first = model.requests[0]
    assert first.tools is not None
    names = {t.name for t in first.tools}
    assert {"write_file", "edit_file", "read_file", "run_command"} <= names
