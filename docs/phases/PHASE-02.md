# Phase 2 — Model Abstraction Layer

## Objective

Introduce a vendor-neutral `ModelProvider` interface and two working adapters — **Ollama** and **OpenAI-compatible HTTP** — plus a registry, shared types, usage accounting on each response, and contract tests with HTTP stubs.

After this phase the rest of WeCoder can call a model without knowing who hosts it. No agent loop yet.

## Why This Phase Exists

If the agent (Phase 04) talks to a vendor SDK, the product is permanently coupled. The roadmap’s multi-model vision, Khwarizmi port, and later router are all impossible without this seam. This phase exists *before* the agent on purpose (ADR-006, ADR-007).

## Current State

After Phase 01:

- Package, CLI, Settings, logging, tests exist
- Settings already contain `model.provider`, `model.model`, `model.base_url`, `model.api_key_env`
- No HTTP clients, no providers, no completion types

If Phase 01 is not done, stop and do Phase 01.

## Target State

- `wecoder.models` defines types + protocol + registry
- `ollama` and `openai_compat` providers implement the protocol
- `wecoder models list` shows registered providers and the configured default
- `wecoder models ping` (or `models check`) performs a *stubbed-in-tests* health check; live ping is optional and never required in CI
- A `FakeModel` exists in tests (and may live under `wecoder.models.providers.fake` marked as test/dev-only) implementing the same protocol
- Completions return usage (`input_tokens`, `output_tokens`) when the backend provides it, else zeros with `usage.estimated = true` only if you must count heuristically — prefer “unknown” over lying

## Scope

**In scope**

- Types: messages, tools-shaped placeholders (optional JSON schema field reserved for Phase 04), completion request/response, stream chunks, usage, capabilities
- Provider protocol
- Registry keyed by provider id
- Ollama adapter (chat API)
- OpenAI-compatible adapter (`/v1/chat/completions`)
- Config wiring from Settings
- CLI `models list` and a non-destructive check command
- Contract tests + HTTP mocks

**Out of scope**

- Agent loop, tools, workspace
- Native Anthropic/Gemini/Khwarizmi SDKs (Phase 09)
- Model router (Phase 09)
- Cost ledger / pricing tables (Phase 08)
- Streaming TUI
- Embedding APIs

## Architecture

```
Settings.model
    → ModelRegistry.create(settings) → ModelProvider
                                           ├─ complete(request) → CompletionResponse
                                           └─ stream(request)  → AsyncIterator[Chunk]

CLI models list  → registry.ids()
```

Providers are **in-process adapters**. They perform HTTP. They do not own retries beyond one clearly documented transport retry for idempotent connection failures (prefer zero retries in this phase).

## Components

| Component | Responsibility |
|-----------|----------------|
| Types | Dataclasses / pydantic models for messages and responses |
| `ModelProvider` | Protocol / ABC |
| `ModelRegistry` | id → factory |
| `OllamaProvider` | Local Ollama chat |
| `OpenAICompatProvider` | OpenAI-compatible chat |
| `ModelError` | Typed failures (auth, unreachable, bad request, timeout) |
| CLI `models` | Introspection |

## Interfaces / Contracts

### Identifiers

- `ollama`
- `openai_compat`

Do not alias `openai` as a separate provider class in this phase; document that OpenAI official API is `openai_compat` with the default base URL.

### Types (normative shape)

```text
Role: "system" | "user" | "assistant" | "tool"

Message:
  role: Role
  content: str
  name: str | None
  tool_call_id: str | None
  tool_calls: list[ToolCall] | None     # reserved; may be empty until Phase 04

ToolCall:
  id: str
  name: str
  arguments: str                        # JSON object text

Usage:
  input_tokens: int | None
  output_tokens: int | None
  raw: dict | None

ModelCapabilities:
  streaming: bool
  tool_calling: bool                    # advertise accurately; Ollama/OpenAI often true
  json_mode: bool

CompletionRequest:
  model: str
  messages: list[Message]
  tools: list[ToolSpec] | None
  temperature: float | None
  max_tokens: int | None
  stream: bool

CompletionResponse:
  message: Message
  usage: Usage
  finish_reason: str | None
  provider_id: str
  model: str
  raw: dict | None                      # never logged in full at INFO
```

