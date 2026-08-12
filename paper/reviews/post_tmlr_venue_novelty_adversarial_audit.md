# Post-TMLR venue and novelty audit

Audit date: 2026-08-02
Status: updated after the frozen Qwen-Plus 160-record confirmation and the
post-hoc four-system robustness audit.

## Recommendation

Primary target: **Empirical Software Engineering, PROMPT-SE 2026 special
issue**, submission deadline 2027-03-01.

Backup: **Software Quality Journal** as a regular Original Paper.

Do not submit the unchanged TMLR manuscript. Finish the frozen Qwen analysis,
run at most the already frozen 100-record JSON Mode ablation, add the
canonicalization/regression tool, and rewrite the paper for empirical software
engineering.

## Why the primary target changed

The EMSE special issue is unusually close to the actual contribution. Its call
treats prompts, message templates, agent communication schemas, and other
instruction artifacts as first-class study objects. It explicitly seeks
empirical work on structured schemas, prompt testing and quality assurance,
reproducibility, and negative or non-significant findings:

https://link.springer.com/collections/bddiejbihe

The regular EMSE scope covers controlled and replicated empirical studies,
verification/validation, quality assurance, and AI applied to software
engineering:

https://link.springer.com/journal/10664/aims-and-scope

This directly addresses the TMLR audience-interest risk. It does not lower the
scientific threshold: the special issue states that submissions receive the
standard rigorous journal review and are evaluated for significance, technical
quality, scholarship, and presentation.

SQJ remains the safer backup because its official scope explicitly accepts
research, technique, and case-study papers on software testing, metrics, and
quality-assurance methods:

https://link.springer.com/journal/11219/aims-and-scope

## Subjective probability ranges

These are calibrated judgment ranges, not publisher acceptance statistics.
They assume accurate reporting, a clean English rewrite, and no newly
discovered arithmetic or provenance problem.

| Venue/route | Current evidence plus major rewrite | With frozen JSON Mode arm, tool, and major rewrite | Main reason |
|---|---:|---:|---|
| EMSE PROMPT-SE special issue | 30-40% | **40-50% (completed)** | Exceptional topical fit, official-provider confirmation, and a matched interface boundary; high empirical breadth and presentation expectations remain |
| Software Quality Journal | 40-55% | **50-60% (completed)** | Strong testing/quality fit and a practical tool contribution; one-benchmark scope is more tolerable |
| Journal of Systems and Software | 15-25% | 20-35% | In scope, but likely to expect broader validation and stronger general software-engineering significance |
| Information and Software Technology | 15-25% | 20-35% | Testing is in scope, but the work must demonstrate improvement to software-development practice |

The Qwen result raises the ceiling but does not make acceptance predictable.
The best EMSE range only reaches roughly even odds after the interface ablation,
tool contribution, and a venue-specific rewrite. It does make a full review
more plausible than the TMLR version because the venue asks exactly for this
class of instruction-artifact evidence.

## Qwen-Plus outcome and adversarial robustness check

The prospective 160-record Qwen-Plus study completed all 2,400 frozen request
keys and passed its operational gate. Both decomposed contrasts exceeded the
0.05 practical threshold: property order was 0.1255 (95% CI 0.0861--0.1674;
Holm p=0.0004), and additional object-member order with property order fixed
was 0.1229 (0.0853--0.1624; Holm p=0.0004). Neither leaf-value accuracy change
was confirmed.

The effect is heterogeneous and should not be described as universal. The
record median is zero for both contrasts. However, symmetric 10% trimmed means
remain 0.0591 and 0.0643. Removing the largest 10% of records yields 0.0488 and
0.0526, respectively. Thus the result is not a single-record artifact, but the
property-order mean is materially influenced by the upper tail. Hard-schema
descriptive means (0.1861 and 0.1741) exceed medium-schema means (0.0649 and
0.0718); this is post-hoc evidence, not a new confirmatory subgroup claim.

Across Sonnet, GPT, DeepSeek, and Qwen-Plus, no pairwise record-susceptibility
correlation survived a global Holm correction. This strengthens the
system-contingent testing interpretation and weakens any proposal for a simple
universal vulnerability detector.

The prospectively frozen Qwen-Plus JSON Mode arm subsequently completed 1,500
of 1,500 requests with the exact `json_object` request contract. Both within-mode
effects were confirmed: 0.1582 for property order and 0.1219 for additional
member order (both Holm p=0.0004). The matched JSON-minus-text changes were
+0.0191 and -0.0249; both intervals included zero, both absolute point estimates
were below the frozen 0.03 mode-interaction threshold, and both Holm p-values
were 0.4951. The correct result is therefore **no material mode interaction was
confirmed**, not proof of mode equivalence. JSON Mode did not demonstrate an
attenuation of serialization sensitivity.

A post-hoc audit found strong matched-record concordance between Qwen text and
JSON Mode (Spearman rho 0.618 and 0.626; both global-Holm p=0.0040). This makes
the interface-boundary finding more coherent, while remaining exploratory.

## Updated novelty boundary

### Claims that are no longer defensible

