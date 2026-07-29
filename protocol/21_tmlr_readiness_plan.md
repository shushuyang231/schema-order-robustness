# TMLR Readiness Plan

Date frozen: 2026-07-19

## Goal

Produce an honest, reproducible, independently understandable submission about
metamorphic testing of validation-equivalent JSON Schema serializations.  TMLR
is the primary quality target.  Acceptance is not assumed, and no new analysis
may retroactively change the preregistered Sonnet or GPT decisions.

## Current evidence state

- 100 disjoint medium/hard SOB records.
- Five Schema representations and five repeats per representation.
- Two gateway aliases and 5,000 successful formal responses in total.
- Sonnet alias: two variants crossed the frozen 0.05 practical threshold.
- GPT alias: smaller positive signals did not cross that threshold.
- No supported corrected average leaf-accuracy degradation.
- No established between-model difference, stable susceptible-record profile,
  or internal mechanism.
- Full first English draft, figures, tables, frozen hashes, and 18 passing tests.

## Submission gates

### Gate A — frozen evidence integrity: PASS

Keep the 2026-07-18 snapshot immutable.  All further work is either a clearly
labelled post-hoc analysis or a newly preregistered study on disjoint records.

### Gate B — construct validity: PASS FOR DISJOINT CONFIRMATION

The original `keywords_reversed` transformation is composite because reversing
all JSON object members also reverses each `properties` mapping.  Before any new
API call:

1. compare `original` with `properties_reversed`;
2. compare `original` with `required_reversed`;
3. compare `original` with `descriptions_first`;
4. compare `properties_reversed` with `keywords_reversed` to hold property order
   fixed while changing additional member order.

This decomposition is post-hoc and may refine interpretation only.  If it
suggests a focused explanation, freeze a disjoint-record confirmation before
calling any model.

Result: recursive property order matched on 100/100 records between
`properties_reversed` and `keywords_reversed`.  The incremental normalized
excess contrast was 0.0578 for the Sonnet alias and 0.0246 for the GPT alias;
both corrected distribution tests were positive, while neither established a
corrected leaf-accuracy difference.  The result supports a disjoint confirmation
of two separate behavioral contrasts: property order, and additional
object-member order given fixed reversed properties.

### Gate C — behavioral explanation: BOTH ALIASES CHARACTERIZED

Prefer testable black-box explanations over unsupported neural-mechanism claims.
Candidate questions, selected only after Gate B:

- Is the effect localized to property order, other keyword/member order, or both?
- Does field-level output change grow with the field's normalized positional
  displacement?
- Can a deterministic canonical serialization reduce between-representation
  variance without changing average task accuracy?

Any new control must specify its records, transformations, repeats, primary
metric, minimum effect, multiple-testing family, and stopping rule before API
execution.  A null result is retained.

The preregistered 200-record Sonnet run confirmed both primary contrasts:
property order produced normalized excess 0.0584 and additional object-member
order with property order held fixed produced 0.0768. The identical GPT run
showed smaller but statistically detectable effects (0.0329 and 0.0380), neither
meeting the 0.05 practical threshold. Its secondary additional-member accuracy
difference was -0.0248 with Holm p=0.0208; this is a cautionary signal below the
earlier 0.03 engineering-effect context threshold, not a confirmed universal
accuracy harm.

### Gate D — endpoint provenance: PENDING/HIGH RISK

The existing evidence applies only to the observed gateway endpoints and
returned aliases.  The paper must not claim verified official weights.  Before
submission, attempt one of the following without replacing the frozen results:

1. a small preregistered replication through an independently verifiable
   official endpoint;
2. a fixed open-weight checkpoint with a recorded revision and deterministic
   inference environment;
3. if neither is feasible, narrow the title, abstract, and conclusions to
   unverified black-box endpoints and treat provenance as a major limitation.

### Gate E — literature and novelty: PENDING

Manually verify every bibliographic field and add work on:

- order sensitivity and positional bias;
- structured generation and tool/function schemas;
- metamorphic and differential testing of nondeterministic systems;
- reproducibility of closed model endpoints.

The novelty claim is the complete combination of specification-derived
validation-equivalent transformations, repeated stochastic baselines,
distribution/correctness separation, and a reusable test procedure—not general
prompt sensitivity.

### Gate F — artifact release: PENDING

Create a clean public export with a license, version, environment lock, one-command
offline smoke test, public example data, and exact reproduction instructions.
Exclude credentials, restricted gold, non-redistributable raw data, and any
response logs whose redistribution permission is unclear.

### Gate G — author readiness: PENDING

The sole author must be able to explain without reading a script:

1. validation equivalence versus byte/token equivalence;
2. why identical-prompt repeats are needed;
3. the excess-disagreement formula;
4. record-level independence and multiple-testing correction;
5. why distribution shift is not accuracy loss;
6. why failed practical cross-model replication is retained;
7. what the gateway evidence can and cannot identify.

### Gate H — submission package: PENDING

After Gates B–G, convert the manuscript to the current official TMLR template,
run an anonymous-submission audit, verify OpenReview profile requirements, and
perform two independent red-team review passes.  AI review is an internal check,
not evidence of expert endorsement.

## Immediate execution order

1. Freeze a 200-record disjoint confirmation with only `original`,
   `properties_reversed`, and `keywords_reversed`.
2. Use five repeats and two primary contrasts: original versus property reversal,
   and property reversal versus whole-object reversal.
3. Implement and offline-test the full control before requesting any API key.
4. Run the same frozen design on both existing aliases; retain null or contrary
   results without changing thresholds.
5. Separately pursue an independently verifiable endpoint for provenance rather
   than treating another gateway alias as provenance evidence.
6. Expand and verify related work and continue the author oral guide.

## Stop rules

- Do not add models only to search for a positive result.
- Do not relabel exploratory results as confirmatory.
- Do not claim an internal attention, position-encoding, or training mechanism.
- Do not claim official model identity without independently checkable evidence.
- If a focused disjoint control contradicts the central engineering claim,
  retain the result and revise or abandon the paper rather than changing the
  threshold or sample.