### Protocol

```text
class ModelProvider(Protocol):
    id: str
    def capabilities(self) -> ModelCapabilities: ...
    async def complete(self, request: CompletionRequest) -> CompletionResponse: ...
    async def stream(self, request: CompletionRequest) -> AsyncIterator[CompletionChunk]: ...
    async def aclose(self) -> None: ...
```

Synchronous wrappers are allowed for CLI convenience but the interface is async.

### Defaults

| Provider | Default base URL | Auth |
|----------|------------------|------|
| `ollama` | `http://127.0.0.1:11434` | none |
| `openai_compat` | `https://api.openai.com/v1` | `Authorization: Bearer $API_KEY` from `settings.model.api_key_env` |

If `settings.model.base_url` is non-empty, it wins.

### Errors

```text
ModelError(WecoderError)
  ModelConfigError      # missing key, bad URL
  ModelAuthError        # 401/403
  ModelUnavailableError # connection refused, 503
  ModelTimeoutError
  ModelResponseError    # unparseable / unexpected payload
```

## Files Expected To Be Created

```
wecoder/models/__init__.py
wecoder/models/types.py
wecoder/models/base.py
wecoder/models/registry.py
wecoder/models/errors.py
wecoder/models/providers/__init__.py
wecoder/models/providers/ollama.py
wecoder/models/providers/openai_compat.py
wecoder/cli/models_cmd.py          # or equivalent module
tests/models/test_types.py
tests/models/test_registry.py
tests/models/test_openai_compat.py
tests/models/test_ollama.py
tests/models/test_contract.py
tests/models/fakes.py              # if FakeModel is test-only
```

`httpx` (async) is an acceptable new runtime dependency for the two adapters.

## Files Expected To Be Modified

- `pyproject.toml` — add `httpx` (pin a current stable)
- `wecoder/cli/app.py` — register `models` subcommands
- `wecoder/errors.py` — only if you re-export; prefer `models/errors.py` subclassing `WecoderError`
- `wecoder/config/settings.py` — only if Phase 01 missed a field the contract above requires
- Tests `conftest.py` — fixtures for a FakeModel / mocked transport

## Files That Must NOT Be Modified

- `LICENSE`
- Planning documents under `docs/` (except you must not “implement” them)
- Phase 01 public CLI behavior for `init` / `status` / `--help` except additive help text
- Do not add agent, tool, or workspace packages

## Dependencies

- Requires Phase 01 complete.
- Depends on Settings keys listed in Phase 01.
- No dependency on Phase 03+.

## Implementation Requirements

1. Registry returns a provider for `settings.model.provider` or raises `ModelConfigError` listing known ids.
2. Both adapters honor `base_url`, `model`, timeout (hardcode a sensible default, e.g. 120s, configurable later).
3. `openai_compat` fails with `ModelConfigError` if the API key env var is missing **when a request is made**, not at import time (so `models list` still works).
4. `ollama` does not require an API key.
5. Streaming is implemented or explicitly raises `NotImplementedError` wrapped as `ModelError` if you defer streaming internals — prefer implementing basic SSE/JSON streaming for OpenAI-compat and Ollama because Phase 04 UX benefits. If streaming is deferred, set `capabilities.streaming = False` and test that.
6. Do not log full prompts or responses at INFO. DEBUG may log sizes and model ids, not content, in this phase (stricter is fine).
7. Redact `Authorization` headers in any error that interpolates request data.
8. `FakeModel` can be scripted: queue of responses, records requests. Phase 04 will depend on this.

## Error Handling

- Transport errors → `ModelUnavailableError` with provider id and base URL (no key).
- HTTP 401/403 → `ModelAuthError`.
- Unexpected JSON → `ModelResponseError`.
- Never retry non-idempotent completed requests.
- Timeouts use the same error type on both providers.

