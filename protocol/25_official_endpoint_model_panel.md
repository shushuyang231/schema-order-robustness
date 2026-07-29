# Preregistered Official DeepSeek-Endpoint Replication

Date frozen: 2026-07-24, before any experimental request to the models below.

Amended: 2026-07-24 13:12:52 +08:00, before any authenticated official-provider
catalog request, connectivity completion, or experimental completion.

## Amendment: active scope narrowed before calls

The initial candidate panel listed Moonshot Kimi K3, DeepSeek V4 Flash, xAI
Grok 4.3, and Gemini 3.6 Flash. No catalog, smoke-test, or experimental request
was made to any of them. Before endpoint outcomes were observed, the active
scope was narrowed to one official replication:

| Provider label | Official base URL | Fixed model ID | Active status |
|---|---|---|---|
| `deepseek_official` | `https://api.deepseek.com` | `deepseek-v4-flash` | active; pending authenticated catalog and three-call smoke gate |

This narrowing follows the pre-outcome decision to add at most one provider for
independently verifiable endpoint provenance rather than search across models
for another positive result. The three other candidate manifests are retained
as a superseded audit trail and must not be called under this protocol.
Specifically, the frozen Kimi candidate was `kimi-k3`; substituting an available
Kimi K2.x model would require a new dated amendment before any such request.

## Purpose

This replication tests whether the two already-frozen decomposed Schema-order
contrasts appear on one additional provider whose endpoint provenance can be
verified. It is not a search for a favorable model. Every positive, null,
contrary, and operationally failed result is retained.

The fixed 200-record sample and three representations from Protocol 22 are
reused. This is a new-model replication on a fixed task sample, not a new
task-sample confirmation.

## Superseded initial candidate panel

The following table records the original candidates only. It is not an active
call list after the amendment above.

| Provider label | Official base URL | Fixed model ID | Final protocol status |
|---|---|---|---|
| `moonshot_official_cn` | `https://api.moonshot.cn/v1` | `kimi-k3` | superseded before calls; do not call |
| `deepseek_official` | `https://api.deepseek.com` | `deepseek-v4-flash` | active under amendment |
| `xai_official` | `https://api.x.ai/v1` | `grok-4.3` | superseded before calls; do not call |
| `google_gemini_official` | `https://generativelanguage.googleapis.com/v1beta/openai` | `gemini-3.6-flash` | superseded before calls; do not call |

The Google Antigravity managed agent is excluded. It starts an autonomous
tool-use loop and therefore is not comparable to the prompt-only Chat
Completions design.

The Prism `grok-4.20-multi-agent-*` aliases are excluded from the formal
official-endpoint panel because both provider provenance and the agent harness
would be confounded with the model. They may be reported only as a separately
labelled exploratory gateway result under a later protocol.

## Availability gate

Before any experimental request:

1. Query DeepSeek's authenticated `/models` endpoint.
2. Run exactly three connectivity prompts against the fixed model ID.
3. Save only sanitized model catalog and response metadata. Do not save
   connectivity-response text or reasoning text; save length, SHA-256, and an
   exact-`API_OK` flag instead.
4. An endpoint enters the panel only when the requested ID is available and all
   three calls succeed with one stable returned-model identifier.

If the gate fails, record the operational result and do not start the
experimental run. No experimental outcome may be used to replace the
inaccessible model. A replacement model requires a new dated protocol written
before any call to that replacement.

## Frozen design

- Public input: `data/processed/sob_decomposed_200_public.jsonl`.
- Independent unit: record.
- Records: 200 (100 medium, 100 hard).
- Conditions: `original`, `properties_reversed`, `keywords_reversed`.
- Repeats: five identical prompts per condition.
- Requests: 3,000 per accessible model.
- Sampling parameters: omitted; each provider's documented model defaults are
  treated as part of the deployed system and recorded.
- DeepSeek thinking mode: the `thinking` field and `reasoning_effort` are
  omitted, so the documented 2026-07-24 provider default (thinking enabled,
  regular-request effort `high`) is part of the observed deployed system.
  Only the final `message.content` is scored. Reasoning text is not persisted;
  its length and SHA-256 are retained for audit when returned.
