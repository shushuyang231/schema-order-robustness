# Preregistered Decomposed Schema-Order Confirmation

Date frozen: 2026-07-19, before any API call on the new records.

## Motivation

The frozen 100-record study compared every named representation with the
original.  A post-hoc audit then identified that `keywords_reversed` is a
composite intervention: it reverses both `properties` entries and additional
JSON object members.  Directly comparing `properties_reversed` with
`keywords_reversed` held recursive property order fixed on 100/100 records and
found exploratory normalized excess disagreement of 0.0578 for the Sonnet alias
and 0.0246 for the GPT alias.

This new experiment confirms or rejects that decomposition on records not used
in any earlier pilot, engineering gate, or formal study.

## Frozen sample and conditions

- Source: SOB text test split.
- 200 records selected deterministically after excluding every prior study ID.
- 100 medium and 100 hard Schema records.
- Three representations: `original`, `properties_reversed`, and
  `keywords_reversed`.
- Five identical-prompt repeats per representation.
- 3,000 requests per model alias.
- The recursive property-order signature of `properties_reversed` and
  `keywords_reversed` must match for every included record.

## Primary contrasts

1. **Property order:** `original` versus `properties_reversed`.
2. **Additional object-member order:** `properties_reversed` versus
   `keywords_reversed`, holding recursive property order fixed.

Both use token-normalized excess disagreement after subtracting the two
within-representation disagreement baselines.

## Frozen inference

- Independent unit: record, not API call.
- 5,000 record-cluster bootstrap samples.
- 5,000 within-record label permutations.
- Holm correction across the two primary contrasts for each model.
- Practical threshold: 0.05 normalized excess disagreement.

A contrast is confirmed when its point estimate is at least 0.05, its 95%
bootstrap lower bound is above zero, and its Holm-adjusted permutation p-value is
below 0.05.  `BOTH_DECOMPOSED_CONTRASTS_CONFIRMED`,
`PARTIAL_DECOMPOSED_CONFIRMATION`, and `DECOMPOSED_CONFIRMATION_NOT_FOUND` are all
publishable outcomes and do not trigger record replacement or threshold changes.

## Model scope

Run the identical frozen design on the two existing gateway aliases.  This tests
task-sample generalization and whether the behavioral decomposition is stable;
it does not repair endpoint provenance.  Any later official-endpoint run must
have its own frozen manifest and cannot replace an unfavorable result here.

## Accuracy and validity

Schema pass rate and leaf-value accuracy differences are secondary.  A
distribution contrast cannot be relabelled as accuracy harm without its own
corrected evidence.  Overall Schema pass must be at least 95%, every expected
successful task key must be present, and one stable returned-model string is
required for the operational gate.
