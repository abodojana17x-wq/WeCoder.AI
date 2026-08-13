# WeCoder.AI — Master Plan

**Status:** Planning only. No application implementation has been performed under this plan.  
**Product name:** WeCoder.AI (repository: `WeCoder.AI`; CLI name: `wecoder`)  
**Date:** 2026-08-12  
**License:** MIT  
**Planning horizon:** NOW → NEXT → LATER → FUTURE

This document is the engineering and product spine for WeCoder.AI. It tells a future implementer what the product is, what the repository actually contains today, what to build first, what must wait, and how the work is sequenced.

It is intentionally **not** an implementation. Phase-level specifications live in `docs/phases/`.

---

## 1. Project Vision

WeCoder.AI is an **AI software development team** that works on the user's machine, against the user's repository, using models the user chooses.

The user should eventually be able to describe a new project or open an existing one, ask for a feature or a fix, and have a coordinated set of specialized agents:

- understand the request and the codebase
- plan and discuss approaches
- edit files and run commands
- execute, test, detect failures, and repair them
- review quality, security, and performance
- record recoverable Git history
- stop and ask a human before dangerous work

The long-term vision includes multi-model collaboration (GPT, Claude, Gemini, Grok, DeepSeek, Kimi, Khwarizmi AI, local models), several collaboration modes (Together, Workers, Leader, Consensus, Debate), a dynamic team assembled from the task, an intelligent model router, shared memory, and solution benchmarking.

**The README describes that vision. The README is not the first release.**

The first release is much smaller: one reliable coding agent, a model-agnostic interface, real tools, and a recoverable workspace. Everything else is earned after that loop works.

### 1.1 What success looks like in one sentence

A developer can point WeCoder.AI at a real repository, give it a concrete software task, and get a tested, reviewable change with a recoverable Git checkpoint — using a local model or a bring-your-own cloud key — without the product depending on any single model vendor.

---

## 2. Product Principles

These principles constrain every phase. If a proposed feature violates them, it waits.

1. **Useful before impressive.** A single agent that completes a real change beats a twelve-agent debate that cannot write a file.
2. **Model-agnostic from day one.** Orchestration never imports a vendor SDK directly. Providers implement a stable interface.
3. **Offline-first, cloud-optional.** The core loop must work with a local model (Ollama or equivalent). Cloud providers are adapters, not a runtime requirement.
4. **Local-first, infrastructure-light.** No mandatory cloud control plane, multi-tenant SaaS, or always-on cluster until paying usage justifies it.
5. **Bring your own intelligence.** Users supply local models or their own API keys. WeCoder.AI must not force a hosted model tax to be useful.
6. **Khwarizmi stays separate.** Khwarizmi AI is a future intelligence provider, not a submodule and not a redesign target.
7. **Safety is a product feature.** Destructive filesystem work, dependency installation, secrets access, and large unreviewed patches require policy and, eventually, explicit human approval.
8. **Recoverability over bravado.** If the agent changes a repo, the user must be able to see the diff and roll it back.
9. **Cost is an architectural concern.** Tokens, retries, multi-agent fan-out, and context dumps are product costs. They are measured before they are multiplied.
10. **Extensible, not universal.** Do not ship nine languages and eight frameworks in the first year. Ship one execution path and a place to hang the next one.
11. **Interfaces before implementations.** A phase that other phases depend on must publish contracts (types, errors, config keys) before growing features.
12. **One phase at a time.** Later collaboration modes, memory, routers, and commercial packaging must not leak into earlier implementation work.

---

## 3. Current Repository State

Inspected on 2026-08-12 from the repository root. Nothing below is inferred from the README alone.

### 3.1 What exists

