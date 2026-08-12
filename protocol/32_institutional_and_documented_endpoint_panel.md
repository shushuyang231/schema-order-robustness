# Prospective Institutional and Documented-Aggregator Endpoint Panel

**Freeze date:** 2026-08-10 (Asia/Shanghai), before any request to the
endpoints or model IDs in this protocol.

This protocol separates two sources that must not be conflated:

1. **SJTU Zhiyuan-1 institutional endpoint (primary provenance tier).** The
   operator-provided access notice identifies the base URL as
   `https://models.sjtu.edu.cn/api/v1` and gives the aliases below. The
   Shanghai Jiao Tong University description of Zhiyuan-1 describes Ascend
   910B-based domestic computing services; Huawei's case description also
   identifies Zhiyuan-1 as an SJTU platform. The service is therefore labelled
   as an SJTU institutional endpoint, not as a direct vendor endpoint.
2. **TokenRhythm model marketplace (documented aggregator tier).** The public
   model catalogue and API documentation are available at
   `https://tokenrhythm.studio/models` and
   `https://tokenrhythm.studio/docs/api-integration`. Its public catalogue is
   evidence about the marketplace endpoint and advertised model IDs only; it
   does **not** independently verify the upstream checkpoint, routing, system
   prompt, caching, or hardware.

The earlier Prism gateway remains a separately labelled historical,
low-provenance observation. It is not used to select models or to replace a
failed endpoint in this protocol.

## Frozen active panel

The following exact requested IDs are fixed before any catalog or completion
request. A missing ID or a failed availability gate is retained as an
operational result; it is not replaced after inspecting results.

| Tier | Provider label | Base URL | Requested model ID | Role |
|---|---|---|---|---|
| SJTU primary | `sjtu_zhiyuan1` | `https://models.sjtu.edu.cn/api/v1` | `deepseek-chat` | primary interface |
| SJTU primary | `sjtu_zhiyuan1` | `https://models.sjtu.edu.cn/api/v1` | `deepseek-reasoner` | predeclared reasoning interface |
| SJTU primary | `sjtu_zhiyuan1` | `https://models.sjtu.edu.cn/api/v1` | `minimax-m2.7` | primary family |
| SJTU primary | `sjtu_zhiyuan1` | `https://models.sjtu.edu.cn/api/v1` | `qwen3.6-27b` | primary family |
| documented aggregator | `tokenrhythm` | `https://tokenrhythm.studio/v1` | `deepseek-v4-flash` | independent replication |
| documented aggregator | `tokenrhythm` | `https://tokenrhythm.studio/v1` | `glm-5.2` | independent replication |
| documented aggregator | `tokenrhythm` | `https://tokenrhythm.studio/v1` | `kimi-k2.7-code` | independent replication |
| documented aggregator | `tokenrhythm` | `https://tokenrhythm.studio/v1` | `minimax-m2.7` | independent replication |
| documented aggregator | `tokenrhythm` | `https://tokenrhythm.studio/v1` | `qwen3.7-max` | independent replication |

The TokenRhythm catalogue currently also displays `deepseek-v4-pro`,
`deepseek-v4-flash-0731`, `seed-2.1-pro`, `seed-2.1-turbo`, `glm-5`,
`glm-5.1`, `kimi-k2.5`, `kimi-k2.6`, `mimo-v2.5-pro`, `qwen3.8-max`,
`qwen-image-2.0`, and `wan2.7-image`. They are recorded as catalogue
inventory, not active models: image-only entries are outside this text
experiment, and adding further text models after seeing outcomes would be
model shopping.

## Fixed task and request contract

- Input: `data/processed/sob_decomposed_200_public.jsonl`.
- Independent unit: record; 100 medium and 100 hard records.
- Schema variants: `original`, `properties_reversed`, and
  `keywords_reversed`.
- Five repeated calls per variant; 3,000 requests per model when the gate
  passes.
- Messages, prompt hashes, deterministic SHA-256 request order, and scoring
  are inherited unchanged from Protocol 22 and the existing
  `run_sob_metamorphic.py` implementation.
- `max_tokens=4096`, `stream=false`; no `temperature`, `top_p`, `seed`, tools,
  `response_format`, or constrained decoding fields are sent.
- Provider-specific thinking flags are not silently harmonized. For the SJTU
  aliases the request body is empty unless a new pre-call amendment records a
  documented flag. For the TokenRhythm aliases the request body is also empty.
  Returned reasoning fields are retained only as length and SHA-256 metadata.
- The actual returned `model` string, response usage, system fingerprint (if
  supplied), timestamps, retries, and endpoint errors are recorded. A
  returned-model change during a run is a fatal provenance error.

## Availability gate

For every fixed row in the active panel, before experimental calls:

1. Query the authenticated `GET /models` endpoint.
2. Confirm that the exact requested ID appears in the catalog.
3. Send exactly three connectivity calls to `POST /chat/completions` using a
   fixed `API_OK` contract.
4. Require three successful responses and one stable returned-model string.
5. Save only sanitized metadata (catalog IDs, response lengths/hashes,
   returned model, usage, and errors). API keys and response text are never
   written to disk.

If any row fails, mark it `OPERATIONAL_FAILURE` and do not substitute another
model. The full run starts only for rows whose gate record reports
`gate_passed: true`.

## Primary analysis and multiplicity

For each model, the two predeclared contrasts are:

1. `original` versus `properties_reversed`;
2. `properties_reversed` versus `keywords_reversed`, holding recursive
   property order fixed.

The primary effect is normalized excess disagreement after subtracting the
within-representation repeat baselines. A model confirms a contrast only when
the frozen practical screen is at least 0.05, the record-cluster bootstrap
95% lower bound is above zero, and the within-record permutation p-value is
below 0.05 after Holm adjustment across that model's two contrasts. Null,
contrary, and operationally failed models remain in the report.

The four SJTU rows form the primary institutional panel. We will not rank
models by the observed effect and will not use a positive result to add a new
model. TokenRhythm is a separately labelled replication tier; its results do
not silently upgrade the upstream checkpoint provenance.

## Deployment and attribution safeguards

The SJTU-side deployment is described as: “上海交通大学‘致远一号’提供
智算服务” (Shanghai Jiao Tong University “Zhiyuan-1” provides the computing
service). The operator reports Huawei Ascend 910B NPU/CANN serving. Possible
FP8/BF16 or backend numerical differences are recorded as deployment metadata
and a threat to validity; hardware is not treated as an experimental causal
variable, and no NPU-versus-CUDA claim is made.

For TokenRhythm, the public base URL may be cited as the documented aggregator
endpoint. We do not call its entries “official vendor checkpoints” unless an
independent checkpoint identity is supplied by the service and recorded before
the run.

## Secure execution rule

Keys must be supplied through environment variables or a hidden prompt. They
must not appear in shell history, source files, manifests, JSONL results,
GitHub commits, or screenshots. Run the generic smoke helper first; only a
passed sanitized smoke record may be passed to the full-run script.

The exact command templates are documented in
`protocol/32_institutional_and_documented_endpoint_panel_commands.md` after
the local key variable names are chosen.
