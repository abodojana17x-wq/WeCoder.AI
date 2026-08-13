# Phase 7 — Dual-Agent Leader Mode

## Objective

Implement the first real collaboration mode, matching the README’s Architect + Developer idea: a **Leader** (Architect) that plans and reviews, and a **Developer** that uses tools. The user sees one coordinated run, not a committee.

This is **Leader mode only**.

## Why This Phase Exists

The product vision is a team. The README’s dual-agent critique is the smallest team that can improve quality. It waits until one agent works (Phase 04), verification exists (Phase 05), and safety/git exist (Phase 06) so two model voices cannot skip the jail or destroy history (ADR-010, ADR-011).

## Current State

After Phase 06:

- One Developer agent, verify/repair, policy, checkpoints
- No role objects, no orchestrator, no Architect prompt

## Target State

- `wecoder run --mode leader` (or `wecoder run` with config `orchestration.mode = leader`)
- Architect produces a plan (and optional file-level approach) **without** a shell by default
- Developer implements against that plan with tools
- Architect reviews the diff / test report and either accepts or requests a bounded revision
- Same Policy, same checkpoint, same TestRunner
- Single-agent mode remains the default unless config says otherwise (do not surprise users with 2× tokens)

## Scope

**In scope**

- `RoleSpec` data: name, prompt, tool allowlist, optional model ref
- Two hardcoded roles: `architect`, `developer`
- `LeaderOrchestrator` state machine
- Architect tool allowlist: read-only tools (`list_dir`, `read_file`, `search_text`) — **no** `run_command`, `write_file`, `edit_file`
- Bounded review rounds (`max_reviews`, default 1)
- CLI/config to select `single` vs `leader`
- Tests with two FakeModels or one FakeModel that switches by role

**Out of scope**

- Together, Workers, Consensus, Debate (Phase 10)
- Dynamic role generation (Phase 10)
- Router picking different vendors per role (Phase 09) — a *manual* per-role model in config is allowed if it is just `RoleSpec.model_ref` using the existing registry
- Memory (Phase 11)

## Architecture

```
mode=single → existing Agent (Phase 04) unchanged

mode=leader
  checkpoint
  Architect.plan(task, context) → Plan
  Developer.run(task + plan)    → AgentResult
  optional verify (Phase 05)
  Architect.review(diff, TestReport) → accept | request_changes
  if request_changes and reviews left: Developer.run(feedback)
  present combined result
```

User interface remains `wecoder run`. Show which role is speaking.

## Components

| Component | Responsibility |
|-----------|----------------|
| `RoleSpec` | Data, not a class hierarchy explosion |
| `LeaderOrchestrator` | Sequence, budgets, stop |
| Architect prompts | Plan + review |
| Combined result | plan, implementation summary, review, verification, usage **sum** |

## Interfaces / Contracts

### Modes

```text
single | leader
```

Settings:

```toml
[orchestration]
mode = "single"          # default
max_reviews = 1

[roles.architect]
provider = ""            # empty = use default model
model = ""

[roles.developer]
provider = ""
model = ""
```

### Plan

```text
goal: str
steps: list[str]
constraints: list[str]
files_likely: list[str]
```

### Review

```text
verdict: "accept" | "request_changes" | "block"
comments: str
must_fix: list[str]
```

`block` is for “this change is dangerous/wrong and should not continue”. It does not bypass Policy.

### Budgets

- Shared session token budget still applies (sum both roles)
- `max_reviews` default 1 (so worst case: plan + implement + review + one fix + optional tests)
- Architect failures should not leave the workspace half-edited without a result; Developer work already checkpointed

## Files Expected To Be Created

```
wecoder/orchestration/__init__.py
wecoder/orchestration/modes.py
wecoder/orchestration/leader.py
wecoder/orchestration/roles.py
wecoder/agent/prompts/architect.md
tests/orchestration/test_leader.py
tests/orchestration/test_role_policy.py
```

## Files Expected To Be Modified

- `wecoder/cli/run_cmd.py` — `--mode`, role logs
- `wecoder/config/settings.py` — `[orchestration]`, optional `[roles.*]`
- `wecoder/agent/result.py` — `mode`, `plan`, `review`, per-role usage if easy
- Help text

