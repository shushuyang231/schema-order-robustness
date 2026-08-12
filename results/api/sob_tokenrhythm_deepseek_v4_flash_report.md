# Decomposed Schema-Order Confirmation

Decision: **DECOMPOSED_CONFIRMATION_NOT_FOUND**

Model alias: `deepseek-v4-flash`; records: 200; successful responses: 3000.

| Primary contrast | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) | Confirmed |
|---|---:|---:|---:|---|
| property_order | 0.0039 [-0.0064, 0.0163] | 0.4759 | -0.0080 [-0.0204, 0.0035] | No |
| additional_keyword_order_given_reversed_properties | -0.0027 [-0.0112, 0.0064] | 0.7101 | -0.0006 [-0.0154, 0.0140] | No |

The two contrasts and the 0.05 practical threshold were frozen before these API calls. A non-confirmed contrast is retained and does not trigger record replacement, threshold changes, or model shopping.
