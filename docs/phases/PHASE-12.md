# Phase 12 — Benchmarking, Extensibility & Commercial Foundations

## Objective

Add three *late* capabilities, each small and optional:

1. **Solution benchmarking** — generate a bounded number of candidate solutions, score them with an explicit rubric, pick or present a winner.
2. **Extensibility** — a documented plugin surface for language/runtime detectors and tools so Python-first WeCoder can grow without a rewrite.
3. **Commercial foundations** — packaging, opt-in telemetry, usage export that a future paid service could read — **not** a SaaS control plane and not billing.

## Why This Phase Exists

Benchmarking is valuable only when the product can already produce *one* good solution and isolate worktrees (Phases 04–10). Extensibility is how we refuse the “support every language in MVP” trap (ADR-020). Commercial hooks belong last so we do not invent Stripe in Phase 01 (ADR-022). This phase is FUTURE work and may be implemented as three sequential PRs inside the phase; it is still one planning unit.

## Current State

After Phase 11:

- Full local coding team loop exists
- Consensus isolation and specialist `Finding`s exist
- No rubric scorer, no plugin API, no packaging/telemetry

## Target State

- `wecoder bench TASK --candidates 2` (cap 3) requires `--allow-expensive`
- Rubric scores: correctness (tests), quality/security findings, complexity proxy, estimated cost
- Winner applied like consensus; others discarded
- `wecoder plugins list` shows detectors/tools
- A documented way to add a language detector (e.g. `go test`) via an in-process entry point
- `pip`/`uv` packaging metadata complete; optional container *recipe* for sandboxed runs (not required to use the CLI)
- Opt-in anonymous usage counters (off by default); `wecoder usage export` writes local JSON
- No license key, no forced login

## Scope

**In scope**

- Benchmark orchestrator reusing consensus isolation
- Rubric implementation that is deterministic given TestReports, findings, token usage, and a simple complexity metric (e.g. lines changed)
- Plugin registries already exist (models/tools); stabilize them and add detector plugins for verify
- One example extra detector (Go *or* Node if Node is not already first-class) as a template
- Packaging polish (`pyproject` classifiers, console script already present)
- Opt-in telemetry design (file-based flag); if implemented, it must send nothing unless enabled and must show the payload
- Usage export

**Out of scope**

- Multi-region hosted runners
- Stripe / accounts / SSO
- Kubernetes
- Universal language matrix completion
- Merging Khwarizmi
- Web IDE
- Claiming enterprise compliance

## Architecture

```
bench
  → N isolated candidates (N≤3) via existing agent/mode
  → verify each
  → optional specialists (off by default during bench)
  → Rubric.score(candidate) → table
  → user flag --apply winner | default present table only

plugins
  → entry points group wecoder.detectors / wecoder.tools
  → loaded in-process, sandboxed only by existing policy
```

Internal sequencing recommended:

1. Rubric + bench CLI (depends on isolation + TestReport)
2. Detector entry points
3. Packaging + usage export + opt-in telemetry stub

## Components

| Component | Responsibility |
|-----------|----------------|
| `Rubric` | weighted score, explainable |
| `BenchOrchestrator` | candidates, isolate, score |
| Detector plugin API | wrap Phase 05 detection |
| Usage export | read Phase 08 ledger |
| Telemetry (optional) | local flag + explicit payload print |

## Interfaces / Contracts

### Rubric dimensions (weights must be documented and configurable)

| Dimension | Signal | Default weight |
|-----------|--------|----------------|
| correctness | tests passed | 0.45 |
| quality | count of med/high quality findings (lower is better) | 0.15 |
| security | count of med/high security findings | 0.15 |
| complexity | lines changed / files touched (lower better) | 0.10 |
| cost | estimated tokens/usd (lower better) | 0.15 |

If tests were skipped, correctness is `unknown` and that candidate cannot auto-win.

### CLI

```text
wecoder bench TASK --candidates 2 --allow-expensive
wecoder bench TASK --apply
wecoder plugins list
wecoder usage export --out usage.json
```

### Telemetry

```toml
[telemetry]
enabled = false
# if ever true: show endpoint and payload schema; allow only counters not prompts
```

Implementing an actual HTTP POST is **optional**. A stub that refuses unless enabled and still no-ops with a “not configured” message is acceptable. Do not pick a vendor.

## Files Expected To Be Created

```
wecoder/verify/rubric.py
wecoder/orchestration/bench.py
wecoder/plugins/__init__.py
wecoder/plugins/discover.py
wecoder/cli/bench_cmd.py
wecoder/cli/plugins_cmd.py
wecoder/cli/usage_cmd.py
# optional example detector
wecoder/verify/detect_go.py
tests/verify/test_rubric.py
tests/orchestration/test_bench.py
tests/plugins/test_discover.py
```

