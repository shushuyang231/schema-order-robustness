# Claim-evidence audit — EMSE rewrite

Date: 2026-08-12
Status: offline manuscript gate passes

## Headline inventory

| Manuscript claim | Frozen evidence | Status | Required boundary |
|---|---|---|---|
| 17,900 successful core responses | 5,000 initial + 6,000 disjoint gateways + 3,000 DeepSeek + 2,400 Qwen text + 1,500 Qwen JSON Mode | verified | The separate 600-response Qwen3.7 pilot is excluded and disclosed |
| Sonnet decomposed effects are 0.0584 and 0.0768 | `sob_decomposed_sonnet5_report.json` | verified | Informal operator communication supports an Anthropic commercial-API route, but no documentary evidence was available and the checkpoint, wrapper, and per-request route were not independently verified |
| GPT decomposed effects are 0.0329 and 0.0380 | `sob_decomposed_gpt55_report.json` | verified | Detectable but below the frozen 0.05 practical threshold; informal operator communication supports an OpenAI commercial-API route subject to the same documentary and authentication limits |
| DeepSeek effects are 0.0133 and 0.0182 | `sob_official_deepseek_v4_flash_report.json` | verified | Negative practical replication, not “no effect” |
| Qwen text effects are 0.1255 and 0.1229 | `sob_official_qwen_plus_resource_full160_report.json` | verified | Real-time `qwen-plus` deployment over the frozen 160 records |
| JSON-Mode effects are 0.1582 and 0.1219 | `sob_official_qwen_plus_json_mode_100_report.json` | verified | JSON object mode, not strict JSON Schema constrained decoding |
| Matched JSON-minus-text changes are +0.0191 and -0.0249 | `sob_official_qwen_plus_mode_interaction_100_report.json` | verified | Neither material interaction confirmed; not an equivalence result |
| No universal average accuracy degradation | all decomposed reports | verified | Retain GPT secondary -0.0248 exception and its Holm p=0.0208 |
| Qwen text and JSON vulnerable-record profiles correlate | robustness audit: rho 0.618/0.626, global Holm p=0.0040 | verified exploratory | Do not promote post-hoc concordance to a confirmatory result |
| All 200 stored triples canonicalize identically | `sob_schema_canonicalization_audit.json` | verified | Conservative intervention, not a general Schema-equivalence checker |
| Core transport audit: 17,900 successes, 20 retained top-level error rows, 28 successful rows with internal retries | `sob_core_retry_audit.json` | verified | Every frozen key completed; permanent availability failures remain outside the estimand |
| Three maximum-effect Qwen cases show omission, factual substitution, and surface normalization | `sob_qwen_high_effect_cases.json` | verified post-hoc | Deliberately contrasting examples, not a frequency estimate or harm estimate |
| Supplemental endpoint panel contains 9,000 successful responses with no new 0.05 practical confirmation | `sob_endpoint_panel_completion_audit.json`; `sob_endpoint_panel_summary.json`; three endpoint reports | verified supplemental | Post-submission evidence; SJTU chat is detectable but subthreshold, reasoner and TokenRhythm are near zero; not pooled as independent model samples |
| Supplemental endpoint effects are 0.0168/0.0160 (SJTU chat), -0.0005/0.0028 (SJTU reasoner), and 0.0039/-0.0027 (TokenRhythm) | endpoint report JSON files | verified supplemental | Six-test panel Holm p-values are reported; no hardware-causal or upstream-checkpoint claim |
| Supplemental endpoint completion retains 28 top-level transport-error rows and has 9,000 unique successful request keys | `sob_endpoint_panel_completion_audit.json` | verified | All previously missing keys were recovered by identical-key continuation before effect analysis |

## Counting and provenance checks

- Every core report passes its operational count gate.
- The Qwen text report contains 2,400 successful keys and one retained earlier
  error row; the manuscript counts successful responses only.
- The Qwen JSON-Mode log contains 1,500 successful unique keys and 1,500 rows
  with the frozen `response_format` request contract.
- Formal Qwen text plus JSON Mode usage is 6,820,229 provider-recorded tokens.
- The supplemental endpoint panel used 17,051,515 provider-reported tokens and is
  reported separately from the core evidence.
- The endpoint completion audit passed at 9,000/9,000 unique successful keys;
  the retained 28 transport-error rows are not silently discarded.
- The mode ablation was designed after viewing the Qwen text interim; the
  manuscript states this selection in the introduction, methods, and threats.

## Statistical boundaries

- The record is the resampling unit; individual API calls are not treated as
  independent observations.
- Holm correction is applied within each declared family.
- The 0.05 distribution threshold and 0.03 mode-interaction threshold are
  engineering contexts, not universal loss functions.
- Descriptive 0.03/0.05/0.08 sensitivity changes which deployments cross the
  magnitude screen but does not replace the frozen 0.05 decision.
- Failure to cross 0.05 is not a null effect.
- Failure to confirm the mode interaction is not equivalence.
- Direct Sonnet-versus-GPT differences did not survive multiplicity
  correction; the paper does not rank providers.

## Visualization and manuscript checks

- Figure 2 retains the initial five-way gateway experiment.
- Figure 3 distinguishes four text deployments by both color and marker shape.
- Figure 4 separates within-interface effects from the JSON-minus-text
  interaction and marks the +/-0.03 boundary.
- Figure captions are outside the images in the review PDF.
- Six in-paper tables and nine generated CSV tables trace back to frozen JSON
  reports.
- All 25 bibliography entries are cited; there are no unresolved citation keys.
