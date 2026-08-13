# WeCoder.AI — MVP Definition

**Status:** Product cut for the first genuinely useful release.  
**MVP boundary:** end of Phase 04.  
**Trust upgrade (not required to *call* it MVP, required to use it on important repos):** Phases 05–06.  
**Companion documents:** `docs/MASTER_PLAN.md`, `docs/PRODUCT_NORTH_STAR.md`, `docs/phases/PHASE-04.md`

The MVP is the smallest WeCoder.AI that can provide a real coding-agent experience. It is not the README. It is not an AI company. It is not a multi-agent operating system.

---

## 1. One-sentence MVP

A developer runs `wecoder` in a repository, describes a concrete software change, and gets a real file-level implementation from a single agent using a local or bring-your-own-key model, with a readable plan, a visible diff, and a workspace the agent is not allowed to escape.

---

## 2. Why this cut

The vision includes teams, debate, routers, memory, and benchmarking. None of those matter if WeCoder cannot:

- see a project
- call a model through a stable interface
- edit the right files
- run a command
- tell the user what happened

A dual-agent Architect that cannot write files is a chatbot. A router with one broken agent is a switchboard to nowhere. The MVP proves the only loop the rest of the product is allowed to decorate.

---

## 3. MVP features

### 3.1 Installable Python CLI

- Package name: `wecoder`
- Python 3.11+
- Invocable as `wecoder` and `python -m wecoder`
- Commands sufficient to configure and run one task (see user journey)

### 3.2 Configuration

- User-level and/or project-level config (TOML)
- Selected model provider and model id
- Workspace root (default: current directory)
- Log level
- Session budgets: max turns, max tokens (simple integers)

API keys are read from the environment or from a gitignored user config. They are never committed and never printed in full.

### 3.3 Model abstraction with two providers

- `ModelProvider` interface (complete, stream, usage)
- **Ollama** (local; offline-first path)
- **OpenAI-compatible HTTP** (covers OpenAI, many gateways, and a large set of “just give me a base URL” servers)

The agent depends only on the interface. Adding Claude or Khwarizmi later must not require rewriting the MVP loop.

### 3.4 Workspace and context

- Bind to a single root directory
- Honor ignore rules (`.gitignore` + WeCoder defaults: `.git`, `node_modules`, `.venv`, build artifacts)
- List and read files with size limits
- Build a **budgeted** project sketch for the model (language hints, top-level tree, requested files) — never the whole repo

### 3.5 Tool system

Minimum tools:

| Tool | Purpose |
|------|---------|
| `list_dir` | Explore the tree |
| `read_file` | Read a text file (capped) |
| `write_file` | Create or replace a text file inside the workspace |
| `edit_file` | Apply a targeted replacement inside a file |
| `search_text` | Find a pattern in the workspace |
| `run_command` | Run a bounded command in the workspace cwd |

Every tool returns a structured result. Every mutating tool is confined by the workspace jail.

### 3.6 Single coding agent loop

One role: **Developer**.

Loop:

1. Ingest user task + budgeted context
2. Plan (short, user-visible)
3. Call tools until done, blocked, or a budget is exhausted
4. Produce an `AgentResult`: summary, files touched, commands run, final status

The model may be local or cloud. There is no second agent, no debate, and no automatic team generation.

### 3.7 User-visible outcome

After a run the CLI prints:

- status (`succeeded`, `failed`, `blocked`, `budget_exceeded`)
- plan / summary
- list of modified paths
- a unified diff or an instruction to inspect the working tree
- usage (tokens in/out if the provider reported them)

### 3.8 Baseline safety (MVP-grade, not enterprise-grade)

Already required in the MVP:

- path jail
- secret-file denylist for automatic reads (`.env`, private keys, credential files)
- command timeout
- turn/token caps
- no execution outside the workspace cwd

Not required in the MVP (Phase 06):

- interactive approve/reject/review flow
- Git commit / reset / branch management
- dependency-install policy UI

