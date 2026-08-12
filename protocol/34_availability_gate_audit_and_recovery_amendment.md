# Post-outcome Availability-Gate Audit and Recovery Amendment

**Audit date:** 2026-08-11 (Asia/Shanghai).

This is a transparent post-outcome deviation record, not a prospective
preregistration. Protocol 32 required exactly one three-completion smoke gate
per requested model and operational failure after a failed gate. The wrapper
was later rerun and issued additional smoke gates. All records are retained;
none are deleted or relabelled as if the repeat had been the first gate.

## Observed gate history

| Requested model | First completion gate | Later completion gate | Formal interpretation |
|---|---|---|---|
| `deepseek-chat` | failed (`20260810T062222543847Z`) | passed (`20260810T155406197510Z`) | post-gate recovery deployment; not a pristine first-gate inclusion |
| `deepseek-reasoner` | passed (`20260810T062235728658Z`) | passed again (`20260810T155419514943Z`) | first gate controls inclusion; second gate is a redundant operational check |
| `minimax-m2.7` | failed (`20260810T062250849493Z`) | failed again (`20260810T155434850929Z`) | operational failure; no further availability attempts |
| `qwen3.6-27b` | failed (`20260810T062305804268Z`) | failed again (`20260810T155449983881Z`) | operational failure; no further availability attempts |

Earlier `--catalog-only` requests do not count as completion smoke gates. They
confirmed all four requested aliases in the authenticated catalog but sent no
generation request.

## Recovery rule from this audit onward

- Resume `deepseek-chat` only with the passed recovery smoke file
  `data/raw/official_smoke/sjtu_zhiyuan1_deepseek-chat_20260810T155406197510Z.json`.
- Resume `deepseek-reasoner` only with its first passed smoke file
  `data/raw/official_smoke/sjtu_zhiyuan1_deepseek-reasoner_20260810T062235728658Z.json`.
- Do not send new catalog or smoke requests when resuming either JSONL. Load
  successful request keys and retry only unsuccessful or unattempted keys.
- Do not retry the MiniMax or Qwen availability gates. Preserve them as
  operational failures; this is not evidence of a null order effect.
- If an endpoint returns a different model identifier or a materially changed
  fingerprint, stop or split the deployment period rather than silently pool.

## Reporting boundary

The SJTU expansion is supplemental/post-submission evidence. `deepseek-chat`
must be described as a recovered deployment after an initially failed gate.
The original official Qwen/DeepSeek evidence remains the main scientific core.
No channel is counted as an independent model sample, no NPU-versus-GPU causal
claim is made, and no panel-level “at least one model confirms” claim is made
without correction across the complete panel family.

## Post-run completion audit (2026-08-12)

The first traversal of each active 3,000-request log reached the final planned
position, but the runner originally returned success even when isolated
transport failures remained. An aggregate audit found 2,999 unique successful
request keys for `deepseek-chat`, 2,997 for `deepseek-reasoner`, and 2,993 for
the separately labelled TokenRhythm deployment. Thus 11 of 9,000 frozen keys
still lacked a successful response. All error rows are retained.

This is an execution-status bug, not an analysis change. The runner has been
amended to return a nonzero exit code unless every frozen request key has a
successful row. Identical-key continuation may retry only the 11 unsuccessful
keys; successful keys, records, conditions, prompts, thresholds, and analysis
rules remain frozen. No inferential result is computed until the aggregate
completion audit passes.
