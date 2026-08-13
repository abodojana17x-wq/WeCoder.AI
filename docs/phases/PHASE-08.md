# Phase 8 — Sessions, Observability & Cost Control

## Objective

Make WeCoder a daily driver: persist sessions on disk, show traces of what happened, meter tokens and **estimated** spend, and give the user commands to list, inspect, and delete their history.

No router yet. No SaaS. Local files/SQLite only (ADR-018, ADR-022).

## Why This Phase Exists

Without persistence, users cannot resume work or file a bug with a trace. Without a usage ledger, Phase 09’s router has nothing honest to optimize and Leader mode’s cost is invisible. This phase is how the product becomes operable and commercially measurable without becoming a cloud service.

## Current State

After Phase 07:

- Single and Leader runs exist
- Session is in-memory
- Usage is printed then thrown away
- Logs exist but are not a queryable history

## Target State

- Each `wecoder run` writes a session directory or SQLite row
- `wecoder session list|show|delete` works
- Traces include: messages metadata (not necessarily full prompts by default), tool names/args summaries, policy decisions, test reports, checkpoints, per-role usage
- Cost estimator applies a user-editable price table (defaults for a few known models; unknown models → tokens only)
- Redaction of secrets in stored traces
- User can delete all history

## Scope

**In scope**

- Session store (SQLite recommended; JSONL files acceptable)
- Trace writer
- Usage ledger + optional USD estimate
- CLI session commands
- Config for storage path and “store full prompts: bool” default **false**
- Resume: `wecoder run --continue SESSION_ID` appends to the same conversation if workspace matches (nice-to-have; required if cheap)

**Out of scope**

- Multi-tenant backend
- License keys / billing
- Model router (Phase 09)
- Hosted telemetry
- Full TUI rewrite (richer `session show` is enough; a Textual app is not required)

## Architecture

```
Agent / Leader
  → TraceSink.append(event)
  → SessionStore.save(session)

wecoder session list → store.query
wecoder session show ID → render (redacted)
wecoder session delete ID|--all
```

Storage root: `.wecoder/sessions/` in the workspace and/or `~/.wecoder/sessions/`. Prefer **workspace-local** so history does not leak across projects. Document the path.

## Components

| Component | Responsibility |
|-----------|----------------|
| `SessionStore` | CRUD, list recent |
| `TraceEvent` | typed events |
| `UsageLedger` | sum tokens per provider/model/role |
| `PriceTable` | optional estimate |
| Redactor | apply to stored content |
| CLI `session` | user control |

## Interfaces / Contracts

### Session record

```text
id: str
created_at, updated_at: datetime
workspace: str
mode: single | leader
status: ...
task: str
checkpoint_id: str | None
usage: {input_tokens, output_tokens, estimated_usd | None}
paths: [changed files]
```

### Trace events (minimum)

`run_started`, `role_changed`, `model_call` (model id, tokens, latency; prompt omitted by default), `tool_call`, `policy_decision`, `verify`, `checkpoint`, `run_finished`

### Settings

```toml
[session]
store = "workspace"          # workspace | user
save_prompts = false
retain_days = 30             # 0 = forever; deletion still available

[cost]
currency = "USD"
# optional path to override prices
price_file = ""
```

### Price table

A small JSON/TOML map `provider/model → {input_per_mtok, output_per_mtok}`. If missing, `estimated_usd = null`. Do not scrape the internet for prices.

## Files Expected To Be Created

```
wecoder/session/__init__.py
wecoder/session/store.py
wecoder/session/trace.py
wecoder/session/redact.py
wecoder/observability/usage.py
wecoder/observability/prices.py
wecoder/cli/session_cmd.py
tests/session/test_store.py
tests/session/test_redact.py
tests/observability/test_usage.py
```

## Files Expected To Be Modified

- `wecoder/agent/session.py` — persist hook
- `wecoder/cli/run_cmd.py` — write session, print session id and cost
- `wecoder/config/settings.py`
- `.gitignore` — sessions already ignored (verify)
- Orchestrator — emit role events

## Files That Must NOT Be Modified

- `LICENSE`, planning docs
- Policy/Git semantics
- Do not add HTTP telemetry
- Do not add Stripe/license checks

## Dependencies

- Phases 04–07 produce the events to store
- Phase 02 usage fields on completions

## Implementation Requirements

1. After a FakeModel `run`, `session list` shows one row.
2. `save_prompts=false`: stored trace does not contain the user task *body* if you also store a short hash or truncated title — actually the task is useful in `list`; allow storing the **user task string** (they typed it) but not file contents or full model transcripts by default.
3. Redactor: `sk-` / `AKIA` / `-----BEGIN` patterns become `***` in anything stored.
4. `session delete --all` removes workspace session files; test it.
5. Cost: with a test price table, 1000 in / 500 out tokens compute a known USD value.
6. Unknown model: tokens recorded, usd null, no crash.
7. No network in tests.

## Error Handling

- Store I/O errors must not crash a successful agent run after the fact; warn and continue (the code change is more important than the ledger). Tests should still cover store success.
- Corrupt session file skipped in `list` with a warning.

## Security Requirements

- Default do not store full prompts/file dumps
- Redact secrets
- `session show` respects the same denylist (do not re-read `.env` into a trace)
- Deletion is real (unlink files / delete rows), not a soft hide only

## Performance Requirements

- `list` of hundreds of sessions should be fine; do not load every trace body
- Do not block the agent loop on expensive serialization of huge raw model payloads

## Cost Considerations

This phase *measures* cost. It must not *add* model calls (no LLM summarizer for traces).

## Testing Requirements

See Implementation Requirements. Include a leader-mode run that stores summed usage.

## Acceptance Tests

1. list/show/delete work on a temp workspace
2. Redaction test
3. Price estimate test
4. Existing run/test/rollback still pass
5. No outbound telemetry

## Deliverables

- Local session store + CLI
- Trace events + usage ledger + price table
- Redaction and deletion
- Tests

## Definition of Done

- Users can answer “what did WeCoder do yesterday and what did it cost?”
- Router (next) can read the ledger schema
- Still zero cloud infrastructure

## Risks

- Building Datadog. **No.**
- Storing entire repos in SQLite. **No.**
- Adding analytics “just a POST”. **Forbidden.**

## Explicitly Deferred Work

- Router (Phase 09)
- Global memory (Phase 11) — sessions are not memory
- Billing (Phase 12)
- Fancy TUI

## Handoff To Next Phase

Phase 09 should import `UsageLedger` aggregates (tokens per model, failure rates if you record `model_call` errors). Do not change event names casually; version them if needed.

---

## Implementation Prompt

```
You are implementing Phase 08 of WeCoder.AI and ONLY Phase 08.

Read first:
- docs/phases/PHASE-08.md
- docs/MASTER_PLAN.md
- docs/COMMERCIAL_STRATEGY.md (measure cost; do not bill; no hosted telemetry)
- docs/ARCHITECTURAL_DECISIONS.md (ADR-018, ADR-021, ADR-022)

Inspect the repository. Phases 04–07 should exist. If the agent/run path is missing, stop and report.

Implement ONLY sessions, observability, and cost control:
- Workspace-local session store (SQLite or JSON files)
- Trace events, usage ledger, optional price table estimates
- `wecoder session list|show|delete`
- Redaction; save_prompts default false
- Real deletion
- Tests offline

Do not implement: model router, new providers, memory, billing, license keys, HTTP telemetry, SaaS, TUI rewrite, extra collaboration modes.

Preserve existing run/leader/policy/git behavior (additive persistence).
Do not modify LICENSE or planning documents.

After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not start Phase 09.
```
