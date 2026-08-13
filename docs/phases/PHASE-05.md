# Phase 5 — Execution, Testing & Self-Repair

## Objective

Close the inner software loop: detect how to run tests (and, when cheap, how to run the project), execute those commands inside the existing jail, parse failures, and run a **bounded** repair cycle until tests pass or the budget is exhausted.

The user-facing promise becomes: not only “I edited files”, but “I tried to verify them”.

## Why This Phase Exists

Phase 04 may already run `pytest` if the model thinks to. That is opportunistic. This phase makes verification a product feature so later review agents and collaboration modes have a ground-truth signal (red/green) instead of prose confidence.

## Current State

After Phase 04 (MVP):

- Single agent can edit files and run arbitrary jailed commands
- No first-class test runner
- No structured failure objects
- No dedicated repair loop
- Fixture mini-app exists

## Target State

- A `TestRunner` detects and runs the primary test command for the workspace
- Failures are structured (`file`, `message`, `excerpt`) when parseable
- `wecoder run` (or `wecoder run --verify`) finishes with a verification block
- On failure, a repair loop invokes the same Developer agent with the failure attached, up to `max_repairs`
- CLI prints: tests command, exit code, pass/fail counts if known, repair attempts

## Scope

**In scope**

- Project execution hints (read-only detection)
- Test runner with detectors: **pytest/unittest** first; **Node `npm test` / `pnpm test`** only if a lockfile/`package.json` exists and detection is cheap
- Failure parsers for pytest output (required); JUnit XML optional
- Repair controller: `max_repairs` default 2
- CLI verification summary
- Fixture mini-app scenario: failing test that the FakeModel repair path can fix

**Out of scope**

- Coverage gates, mutation testing, performance labs
- Language matrix (Java, Go, Rust, Flutter, …)
- Human approval / Git (Phase 06)
- Security reviewer agent (Phase 11)
- Starting long-lived dev servers as a daemon (a short `python -m app --check` is ok if it exits)

## Architecture

```
AgentResult (from Phase 04 loop)
    → TestRunner.detect(workspace) → RunSpec | None
    → TestRunner.execute(RunSpec) → TestReport
    → if failed and repairs left:
          Agent.run(repair_task_from(TestReport))
          repeat
    → VerificationResult attached to final output
```

Detection is deterministic. Models do not choose the test command when a detector matches, unless the user passed `--test-cmd`.

## Components

| Component | Responsibility |
|-----------|----------------|
| `RunSpec` | argv, cwd, timeout, kind=`tests`\|`smoke` |
| `TestRunner` | detect + execute via the existing shell/jail (do not spawn an unconstrained subprocess module) |
| `TestReport` | ok, command, exit_code, counts, failures[], raw_excerpt |
| `RepairController` | bounded outer loop |
| Detectors | Python, optional Node |
| pytest parser | extract failing node ids and messages |

## Interfaces / Contracts

### Detection order

1. User `--test-cmd` if provided (still jailed; still argv/timeout)
2. `pytest` if `pytest.ini` / `pyproject.toml` `[tool.pytest]` / `tests/` + `requirements` suggest it; prefer `python -m pytest`
3. `python -m unittest` if tests look like unittest and pytest is absent
4. `npm test` / `pnpm test` if `package.json` has a `test` script
5. Else `TestReport` with `ok=None` / status `skipped` — do not invent `make test`

### TestReport

```text
status: "passed" | "failed" | "error" | "skipped"
command: list[str] | None
exit_code: int | None
passed: int | None
failed: int | None
failures: list[{name: str, message: str, file: str | None}]
excerpt: str                  # capped
```

### Settings additions

```toml
[verify]
max_repairs = 2
test_timeout_seconds = 60
```

### CLI

```text
wecoder run TASK [--verify | --no-verify]
wecoder test                 # run detection + tests only, no agent
```

Default for `run`: `--verify` on. Allow `--no-verify` for edit-only.

`wecoder test` must not call a model.

## Files Expected To Be Created

```
wecoder/verify/__init__.py
wecoder/verify/runner.py
wecoder/verify/detect.py
wecoder/verify/parse_pytest.py
wecoder/verify/repair.py
wecoder/cli/test_cmd.py
tests/verify/test_detect.py
tests/verify/test_parse_pytest.py
tests/verify/test_repair.py
# extend tests/fixtures/mini_app with a known-failing test scenario
```

## Files Expected To Be Modified

- `wecoder/agent/result.py` — attach `verification: TestReport | None` and `repairs_used: int`
- `wecoder/cli/run_cmd.py` — verify flag and print block
- `wecoder/config/settings.py` — `[verify]` keys
- Fixture mini-app — add a deterministic failing test used by FakeModel repair tests
- Help text — mention verification

