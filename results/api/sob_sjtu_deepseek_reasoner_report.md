# Decomposed Schema-Order Confirmation

Decision: **DECOMPOSED_CONFIRMATION_NOT_FOUND**

Model alias: `deepseek-reasoner`; records: 200; successful responses: 3000.

| Primary contrast | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) | Confirmed |
|---|---:|---:|---:|---|
| property_order | -0.0005 [-0.0111, 0.0114] | 0.6151 | 0.0065 [-0.0085, 0.0220] | No |
| additional_keyword_order_given_reversed_properties | 0.0028 [-0.0070, 0.0129] | 0.6151 | -0.0080 [-0.0221, 0.0057] | No |

The two contrasts and the 0.05 practical threshold were frozen before these API calls. A non-confirmed contrast is retained and does not trigger record replacement, threshold changes, or model shopping.
