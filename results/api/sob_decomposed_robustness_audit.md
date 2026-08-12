# Decomposed Effect Robustness Audit

**Status: post-hoc descriptive/exploratory. Confirmatory decisions are unchanged.**

## Effect concentration

| System | Contrast | n | Mean | 10% trimmed | Remove largest 10% | Top-decile positive mass |
|---|---|---:|---:|---:|---:|---:|
| sonnet_gateway | property_order | 200 | 0.0584 | 0.0159 | 0.0068 | 80.2% |
| sonnet_gateway | additional_keyword_order_given_reversed_properties | 200 | 0.0768 | 0.0269 | 0.0166 | 74.2% |
| gpt_gateway | property_order | 200 | 0.0329 | 0.0049 | -0.0059 | 83.8% |
| gpt_gateway | additional_keyword_order_given_reversed_properties | 200 | 0.0380 | 0.0042 | -0.0066 | 85.8% |
| deepseek_official | property_order | 200 | 0.0132 | 0.0012 | -0.0104 | 72.0% |
| deepseek_official | additional_keyword_order_given_reversed_properties | 200 | 0.0182 | 0.0046 | -0.0066 | 72.0% |
| qwen_plus_official | property_order | 160 | 0.1255 | 0.0591 | 0.0488 | 63.3% |
| qwen_plus_official | additional_keyword_order_given_reversed_properties | 160 | 0.1229 | 0.0643 | 0.0526 | 59.5% |
| qwen_plus_json_mode | property_order | 100 | 0.1582 | 0.0854 | 0.0752 | 57.0% |
| qwen_plus_json_mode | additional_keyword_order_given_reversed_properties | 100 | 0.1219 | 0.0546 | 0.0443 | 65.2% |

## Cross-system record concordance

| Pair | Contrast | Shared n | Spearman rho (95% CI) | Global Holm p |
|---|---|---:|---:|---:|
| sonnet_gateway vs gpt_gateway | additional_keyword_order_given_reversed_properties | 200 | -0.132 [-0.289, +0.030] | 1.0000 |
| sonnet_gateway vs gpt_gateway | property_order | 200 | -0.030 [-0.199, +0.142] | 1.0000 |
| sonnet_gateway vs deepseek_official | additional_keyword_order_given_reversed_properties | 200 | +0.093 [-0.078, +0.262] | 1.0000 |
| sonnet_gateway vs deepseek_official | property_order | 200 | +0.092 [-0.072, +0.255] | 1.0000 |
| sonnet_gateway vs qwen_plus_official | additional_keyword_order_given_reversed_properties | 160 | +0.172 [-0.002, +0.339] | 0.5435 |
| sonnet_gateway vs qwen_plus_official | property_order | 160 | +0.058 [-0.124, +0.239] | 1.0000 |
| sonnet_gateway vs qwen_plus_json_mode | additional_keyword_order_given_reversed_properties | 100 | +0.103 [-0.109, +0.311] | 1.0000 |
| sonnet_gateway vs qwen_plus_json_mode | property_order | 100 | +0.125 [-0.105, +0.344] | 1.0000 |
| gpt_gateway vs deepseek_official | additional_keyword_order_given_reversed_properties | 200 | -0.024 [-0.188, +0.138] | 1.0000 |
| gpt_gateway vs deepseek_official | property_order | 200 | +0.024 [-0.131, +0.180] | 1.0000 |
| gpt_gateway vs qwen_plus_official | additional_keyword_order_given_reversed_properties | 160 | +0.089 [-0.088, +0.260] | 1.0000 |
| gpt_gateway vs qwen_plus_official | property_order | 160 | +0.086 [-0.090, +0.263] | 1.0000 |
| gpt_gateway vs qwen_plus_json_mode | additional_keyword_order_given_reversed_properties | 100 | -0.054 [-0.260, +0.164] | 1.0000 |
| gpt_gateway vs qwen_plus_json_mode | property_order | 100 | +0.060 [-0.147, +0.258] | 1.0000 |
| deepseek_official vs qwen_plus_official | additional_keyword_order_given_reversed_properties | 160 | +0.157 [-0.026, +0.326] | 0.8702 |
| deepseek_official vs qwen_plus_official | property_order | 160 | +0.039 [-0.142, +0.219] | 1.0000 |
| deepseek_official vs qwen_plus_json_mode | additional_keyword_order_given_reversed_properties | 100 | +0.126 [-0.096, +0.339] | 1.0000 |
| deepseek_official vs qwen_plus_json_mode | property_order | 100 | -0.005 [-0.224, +0.209] | 1.0000 |
| qwen_plus_official vs qwen_plus_json_mode | additional_keyword_order_given_reversed_properties | 100 | +0.626 [+0.409, +0.802] | 0.0040 |
| qwen_plus_official vs qwen_plus_json_mode | property_order | 100 | +0.618 [+0.383, +0.795] | 0.0040 |

The concentration deletions and all cross-system analyses were specified after observing earlier model reports. They diagnose robustness and heterogeneity; they do not replace or upgrade a frozen confirmatory decision.
