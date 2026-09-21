# Candidate Implementation Notes & Architecture Summary

---

## 1. Multi-Stage AI Agent Architecture & Orchestration

`ExpenseClassifierAgent` builds all of its reusable state once, in the constructor, rather than
per request:

* `_toolCallingChatClient` — the injected `IChatClient` wrapped once via
  `chatClient.AsBuilder().UseFunctionInvocation().Build()`. This is the `Microsoft.Extensions.AI`
  middleware that runs the actual tool-calling loop against a live model: when the model requests
  `get_company_policy` / `get_spending_limits`, the wrapped client executes the bound delegate and
  feeds the result back automatically. `SimulationChatClient` never emits a function-call request,
  so the wrapper is a no-op there and the simulation and live code paths share one implementation.
* `CompanyPolicyTool.GetPolicy` and `SpendingLimitTool.GetSpendingLimits` are turned into
  `AIFunction`s with `AIFunctionFactory.Create(...)` once and stored in a `List<AITool>` reused by
  every Stage 1 call — this avoids re-running reflection over the tool methods' signatures on every
  request.
* Two `ChatOptions` instances (`_stage1Options` with `Tools` set, `_stage2Options` without) and two
  `const string` system prompts are also built once, so no prompt string concatenation happens per
  request either.
* `Classify` calls Stage 1 (`_toolCallingChatClient` + tools + policy prompt). If the returned
  category is `"Other"`, empty, or not one of the six known company categories, it falls back to
  Stage 2 (`_chatClient` directly, no tools, general-classification prompt). This exactly mirrors
  the workflow diagram: the fallback only fires when the primary policy agent fails to place the
  expense in a recognized bucket (e.g. a JetBrains license, which the policy tool doesn't itself
  enumerate as "Transportation/Food/etc.").
* Thread-safety: the agent is registered as a **singleton** and holds no per-request mutable
  state — the only shared mutable structure is `_cacheKeyLocks` (a `ConcurrentDictionary`), so
  concurrent calls are safe by construction.

### Structured, deterministic output
The model is asked to return a **minimal** JSON object (`category`, `subCategory`,
`extractedAmount`, `currency`, `merchant`, `confidenceScore`) — nothing else. `ComplianceStatus`,
`ComplianceNotes`, `ClassificationStage`, and `ExpenseDescription` are **never** taken from the
model's output; they're computed/assigned by the agent itself (see §3), matching the sequence
diagram's explicit "Agent -> Agent: Evaluate Compliance & Format ResponseDto" step. This means
compliance verdicts can't be broken by an LLM doing currency-threshold arithmetic badly, and stay
byte-for-byte consistent with what `SimulationChatClient` produces (both use the shared
`ComplianceEvaluator`). Response parsing is defensive: `ParseExtraction` strips any markdown
fencing/prose around the JSON object via regex before deserializing with
`PropertyNameCaseInsensitive = true`, so an imperfect live-model response doesn't hard-fail Stage 1
— it just triggers the Stage 2 fallback (or, if Stage 2 also can't be parsed, an `UpstreamAiException`
which is mapped to a 502 `ProblemDetails`, see §4).

---

## 2. Dependency Injection & Service Lifetime Strategy

| Service | Lifetime | Why |
|---|---|---|
| `CompanyPolicyTool`, `SpendingLimitTool` | Singleton | Stateless, pure functions returning static text — safe to share. |
| `IMemoryCache` (`AddMemoryCache()`) | Singleton (framework default) | Cache must be shared across all requests to be useful. |
| `AzureOpenAIClient` (live mode) | Singleton | The official client is documented as thread-safe and pools its own HTTP connections; recreating it per request/scope would repeatedly pay TLS/connection setup cost for no benefit — the classic "captive dependency" trap the assessment calls out, just inverted (a Scoped registration here would itself be the waste, since nothing about the client is request-specific). |
| `IChatClient` (both branches) | Singleton | Wraps the client above; itself stateless per call. |
| `IChatClient` (`SimulationChatClient`) | Singleton | Stateless, deterministic, no per-request state. |
| `IExpenseClassifierAgent` → `ExpenseClassifierAgent` | Singleton | Depends only on the singletons above plus `IOptions<T>`, and pre-builds its `AIFunction`/`ChatOptions`/function-invoking-client state in the constructor specifically so that work happens once, not per request. |
| `ExpenseClassifierOptions` | `IOptions<T>` (Configure) | Strongly-typed, validated-at-bind config instead of magic `IConfiguration["..."]` string lookups scattered through the agent. |

