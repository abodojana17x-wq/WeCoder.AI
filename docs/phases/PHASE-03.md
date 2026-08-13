# Phase 3 — Workspace, Context & Tool System

## Objective

Give WeCoder eyes and hands: bind a workspace root, refuse path escape, ignore bulky/secret files, pack a budgeted project sketch, and expose a tool registry with filesystem, search, and jailed shell tools.

No agent loop yet. Tools must be callable from tests and (optionally) a debug CLI.

## Why This Phase Exists

Phase 04 cannot be a coding agent if it cannot read a repo or write a file. This phase also installs the security boundary (workspace jail, secret denylist, command timeout) *before* a model is allowed to propose commands (ADR-014, ADR-015).

## Current State

After Phases 01–02:

- CLI, settings, model providers exist
- Settings have `project.workspace` as a string
- No workspace resolution, no tools, no context packer

## Target State

- A `Workspace` object resolves and holds an absolute root
- All file operations go through it
- `ToolRegistry` lists tools with JSON-schema parameters
- Tools return a structured `ToolResult`
- Context packer produces a size-capped sketch (root listing, language hints, ignore stats)
- `wecoder inspect` (or `wecoder workspace info`) prints the sketch for humans
- Tests prove jail, denylist, and ignore behavior

## Scope

**In scope**

- Workspace bind + path jail
- Ignore rules (`.gitignore` + built-in defaults)
- Secret-file denylist for **reads**
- Tools: `list_dir`, `read_file`, `write_file`, `edit_file`, `search_text`, `run_command`
- Tool registry and JSON schemas
- Context packer with byte/token-ish caps
- Debug/info CLI
- Policy *hooks* as a simple allow/deny callback or `Policy` protocol with a default “allow all except jail/denylist/timeout” — the interactive approval UI is Phase 06

**Out of scope**

- Agent loop / tool-calling conversation (Phase 04)
- Git mutating commands (Phase 06); read-only `git status` as a *shell* command is possible but do not add a Git tool API yet
- Test runner productization (Phase 05)
- Memory, embeddings, vector DB
- Container sandbox
- MCP

## Architecture

```
Settings.project.workspace
    → Workspace.open(path) → root, ignore, denylist

ToolRegistry
    → Tool.execute(args, ToolContext(workspace, policy, budgets))
        → ToolResult(ok, data | error, metadata)

ContextPacker.pack(workspace, extra_paths=[]) → ContextBundle
```

The agent (next phase) will see tools only through the registry schemas and `ToolResult` text.

## Components

| Component | Responsibility |
|-----------|----------------|
| `Workspace` | Root, resolve, jail, open text files |
| `IgnoreMatcher` | `.gitignore` + defaults |
| `SecretDenylist` | Refuse automatic reads of credential-like paths |
| `Tool` protocol | name, description, parameters_schema, execute |
| `ToolRegistry` | name → tool |
| `run_command` | subprocess in workspace cwd, timeout, captured stdio |
| `ContextPacker` | Budgeted sketch |
| Default `Policy` | Enforces jail (already in workspace), denylist, max file bytes, command timeout |

## Interfaces / Contracts

### Workspace

```text
Workspace.root: Path          # absolute, resolved
Workspace.resolve(user_path: str) -> Path
    # join + resolve; raise ToolError/PathEscapeError if not inside root
```

Symlinks: resolve and refuse if the **final** path is outside the root.

### Built-in ignore defaults (minimum)

`.git/`, `.wecoder/sessions/`, `__pycache__/`, `.venv/`, `venv/`, `node_modules/`, `dist/`, `build/`, `.mypy_cache/`, `.ruff_cache/`, `*.pyc`

Also honor the workspace’s `.gitignore` if present (a simple implementation is acceptable; do not vendor a full git engine if a maintained library is lighter — `pathspec` is acceptable).

### Secret denylist (read)

Refuse `read_file` (and context packing) for paths whose names match:

