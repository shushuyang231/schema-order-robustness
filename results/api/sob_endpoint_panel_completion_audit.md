# Endpoint-panel completion audit

This report contains aggregate transport and provenance metadata only; it does not contain response content.

| Run | Unique successes | Missing | Error rows retained | Schema pass rate | Complete |
|---|---:|---:|---:|---:|---|
| sjtu_deepseek_chat | 2999/3000 | 1 | 6 | 0.9883 | No |
| sjtu_deepseek_reasoner | 2997/3000 | 3 | 15 | 0.9973 | No |
| tokenrhythm_deepseek_v4_flash | 2993/3000 | 7 | 7 | 0.9967 | No |

Panel status: **FAIL**. Missing requests must be retried with identical frozen request keys before inference.
