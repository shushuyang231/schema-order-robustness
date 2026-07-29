# Claim-evidence audit

Audit date: 2026-07-24  
Audience: TMLR reviewers and action editor  
Question: Does every high-impact manuscript claim match the frozen design,
reports, and redistribution boundary?

## Overall assessment: Ready to share with caveats

The central empirical claim is supported and now stated narrowly: the tested
validation-equivalent Schema serializations can induce positive black-box
output-distribution distances beyond repeated-prompt variability. Only the
Sonnet gateway alias reaches the frozen 0.05 practical rule in the decomposed
follow-up. GPT and official DeepSeek are retained as negative practical
replications. No manuscript claim asserts a universal accuracy loss, an
internal mechanism, or a statistically confirmed between-system difference.

The remaining caveats are external validity and reproducibility limits of
mutable hosted systems, not unresolved arithmetic.

## Claim inventory

| Manuscript claim | Evidence | Audit result | Required wording boundary |
|---|---|---|---|
| The tested transformations are validation-equivalent | RFC 8259; JSON Schema Draft 2020-12; transformation signature guard; `results/gate/sob_schema_variant_audit.json` | Supported for the tested constructs | Do not generalize to arbitrary Schema rewrites, references, annotations, or implementation-specific behavior |
| 14,000 successful responses are analyzed | 5,000 primary + 6,000 disjoint gateway follow-up + 3,000 official DeepSeek | Verified | Distinguish successful responses from transient error rows |
| Sonnet crosses 0.05 on both decomposed contrasts | `sob_decomposed_sonnet5_report.json`: 0.0584 and 0.0768 | Verified | System-specific rule; not prevalence across models |
| GPT is positive but below 0.05 on both decomposed contrasts | `sob_decomposed_gpt55_report.json`: 0.03285 and 0.03795 | Verified | Call this a negative practical replication, not a null effect |
| Official DeepSeek is positive but below 0.05 | `sob_official_deepseek_v4_flash_report.json`: 0.01325 and 0.01815 | Verified | “Official endpoint” refers to the recorded DeepSeek endpoint, model ID, and fingerprint, not a fixed checkpoint |
| All six decomposed system-contrast estimates are statistically detectable | Holm p-values: Sonnet 0.00039992/0.00039992; GPT 0.00039992/0.00039992; DeepSeek 0.01319736/0.00159968 | Verified | Do not convert separate within-system results into a between-system test |
| No universal accuracy degradation is established | Primary accuracy families do not pass their frozen rule; Sonnet follow-up has no supported change; DeepSeek follow-up has no supported change | Verified | Retain the secondary GPT exception |
| GPT additional-member contrast has leaf-accuracy difference -0.0248 | `sob_decomposed_gpt55_report.json`, CI [-0.04631, -0.00674], Holm p=0.02080 | Verified | Secondary, below earlier 0.03 engineering context threshold, requires targeted replication |
| Sonnet and GPT differ in observed magnitudes, but not confirmatorily | `sob_decomposed_cross_model.json`: Holm p=0.0696 and 0.0664 for the two distribution differences | Verified | Never state that Sonnet is significantly more susceptible |
| The experiment is prompt-based, not native structured decoding | Request construction and manifests omit tools, response schemas, and `response_format`; official protocol 25 | Verified | Use “schema-guided JSON generation/extraction,” not “native Structured Outputs API” |
| DeepSeek was selected before official-provider outcomes | Dated amendment in protocol 25 and `sob_official_panel_freeze.json` | Auditable | Report the amendment and do not imply a preplanned multi-provider panel was completed |
| Kimi was not run or substituted | Protocol 25 supersedes the unavailable K3 candidate before calls | Auditable | Do not describe Kimi as an empirical result |
| Paper artifacts rebuild without inference | `src/build_paper_artifacts.py` reads frozen aggregate reports and sets `frozen_results_recomputed=false` | Verified | Do not call this a raw-data reanalysis |
| Anonymous artifact excludes raw responses and restricted gold | `src/build_anonymous_artifact.py`, `LICENSES.md`, ZIP allowlist | Verified | Distinguish the local audit archive from the distributable supplement |

## Calculation spot-checks

- Excess-disagreement population quantity: verified algebraically as
  \(\frac{1}{2}\sum_z(p(z)-q(z))^2\), equal to one half squared MMD under a
  Kronecker-delta kernel on normalized signatures.
- Independent unit: verified as record clusters, \(n=100\) for the primary
  study and \(n=200\) for the decomposed follow-up; calls are repeats, not
  additional independent records.
- Multiple testing: verified as Holm correction across four primary-study
  variants and two decomposed contrasts within each system/metric family.
- DeepSeek operational count: 3,000 unique successful keys plus two transient
  error rows later recovered; no duplicate success cells or response IDs.
- DeepSeek Schema pass: 2,989/3,000 = 0.996333.
- Figure/table provenance: verified through `paper/artifact_manifest.json`,
  which hashes every frozen source report and generated output.

## Visualization review

- Figure 2 distinguishes Sonnet and GPT with both color and marker shape.
- Figure 3 distinguishes Sonnet, GPT, and DeepSeek with circle, open square,
  and triangle markers; the 0.05 line is labelled as a model-specific practical
  threshold.
- No figure encodes a confirmatory between-system comparison.
- Tables report estimates, confidence intervals, adjusted p-values, and
  threshold decisions together, preventing “significant” from being read as
  automatically “practically large.”

## Required caveats

- The 0.05 threshold is a frozen study-specific engineering screen, not a
  universal utility threshold.
- The 200-record DeepSeek run reuses the decomposed task sample and is a
  system replication, not a second task-sample replication.
- Gateway aliases do not establish upstream provider identity or weights.
- The official endpoint remains mutable despite a stable returned model string
  and system fingerprint during the run.
- The estimand covers eligible medium/hard SOB text records for which both
  decomposed reorderings are nontrivial.
- Token normalization is not a semantic equivalence oracle; correctness
  metrics and Schema validation must remain separate.

## Incomplete handoff blockers

None for claim arithmetic. Submission still requires the author to enter real
author metadata only after the double-blind phase and to confirm the final
OpenReview administrative declarations.