## Files That Must NOT Be Modified

- `LICENSE`, planning docs
- Policy defaults that would give Architect a shell
- Git checkpoint semantics
- Do not add other modes beyond a stub enum value that errors “not implemented”

## Dependencies

- Phase 04 Agent (Developer)
- Phase 05 TestReport (review input)
- Phase 06 Policy + checkpoint (must wrap the whole leader run)

## Implementation Requirements

1. Default mode remains `single`. Tests assert that existing `wecoder run` path is unchanged when mode is single.
2. Architect cannot call write/shell tools even if the model emits those tool names — registry is filtered by allowlist.
3. Leader integration with FakeModels: plan mentions a file, developer writes it, review accepts.
4. Review `request_changes` triggers one more developer turn, then stops even if review still unhappy.
5. Usage printed is the **sum**.
6. Checkpoint occurs once at the start of the leader run, not per role (rollback still works).
7. Do not implement a generic graph engine.

## Error Handling

- Architect plan failure → do not start developer; status `failed`; no silent fallback to single unless `--fallback-single` is explicitly passed (optional flag; default off)
- Architect review failure after developer worked → return implementation result with `review` error; do not delete work
- Policy reject during developer → same as Phase 06

## Security Requirements

- Shared Policy object (ADR-025)
- Architect read-only
- Review text is not executed as commands
- Prompt injection in the repo cannot grant Architect write tools

## Performance Requirements

- Do not have Architect and Developer talk for unbounded turns
- Do not send the full conversation of one role into the other except: plan, diffstat/diff excerpt, test report, review comments

## Cost Considerations

Leader mode is at least 2–4× single mode. Therefore:

- It is **opt-in**
- `max_reviews` is 1
- CLI should print an estimated “this will use multiple model calls” line at start

## Testing Requirements

- Allowlist enforcement
- Single mode regression
- Fake Leader happy path
- Review loop bound
- Checkpoint still created (reuse Phase 06 git fixture)

## Acceptance Tests

1. `mode=single` behavior unchanged.
2. `mode=leader` FakeModel path produces plan + file + review.
3. Architect write attempt is denied.
4. `max_reviews=0` means implement + optional review without extra fix loop (document: 0 = no revision round).
5. pytest offline green.

## Deliverables

- RoleSpec + LeaderOrchestrator
- Architect prompts
- CLI/config mode switch
- Tests

## Definition of Done

- Acceptance tests pass
- README dual-agent claim is *now* implementable; do not rewrite README unless you also remove false Beta claims — prefer leaving README to a docs hygiene task
- No other collaboration modes

## Risks

- Building a mode plugin framework for four future modes. **Only Leader.**
- Architect that “helps” by editing. **Allowlist.**
- Making leader the default and surprising users with cost.

## Explicitly Deferred Work

- Phase 10 modes and dynamic teams
- Phase 09 automatic model assignment
- Specialist security reviewer (Phase 11) — Architect review is general, not a security product

## Handoff To Next Phase

Phase 08 will persist sessions that now include multiple roles and summed usage. Keep result fields serializable. Phase 09 may set `RoleSpec.model_ref` automatically; keep that field.

---

## Implementation Prompt

```
You are implementing Phase 07 of WeCoder.AI and ONLY Phase 07.

Read first:
- docs/phases/PHASE-07.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-010, ADR-011, ADR-012, ADR-025)
- README.md (vision of Architect + Developer — implement Leader mode only)

Inspect the repository. Phases 04–06 must exist (agent, verify, policy, git checkpoints). If not, stop and report.

Implement ONLY Dual-Agent Leader Mode:
- RoleSpec data objects
- Hardcoded roles: architect (read-only tools) and developer (existing agent)
- LeaderOrchestrator: plan → implement → optional verify → review → at most one revision
- Config/CLI --mode single|leader, default single
- Shared Policy and a single pre-run checkpoint
- FakeModel tests for happy path, allowlist, review bound, single-mode regression

Do not implement: Together, Workers, Consensus, Debate, dynamic teams, model router, memory, new vendors, web UI.

Do not give the Architect a shell or write tools.
Do not make leader mode the default.
Preserve existing functionality.
Do not modify LICENSE or planning documents.

After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not start Phase 08.
```
