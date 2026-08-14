"""``wecoder run`` command (Phase 04 MVP).

Runs the single Developer agent against a natural-language task.  Prints the
resolved workspace root **before** any model call so the user can Ctrl-C.

Exit codes:
    0  succeeded
    1  failed / blocked / budget_exceeded / config errors
    2  unexpected internal errors
"""

from __future__ import annotations

import asyncio
import json as _json
import logging
from collections.abc import Mapping
from pathlib import Path

from wecoder.agent.loop import DeveloperAgent
from wecoder.agent.session import Session
from wecoder.config.settings import Settings
from wecoder.errors import WecoderError
from wecoder.models.registry import default_registry

_LOGGER = logging.getLogger("wecoder.cli.run")

# A documented test hook: when this env var is set, ``run`` builds a FakeModel
# from a scripted JSON file path in ``WECODER_FAKE_MODEL_SCRIPT`` instead of a
# real provider.  This keeps CLI tests offline and credential-free.
_FAKE_ENV = "WECODER_FAKE_MODEL"
_FAKE_SCRIPT_ENV = "WECODER_FAKE_MODEL_SCRIPT"


def run(
    settings: Settings,
    task: str,
    *,
    workspace: str | Path | None = None,
    provider: str | None = None,
    model: str | None = None,
    max_turns: int | None = None,
    json_output: bool = False,
    cwd: str | Path | None = None,
    env: Mapping[str, str] | None = None,
) -> int:
    """Execute ``wecoder run`` and return an exit code.

    ``cwd``/``env`` support isolated test runs.
    """
    if not task or not task.strip():
        print("wecoder: error: empty task", flush=True)
        return 1

    # Resolve workspace root from flag, then settings, then cwd.
    ws_path = workspace or settings.project.workspace or "."
    base = Path(cwd) if cwd is not None else Path.cwd()
    wp = Path(ws_path)
    resolved_ws = wp if wp.is_absolute() else (base / wp)

    try:
        from wecoder.workspace.workspace import Workspace

        workspace_obj = Workspace.open(resolved_ws)
    except (FileNotFoundError, NotADirectoryError) as exc:
        print(f"wecoder: error: {exc}", flush=True)
        return 1

    # CRITICAL: print the resolved root before any model call.
    print(f"workspace: {workspace_obj.root}", flush=True)

    effective_provider = provider or settings.model.provider
    effective_model = model or settings.model.model
    effective_max_turns = max_turns if max_turns is not None else settings.limits.max_turns
    if effective_max_turns <= 0:
        print("wecoder: error: --max-turns must be a positive integer", flush=True)
        return 1

    import os

    env_vars = env if env is not None else os.environ

    try:
        model_provider = _build_model(
            settings,
            effective_provider,
            effective_model,
            env_vars,
        )
    except WecoderError as exc:
        print(f"wecoder: error: {exc}", flush=True)
        return 1

    session = Session(workspace=workspace_obj)
    agent = DeveloperAgent(model=model_provider)

    try:
        result = asyncio.run(
            agent.run(
                task,
                session,
                max_turns=effective_max_turns,
                max_tokens=settings.limits.max_tokens,
            )
        )
    except WecoderError as exc:
        print(f"wecoder: error: {exc}", flush=True)
        return 1
    except Exception as exc:  # pragma: no cover - guards the loop boundary
        _LOGGER.exception("unexpected error during run")
        print(f"wecoder: internal error: {exc}", flush=True)
        return 2
    finally:
        try:
            asyncio.run(model_provider.aclose())
        except Exception:  # pragma: no cover - best-effort cleanup
            pass

    if json_output:
        _print_json(result, workspace_obj)
    else:
        _print_human(result, workspace_obj)
    return result.exit_code


def _build_model(settings, provider_id, model_name, env_vars):
    """Construct a ModelProvider.

    Honours the ``WECODER_FAKE_MODEL`` test hook; otherwise uses the
    registry with an overridden provider/model if the CLI flags differ from
    the loaded settings.
    """
    if env_vars.get(_FAKE_ENV):
        return _build_fake_model(env_vars)

    # Apply CLI overrides to settings for registry construction.
    from dataclasses import replace

    overridden = replace(
        settings,
        model=replace(
            settings.model,
            provider=provider_id,
            model=model_name,
        ),
    )
    return default_registry().create(overridden)


