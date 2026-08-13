# WeCoder.AI — Commercial Strategy

**Status:** High-level commercial path. Not a financial forecast.  
**Principle:** become useful and cheap to operate before becoming a business.  
**Companion documents:** `docs/MASTER_PLAN.md`, `docs/PRODUCT_NORTH_STAR.md`, `docs/MVP.md`

This document does not promise profit, users, or valuation. It describes how WeCoder.AI *could* become economically sustainable if the product is real, and which commercial ideas are forbidden until then.

---

## 1. Target users

### Beachhead (first 50 users)

Individual developers and technical founders who:

- live in the terminal
- already use Git
- feel vendor lock-in or API cost from existing coding copilots
- want local/offline capability, or want to mix local and cloud models
- will tolerate a CLI and will review diffs

These people can be reached without a sales team. They are also the only people who can tell us whether the loop works.

### Expansion (after the loop is trusted)

- Small product teams that want a shared policy (approvals, cost caps) and the same CLI
- Developers in constrained environments (low connectivity, privacy-sensitive code, air-gapped-ish labs)
- Educators and student teams who need a free local path

### Not a beachhead

- Enterprises that buy through procurement
- Non-technical consumers
- “Replace your engineering department” buyers

Those markets require trust, support, and compliance WeCoder will not have for a long time. Chasing them early is how the project becomes a slide deck.

---

## 2. Core customer problem

Existing tools force a bad choice:

1. **A strong hosted copilot** that is excellent, expensive or metered, and tied to one vendor’s model and workspace.
2. **A raw model chat** that cannot see the repo, cannot run tests, and cannot be reviewed as a patch.
3. **A research multi-agent stack** that looks like a team and behaves like a science fair.

The job to be done:

> “On *this* repository, with *the models I already have*, help me land a change I am willing to keep — without locking me to one vendor or shipping my tree to a product I do not control.”

WeCoder is a product if it does that job. It is not a product if it only describes a team of agents.

---

## 3. Differentiation

Differentiation is a combination. Any single piece is already owned by someone else.

| Claim | Who already has a version | WeCoder’s version only counts if… |
|-------|---------------------------|-----------------------------------|
| Coding agent in your repo | Aider, Claude Code, Codex, Cline, Continue | The loop is reliable and simpler to reason about than a pile of prompts |
| Multi-model | OpenRouter, Continue, some IDEs | Providers are first-class and the *agent* is vendor-neutral |
| Offline / local | Ollama + various wrappers | A local model can complete a small real task, not just chat |
| Multi-agent team | CrewAI, AutoGen, Wegent, research demos | A second role improves outcomes after one agent already works |
| Autonomous SWE | Devin and similar | We do **not** compete here first; too expensive, too much trust |

**Positioning we can defend:**

> WeCoder.AI is the local-first, model-agnostic software team you run on your own repo. Start with one agent. Add models and roles when they pay for themselves.

**Positioning we cannot defend today:**

> “Beta dual-agent framework that replaces your developers.”

The current README leans toward the second. Commercial credibility requires the first.

---

## 4. Competitors and categories

WeCoder does not need a unique category name. It needs a clear *comparison set*.

### Direct substitutes (what a beachhead user already tries)

- **Aider** — mature CLI coding agent, Git-native, pragmatic. Highest bar for our MVP.
- **Claude Code / OpenAI Codex CLI** — excellent single-vendor agents.
- **Cline / Continue / similar IDE agents** — close to the editor, often multi-model.
- **Cursor / Windsurf** — full IDE products, hosted gravity, strong UX.

### Adjacent, not first substitutes

- **Copilot** — completion and chat inside GitHub’s world.
- **Devin / Cognition-class** — hosted autonomous SWE. Different buyer and cost structure.
- **LangGraph / CrewAI / AutoGen** — frameworks for builders, not a coding product.
- **Wegent (wecode-ai)** — agent-team OS with a web console. Different architecture and product surface. Not this repository.

### Implication

We do not win by adding more agents than Wegent or more polish than Cursor in year one. We win by being the best **local, recoverable, vendor-neutral team-shaped coding tool** for people who already have a terminal and a repo.

If we cannot beat “just use Aider” on a subset of jobs (offline, multi-model, explicit team roles, cost visibility), we do not have a business. We have a fork of an idea.

---

## 5. Free / open-source strategy

The repository is already **MIT**. That should remain the strategy for the core.

### Keep open (forever, unless a later ADR reverses this with a real reason)

- CLI
- Model interface and provider adapters
- Tool system, agent loop, Leader mode
- Safety policy engine and Git checkpoints
- Docs and fixture projects

### Why open-source the core

- Developers will not send their repositories to an unknown hosted agent.
- Credibility in this category is “I can read what will run on my machine”.
- Distribution is free: GitHub, `pip`/`uv`, word of mouth.
- Contributors can add providers (including Khwarizmi) without a partnership contract.
- MIT is compatible with later paid *services* around the core.

