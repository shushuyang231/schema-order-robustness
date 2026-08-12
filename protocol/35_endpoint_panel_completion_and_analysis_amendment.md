# Endpoint-panel completion and effect-analysis amendment

**Freeze time:** 2026-08-12 (Asia/Shanghai), after response collection and the
aggregate completion/provenance audit, but before computing any distributional
effect estimate for the three active deployments.

This is not a preregistration. It is a transparent post-data, pre-effect
analysis amendment. Before this freeze, inspection was limited to transport
status, successful request-key coverage, returned model strings, system
fingerprints, smoke-record hashes, parse status, and aggregate Schema validity.
No endpoint-panel excess-disagreement estimate, confidence interval,
permutation p-value, leaf-accuracy contrast, or cross-deployment concordance was
computed.

## Completion rule

Each active log must contain one successful row for every one of its 3,000
frozen request keys. Top-level error rows remain in the append-only log.
Continuation retries only keys without a successful row, using the identical
record, condition, prompt, requested model, endpoint, smoke record, and request
contract. No effect analysis begins until the aggregate completion audit passes.

## Active evidence and roles

1. `sjtu_zhiyuan1/deepseek-reasoner`: institutional deployment whose first
   completion gate passed; confirmatory deployment-local analysis.
2. `sjtu_zhiyuan1/deepseek-chat`: institutional post-gate recovery deployment;
   reported separately and never presented as a pristine first-gate inclusion.
3. `tokenrhythm/deepseek-v4-flash`: documented-aggregator deployment/channel
   sensitivity analysis; advertised upstream identity is not independently
   verified.
4. SJTU `minimax-m2.7` and `qwen3.6-27b`: retained as operational gate failures,
   not analyzed for effects and not interpreted as null effects.

The two SJTU interfaces and the TokenRhythm route are deployments, not three
independent draws from a model population. They are not pooled, averaged, or
counted as a majority vote.

## Frozen effect analysis

For each completed deployment, evaluate the two already fixed contrasts:

1. `original` versus `properties_reversed`;
2. `properties_reversed` versus `keywords_reversed`.

The record is the independent unit. The effect statistic, 5,000 deterministic
resamples, 95% record-bootstrap interval, within-record permutation test,
leaf-value accuracy analysis, and 0.05 practical screen are inherited unchanged
from the frozen manifests. A deployment-local confirmation requires an effect
of at least 0.05, a confidence-interval lower bound above zero, and a Holm
p-value below 0.05 across that deployment's two contrasts.

Deployment-local decisions are reported even when negative. In addition, the
six raw distributional p-values from the three active deployments are adjusted
together with Holm's method. Only this six-test family may support an omnibus
statement about the active endpoint expansion. No operational failure is
silently removed from the accompanying coverage table.

## Reporting boundary

The original 17,900-response study remains the manuscript's scientific core.
These runs are supplemental/post-submission evidence about deployment
robustness and provenance sensitivity. The analysis does not identify an
upstream checkpoint, establish model-family prevalence, or isolate hardware.
In particular, it cannot support an Ascend-versus-CUDA causal claim.
