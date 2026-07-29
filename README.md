# JSON Schema 序列化稳健性蜕变测试

当前研究题目：

**Equivalent Schemas, Different Distributions: Metamorphic Testing of Schema-Guided JSON Generation under Serialization Reordering**

项目把 JSON Schema 当作机器可读的软件接口契约。若两个 Schema 接受完全相同的 JSON 实例，但序列化顺序不同，黑盒 LLM 的输出分布是否仍然稳定？本项目通过等价重排、重复调用和 gold 指标分别测量表示敏感性、模型自身随机性、Schema 合规与答案正确性。

## 当前结论（2026-07-24）

- 100 条初始样本上的 5×5 重复测量结果显示，`claude-sonnet-5` 网关 alias 的两个主要复合重排超过冻结的 0.05 实用阈值，`gpt-5.5` alias 没有超过；
- 在不相交的 200 条样本、3 个分解条件、每条件 5 次重复中，Sonnet alias 的 property-order 和 additional-member-order 效应分别为 0.0584 和 0.0768，均超过阈值；
- 同一分解确认中，GPT alias 的两个效应为 0.03285 和 0.03795，均低于阈值；additional-member 对叶值准确率约有 -2.48 个百分点的次要信号，不能提升为主要结论；
- 官方 DeepSeek `deepseek-v4-flash` 端点的两个分解效应为 0.01325 和 0.01815，统计上可辨但低于 0.05 实用阈值，也没有得到受支持的准确率变化；
- 直接的 Sonnet–GPT 配对差异未通过 Holm 校正，因此不能声称模型间易感性差异已经得到确认；
- 全部正式实验共计 14,000 个成功黑盒响应。没有证据支持“所有模型都受显著影响”或“一般性准确率下降”。

裁决：作为软件测试/黑盒接口稳健性论文继续投稿准备。论文只主张部分部署系统存在达到预先冻结阈值的表示敏感性，并把 GPT 与 DeepSeek 的低于阈值结果作为模型依赖边界，而不是隐藏的失败实验。

## 重要边界

- JSON Schema 作为普通文本放在 user prompt 中；这不是厂商原生 `response_format` 或 constrained decoding 实验。
- 模型名称按网关 requested/returned alias 报告；上游权重和官方供应商身份未被独立验证。
- 100 条记录是独立统计单位；重复调用不作为额外独立样本虚增 n。
- `data/restricted/` 中的 gold 不进入生成 prompt，也不发布。
- 不根据 DeepSeek 结果再追加 Kimi 或其他模型来寻找阳性结果。未来若扩展模型面板，应作为独立、预先冻结的新研究。

## 关键文档

- `protocol/13_confirmatory_repeated_mve.md`：Sonnet 确认性重复测量协议；
- `protocol/14_gpt55_cross_model_replication.md`：GPT 跨模型复现协议；
- `protocol/16_cross_model_result_decision.md`：正式结果后的裁决；
- `protocol/17_related_work_novelty_audit.md`：相关工作与新颖性审计；
- `protocol/18_paper_research_questions_and_outline.md`：冻结 RQ、贡献边界和投稿级大纲；
- `protocol/26_official_deepseek_result.md`：官方 DeepSeek 端点的审计、结果与哈希；
- `protocol/related_work_matrix.csv`：机器可读相关工作矩阵；
- `paper/manuscript.md`：当前完整英文正文；
- `paper/claim_evidence_audit.md`：论文主张—证据审计；
- `paper/tmlr/main.tex`：官方 TMLR review-mode 匿名 LaTeX 源；
- [GitHub Releases](https://github.com/shushuyang231/schema-order-robustness/releases/latest)：已渲染并完成视觉检查的匿名论文 PDF，以及经过 allowlist 和密钥扫描的离线复现 ZIP；
- 本仓库运行 `scripts/reproduce_paper_offline.ps1` 后会在 `output/artifact/` 重新生成匿名离线复现工件。

## 安装

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-structured-output.txt
```

## 通用任务准备 CLI

输入 JSONL 每行需要四个公开字段：

```json
{"record_id":"example-1","context":"...","question":"...","json_schema":{"type":"object","properties":{}}}
```

答案侧字段（如 `ground_truth`、`gold`、`answer`）会被拒绝，防止意外泄漏。生成五种 Schema 表示、运行 manifest 和逐条哈希审计：

```powershell
.\.venv\Scripts\python.exe src\prepare_schema_metamorphic_tasks.py `
  --input data\public\tasks.jsonl `
  --public-output data\processed\tasks_with_variants.jsonl `
  --manifest-output protocol\tasks_manifest.json `
  --audit-output results\gate\tasks_variant_audit.json `
  --study-name my_schema_test `
  --model-alias model-alias `
  --repeats 5
```

该输出可直接交给现有的可断点续跑生成器：

```powershell
.\.venv\Scripts\python.exe src\run_sob_metamorphic.py `
  --public-input data\processed\tasks_with_variants.jsonl `
  --manifest protocol\tasks_manifest.json `
  --output results\api\tasks_predictions.jsonl `
  --model-alias model-alias `
  --mock
```

先使用 `--mock` 验证保存、解析和 Schema 校验链路；正式调用时去掉 `--mock` 并通过环境变量提供 API key。密钥不得写入命令、文件、日志或截图。

## 测试

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

完整离线重建论文图表、审计正文并打包匿名工件：

```powershell
.\scripts\reproduce_paper_offline.ps1
```

该脚本不调用任何模型 API。原始模型响应、受限 gold 数据和本地密钥均不进入匿名工件。

本机已核验的解释器为 Python 3.12.13。Windows `py` launcher 当前不可用，因此文档统一使用项目虚拟环境的绝对相对入口。

## 已放弃的早期方向

仓库仍保留 BIRD-Critic SQL repair 的审计和实验文件，作为完整研究过程记录。该方向的 M1 最小补丁方法只通过 3/30，已按预注册规则判定 `NO_GO_REVISE_OR_ABANDON`，不属于当前论文主线。
