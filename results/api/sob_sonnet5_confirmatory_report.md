# Sonnet 5 Repeated-Measures Schema-Order Analysis

**Decision: CONFIRMED_FOR_SECOND_MODEL_REPLICATION**

> Confirmatory analysis on the frozen 100-record sample.

- Responses: 2500
- Schema pass rate: 99.9%
- Returned models: `{"claude-sonnet-5": 2500}`

| Variant | Leaf accuracy | Token F1 | Perfect | Within normalized disagreement |
|---|---:|---:|---:|---:|
| original | 81.1% | 89.0% | 46.4% | 0.220 |
| properties_reversed | 80.3% | 88.2% | 45.4% | 0.261 |
| required_reversed | 79.7% | 87.8% | 46.4% | 0.236 |
| keywords_reversed | 79.9% | 87.7% | 45.4% | 0.257 |
| descriptions_first | 82.1% | 89.8% | 47.8% | 0.218 |

| Variant vs original | Normalized excess (95% CI) | Holm p | Leaf difference (95% CI) | Holm p |
|---|---:|---:|---:|---:|
| properties_reversed | 0.083 [0.046, 0.128] | 0.0008 | -0.008 [-0.034, +0.016] | 1.0000 |
| required_reversed | 0.033 [0.009, 0.062] | 0.0008 | -0.014 [-0.039, +0.007] | 1.0000 |
| keywords_reversed | 0.070 [0.039, 0.107] | 0.0008 | -0.012 [-0.035, +0.011] | 1.0000 |
| descriptions_first | 0.027 [0.009, 0.050] | 0.0008 | +0.010 [-0.002, +0.027] | 0.6871 |
