"""The single Developer coding-agent loop (Phase 04 MVP).

The agent accepts a natural-language task, packs workspace context, calls the
model with the tool registry's schemas, executes tool calls **sequentially**
through the registry (so Phase 03 jail/denylist/limits still apply), appends
results to the conversation, and stops on completion, block, or budget.

Design rules enforced here:
- Depends only on :class:`ModelProvider` — no vendor SDK imports.
- Never writes files or runs subprocesses directly; every mutation goes
  through :class:`ToolRegistry` tools.
- ``changed_files`` / ``commands`` are derived from actual tool results, not
  from model prose.
- No ``if provider == "..."`` branching.
"""

from __future__ import annotations

import json
import logging

from wecoder.agent.prompts import load_developer_prompt
from wecoder.agent.result import AgentResult, CommandRecord
from wecoder.agent.session import Session, SessionStatus
from wecoder.context.packer import ContextPacker
from wecoder.models.base import ModelProvider
from wecoder.models.errors import ModelConfigError, ModelError
from wecoder.models.types import (
    CompletionRequest,
    CompletionResponse,
    Message,
    ToolCall,
    ToolSpec,
)
from wecoder.tools.base import ToolContext, ToolLimits, ToolResult
from wecoder.tools.registry import ToolRegistry, default_registry
from wecoder.workspace.workspace import Workspace

_LOGGER = logging.getLogger("wecoder.agent")

# Marker prefixed to the plan so it can be extracted from the first assistant
# message without an extra model call.
_PLAN_MARKER = "PLAN:"


