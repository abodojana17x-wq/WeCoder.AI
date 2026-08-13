# Phase 1 — Foundation & Engineering Baseline

## Objective

Turn this repository from a license-and-README stub into an installable Python 3.11+ project with a real package (`wecoder`), a CLI entry point, typed configuration, structured logging, a small public error hierarchy, and a CI-ready test harness.

No model calls. No tools. No agent. After this phase a contributor can clone, install, run `wecoder --help`, and run `pytest`.

## Why This Phase Exists

Every later phase needs a place to land. Without a package, config schema, logger, and tests, Phase 02 will invent those ad hoc and Phase 04 will be untestable. This phase exists to make the repository honest engineering, not to implement the product vision.

## Current State

Implemented:

- `README.md` (incomplete vision; claims Beta / dual-agent / Python 3.9+)
- `LICENSE` (MIT)
- `.gitignore` (generic Python)

Missing: all application code, `pyproject.toml`, tests, CI, CLI, config.

## Target State

- `wecoder` is an importable package
- `wecoder` and `python -m wecoder` print help and a version
- Settings load from defaults, optional TOML files, and environment variables with a documented precedence
- Logs are structured enough to grep (timestamp, level, logger, message) and never print secrets
- `pytest` runs at least smoke tests for CLI and config
- Optional GitHub Actions workflow runs lint + tests on Python 3.11 and 3.12

## Scope

**In scope**

- Project metadata and package layout
- CLI skeleton (`--help`, `--version`, `init` that writes a default config, `status` that prints config source and python version)
- Settings object and config file format
- Logging setup
- Error types
- pytest, ruff, and a type checker
- Minimal CI
- A short `CONTRIBUTING.md` *only if needed* for how to run tests (prefer putting that in `pyproject` scripts / a tiny `docs` note rather than rewriting the README)

**Out of scope**

- Model providers
- Tools, workspace jail, agent loop
- README feature implementation
- Web UI
- Telemetry
- Changing the MIT license

## Architecture

```
CLI (typer or argparse)
  → Settings.load()
  → configure_logging(settings)
  → command handler
       → prints result or raises WecoderError
```

This phase introduces the **process boundary** of the product: one CLI process, in-process libraries, no services.

## Components

| Component | Responsibility |
|-----------|----------------|
| `wecoder` package | Public version, package root |
| CLI app | Parse argv, dispatch commands, map errors to exit codes |
| Settings | Immutable (or frozen) config object |
| Logging | One setup function used by CLI and tests |
| Errors | `WecoderError` and a few subclasses (`ConfigError`, later phases add more) |

## Interfaces / Contracts

### Settings (initial keys — do not invent a kitchen sink)

```toml
# .wecoder/config.toml  (project)
# ~/.wecoder/config.toml (user)

[project]
workspace = "."          # resolved later in Phase 03; store as string

[model]
provider = "ollama"      # unused until Phase 02; still defined now
model = "qwen2.5-coder"
base_url = ""            # empty = provider default
api_key_env = "OPENAI_API_KEY"

[limits]
max_turns = 20
max_tokens = 100000

[logging]
level = "INFO"
```

Precedence (highest last wins, document this in code):

1. Built-in defaults
2. User file `~/.wecoder/config.toml` if present
3. Project file `<cwd>/.wecoder/config.toml` if present
4. Environment variables with prefix `WECODER_` (for example `WECODER_MODEL_PROVIDER`, `WECODER_LOGGING_LEVEL`)
5. CLI flags on commands that need them (Phase 01: `--verbose` is enough)

`Settings` must expose a `redacted()` view for printing (API-key-like fields become `***` even if added later).

### CLI exit codes

| Code | Meaning |
|-----:|---------|
| 0 | Success |
| 1 | Usage / config error |
| 2 | Unexpected error |

Later phases may add codes; do not reuse 0/1/2 differently.

### Errors

```text
WecoderError
  ConfigError
  # later: ModelError, ToolError, PolicyError, GitError, BudgetExceeded
```

CLI catches `WecoderError` → stderr message + exit 1. Unknown exceptions → log traceback at DEBUG, stderr “internal error”, exit 2.

## Files Expected To Be Created

```
pyproject.toml
wecoder/__init__.py
wecoder/__main__.py
wecoder/cli/__init__.py
wecoder/cli/app.py
wecoder/config/__init__.py
wecoder/config/settings.py
wecoder/observability/__init__.py
wecoder/observability/logging.py
wecoder/errors.py
tests/conftest.py
tests/test_cli.py
tests/test_config.py
.github/workflows/ci.yml
```

Optional: `wecoder/py.typed`.

## Files Expected To Be Modified

- `.gitignore` — only if product paths should be added (recommend ignoring `.wecoder/sessions/`, `.wecoder/logs/`, and local override configs). Do not replace the file.
- `README.md` — **only** if required to state install/dev commands without claiming unimplemented features. Prefer not rewriting the vision. Do **not** keep or add a Beta badge that implies a working product if you touch badges.

## Files That Must NOT Be Modified

- `LICENSE`
- `docs/MASTER_PLAN.md` and other planning documents, except a one-line status note is unnecessary and should not be added
- No deletion of existing files

