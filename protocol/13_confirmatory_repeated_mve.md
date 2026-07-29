# Confirmatory 100-Record Repeated-Measures MVE

Date frozen: 2026-07-17, before any API call on these 100 records.

## Evidence entering confirmation

The disjoint 20-record engineering gate completed 500 real calls. After
subtracting within-prompt stochastic disagreement, three variants passed the
pre-registered normalized distribution-shift gate:

- `properties_reversed`: 0.1375, 95% CI [0.0225, 0.2830]
- `keywords_reversed`: 0.1655, 95% CI [0.0445, 0.3140]
- `descriptions_first`: 0.0635, 95% CI [0.0135, 0.1245]

No leaf Value Accuracy difference was statistically supported. The confirmatory
claim is therefore about output-distribution sensitivity, not accuracy
improvement.

## Frozen population and calls

- The 100 record IDs were frozen before the 20-record gate was run.
- 50 medium and 50 hard schemas.
- Zero overlap with the five-record debugging pilot or 20-record engineering
  gate.
- Five schema variants, five independent calls per variant.
- Total: 100 x 5 x 5 = 2,500 calls.
- All requests are deterministically interleaved by SHA256 and resumable.
- Sampling parameters are omitted; requested alias is `claude-sonnet-5`.

All four non-original variants change bytes on all 100 records except
`descriptions_first`, which is a no-op on two records whose descriptions are
already first or absent. The primary analysis is intent-to-treat over all 100
frozen records; applicability counts are reported explicitly. This choice avoids
post-pilot sample replacement.

## Primary hypotheses

The three variants selected on the independent engineering gate are primary:

- H1: `properties_reversed` has positive token-normalized excess disagreement.
- H2: `keywords_reversed` has positive token-normalized excess disagreement.
- H3: `descriptions_first` has positive token-normalized excess disagreement.

`required_reversed` is retained as an exploratory comparison. Accuracy changes,
exact-string distribution shifts, schema compliance, tokens, and latency are
secondary outcomes.

## Frozen analysis

The metrics, random-noise subtraction, record-cluster bootstrap, stratified
permutation test, seed, and output normalization are identical to
`protocol/12_repeated_measures_redesign.md`:

`excess = cross(original, variant) - 0.5 * (within(original) + within(variant))`

- 5,000 record-cluster bootstrap resamples.
- 5,000 within-record label permutations.
- Holm correction across all four non-original variants (conservative relative
  to correcting only the three primary hypotheses).
- A primary variant replicates when normalized excess disagreement is at least
  0.05, its 95% CI lower bound is above zero, and Holm p is below 0.05.

## Confirmation decision

`CONFIRMED_FOR_SECOND_MODEL_REPLICATION` requires:

1. exactly 2,500 successful cells, one stable returned-model identifier, unique
   provided response IDs, and at least 95% Schema Pass Rate; and
2. at least two of the three primary variants replicate in the positive
   direction under the frozen rule.

Otherwise the decision is `NOT_CONFIRMED`. Even if confirmed, the paper is not
ready: the same direction must then be tested on a second model alias.

