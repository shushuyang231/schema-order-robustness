# Official DeepSeek Endpoint Replication Result

Run date: 2026-07-24  
Protocol: `protocol/25_official_endpoint_model_panel.md`  
Requested and returned model: `deepseek-v4-flash`  
Official base URL: `https://api.deepseek.com`

## Frozen decision

`DECOMPOSED_CONFIRMATION_NOT_FOUND`

Both order contrasts were statistically detectable after Holm correction, but
both were well below the frozen 0.05 practical threshold:

| Primary contrast | Normalized excess | 95% CI | Holm p | Frozen rule |
|---|---:|---:|---:|---|
| Property order | 0.01325 | [0.00140, 0.02540] | 0.01320 | Not confirmed |
| Additional object-member order with property order fixed | 0.01815 | [0.00570, 0.03220] | 0.00160 | Not confirmed |

The corresponding leaf-value accuracy differences were -0.00543
([-0.02175, 0.01044], Holm p = 0.72026) and 0.00710
([-0.00735, 0.02219], Holm p = 0.72026). Neither supports an accuracy change.

The result is retained as a negative practical replication. It strengthens
endpoint provenance and provider diversity, but it does not establish a
between-model susceptibility difference.

## Operational and data-quality audit

- Expected and successful responses: 3,000.
- Raw log lines: 3,002; two transient incomplete-chunk connection errors were
  later recovered under the identical request keys.
- Duplicate successful request keys: zero.
- Duplicate successful record-condition cells: zero.
- Duplicate response IDs: zero.
- Prompt-repeat hash inconsistencies: zero.
- Returned model identifiers: `deepseek-v4-flash` for all 3,000 successes.
- System fingerprint: one stable value,
  `fp_8b330d02d0_prod0820_fp8_kvcache_20260402`.
- Smoke-record hashes in successful rows: one.
- Exact JSON responses: 2,995.
- Invalid JSON responses: five; all five ended with `finish_reason=length`.
- Overall Schema pass rate: 0.996333 (2,989/3,000).
- Run interval: 2026-07-24T05:41:55Z to 2026-07-24T14:27:17Z.

Token use:

- Input tokens: 4,861,845.
- Cache-hit input tokens: 4,006,784.
- Cache-miss input tokens: 855,061.
- Output tokens: 1,095,139.
- Reasoning tokens: 849,108.
- Estimated charge under the frozen 2026-07-24 CNY price snapshot:
  approximately CNY 3.13.

## Reproducibility hashes

- Manifest SHA-256:
  `DA6030811454B5B28FC54CDFAE158CAC66919196FEA20EBA06B989E5C40046C4`
- Smoke record SHA-256:
  `FF22CA02D3313600F7F80AA7EBFFBFCA412EEB9FDD2F81655BAB189F930F8B32`
- Raw log SHA-256:
  `0C3B8CAC96B1E6310FB048278804E465E818FA54A35E96ADA91441DD81ED2491`
- JSON report SHA-256:
  `1CAA7BF4D6EE4E74D1B009770AEB6A2F3805C02DD9B08A97673753297061457A`
- Markdown report SHA-256:
  `C128D1F14B6C5B84557B1ACB9C0B59F586B66A04063D0D4D4BEC710A1A860512`

An immediate independent evaluator rerun reproduced the JSON report byte for
byte.