| Path | Role | Assessment |
|------|------|------------|
| `README.md` | Product vision (37 lines) | Partial. Describes an offline-first dual-agent framework. Cuts off mid-sentence in “How It Works”. Badges claim Beta, Python 3.9+, Dual-Agent, Offline-First. None of those capabilities exist in code. |
| `LICENSE` | MIT, copyright 2026 `abodojana17x-wq` | Complete and usable. |
| `.gitignore` | Stock GitHub Python template | Complete enough to start a Python project. Not product-specific. |
| Git remote | `https://github.com/abodojana17x-wq/WeCoder.AI.git` | Public repo. One commit on `main`. |
| Git history | Single commit: “Revise README.md for improved clarity and structure” | No product history. |

### 3.2 What does not exist

| Area | Status |
|------|--------|
| Application source | **Missing** |
| Package layout / `pyproject.toml` / lockfile | **Missing** |
| Dependencies | **Missing** |
| CLI, TUI, or UI | **Missing** |
| Configuration system | **Missing** |
| Model providers or SDKs | **Missing** |
| Agent loop / orchestration | **Missing** |
| Tool system (filesystem, shell, git, tests) | **Missing** |
| Safety / approval / sandbox | **Missing** |
| Tests | **Missing** |
| CI/CD | **Missing** |
| Docs beyond the README | **Missing** (created by this planning work) |
| Khwarizmi integration | **Missing** (and must remain decoupled) |

### 3.3 Status legend applied to the vision

| Capability | Status |
|------------|--------|
| Dual-agent Architect + Lead Developer | **Planned** (README). **Missing** in code. Introduced in Phase 07. |
| Offline-first / local models | **Planned**. Interface in Phase 02. First local provider: Ollama. |
| Multi-model mix-and-match | **Planned**. Interface in Phase 02. Router in Phase 09. |
| Full software-development loop | **Planned**. Inner loop in Phases 04–05. |
| Collaboration modes (Together / Workers / Leader / Consensus / Debate) | **Planned**. Leader in Phase 07. Remaining modes in Phase 10. |
| Dynamic AI team | **Planned**. Phase 10. |
| Intelligent model router | **Planned**. Phase 09. |
| Global memory | **Planned**. Phase 11. |
| Git intelligence | **Planned**. Phase 06. |
| Human approval | **Planned**. Phase 06. |
| Solution benchmarking | **Planned**. Phase 12. |
| Universal language/framework matrix | **Planned / deferred**. Extensibility in Phase 12, not a launch checklist. |
| Commercial layer | **Planned**. Phase 12. Strategy in `docs/COMMERCIAL_STRATEGY.md`. |

**Honest summary:** this repository is a **named vision with a license**, not a codebase. That is not a failure. It is a clean slate. The danger is treating the README as if a product already exists.

---

## 4. Architectural Assessment

### 4.1 Strengths

- **No legacy to unwind.** There is no vendor lock-in, no tangled agent framework, and no premature SaaS.
- **License is commercially usable.** MIT permits open-source distribution and later paid adjacent services.
- **Product intent is coherent.** Offline-first, multi-model, dual-agent critique is a real positioning, not a random feature pile.
- **Python is the right first implementation language** for this class of tool (agents, CLIs, process control, tests). The `.gitignore` already assumes Python.
- **Scope can still be chosen.** The most expensive architectural mistakes have not been made yet.

### 4.2 Weaknesses

- **Zero executable product.** There is no way to validate the idea against a real repository today.
- **README overclaims.** “Status: Beta” and “Architecture: Dual-Agent” are not true. They will mislead contributors and users.
- **README is incomplete** and narrower than the real product vision (dual-agent only, no mention of safety, git, router, or commercial path).
- **No engineering baseline.** No package, linter, test runner, typed config, or CI.
- **No interface seams.** There is nothing to extend. Every future capability still needs a place to land.

### 4.3 Technical debt

There is no code debt. There is **planning debt**:

- Vision is larger than any first release can absorb.
- Two names appear in conversation (`WeCode.AI` vs `WeCoder.AI`). The repository name **WeCoder.AI** is canonical.
- Python 3.9+ is advertised; the plan standardizes on **Python 3.11+** (see `docs/ARCHITECTURAL_DECISIONS.md`).
- Offline-first and multi-cloud-model collaboration are in tension. Both are valid; the architecture must allow a fully local path.

