# Testing JSON Schema Instruction Artifacts / JSON Schema 指令工件测试

This repository contains the paper, frozen aggregate results, and offline
reproduction package for **Testing JSON Schema Instruction Artifacts:
Distributional Robustness under Validation-Equivalent Serialization and JSON
Mode**. The work treats a serialized JSON Schema as both a validation contract
and an instruction artifact consumed by a language-model software component.

本仓库公开论文、冻结后的汇总结果和离线复现包。研究的核心问题是：当
JSON Schema 的序列化顺序改变、但验证语义不变时，它作为大语言模型指令
工件的行为分布是否仍然稳定。结论是：**验证等价本身不足以作为面向 LM
Schema 工件的行为回归判据**；效应取决于具体部署，不能据此提出“字段永远
应该排在前面”的通用规则。

**Repository snapshot:** 12 August 2026
**Submission target:** Empirical Software Engineering, PROMPT-SE 2026
**Author:** Shengyao Sun, Shanghai Jiao Tong University
**ORCID:** [0009-0008-9175-8226](https://orcid.org/0009-0008-9175-8226)

## Latest evidence

### 最新结果（2026 年 8 月）

正式核心研究包含 17,900 个成功的黑盒响应；每个条件重复调用 5 次。Sonnet
网关和官方 Qwen-Plus 文本部署的两个主要对比均超过预先冻结的 0.05 工程筛选
线；GPT 网关和 DeepSeek 官方端点的效应虽可统计检测，但没有越过这条实际量级
筛选线。Qwen 的 JSON Mode 匹配实验没有证明它会实质性削弱顺序敏感性。此前
因资源权益问题停止的 600 次 Qwen3.7 探索性响应不进入正式结果。

The core study contains **17,900 successful black-box responses**. Each
condition uses five repeated calls, and the analysis compares cross-
serialization disagreement with repeated-call disagreement. The two primary
decomposed contrasts and the frozen 0.05 practical screen are:

| Deployment | Property order | Additional Schema-member order |
| --- | ---: | ---: |
| Sonnet gateway alias | 0.0584 | 0.0768 |
| GPT gateway alias | 0.0329 | 0.0380 |
| Official DeepSeek endpoint | 0.0133 | 0.0182 |
| Official Qwen-Plus text mode | **0.1255** | **0.1229** |
| Official Qwen-Plus JSON Mode | 0.1582 | 0.1219 |

The positive practical replications are therefore deployment-contingent:
both contrasts crossed 0.05 for the Sonnet gateway and official Qwen-Plus
text deployment, while GPT and DeepSeek produced statistically detectable but
smaller effects. In a matched 100-record Qwen comparison, JSON-minus-text
changes were +0.0191 and -0.0249; neither met the separately frozen 0.03
material-interaction rule. The results do **not** establish universal accuracy
degradation, a universal field-order rule, or equivalence between text mode and
JSON Mode. The 600-response Qwen3.7 resource-entitlement pilot was stopped and
is excluded from the formal results.

The headline conclusion is deliberately narrow: **validation equivalence is
not by itself a sufficient behavioral regression oracle for LM-facing Schema
artifacts**. Effects depend on the deployed model/interface, and the gateway
aliases are reported as observed deployments because their upstream checkpoint
identities were not independently verified.

上述结论只针对记录时实际调用的部署，不是模型家族排名，也不是所有模型都
对顺序敏感的普遍定律。网关上游 checkpoint 没有被独立验证，因此仓库按
“Sonnet gateway alias / GPT gateway alias”报告，而不是把它们写成官方模型。

### 新端点扩展状态（尚未查看效应）

SJTU“致远一号”的 `deepseek-chat`、`deepseek-reasoner` 与
TokenRhythm 的 `deepseek-v4-flash` 已分别走完 3,000 个计划位置，但离线审计
发现其中 11 个请求只有传输错误、尚无成功响应：当前为 **8,989/9,000** 个
唯一成功 request key。原错误行全部保留，补跑程序只重试这 11 个缺口。

这批数据尚未计算序列化效应，也不会被包装成三个独立模型的“投票”。原来的
17,900 个响应仍是论文核心；新端点只是投稿后的部署稳健性证据。完整性审计与
预先冻结的后续分析边界见
`results/api/sob_endpoint_panel_completion_audit.md` 和
`protocol/35_endpoint_panel_completion_and_analysis_amendment.md`。

## Repository contents

- `paper/manuscript.md` — authoritative manuscript and current conclusions.
- `paper/emse/main.tex` — editable flat LaTeX source for the EMSE submission.
- `output/pdf/schema_order_emse_promptse_revision.pdf` — latest rendered review
  PDF (the earlier filename remains for provenance because it may be open in a
  local viewer).
- `output/artifact/schema_order_emse_online_resource1.zip` — allowlisted
  offline artifact package.
- `results/` and `protocol/` — frozen aggregate reports, manifests, and
  analysis decisions.
- `PROJECT_HANDOFF.md` — audit trail, checksums, and file-level status.

## Offline reproduction

The reproduction path never calls a model API:

```powershell
python -m pip install -r requirements-paper.txt
.\scripts\reproduce_paper_offline.ps1
```

It compiles the Python sources, runs offline tests, rebuilds tables and
figures from frozen aggregate reports, audits manuscript claims and citations,
regenerates the LaTeX/PDF package, and validates the artifact archive. API
runners are retained for method inspection but are not invoked by this command.

## Scope and data policy

Raw provider responses, credentials, restricted benchmark contexts, and
private gateway communications are intentionally not redistributed. The public
artifact exposes the method, manifests, aggregate outputs, validation checks,
and an authorized example task panel. See `ARTIFACT_README.md` and
`LICENSES.md` for the three reproducibility levels and licensing details.
