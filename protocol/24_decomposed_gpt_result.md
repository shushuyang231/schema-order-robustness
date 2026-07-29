# GPT Decomposed-Contrast Confirmation Result

Date: 2026-07-21

## Decision

**DECOMPOSED_CONFIRMATION_NOT_FOUND** under the frozen practical threshold.

This is not a zero-effect result. Both distribution contrasts were positive and
statistically detectable, but neither reached the preregistered 0.05 practical
threshold.

## Primary distribution results

| Contrast | Normalized excess | 95% CI | Holm p | Practical threshold |
|---|---:|---:|---:|---|
| `original` → `properties_reversed` | 0.03285 | [0.0140, 0.05475] | 0.0004 | Not met |
| `properties_reversed` → `keywords_reversed` | 0.03795 | [0.01590, 0.06315] | 0.0004 | Not met |

The direction is consistent with the Sonnet confirmation, but the practical
magnitude is smaller in this gateway alias.

## Secondary quality signal

The additional-member-order contrast had leaf-value accuracy difference
−0.02482 (95% CI [−0.04631, −0.00674], Holm p=0.0208).  This is a statistically
detectable small negative signal, not a preregistered primary accuracy claim. It
is below the earlier 0.03 engineering-effect context threshold and must be
presented as a cautionary signal requiring independent targeted replication.

## Data-quality audit

- Raw lines: 3,002.
- Final successful cells: 3,000/3,000.
- Two transient server-disconnect rows; both tasks subsequently succeeded.
- Each representation: 1,000 successful responses.
- Duplicate successful cells, request keys, and response IDs: zero.
- Repeat groups with inconsistent prompt hashes: zero.
- Independent evaluator rerun produced a byte-identical JSON report.

## Combined interpretation

The two gateway aliases show the same qualitative direction: validation-
equivalent Schema serialization changes can shift output distributions beyond
ordinary repeated-prompt variation. The Sonnet alias crosses the practical
threshold on both decomposed contrasts; the GPT alias does not. Therefore the
paper should claim a model-contingent practical magnitude, not universal
cross-model replication or a universal accuracy loss.

The next experiment should not be another gateway model chosen for a favorable
result. The next high-value gate is endpoint provenance: an independently
verifiable official API or a fixed open-weight checkpoint, with a new frozen
manifest and the same decomposed contrasts.
