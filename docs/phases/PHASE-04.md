# Phase 4 — Single Coding Agent (MVP)

## Objective

Ship the first genuinely useful WeCoder.AI: one Developer agent that takes a natural-language task, inspects the bound workspace through tools, plans, edits files, runs bounded commands, and prints a structured result — using `ModelProvider` and nothing else.

This phase **is the MVP**. See `docs/MVP.md`.

## Why This Phase Exists

Phases 01–03 are machinery. This phase is the product. Until a single agent can land a change, dual-agent critique, routers, and memory are theater.

## Current State

After Phases 01–03:

- CLI, settings, logging exist
- Model providers + FakeModel exist
- Workspace, tools, context packer exist
- No agent loop, no `wecoder run`

If those are missing, stop.

## Target State

A user can run:

```text
wecoder run "Add a function greet(name) -> str in app/hello.py and a unit test"
```

The agent:

1. Packs context
2. Calls the configured model with tool schemas
3. Executes tool calls through the registry (jail still enforced)
4. Stops on completion, block, or budget
5. Prints plan/summary, files changed, commands run, usage, status

Offline path uses Ollama. Cloud path uses `openai_compat`. Tests use FakeModel.

## Scope

**In scope**

- Session object **in memory** for one invocation (persistence is Phase 08)
- Developer system prompt
- Tool-calling loop
- Budget enforcement (`max_turns`, `max_tokens` from Settings)
- `wecoder run "…"` CLI (plus optional `--provider`, `--model`, `--workspace`)
- User-visible plan and final `AgentResult`
- Fixture mini-app under `tests/fixtures/`
- Integration tests with FakeModel

**Out of scope**

- Second agent / Architect (Phase 07)
- Specialized test-repair controller (Phase 05) — the agent *may* call `run_command` with `pytest`
- Approval UI and Git writes (Phase 06)
- Session database (Phase 08)
- Router (Phase 09)
- Memory (Phase 11)

## Architecture

```
CLI run
  → Settings + Workspace.open
  → ContextPacker.pack
  → ModelRegistry.create
  → Agent(role=developer).run(task, session)
        loop:
          model.complete(messages, tools=registry.specs)
          if tool_calls: execute each, append tool results
          else: finish
          if budgets exceeded: stop
  → render AgentResult
```

One process. Sequential tool calls in this phase (no parallel tool fan-out required).

## Components

| Component | Responsibility |
|-----------|----------------|
| `Session` | messages, turn count, usage sum, status |
| `Agent` | loop, stop conditions |
| `Developer` prompt | role instructions: inspect before edit, small diffs, do not escape jail, do not read secrets |
| `AgentResult` | status, summary, changed_files, commands, usage, error |
| CLI renderer | human-readable output; optional `--json` is nice and allowed |
| Fixture mini-app | regression target |

## Interfaces / Contracts

### Session (in-memory)

```text
id: str
workspace: Workspace
messages: list[Message]
turns: int
usage: Usage            # accumulated
status: "running" | "succeeded" | "failed" | "blocked" | "budget_exceeded"
```

### AgentResult

```text
status: as above
summary: str
plan: str | None
changed_files: list[str]
commands: list[{argv, exit_code}]
usage: Usage
stop_reason: str
```

`changed_files` should be derived from successful `write_file` / `edit_file` tool calls, not from trusting the model’s prose.

### Stop conditions

Stop when any is true:

- Model returns a final assistant message with no tool calls and (optionally) a structured “done”
- `turns >= max_turns`
- accumulated tokens >= `max_tokens` (if usage known; if unknown, turn cap is the backstop)
- A tool returns `PathEscapeError` / `DeniedSecretError` — record and **do not retry the same call blindly**; the model may try something else until budgets hit
- Unrecoverable `ModelError`

### System prompt requirements (normative intent, not exact wording)

The Developer must be instructed to:

- Work only inside the workspace
- Inspect before editing
- Prefer `edit_file` for small changes
- Not dump or request denylisted files
- Not invent commands that need network installs
- Produce a short plan first (either as the first assistant message or a dedicated `plan` field you extract)
- Stop when the task is done or blocked, with a concise summary

Keep the prompt in a module or markdown under `wecoder/agent/prompts/`, not hardcoded in the CLI.

### CLI

```text
wecoder run TASK
  --workspace PATH     default cwd
  --provider ID
  --model NAME
  --json
  --max-turns N
```

Print workspace root **before** any model call so the user can Ctrl-C.

Exit codes:

- 0 if `succeeded`
- 1 if `failed` / `blocked` / `budget_exceeded` / config errors
- 2 unexpected internals

(If this conflicts with Phase 01’s “1 = config”, prefer: 1 for any expected operational failure including budget, and keep 2 for bugs. Document it.)

## Files Expected To Be Created

```
wecoder/agent/__init__.py
wecoder/agent/loop.py
wecoder/agent/session.py
wecoder/agent/result.py
wecoder/agent/prompts/developer.md   # or .py string
wecoder/cli/run_cmd.py
tests/agent/test_loop.py
tests/agent/test_run_cli.py
tests/fixtures/mini_app/             # small Python project
tests/fixtures/mini_app/tests/...
```

## Files Expected To Be Modified

- `wecoder/cli/app.py` — register `run`
- `wecoder/models/types.py` — only if tool-call fields need a backward-compatible fix
- Provider adapters — only if they do not yet pass `tools` through (additive)
- `pyproject.toml` — only if needed

## Files That Must NOT Be Modified

- `LICENSE`
- Planning docs
- Tool jail / denylist behavior (agent must not gain a bypass)
- Phase 01–03 CLI commands except additive help

## Dependencies

