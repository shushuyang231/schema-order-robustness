# Endpoint expansion: deployment-level summary

**Status: supplemental post-submission evidence. Deployments are not independent model samples.**

| Deployment | Contrast | Effect (95% CI) | Local Holm p | Panel Holm p | Local decision |
|---|---|---:|---:|---:|---|
| sjtu_deepseek_chat_recovery | property_order | 0.0168 [0.0023, 0.0331] | 0.0052 | 0.0156 | not confirmed |
| sjtu_deepseek_chat_recovery | additional_keyword_order_given_reversed_properties | 0.0160 [0.0036, 0.0298] | 0.0052 | 0.0156 | not confirmed |
| sjtu_deepseek_reasoner | property_order | -0.0005 [-0.0111, 0.0114] | 0.6151 | 1.0000 | not confirmed |
| sjtu_deepseek_reasoner | additional_keyword_order_given_reversed_properties | 0.0028 [-0.0070, 0.0129] | 0.6151 | 0.9518 | not confirmed |
| tokenrhythm_deepseek_v4_flash | property_order | 0.0039 [-0.0064, 0.0163] | 0.4759 | 0.9518 | not confirmed |
| tokenrhythm_deepseek_v4_flash | additional_keyword_order_given_reversed_properties | -0.0027 [-0.0112, 0.0064] | 0.7101 | 1.0000 | not confirmed |

Operational coverage: SJTU MiniMax-M2.7 and Qwen3.6-27B remain failed availability gates and are not scientific null results.

The panel-level Holm values cover all six active deployment-by-contrast distributional tests. No pooling, model vote, checkpoint-identity claim, or NPU-versus-GPU claim is made.
