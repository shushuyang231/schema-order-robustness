# Decomposed Schema-Order Confirmation

Decision: **DECOMPOSED_CONFIRMATION_NOT_FOUND**

Model alias: `deepseek-chat`; records: 200; successful responses: 3000.

| Primary contrast | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) | Confirmed |
|---|---:|---:|---:|---|
| property_order | 0.0168 [0.0023, 0.0331] | 0.0052 | -0.0225 [-0.0404, -0.0067] | No |
| additional_keyword_order_given_reversed_properties | 0.0160 [0.0036, 0.0298] | 0.0052 | 0.0131 [-0.0022, 0.0292] | No |

The two contrasts and the 0.05 practical threshold were frozen before these API calls. A non-confirmed contrast is retained and does not trigger record replacement, threshold changes, or model shopping.
