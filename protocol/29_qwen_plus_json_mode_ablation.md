# Prospective Qwen-Plus JSON Mode Ablation

Status: frozen on 2026-08-02 before any JSON Mode call.

Provenance note: before any JSON Mode call, the source interim report was
regenerated to add the explicit maximum record count (160) and correct one
sentence that had mistakenly said 200. The interim decision and every effect
estimate were unchanged; the JSON Mode manifest was re-hashed after this
metadata-only correction.

## Motivation and selection disclosure

The Qwen-Plus text-mode 100-record futility report was inspected before this
study was designed. It showed normalized excess disagreement near 0.14 for
both decomposed order contrasts. This follow-up therefore does not pretend that
its hypothesis was selected blind to the text-mode result.

The 100 record IDs were nevertheless fixed by SHA-256 ranking before any
Qwen-Plus response, with 50 medium and 50 hard schemas. No record is selected,
replaced, or weighted by its observed effect.

## Question

Does Alibaba Qwen-Plus JSON Mode (`response_format={"type":"json_object"}`)
change serialization-order sensitivity relative to the otherwise identical
prompt-only/text-mode interface?

JSON Mode is a syntax-oriented provider control. It is **not** passed a JSON
Schema and must never be described as strict JSON Schema constrained decoding.

## Matched design and cost cap

- Model: official Alibaba Bailian `qwen-plus`, non-thinking.
- Records: the already frozen Qwen-Plus interim 100.
- Representations: `original`, `properties_reversed`, `keywords_reversed`.
- Repeats: five independent calls per representation.
- New requests: 1,500.
- Reused comparison arm: the existing 1,500 text-mode calls on the same records.
- There is no interim look, early-success rule, record replacement, or new model.

The only request-body change is adding
`response_format={"type":"json_object"}`. A new three-call JSON Mode smoke gate
must pass, and its sanitized request contract must exactly match the manifest.

## Frozen analyses

1. Within JSON Mode, apply the existing two-contrast rule: estimate normalized
   excess disagreement, use record bootstrap confidence intervals and
   within-record label permutations, correct the two contrasts with Holm, and
   compare against the 0.05 practical threshold.
2. For each record and contrast, subtract the already observed text-mode excess
   disagreement from the new JSON-Mode excess disagreement. Use a record
   bootstrap 95% interval and a two-sided record sign-flip test, with Holm
   correction across the two contrasts.
3. Call a mode interaction materially attenuating or amplifying only when its
   absolute mean is at least 0.03, the confidence interval excludes zero, and
   the Holm-adjusted p-value is below 0.05.
4. Retain attenuation, persistence, amplification, and inconclusive outcomes.

The mode-interaction analysis is prospectively fixed for the new arm, but its
motivation followed inspection of the text-mode outcome. This history must be
reported in the paper.

## Engineering interpretation

- Persistence would show that JSON syntax enforcement is not sufficient for
  semantic distributional stability under equivalent schema reorderings.
- Attenuation would quantify a low-cost provider-mode mitigation.
- Amplification would expose an interface interaction requiring explicit
  regression testing.
- An inconclusive result would preserve the original prompt-only scope and
  should not trigger another model search.

Separately, deterministic conservative canonicalization sorts JSON object
members and unique `required` arrays before prompt construction. It removes the
tested representation degree of freedom by construction; it does not claim to
improve reasoning or average correctness.