A user running the MVP on a precious repository is expected to use their own Git hygiene (commit or stash first). The product will take that over in Phase 06. This limitation must be documented in the CLI help and phase handoff, not hidden.

### 3.9 Tests that prove the loop

- Fake model + temp project: agent writes a requested file and stops
- Path jail refuses `../` escape
- Ollama and OpenAI-compatible providers conform to the interface with HTTP stubs
- CLI `wecoder run` on the fixture project exits with a structured result

---

## 4. Why each included feature matters

| Feature | Why it is in the MVP | What happens if we omit it |
|---------|----------------------|----------------------------|
| CLI | Developers will not adopt an unrunnable library | The product is a folder of intentions |
| Config | Models and keys must be selectable | Hardcoded vendor demo |
| Model interface + 2 providers | Offline path + escape hatch to a strong cloud model | Locked to one brain; README becomes a lie |
| Workspace jail | The first tool is already dangerous | Unacceptable risk |
| Budgeted context | Local models die; cloud models get expensive | Unusable or insolvent |
| File + search tools | Coding is file work | Chatbot |
| Shell tool | Real projects need `pytest`, `ls`, `python` | Toy editor |
| Single agent loop | Proves the product | Framework without a job |
| Visible diff/summary | Trust | Users cannot review work |
| Token report | Cost is real even for one agent | Surprise bills |
| Automated tests | Next phases will break the loop otherwise | Unmaintainable greenfield |

---

## 5. Features explicitly excluded from the MVP

These are real product ideas. They are forbidden in Phases 01–04.

