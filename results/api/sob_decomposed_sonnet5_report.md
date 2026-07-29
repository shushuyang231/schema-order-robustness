# Decomposed Schema-Order Confirmation

Decision: **BOTH_DECOMPOSED_CONTRASTS_CONFIRMED**

Model alias: `claude-sonnet-5`; records: 200; successful responses: 3000.

| Primary contrast | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) | Confirmed |
|---|---:|---:|---:|---|
| property_order | 0.0584 [0.0363, 0.0845] | 0.0004 | -0.0007 [-0.0199, 0.0174] | Yes |
| additional_keyword_order_given_reversed_properties | 0.0768 [0.0498, 0.1061] | 0.0004 | 0.0000 [-0.0167, 0.0166] | Yes |

The two contrasts and the 0.05 practical threshold were frozen before these API calls. A non-confirmed contrast is retained and does not trigger record replacement, threshold changes, or model shopping.
