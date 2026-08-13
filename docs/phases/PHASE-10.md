# Phase 10 — Collaboration Modes & Dynamic Teams

## Objective

Extend Leader mode into the remaining collaboration strategies — **Workers**, **Together**, **Consensus**, and **Debate** — and add **dynamic team composition** that builds a small `RoleSpec` list from the task type, all behind explicit opt-in and strict budgets.

## Why This Phase Exists

This is the long-term product identity: an AI software team. It is also the easiest phase to bankrupt a user or produce theater. It exists only after Leader mode is real (Phase 07), sessions/cost exist (Phase 08), and routing can assign cheaper models (Phase 09) (ADR-010, ADR-012).

## Current State

After Phase 09:

- `single` and `leader` modes
- RoleSpec data shape exists
- Router + usage ledger exist
- Policy and git wrap every run

## Target State

- `orchestration.mode` accepts: `single`, `leader`, `workers`, `together`, `consensus`, `debate`
- Each mode has a written state machine, a budget, and tests with FakeModels
- Dynamic teams: optional `team = auto` generates 2–4 roles from a **template table**, not free-form LLM org charts with 12 people
- User can still pin a static team file
- Default remains `single`

## Scope

**In scope**

- Four mode orchestrators (+ keep Leader)
- Shared `Budget` (max roles, max parallel, max tokens, max wall clock)
- Workers: decompose into independent file/task units; sequential is required, parallel optional and default off
- Together: two models alternate on the **same** plan document for a bounded number of turns, then Developer implements **once**
- Consensus: two independent Developer attempts on **isolated worktrees or copies** if and only if Git worktrees are feasible; otherwise sequential copies in temp dirs; a Judge (read-only) picks one; **never merge blindly**
- Debate: Architect-like critic must produce dissenting objections before implementation; cap 2 rounds
- Dynamic team templates: `web_api`, `bugfix`, `cli`, `unknown` → fixed role lists
- CLI `--mode`, `--team auto|path`

**Out of scope**

- Unlimited parallelism
- Game-studio 8-role fantasy as default
- Memory of past teams (Phase 11)
- Benchmark scoring rubric beyond Judge prompt (Phase 12)
- Marketplace of community teams

## Architecture

```
ModeController
  → enforce Budget
  → dispatch to mode orchestrator
  → each role: Agent(role) with tool allowlist + ModelRef (router or pin)
  → single Policy, one pre-run checkpoint (consensus may add per-candidate checkouts)
```

### Mode sketches (normative)

**Workers**

1. Leader/architect-like decomposer (read-only) outputs ≤ N tasks with disjoint file hints
2. Developer runs tasks sequentially
3. Stop if overlap detected (same file claimed twice) — do not lock-server; just refuse and ask user or serialize

**Together**

1. Two reasoners (no write tools) produce a shared plan for ≤ 2 rounds
2. One Developer implements
3. Optional Phase 05 verify

**Consensus**

1. Two isolated Developer runs (budget!)
2. Judge reads diffs + test reports, picks winner or `neither`
3. Discard loser tree; keep winner as the workspace result (or apply winner patch onto original checkpoint)

**Debate**

1. Proposer plan
2. Opponent must list objections (empty objections are a failure — force at least one considered risk or “no objection: X”)
3. Proposer revises once
4. Developer implements the revised plan

**Dynamic team**

```text
bugfix     → developer + tester(read+shell tests only)
web_api    → architect + developer
cli        → developer
unknown    → architect + developer   # i.e. leader
```

No “Network Engineer” unless a user-supplied team file says so.

## Components

| Component | Responsibility |
|-----------|----------------|
| `ModeController` | dispatch + budget |
| Mode orchestrators | one module per mode is fine |
| `TeamSpec` | list of RoleSpec |
| `TeamTemplates` | deterministic |
| Isolation helper | temp copy / git worktree for consensus |

## Interfaces / Contracts

```toml
[orchestration]
mode = "single"
max_roles = 4
max_mode_rounds = 2
allow_parallel = false

[team]
source = "off"           # off | auto | file
file = ""
```

CLI:

```text
wecoder run TASK --mode workers
wecoder team explain "TASK"     # prints which template would be used, no model required for templates
```

`team explain` should be heuristic (keywords) so it is free.

## Files Expected To Be Created

