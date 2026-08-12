# Prospective Resource-Efficient Qwen-Plus Validation

Status: frozen on 2026-08-01 before any `qwen-plus` API call.

## Why this is a new study

The completed 40-record, 600-response `qwen3.7-plus-2026-05-26` interim passed
its prospectively frozen continuation rule. Its two descriptive normalized
excess-disagreement estimates were 0.04175 and 0.05850. That fixed-snapshot
result is retained as an exploratory example; it is not pooled with this study.

The resource plan applies to the requested `qwen-plus` alias rather than the
fixed Qwen3.7 snapshot. Changing the model therefore starts a separately dated
validation. To prevent inspected Qwen3.7 outcomes from influencing the formal
record sample, all 40 records in that pilot are excluded here.

## Endpoint and request contract

- Alibaba Cloud Model Studio / Bailian, China (Beijing).
- OpenAI-compatible base URL:
  `https://dashscope.aliyuncs.com/compatible-mode/v1`.
- Requested model alias: `qwen-plus`.
- Real-time Chat Completions, with `enable_thinking=false`.
- Sampling parameters omitted; maximum output 4,096 tokens.
- An authenticated catalog check and three-call smoke gate precede formal
  requests. Returned-model stability and timestamps are recorded.

Resource-plan deduction is an account/billing property, not a scientific
claim. No `qwen3.7-plus-2026-05-26` response is treated as a `qwen-plus`
response.

## Record sample and conditions

The source is the already frozen, balanced 200-record decomposed sample. After
excluding the Qwen3.7 pilot's 20 medium and 20 hard records, 160 records remain:
80 medium and 80 hard.

Each record uses the same three representations and five repeated calls per
representation:

1. `original`;
2. `properties_reversed`;
3. `keywords_reversed`.

The primary contrasts remain property order and additional object-member order
while recursive property order is held fixed. The independent unit is the
record, not an API call.

## Token-efficient staged algorithm

Stage 1 selects 50 medium and 50 hard records by a frozen SHA-256 ranking,
independent of any Qwen-Plus response. It makes 1,500 formal requests. There is
one futility-only look at 100 records and no early efficacy decision.

For each contrast, estimate the interim record mean and standard deviation of
normalized excess disagreement. A plug-in normal prediction calculates the
conditional probability that the final 160-record mean will be at least 0.05.

- Stop only if both contrast probabilities are below 0.10.
- Otherwise add the remaining 60 records (900 calls) and finish at 160.
- There are no further interim looks, record replacements, or model changes.

At the final 160 records, a contrast is confirmed only when its point estimate
is at least 0.05, its record-bootstrap 95% lower bound is above zero, and its
Holm-adjusted within-record permutation p-value is below 0.05. Both positive
and negative outcomes are retained.

## Budget

The completed Qwen3.7 pilot used 1,073,291 tokens for 600 calls. At that
observed rate, Qwen-Plus Stage 1 is expected to use about 2.68 million tokens;
the 160-record maximum is about 4.29 million. Actual provider tokenization and
resource-plan balance govern billing.