def _build_fake_model(env_vars):
    """Construct a FakeModel from a scripted JSON file for offline tests."""
    from wecoder.models.types import Message

    script_path = env_vars.get(_FAKE_SCRIPT_ENV)
    if not script_path:
        # Default minimal script: a single final message with no tools.
        responses = [
            _fake_response(Message("assistant", "No script provided; nothing to do."))
        ]
    else:
        text = Path(script_path).read_text(encoding="utf-8")
        script = _json.loads(text)
        responses = [_fake_response_from_entry(entry) for entry in script]

    from tests.models.fakes import FakeModel

    fake = FakeModel(responses)
    # FakeModel advertises tool_calling=False; override for the agent loop.
    fake.capabilities = lambda: __import__(
        "wecoder.models.types", fromlist=["ModelCapabilities"]
    ).ModelCapabilities(streaming=False, tool_calling=True, json_mode=False)
    return fake


def _fake_response_from_entry(entry: dict):
    from wecoder.models.types import CompletionResponse, Message, ToolCall, Usage

    content = entry.get("content", "")
    role = entry.get("role", "assistant")
    tool_calls = None
    raw_calls = entry.get("tool_calls")
    if isinstance(raw_calls, list):
        tool_calls = [
            ToolCall(
                id=str(c.get("id", "")),
                name=c["name"],
                arguments=c.get("arguments", ""),
            )
            for c in raw_calls
            if isinstance(c, dict) and "name" in c
        ] or None
    msg = Message(role, content, tool_calls=tool_calls)
    usage_in = entry.get("usage", {})
    usage = Usage(
        input_tokens=usage_in.get("input_tokens") if isinstance(usage_in, dict) else None,
        output_tokens=usage_in.get("output_tokens") if isinstance(usage_in, dict) else None,
    )
    return CompletionResponse(
        message=msg,
        usage=usage,
        finish_reason=entry.get("finish_reason", "stop"),
        provider_id="fake",
        model=entry.get("model", "fake"),
    )


def _fake_response(message):
    from wecoder.models.types import CompletionResponse, Usage

    return CompletionResponse(
        message=message,
        usage=Usage(input_tokens=1, output_tokens=1),
        finish_reason="stop",
        provider_id="fake",
        model="fake",
    )


def _print_human(result, workspace_obj) -> None:
    print(f"status: {result.status}", flush=True)
    if result.plan:
        print("plan:", flush=True)
        for line in result.plan.splitlines():
            print(f"  {line}", flush=True)
    print(f"summary: {result.summary}", flush=True)
    if result.changed_files:
        print("changed files:", flush=True)
        for f in result.changed_files:
            print(f"  {f}", flush=True)
    if result.commands:
        print("commands:", flush=True)
        for cmd in result.commands:
            print(f"  {' '.join(cmd.argv)} (exit {cmd.exit_code})", flush=True)
    usage = result.usage
    if usage.input_tokens or usage.output_tokens:
        print(
            f"usage: {usage.input_tokens or 0} in / {usage.output_tokens or 0} out",
            flush=True,
        )
    print(f"stop reason: {result.stop_reason}", flush=True)


def _print_json(result, workspace_obj) -> None:
    payload = {
        "status": result.status,
        "summary": result.summary,
        "plan": result.plan,
        "changed_files": result.changed_files,
        "commands": [
            {"argv": cmd.argv, "exit_code": cmd.exit_code} for cmd in result.commands
        ],
        "usage": {
            "input_tokens": result.usage.input_tokens,
            "output_tokens": result.usage.output_tokens,
        },
        "stop_reason": result.stop_reason,
        "workspace": str(workspace_obj.root),
    }
    print(_json.dumps(payload, indent=2), flush=True)


__all__ = ["run"]
