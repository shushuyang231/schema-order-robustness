# Decomposed Schema-Order Confirmation

Decision: **DECOMPOSED_CONFIRMATION_NOT_FOUND**

Model alias: `deepseek-v4-flash`; records: 200; successful responses: 3000.

| Primary contrast | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) | Confirmed |
|---|---:|---:|---:|---|
| property_order | 0.0132 [0.0014, 0.0254] | 0.0132 | -0.0054 [-0.0217, 0.0104] | No |
| additional_keyword_order_given_reversed_properties | 0.0182 [0.0057, 0.0322] | 0.0016 | 0.0071 [-0.0073, 0.0222] | No |

The two contrasts and the 0.05 practical threshold were frozen before these API calls. A non-confirmed contrast is retained and does not trigger record replacement, threshold changes, or model shopping.