- Maximum output: 4,096 tokens.
- Tools, search, `response_format`, response schemas, and constrained decoding:
  disabled/not sent. DeepSeek's text response mode is therefore used, not its
  JSON Output feature.
- Request order: deterministic SHA256 order already defined in Protocol 22.

## Primary contrasts

1. Property order: `original` versus `properties_reversed`.
2. Additional object-member order: `properties_reversed` versus
   `keywords_reversed`, holding recursive property order fixed.

The primary effect is token-normalized excess disagreement after subtracting
the two within-representation repeat baselines.

## Inference and decisions

The per-model confirmation rule is unchanged from Protocol 22:

- point estimate at least 0.05;
- 95% record-cluster bootstrap lower bound above zero;
- Holm-adjusted within-record permutation p below 0.05 across the two
  contrasts.

Each model receives one of:

- `BOTH_DECOMPOSED_CONTRASTS_CONFIRMED`;
- `PARTIAL_DECOMPOSED_CONFIRMATION`;
- `DECOMPOSED_CONFIRMATION_NOT_FOUND`;
- `OFFICIAL_ENDPOINT_OPERATIONAL_FAILURE`.

The DeepSeek decision is reported regardless of direction. Because the amended
active scope contains one model, the per-model Holm family across the two
contrasts is also the complete new-provider primary family. The result is not
used to estimate population prevalence across models.

Schema pass rate and leaf-value accuracy remain secondary. A distribution shift
is not relabelled as accuracy harm without its own corrected evidence.

## Stopping and reporting rules

- Complete the fixed DeepSeek run if the availability gate passes.
- Do not add another model after inspecting these results.
- Resume failed jobs only with the identical request key and prompt hash.
- Stop immediately on a non-retryable 4xx request error or returned-model
  mismatch. Pause after five consecutive request errors; inspect saved rows
  before resuming.
- Report exact requested/returned model IDs, official base URL, call date,
  manifest hash, smoke-record hash, system fingerprint where returned, output
  hash, parse rate, Schema pass rate, token usage, and all failures.
- Provider subscriptions and API billing are reported separately; a consumer
  chat subscription is not assumed to include API quota.

## Preflight pricing snapshot and commands

The official DeepSeek pricing page retrieved on 2026-07-24 listed V4 Flash at
CNY 1 per million cache-miss input tokens, CNY 0.02 per million cache-hit input
tokens, and CNY 2 per million output tokens (USD 0.14, 0.0028, and 0.28
respectively). The prior GPT follow-up used 4,792,315 input and 512,966 output
tokens for the identical 3,000 prompts, implying a non-binding comparable-usage
estimate of about CNY 5.82 (USD 0.82) if all input is billed as cache misses.
Thinking is enabled by default, so actual output usage may be higher. With the
frozen 4,096-token cap, a conservative no-retry ceiling using the same input
estimate is about CNY 29.37 (USD 4.11).

Documentation snapshots:

- <https://api-docs.deepseek.com/api/list-models/>
- <https://api-docs.deepseek.com/api/create-chat-completion/>
- <https://api-docs.deepseek.com/guides/thinking_mode/>
- <https://api-docs.deepseek.com/quick_start/pricing/>

After local tests pass and `DEEPSEEK_API_KEY` is set, run the authenticated
catalog-only check first:

```powershell
.\.venv\Scripts\python.exe src\smoke_official_provider.py `
  --provider deepseek `
  --catalog-only
```

Then run the required three-completion smoke gate:

```powershell
.\.venv\Scripts\python.exe src\smoke_official_provider.py `
  --provider deepseek `
  --repeats 3
```

Only after that command reports `gate_passed: true`, run:

```powershell
.\.venv\Scripts\python.exe src\run_sob_metamorphic.py `
  --public-input data\processed\sob_decomposed_200_public.jsonl `
  --manifest protocol\sob_official_deepseek_v4_flash_manifest.json `
  --output results\api\sob_official_deepseek_v4_flash.jsonl `
  --model-alias deepseek-v4-flash `
  --base-url https://api.deepseek.com `
  --api-key-env DEEPSEEK_API_KEY `
  --provider-label deepseek_official `
  --smoke-record data\raw\official_smoke\<deepseek-smoke-file>.json `
  --no-key-prompt
```
