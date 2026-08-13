# Phase 6 — Safety, Human Approval & Git Intelligence

## Objective

Make WeCoder safe enough for a real repository: a policy engine that classifies tool calls, an interactive **Approve / Reject / Review** flow for dangerous actions, and local Git checkpoints so every mutating run can be inspected and rolled back.

After this phase, two agents (Phase 07) are allowed to share a shell.

## Why This Phase Exists

Phases 03–05 already execute model-proposed commands. That is local RCE with a friendlier prompt. Multi-agent (Phase 07) multiplies the chance of a bad command. Recoverability and human authority must exist first (ADR-016, ADR-017, ADR-025).

## Current State

After Phase 05:

- Agent + tools + test/repair exist
- Default policy is jail + denylist + timeout
- No interactive approval
- No product-owned Git checkpoints
- CLI help still tells users to use their own Git hygiene

## Target State

- `Policy` classifies each tool call: `allow`, `deny`, `ask`
- Terminal approval prompt: Approve / Reject / Review (show args or diff)
- `wecoder run` creates a checkpoint **before** mutating tools (and optionally after)
- `wecoder checkpoint`, `wecoder diff`, `wecoder rollback` work on those checkpoints
- Audit log of decisions for the in-memory (and later persistent) session
- Non-interactive `--yes` / `--deny-dangerous` flags exist and are explicit

## Scope

**In scope**

- Policy rules for: destructive fs, writes to config/secret-like paths, dependency installs, remote-pipe patterns, broad `chmod`/`chown`, git mutating commands not issued by our Git tool
- Interactive TTY approval
- Git wrapper: detect repo, create stash or WeCoder branch/ref checkpoints, show diff, reset to checkpoint
- CLI for checkpoint/diff/rollback
- Refuse to run mutating sessions outside a Git repo unless `--allow-no-git` is set
- Tests with a temp git repo

**Out of scope**

- GitHub/GitLab PR bots, OAuth apps
- Enterprise SSO
- Container sandbox
- Multi-agent (Phase 07)
- Persistent audit server
- Silent “YOLO” default

## Architecture

```
Tool.execute request
  → Policy.classify(tool, args, workspace) → allow | deny | ask
  → if ask: Approver.prompt() → approve | reject | review
  → if approve: execute
  → if reject: ToolResult.ok=False, error_type=UserRejected

wecoder run
  → Git.ensure_repo or --allow-no-git
  → Git.create_checkpoint("pre-run")
  → Agent.run (policy-wrapped tools)
  → Git.create_checkpoint("post-run") optional
  → print rollback hint
```

Checkpoints must work even if the user rejects mid-run.

## Components

| Component | Responsibility |
|-----------|----------------|
| `Policy` | Deterministic classification |
| `Approver` | TTY UI; programmable in tests |
| `GitService` | status, checkpoint, diff, rollback |
| `Checkpoint` | id, ref, message, timestamp |
| CLI | `checkpoint`, `diff`, `rollback` |
| Audit events | in-session list |

## Interfaces / Contracts

### Policy decisions

```text
Decision = "allow" | "deny" | "ask"
PolicyResult(decision, reason, rule_id)
```

Default rules (normative):

| Pattern | Decision |
|---------|----------|
| `list_dir`, `read_file` (non-secret), `search_text` | allow |
| `write_file` / `edit_file` on ordinary source | allow (checkpoint already taken) |
| write/edit on denylisted secret paths | deny |
| delete / recursive rm / wipe (`run_command` argv matching) | ask |
| `pip install`, `npm install`, `yarn`, `pnpm add`, `poetry add`, `curl * \| sh` | ask |
| `git reset --hard`, `git checkout .`, `git push --force` issued via shell | ask or deny (prefer deny for force-push; ask for hard reset) |
| path escape | deny (already) |

Exact regexes are an implementation detail; tests lock behavior.

### Approver

In a TTY:

```text
Dangerous action: run_command
argv: ["pip", "install", "requests"]
Reason: dependency_install (rule install.pip)

[a]pprove  [r]eject  [v]iew details
```

Non-TTY default: **deny** dangerous actions unless `--yes` was passed. Never imply yes from a pipe.

Flags:

```text
--yes                 auto-approve "ask" (still cannot override deny)
--deny-dangerous      auto-reject "ask"
--allow-no-git        permit mutating run without a repo
```

### Git checkpoints

Prefer one of these, documented clearly:

**Recommended:** `git stash create` / a ref under `refs/wecoder/checkpoints/<id>` pointing at a commit created with `git write-tree` + `commit-tree` **without** moving `HEAD` if possible, so we do not disturb the user’s branch. If that is too complex, a dedicated branch `wecoder/checkpoints/<id>` is acceptable.

Minimum viable: create a commit on a branch `wecoder/work` only if the user opts in later. For this phase, **do not rewrite the user’s current branch** unless they pass `--commit` (optional, default off).

Rollback:

- Restores tracked files to checkpoint tree
- Must warn about untracked files WeCoder created (delete only those listed in `changed_files` if rolling back a session)

If Git is unavailable: error, unless `--allow-no-git`.

### CLI

```text
wecoder checkpoint          # create named checkpoint now
wecoder diff [ID]           # vs checkpoint or vs start of last run
wecoder rollback [ID]       # restore; ask for confirmation unless --yes
```

