# WeCoder.AI — Architectural Decision Records

**Status:** Decisions made during planning (2026-08-12).  
**Scope:** Only decisions that are justified by the empty repository, the product principles, or an explicit constraint in the master plan.  
**Not in this file:** Implementation micro-choices (library X vs Y) unless they are load-bearing. Those belong to the phase that introduces them.

Format: each record is a decision, the context that forced it, the options considered, the consequences, and the phase it takes effect.

---

## ADR-001 — The README is vision, not architecture

**Decision:** Treat `README.md` as an aspirational product description. Do not implement its dual-agent, offline-first, or “Beta” claims as if they already exist. Do not let the README’s narrower dual-agent story block the broader team vision, and do not let the broader vision replace the README’s useful constraint (local, low-resource, critique loop).

**Context:** The repository contains a README, a MIT license, and a Python `.gitignore`. The README stops mid-section and advertises a Beta dual-agent system that is not in the tree.

**Consequences:**

- Planning documents are the source of sequencing.
- A future README rewrite is allowed only when a phase actually ships the capability being claimed.
- Phase 01 must not “complete the README features”.

**Takes effect:** Immediately (planning).

---

## ADR-002 — Canonical name is WeCoder.AI

**Decision:** The product, package, and CLI are **WeCoder.AI** / `wecoder`. Conversational use of “WeCode.AI” refers to the same product and is not a second codebase.

**Context:** The repository, GitHub project, and README use WeCoder.AI. Some planning language uses WeCode.AI.

**Consequences:**

- Python distribution name: `wecoder`
- Config directories: `.wecoder/` and `~/.wecoder/`
- No `wecode` / `wecoder` dual packages

**Takes effect:** Phase 01.

---

## ADR-003 — Python 3.11+ as the implementation language

**Decision:** Implement WeCoder.AI as a Python 3.11+ application.

**Context:** The README advertises Python 3.9+. The `.gitignore` is a Python template. There is no existing code to preserve. Agent products need asyncio, typing, process control, and a fast CLI ecosystem.

**Options considered:**

| Option | Why not (or why yes) |
|--------|----------------------|
| Python 3.9+ as advertised | Loses `tomllib`, better typing, and TaskGroup/exception groups. No users to break. |
| **Python 3.11+** | Available everywhere we care about; matches modern tooling. **Chosen.** |
| TypeScript/Node | Fine for later IDE work; weaker default for local process/jail tooling as the core. |
| Rust/Go | Better for a sandbox supervisor later; slower product iteration now. |

**Consequences:**

- README badge should be updated when the project becomes installable (Phase 01 or whenever the README is honestly rewritten).
- No runtime dependency on 3.9-specific compromises.

**Takes effect:** Phase 01.

---

## ADR-004 — CLI first; no web product in the early architecture

**Decision:** The first interface is a terminal CLI. A richer terminal UX may appear in Phase 08. A web UI, desktop IDE, or VS Code extension is out of scope until the loop is proven (Phase 12 at the earliest, and only if demanded).

**Context:** The vision mentions a user interface layer. Hosted UIs create origin, auth, and infrastructure problems the project cannot afford and does not need to validate the idea.

**Consequences:**

- Phase 01 delivers `wecoder` as the entry point.
- No FastAPI control plane, no Next.js app, no WebSocket agent console in Phases 01–09.
- Later UIs must be clients of the same session/agent APIs, not a second agent implementation.

**Takes effect:** Phase 01; re-open only in Phase 12.

---

## ADR-005 — In-house agent loop; no orchestration framework as foundation

**Decision:** Phases 04–07 implement a small, explicit agent loop and (later) a Leader orchestrator. Do not adopt LangGraph, CrewAI, AutoGen, LlamaIndex, or similar as the core runtime.

**Context:** The repository is empty. Frameworks optimize for graph experiments and vendor examples. They also become the product, which conflicts with “users should not have to learn an orchestration library”.

**Consequences:**

- We own the session state machine.
- We can add modes in Phase 10 without a framework migration.
- We will reinvent a *small* amount of loop code. That is acceptable.
- Libraries for HTTP, CLI, and testing are encouraged. Libraries that want to own “the agent” are not.

**Takes effect:** Phase 04. Revisit only if a later phase proves the in-house loop is the bottleneck (unlikely before Phase 10).

---

## ADR-006 — Model-agnostic interface before any agent

