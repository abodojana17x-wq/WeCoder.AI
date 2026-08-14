"""Jailed shell tool (Phase 03).

Runs a command inside the workspace with:

* ``shell=False`` and an argv list (never ``shell=True``)
* the cwd fixed inside the workspace jail
* a new process group killed on timeout
* a minimal, allowlisted environment (no blanket parent env)
* best-effort secret redaction in captured output

Non-zero exits are returned as ``ToolResult(ok=False)`` with the captured
stderr/stdout — they are a *result*, not an exception.  Only timeouts and
infrastructure crashes raise.
"""

from __future__ import annotations

import os
import re
import signal
import subprocess
from pathlib import Path

from wecoder.errors import CommandTimeoutError, PathEscapeError, ToolError
from wecoder.tools.base import ToolContext, ToolResult
from wecoder.tools.fs import _truncate

# Environment variables forwarded to subprocesses.  We start from a minimal
# allowlist rather than copying the parent env so we never leak credentials
# that happen to live in the surrounding environment.
_ALLOWED_ENV_VARS: tuple[str, ...] = (
    "PATH",
    "HOME",
    "LANG",
    "LC_ALL",
    "VIRTUAL_ENV",
    "SYSTEMROOT",  # needed on Windows for Python subprocesses
    "USER",
)

# Best-effort secret redaction patterns applied to captured command output.
# This is intentionally a small set of high-signal patterns; it is documented
# as best-effort and not a security boundary.
_SECRET_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{36}"),
    re.compile(r"gho_[A-Za-z0-9]{36}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
)


def _build_env() -> dict[str, str]:
    """Build a minimal, allowlisted environment for subprocesses."""
    env: dict[str, str] = {}
    for key in _ALLOWED_ENV_VARS:
        value = os.environ.get(key)
        if value is not None:
            env[key] = value
    # ``PYTHONPATH`` is intentionally NOT forwarded; subprocesses must not
    # inherit the WeCoder import path by accident.
    return env


def _redact(text: str) -> str:
    """Best-effort redaction of obvious secret patterns in ``text``."""
    redacted = text
    for pattern in _SECRET_PATTERNS:
        redacted = pattern.sub("***REDACTED***", redacted)
    return redacted


class RunCommand:
    """Run a command in the workspace with a bounded timeout."""

    name = "run_command"
    description = (
        "Run a command inside the workspace with shell=False, a bounded "
        "timeout, a scrubbed environment, and captured stdio. The cwd is "
        "jailed to the workspace root (a relative subdir is allowed)."
    )
    parameters_schema: dict[str, object] = {
        "type": "object",
        "properties": {
            "argv": {
                "type": "array",
                "items": {"type": "string"},
                "description": "The command and its arguments as a list. "
                "Never run through a shell.",
            },
            "cwd": {
                "type": "string",
                "description": "Optional working directory relative to the "
                "workspace root. External paths are rejected.",
            },
            "timeout": {
                "type": "integer",
                "description": "Optional timeout in seconds. Capped by the "
                "policy default (30s).",
            },
        },
        "required": ["argv"],
        "additionalProperties": False,
    }

    async def execute(self, args: dict[str, object], ctx: ToolContext) -> ToolResult:
        try:
            raw_argv = args.get("argv")
            if not isinstance(raw_argv, list) or not raw_argv:
                return ToolResult.failure("'argv' must be a non-empty list")
            argv = [str(a) for a in raw_argv]
            if not all(isinstance(a, str) and a != "" for a in argv):
                return ToolResult.failure("'argv' entries must be non-empty strings")

            cwd_rel = args.get("cwd") or "."
            cwd = ctx.workspace.resolve(str(cwd_rel))
            if not cwd.exists():
                return ToolResult.failure(f"cwd does not exist: {cwd_rel}")
            if not cwd.is_dir():
                return ToolResult.failure(f"cwd is not a directory: {cwd_rel}")

            raw_timeout = args.get("timeout")
            if isinstance(raw_timeout, bool) or not isinstance(raw_timeout, int):
                timeout = ctx.limits.command_timeout_seconds
            else:
                timeout = raw_timeout
            ctx.policy.check_command(ctx.workspace, argv=argv, timeout=timeout)

            try:
                return await self._run(argv, cwd, timeout, ctx)
            except CommandTimeoutError as exc:
                return ToolResult.failure(
                    f"command timed out after {timeout}s: {' '.join(argv)}",
                    error_type=type(exc).__name__,
                    data={"argv": argv, "timeout": timeout},
                )
        except (PathEscapeError, ToolError) as exc:
            return _error_result(exc)
        except OSError as exc:
            return _error_result(exc)

    async def _run(
        self,
        argv: list[str],
        cwd: Path,
        timeout: int,
        ctx: ToolContext,
    ) -> ToolResult:
        env = _build_env()
        limit = ctx.limits.max_command_output_bytes
        try:
            proc = subprocess.Popen(  # noqa: S603 - argv is a list, shell=False
                argv,
                cwd=str(cwd),
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                start_new_session=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            return ToolResult.failure(
                f"command not found: {argv[0]}",
                error_type="CommandFailedError",
                data={"argv": argv},
            )

        try:
            stdout, stderr = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            _kill_process_group(proc)
            # Drain whatever was captured before the kill.
            try:
                stdout, stderr = proc.communicate(timeout=5)
            except Exception:  # pragma: no cover - best-effort drain
                stdout, stderr = "", ""
            raise CommandTimeoutError(
                f"command timed out after {timeout}s: {' '.join(argv)}"
            ) from exc

        stdout = _redact(stdout or "")
        stderr = _redact(stderr or "")
        combined = stdout + stderr
        truncated = len(combined) > limit
        stdout = _truncate(stdout, limit)
        stderr = _truncate(stderr, limit)

        exit_code = proc.returncode if proc.returncode is not None else -1
        output = (
            f"exit code: {exit_code}\n"
            f"--- stdout ---\n{stdout}"
            + (f"\n--- stderr ---\n{stderr}" if stderr else "")
        )
        ok = exit_code == 0
        return ToolResult(
            ok=ok,
            output=output,
            data={
                "exit_code": exit_code,
                "stdout": stdout,
                "stderr": stderr,
                "truncated": truncated,
                "argv": argv,
            },
            error_type=None if ok else "CommandFailedError",
        )


def _kill_process_group(proc: subprocess.Popen[str]) -> None:
    """Terminate the process group started with ``start_new_session=True``."""
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
    except (ProcessLookupError, PermissionError, OSError):
        return
    try:
        proc.wait(timeout=3)
    except Exception:  # pragma: no cover - escalation path
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError, OSError):
            pass


def _error_result(exc: Exception) -> ToolResult:
    if isinstance(exc, ToolError):
        return ToolResult.failure(str(exc), error_type=type(exc).__name__)
    return ToolResult.failure(f"{type(exc).__name__}: {exc}", error_type="ToolError")


__all__ = ["RunCommand"]
