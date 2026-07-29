# Sonnet Decomposed-Contrast Confirmation Result

Date: 2026-07-19

## Decision

**BOTH_DECOMPOSED_CONTRASTS_CONFIRMED**

The preregistered 200-record, three-representation, five-repeat experiment
completed with 3,000 successful responses and 99.7% overall Schema pass rate.

## Primary results

### Property order

`original` versus `properties_reversed`:

- normalized excess disagreement: 0.0584;
- 95% record-bootstrap CI: [0.0363, 0.0845];
- Holm-adjusted permutation p: 0.0004;
- leaf-value accuracy difference: -0.0007, CI [-0.0199, 0.0174].

This contrast passed the frozen 0.05 practical-effect rule without supported
average accuracy harm.

### Additional member order with property order held fixed

`properties_reversed` versus `keywords_reversed`:

- normalized excess disagreement: 0.0768;
- 95% record-bootstrap CI: [0.0498, 0.1061];
- Holm-adjusted permutation p: 0.0004;
- leaf-value accuracy difference: 0.00004, CI [-0.0167, 0.0166].

This contrast also passed the frozen practical-effect rule.  Because recursive
property order is identical between the two representations on every included
record, the evidence shows an additional effect of Schema-object member ordering
beyond property ordering.  It does not isolate any one keyword or establish an
internal neural mechanism.

## Data-quality audit

- Raw lines: 3,001.
- Final successful cells: 3,000/3,000.
- One retained transient server-disconnect row; the same task subsequently
  succeeded through the resumable runner.
- Each representation: 1,000 successful responses.
- Duplicate successful cells, request keys, and response IDs: zero.
- Repeat groups with inconsistent prompt hashes: zero.
- Independent evaluator rerun produced a byte-identical JSON report.

Decision: **PASS_SAFE_TO_CITE**.  The result applies to the observed
`claude-sonnet-5` gateway alias and execution window; upstream identity and
weights remain unverified.

## Paired result status

The already-frozen identical 200-record protocol has now also been run on the
`gpt-5.5` gateway alias. Its separate report is in
`protocol/24_decomposed_gpt_result.md`. An official or fixed open-weight endpoint
remains a separate provenance gate after the paired gateway experiments.