- `.env`, `.env.*` (allow `.env.example` if you want — document it)
- `*.pem`, `*.p12`, `*.key`
- `id_rsa`, `id_ed25519`, `*.ppk`
- `credentials.json`, `service-account*.json`
- files under `.ssh/` and `.aws/` if they appear inside the workspace

`write_file` to these paths is also denied in this phase (safer default).

### Tools

Each tool:

```text
name: str
description: str
parameters_schema: dict   # JSON Schema object
async def execute(args: dict, ctx: ToolContext) -> ToolResult
```

`ToolResult`:

```text
ok: bool
output: str               # model-facing text, size-capped
data: dict | None         # optional structured
error_type: str | None
```

Caps (defaults, Settings-overridable later if easy; constants are fine):

| Limit | Default |
|-------|---------|
| Max read file bytes | 200_000 |
| Max write file bytes | 200_000 |
| Max `list_dir` entries returned | 200 |
| Max search matches | 50 |
| Max command stdout+stderr | 32_000 bytes |
| Command timeout | 30 seconds |
| Context sketch bytes | 20_000 |

### `run_command`

- `argv` as a list **or** a single string run with `shell=False` via `shlex` on POSIX; **prefer argv list in the schema**
- `cwd` fixed to workspace root (subdirs allowed only if still inside root and passed as a relative `cwd` arg that is jailed)
- New process group; kill on timeout
- Do not pass the user’s entire environment blindly if it contains obvious secrets — start with a minimal env (`PATH`, `HOME`, `LANG`, `VIRTUAL_ENV` if set) plus an allowlist. Document the allowlist.
- No network policy in this phase (hard). Do not implement iptables. Phase 06 policy will gate installers.

### ContextBundle

```text
root: str
language_hints: list[str]     # from extensions / lockfiles
tree_excerpt: str             # top levels + important files
notes: list[str]              # e.g. "ignored 12k paths"
approx_bytes: int
```

Never include denylisted file contents.

### CLI

`wecoder inspect` prints root, hints, tree excerpt, tool names. No model call.

## Files Expected To Be Created

```
wecoder/workspace/__init__.py
wecoder/workspace/workspace.py
wecoder/workspace/ignore.py
wecoder/workspace/secrets.py
wecoder/context/__init__.py
wecoder/context/packer.py
wecoder/tools/__init__.py
wecoder/tools/base.py
wecoder/tools/registry.py
wecoder/tools/fs.py
wecoder/tools/search.py
wecoder/tools/shell.py
wecoder/tools/errors.py
wecoder/safety/__init__.py
wecoder/safety/policy.py          # default policy; approval comes in Phase 06
wecoder/cli/inspect_cmd.py
tests/workspace/test_jail.py
tests/workspace/test_ignore.py
tests/tools/test_fs.py
tests/tools/test_search.py
tests/tools/test_shell.py
tests/context/test_packer.py
```

## Files Expected To Be Modified

- `wecoder/cli/app.py` — add `inspect`
- `wecoder/config/settings.py` — optional limits section keys if you wire caps to config
- `wecoder/errors.py` — only re-exports if needed
- `.gitignore` — ensure `.wecoder/` runtime dirs stay ignored
- `pyproject.toml` — `pathspec` if used

## Files That Must NOT Be Modified

- `LICENSE`
- Planning docs
- Model provider contracts (additive imports only if inspect wants to show configured model — allowed, do not change protocol)
- Do not create `wecoder/agent/`

## Dependencies

- Requires Phase 01.
- Phase 02 is not strictly required for tools, but should already be present in the intended sequence. Do not break it.
- No Phase 04 agent.

## Implementation Requirements

1. Jail tests are mandatory and must include: `../`, absolute paths outside root, symlink escape.
2. `edit_file` takes `path`, `old_text`, `new_text` and fails if `old_text` is not found exactly once (or N times if you add `replace_all: bool`, default false).
3. `write_file` creates parents inside the jail only.
4. Binary files: `read_file` refuses or returns a clear error; do not dump binary into context.
5. `search_text` skips ignored and denylisted files.
6. Tool schemas must be valid JSON Schema so Phase 04 can pass them to models.
7. Default policy denies denylisted reads/writes even if a future agent asks.