```
wecoder/orchestration/budget.py
wecoder/orchestration/workers.py
wecoder/orchestration/together.py
wecoder/orchestration/consensus.py
wecoder/orchestration/debate.py
wecoder/orchestration/team.py
wecoder/orchestration/templates.py
tests/orchestration/test_workers.py
tests/orchestration/test_together.py
tests/orchestration/test_consensus.py
tests/orchestration/test_debate.py
tests/orchestration/test_templates.py
```

## Files Expected To Be Modified

- `wecoder/orchestration/modes.py`
- CLI run + help (cost warning when mode ≠ single)
- Settings
- Session traces — record mode and role names (Phase 08 events)

## Files That Must NOT Be Modified

- `LICENSE`, planning docs
- Policy defaults (no mode-specific privilege escalation)
- Jail
- Do not remove Leader or Single

## Dependencies

- Phase 07 RoleSpec + Leader
- Phase 06 isolation/checkpoints
- Phase 08 traces (emit events)
- Phase 09 router optional

## Implementation Requirements

1. Each mode has a FakeModel test that finishes within budget.
2. Consensus isolation test: loser writes do not remain if winner is chosen (workspace matches winner or original+winner).
3. Overlapping worker file claims → safe stop.
4. Debate test asserts opponent output is fed to proposer.
5. `max_roles` exceeded by a user team file → ConfigError, no run.
6. Templates never emit more than 4 roles.
7. Parallelism default off; if you implement parallel workers, they must not share a write workspace.
8. Cost warning printed for non-single modes.

## Error Handling

- Mode not implemented (should not happen if you ship all four) → ConfigError
- Isolation failure in consensus → abort, rollback to pre-run checkpoint
- Judge says `neither` → rollback, status `blocked`

## Security Requirements

- Shared Policy
- Isolated trees cannot write to the original root until a winner is applied
- Dynamic team cannot request `run_command` for a role that template marked read-only
- User team files are data: schema-validated, not `eval`’d Python

## Performance Requirements

- Sequential default
- Hard caps on rounds and roles
- Consensus is expensive: document it; consider requiring `--yes` or an extra `--allow-expensive` flag. **Require `--allow-expensive` for consensus and debate.**

## Cost Considerations

This phase can destroy the commercial story if defaults are wrong.

- Default mode still `single`
- Consensus/Debate require `--allow-expensive`
- Workers default sequential, max 3 tasks
- Together max 2 reasoners × 2 rounds

## Testing Requirements

Per-mode FakeModel tests + template tests + isolation test. Offline.

## Acceptance Tests

1. `wecoder team explain` returns a template without network
2. Each mode’s unit/integration test passes
3. `--allow-expensive` required for consensus/debate
4. Policy still denies secret writes inside a worker
5. Single and leader regression tests pass

## Deliverables

- Four modes + templates + budgets
- Isolation for consensus
- CLI flags and warnings
- Tests

## Definition of Done

- Users can opt into a team-shaped run with known cost bounds
- No 8-agent default
- Loser consensus work cannot corrupt the repo

## Risks

- Theater teams (many roles, no tools)
- Parallel writes on one tree
- Making debate the README default

## Explicitly Deferred Work

- Memory of team decisions (Phase 11)
- Numeric multi-metric benchmarking (Phase 12)
- User marketplace

## Handoff To Next Phase

Phase 11 specialists are just more RoleSpecs (security reviewer read-only). Reuse templates rather than inventing a third team system. Phase 12 benchmarking can reuse consensus isolation.

---

## Implementation Prompt

```
You are implementing Phase 10 of WeCoder.AI and ONLY Phase 10.

Read first:
- docs/phases/PHASE-10.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-010, ADR-011, ADR-012)
- docs/COMMERCIAL_STRATEGY.md (do not multiply models by default)

Inspect the repository. Phase 07 Leader mode and Phase 06 git/policy must exist. If not, stop and report.

Implement ONLY collaboration modes and dynamic team templates:
- workers, together, consensus, debate (keep single + leader)
- Budgets: max roles, max rounds; sequential default
- Deterministic templates (web_api, bugfix, cli, unknown)
- Consensus isolation; judge picks winner or neither
- --allow-expensive required for consensus and debate
- Schema-validated user team files
- FakeModel tests for each mode; no live network

Do not implement: global memory, specialist security product, numeric benchmarking, plugin marketplace, 8-role game-studio generator, privilege escalation per role.

Do not change the default mode from single.
Preserve existing functionality.
Do not modify LICENSE or planning documents.

After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not start Phase 11.
```
