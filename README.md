# Testing JSON Schema Instruction Artifacts / JSON Schema 指令工件测试

This repository contains the manuscript, frozen aggregate results, protocols,
and an offline reproduction package for **Testing JSON Schema Instruction
Artifacts: Distributional Robustness under Validation-Equivalent Serialization
and JSON Mode**.

本仓库公开论文、冻结后的聚合结果、实验协议和离线复现包。核心问题是：当
JSON Schema 的序列化顺序改变、验证语义不改变时，它作为大语言模型指令工件
的输出分布是否仍然稳定？结论是：验证等价本身不足以作为 LM-facing 工件的
端到端回归判据；效应取决于具体部署，不能推出“字段永远应该放在前面”的普遍规则。

**Repository snapshot:** 12 August 2026

**Submission target:** Empirical Software Engineering, PROMPT-SE 2026

**Author:** Shengyao Sun, Shanghai Jiao Tong University
**ORCID:** [0009-0008-9175-8226](https://orcid.org/0009-0008-9175-8226)

## Latest evidence / 最新证据

The core study contains **17,900 successful black-box responses**. Each cell
uses five repeated calls and compares cross-serialization disagreement with
within-condition disagreement:

| Deployment | Property order | Additional member order | Practical decision |
| --- | ---: | ---: | --- |
| Sonnet gateway alias | 0.0584 | 0.0768 | both confirmed |
| GPT gateway alias | 0.0329 | 0.0380 | below 0.05 |
| Official DeepSeek endpoint | 0.0133 | 0.0182 | below 0.05 |
| Official Qwen-Plus text | **0.1255** | **0.1229** | both confirmed |
| Qwen-Plus JSON Mode | 0.1582 | 0.1219 | within-mode effects |

The matched Qwen JSON-minus-text changes were +0.0191 and -0.0249; neither
met the separately frozen 0.03 material-interaction rule. These results do not
establish universal accuracy degradation or equivalence between text mode and
JSON Mode. Gateway aliases are reported as observed deployments because their
upstream checkpoint identities were not independently verified.

### Supplemental endpoint panel / 投稿后补充面板

The later panel is explicitly separate from the 17,900-response core. It
completed **9,000/9,000 unique successful request keys** and retained **28**
top-level transport-error rows. The effects were analyzed only after the
completion/provenance audit passed:

| Deployment | Property order | Additional member order | Interpretation |
| --- | ---: | ---: | --- |
| SJTU Zhiyuan-1 `deepseek-chat` (recovery) | 0.0168 | 0.0160 | detectable, below 0.05 |
| SJTU Zhiyuan-1 `deepseek-reasoner` | -0.0005 | 0.0028 | not confirmed |
| TokenRhythm `deepseek-v4-flash` | 0.0039 | -0.0027 | not confirmed |

The six supplemental distribution tests use a single panel-wide Holm family;
none crosses the frozen 0.05 practical screen. SJTU's two aliases share a
stable vLLM fingerprint; TokenRhythm returned no fingerprint. These are
deployment observations, not three independent model samples, and they do not
support an Ascend-versus-CUDA or upstream-checkpoint causal claim.

## Offline reproduction / 离线复现

The reproduction path never calls a model API:

```powershell
python -m pip install -r requirements-paper.txt
.\scripts\reproduce_paper_offline.ps1
```

It compiles the Python sources, runs offline tests, rebuilds tables and figures
from frozen aggregate reports, audits manuscript claims and citations,
regenerates the flat LaTeX/PDF package, and validates the Online Resource 1
archive. Raw provider responses, credentials, restricted benchmark contexts,
and private gateway communications are intentionally excluded.

## Repository contents / 目录

- `paper/manuscript.md` — authoritative English manuscript.
- `paper/emse/main.tex` — editable flat LaTeX source.
- `output/pdf/schema_order_emse_promptse.pdf` — rendered 20-page review PDF.
- `output/artifact/schema_order_emse_online_resource1.zip` — allowlisted offline artifact.
- `results/` and `protocol/` — aggregate reports, manifests, and decision records.
- `PROJECT_HANDOFF.md` — file-level status, checksums, and next actions.

The reusable engineering contribution is a metamorphic test, a
stochasticity-adjusted estimator, a conservative Schema canonicalizer, and a
CI workflow. It removes the tested serialization degree of freedom when that
order is not intentional, while leaving domain-specific validation and safety
checks to the deployment.