### 4.4 Architectural risks

| Risk | Why it matters | Mitigation |
|------|----------------|------------|
| Boiling the ocean | Building modes, router, memory, and teams before one agent works | Phased NOW/NEXT/LATER/FUTURE; MVP is a single agent |
| Vendor coupling | Importing OpenAI/Anthropic types into the agent loop | Model interface in Phase 02, before the agent |
| Framework lock-in | Adopting LangGraph/CrewAI/AutoGen as the product | Thin in-house loop first; no orchestration framework as a foundation |
| Token cost explosion | Naive multi-agent + full-repo context | Context budgets in Phase 03; usage accounting in Phase 08; router in Phase 09 |
| Irreversible repo damage | Agents with a shell and no git/approval | Tools are jailed in Phase 03; approval + git in Phase 06, before multi-agent |
| Fake generality | “Supports every language” with no runner | First-class path: Python (and JS/TS as opportunistic). Plugins later |
| Khwarizmi gravity | Merging a sibling model project into the coding product | Hard rule: provider adapter only |
| Premature SaaS | Auth, multi-tenant, billing, hosted runners | Forbidden until Phase 12 and only if usage demands it |

### 4.5 Security risks (even with no code)

The moment Phase 03 adds a shell tool, WeCoder.AI becomes a program that can destroy a workstation or leak secrets. Security work is therefore not a late “hardening sprint”. Policy starts when tools start.

Primary future risks:

- Path escape from the workspace
- Exfiltration of `.env`, SSH keys, cloud credentials
- Unapproved `pip install` / `npm install` / `curl | sh`
- Prompt injection via README, issues, or files the agent is told to read
- Logging API keys and file contents

### 4.6 Cost risks

- Multi-agent modes multiply tokens roughly linearly with participants and turns.
- Dumping an entire repository into context is the fastest way to make the product unusable locally and expensive in the cloud.
- Retries without a cap turn a failed task into a bill.
- A hosted-only architecture would add infrastructure cost before there is revenue.

### 4.7 Testing weaknesses

Total. Phase 01 must introduce pytest, fixtures, and a rule that model providers are tested with fakes. Live API calls never block CI.

### 4.8 What should be designed before implementation

1. A stable **Model Provider** contract.
2. A stable **Tool** contract with a `ToolContext` that carries workspace and policy.
3. A **Session** object that later modes can share.
4. A config schema that can grow without renaming keys every phase.
5. A rule that orchestration depends on interfaces, not providers.

These are designed in Phases 01–04. They are not a six-month architecture board exercise.

---

## 5. Target Architecture

The target is a **local-first, layered system**. Layers exist so features can be added without rewriting the product. They are not all built at once.

```
┌──────────────────────────────────────────────────────────────┐
│ Interface                                                    │
│   CLI (NOW) → richer terminal UX (LATER) → optional IDE/Web  │
├──────────────────────────────────────────────────────────────┤
│ Product / Session                                            │
│   Config · Session store · Usage/cost · Traces · Preferences │
├──────────────────────────────────────────────────────────────┤
│ Orchestration                                                │
│   Single-agent loop → Leader mode → other modes → teams      │
│   Model Router (LATER) · Approval gate (NEXT)                │
├──────────────────────────────────────────────────────────────┤
│ Agents / Roles                                               │
│   Developer (NOW) · Architect (NEXT) · Reviewer / QA (FUTURE)│
│   Dynamic role specs (FUTURE)                                │
├──────────────────────────────────────────────────────────────┤
│ Capabilities                                                 │
│   Tools · Project context · Test runner · Git · Verification │
│   Memory (FUTURE) · Benchmarking (FUTURE)                    │
├──────────────────────────────────────────────────────────────┤
│ Model abstraction                                            │
│   ModelProvider interface                                    │
│     Ollama · OpenAI-compatible · later: Claude, Gemini,      │
│     Khwarizmi, other local/cloud adapters                    │
├──────────────────────────────────────────────────────────────┤
│ Runtime & safety                                             │
│   Workspace jail · Command policy · Timeouts · Secret redaction│
│   Optional OS/container sandbox (FUTURE, only if needed)     │
└──────────────────────────────────────────────────────────────┘
```