### What open-source is not

- A growth hack that replaces a working product.
- A reason to accept every feature PR that implements Phase 12 early.
- A promise that hosted services, if they ever exist, are also free at unlimited scale.

Community strategy with near-zero budget:

- Ship something pip-installable.
- Write a short, honest README once Phase 04 exists (no false Beta badges).
- Publish 2–3 recorded runs on real public repos.
- Be present where Aider/Cline users already complain about vendor lock-in and cost.
- Accept provider adapters and language runners that pass contract tests.

Do not buy ads. Do not staff a “developer relations organization”. Do not launch a Discord before there is a CLI worth discussing.

---

## 6. Potential paid features

Charge only for value that is expensive to provide or clearly extra.

| Candidate | Why someone might pay | When it becomes honest to offer |
|-----------|----------------------|----------------------------------|
| Hosted model router with budget policies | Teams want “cheap model first, escalate if needed” without building it | After Phase 09 exists locally |
| Managed isolated runners | Users who do not want agents executing on their laptop | After the local jail is trusted and there is demand |
| Team policy / audit log | Shared approvals, retention, SSO later | After Phase 06 and real team users |
| Priority support / assisted onboarding | Consultants and small teams | After we can actually support them |
| Khwarizmi or other premium local models as a *separate* product | Users want a stronger offline brain | Never bundled as a WeCoder rewrite; sold or shipped by that project |
| Packaged desktop/TUI distribution | Convenience | After CLI is stable |
| Enterprise policy pack | Air-gapped install, allowlists, retention | Much later |

### Do not sell

- The right to use the open-source CLI.
- “Unlimited magic teams” that secretly burn our API keys.
- Benchmark theater (“we generate 12 solutions”) as a default paid SKU — it is a cost multiplier.

---

## 7. Possible subscription structure (later, hypothetical)

These are **shapes**, not prices and not a commitment.

### While validating (NOW / NEXT)

**$0.** User pays their own model provider or uses Ollama. WeCoder’s marginal cost per user should be approximately **zero**.

### If a hosted layer is ever justified

A conservative three-tier sketch:

1. **Community (free)** — full local product, BYOK, GitHub issues.
2. **Pro (flat monthly, individual)** — optional hosted router, synced policy, email support, maybe a nicer packaged client.
3. **Team (per seat, small)** — shared audit, admin policy, cost caps across a small org.

Usage-based add-on **only** for *our* hosted compute (router, runners), never as a silent markup on the user’s own OpenAI/Anthropic keys if we are merely proxying them. Proxying user keys is a trust and liability problem. Prefer BYOK even in Pro.

No free-tier that gives away *our* GPU or *our* foundation-model bill. That is how similar products die.

---

## 8. Usage-based cost considerations

Almost all variable cost in this category is **someone’s model bill**.

### Who should pay inference

| Path | Who pays | WeCoder COGS |
|------|----------|--------------|
| Ollama / LM Studio / local OpenAI-compatible | User’s electricity and hardware | ~0 |
| User’s OpenAI / Anthropic / Gemini / etc. keys | User | ~0 |
| WeCoder-hosted models or WeCoder-paid router | WeCoder | High; only with a budget and a price |

**Rule:** do not put WeCoder in the position of paying foundation-model APIs for free users.

### Product behaviors that destroy margins (or user trust) later

- Unbounded retries
- Full-repository context
- Debate mode with five frontier models by default
- Benchmarking four complete implementations for a typo fix
- Hidden tool loops that keep calling the model after the user thinks it stopped

Phases 03, 08, and 09 exist so these are measurable and capped *before* any hosted offering.

### Cost architecture that keeps a future business honest

- Every session has a usage ledger (Phase 08).
- Every collaboration mode has a budget (Phase 10).
- The router optimizes for “cheapest model that can do this class of job” (Phase 09).
- Expensive modes are opt-in.

---

## 9. Cloud vs local execution

| Concern | Default | Cloud later only if |
|---------|---------|---------------------|
| Product runtime | Local CLI | Users ask to run untrusted jobs off-laptop |
| Model inference | Local or BYOK | We have a model (e.g. Khwarizmi) people will pay to rent |
| Storage of sessions | Local SQLite / files | Team wants shared history and accepts the privacy trade |
| Auth | None | There is a team SKU |
| Build/test isolation | Process jail | Jail is insufficient and users pay for stronger boxes |

Cloud is a **product option**, not the architecture. A cloud-first WeCoder would compete with better-funded hosted agents on their strongest ground, while paying rent WeCoder cannot afford.

---

## 10. Model API cost considerations

- Prefer small/cheap models for ranking files, classifying task type, writing commit messages, and summarizing traces.
- Prefer the user’s strongest model for architecture and final code on hard tasks.
- Do not call N models “for quality” until Phase 12 benchmarking, and then only with a numeric budget.
- Cache nothing sensitive in a third-party observability vendor by default.
- Estimate cost from provider price tables the user can edit. Do not pretend we know every vendor’s price.

