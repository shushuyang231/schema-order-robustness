# Core run retry audit

This report contains aggregate transport metadata only; it does not contain response content.

| Run | Successful | Top-level error rows | Successful rows with internal retry | Complete |
|---|---:|---:|---:|---|
| sonnet_initial | 2500 | 11 | 17 | Yes |
| gpt_initial | 2500 | 3 | 5 | Yes |
| sonnet_decomposed | 3000 | 1 | 2 | Yes |
| gpt_decomposed | 3000 | 2 | 3 | Yes |
| deepseek_decomposed | 3000 | 2 | 1 | Yes |
| qwen_text_decomposed | 2400 | 1 | 0 | Yes |
| qwen_json_mode | 1500 | 0 | 0 | Yes |

Across 17,920 logged rows, 17,900 were successful and 20 were retained top-level error rows. A further 28 successful rows recorded at least one internal retry. All frozen request keys eventually completed.

Raw logs are intentionally not redistributed. File hashes bind these aggregate counts to the locally retained source logs.