### 5.1 Components that are necessary, and when

| Component | First phase | Why it exists | When it is *not* needed |
|-----------|-------------|----------------|-------------------------|
| CLI | 01 | The product is a developer tool. A CLI is the cheapest honest interface. | Web/IDE UI is not required to prove the loop. |
| Config / settings | 01 | Models, workspace root, log level, policy flags. | Cloud feature flags, org SSO. |
| Observability (structured logs) | 01 | You cannot debug an agent you cannot see. | Full tracing backend, APM SaaS. |
| Model abstraction | 02 | Prevents vendor lock-in and enables Khwarizmi later. | Router, ten providers, ensemble calls. |
| Workspace + context packer | 03 | The agent must see a project without eating the whole disk. | Vector memory, global cross-project memory. |
| Tool system (fs, search, shell) | 03 | Hands of the agent. | MCP marketplace, arbitrary plugin store. |
| Single coding agent | 04 | First useful product. | Multi-agent anything. |
| Test runner + repair loop | 05 | Completes “run → error → fix → run”. | Dedicated performance lab, coverage SaaS. |
| Approval / safety policy | 06 | Makes the tool safe on a real machine. | Enterprise GRC, SOC2 program. |
| Git intelligence | 06 | Checkpoints, diffs, rollback. | Hosted PR bots, multi-remote orchestration. |
| Leader mode (Architect + Developer) | 07 | First real collaboration; matches README. | Debate/consensus/dynamic teams. |
| Session store + cost ledger | 08 | Daily-driver UX; cost visibility. | Multi-tenant billing. |
| Model router | 09 | Cost/quality assignment once multiple models exist. | Before two providers are actually used. |
| Collaboration modes + dynamic teams | 10 | The long-term product identity. | Before Leader mode is reliable. |
| Global memory | 11 | Preferences, decisions, reusable project facts. | Before sessions and user control exist. |
| Specialist reviewers | 11 | Security/quality/performance passes. | Separate “AI security company” scope. |
| Benchmarking | 12 | Compare candidate solutions. | Before the product can complete one solution. |
| Commercial foundations | 12 | Packaging, telemetry opt-in, paid hooks. | Auth0, Stripe, Kubernetes, on day one. |
| Execution sandbox (containers) | 12 if ever | Strong isolation for untrusted repos. | Not required if cwd jail + policy + git are solid. |
| Team Manager as a platform | 10 | Dynamic workforce. | Not a microservice. |

### 5.2 Components deliberately omitted from the early architecture

- Multi-tenant control plane
- Hosted worker fleet
- Vector database as a default dependency
- LangChain / LlamaIndex as a core runtime
- Built-in model weights
- Khwarizmi source
- A web IDE
- Kubernetes manifests
- Plugin marketplace

These can be reconsidered only after the local product has real users.

### 5.3 Canonical runtime objects

These objects are the spine. Names may vary slightly in code; the meanings must not.

- **Workspace** — a rooted directory the tools are not allowed to escape.
- **Session** — one user task (or a continued conversation) with messages, tool traces, usage, and status.
- **ModelRef** — a provider id + model id + optional parameters. Never a hardcoded vendor class.
- **Tool** — a named, schema-described capability with a deterministic result object.
- **Policy** — what may run without asking, what must be approved, what is forbidden.
- **AgentResult** — files changed, commands run, tests run, summary, and whether human action is required.
- **Checkpoint** — a Git reference created by WeCoder so work is recoverable.

### 5.4 Khwarizmi integration shape

```
WeCoder.AI  →  ModelProvider  →  Ollama
                              →  OpenAI-compatible
                              →  Anthropic (later)
                              →  Gemini (later)
                              →  Khwarizmi (later, other repo)
                              →  other local/cloud adapters
```