Optional: `packaging/Dockerfile` for a **dev** sandbox image. Not required for CLI users.

## Files Expected To Be Modified

- `pyproject.toml` — entry points, project URLs, optional extras
- Settings — `[bench]`, `[telemetry]`
- README **only if** the product is now real enough to replace false Beta claims with honest install + mode docs. This is the first phase where a README rewrite is appropriate, and only to match implemented reality.

## Files That Must NOT Be Modified

- `LICENSE` (keep MIT unless a separate, explicit legal decision is made — not this phase)
- Planning docs (do not “close” them with fake completion checkboxes)
- Do not add billing code
- Do not vendor Khwarizmi

## Dependencies

- Phase 05 TestReport
- Phase 06/10 isolation + checkpoints
- Phase 08 usage ledger
- Phase 11 Finding (optional input; bench must work if specialists off)

## Implementation Requirements

1. Rubric unit tests with synthetic TestReports (winner is explainable).
2. Bench integration with FakeModel two candidates; table printed; workspace unchanged without `--apply`.
3. `--apply` keeps winner, discards loser (same invariants as consensus).
4. `--candidates 4` rejected (cap 3).
5. `plugins list` works with the built-in detectors.
6. `usage export` produces JSON from a stored session.
7. Telemetry remains off; a test asserts no HTTP is attempted by default.
8. Still no live model in CI.

## Error Handling

- Candidate crash → score that candidate as failed, continue others
- All candidates fail tests → do not apply; status failed
- Plugin import error → skip plugin, warn, do not crash CLI

## Security Requirements

- Plugins run in-process: only load entry points from installed packages, not from random workspace Python files (workspace code execution is already a tool concern)
- Bench isolation same as consensus
- Telemetry, if enabled later, never includes prompts, file contents, or secrets
- Usage export stays local

## Performance Requirements

- Sequential candidates by default
- Cap 3
- Specialists off unless asked (they multiply cost)

## Cost Considerations

Benchmarking is the most expensive feature in the roadmap. That is why it is last, opt-in, capped, and requires `--allow-expensive`.

Commercial foundation must not create WeCoder-paid inference.

## Testing Requirements

See Implementation Requirements.

## Acceptance Tests

1. Rubric + bench FakeModel tests
2. Plugin discovery test
3. Usage export test
4. Telemetry-off test
5. Regression: `wecoder run` single mode still default and cheap

## Deliverables

- Benchmark command + rubric
- Stabilized plugin/detector surface + one example
- Usage export + packaging polish
- Optional telemetry stub (off)
- Tests

## Definition of Done

- A user can compare two solutions with an explained score
- A contributor can add a test detector without editing the orchestrator
- A future commercial experiment can read usage export without a rewrite
- The product is still local-first MIT software

## Risks

- Building a billing system “while we are here”
- Treating this phase as permission to implement a web SaaS
- Running specialists + 3 candidates × leader mode by default
- README that again overclaims

## Explicitly Deferred Work

Anything not listed: hosted runners, SSO, marketplaces, full language matrix, Khwarizmi merge, IDE.

Those require new ADRs and, honestly, evidence of users.

## Handoff To Next Phase

There is no Phase 13 in this plan. Further work starts with evidence from real users and a new ADR. Do not invent Phase 13 during implementation.

---

## Implementation Prompt

```
You are implementing Phase 12 of WeCoder.AI and ONLY Phase 12.

Read first:
- docs/phases/PHASE-12.md
- docs/MASTER_PLAN.md
- docs/COMMERCIAL_STRATEGY.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-020, ADR-021, ADR-022)
- docs/PRODUCT_NORTH_STAR.md

Inspect the repository. You need TestReport, isolation/checkpoints, and usage ledger. If those are missing, stop and report. Implement this phase as three tight slices if needed (bench, plugins, commercial foundations) but do not start unrelated vision items.

Implement ONLY:
- Bounded solution benchmarking (max 3 candidates, --allow-expensive, explainable rubric)
- Apply-winner optional; default is report only
- Detector/tool plugin discovery via package entry points
- usage export
- packaging polish
- telemetry OFF by default and no HTTP in tests

Do not implement: Stripe, SSO, control plane, Kubernetes, web IDE, Khwarizmi merge, universal language support, default multi-candidate runs.

Do not modify LICENSE.
You may update README only to honestly match implemented reality (remove false Beta/dual-agent claims if they are still wrong, or describe what actually works).
Do not modify planning documents except you must not mark the whole vision done if it is not.

Preserve existing defaults (single mode, router off, specialists off).
After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not invent Phase 13.
```