class DeveloperAgent:
    """The MVP single-agent loop.

    Args:
        model: A configured :class:`ModelProvider` (FakeModel in tests,
            Ollama or OpenAI-compatible in production).
        registry: The tool registry the agent may call. Defaults to the six
            Phase 03 built-ins.
    """

    def __init__(
        self,
        model: ModelProvider,
        *,
        registry: ToolRegistry | None = None,
    ) -> None:
        self._model = model
        self._registry = registry or default_registry()

    async def run(
        self,
        task: str,
        session: Session,
        *,
        max_turns: int,
        max_tokens: int | None = None,
    ) -> AgentResult:
        """Execute ``task`` against ``session`` and return an :class:`AgentResult`.

        ``max_turns`` is the hard backstop; ``max_tokens`` (if the provider
        reports usage) is enforced when known.
        """
        if not task.strip():
            return AgentResult(
                status="failed",
                summary="empty task: no work requested",
                stop_reason="empty_task",
            )

        # Fail fast if the provider cannot do tool calling (MVP assumes tools).
        caps = self._model.capabilities()
        if not caps.tool_calling:
            raise ModelConfigError(
                f"provider {self._model.id!r} does not advertise tool calling; "
                "the MVP agent requires a tool-calling model"
            )

        # Pack the initial workspace context once (ADR-019 budget).
        bundle = ContextPacker().pack(session.workspace)
        system_prompt = _build_system_prompt(bundle)

        session.add_message(Message("system", system_prompt))
        session.add_message(Message("user", task))

        tool_specs = self._tool_specs()
        ctx = ToolContext(
            workspace=session.workspace,
            policy=_default_policy(),
            limits=ToolLimits(),
        )

        plan: str | None = None
        changed_files: list[str] = []
        commands: list[CommandRecord] = []
        tool_executed = False

        try:
            while True:
                if session.turns >= max_turns:
                    return _finish(
                        session,
                        status="budget_exceeded",
                        summary=(
                            f"turn budget reached ({max_turns}) before the task "
                            "completed"
                        ),
                        plan=plan,
                        changed_files=changed_files,
                        commands=commands,
                        stop_reason="max_turns",
                    )

                response = await self._call_model(session, tool_specs, max_tokens)
                session.turns += 1
                session.accumulate_usage(response.usage)

                if _tokens_exceeded(session, max_tokens):
                    return _finish(
                        session,
                        status="budget_exceeded",
                        summary=(
                            f"token budget reached (~{session.total_tokens}) "
                            "before the task completed"
                        ),
                        plan=plan,
                        changed_files=changed_files,
                        commands=commands,
                        stop_reason="max_tokens",
                    )

                assistant_msg = response.message
                session.add_message(assistant_msg)

                if plan is None:
                    plan = _extract_plan(assistant_msg.content)

                tool_calls = assistant_msg.tool_calls
                if not tool_calls:
                    # No tool calls. If the agent has already executed tools, or
                    # the model has had more than one turn, treat this as the
                    # final answer. Otherwise it is a plan-only first message
                    # and the loop continues to the next model call.
                    if tool_executed or session.turns > 1:
                        return _finish(
                            session,
                            status="succeeded",
                            summary=_clean_summary(assistant_msg.content),
                            plan=plan,
                            changed_files=changed_files,
                            commands=commands,
                            stop_reason="final_message",
                        )
                    # Plan-only first message: continue the loop.
                    continue

                # Execute tool calls sequentially through the registry.
                tool_executed = True
                for call in tool_calls:
                    result, record_file, record_cmd = await self._execute_tool(
                        call, ctx
                    )
                    if record_file:
                        changed_files.append(record_file)
                    if record_cmd is not None:
                        commands.append(record_cmd)

                    # Feed the tool result back to the model.
                    session.add_message(
                        Message(
                            "tool",
                            result.output,
                            tool_call_id=call.id or call.name,
                        )
                    )

                    # Security denial: log and let the model choose another
                    # safe action. The turn cap prevents infinite retries.
                    if result.error_type in ("PathEscapeError", "DeniedSecretError"):
                        _LOGGER.warning(
                            "tool %s denied (%s) — returning to model",
                            call.name,
                            result.error_type,
                        )

                # If the model keeps repeating a denied call, the turn cap
                # will stop it; we do not add sleeps or retries here.

        except ModelError as exc:
            _LOGGER.debug("model error in agent loop", exc_info=True)
            return _finish(
                session,
                status="failed",
                summary=f"model error: {exc}",
                plan=plan,
                changed_files=changed_files,
                commands=commands,
                stop_reason="model_error",
            )
        except Exception as exc:  # pragma: no cover - unexpected internal failure
            _LOGGER.exception("unexpected error in agent loop")
            return _finish(
                session,
                status="failed",
                summary=f"internal error: {exc}",
                plan=plan,
                changed_files=changed_files,
                commands=commands,
                stop_reason="internal_error",
            )

    async def _call_model(
        self,
        session: Session,
        tool_specs: list[ToolSpec],
        max_tokens: int | None,
    ) -> CompletionResponse:
        request = CompletionRequest(
            model="",  # provider uses its configured model; empty = default
            messages=list(session.messages),
            tools=tool_specs,
            max_tokens=max_tokens,
        )
        return await self._model.complete(request)

    def _tool_specs(self) -> list[ToolSpec]:
        return [
            ToolSpec(
                name=str(entry["name"]),
                description=str(entry["description"]) if entry["description"] else None,
                parameters=entry["parameters"]  # type: ignore[arg-type]
                if isinstance(entry.get("parameters"), dict)
                else None,
            )
            for entry in self._registry.schemas()
        ]

    async def _execute_tool(
        self, call: ToolCall, ctx: ToolContext
    ) -> tuple[ToolResult, str | None, CommandRecord | None]:
        """Execute one tool call through the registry.

        Returns ``(tool_result, changed_file, command_record)``.  Mutations
        and commands are tracked only from successful tool results.
        """
        name = call.name
        args = _parse_arguments(call.arguments)
        try:
            tool = self._registry.get(name)
        except Exception as exc:
            result = ToolResult.failure(
                f"unknown tool {name!r}: {exc}", error_type="ToolError"
            )
            return result, None, None

        try:
            result = await tool.execute(args, ctx)
        except Exception as exc:  # pragma: no cover - tools return results
            result = ToolResult.failure(
                f"tool {name!r} crashed: {exc}", error_type="ToolError"
            )

        changed_file = _track_changed_file(name, args, result, ctx.workspace)
        command_record = _track_command(name, args, result)
        return result, changed_file, command_record


