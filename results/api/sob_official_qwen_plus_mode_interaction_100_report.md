# Qwen-Plus Text Mode vs JSON Mode

Decision: **NO_MATERIAL_JSON_MODE_INTERACTION_CONFIRMED**

> JSON Mode means `response_format={"type":"json_object"}`. It is not strict JSON Schema constrained decoding.

| Contrast | Text effect | JSON-Mode effect | Mode change (95% CI) | Holm p | Classification |
|---|---:|---:|---:|---:|---|
| property_order | 0.1391 | 0.1582 | +0.0191 [-0.0199, +0.0594] | 0.4951 | NO_MATERIAL_MODE_CHANGE_CONFIRMED |
| additional_keyword_order_given_reversed_properties | 0.1468 | 0.1219 | -0.0249 [-0.0677, +0.0162] | 0.4951 | NO_MATERIAL_MODE_CHANGE_CONFIRMED |

The mode change is JSON-Mode excess minus text-mode excess at the record level. A material classification requires absolute change at least 0.03, a bootstrap interval excluding zero, and Holm-adjusted p < 0.05.
