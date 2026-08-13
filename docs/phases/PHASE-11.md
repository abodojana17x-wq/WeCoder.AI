# Phase 11 — Global Memory & Specialist Review

## Objective

Add **user-controlled persistent memory** (project and user preferences/decisions, not a silent brain dump) and **specialist reviewer roles** for quality, security, and (light) performance that run *after* a change exists and cannot write code unless the user opts into applying their suggested patches through the Developer.

## Why This Phase Exists

Memory without a working loop becomes a junk drawer. Specialists without a diff become blog posts. Both wait until sessions, teams, and policy exist so memory is inspectable and reviewers share the same jail (ADR-019, north-star human authority).

## Current State

After Phase 10:

- Sessions store traces (not memory)
- Roles and modes exist
- No durable preference store
- Architect review is general, not a security pass

## Target State

- Memory store with typed records: `preference`, `decision`, `fact`, `ignore`
- CLI: `wecoder memory list|add|delete|export`
- Agent may *read* a budgeted memory excerpt relevant to the workspace
- Agent may *propose* a memory write; default **ask** (policy) before persisting
- Specialists: `quality_reviewer`, `security_reviewer`, `perf_reviewer` as read-only RoleSpecs
- `wecoder run --review security,quality` or config after successful implement/verify
- Reviewers produce structured findings; they do not silently edit
- User can delete all memory

## Scope

**In scope**

- Local memory store (SQLite or YAML under `.wecoder/memory/` and `~/.wecoder/memory/`)
- Record schema, tags, timestamps
- Injection of a short memory excerpt into Developer/Architect prompts
- Propose-memory tool (`memory_add`) gated by policy `ask`
- Three specialist prompts + structured finding schema
- Optional apply-findings path: user says “fix finding #2” as a new run (or a bounded Developer pass if `--apply-review` and still policy-wrapped)
- Tests for deletion, redaction, allowlist

**Out of scope**

- Vector DB as a required dependency (embeddings optional and off by default; do not add Chroma/Pinecone)
- Cross-org cloud memory
- “Autonomous CISO” that files CVEs
- Performance lab / profilers beyond reading code and test timings already in TestReport
- Benchmarking multiple full solutions (Phase 12)

## Architecture

```
MemoryStore
  → retrieve(workspace_id, query_tags, budget) → list[Record]
  → propose(record) → Policy.ask → commit

After AgentResult + TestReport
  → for each requested specialist:
        read-only Agent(role) + diff + test report + memory excerpt
        → Findings
  → print findings
  → optionally queue Developer repair for selected finding ids
```

## Components

| Component | Responsibility |
|-----------|----------------|
| `MemoryRecord` | id, kind, text, tags, source, created_at |
| `MemoryStore` | CRUD, export, wipe |
| `memory_add` tool | proposal |
| Specialist prompts | quality / security / perf |
| `Finding` | severity, title, evidence path, recommendation |
| CLI `memory`, `review` | user control |

## Interfaces / Contracts

### MemoryRecord

```text
id: str
kind: preference | decision | fact | ignore
text: str                 # capped e.g. 1k chars
tags: list[str]
scope: user | workspace
```

### Findings

```text
id: str
reviewer: str
severity: low | med | high
title: str
evidence: str
path: str | None
recommendation: str
```

### Settings

```toml
[memory]
enabled = true
save_requires_approval = true
max_records_in_prompt = 12

[review]
specialists = []          # e.g. ["quality", "security"]
apply = false
```

### Security reviewer focus (keep it finite)

- hardcoded secrets
- obvious command injection in edited files
- unrestricted `run_command` patterns in *user project* code if visible
- dependency pins missing when the change added a dependency

This is **not** a replacement for a real SAST product. Say so in the CLI output.

## Files Expected To Be Created

```
wecoder/memory/__init__.py
wecoder/memory/store.py
wecoder/memory/types.py
wecoder/tools/memory.py
wecoder/agent/prompts/quality_reviewer.md
wecoder/agent/prompts/security_reviewer.md
wecoder/agent/prompts/perf_reviewer.md
wecoder/orchestration/reviewers.py
wecoder/cli/memory_cmd.py
wecoder/cli/review_cmd.py
tests/memory/test_store.py
tests/orchestration/test_reviewers.py
```