def _default_policy():
    from wecoder.safety import DefaultPolicy

    return DefaultPolicy()


def _build_system_prompt(bundle) -> str:  # type: ignore[no-untyped-def]
    """Compose the developer prompt with the packed context."""
    base = load_developer_prompt()
    context = (
        f"\n\n## Workspace context\n\n"
        f"Root: {bundle.root}\n"
        f"Language hints: {', '.join(bundle.language_hints) or '(none)'}\n"
        f"Tree excerpt:\n{bundle.tree_excerpt}\n"
    )
    if bundle.notes:
        context += "Notes: " + "; ".join(bundle.notes) + "\n"
    return base + context


def _parse_arguments(raw: str) -> dict[str, object]:
    """Parse a tool call's JSON arguments string into a dict."""
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def _extract_plan(content: str) -> str | None:
    """Extract a plan from the first assistant message.

    The model is instructed to produce a short plan first.  We look for a
    ``PLAN:`` marker; if absent, we take the first non-empty lines as the
    plan up to a reasonable length.
    """
    if not content:
        return None
    text = content.strip()
    if _PLAN_MARKER in text:
        after = text.split(_PLAN_MARKER, 1)[1].strip()
        # Plan ends at the first blank line or after a few lines.
        lines: list[str] = []
        for line in after.splitlines():
            if not line.strip():
                break
            lines.append(line.strip())
            if len(lines) >= 10:
                break
        return "\n".join(lines) if lines else None
    # No marker: treat the whole first message (capped) as the plan.
    snippet = text[:500]
    return snippet if snippet else None


def _clean_summary(content: str) -> str:
    """Strip any plan marker from the final assistant message for the summary."""
    if _PLAN_MARKER in content:
        parts = content.split(_PLAN_MARKER, 1)
        # Keep text after the plan block.
        summary = parts[-1].strip()
        return summary or content.strip()
    return content.strip()


def _track_changed_file(
    tool_name: str,
    args: dict[str, object],
    result: object,  # ToolResult
    workspace: Workspace,
) -> str | None:
    """Return the workspace-relative path a write tool mutated, if successful."""
    if not getattr(result, "ok", False):
        return None
    if tool_name not in ("write_file", "edit_file"):
        return None
    raw_path = args.get("path")
    if not isinstance(raw_path, str):
        return None
    try:
        resolved = workspace.resolve(raw_path)
        return str(resolved.relative_to(workspace.root))
    except Exception:
        return raw_path


def _track_command(
    tool_name: str,
    args: dict[str, object],
    result: object,  # ToolResult
) -> CommandRecord | None:
    """Return a :class:`CommandRecord` for an executed run_command call."""
    if tool_name != "run_command":
        return None
    data = getattr(result, "data", None) or {}
    argv = args.get("argv")
    if not isinstance(argv, list):
        argv = data.get("argv", [])
    exit_code = data.get("exit_code")
    if not isinstance(exit_code, int):
        exit_code = -1
    return CommandRecord(argv=[str(a) for a in argv], exit_code=exit_code)


def _tokens_exceeded(session: Session, max_tokens: int | None) -> bool:
    if max_tokens is None:
        return False
    total = session.total_tokens
    return total is not None and total >= max_tokens


def _finish(
    session: Session,
    *,
    status: SessionStatus,
    summary: str,
    plan: str | None,
    changed_files: list[str],
    commands: list[CommandRecord],
    stop_reason: str,
) -> AgentResult:
    session.status = status
    return AgentResult(
        status=status,  # type: ignore[arg-type]
        summary=summary,
        plan=plan,
        changed_files=changed_files,
        commands=commands,
        usage=session.usage,
        stop_reason=stop_reason,
    )


__all__ = ["DeveloperAgent"]