## Security Requirements

- API keys only from env (or a future user-level config field that is not committed). Do not read keys from the project workspace in this phase.
- Do not write keys into `wecoder models` output.
- No prompt content in exceptions shown to the CLI at default log level.

## Performance Requirements

- Connection timeouts must exist. No infinite hang on a dead Ollama.
- Do not load model weights into this process.
- Do not prefetch models on CLI import.

## Cost Considerations

- No automatic completion on `status` or `list`.
- A live `models ping` must be explicit and send a tiny request (e.g. one-token completion or Ollama tags GET — prefer `GET /api/tags` for Ollama and a tiny chat for OpenAI-compat). Document that ping may cost money on cloud providers.
- CI never pings live services.

## Testing Requirements

- Contract test parametrized over FakeModel, stubbed Ollama, stubbed OpenAI-compat: `complete()` returns a `CompletionResponse` with `provider_id` set.
- OpenAI-compat unit test: given a fixture JSON body, parse assistant content and usage.
- Ollama unit test: same for Ollama’s chat response shape.
- Missing API key → `ModelConfigError` on `complete`, not on registry construction.
- Registry unknown provider → `ModelConfigError`.
- No tests make real network calls.

## Acceptance Tests

1. `wecoder models list` shows `ollama` and `openai_compat` and marks the configured default.
2. pytest models tests pass offline.
3. FakeModel is importable by tests and implements the protocol.
4. Source of agent-facing code (there should be none yet) does not exist; `wecoder/models` does not import `wecoder.agent`.

## Deliverables

- Model types, protocol, registry
- Two adapters + FakeModel
- CLI models commands
- Contract tests

## Definition of Done

- All acceptance tests pass.
- A later phase can depend only on `ModelProvider` + `ModelRegistry`.
- No agent, no tools, no extra vendors.

## Risks

- Implementing a mini-LangChain. **Refuse.**
- Treating streaming as a reason to add a web UI.
- Encoding OpenAI-only tool-call quirks into `Message` so tightly that Ollama cannot fit — keep fields optional.
- Calling out to the network in CI.

## Explicitly Deferred Work

- Anthropic / Gemini / Khwarizmi native adapters (Phase 09)
- Router, fallback chains (Phase 09)
- Pricing and spend estimates (Phase 08)
- Tool-calling end-to-end (Phase 04 will send `tools=` through this interface)

## Handoff To Next Phase

Phase 03 does not need models. Phase 04 will:

- build `CompletionRequest` from the session
- pass tool specs
- use FakeModel in integration tests

Do not change the protocol in Phase 03. If Phase 04 needs a small additive field, it may add it backward-compatibly.

---

## Implementation Prompt

```
You are implementing Phase 02 of WeCoder.AI and ONLY Phase 02.

Read first:
- docs/phases/PHASE-02.md
- docs/MASTER_PLAN.md
- docs/ARCHITECTURAL_DECISIONS.md (ADR-006, ADR-007, ADR-008, ADR-009, ADR-021, ADR-023)
- Inspect the repository. Phase 01 must already exist (package, Settings, CLI). If it does not, stop and report that Phase 01 is missing.

Implement ONLY the Model Abstraction Layer:
- ModelProvider protocol, shared types, registry, ModelError hierarchy.
- Adapters: ollama, openai_compat.
- FakeModel for tests.
- CLI: `wecoder models list` and an explicit optional check/ping that CI does not run live.
- Contract tests with HTTP stubs. No live API calls in default pytest.

Do not implement: agent loop, tools, workspace jail, router, extra vendors (Claude/Gemini/Khwarizmi), cost ledger, web UI.

Preserve existing Phase 01 CLI behavior (additive changes only).
Do not modify LICENSE or planning docs.
Do not start Phase 03 or 04.

After implementation, run relevant tests and linters.
Report files created/modified, test results, and failures.
Stop.
```