WeCoder never vendors Khwarizmi. Khwarizmi never imports WeCoder internals. The only shared contract is the ModelProvider interface (and, if useful later, an OpenAI-compatible HTTP surface that Khwarizmi already speaks).

---

## 6. Phase Overview

Twelve phases. Four horizons. Each phase is sized so a coding agent or a small team can complete it without inventing the rest of the product.

| Phase | Horizon | Name | One-line objective |
|------:|---------|------|--------------------|
| 01 | NOW | Foundation & Engineering Baseline | Make the repo a real Python project with a CLI, config, logs, and tests. |
| 02 | NOW | Model Abstraction Layer | Ship a vendor-neutral model interface with Ollama + OpenAI-compatible providers. |
| 03 | NOW | Workspace, Context & Tool System | Give the product eyes and hands: project context, file tools, jailed shell. |
| 04 | NOW | Single Coding Agent (MVP) | Complete a real coding task end-to-end with one agent. |
| 05 | NEXT | Execution, Testing & Self-Repair | Close the run → error → fix → re-run loop. |
| 06 | NEXT | Safety, Human Approval & Git Intelligence | Make changes recoverable and dangerous actions explicit. |
| 07 | NEXT | Dual-Agent Leader Mode | Architect + Developer critique loop. First collaboration mode. |
| 08 | LATER | Sessions, Observability & Cost Control | Persist work, show traces, meter tokens and estimated spend. |
| 09 | LATER | Intelligent Model Router & Provider Expansion | Choose, fall back, and add providers (including a Khwarizmi port). |
| 10 | FUTURE | Collaboration Modes & Dynamic Teams | Workers, Together, Consensus, Debate, and task-shaped teams. |
| 11 | FUTURE | Global Memory & Specialist Review | User-controlled memory plus quality/security/performance reviewers. |
| 12 | FUTURE | Benchmarking, Extensibility & Commercial Foundations | Compare solutions, plug in runtimes, prepare a sustainable product. |

MVP is reached at the end of **Phase 04**, with Phases 05–06 turning that MVP from “demo-able” into “safe to use on a real repo”.

See `docs/MVP.md` for the product cut. See `docs/phases/` for implementation specifications.

---

## 7. Dependencies Between Phases

```
01 Foundation
    └─► 02 Model Abstraction
            └─► 03 Workspace + Tools
                    └─► 04 Single Agent          ← MVP
                            ├─► 05 Test & Repair
                            │       └─► 06 Safety + Git
                            │               └─► 07 Leader Mode
                            │                       └─► 10 Modes + Dynamic Teams
                            │                               └─► 11 Memory + Specialists
                            └─► 08 Sessions + Cost
                                    └─► 09 Router + Providers
                                            └─► 12 Benchmarking + Extensibility + Commercial
```

Hard rules:

- **01 before everything.** No package, no tests, no product.
- **02 before 04.** The agent talks to `ModelProvider`, never to a vendor client.
- **03 before 04.** No agent without tools and a workspace jail.
- **04 before 05–07.** Collaboration and repair have nothing to orchestrate otherwise.
- **06 before 07.** Two agents must not get a shell before approval and checkpoints exist.
- **07 before 10.** Do not invent four more modes before Leader mode works.
- **08 before 09.** A router without usage data will optimize folklore.
- **09 before 12 benchmarking-at-scale.** Comparing solutions across models needs a router and a cost ledger.
- **10 before 11 dynamic memory-of-teams.** Memory should record decisions from a real team, not a hypothetical one.

Soft (allowed later, not earlier):

- Additional OpenAI-compatible providers can be added in Phase 02 tests as config aliases, but first-class Claude/Gemini/Khwarizmi adapters wait for Phase 09.
- A slightly nicer CLI in Phase 04 is fine. A TUI rewrite is Phase 08+.
- Git *read* operations (status, diff) may appear in Phase 03/04 as read-only tools. Git *write* (commit, reset) waits for Phase 06.

---

## 8. Major Risks

### Product risks

