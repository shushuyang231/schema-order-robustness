# Prospective Qwen Staged Futility Extension

Status: frozen on 2026-08-01 before any Qwen calls.

## Endpoint and model

- Provider: Alibaba Cloud Model Studio / Bailian, China (Beijing).
- OpenAI-compatible base URL: `https://dashscope.aliyuncs.com/compatible-mode/v1`.
- Fixed model snapshot: `qwen3.7-plus-2026-05-26`.
- Thinking is explicitly disabled with `enable_thinking=false`.
- Sampling parameters are omitted, matching the existing deployed-system design.
- Maximum output is 4,096 tokens.

The fixed snapshot was selected from the user's existing Alibaba Cloud access,
not from observed Qwen outcomes. No Qwen completion had been requested when
this protocol was frozen.

## Design

The maximum design reuses the frozen, disjoint 200-record decomposed sample,
the same three Schema representations, the same five repeats, and the same two
primary contrasts as the completed Sonnet, GPT, and DeepSeek runs.

There is exactly one interim look after 40 records (20 medium and 20 hard), or
600 successful calls. The 40 records are selected without Qwen outcomes by a
SHA-256 rank of `study_name|record_id`. If continuation is authorized, the same
request keys remain in the final 200-record dataset and only the missing 160
records are called.

## Frozen futility rule

For each primary contrast, calculate the interim record mean and sample
standard deviation of normalized excess disagreement. Under a plug-in normal
prediction that future record effects are iid with those interim moments,
calculate the conditional probability that the final 200-record point estimate
will be at least 0.05.

- Stop for futility only if both per-contrast probabilities are below 0.10.
- Otherwise continue to the maximum 200 records.
- No early efficacy or confirmation claim is allowed at the interim.
- No additional interim looks are allowed.
- The interim report is retained and disclosed whether the study stops or
  continues.

`STOP_FOR_FUTILITY` means insufficient promise of reaching the study-specific
0.05 practical magnitude. It does not mean an exactly zero effect.

## Calibration provenance

The 40-record timing and 0.10 continuation probability were selected before
Qwen calls using retrospective record-level calibration on the already
completed Sonnet, GPT, and DeepSeek runs. Approximate calibrated futility-stop
rates were 4.8% for the Sonnet-like run, 37.5% for the GPT-like run, and 92.4%
for the DeepSeek-like run. These are design diagnostics, not guarantees about
Qwen.

## Reporting commitment

If the Qwen extension stops, any later manuscript based on this project must
report the stopped interim in the main text or supplement. The model cannot be
silently omitted based on this result. If it continues, final confirmation uses
the original 200-record threshold, record-cluster intervals, permutation tests,
and Holm family; the interim itself remains descriptive and futility-only.
