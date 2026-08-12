# Official Qwen-Plus Resource-Plan Result

Status: completed 2026-08-02 under the prospectively frozen 160-record maximum.

## Operational audit

- Requested and returned model: `qwen-plus`.
- Successful frozen request keys: 2,400 / 2,400.
- Raw log: 2,400 successful rows plus one retained, later-recovered arrearage
  error row.
- Schema pass rate: 99.33%.
- Tokens recorded by the provider: 4,033,665 input, 173,769 output, 4,207,434
  total; 563,328 input tokens were reported as cached.

## Frozen decisions

| Contrast | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) | Decision |
|---|---:|---:|---:|---|
| Property order | 0.1255 [0.0861, 0.1674] | 0.0004 | -0.0177 [-0.0392, 0.0003] | Confirmed |
| Additional member order with property order fixed | 0.1229 [0.0853, 0.1624] | 0.0004 | +0.0063 [-0.0142, 0.0251] | Confirmed |

Both preregistered distributional contrasts exceed the 0.05 practical
threshold, have confidence intervals excluding zero, and pass Holm-adjusted
tests. Neither average leaf-value accuracy change is confirmed. The permitted
claim is therefore distributional instability, not universal accuracy harm.

## Post-hoc robustness boundary

The Qwen effects are heterogeneous: the median record effect is zero. Symmetric
10% trimmed means remain 0.0591 and 0.0643; means after deleting the largest
10% of record effects are 0.0488 and 0.0526. The first contrast is therefore
somewhat upper-tail dependent, while the second remains just above the frozen
practical threshold after this deliberately severe deletion. These deletion
analyses are descriptive and do not change the frozen confirmation.

No record-level susceptibility correlation between Qwen-Plus and the Sonnet,
GPT, or DeepSeek runs survived global Holm correction. This argues for a
system-contingent regression-testing recommendation rather than a universal
schema-risk classifier.
