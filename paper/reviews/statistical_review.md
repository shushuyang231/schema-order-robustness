# Simulated review: statistics and experimental design

## Summary

This paper studies whether validation-equivalent JSON Schema serializations
induce different output distributions in prompt-based, black-box JSON
extraction. The strongest methodological element is the use of repeated calls
per representation and an excess-disagreement estimator that subtracts
within-representation variation. The paper reports a frozen primary study, a
disjoint decomposed follow-up, and an official DeepSeek endpoint replication.

## Recommendation: weak accept after revision

The central claim is supported at the level at which it is now stated. I do not
see a blocking calculation error. The result should be considered an empirical
software-testing contribution, not evidence about model internals or a
universal performance loss.

## Major comments

1. **Clarify the estimand.** The original draft introduced the subtraction
   heuristically. The revised manuscript derives its expectation as
   \(\frac12\sum_z(p(z)-q(z))^2\), identifies the Kronecker-kernel MMD
   connection, and explains why record-level finite-sample estimates can be
   negative. This resolves my main statistical interpretation concern.

2. **Five repeats per cell are sparse.** The within-record distribution is
   estimated from only five outputs per representation. The U-statistic is
   unbiased, but record-level estimates can be noisy. The inference correctly
   treats records, not calls, as independent and uses 100/200 record clusters.
   The paper should continue to describe the repeats as a noise correction,
   not a high-resolution estimate of each task's full response distribution.

3. **The 0.05 threshold lacks a downstream utility anchor.** The revision now
   states that it was a frozen engineering screen corresponding to five
   percentage points of excess pair disagreement, not a universal loss
   function. Reporting all estimates and intervals, including DeepSeek's
   statistically detectable sub-threshold effects, is the correct treatment.

4. **Sequential hypothesis formation must remain visible.** The Sonnet
   hypotheses were selected on a disjoint engineering gate; GPT was a targeted
   replication after Sonnet; the decomposition was discovered post hoc and
   then tested on disjoint records; DeepSeek reused those records under a dated
   new-system protocol. The manuscript now distinguishes these stages. Do not
   compress them into one fully preregistered multi-model experiment.

5. **Between-system inference is appropriately limited.** Different
   model-specific threshold decisions do not establish heterogeneity. The
   post-hoc Sonnet-minus-GPT tests do not survive Holm correction. The revised
   text and figure captions state this explicitly.

6. **Accuracy must remain secondary in the decomposed follow-up.** The GPT
   -0.0248 leaf-accuracy contrast is statistically detectable but below the
   earlier 0.03 engineering context threshold and was not assigned a new
   practical threshold. The current “secondary caution requiring targeted
   replication” wording is appropriate.

7. **Multiple testing families are study-local.** Holm correction is applied
   within the four primary-study variants and within the two decomposed
   contrasts for each system/metric family. This does not create a single
   global family over every exploratory analysis ever run. The paper now
   discloses the staged design, so the family definitions are interpretable.

## Minor comments

- Keep exact adjusted p-values and confidence intervals in tables; do not rely
  on “significant” alone.
- The threshold line in Figures 2 and 3 must remain labelled as practical and
  model-specific.
- The 200-record DeepSeek result is a system replication on a fixed task
  sample, not independent task-sample confirmation.
- The two validation dialects should remain an internal-validity disclosure
  even though the post-hoc audit found zero decision disagreements.

## Residual limitations

- Five repeats cannot characterize long-tailed response distributions.
- Hosted-system defaults and updates are not controlled.
- The record sample is deterministic from one benchmark and not a probability
  sample of all JSON Schemas.
- The normalized-signature kernel is transparent but not a semantic oracle.
