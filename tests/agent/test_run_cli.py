"""CLI tests for ``wecoder run`` (Phase 04).

All offline, using the ``WECODER_FAKE_MODEL`` test hook with a scripted JSON
response file.  No network, no Ollama, no credentials required.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from wecoder.cli.app import main


def _write_script(path: Path, entries: list[dict]) -> Path:
    path.write_text(json.dumps(entries), encoding="utf-8")
    return path


def _write_call(path: str, content: str) -> dict:
    return {
        "name": "write_file",
        "arguments": json.dumps({"path": path, "content": content}),
    }


def test_run_help_exits_zero(capsys) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["run", "--help"])
    assert excinfo.value.code == 0
    out = capsys.readouterr().out
    assert "task" in out.lower()
    assert "--workspace" in out
    assert "--provider" in out
    assert "--max-turns" in out
    assert "--json" in out


def test_run_with_fake_model_writes_file(
    project_dir: Path, home_dir: Path, tmp_path: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    script = _write_script(
        tmp_path / "script.json",
        [
            {"content": "PLAN: create greet in app/hello.py"},
            {
                "content": "creating",
                "tool_calls": [
                    _write_call(
                        "app/hello.py",
                        "def greet(name):\n    return f'hello {name}'\n",
                    )
                ],
            },
            {"content": "Done."},
        ],
    )

    code = main(
        ["run", "add greet function"],
        cwd=str(project_dir),
        home=str(home_dir),
        env={
            "WECODER_FAKE_MODEL": "1",
            "WECODER_FAKE_MODEL_SCRIPT": str(script),
        },
    )
    assert code == 0
    out = capsys.readouterr().out
    assert "workspace:" in out
    assert "status: succeeded" in out
    assert "app/hello.py" in out
    # The file actually exists on disk.
    assert (project_dir / "app" / "hello.py").read_text().startswith("def greet")


def test_run_workspace_root_printed_before_model_call(
    project_dir: Path, home_dir: Path, tmp_path: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    script = _write_script(
        tmp_path / "script.json",
        [{"content": "PLAN: done"}, {"content": "Done."}],
    )
    code = main(
        ["run", "task"],
        cwd=str(project_dir),
        home=str(home_dir),
        env={
            "WECODER_FAKE_MODEL": "1",
            "WECODER_FAKE_MODEL_SCRIPT": str(script),
        },
    )
    assert code == 0
    out = capsys.readouterr().out
    # The workspace line appears before any model activity.
    assert out.index("workspace:") < out.index("status:")


def test_run_empty_task_fails_without_model_call(
    project_dir: Path, home_dir: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    code = main(
        ["run", "   "],
        cwd=str(project_dir),
        home=str(home_dir),
        env={"WECODER_FAKE_MODEL": "1"},
    )
    assert code == 1
    out = capsys.readouterr().out
    assert "empty task" in out.lower()
    # No workspace/model output beyond the error.
    assert "status:" not in out


def test_run_json_output(
    project_dir: Path, home_dir: Path, tmp_path: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    script = _write_script(
        tmp_path / "script.json",
        [
            {"content": "PLAN: x"},
            {
                "content": "writing",
                "tool_calls": [_write_call("out.txt", "hello")],
            },
            {"content": "Done."},
        ],
    )
    code = main(
        ["run", "task", "--json"],
        cwd=str(project_dir),
        home=str(home_dir),
        env={
            "WECODER_FAKE_MODEL": "1",
            "WECODER_FAKE_MODEL_SCRIPT": str(script),
        },
    )
    assert code == 0
    out = capsys.readouterr().out
    # JSON output is the last block; find the JSON object.
    json_start = out.index("{")
    payload = json.loads(out[json_start:])
    assert payload["status"] == "succeeded"
    assert "out.txt" in payload["changed_files"]
    assert payload["stop_reason"] == "final_message"


def test_run_max_turns_flag(
    project_dir: Path, home_dir: Path, tmp_path: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    # Script always requests a tool; with --max-turns 1 it must budget-exhaust.
    script = _write_script(
        tmp_path / "script.json",
        [
            {"content": "PLAN: x"},
            {
                "content": "writing",
                "tool_calls": [_write_call("a.txt", "x")],
            },
        ],
    )
    code = main(
        ["run", "task", "--max-turns", "1"],
        cwd=str(project_dir),
        home=str(home_dir),
        env={
            "WECODER_FAKE_MODEL": "1",
            "WECODER_FAKE_MODEL_SCRIPT": str(script),
        },
    )
    assert code == 1
    out = capsys.readouterr().out
    assert "budget_exceeded" in out


def test_run_nonexistent_workspace_fails(
    project_dir: Path, home_dir: Path, capsys
) -> None:
    project_dir.mkdir(exist_ok=True)
    code = main(
        ["run", "task", "--workspace", str(project_dir / "nope")],
        cwd=str(project_dir),
        home=str(home_dir),
        env={"WECODER_FAKE_MODEL": "1"},
    )
    assert code == 1
    err = capsys.readouterr().out
    assert "error" in err.lower()