**Decision:** Phase 02 introduces a `ModelProvider` protocol. All completions go through it. Vendor SDKs, if used at all, stay inside provider adapters.

**Context:** The vision lists GPT, Claude, Gemini, Grok, DeepSeek, Kimi, Khwarizmi, and local models. The README already wants Ollama, LM Studio, and cloud APIs. If the agent imports a vendor client, the rest of the roadmap is fiction.

**Consequences:**

- Orchestration never switches on `if provider == "openai"`.
- Khwarizmi, Claude, and Gemini can be added later as adapters.
- Tests use a `FakeModel` that implements the same protocol.

**Takes effect:** Phase 02. Irreversible without a new ADR.

---

## ADR-007 — First providers are Ollama and OpenAI-compatible HTTP

**Decision:** Ship exactly two adapters in Phase 02:

1. **Ollama** — local, offline-first, matches the README.
2. **OpenAI-compatible HTTP** — one client covers OpenAI, many proxies, LM Studio, vLLM, Groq-compatible endpoints, DeepSeek-compatible endpoints, and other `/v1/chat/completions` servers.

Dedicated Anthropic, Gemini, Grok, Kimi, and Khwarizmi adapters wait for Phase 09 unless they already speak OpenAI-compatible HTTP, in which case they are **config**, not new code.

**Context:** Supporting “all the logos” in Phase 02 would delay the MVP and still not produce a coding agent.

**Consequences:**

- LM Studio is supported if it exposes an OpenAI-compatible port (it does). No special adapter in Phase 02.
- A user can point `openai_compat.base_url` at almost anything.
- We still add native adapters later where APIs differ (tool calling, caching, thinking blocks).

**Takes effect:** Phase 02.

---

## ADR-008 — Khwarizmi AI is a provider, never a merge

**Decision:** WeCoder.AI must not vendor, submodule, redesign, or depend on Khwarizmi internals. Khwarizmi may later implement `ModelProvider` or expose an HTTP surface WeCoder already speaks.

**Context:** Both projects share an ecosystem owner. The cheapest mistake is to fuse them into an unmaintainable monorepo of “the model plus the IDE plus the team”.

**Consequences:**

- No Khwarizmi code in this repository.
- Phase 09 includes a *port* (adapter or documented OpenAI-compatible target), not an integration program.
- Product success is defined even if Khwarizmi never ships.

**Takes effect:** Immediately. Rechecked in Phase 09.

---

## ADR-009 — Offline-first is a runtime path, not a cloud ban

**Decision:** The default documented path is local (Ollama). Cloud is optional and BYOK. Core features must not require the network except for the model the user explicitly selected.

**Context:** The README is offline-first. The long-term vision includes hosted frontier models. Both are true if and only if the architecture has a local path.

**Consequences:**

- Telemetry, if ever added, is opt-in (Phase 12).
- Phase 04 acceptance requires at least one successful Ollama run.
- Features that cannot work offline (web search, hosted runners) are optional tools, not the spine.

**Takes effect:** Phase 02 onward.

---

## ADR-010 — Single agent before any collaboration mode

**Decision:** Phase 04 ships one Developer agent. Leader mode (Architect + Developer) is Phase 07. Together, Workers, Consensus, and Debate are Phase 10.

**Context:** Multi-agent systems fail by multiplying tokens and hiding the fact that no agent can use tools well. The README’s dual-agent story is valuable, but it is a *next* product, not a first one.

**Consequences:**

- No “team” objects in Phase 04 beyond a single role name.
- Phase 07 is the first time two model calls share a task by design.
- Debate/consensus are forbidden until Leader mode has evidence it helps.

**Takes effect:** Phases 04, 07, 10.

---

## ADR-011 — Why Leader mode is the first collaboration mode

**Decision:** When collaboration begins, implement **Leader mode** first: one lead (Architect) plans and reviews; one worker (Developer) edits and runs tools. The user talks to the lead’s summary, not to a committee.

**Context:** The README already describes Architect + Lead Developer. Leader mode maps to that, has a simple user experience, and limits fan-out to two roles.

**Why not the others first:**

- **Together** (shared reasoning) is hard to attribute and expensive.
- **Workers** needs a task graph and isolation we will not have.
- **Consensus** and **Debate** multiply cost and need a scoring story (Phase 12).

**Consequences:** Phase 07 deliverable is specifically Leader mode, not a mode framework with empty slots.

