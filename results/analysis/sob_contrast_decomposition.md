# Post-hoc Schema Contrast Decomposition

**Status: exploratory only; preregistered decisions are unchanged.**

`keywords_reversed` also reverses every `properties` mapping. The final contrast below therefore compares it directly with `properties_reversed` to hold recursive property order fixed.

Property-order audit: 100/100 records match.

## sonnet5

| Contrast | Left | Right | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) |
|---|---|---|---:|---:|---:|
| property_order | original | properties_reversed | 0.0831 [0.0447, 0.1277] | 0.0008 | -0.0084 [-0.0333, 0.0139] |
| required_array_order | original | required_reversed | 0.0328 [0.0098, 0.0614] | 0.0008 | -0.0136 [-0.0413, 0.0075] |
| description_member_placement | original | descriptions_first | 0.0270 [0.0091, 0.0486] | 0.0008 | 0.0103 [-0.0020, 0.0270] |
| additional_keyword_order_given_reversed_properties | properties_reversed | keywords_reversed | 0.0578 [0.0272, 0.0938] | 0.0008 | -0.0038 [-0.0200, 0.0135] |

## gpt55

| Contrast | Left | Right | Normalized excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) |
|---|---|---|---:|---:|---:|
| property_order | original | properties_reversed | 0.0389 [0.0182, 0.0634] | 0.0008 | -0.0015 [-0.0136, 0.0101] |
| required_array_order | original | required_reversed | 0.0109 [-0.0022, 0.0258] | 0.0980 | -0.0022 [-0.0107, 0.0066] |
| description_member_placement | original | descriptions_first | 0.0015 [-0.0077, 0.0120] | 0.4109 | 0.0010 [-0.0063, 0.0090] |
| additional_keyword_order_given_reversed_properties | properties_reversed | keywords_reversed | 0.0246 [0.0061, 0.0453] | 0.0066 | -0.0184 [-0.0423, 0.0004] |

## Interpretation boundary

This analysis was specified after the formal outcomes were observed. It can refine construct interpretation and motivate a disjoint confirmatory control, but it cannot create a new confirmatory claim.
