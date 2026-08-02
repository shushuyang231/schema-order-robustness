# Qwen-Plus JSON Mode Boundary Result

Status: completed 2026-08-02 under the prospectively frozen 100-record matched
ablation. No further model or provider arm is authorized by this study.

## Operational audit

- Requested and returned model: `qwen-plus`.
- JSON Mode request: `response_format={"type":"json_object"}` with thinking
  disabled. This is not strict JSON Schema constrained decoding.
- Successful frozen request keys: 1,500 / 1,500; errors: zero.
- All 1,500 stored request contracts record `json_object` mode.
- Schema pass rate: 98.73%.
- Tokens: 2,501,580 input, 111,215 output, 2,612,795 total; 264,192
  input tokens were reported as cached.
- Within-mode report SHA256:
  `c86990e79544f86f3e628349f3cabbaad2e3cb6db626ae1212e5eaa6ed8fd716`.
- Matched-interaction report SHA256:
  `f9de7f43a86e18567ab0b4cde2cf538b06286148f68cea9ca666a2017294c55b`.
- Raw JSON Mode log SHA256:
  `0e471ed92c09d79510505e1cb69ced7245405e1bbfdd984b522f136927fe6966`.

The completed text and JSON Mode Qwen studies together recorded 6,535,245
input tokens, 284,984 output tokens, and 6,820,229 total tokens; 827,520 input
tokens were reported as cached.

## Frozen within-JSON-Mode results

| Contrast | JSON Mode excess (95% CI) | Holm p | Leaf accuracy difference (95% CI) | Decision |
|---|---:|---:|---:|---|
| Property order | 0.1582 [0.1049, 0.2194] | 0.0004 | -0.0246 [-0.0633, 0.0068] | Confirmed |
| Additional member order with property order fixed | 0.1219 [0.0724, 0.1803] | 0.0004 | +0.0089 [-0.0243, 0.0397] | Confirmed |

Both order effects exceed the frozen 0.05 practical threshold in JSON Mode.
Neither average leaf-value accuracy change is confirmed.

## Frozen matched mode interactions

| Contrast | Text excess | JSON Mode excess | JSON-minus-text change (95% CI) | Holm p | Decision |
|---|---:|---:|---:|---:|---|
| Property order | 0.1391 | 0.1582 | +0.0191 [-0.0199, 0.0594] | 0.4951 | No material mode change confirmed |
| Additional member order | 0.1468 | 0.1219 | -0.0249 [-0.0677, 0.0162] | 0.4951 | No material mode change confirmed |

The study does not prove that the modes are equivalent. It shows that neither
interaction met the prospectively frozen requirements of absolute mean change
at least 0.03, a confidence interval excluding zero, and Holm-adjusted
`p < 0.05`. JSON syntax enforcement therefore was not demonstrated to attenuate
the tested semantic distribution shifts.

## Post-hoc robustness boundary

In JSON Mode, symmetric 10% trimmed effects are 0.0854 and 0.0546. After
removing the largest 10% of record effects, the means are 0.0752 and 0.0443.
The effects remain heterogeneous, with a zero record median in both contrasts.

Matched record susceptibility is strongly concordant between text and JSON
Mode: Spearman rho is 0.618 for property order and 0.626 for additional member
order; both global-Holm p=0.0040. This analysis is post-hoc, but it supports a
stable system-specific vulnerability profile across the two Qwen interfaces.

## Permitted conclusion

For this Qwen-Plus deployment and benchmark, `json_object` syntax enforcement
did not remove validation-equivalent serialization sensitivity. JSON syntax
validity and semantic distributional robustness are distinct properties.
This is a system-and-task result, not a universal statement about JSON Mode or
structured decoding.
