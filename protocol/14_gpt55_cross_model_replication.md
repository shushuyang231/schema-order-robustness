# GPT-5.5 Cross-Model Replication Protocol

## Purpose

The frozen Sonnet 5 confirmatory experiment found normalized schema-order
distribution shifts for `properties_reversed` and `keywords_reversed`. This
experiment tests whether either effect appears for the independent gateway model
alias `gpt-5.5`. The alias is reported exactly as returned by the gateway; model
weights and upstream identity are not independently verified.

## Frozen design

- Reuse the same frozen 100 SOB records to make model comparisons paired by task.
- Run five schema representations with five identical-prompt repeats each.
- Total: 100 records x 5 representations x 5 repeats = 2,500 requests.
- Omit sampling parameters because gateway model support is not assumed.
- Preserve the same prompts, parser, schema validator, scoring, cluster bootstrap,
  stratified permutation, random seed, and Holm correction as the Sonnet 5 run.
- Treat `properties_reversed` and `keywords_reversed` as the two primary variants.
- Treat `required_reversed` and `descriptions_first` as exploratory variants.

The primary analysis is intent-to-treat over all 100 records. The two known
`descriptions_first` no-op schemas remain in the frozen sample and are reported
through applicability counts.

## Frozen signal rule

A primary variant replicates when normalized excess disagreement is at least
0.05, its 95% cluster-bootstrap confidence interval has a lower bound above zero,
and its Holm-adjusted permutation p-value is below 0.05. Accuracy shifts remain
secondary and do not rescue a failed primary distribution-shift hypothesis.

Operational validity requires 2,500 successful task keys, one returned model
identifier, unique provided response IDs, and at least 95% Schema Pass Rate.

- `STRONG_CROSS_MODEL_REPLICATION`: both primary variants replicate.
- `PARTIAL_CROSS_MODEL_REPLICATION`: exactly one primary variant replicates.
- `CROSS_MODEL_REPLICATION_NOT_FOUND`: neither primary variant replicates.
- `CROSS_MODEL_REPLICATION_INCOMPLETE`: an operational validity gate fails.

Partial replication supports a narrower cross-model claim. Strong replication
supports the planned general claim more directly. Failure to replicate is retained
and reported rather than followed by replacement records or post-hoc thresholds.

## Claim boundary

The experiment can establish representation-sensitive output distributions. It
does not by itself establish that any ordering improves accuracy, reveal a causal
internal mechanism, or prove behavior for models beyond the tested gateway
aliases and SOB task distribution.
