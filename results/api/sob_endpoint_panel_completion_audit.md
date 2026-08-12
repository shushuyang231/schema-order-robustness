# Endpoint-panel completion audit

This report contains aggregate transport and provenance metadata only; it does not contain response content.

| Run | Unique successes | Missing | Error rows retained | Schema pass rate | Complete |
|---|---:|---:|---:|---:|---|
| sjtu_deepseek_chat | 3000/3000 | 0 | 6 | 0.9883 | Yes |
| sjtu_deepseek_reasoner | 3000/3000 | 0 | 15 | 0.9973 | Yes |
| tokenrhythm_deepseek_v4_flash | 3000/3000 | 0 | 7 | 0.9967 | Yes |

Panel status: **PASS**. Missing requests must be retried with identical frozen request keys before inference.