**Takes effect:** Phase 07.

---

## ADR-012 — Dynamic teams are late-bound

**Decision:** Do not generate role lists from the user’s prompt until Phase 10, and only after Leader mode is reliable.

**Context:** A “Game Architect + Network Engineer + QA” roster looks like the vision and usually produces a pile of prose.

**Consequences:** Role objects should be data (name, instructions, tool allowlist, model ref) from Phase 07 so Phase 10 can generate them. Phase 07 hardcodes two roles.

**Takes effect:** Phase 07 (shape), Phase 10 (generation).

---

## ADR-013 — Model router is introduced only after usage exists

**Decision:** Phase 09 adds the router. Phases 02–08 select models by explicit config or CLI flags.

**Context:** A router needs (a) more than one provider in real use, (b) a usage ledger, and (c) a working agent to assign work to. Otherwise it is a table of guesses.

**Consequences:**

- No hidden model switching in the MVP.
- Phase 08’s cost ledger is a dependency for intelligent routing.
- The router is optional; users can still pin a model.

**Takes effect:** Phase 09.

---

## ADR-014 — Tools before intelligence features

**Decision:** Filesystem, search, and a jailed shell land in Phase 03, before the agent. Memory, reviewers, and benchmarking wait until those tools and the agent loop are real.

**Context:** Coding agents are tool users. Memory of decisions is worthless if the product cannot edit `main.py`.

**Consequences:** Phase 03 is a hard dependency of Phase 04. Phase 11 memory cannot substitute for context packing in Phase 03.

**Takes effect:** Phase 03.

---

## ADR-015 — Workspace jail is mandatory; containers are optional and late

**Decision:** From the first mutating tool, all paths are resolved under a workspace root and refused if they escape. Commands run with that cwd, a timeout, and a scrubbed environment. Full container/microVM isolation is not a Phase 03 requirement.

**Context:** The product will execute model-proposed commands. A Docker dependency would block offline and low-resource users the README cares about. A missing jail would be negligent.

**Consequences:**

- Prompt injection can still *ask* for `rm -rf /`; the jail and Phase 06 policy must make that fail or require approval.
- Some users will want stronger isolation later (Phase 12).
- Tests in every relevant phase assert path escape failure.

**Takes effect:** Phase 03; approval layer in Phase 06.

---

## ADR-016 — Safety and human approval exist because the tool is a local RCE engine

**Decision:** Introduce an explicit policy engine and Approve / Reject / Review flow in Phase 06, before multi-agent. Default-deny for destructive filesystem operations, dependency installation, and commands that look like secret or remote-install hazards.

**Context:** Once Phase 03 exists, WeCoder is a program that can destroy a disk and exfiltrate `.env` files. Two agents (Phase 07) increase the chance of a bad command. Approval after that would be late.

**Consequences:**

- Phase 04 documents that users should run on a branch and that product-level approval is not done yet.
- Phase 07 agents share one policy; they do not get extra privileges.
- “YOLO mode” if it ever exists must be explicit and non-default.

**Takes effect:** Phase 06.

---

## ADR-017 — Git intelligence is a recoverability feature, not a GitHub product

**Decision:** Phase 06 adds local checkpoints, diffs, and rollback (and conservative commits on a WeCoder branch if the user opts in). Hosted PR automation, multi-remote orchestration, and GitHub Apps are out of scope until there is a reason.

**Context:** The vision lists commits, branches, checkpoints, diffs, rollbacks. The commercially honest need is: **undo the agent**.

**Consequences:**

- Prefer local Git operations on the user’s existing repo.
- Do not require GitHub authentication for the core loop.
- Read-only `git status` / `git diff` may appear earlier; mutating Git waits for Phase 06.

**Takes effect:** Phase 06.

---

## ADR-018 — Local-first persistence; no required cloud data plane

**Decision:** Config, logs, and (Phase 08) sessions live on disk — files and/or SQLite. No Postgres, Redis, object store, or hosted telemetry is part of the target architecture for Phases 01–11.

**Context:** Premature infrastructure is the main way similar projects spend money before they have users.

**Consequences:**

- Phase 08 session store must be deletable by deleting a directory or running a documented command.
- Team-shared history is a Phase 12 commercial question, not a NOW design input.

**Takes effect:** Phase 01 (logs/config), Phase 08 (sessions).

---