## Files That Must NOT Be Modified

- `LICENSE`, planning docs
- Model protocol (unless a tiny additive field is unavoidable — avoid)
- Jail/denylist
- Do not add a second agent role

## Dependencies

- Requires Phase 04 `Agent`, `AgentResult`, tools, workspace
- Uses Phase 03 `run_command` or an equivalent jailed executor — **do not open a second, less-safe subprocess path**

## Implementation Requirements

1. Detection unit tests on temp projects (pytest layout, empty project → skipped, package.json with test script).
2. Parser unit tests with recorded pytest failure output (store a fixture text file).
3. Repair integration: FakeModel first writes wrong code (or starts from failing fixture), TestRunner fails, FakeModel then edits the correct implementation, tests pass. `repairs_used == 1`.
4. Repair budget: always-failing tests + FakeModel no-op → stop at `max_repairs`, status not `succeeded`.
5. `wecoder test` on fixture without model.
6. Timeouts use settings; hung tests cannot block forever.
7. Repair prompts include structured failures, not 2MB of raw log.

## Error Handling

- Detector exception → `skipped`/`error` with message, do not crash `run` if the edit itself succeeded; final status should reflect verification error honestly (`failed` or a distinct `verify_error` — pick one and document)
- Test process crash / timeout → `TestReport.status = error`
- Repair model failure → stop, show last TestReport

## Security Requirements

- User-supplied `--test-cmd` is still jailed and timed out
- Do not run tests as root or with extra env secrets
- Do not auto-install `pytest` / `npm install` if missing. Report `skipped` or `error` with “dependency missing; install it yourself” (install approval is Phase 06)

## Performance Requirements

- Detect must be a cheap filesystem look, not a model call
- Repair default 2 keeps token cost bounded
- Do not re-pack the entire repo from scratch more than once per repair if you can reuse the session messages (you should)

## Cost Considerations

Each repair is a full agent continuation. Default `max_repairs=2`. Do not fan out multiple models. Do not re-run detection via LLM.

## Testing Requirements

Listed under Implementation Requirements. All offline.

## Acceptance Tests

1. `wecoder test` on mini_app (green fixture) exits 0 without network.
2. FakeModel repair scenario goes red → edit → green.
3. Exhausted repairs stop.
4. Unknown project: `skipped`, no invented `rm -rf` test command.
5. Phase 04 edit-only still works with `--no-verify`.

## Deliverables

- TestRunner + detectors + pytest parser
- RepairController
- `wecoder test`
- Verification section on `wecoder run`
- Tests and fixture updates

## Definition of Done

- Acceptance tests pass
- No approval UI, no Git writes, no second agent
- Missing test tooling does not cause silent “success”

## Risks

- Letting the model invent `sudo apt-get install`. Forbidden; no auto-install.
- Parsing every test framework on earth. Only pytest required.
- Infinite repair by setting a high default. Keep 2.

## Explicitly Deferred Work

- Approval for installs (Phase 06)
- Coverage and quality reviewers (Phase 11)
- Multi-language runners (Phase 12)
- Dev-server watch mode

## Handoff To Next Phase

Phase 06 should run **before** dangerous repairs become habitual on real repos: wrap `wecoder run` with checkpoints so a failed repair can be rolled back. Keep `TestReport` stable so approval logs can include it.

---

## Implementation Prompt

```
You are implementing Phase 05 of WeCoder.AI and ONLY Phase 05.

Read first:
- docs/phases/PHASE-05.md
- docs/MVP.md (verification is post-MVP trust, do not redefine MVP)
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-020)

Inspect the repository. Phase 04 (wecoder run, Agent, AgentResult, tools, fixture mini_app) must exist. If not, stop and report.

Implement ONLY execution, testing, and self-repair:
- TestRunner with deterministic detectors (pytest/unittest required; Node npm test optional if cheap)
- pytest failure parser
- Bounded RepairController (default max_repairs=2) that continues the existing Developer agent
- `wecoder test` (no model) and `wecoder run --verify/--no-verify`
- Attach TestReport to AgentResult
- Offline tests: detect, parse, red-to-green FakeModel repair, repair budget, no auto-install

Do not implement: human approval UI, Git commits/rollback, Architect/multi-agent, router, memory, extra languages, package installation, containers.

Use the existing jailed command execution path. Do not create an unconstrained subprocess helper.
Preserve existing functionality. Do not modify LICENSE or planning docs.

After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not start Phase 06.
```
