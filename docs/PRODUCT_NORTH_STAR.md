# WeCoder.AI — Product North Star

**Status:** Product definition. Not an implementation plan.  
**Companion documents:** `docs/MASTER_PLAN.md`, `docs/MVP.md`, `docs/COMMERCIAL_STRATEGY.md`

---

## What WeCoder.AI is

WeCoder.AI is a **local-first AI software development team**.

The user does not chat with a novelty bot. The user assigns work to a system that can inspect a repository, plan a change, edit files, run commands, test the result, and present a recoverable outcome.

In the long term, that system is a coordinated team of specialized agents backed by interchangeable models. In the first useful version, it is one disciplined coding agent with a model-agnostic interface and real tools. The team is the destination. The reliable loop is the north star that makes the team worth building.

The product lives where the code lives: on the developer's machine, against a real working tree.

---

## What WeCoder.AI is not

- **Not a chatbot.** Conversation is an interface, not the product. If the system cannot change a repository, it has failed.
- **Not a single-vendor coding copilot.** It must not be “the OpenAI app”, “the Claude app”, or “the Khwarizmi app”.
- **Not Khwarizmi AI.** Khwarizmi is a sibling intelligence project. WeCoder may call it later through the model interface. The two products are not merged.
- **Not a multi-agent research framework.** CrewAI, AutoGen, and LangGraph are not the product. Users should not have to learn an orchestration library to fix a bug.
- **Not a hosted IDE or cloud OS.** Cursor, Replit, and Devin occupy that space. WeCoder can grow a UI later. It does not start as a SaaS workspace.
- **Not an autonomous employee that hides its work.** The user remains accountable for the repository. Diffs, approvals, and rollbacks are part of the experience.
- **Not a universal compiler farm.** Supporting every language on a slide deck is not a goal. Completing work in a few real stacks is.
- **Not a landing page with badges.** The current README's “Beta” badge is not the product.

---

## Who it is for

### Primary user (NOW and NEXT)

A software developer or technical founder who:

- already has a repository
- is comfortable with a terminal
- wants help implementing, modifying, and repairing code
- cares about privacy, cost, or not being locked to one model vendor
- is willing to review a diff before treating work as done

Typical contexts: side projects, early-stage products, local automation, consulting work, offline or low-connectivity environments, teams that already run Ollama or bring their own API keys.

### Secondary user (LATER)

Small product teams that want a shared local/team workflow: the same agent loop, visible cost, and policy around dangerous operations.

### Not the first user

- Non-technical operators who need a fully hosted “describe an app, get a company”
- Enterprises that require SSO, VPC, and compliance paperwork before touching a CLI
- Researchers who want a paper-friendly multi-agent sandbox more than a working patch

Those audiences may matter later. They do not define the first product.

---

## The core user experience

The user is inside a project directory and says what they want.

```text
$ cd my-app
$ wecoder run "Add a /health endpoint and a test for it"
```

What must happen, every time, once the MVP exists:

1. WeCoder binds to this workspace and does not wander the disk.
2. It inspects enough of the project to understand how to make the change.
3. It plans in language the user can read.
4. It edits files and, when needed, runs commands.
5. It shows what it did: summary, changed paths, and a diff.
6. If something fails and the failure is visible, it tries a bounded repair.
7. The user can keep, inspect, or undo the work.

As the product matures, the same surface grows without changing its meaning:

- “Who is working?” becomes visible (Developer, then Architect + Developer, then a task-shaped team).
- “Which model did this, and what did it cost?” becomes visible.
- “May I install this dependency / delete this file / run this command?” becomes an explicit question.
- “Show me the checkpoint and roll back” becomes a first-class action.

The user should feel like they are directing a careful junior team, not watching a slot machine.

---

## The main competitive advantage

The market already has strong single-agent tools and strong hosted tools.

WeCoder.AI's advantage is the **combination**, not any one slogan:

| Advantage | Why it is real only if we earn it |
|-----------|-----------------------------------|
| **AI team, not one voice** | Valuable after one agent works and a second role (Architect) actually improves outcomes. |
| **Model-agnostic** | Valuable only if providers are interchangeable without rewriting the agent. |
| **Offline-first** | Valuable only if a local model can complete a small real task with no cloud dependency. |
| **Recoverable by default** | Valuable only if checkpoints and diffs exist before multi-agent fan-out. |
| **Cost-visible and cost-disciplined** | Valuable only if context is budgeted and multi-model work is optional, not the default. |
| **Local and private** | Valuable only if secrets are not ingested or logged casually. |

If the product ships as “yet another chat CLI over one API”, it has no advantage. If it ships as “an unrecoverable swarm that spends $12 to rename a function”, it has a negative advantage.

The advantage we protect first is: **a trustworthy local loop that can later host a team of models.**

---

## What must be true for the product to be considered successful

These are product truths, not vanity metrics.

1. A developer who is not the author can install WeCoder and complete a non-trivial change on their own repository.
2. The same task can be run with a local model or a cloud model by changing configuration, not code.
3. Failed commands and failed tests produce a repair attempt and an honest final status, not a shrug and a wall of tokens.
4. Every mutating session has a visible diff and a rollback path.
5. Destructive or irreversible actions can be rejected by a human.
6. Adding a new model provider does not require touching orchestration.
7. Khwarizmi AI, if and when it is ready, can appear as one more provider.
8. A user can see what was spent (tokens, estimated money, number of turns).
9. The open-source core remains usable without paying WeCoder for model inference.
10. At least a small group of real users choose it for actual work, not for a demo video.

Until (1)–(4) are true, later vision items are not success. They are unfinished sketches.

---

## What should never be sacrificed for unnecessary features

These are non-negotiable. New phases, modes, and commercial ideas lose if they conflict with this list.

1. **The closed loop.** Understand → change → run/test → report. No feature is allowed to replace this with conversation-only output.
2. **Model independence.** No vendor SDK in the agent core. No “works best only if you use our model” as an architectural assumption.
3. **Workspace containment.** The product does not write outside the bound project without an explicit, later, carefully designed exception.
4. **Recoverability.** If WeCoder touched the tree, the user can see and undo it.
5. **Human authority.** The model proposes. The user owns the repository.
6. **Honest scope.** Do not advertise dual-agent, offline-first, or Beta unless that path works.
7. **Cost discipline.** Do not multiply models, debate rounds, or context dumps to look sophisticated.
8. **Separation from Khwarizmi.** Do not merge the coding product and the model project.
9. **Local usefulness without a cloud bill.** A disconnected user must still have a path.
10. **Phase discipline.** Do not implement FUTURE work because it is exciting. Implement it because the previous horizon is done.

---

## North-star test

When a decision is unclear, ask:

> Does this help a developer get a correct, reviewable, recoverable change in their own repository — with the model they already have — more reliably than they can today?

If the answer is no, it is not the north star. It can wait.
