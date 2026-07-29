# Exploratory Cross-Model SOB Analysis

**Status: post-hoc exploratory only. The frozen confirmatory decisions are unchanged.**

- Records: 100; repeats per representation: 5
- Sonnet 5 decision: `CONFIRMED_FOR_SECOND_MODEL_REPLICATION`
- GPT-5.5 decision: `CROSS_MODEL_REPLICATION_NOT_FOUND`
- Gateway aliases are reported verbatim; upstream model identity is not independently verified.

## Paired model differences

Positive differences mean larger representation sensitivity for Sonnet 5.

| Variant | Sonnet excess | GPT excess | Difference (95% CI) | Holm p |
|---|---:|---:|---:|---:|
| properties_reversed | 0.083 | 0.039 | +0.044 [-0.003, +0.094] | 0.1662 |
| required_reversed | 0.033 | 0.011 | +0.022 [-0.005, +0.054] | 0.1784 |
| keywords_reversed | 0.070 | 0.029 | +0.042 [-0.000, +0.085] | 0.1662 |
| descriptions_first | 0.027 | 0.001 | +0.026 [+0.004, +0.049] | 0.0864 |

## Record-level concordance

| Variant | Spearman rho (95% CI) | Holm p |
|---|---:|---:|
| properties_reversed | -0.011 [-0.246, +0.233] | 1.0000 |
| required_reversed | +0.141 [-0.103, +0.379] | 0.6615 |
| keywords_reversed | +0.038 [-0.214, +0.286] | 1.0000 |
| descriptions_first | +0.045 [-0.222, +0.296] | 1.0000 |

## Fixed schema-feature associations

Only Holm-adjusted p-values below 0.05 are listed here; the JSON report contains every estimate.

- No fixed feature association survived within-family Holm correction.

## Interpretation boundary

These analyses may describe model heterogeneity or generate hypotheses about when sensitivity is larger. They do not reveal an internal neural mechanism, establish a universal ordering effect, or change the preregistered GPT-5.5 decision.