1. First discovery that prompt formatting changes LLM behavior.
2. First discovery that structured or schema-valid output can be semantically
   wrong.
3. First use of metamorphic testing for LLMs.
4. First observation that property order matters in structured generation.
   Google documentation explicitly says property order is important and warns
   that mixing schema and prompt field order can lead to output errors.
5. Universal harm, universal accuracy degradation, or a model-internal causal
   mechanism.

### Still defensible, with "to our knowledge"

The located literature does not combine all of the following:

1. validation-semantics-grounded JSON Schema reorderings as metamorphic
   relations;
2. fixed task content with only schema serialization changed;
3. repeated black-box calls under each representation;
4. an excess-disagreement estimator that subtracts within-representation
   stochasticity from cross-representation disagreement;
5. separate distribution, schema-validity, and gold-value oracles;
6. cross-system practical-threshold evidence including subthreshold
   replications; and
7. a matched provider JSON Mode boundary test plus a deployable
   canonicalization/regression guard.

The novelty is therefore a **testing method and empirical boundary**, not the
generic phenomenon that order or formatting can matter.

## Closest new threats found in August 2026

- StructHallu-Drift applies realistic schema mutations across three structured
  tasks and four models, and separates syntax from semantic fidelity. It is
  broader than this paper, but its mutations change schema meaning or schema
  identity rather than validation-equivalent serialization order:
  https://aclanthology.org/2026.surgellm-1.22/
- PARSE treats JSON schemas as contracts to optimize for LLM consumption and
  evaluates three extraction datasets. It raises the engineering bar because
  it provides an intervention, not just a diagnosis:
  https://aclanthology.org/2025.emnlp-industry.184/
- Schema Reinforcement Learning/SchemaBench evaluates validity across roughly
  40,000 schemas and improves structured generation through training. It does
  not test equivalent serialization order:
  https://aclanthology.org/2025.acl-long.243/
- OrderBench compares prompt-only and JSON-schema modes and shows that schema
  validity does not ensure semantic success. Its "ordering" is restaurant
  ordering, not member order, but it makes an interface-mode comparison an
  expected baseline:
  https://arxiv.org/abs/2607.18261
- Google documents property ordering and warns about mismatched schema/prompt
  order. This is the strongest threat to any broad novelty claim and should be
  cited as practitioner motivation rather than hidden:
  https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/control-generated-output

## Capped design that best improves acceptance odds

### Paid arm: one final matched interface ablation (completed)

- Reuse the 100 Qwen-Plus record IDs and 1,500 text-mode calls frozen before
  Qwen outcomes.
- Add only 1,500 Qwen-Plus calls with
  `response_format={"type":"json_object"}` and thinking disabled.
- Keep messages, schema strings, three representations, five repeats, records,
  model alias, and endpoint fixed.
- Test the two within-JSON-Mode order effects and the two paired mode-by-order
  interactions under the frozen 0.05/0.03 thresholds.
- Call it JSON Mode, never strict JSON Schema constrained decoding.
- The arm completed with both within-mode contrasts confirmed and no material
  mode interaction confirmed. Stop here; do not add another model.

### Zero-token additions

1. Conservative schema canonicalizer: sort all JSON object members and unique
   `required` arrays; preserve all other arrays. The current audit confirms
   that all three variants collapse for all 200 decomposed records.
2. CI regression gate: fail when a production schema is non-canonical or when
   repeated equivalent-serialization effects exceed a configured threshold.
3. Effect concentration: report trimmed means, top-record contribution, and
   schema-complexity strata so that the Qwen result cannot be dismissed as a
   few outliers.
4. Cross-system record transfer: report whether records vulnerable in one
   system predict vulnerability in another; retain a negative result.
5. Full selection timeline: disclose that Qwen3.7 was exploratory, Qwen-Plus
   was a new resource-compatible prospective study, and JSON Mode was designed
   after seeing the Qwen-Plus text-mode interim.

## Required paper repositioning

Suggested title:

> Testing JSON Schema Instruction Artifacts: Distributional Robustness under
> Validation-Equivalent Serialization and JSON Mode

Suggested contribution order:

1. specification-derived metamorphic oracle;
2. stochasticity-adjusted distribution test;
3. empirical boundary across systems and provider modes;
4. auditable canonicalization and CI regression guard;
5. transparent negative results for average accuracy and practical replication.

The abstract should lead with a software-engineering failure mode: source-code
generators, serializers, or refactors can reorder a validation-equivalent
schema without changing its contract, yet an LM-facing system may change
behavior. It should not lead with a claim that LLMs are generally sensitive to
formatting.

## Hard stop and contingency

- Both the Qwen text-mode maximum and the capped JSON Mode arm are complete.
  No further API experiment is justified before submission.
- If JSON Mode is not covered by the same resource plan, do not incur new
  pay-as-you-go cost merely to preserve the plan; use the zero-token tool route
  and prefer SQJ.
- A second dataset or fixed open-weight checkpoint is reviewer-response work,
  not a pre-submission prerequisite under the current budget and deadline.