## Files Expected To Be Modified

- Tool registry — add `memory_add` / `memory_list` (list is allow)
- Policy — `memory_add` → ask by default
- Agent prompts — optional memory excerpt section
- Settings, traces (Phase 08) — `memory_written`, `finding` events
- Help text — limitations of specialist review

## Files That Must NOT Be Modified

- `LICENSE`, planning docs
- Jail / git checkpoint semantics
- Do not add cloud SDKs for vectors
- Do not give reviewers write/shell (shell may be allowed **read-only** for `git diff` via GitService, not arbitrary shell)

## Dependencies

- Phase 06 policy/approval
- Phase 08 store patterns (you may reuse SQLite helpers but keep memory *separate* from session traces)
- Phase 07/10 RoleSpec

## Implementation Requirements

1. Memory wipe test: records gone from prompt after delete.
2. Approval: FakeApprover rejects `memory_add` → store unchanged.
3. Prompt budget: 100 planted records → at most `max_records_in_prompt` injected.
4. Reviewer cannot call `write_file` (allowlist test).
5. Security reviewer FakeModel emits a finding; CLI prints it; workspace files unchanged without `--apply-review`.
6. `--apply-review` uses Developer + existing repair/policy/checkpoint.
7. Redact secrets in memory text on write.

## Error Handling

- Corrupt memory file → skip + warn
- Reviewer model failure → report reviewer error, do not fail a green implementation unless `--review-strict`
- Default: findings do not change process exit code if implementation succeeded; `--review-strict` makes high severity exit 1

## Security Requirements

- Memory is inspectable and deletable
- No silent storage of file contents
- Reviewers read-only
- Do not upload memory anywhere
- Scope `user` vs `workspace` must not leak workspace A facts into workspace B prompts

## Performance Requirements

- Memory retrieve is local and cheap (tag/filter, not a neural search required)
- Specialists run sequentially by default
- Do not run all three unless asked

## Cost Considerations

Each specialist is another model call. Default specialists list is **empty**. Security+quality on every run would surprise users.

## Testing Requirements

See Implementation Requirements. Offline FakeModels.

## Acceptance Tests

1. memory add/list/delete/export
2. approval gate
3. no cross-workspace leak
4. reviewer allowlist
5. findings do not mutate the tree by default

## Deliverables

- Memory store + CLI + tool
- Three specialist roles
- Optional apply path
- Tests

## Definition of Done

- Users can see and wipe what WeCoder remembers
- Specialists produce findings, not silent edits
- Still no vector cloud

## Risks

- Memory as uncurated chat logs. **Typed short records only.**
- Reviewer with a shell “to try exploits”. **No.**
- Turning specialists on by default.

## Explicitly Deferred Work

- Embeddings / RAG platform
- Benchmarking (Phase 12)
- Commercial compliance packs

## Handoff To Next Phase

Phase 12 may score candidate solutions using specialist findings as *inputs* to a rubric. Keep `Finding` serializable. Memory should not be required for benchmarking.

---

## Implementation Prompt

```
You are implementing Phase 11 of WeCoder.AI and ONLY Phase 11.

Read first:
- docs/phases/PHASE-11.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-016, ADR-019, ADR-025)
- docs/PRODUCT_NORTH_STAR.md (user authority, inspectable memory)

Inspect the repository. Sessions (Phase 08), policy (Phase 06), and RoleSpec (Phase 07+) should exist. If they do not, stop and report.

Implement ONLY global memory and specialist review:
- Local typed memory store with list/add/delete/export
- memory_add requires approval by default
- Budgeted memory excerpt in prompts; no cross-workspace leak
- Read-only quality, security, and performance reviewers
- Structured findings; no silent file writes
- Optional --apply-review through the existing Developer + policy + checkpoint
- Specialists default off
- Offline tests

Do not implement: vector DB, cloud memory, benchmarking ensembles, new collaboration modes, billing, SAST vendor integrations, reviewer shells.

Preserve existing functionality.
Do not modify LICENSE or planning documents.

After implementation, run relevant tests and linters.
Report files created/modified, test results, failures.
Stop. Do not start Phase 12.
```