- **The market is crowded** (Aider, Claude Code, Codex, Cursor, Continue, Cline, Devin). WeCoder wins only if multi-model + offline-first + recoverable local execution is real, not advertised.
- **Vision gravity.** Contributors will try to implement the entire README. The phase documents exist to stop that.
- **Empty-repo credibility.** Shipping “Beta” with no code damages trust. Phase 01 should stop implying a finished product.

### Technical risks

- Local models may be too weak for a satisfying MVP. Mitigation: OpenAI-compatible provider in Phase 02 so users can bring a strong cloud model without rewriting the agent.
- Prompt injection via repository files. Mitigation: tool policy, secret path denylist, and (Phase 06) approval for high-impact tools.
- Shell tool is an RCE surface. Mitigation: cwd jail, timeouts, denylist, no network-install by default.
- Context overflow. Mitigation: budgeted context packer in Phase 03, not “add the whole repo”.

### Commercial risks

- Building hosted infrastructure before anyone uses the CLI.
- Absorbing users' model bills (never do this in early stages).
- Paying for a dozen model evaluations per task (Phase 10–12 must be opt-in and budgeted).

### Process risks

- Implementing later phases “while we are here”.
- Designing a plugin universe before the first plugin is needed.
- Treating Khwarizmi as the default brain.

---

## 9. Commercial Strategy (summary)

Full analysis: `docs/COMMERCIAL_STRATEGY.md`.

Realistic path:

1. Open-source, local-first CLI that is actually useful (Phases 04–07).
2. Users bring local models or their own keys — **near-zero cost of goods** for the project.
3. Find 10–50 developers who complete real tasks with it.
4. Charge later, and only for things that create cost or extra value: hosted routing, managed sandboxes, team policy, priority models, support.
5. Do not build a multi-tenant SaaS to “be a startup”.

WeCoder.AI can become economically sustainable without a fantasy of millions of users. It cannot become sustainable if it is an expensive cloud agent that nobody prefers to Aider or Claude Code.

---

## 10. Testing Strategy

### Rules that apply to every phase

1. **pytest is the test runner** from Phase 01 onward.
2. **No live model calls in CI.** Providers are faked. Optional manual live tests are marked and never required to merge.
3. **Filesystem and shell tests use temporary directories**, never the developer's real home or this git checkout's `.git`.
4. **Contract tests** lock the `ModelProvider` and `Tool` interfaces so later phases cannot casually break them.
5. **A fixture mini-project** (small Python app with tests) is introduced in Phase 04 and reused through Phase 06.
6. Every phase document lists acceptance tests. A phase is not done if those tests do not exist or do not pass.

### What is not tested early

- Model quality (“did GPT choose a good name”).
- Multi-provider bake-offs.
- UI screenshots.
- Load tests for thousands of concurrent sessions.

### Quality gates

- Unit tests for config, path jail, policy, usage accounting.
- Integration tests for the agent loop against a FakeModel and a temp workspace.
- Lint + typecheck in CI from Phase 01 (ruff, and mypy or pyright once types exist).

---

## 11. Security Strategy

Security grows with capability. It is not postponed to Phase 12.

| When | Control |
|------|---------|
| Phase 01 | No secrets in logs; `.env` stays gitignored; config files do not print API keys. |
| Phase 02 | Keys only from env / user config; never from the repo by default; redacted traces. |
| Phase 03 | Workspace path jail; secret-file denylist (`.env`, `*.pem`, `id_rsa`, etc.); shell timeout; no parent-directory writes. |
| Phase 04 | Agent cannot disable the jail; tool errors are returned, not raised into unconstrained retries. |
| Phase 05 | Test commands run inside the workspace with the same jail. |
| Phase 06 | Explicit approval for destructive fs, installs, config edits, and untrusted commands; Git checkpoints before mutating work. |
| Phase 07+ | Multi-agent does not mean multi-policy. Every agent shares the same Policy. |
| Phase 08 | Persistent traces redact secrets; user can delete sessions. |
| Phase 11 | Memory is inspectable and deletable. No silent long-term storage of file contents. |
| Phase 12 | Optional stronger sandbox; commercial telemetry is opt-in. |

