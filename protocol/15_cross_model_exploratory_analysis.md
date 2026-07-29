# Post-Hoc Cross-Model Exploratory Analysis

## Status and purpose

This analysis was specified after the frozen Sonnet 5 confirmatory report and
GPT-5.5 cross-model replication report were observed.  It is exploratory and
cannot change either formal decision.  In particular, it does not rescue the
`CROSS_MODEL_REPLICATION_NOT_FOUND` outcome by relaxing the preregistered 0.05
minimum normalized-excess threshold.

The analysis asks two narrower questions:

1. Is the record-paired representation-sensitivity estimate larger for one
   gateway model alias than the other?
2. Do a small set of fixed, public-side JSON Schema features covary with the
   record-level sensitivity estimate?

## Inputs

- The same frozen 100 public SOB records used by both formal experiments.
- Five identical-prompt repeats for each of five schema representations.
- The append-only prediction logs and formal reports for gateway aliases
  `claude-sonnet-5` and `gpt-5.5`.
- No new API calls and no replacement records.

Gateway aliases and returned model strings are reported verbatim.  The upstream
providers, weights, and model identities are not independently verified.

## Paired model comparison

For each record and schema variant, compute normalized excess disagreement
against the record's original-schema repeats.  Subtract the GPT-5.5 record
estimate from the Sonnet 5 record estimate.  Report the mean paired difference,
a record-cluster bootstrap 95% confidence interval, and a two-sided record-level
sign-flip p-value.  Apply Holm correction across the four non-original variants.

These tests are post-hoc.  A positive result may support a model-heterogeneity
hypothesis but is not a confirmatory replication result.

## Record-level concordance

For each variant, compute the Spearman correlation between the two models' 100
record-level sensitivity estimates.  Use record permutation for p-values and
record bootstrap for confidence intervals.  Apply Holm correction across the
four variants.

## Fixed schema features

The feature set is frozen here before the exploratory script is run:

- compact original-schema character count;
- total property count across nested objects;
- maximum schema-node depth;
- total description character count.

For every model-variant pair, report Spearman correlations with record-level
normalized excess disagreement, record-permutation p-values, bootstrap
confidence intervals, and Holm correction across the four fixed features.
No additional feature is selected based on significance.

## Claim boundary

The results can characterize model heterogeneity and generate hypotheses about
conditions associated with sensitivity.  They cannot reveal an internal neural
mechanism, establish that one ordering improves accuracy, prove universality
beyond the two gateway aliases and SOB sample, or revise the formal replication
decision.
