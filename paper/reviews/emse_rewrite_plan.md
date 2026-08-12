# EMSE PROMPT-SE Rewrite Plan

Target: Empirical Software Engineering, PROMPT-SE 2026 special issue.
Backup: Software Quality Journal.
API status: experimental branch closed; no additional model calls.

## New framing

Working title:

> Testing JSON Schema Instruction Artifacts: Distributional Robustness under
> Validation-Equivalent Serialization and JSON Mode

Lead with a software-engineering failure mode: serializers, refactors, code
generators, or middleware can reorder a validation-equivalent JSON Schema
without changing its validator-visible contract, while an LM-facing component
may change its output distribution.

Do not lead with generic prompt-format sensitivity. Do not claim first evidence
that order matters, universal accuracy harm, a model-internal mechanism, or
strict constrained decoding.

## Revised research questions

1. Do validation-equivalent Schema serializations change black-box output
   distributions beyond identical-prompt variability?
2. Do property order and additional Schema-object member order independently
   exceed a prespecified practical threshold across deployed systems?
3. Do these distribution changes imply average schema-compliance or task-value
   degradation?
4. Does provider JSON Mode materially attenuate the order effects for the
   matched Qwen-Plus deployment?
5. Are vulnerable records stable across systems or interfaces, and are the
   mean effects concentrated in a small record subset?

RQ5 is exploratory. The JSON Mode interaction was frozen after observing the
Qwen text-mode interim and must carry that selection disclosure.

## Contribution order

1. A JSON-Schema-semantics-derived metamorphic testing method.
2. A stochasticity-adjusted excess-disagreement estimator with record-cluster
   inference and a prespecified practical threshold.
3. Positive and negative practical replications across gateway aliases and
   official DeepSeek/Qwen endpoints.
4. A matched Qwen text-vs-JSON-Mode boundary showing that syntax enforcement
   did not demonstrate attenuation of semantic distribution shifts.
5. A conservative canonicalizer and CI regression guard that remove the tested
   representation degree of freedom by construction.

## Main result structure

- Primary/follow-up table: Sonnet 0.0584/0.0768; GPT 0.0329/0.0380;
  DeepSeek 0.0133/0.0182; Qwen-Plus 0.1255/0.1229.
- JSON Mode table: within-mode 0.1582/0.1219; matched changes
  +0.0191/-0.0249, neither material interaction confirmed.
- Accuracy table: retain all null/secondary results; explicitly separate
  distributional instability from average task harm.
- Robustness table: median, 10% trimmed mean, largest-decile deletion, and
  medium/hard descriptive strata.
- Concordance: no cross-system record profile; strong post-hoc concordance
  between the two matched Qwen interfaces.

## Required wording boundaries

Permitted:

> In this Qwen-Plus deployment, JSON Mode preserved JSON syntax but did not
> demonstrate attenuation of validation-equivalent serialization sensitivity.

Not permitted:

> JSON Mode has no effect.

The interaction confidence intervals include both modest attenuation and
amplification. Absence of a confirmed material interaction is not equivalence.

## Artifact and practical intervention

- Include `src/canonicalize_json_schema.py` as the deterministic mitigation.
- Report that all three stored variants collapse for all 200 records under the
  conservative canonicalizer.
- Preserve all arrays except unique `required` arrays; never describe the tool
  as a complete JSON Schema equivalence checker.
- Present the metamorphic runner as a CI regression test for system updates,
  provider changes, prompt refactors, and schema generator changes.

## Submission sequence

1. Rewrite `paper/manuscript.md` around the structure above.
2. Replace TMLR-specific formatting/disclosure text with the EMSE author
   instructions while retaining the generative-AI disclosure as required.
3. Regenerate tables/figures and build a clean non-anonymous or journal-required
   manuscript package.
4. Run the complete offline test/artifact/PDF audit.
5. Submit to EMSE as Research Paper, mark PROMPT-SE 2026, and explain special
   issue fit in the cover letter.
