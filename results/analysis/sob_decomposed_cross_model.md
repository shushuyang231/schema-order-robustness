# Post-hoc Paired Cross-Model Decomposition

**Exploratory only: specified after both formal reports were observed.**

Difference direction: `sonnet5 minus gpt55`.

| Contrast | Distribution difference (95% CI) | Holm p | Accuracy contrast difference (95% CI) | Holm p |
|---|---:|---:|---:|---:|
| property_order | 0.0256 [-0.0026, 0.0534] | 0.0696 | 0.0052 [-0.0166, 0.0267] | 0.6471 |
| additional_keyword_order_given_reversed_properties | 0.0388 [0.0043, 0.0740] | 0.0664 | 0.0249 [-0.0026, 0.0554] | 0.1732 |

A corrected paired difference may support an exploratory statement about heterogeneity, but it does not retroactively convert the model-specific preregistered decisions into a preregistered cross-model test.
