# Repeated-Measures Redesign for Schema-Order Metamorphic Testing

Date frozen: 2026-07-17

## Why the one-shot design was rejected

The first five-record pilot produced the same disagreement rates under schema
reordering and under five byte-identical repeats: 60% exact and 40% after SOB
token normalization. The one-shot design therefore cannot identify a schema
serialization effect separately from ordinary black-box sampling variation.

## Engineering gate population

- Source: SOB text test split.
- Raw source: 5,000 rows, 4,951 unique record IDs; 49 byte-identical duplicate
  rows are removed before sampling.
- Exclusions: the frozen 100-record confirmatory sample and the earlier
  five-record pilot.
- Eligibility: all five schema serializations must be pairwise byte-distinct and
  validation-semantically equivalent.
- Fixed gate sample: 20 unique records, 10 medium and 10 hard schemas.
- This gate sample is never included in confirmatory inference.

## Experimental cells

For every record, run five serialization variants with five independent API
requests per variant:

- `original`
- `properties_reversed`
- `required_reversed`
- `keywords_reversed`
- `descriptions_first`

Total: 20 records x 5 variants x 5 repeats = 500 requests. Request order is a
deterministic SHA256 permutation over all cells. Sampling parameters are omitted
because the target model rejects non-default sampling controls. Every request is
stateless and stores its requested alias, returned model identifier, prompt hash,
token usage, latency, raw response, parsed object, and schema-validation result.

## Metrics

Accuracy metrics follow SOB:

- Schema Pass Rate
- Perfect Response Rate
- macro leaf-level exact Value Accuracy
- Value Token F1 using lowercase, punctuation removal, article removal, and
  whitespace tokenization

For each record and non-original variant, let A be the five original outputs and
B be the five variant outputs. For canonical exact JSON signatures and
token-normalized signatures, compute:

`excess_disagreement = cross(A,B) - 0.5 * (within(A) + within(B))`

where `cross` is the disagreement proportion over all 25 cross-condition pairs
and `within` is the disagreement proportion over the 10 unordered repeat pairs.
This subtracts ordinary within-prompt stochasticity from cross-schema
disagreement. Positive values indicate a distribution shift beyond repeat noise.

## Statistical procedure

- Unit of resampling: record, never individual API call.
- Paired differences: each variant versus original within the same record.
- 95% percentile cluster bootstrap intervals: 5,000 resamples, seed 20260717.
- Distribution-shift p-values: 5,000 stratified label permutations within each
  record, one-sided.
- Accuracy-difference p-values: 5,000 paired sign-flip permutations, two-sided.
- Four variant comparisons are Holm-corrected within each metric family.

## Go / No-Go gate

Proceed to the frozen 100-record repeated-measures experiment only if:

1. all 500 jobs are present, the returned model identifier is stable, and Schema
   Pass Rate is at least 95%; and
2. at least one non-original variant meets either:
   - token-normalized excess disagreement >= 0.05, bootstrap 95% CI lower bound
     above zero, and Holm-adjusted permutation p < 0.05; or
   - absolute macro leaf Value Accuracy change >= 0.03, bootstrap 95% CI excludes
     zero, and Holm-adjusted sign-flip p < 0.05.

Otherwise the schema-order causal claim is No-Go. A No-Go result may still
support a separate study of black-box structured-output stochasticity, but the
paper must not claim an order effect.

## Scope

The 20-record experiment is an engineering and power gate, not final evidence.
If it passes, the same frozen analysis is run on 100 untouched records and then
replicated on a second gateway model alias.

