# Amendment: TokenRhythm single-model execution rate

**Freeze date:** 2026-08-11 (Asia/Shanghai), before any TokenRhythm
catalog/completion request for this single-model execution.

The active TokenRhythm model remains the predeclared `deepseek-v4-flash` entry
from Protocol 32. The provider documentation specifies the OpenAI-compatible
base URL and request paths but does not publish a request-rate limit. To avoid
turning an undocumented service limit into a source of avoidable operational
failures, the full run uses a minimum one-second interval between request
starts (`request_interval_seconds = 1.0`). This changes only pacing, not the
messages, model ID, output cap, response contract, sample, repeats, scoring,
or stopping rule.

No additional TokenRhythm model is added after observing outcomes. If the
endpoint still returns rate-limit or connection errors, the saved JSONL is
resumed with the identical request keys after service recovery.
