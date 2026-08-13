# Phase 9 — Intelligent Model Router & Provider Expansion

## Objective

Add an optional **Model Router** that chooses, falls back, and (lightly) escalates models based on task class and cost, and expand first-class providers beyond Ollama + OpenAI-compatible — including a **Khwarizmi port** (adapter or documented OpenAI-compatible target) without merging Khwarizmi.

Pinned models must still work. The router is not the default surprise.

## Why This Phase Exists

By now the product has a working agent, optional dual-agent, and a usage ledger. Only now is routing more than folklore (ADR-013, ADR-008). Additional native adapters exist because some APIs are not actually OpenAI-compatible once tool calling and errors matter.

## Current State

After Phase 08:

- Two providers + FakeModel
- Explicit provider/model in config
- Usage ledger exists
- Leader mode can set per-role model refs manually

## Target State

- `Router` interface: `select(task_profile) -> ModelRef`
- Strategies: `pinned` (current behavior), `cheap_first`, `leader_split` (architect vs developer)
- Fallback: on `ModelUnavailableError` / `ModelAuthError`, try the next candidate once
- Additional adapters as justified: Anthropic Messages and/or Gemini only if you can do so with a thin adapter; plus `khwarizmi` as either a named OpenAI-compatible preset or a tiny adapter wrapping the same client
- `wecoder models route --dry-run "task"` prints the chosen ref without calling (or with a cheap classify)
- Classification must not use a frontier model by default (heuristic first; optional tiny local model later)

## Scope

**In scope**

- Router module + config
- Task profile heuristics (e.g. size of workspace sketch, presence of tests, mode=leader)
- Fallback list
- One or two native cloud adapters **or** well-named presets if native SDKs would explode scope
- Khwarizmi provider **slot**
- Tests with FakeModels representing multiple ids
- Docs in help text for adding a provider

**Out of scope**

- Learned bandit that trains on user data in the cloud
- Calling three models and voting (that is Consensus, Phase 10 / Benchmarking Phase 12)
- Merging Khwarizmi source
- Changing the agent loop’s ModelProvider usage (it still receives one provider instance)

## Architecture

```
Settings.router
  → Router.select(TaskProfile, UsageHints) → ModelRef
  → Registry.create(ModelRef)
  → on ModelUnavailableError → next ModelRef once
```

Heuristics examples (document and test):

- Default / small edit → cheap or local model
- Leader architect step → stronger model if configured
- After N failures → optional escalate (off by default)

## Components

| Component | Responsibility |
|-----------|----------------|
| `TaskProfile` | mode, estimated context bytes, verify requested |
| `Router` | select + fallback |
| `pinned` strategy | ignore profile, use settings.model |
| `cheap_first` | prefer ollama / cheaper ids from a user list |
| Provider adapters | thin |
| `khwarizmi` registration | no Khwarizmi code vendored |

## Interfaces / Contracts

### Settings

```toml
[router]
enabled = false
strategy = "pinned"          # pinned | cheap_first | leader_split
fallback = ["ollama", "openai_compat"]   # provider ids; model from their config sections
escalate_on_verify_fail = false

[models.cheap]
provider = "ollama"
model = "qwen2.5-coder"

[models.strong]
provider = "openai_compat"
model = "gpt-4.1-mini"

[providers.khwarizmi]
# Either:
#   type = "openai_compat"
#   base_url = "http://127.0.0.1:PORT/v1"
# or a dedicated adapter later with the same ModelProvider
```

### Router protocol

```text
select(profile: TaskProfile) -> list[ModelRef]   # ordered candidates
```

Agent/orchestrator tries in order on unavailable/auth only — **not** on “I didn’t like the code”.

### Khwarizmi rule

- No submodule
- No copy of Khwarizmi weights or training code
- Register `khwarizmi` in the registry
- If the real HTTP schema is unknown at implementation time, implement it as an `openai_compat` preset with a clear TODO and contract tests against a stub

## Files Expected To Be Created

```
wecoder/orchestration/router.py
wecoder/orchestration/task_profile.py
wecoder/models/providers/anthropic.py     # only if implemented
wecoder/models/providers/gemini.py        # only if implemented
wecoder/models/providers/khwarizmi.py     # preset or thin wrapper
tests/orchestration/test_router.py
tests/models/test_new_providers.py        # stubs
```