- Phase 01 Settings, CLI, errors
- Phase 02 `ModelProvider`, FakeModel, tool-capable request types
- Phase 03 Workspace, tools, packer

If providers cannot yet send tool specs, fix that *minimally* here (still Phase 04 scope, because the MVP cannot work otherwise). Do not add new vendors.

## Implementation Requirements

1. The agent never imports `openai` / `ollama` clients directly.
2. The agent never writes files except via tools (so jail applies).
3. FakeModel integration test: script a sequence (optional plan text → `write_file` → `edit_file` or second write → final message). Assert the file exists on disk in the temp workspace and `AgentResult.changed_files` contains it.
4. A second test: FakeModel tries `read_file` on `.env`; tool denies; agent result does not include that file’s contents (even if FakeModel later echoes them — the tool output must be the denial).
5. Budget test: `max_turns=1` and a model that always requests a tool → `budget_exceeded`, no infinite loop.
6. Fixture mini-app is a valid tiny Python project the agent can be aimed at manually.
7. Live Ollama is **not** required for pytest. Document a manual command for MVP acceptance (`docs/MVP.md` section 7).
8. If the selected provider advertises `tool_calling=False`, fail fast with a clear `ModelConfigError` or degrade to a single-shot “propose a patch” mode **only if** you can still apply edits safely. Prefer fail-fast: MVP assumes tool calling.

## Error Handling

- Model transport errors → status `failed`, summary explains provider error, exit 1
- Jail/denylist → tool result to the model; do not crash the CLI
- Unexpected exception in the loop → log, status `failed`, exit 2
- Empty task string → usage error, no model call

## Security Requirements

- Print resolved workspace before work
- No policy bypass flags in this phase
- Do not auto-run `curl | sh`, package installs, or commands outside the jail (shell tool already constrained)
- Do not attach the entire environment to the prompt
- System prompt cannot instruct the model that it may ignore the jail

## Performance Requirements

- Bound the loop. No sleep-retry storms.
- Do not pack more than the Phase 03 context budget.
- Stream tokens to the terminal if streaming is available; not required for Done.

## Cost Considerations

- One model, one loop, hard caps.
- Do not call the model to “summarize tools” extra times unless part of the same turn.
- `inspect` remains free (no model). `run` is the paid/local-compute path.

## Testing Requirements

See Implementation Requirements 3–5, plus:

- CLI `wecoder run --help` works
- CLI integration with FakeModel injected via a clearly documented test hook (e.g. env `WECODER_FAKE_MODEL=1` or a pytest monkeypatch on the registry). Do not require network.
- changed_files tracking
- usage accumulated from FakeModel-reported tokens

## Acceptance Tests

Automated:

1. pytest green offline including agent integration tests
2. Jail still holds when the agent is the caller
3. Budget stop works

Manual (MVP.md):

4. At least one Ollama run on the fixture or a throwaway clone
5. At least one external small repo task, human-reviewed

Do not claim MVP complete without the manual offline run.

## Deliverables

- `wecoder run`
- Single Developer agent loop
- AgentResult renderer
- Fixture mini-app
- Integration tests
- Honest CLI help: no product Git, no second agent, user should work on a branch

## Definition of Done

- `docs/MVP.md` automated acceptance criteria are met
- Manual offline run documented in the implementation report (command + outcome)
- No Architect, no Git writer, no session DB, no router

## Risks

- Implementing “just a little Architect” because the README said so. **Out of scope.**
- Letting the model output a full file in chat and writing it without the tool (bypasses caps). **Forbidden.** All writes via tools.
- Infinite tool loops. Must be tested.
- Provider tool-call format mismatches (Ollama vs OpenAI). Handle in adapters, not with `if provider` in the agent.

## Explicitly Deferred Work

- Phase 05 specialized repair
- Phase 06 approval + Git
- Phase 07 dual-agent
- Persistent sessions, TUI, router, memory, extra modes

## Handoff To Next Phase

Phase 05 will wrap execution/testing around `AgentResult` and add a repair loop that still uses this same agent or a thin controller. Do not rename `AgentResult` casually. Phase 06 will persist checkpoints before mutating runs.

---

## Implementation Prompt

```
You are implementing Phase 04 of WeCoder.AI and ONLY Phase 04 (the MVP).

Read first:
- docs/phases/PHASE-04.md
- docs/MVP.md
- docs/PRODUCT_NORTH_STAR.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-005, ADR-010, ADR-021)

Inspect the repository. Phases 01–03 must exist (CLI, ModelProvider, FakeModel, Workspace, tools, context packer). If they do not, stop and report what is missing. Do not silently implement earlier phases beyond the minimum needed to compile — if foundations are missing, stop.

Implement ONLY the single Developer coding agent:
- In-memory Session and Agent loop with tool calling through ToolRegistry
- Budgets: max_turns, max_tokens
- `wecoder run` CLI with workspace/provider/model flags
- AgentResult (status, summary, plan, changed_files from actual tool calls, commands, usage)
- tests/fixtures/mini_app
- Offline tests using FakeModel (scripted tool calls, jail denial, budget stop)

Rules:
- The agent must not import vendor SDKs.
- All file writes go through tools (jail + denylist still apply).
- No Architect, no multi-agent, no Git commits/rollback, no approval UI, no session database, no router, no memory, no web UI.
- Do not implement Phase 05’s dedicated test-repair controller.
- Preserve existing functionality. Additive CLI only.
- Do not modify LICENSE or planning documents.

After implementation:
- Run relevant tests and linters.
- If you can, perform the documented manual Ollama run on the fixture and report the outcome. If you cannot, say so explicitly.
- Report files created/modified, tests, failures.
- Stop. Do not start Phase 05.
```