## ADR-019 — Context is packed and budgeted; RAG is not a foundation

**Decision:** Phase 03 builds a deterministic context packer (tree, ignore rules, explicit reads, size caps). Vector databases and embedding pipelines are not introduced until memory work in Phase 11, and only if the packer is insufficient.

**Context:** RAG adds a service, failure mode, and privacy surface. Most early coding tasks fail from bad tools or bad instructions, not from missing cosine similarity.

**Consequences:**

- Full-repo dumps are a bug.
- “Memory” in Phase 11 is structured and user-visible first, embeddings later if ever.

**Takes effect:** Phase 03.

---

## ADR-020 — Language support is an execution plugin surface, not a matrix to finish

**Decision:** First-class support is **Python**, because WeCoder itself is Python and the fixture app is Python. JavaScript/TypeScript is opportunistic (the shell can run `npm test` if present). Dart, Java, C#, C++, Rust, Go, Flutter, Godot, Android, and .NET wait for an extension mechanism in Phase 12, driven by actual users.

**Context:** The vision lists many languages and frameworks. Implementing “universal support” is how the MVP never ships.

**Consequences:**

- Test runner in Phase 05 detects Python pytest/unittest first; Node as a second detector is allowed if cheap.
- Do not add language-specific agents in Phase 04.

**Takes effect:** Phases 04–05; reopen in Phase 12.

---

## ADR-021 — Bring your own keys; WeCoder does not buy tokens for users

**Decision:** Cloud inference is billed to the user through their keys or their local hardware. The architecture must not assume a WeCoder-operated inference budget.

**Context:** Commercial strategy requires near-zero COGS until someone pays for a hosted add-on.

**Consequences:**

- No server-side proxy in Phases 01–11.
- Cost features estimate *the user’s* spend, not ours.
- A hosted router in Phase 12, if any, is optional and priced.

**Takes effect:** Phase 02 onward.

---

## ADR-022 — Commercial packaging is last

**Decision:** Billing, feature gates, hosted control planes, and marketing sites are Phase 12 concerns. They must not shape Phases 01–09 interfaces beyond leaving a usage ledger (Phase 08) that a later billing system could read.

**Context:** There is no product to sell. Building Stripe early is a category error.

**Consequences:** Phase 08 may record usage. It may not include license-key checks.

**Takes effect:** Phase 12.

---

## ADR-023 — Testing uses fakes; live models never block merge

**Decision:** CI and default pytest runs use `FakeModel`, temp workspaces, and HTTP stubs. Optional live tests are marked and skipped unless explicitly selected.

**Context:** Live model calls are non-deterministic, secret-bearing, and expensive. They cannot be the definition of green.

**Consequences:**

- Contract tests lock provider adapters.
- Quality of GPT vs Claude is not a unit test.
- Phase 04 still requires a documented manual live run for MVP acceptance.

**Takes effect:** Phase 01 (harness), Phase 02 (provider contracts).

---

## ADR-024 — Extensibility via registries, not microservices

**Decision:** Models, tools, and (later) roles are registered in-process. WeCoder is one CLI process coordinating subprocesses for user commands. It is not a mesh of services.

**Context:** “Scalability” in this product means “more tools and providers”, not “more Kubernetes pods”.

**Consequences:**

- `ModelRegistry`, `ToolRegistry`, and later `RoleSpec` are the extension points.
- No message bus in the target architecture.

**Takes effect:** Phases 02–03; roles in 07.

---

## ADR-025 — Safety policy is shared across agents

**Decision:** When multiple agents exist, they share one `Policy` and one workspace. A reviewer does not get a looser shell because it is “senior”.

**Context:** Multi-agent privilege escalation is a realistic failure mode (“the architect said to install this”).

**Consequences:** Phase 07 must pass the same policy object into every role. Phase 10 dynamic teams cannot mint elevated tools without a user-visible policy change.

**Takes effect:** Phase 06 (policy object), Phase 07 (shared use).

---

## Record hygiene

New ADRs should be added when a phase would otherwise silently reverse one of the above. Do not add ADRs for library version pins unless they leak across phases.

Rejected on purpose (not decisions we made, ideas we refused):

- Making Khwarizmi the default model
- Implementing all five collaboration modes in the first multi-agent phase
- Requiring Docker to run the MVP
- Building a SaaS control plane so the CLI has something to call
- Supporting the full language/framework list as a Phase 04 goal