| Excluded feature | First allowed phase | Why it waits |
|------------------|---------------------|--------------|
| Architect / dual-agent critique | 07 | Nothing to critique until one agent writes code |
| Together / Workers / Consensus / Debate | 10 | Mode zoo before a working employee |
| Dynamic team generation | 10 | Role play is not a substitute for tools |
| Intelligent model router | 09 | Need usage data and >1 serious provider |
| Claude / Gemini / Grok / Kimi / Khwarizmi first-class SDKs | 09 | OpenAI-compatible covers many; dedicated adapters later |
| Persistent global memory | 11 | Session messages are enough |
| Human approval UI | 06 | Needed before multi-agent, not before first demo |
| Git commits, branches, rollback | 06 | User Git is acceptable for MVP; product Git needs policy |
| Dedicated test-repair controller | 05 | Agent may run tests via shell; specialized loop comes next |
| Security / performance reviewer roles | 11 | Specialists need a working change to review |
| Solution benchmarking | 12 | Cannot compare solutions we cannot produce |
| Web UI / IDE extension | 12+ | Expensive surface; CLI proves value |
| Vector database / RAG platform | 11+ if ever | Context packer first |
| Container sandbox / cloud runners | 12 if needed | Jail + timeout first |
| Multi-tenant SaaS, billing, SSO | 12 | No product yet to sell |
| Universal language matrix (Dart, Java, C#, C++, Rust, Go, Flutter, Godot, Android, .NET) | 12 | Extensibility, not a launch checklist |
| Automatic dependency installation | 06 at earliest, still gated | High risk, low MVP value |
| Marketplace / MCP plugin store | Future, unscheduled | Tool registry is enough |

The MVP agent **may** run `pytest` or `npm test` through `run_command` if the user asks and the command is inside the workspace. That is not the Phase 05 test subsystem.

---

## 6. User journey

### 6.1 First-time setup

```text
$ pip install -e .          # or the documented equivalent
$ wecoder init
```

`init` writes a project config (for example `.wecoder/config.toml`) with:

- provider = `ollama` (default) or `openai_compat`
- model id
- budgets
- comments explaining how to set `OPENAI_API_KEY` / `OLLAMA_HOST`

### 6.2 Offline path

```text
$ ollama pull qwen2.5-coder
$ wecoder models list
$ wecoder run "Add a README section describing how to run tests"
```

### 6.3 Cloud path (BYOK)

```text
$ export OPENAI_API_KEY=...
$ wecoder run --provider openai_compat --model gpt-4.1-mini "Fix the failing test in tests/test_health.py"
```

### 6.4 What the user sees

1. Workspace confirmation (`Using /path/to/my-app`)
2. Short plan
3. Tool activity (read / edit / command) as it happens
4. Final status, diffstat, usage
5. Exit code: `0` on success, non-zero on failure/block/budget

### 6.5 What the user does next

- Reviews the working tree (and their own Git)
- Re-runs with a follow-up instruction in the same or a new invocation
- If unhappy, discards the working tree changes themselves

Phase 06 replaces that last bullet with `wecoder rollback`.

---

## 7. Acceptance criteria

The MVP is accepted when all of the following are true on a clean machine with the test suite and one manual walkthrough.

### Automated

1. `pytest` for Phases 01–04 is green without network access.
2. A FakeModel-driven integration test on a fixture Python project:
   - creates or modifies a requested module
   - adds or updates a test file when asked
   - does not write outside the temp workspace
3. Jail tests reject path escape and secret-file reads.
4. Both providers pass contract tests with stubbed HTTP.
5. CLI help runs; `wecoder run --help` documents the offline-first default and the “no product Git yet” limitation.

### Manual (real projects)

Use three repositories, not one toy:

| # | Project | Task | Pass condition |
|---|---------|------|----------------|
| 1 | WeCoder's own **fixture mini-app** (in-repo, tiny FastAPI or CLI) | Add `/health` (or equivalent) + test | File exists, test command can be run by the user, output is coherent |
| 2 | A **small public Python repo** cloned locally | “Add a `--version` flag” or “fix this documented bug” | Diff is relevant; no writes outside the clone |
| 3 | A **small Node or Python app the implementer already has** | One concrete feature the implementer would have done by hand | Implementer would keep the patch after review |

Manual runs may use Ollama or a BYOK cloud model. At least one successful offline (Ollama) run is required to claim “offline-first”.

### Explicit non-criteria

- The agent does not need to beat Claude Code or Cursor on SWE-bench.
- The agent does not need to recover from every failure (that is Phase 05).
- The agent does not need to open a PR.
- The agent does not need a second model in the loop.

---

## 8. How the MVP is tested on real software projects

### Fixture project (automated + manual)

A tiny in-repo application, created in Phase 04 under something like `tests/fixtures/mini_app/`:

- a few Python modules
- a test that fails until a missing function is implemented, **or** a green suite the agent must extend
- a README

This fixture is the regression spine for Phases 04–06.

### External projects (manual protocol)

1. Clone into a throwaway directory.
2. Create a user branch / stash so the implementer can reset (human Git, since product Git is later).
3. Run one specified `wecoder run "..."` prompt.
4. Record: did it plan, which files changed, did it escape, did it touch secrets, did the change work, token usage.
5. Reset the clone.

Do **not** point the MVP at this WeCoder.AI planning repository as the only test. The fixture and at least one external repo are required.

### Failure logging

Every failed manual run should answer:

- Was this a model quality miss, a tool miss, a context miss, or a product bug?
- Did we hit a budget cap?
- Did the jail or denylist fire correctly?

Only product bugs block MVP acceptance. Model quality misses are documented, not treated as Phase 04 scope expansion.

---

## 9. What “genuinely useful” means here

Genuinely useful does **not** mean “autonomous software company”.

It means:

- faster than doing a small, well-specified change entirely by hand, for a user who reviews diffs
- usable on a laptop
- usable with a local model for small tasks
- usable with a stronger cloud model when the user chooses
- safe enough that a careful developer will try it on a branch of a real project

If that bar is not cleared, later phases are not allowed to add agents. They will only add cost.

---

## 10. Handoff after MVP

When Phase 04 is accepted:

- Phase 05 specializes execution and repair so “run the tests” is a product feature, not a hope.
- Phase 06 adds approval and Git so the MVP can be used on repositories the user cares about.
- Phase 07 may introduce the Architect.

No phase after 04 may redefine the MVP to include itself.