If you skip native Anthropic/Gemini because of time, that is acceptable **if** `khwarizmi` slot + router + fallback are done and documented. Do not skip the router.

## Files Expected To Be Modified

- `wecoder/models/registry.py` — new ids
- `wecoder/cli/run_cmd.py` — use router when enabled
- `wecoder/cli/models_cmd.py` — dry-run route
- Settings
- Leader orchestrator — `leader_split` assigns cheap/strong if configured

## Files That Must NOT Be Modified

- `LICENSE`, planning docs, any Khwarizmi external repo (there isn’t one here — do not add it)
- Policy / git
- Do not change FakeModel contract except additive

## Dependencies

- Phase 02 registry
- Phase 08 usage types (optional input to heuristics; do not require a populated DB)
- Phase 07 RoleSpec.model_ref

## Implementation Requirements

1. `router.enabled=false` → bit-identical selection to today’s pinned settings (test).
2. Fallback: first FakeModel raises `ModelUnavailableError`, second succeeds.
3. Do **not** fallback on `PathEscapeError` or user reject.
4. `cheap_first` returns the cheap ModelRef when configured.
5. `leader_split` assigns architect=strong, developer=cheap when both configured (or the inverse if you document cost-aware architect-on-cheap — pick one, test it, default architect=strong / developer=cheap is fine).
6. Khwarizmi appears in `wecoder models list`.
7. New adapters have HTTP stub contract tests like Phase 02.
8. No live network in CI.

## Error Handling

- Empty fallback list + unavailable → `ModelUnavailableError` as today
- Unknown strategy → `ConfigError`
- Router must not swallow tool errors

## Security Requirements

- New providers use the same key-from-env pattern
- Do not log API keys
- Khwarizmi base URL is user-configured, not a hardcoded secret endpoint that phones home without disclosure

## Performance Requirements

- Selection is in-process and cheap
- At most one fallback retry per step
- No “classify this task” extra cloud call by default

## Cost Considerations

- Router default **off**
- `escalate_on_verify_fail` default **false**
- Heuristics exist to **reduce** spend, not to ensemble

## Testing Requirements

Listed above. Also: leader mode still works with router off.

## Acceptance Tests

1. Pinned path unchanged when router disabled
2. Fallback test
3. cheap_first / leader_split tests
4. khwarizmi listed and stub-complete
5. Offline pytest green

## Deliverables

- Router + strategies + dry-run CLI
- Khwarizmi provider slot
- Optional native adapters
- Tests

## Definition of Done

- Users can pin, or opt into cheap_first/fallback
- Khwarizmi can be pointed at without a WeCoder redesign
- No voting ensembles

## Risks

- Router that always picks the expensive model “to be safe”
- Secretly calling two models every turn
- Vendoring Khwarizmi

## Explicitly Deferred Work

- Consensus/Debate (Phase 10)
- Benchmarking many solutions (Phase 12)
- Learned pricing optimizer

## Handoff To Next Phase

Phase 10 modes must request models through the same router/pinned path. A Debate mode must not hardcode four vendor SDKs.

---

## Implementation Prompt

```
You are implementing Phase 09 of WeCoder.AI and ONLY Phase 09.

Read first:
- docs/phases/PHASE-09.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-006, ADR-007, ADR-008, ADR-013)
- docs/COMMERCIAL_STRATEGY.md (BYOK, do not pay users’ tokens)

Inspect the repository. Phases 02 and 08 should exist (registry, usage). Phase 07 RoleSpec if leader exists. If the model interface is missing, stop and report.

Implement ONLY the model router and provider expansion:
- Router with pinned (default), cheap_first, leader_split
- enabled=false preserves current behavior
- One fallback on unavailable/auth only
- Khwarizmi provider slot without vendoring Khwarizmi
- Optional thin Anthropic/Gemini adapters; do not block the phase on them if time is tight
- Stubbed contract tests; no live network
- `wecoder models route --dry-run`

Do not implement: Consensus/Debate/Workers/Together, dynamic teams, memory, benchmarking, billing, web UI.
Do not call multiple models per turn to “vote”.
Do not add Khwarizmi source code.

Preserve existing functionality.
Do not modify LICENSE or planning documents.

After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not start Phase 10.
```