Because every dependency in the chain is a singleton, there are no captive-dependency risks (a
longer-lived singleton never holds a reference to a shorter-lived scoped/transient service).

**Offline/CI support**: `ExpenseClassifier:UseSimulation` in `appsettings.json` (default `true`)
switches the `IChatClient` registration between `SimulationChatClient` and the real Azure OpenAI
client — the agent code is completely unaware of which one it's talking to, since both are plain
`IChatClient` implementations. This is what let the whole two-stage/fallback/cache/batch pipeline
be built and tested (`dotnet test`, plus manual `curl` runs against all four README examples) with
zero API cost and zero network dependency on Azure OpenAI.

**A note on the supplied Azure OpenAI key**: this submission intentionally does **not** commit the
API key into `appsettings.json` (it's checked in as `""`, simulation stays the default). Committing
a live key to a Git repository — public or private — puts it in the permanent history and risks
leaking it. The live branch reads `AzureOpenAI:Endpoint` / `:ApiKey` / `:DeploymentName` from
standard ASP.NET Core configuration, so the key should be supplied out-of-band at runtime (e.g. the
`AzureOpenAI__ApiKey` environment variable, `dotnet user-secrets`, or Key Vault in production) —
never hard-coded in source control.

---

## 3. High-Performance Caching & Concurrency

**Key normalization** (`NormalizeCacheKey`): trims, lowercases, strips all punctuation (regex
`[^\p{L}\p{N}\s]` → space), then collapses repeated whitespace. `" Bolt ride to Victoria Island! "`
and `"bolt ride to victoria island"` both normalize to the same key, so they hit the same cache
entry — verified by `Classify_SecondCallWithSameNormalizedDescription_IsCacheHit`.

**Stampede prevention**: a `ConcurrentDictionary<string, SemaphoreSlim>` keyed by the same
normalized cache key gates the miss path — `GetOrAdd` then `WaitAsync`/`Release` around a
double-checked cache read. Concurrent requests for the *same* expense description block on one
semaphore and only the first one actually calls the AI stage(s); the rest see the now-populated
cache entry once they acquire the gate. (Trade-off, noted for production: the per-key semaphores
are never evicted from the dictionary, since removing one while another request might be waiting on
it is racy to do safely without a reference-counted keyed-lock implementation. For the bounded
input space of this assessment that's an acceptable amount of long-lived, tiny objects; at real
scale I'd reach for a proper keyed-lock library, e.g. `AsyncKeyedLock`, or move to
`Microsoft.Extensions.Caching.Hybrid`'s `HybridCache`, which has stampede protection built in.)

**Safe storage**: only a successfully constructed `ResponseDto` is ever passed to `_cache.Set(...)`
— parse failures and AI-stage exceptions never reach the cache line, so a transient upstream
failure can't get "stuck" as a bad cached answer. `Unverifiable` results (amount not found in the
text) *are* cached, since that's a legitimate, deterministic answer for that description, not a
failure state.

**Expiration**: `AbsoluteExpirationRelativeToNow` = `CacheDurationMinutes` (config, default 30) with
an additional `SlidingExpiration` (capped at 10 minutes) so hot entries stay warm without ever
exceeding the absolute TTL.

**Batch concurrency** (`ClassifyBatch`): `Parallel.ForEachAsync` over the item indices with
`MaxDegreeOfParallelism` bound to `ExpenseClassifier:MaxBatchConcurrency` (config, default 5) and
the request `CancellationToken` wired into `ParallelOptions`. Results are written into a
pre-sized `ResponseDto[]` by index (not a concurrent collection), which both avoids any
synchronization on the hot path and guarantees the response list stays in the same order as the
request's `Items` list — verified by `ClassifyBatch_AggregatesSummaryAcrossCurrenciesAndStatuses`
and `ClassifyBatch_RespectsBoundedConcurrency`. Every batch item still goes through the same
`Classify` cache-aside path, so duplicate line items within one batch (or across batches) reuse a
single upstream call.

---

## 4. Resilience, Error Handling & API Robustness

* **Client input errors** (empty/whitespace `description`, empty/null batch `items`, or any batch
  item with an empty `description`) are validated in `Program.cs` *before* the agent is invoked, and
  return `400 Bad Request` with an RFC 7807 `ProblemDetails` body (`Title`/`Detail`/`Status`).
* **Upstream AI failures**: each stage's chat-client call is wrapped in a try/catch inside
  `CallStageAsync` — a thrown exception (network error, malformed tool response, etc.) is logged and
  treated as "no result for this stage", which lets the pipeline still attempt the fallback stage
  rather than failing the whole request outright. Only if *both* stages fail to produce a parseable
  result does the agent throw `UpstreamAiException`, which a global `UseExceptionHandler` middleware
  in `Program.cs` maps to a `502 Bad Gateway` `ProblemDetails` (distinct from the `400`s above, and
  distinct from an unexpected `500` for anything else unhandled) — so a client can tell "you sent us
  something invalid" apart from "we couldn't get a good answer from the AI service" apart from "we
  broke".
* `OperationCanceledException` is explicitly rethrown (not swallowed as a stage failure) so that
  request cancellation propagates correctly instead of being misreported as an upstream AI error.
* `CancellationToken` flows from the Minimal API endpoint parameter through `Classify`/
  `ClassifyBatch`, into every `IChatClient.GetResponseAsync` call and into `ParallelOptions` for the
  batch path.
* `<Nullable>enable</Nullable>` is already on in both projects; the solution builds with **zero**
  compiler warnings (`dotnet build ExpenseClassifier.slnx`).

---

## 5. Production & Enterprise Scale Roadmap

At ~100,000 expense claims/day (~1.2 req/s average, with bursty batch traffic), the changes I'd
prioritize:

* **Distributed, semantic cache** — swap `IMemoryCache` for `HybridCache` backed by Redis, so cache
  hits are shared across horizontally-scaled instances instead of being per-process. Layer in
  semantic/embedding-based cache lookups (e.g. a vector store like Qdrant/Azure AI Search) so
  near-duplicate descriptions ("Bolt to VI" vs "Bolt ride to Victoria Island") hit cache too, not
  just exact-normalized matches.
* **Async batch processing via a queue** — for large batch submissions, accept the request, enqueue
  items onto Azure Service Bus / a durable queue, return `202 Accepted` with a status URL, and let a
  pool of workers (still bounded-concurrency, but now horizontally scalable) drain the queue. This
  decouples batch size from a single HTTP request's timeout budget.
* **Managed Identity** for the Azure OpenAI client instead of an API key in configuration — removes
  a long-lived secret from the deployment entirely.
* **Resilience policies** — wrap the `IChatClient` with `Microsoft.Extensions.Http.Resilience` /
  Polly (retry with jitter on 429/5xx, circuit breaker, timeout) rather than the single try/catch
  used here, plus honoring `Retry-After` on Azure OpenAI rate-limit responses.
* **Observability** — OpenTelemetry tracing/metrics (span per classification stage, token usage
  counters, cache hit-rate gauge, batch concurrency utilization) exported to
  Prometheus/Grafana or Aspire dashboard, so degraded model latency or a spike in Stage-2 fallback
  rate (a proxy for policy-tool prompt quality drifting) is visible before it becomes an incident.
* **Structured schema validation** — move from "ask for JSON in the prompt" to the SDK's
  `ChatResponseFormat.ForJsonSchema<T>` enforced schema mode end-to-end (already wired as a hint via
  `ResponseFormat = ChatResponseFormat.Json`; a stricter per-field JSON Schema with enums for
  `Category`/`Currency` would cut malformed-response fallbacks further).
