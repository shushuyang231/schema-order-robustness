# Disposition of the August 2026 adversarial review

Date: 2026-08-02
Target: Empirical Software Engineering, PROMPT-SE 2026 special issue
API status: closed; no new model calls were made for this revision

## Bottom line

The review contains several useful scientific criticisms, but its highest-
priority venue conclusion is based on conflating two different submission
routes:

- The completed EASE 2026 Prompt-SE workshop used the ACM template, limited
  full papers to 10 pages including references, and closed submissions on
  2026-03-09:
  https://conf.researchr.org/home/ease-2026/prompt-se-2026
- The current target is the open EMSE journal collection “Empirical Studies for
  Prompt Engineering in Software Engineering (PROMPT-SE 2026).” It accepts
  direct Research Paper submissions through the EMSE Editorial Manager until
  2027-03-01 and instructs authors to follow the journal guidelines:
  https://link.springer.com/collections/bddiejbihe

Consequently, converting the manuscript to a 10-page ACM workshop paper is not
required and would remove evidence needed for journal review. The remaining
comments were assessed independently of that error.

## Comments accepted and implemented

1. **Connect the distribution statistic to observable changes.** Added a
   clearly post-hoc, non-representative inspection of three maximum-effect Qwen
   records. The cases include omitted gold list elements, a factual field
   substitution, and a semantically benign date-format change. This shows both
   why the statistic can matter and why it is not itself a harm score.
2. **Show threshold sensitivity.** Added a descriptive 0.03/0.05/0.08 screen.
   The identity of deployments labeled practically material changes, while the
   more basic finding—nonzero and deployment-contingent sensitivity—does not.
3. **Foreground the reusable method.** The abstract, introduction, and
   conclusion now emphasize the semantics-derived metamorphic relation,
   stochasticity-adjusted estimator, conservative canonicalizer, and CI
   workflow rather than a hosted-model ranking.
4. **Strengthen the gateway provenance boundary.** The abstract and discussion
   now state that the Sonnet and GPT labels are gateway-deployment observations,
   not independently authenticated vendor checkpoints. Gateway routing,
   wrapping, caching, and backend effects cannot be separated.
5. **Define reproducibility layers.** Section 8 now distinguishes what is fully
   reproducible offline, what is auditable from public metadata and aggregates,
   and what requires authorized benchmark inputs and mutable live services.
6. **Explain the two smaller transformations.** Section 3.3 now distinguishes
   annotation placement (`descriptions_first`) from assertion-member order and
   explains why only unique `required` arrays are safely permuted. The smaller
   observed effects are discussed without claiming a model mechanism.
7. **Report retry behavior.** The core logs contain 17,900 successes plus 20
   retained top-level error rows; 28 successful rows also recorded an internal
   transport retry. Every frozen cell eventually completed. The paper now
   states that permanent representation-specific availability would require a
   separate outcome.

## Comments accepted as limitations, not solved by stronger claims

- The study does not measure downstream economic, safety, or user-experience
  harm. The new cases make changes concrete, but the manuscript explicitly
  keeps business-utility and unsafe-action metrics deployment-specific.
- Hosted endpoints are mutable. Frozen provenance supports audit, not a promise
  that future calls will reproduce identical outputs.
- Raw provider responses and restricted source material are not redistributed.
  The paper no longer describes all layers under the single word
  “reproducible.”

## Comments not implemented

- **No new official Anthropic or OpenAI calls.** Adding a small provider study
  after seeing all existing results would be an outcome-informed extension,
  would spend additional budget, and would not resolve the mutable-service
  problem. A versioned open-weight or official-checkpoint replication is better
  handled as a separately frozen study or reviewer-requested revision.
- **No ACM 10-page conversion.** That rule belongs to the closed workshop, not
  the direct EMSE special-issue submission.
- **No claim that the examples establish real-world harm.** They demonstrate
  observed content changes and operational consequences for exact-output
  consumers, not downstream causal effects.

## Revised objective assessment

The manuscript is now a credible journal submission with unusually close topic
fit, broad black-box evidence, honest subthreshold replications, and a
usable testing intervention. Its main remaining weaknesses are one benchmark,
mutable hosted deployments, no fixed open-weight checkpoint, and no direct
production-utility endpoint. Acceptance is plausible but not predictable; the
submission should be viewed as a serious attempt rather than a safe paper.

## Gateway-provenance addendum

On 2026-08-02, the author obtained informal communication from the third-party
gateway operator stating that the Sonnet and GPT routes ultimately used
Anthropic and OpenAI commercial API platforms, respectively. The operator also
reported behavior consistent with operator-side official-API comparisons while
making clear that no written routing, billing, or subscription evidence was
available. The manuscript therefore reports this as provenance-supporting
evidence, not independent authentication, and retains the term *gateway alias*
for both deployments. Neither the gateway's identity nor the chat screenshots
are included in the public artifact because they are unnecessary for auditing
the reported results and would expose third-party identifying information.