## Dependencies

- None on other implementation phases.
- External libraries: keep the Phase 01 runtime dependency list short. Recommended: `typer` (or stdlib `argparse` if you want zero deps — either is acceptable; prefer typer if it stays a direct, pinned dependency), `tomli` only if you must support a world without `tomllib` (you should not; 3.11+ has `tomllib`).
- Dev: `pytest`, `ruff`, `mypy` or `pyright`.

Do not add `openai`, `langchain`, `httpx` (unless you truly need it — you do not), Docker, or a web framework.

## Implementation Requirements

1. `pyproject.toml` defines package `wecoder`, script `wecoder = wecoder.cli.app:main` (or equivalent), `requires-python = ">=3.11"`, and pytest/ruff config.
2. Version is a single source (`wecoder.__version__`), e.g. `0.1.0`.
3. `wecoder init` creates `.wecoder/config.toml` in the current directory if missing, refuses to overwrite without `--force`, and does not write secrets.
4. `wecoder status` prints version, python version, config files found, provider/model *as configured* (even though unused), and logging level. No network.
5. Logging defaults to stderr. No log file is required in this phase.
6. Type hints on public functions. Ruff clean on the package and tests.
7. Do not implement `wecoder run`. A stub that says “not implemented until Phase 04” is acceptable but not required; omitting the command is cleaner.

## Error Handling

- Missing/invalid TOML → `ConfigError` with file path and reason.
- `init` when file exists without `--force` → `ConfigError`, exit 1.
- Never swallow exceptions in CLI without an exit code.

## Security Requirements

- Do not log environment values that look like keys (`*KEY*`, `*TOKEN*`, `*SECRET*`).
- Do not read `.env` into settings in this phase.
- `init` must not create world-writable config in a careless way; default file mode should be user-readable.
- No collection of user data.

## Performance Requirements

Irrelevant beyond “help and status return instantly”. Do not start threads or daemons.

## Cost Considerations

Zero model cost. Do not add paid services. CI should use GitHub-hosted free runners only.

## Testing Requirements

- `tests/test_cli.py`: `--help` exits 0; `--version` prints the package version; `status` exits 0.
- `tests/test_config.py`: defaults load without files; a temp TOML overrides defaults; env `WECODER_LOGGING_LEVEL=DEBUG` overrides file; `redacted()` does not contain a planted fake secret if you add a dummy field in the test.
- Tests must not write into the real repo’s `.wecoder/` or the user’s home. Use `tmp_path` and monkeypatch home/cwd.

## Acceptance Tests

1. Fresh venv, `pip install -e ".[dev]"`, `wecoder --help` works.
2. `pytest` is green offline.
3. `ruff check` is green.
4. Type checker is configured and does not explode on the package (zero or documented baseline).
5. CI file exists and invokes the same commands.

## Deliverables

- Installable package and CLI skeleton
- Config + logging + errors
- Test and lint baseline
- CI workflow

## Definition of Done

- All acceptance tests pass.
- No model/tool/agent code exists.
- Planning docs untouched.
- A stranger can follow `pyproject.toml` / CI to run tests without asking you.

## Risks

- Overbuilding a plugin framework “for later”. **Do not.**
- Pulling in an agent framework because “we will need it”. **Do not.**
- Rewriting the README into a fake product. **Do not.**
- Supporting Python 3.9 to match the badge. **Do not** (ADR-003).

## Explicitly Deferred Work

- Everything in Phases 02–12
- README marketing rewrite (unless the Beta badge is corrected)
- Session persistence, TUI, Docker

## Handoff To Next Phase

Phase 02 will add `wecoder/models/` and a `wecoder models` command. It must use `Settings` for provider/model/base_url/api_key_env and must not invent a parallel config system. It must raise subclasses of `WecoderError`.

---

## Implementation Prompt

```
You are implementing Phase 01 of WeCoder.AI and ONLY Phase 01.

Read first:
- docs/phases/PHASE-01.md (this phase is the spec)
- docs/MASTER_PLAN.md (context, do not implement later phases)
- docs/ARCHITECTURAL_DECISIONS.md (ADR-002, ADR-003, ADR-004, ADR-018)

Then inspect the repository as it actually exists. Do not assume features from the README exist.

Implement ONLY Phase 01: Foundation & Engineering Baseline.

Requirements:
- Create an installable Python 3.11+ package named wecoder with CLI entry points `wecoder` and `python -m wecoder`.
- Add typed settings (TOML + WECODER_* env + defaults), structured logging, and WecoderError.
- Commands: --help, --version, init, status. Do not implement run, tools, models, or agents.
- Add pytest, ruff, type checking, and a minimal GitHub Actions CI workflow.
- Tests must use temporary directories; do not write into the user’s home or this repo’s real config.
- Preserve LICENSE. Do not delete existing files. Do not implement later phases “while you are here”.
- Do not install or import openai, anthropic, langchain, docker, or web frameworks.
- Do not rewrite the README into a finished-product claim. You may add a brief honest Development section if necessary.

After implementation:
- Run the relevant tests and linters.
- Report: files created, files modified, test results, any failures.
- Stop. Do not start Phase 02.
```