## Error Handling

```text
ToolError(WecoderError)
  PathEscapeError
  DeniedSecretError
  FileTooLargeError
  EditMismatchError
  CommandTimeoutError
  CommandFailedError     # non-zero exit still returns ToolResult.ok=False; do not raise unless the tool itself crashed
```

Non-zero command exit is a **result**, not an exception. The future agent needs the stderr.

## Security Requirements

- Jail + denylist + timeout as specified.
- Do not implement a tool that reads `/etc/passwd` or `$HOME` outside the workspace.
- Redact known secret patterns in `run_command` output if cheap (e.g. `AKIA[0-9A-Z]{16}`, `sk-` prefixes). Best-effort is acceptable; document it as best-effort.
- Prompt injection: treat file contents as data. Tools do not evaluate instructions found in files.
- No `eval` on tool arguments.

## Performance Requirements

- `inspect` on a large tree must not walk forever: cap walk (e.g. 5_000 files) and stop.
- Search must honor the match cap and not load huge files fully (skip over max read size).

## Cost Considerations

No model calls. Context caps exist so Phase 04 cannot dump a monorepo into a prompt by accident.

## Testing Requirements

- Jail escape cases (see above)
- Denylist read/write
- Ignore: a file in `node_modules` is not searched
- `edit_file` mismatch
- `run_command` timeout (a `python -c "import time; time.sleep(60)"` with a 1s timeout)
- `run_command` cwd cannot be `/`
- Packer stays under the byte budget on a generated wide tree
- Tool registry exports schemas for every built-in tool

## Acceptance Tests

1. `wecoder inspect` on a temp project prints tree and tool names, exit 0.
2. All security tests above pass.
3. No network required.
4. No `wecoder run` agent loop.

## Deliverables

- Workspace, ignore, denylist
- Tool system with six tools
- Context packer
- `inspect` command
- Security-focused tests

## Definition of Done

- Acceptance tests pass.
- Phase 04 can import registry + packer + workspace without adding new security primitives.
- No agent conversation code.

## Risks

- Shell tool with `shell=True` and string concatenation. **Forbidden.**
- Walking the user’s entire home because workspace defaulted wrong. Default workspace is cwd, and `inspect` must print the resolved root prominently.
- Implementing Git write tools “for convenience”.
- Adding a vector index.

## Explicitly Deferred Work

- Interactive approval (Phase 06)
- Git checkpoints (Phase 06)
- Agent tool-calling loop (Phase 04)
- Test runner (Phase 05)
- Network egress sandbox

## Handoff To Next Phase

Phase 04 will:

- Create an agent that selects tools from the registry
- Put `ContextBundle` into the system/user prompt
- Use FakeModel to emit tool calls

Do not pre-create `wecoder/agent/` in this phase.

---

## Implementation Prompt

```
You are implementing Phase 03 of WeCoder.AI and ONLY Phase 03.

Read first:
- docs/phases/PHASE-03.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-014, ADR-015, ADR-019)
- Inspect the repository. Phases 01 (and 02 in the intended sequence) should exist. If the package/CLI/settings are missing, stop and report.

Implement ONLY Workspace, Context, and the Tool System:
- Workspace path jail (including symlink escape tests)
- Ignore rules + secret denylist
- Tools: list_dir, read_file, write_file, edit_file, search_text, run_command
- ToolRegistry + JSON schemas + structured ToolResult
- Budgeted ContextPacker
- CLI `wecoder inspect`
- Default policy hooks (no interactive approval UI)

Do not implement: the coding agent loop, `wecoder run`, Git mutating APIs, model router, memory, vector DB, containers, MCP, extra collaboration modes.

Preserve existing CLI commands (additive only).
Do not modify LICENSE or planning documents.
Do not start Phase 04.

After implementation, run relevant tests and linters.
Report files created/modified, test results, and failures.
Stop.
```