Khwarizmi, if it becomes a strong local model, is commercially interesting because it can **reduce** API spend. That is a reason to keep the provider slot open. It is not a reason to delay the MVP until Khwarizmi exists.

---

## 11. Customer acquisition with near-zero budget

Practical sequence:

1. **Make a demo that is a Git diff**, not a slide.
2. Publish the CLI and three honest write-ups: a success, a failure, and a cost breakdown.
3. Post where practitioners already compare Aider / Cline / local models (GitHub, relevant subreddits, HN only when the MVP is real).
4. Add provider adapters that other people want (the contributor acquires themselves).
5. Talk to every user who files an issue. There will not be many at first; that is a feature.

Avoid:

- Launching on Product Hunt with a Beta badge and no `pip install`
- Influencer seeding
- “AI software company in a box” videos
- Partnership theater with model vendors

---

## 12. Early-user strategy

Goal: **10 developers who complete at least one real task they keep.**

How:

- Personal networks of the maintainers
- A short “office hours” offer in the README once Phase 04 ships
- Watch one user share their screen; fix the first 10 papercuts
- Keep a manual log: task, repo type, provider, outcome, tokens, would-they-use-again

Early users are not a funnel. They are the specification for Phases 05–08.

Graduation criterion to even discuss paid features: several unrelated users run WeCoder more than once on purpose.

---

## 13. Validation strategy

Validate in this order. Do not skip ahead.

| Stage | Question | Evidence |
|-------|----------|----------|
| Loop | Can one agent land a change on a fixture and one external repo? | Phase 04 acceptance |
| Trust | Will a careful developer run it on a branch of a real project? | Phase 06 + user interviews |
| Preference | Do they run it a second time without us asking? | Repeat usage |
| Differentiation | Do they choose it *because* of local / multi-model / team — not just because it is ours? | Qualitative notes |
| Willingness to pay | Will anyone pay for router / runners / support? | Ask only after repeat usage |

Vanity metrics to ignore until then: GitHub stars, landing-page visits, number of agents in a diagram, number of supported model logos.

---

## 14. Metrics to track

Track a short list. If it is not used to change the product, do not build a warehouse for it.

### Product (from Phase 04, locally; optional anonymous opt-in much later)

- Tasks started / completed / blocked / budget-exceeded
- Median turns and tokens per completed task
- Share of tasks that touch tests
- Jail or policy denials (are they correct or noisy?)
- Provider mix (Ollama vs cloud)

### Trust (from Phase 06)

- Share of sessions with a checkpoint
- Rollbacks per 10 sessions (high is not always bad; zero with many failures is suspicious)
- Approval reject rate

### Commercial (only if a paid surface exists)

- Paying accounts
- Gross margin after inference and runners
- Support hours per paying account
- Churn after first invoice

### Quality of evidence

Prefer retained patches and repeat invocations over star counts.

---

## 15. Path from first users to sustainable revenue

A realistic, boring path:

1. **Phases 01–04.** Open-source MVP. COGS ≈ 0. No revenue. Success = real tasks completed.
2. **Phases 05–07.** Trust + README dual-agent. Still free. Success = people run it on purpose.
3. **Phases 08–09.** Cost visibility + router. Still free locally. We learn which models people actually use.
4. **If and only if** repeat users ask for hosted routing, team audit, or isolated runners: a small Pro/Team SKU that does not tax BYOK.
5. **Khwarizmi or other local models** can become a separate revenue line for the sibling project. WeCoder remains the client.
6. Enterprise features last, if ever.

### Paths that are not realistic for this repository right now

- Raising a seed round to build a Devin competitor
- Hiring a sales team
- Forecasting ARR
- Building multi-region inference

### Sustainability definition

WeCoder is commercially healthy if:

- the open-source core stays useful without our paying anyone’s tokens
- any hosted add-on has **positive gross margin**
- maintainers are not financing users’ multi-agent experiments
- revenue, if any, comes from people who already succeeded locally

That is a small, durable business or a healthy open-source project with optional paid edges. Both are acceptable. A money-losing autonomous-engineer fantasy is not.

---

## 16. Risks to the commercial story

- **Aider-class tools remain better and simpler.** Then WeCoder should stay a focused open-source experiment, not a company.
- **Frontier vendors give away excellent CLIs.** Differentiation must stay local + multi-model + team + recoverability.
- **We host inference too early.** This is the fastest way to go broke.
- **We close-source the core** to “have a business”. In this category that usually just removes the reason to trust us.
- **We wait for Khwarizmi** to be commercially ready. WeCoder must stand alone.

---

## 17. What this strategy forbids in engineering

Commercial ambition is not a license to implement:

- Stripe, SSO, or a marketing site as Phase 01
- A control plane
- A default path that bills us for tokens
- Feature gates that disable the local loop

Those ideas, if they ever happen, belong in Phase 12 after the north-star loop is real.