## Files Expected To Be Created

```
wecoder/safety/rules.py
wecoder/safety/approver.py
wecoder/gittool/__init__.py
wecoder/gittool/service.py
wecoder/gittool/checkpoint.py
wecoder/cli/git_cmd.py
tests/safety/test_policy.py
tests/safety/test_approver.py
tests/gittool/test_checkpoint.py
```

(Phase 03 already has `wecoder/safety/policy.py` — extend it, do not create a second policy system.)

## Files Expected To Be Modified

- `wecoder/safety/policy.py`
- `wecoder/tools/registry.py` or execute path — policy wrap
- `wecoder/cli/run_cmd.py` — checkpoint + flags
- `wecoder/agent/session.py` / result — `checkpoint_id`, `audit[]`
- Settings — `[safety]` and `[git]`
- Help text — remove “bring your own git only” as the whole story; keep “review diffs”

## Files That Must NOT Be Modified

- `LICENSE`, planning docs
- Model adapters except if needed to thread a flag (avoid)
- Do not add Architect
- Do not force-push or delete `.git`

## Dependencies

- Requires Phases 03–05 (tools, agent, verify)
- System `git` binary must be present for Git tests; skip Git tests with a clear marker if `git` is missing (CI images should have git)

## Implementation Requirements

1. Policy unit tests for each default rule family.
2. Approver is injectable: tests never block on stdin.
3. Temp git repo: run a FakeModel mutating session → checkpoint exists → rollback restores original file content.
4. Non-TTY + no `--yes` + install command → rejected, file system unchanged for that command.
5. `--yes` cannot write `.env` (deny stays deny).
6. `rollback` confirmation in TTY; `--yes` for scripts.
7. Never `git push`.
8. If workspace is not a git repo and `--allow-no-git` is absent, `wecoder run` refuses before model calls.

## Error Handling

```text
PolicyError(WecoderError)
GitError(WecoderError)
  NotAGitRepository
  GitUnavailable
  CheckpointMissing
  RollbackFailed
```

Rollback failure must say the workspace may be dirty and not pretend success.

## Security Requirements

- Default-deny in non-interactive dangerous cases
- No force-push, no `git clean -fdx` as a built-in
- Checkpoints must not include ignored secret files that were never meant to be committed; use Git’s own ignore. Do not `git add -f .env`
- Approval logs must not include API keys
- Policy shared object — one instance per run (ADR-025)

## Performance Requirements

- Checkpoint should be seconds, not a full history rewrite
- Do not `git add -A` the entire monorepo if only a few files changed for *post* checkpoints; pre-run checkpoint is “current tree”

## Cost Considerations

No extra model calls. Approval is human time, which is intended.

## Testing Requirements

See Implementation Requirements. Include a test that repair loop (Phase 05) still works with policy wrapping and auto-approver in tests.

## Acceptance Tests

1. Policy matrix tests pass.
2. Checkpoint + rollback integration passes.
3. Non-TTY dangerous command denied.
4. `wecoder diff` shows the FakeModel edit.
5. Existing `wecoder test` still works.

## Deliverables

- Policy engine + TTY approver
- Git checkpoints, diff, rollback
- CLI flags and commands
- Audit list on the session/result
- Tests on temp repos

## Definition of Done

- Acceptance tests pass
- Help text honestly describes approval and git requirements
- No GitHub integration
- No second agent

## Risks

- Implementing checkpoint as `git commit` on `main`. **Do not** surprise-commit user branches.
- Auto-approving because tests were annoying. Tests use a FakeApprover; production defaults stay safe.
- Rolling back with `git reset --hard` wiping user unrelated work. Scope rollback to the workspace and warn; prefer restoring the checkpoint tree explicitly.

## Explicitly Deferred Work

- Dual-agent (Phase 07)
- Hosted PR flow
- Persistent session audit DB (Phase 08 may store these events)
- Container isolation (Phase 12)

## Handoff To Next Phase

Phase 07 must pass the same `Policy` and create the same pre-run checkpoint. Architect does not get extra tools. Leader mode must not add a silent `--yes`.

---

## Implementation Prompt

```
You are implementing Phase 06 of WeCoder.AI and ONLY Phase 06.

Read first:
- docs/phases/PHASE-06.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-016, ADR-017, ADR-025)
- docs/PRODUCT_NORTH_STAR.md (human authority, recoverability)

Inspect the repository. Phases 03–05 must exist (tools, agent, verify). If not, stop and report.

Implement ONLY safety, human approval, and local Git intelligence:
- Extend the existing Policy (do not create a second policy system)
- Classify tool calls allow/deny/ask with the specified default rules
- Approver with Approve / Reject / Review; injectable for tests
- Non-TTY defaults to deny "ask" unless --yes; --yes cannot override deny
- Git checkpoints that do not surprise-commit the user’s current branch
- CLI: checkpoint, diff, rollback; run creates a pre-run checkpoint
- Refuse mutating runs outside a git repo unless --allow-no-git
- Never git push

Do not implement: Architect/multi-agent, GitHub apps, router, memory, containers, SaaS audit log.

Preserve existing functionality (agent, test runner) with policy wrapping.
Do not modify LICENSE or planning documents.

After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not start Phase 07.
```