Human approval actions, when introduced: **Approve**, **Reject**, **Review** (inspect the proposed tool call or diff first).

Prompt injection is treated as a first-class threat from Phase 03: repository content is data, not an instruction source with higher privilege than the user.

---

## 12. Cost-Control Strategy

1. **Default local.** Ollama (or another local OpenAI-compatible server) is a first-class path.
2. **BYOK cloud.** WeCoder never proxies paid model calls in the MVP and should not do so until Phase 12, if ever.
3. **Budgeted context.** The context packer has byte/token ceilings. Full-repo dumps are forbidden.
4. **Hard caps.** Max turns, max tool calls, max tokens per session. Exceeding a cap stops the agent with a clear report.
5. **Measure before multiplying.** Usage ledger in Phase 08. Router in Phase 09. Multi-agent fan-out in Phase 10 only with budgets.
6. **Cheap model for cheap work.** Once the router exists: classification, file ranking, and commit messages should not use the most expensive model by default.
7. **No hidden retries.** Retries are counted, logged, and capped.
8. **No mandatory GPU cluster, vector DB, or cloud queue** in the architecture.

---

## 13. Definition of Overall Project Success

WeCoder.AI is succeeding when all of the following are true:

1. **A real task on a real repo completes.** Not a canned demo. A user-requested feature or bugfix lands with a visible diff.
2. **The loop is closed.** If tests or a run fail for a reason the agent can see, it attempts a bounded repair and reports the outcome honestly.
3. **Work is recoverable.** There is a checkpoint and a rollback path.
4. **Dangerous work is explicit.** The tool does not silently install packages, delete trees, or rewrite secrets.
5. **Two brains are possible without a rewrite.** A second provider can be added by implementing `ModelProvider`. Khwarizmi can be added the same way.
6. **Offline is real.** A user with Ollama and no internet can complete a small task.
7. **Cost is visible.** The user can see tokens and estimated spend for a session.
8. **The product is smaller than the vision.** Collaboration modes, memory, and benchmarking exist only after 1–7.

Failure modes that do **not** count as success:

- A beautiful multi-agent diagram with no working file edit.
- A ChatGPT wrapper with a new name.
- A SaaS landing page.
- A framework that requires a research team to run.

---

## 14. NOW / NEXT / LATER / FUTURE

### NOW — Phases 01–04

Create the first genuinely useful version: installable CLI, model interface, tools, one agent.

### NEXT — Phases 05–07

Make it trustworthy and closer to the README: repair loop, approval, git, Architect + Developer.

### LATER — Phases 08–09

Make it a daily driver with more than one model: sessions, traces, cost, router, additional providers.

### FUTURE — Phases 10–12

Become an AI software team and a sustainable product: more modes, dynamic teams, memory, specialists, benchmarking, commercial hooks.

Do not let FUTURE requirements reshape NOW interfaces beyond leaving clean seams (provider registry, tool registry, session object, policy object).

---

## 15. Document Map

| Document | Purpose |
|----------|---------|
| `docs/MASTER_PLAN.md` | This file. Journey, constraints, architecture. |
| `docs/PRODUCT_NORTH_STAR.md` | What the product is and is not. |
| `docs/MVP.md` | Smallest useful end-to-end cut. |
| `docs/COMMERCIAL_STRATEGY.md` | How this can become sustainable. |
| `docs/ARCHITECTURAL_DECISIONS.md` | Why major choices were made. |
| `docs/phases/PHASE-01.md` … `PHASE-12.md` | Implementation specifications and implementation prompts. |

---

## 16. Implementation Discipline

Future coding agents and humans:

- Read the phase file for the phase you are assigned.
- Inspect the repository as it is, not as the README dreams.
- Implement **only** that phase.
- Preserve existing behavior and contracts.
- Run that phase's tests.
- Stop.

Do not start Phase 01 as part of this planning work. This file is a map, not a construction permit for the whole city.
