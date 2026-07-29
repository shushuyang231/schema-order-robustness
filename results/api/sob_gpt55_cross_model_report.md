# Repeated-Measures Schema-Order Analysis

**Decision: CROSS_MODEL_REPLICATION_NOT_FOUND**

> Confirmatory analysis on the frozen 100-record sample.

- Responses: 2500
- Schema pass rate: 99.7%
- Returned models: `{"gpt-5.5": 2500}`

| Variant | Leaf accuracy | Token F1 | Perfect | Within normalized disagreement |
|---|---:|---:|---:|---:|
| original | 84.7% | 90.5% | 53.2% | 0.225 |
| properties_reversed | 84.6% | 90.1% | 54.2% | 0.238 |
| required_reversed | 84.5% | 90.6% | 52.6% | 0.230 |
| keywords_reversed | 82.7% | 88.7% | 51.8% | 0.244 |
| descriptions_first | 84.8% | 90.5% | 52.4% | 0.228 |

| Variant vs original | Normalized excess (95% CI) | Holm p | Leaf difference (95% CI) | Holm p |
|---|---:|---:|---:|---:|
| properties_reversed | 0.039 [0.017, 0.063] | 0.0008 | -0.002 [-0.013, +0.010] | 1.0000 |
| required_reversed | 0.011 [-0.002, 0.028] | 0.0996 | -0.002 [-0.011, +0.006] | 1.0000 |
| keywords_reversed | 0.029 [0.005, 0.059] | 0.0008 | -0.020 [-0.042, -0.002] | 0.2040 |
| descriptions_first | 0.001 [-0.008, 0.012] | 0.4043 | +0.001 [-0.006, +0.009] | 1.0000 |
