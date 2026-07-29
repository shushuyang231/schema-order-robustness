# Cross-Model Result Decision

## Frozen formal outcomes

- Sonnet 5 confirmatory experiment: `CONFIRMED_FOR_SECOND_MODEL_REPLICATION`.
- GPT-5.5 replication experiment: `CROSS_MODEL_REPLICATION_NOT_FOUND`.
- Both operational gates passed with 2,500 unique successful task keys.
- The formal decisions and the preregistered 0.05 minimum practical-effect
  threshold remain unchanged.

## Post-hoc exploratory findings

The shared 100-record design permits record-paired model comparisons, but these
comparisons were specified only after both formal reports were observed.

For the two primary cross-model variants, the Sonnet-minus-GPT normalized excess
point estimates were:

- `properties_reversed`: +0.0442, 95% bootstrap CI [-0.0030, 0.0936],
  Holm-adjusted sign-flip p = 0.1662.
- `keywords_reversed`: +0.0416, 95% bootstrap CI [-0.0001, 0.0849],
  Holm-adjusted sign-flip p = 0.1662.

The point estimates suggest larger effects for Sonnet 5, but the paired evidence
does not establish a between-model difference.  This distinction must be kept in
the paper: one model crossed the preregistered practical threshold and the other
did not, yet “significant in one and not significant in another” is not itself a
significant model difference.

No schema variant showed corrected record-level concordance across models.  None
of four fixed public-side schema features—schema characters, total properties,
maximum schema depth, and description characters—showed a corrected association
with sensitivity in any model-variant family.

## Decision

**KEEP THE TOPIC, NARROW THE CLAIM, AND DO NOT CLAIM A MECHANISM.**

The defensible empirical result is:

> Semantics-preserving JSON Schema reorderings produced statistically detectable
> output-distribution shifts for the two tested gateway model aliases, but the
> preregistered practical-magnitude replication criterion was met only in the
> Sonnet 5 experiment.  The current data do not establish a between-model effect
> difference, a stable record-level susceptibility profile, an accuracy benefit
> or harm, or an internal mechanism.

## Next gate before new API calls

Do not add a third model simply to search for a positive replication.  First:

1. audit related work for the novelty of schema-order metamorphic testing;
2. turn the current design and results into a paper outline with explicit RQs;
3. decide whether a newly preregistered third-model characterization materially
   answers an RQ rather than functioning as a replacement for GPT-5.5;
4. design any mechanism-oriented follow-up as a separate exploratory study.

All gateway aliases must be reported as unverified aliases unless upstream model
identity can be independently established.
