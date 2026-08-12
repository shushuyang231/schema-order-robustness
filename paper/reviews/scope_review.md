# Simulated review: TMLR scope, contribution, and positioning

## Summary

The paper presents a black-box robustness evaluation for schema-guided JSON
generation. Its novelty is not that language models are sensitive to prompt
formatting. The contribution is the combination of specification-derived
metamorphic relations, automatic equivalence guards, repeated stochastic
baselines, separate distribution and correctness oracles, and an auditable
multi-stage study with an official-endpoint subthreshold replication.

## Recommendation: borderline to weak accept

The work is within TMLR's scope as an experimental study of intelligent-system
behavior and an assessment method. It is plausibly publishable if reviewers
value rigorous negative-boundary evidence and reusable testing methodology.
The main rejection risk is that it may be read as a narrow prompt-sensitivity
case study with only one benchmark and no native structured-decoding tests.

## Major comments

1. **Lead with the testing method, not a novelty claim about format
   sensitivity.** The revised introduction now cites the closest formatting,
   output-format, stochastic-evaluation, MMD, API-auditing, and metamorphic
   testing work. It explicitly says general prompt sensitivity and LLM
   metamorphic testing are not new.

2. **Be precise about “structured output.”** The Schema is ordinary prompt
   text. The study does not test provider `response_format`, function calling,
   tool schemas, or constrained decoding. The revised manuscript consistently
   uses “prompt-based schema-guided JSON generation/extraction.”

3. **The subthreshold replications increase credibility.** GPT and
   official DeepSeek do not cross 0.05. Retaining them supports a
   system-contingent boundary and makes the study more useful than a
   positive-only case report. They should not be hidden in the supplement.

4. **Official DeepSeek improves provenance but does not fix mutability.** The
   requested and returned model ID, official base URL, smoke gate, response
   identifiers, time window, and fingerprint are recorded. This supports a
   dated deployed-system result, not a stable checkpoint claim.

5. **Artifact claims must match what can be redistributed.** The revised paper
   distinguishes the local audit archive from the anonymous artifact. The
   supplement includes aggregate reports and hashes but excludes raw provider
   responses, restricted gold, and downloaded benchmark contexts pending
   their own terms.

6. **Engineering value should be concrete.** The four-step deployment test in
   the discussion is useful: generate equivalent serializations, repeat both
   conditions, separate validity/correctness/distribution oracles, and
   investigate excess disagreement without automatically calling it harm.

## Residual rejection risks

- Only 300 medium/hard records from one benchmark are covered.
- The primary positive results are gateway aliases with unverified upstream
  identity.
- No fixed open-weight checkpoint is evaluated.
- The method is demonstrated only for prompt-based Schema presentation.
- The simple public Schema features do not explain sensitivity, so the paper
  offers testing rather than prediction or mechanism.

These are appropriately framed as external-validity limits. Adding models
after inspecting DeepSeek would create a larger selective-reporting risk and is
not recommended for this submission.
