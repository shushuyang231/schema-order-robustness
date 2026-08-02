# JSON Schema 指令工件的分布稳健性测试

当前论文题目：

> Testing JSON Schema Instruction Artifacts: Distributional Robustness under
> Validation-Equivalent Serialization and JSON Mode

本项目把序列化后的 JSON Schema 同时视为验证契约和 LM 指令工件。研究问题是：如果序列化器、代码生成器或中间件只改变 Schema 成员顺序，而不改变验证语义，黑盒 LM 组件的输出分布是否仍然稳定？

## 当前结论（2026-08-02）

- 核心证据包含 17,900 个成功响应；另有 600 个因模型资源包不适用而停止的探索性 Qwen3.7 响应，未合并进入正式结果。
- 在不相交的分解实验中，Sonnet 网关 alias 的 property-order / additional-member-order 效应为 0.0584 / 0.0768，均超过冻结的 0.05 实用阈值。
- GPT 网关 alias 的对应效应为 0.0329 / 0.0380；DeepSeek 官方端点为 0.0133 / 0.0182。它们统计上可检测，但未达到 0.05，因此是应当保留的负向实用复现，不是“零效应”。
- Qwen-Plus 官方文本模式的对应效应为 0.1255 / 0.1229，均得到确认。
- Qwen-Plus JSON Mode 内的效应为 0.1582 / 0.1219。与同一批 100 条文本模式记录相比，JSON-minus-text 变化为 +0.0191 / -0.0249；两项都没有确认达到冻结的 0.03 material-interaction 规则。
- 上述 JSON Mode 结果只能表述为“没有证明其能实质削弱序列化敏感性”，不能表述为“模式没有影响”或“两个模式等价”。这里使用的是 `response_format={"type":"json_object"}`，不是严格 JSON Schema constrained decoding。
- 没有证据支持一般性的平均准确率下降。GPT additional-member 对 leaf accuracy 的 -0.0248 次要信号被完整保留，但不能升级为普遍结论。
- 保守 canonicalizer 在全部 200 条分解记录上把三个存储变体折叠为同一字节表示；它只处理本研究审计过的顺序自由度，不是通用 Schema 等价证明器。

实验分支已经关闭。不要为了寻找更多阳性结果继续添加模型。

## 主要文件

- `paper/manuscript.md`：EMSE PROMPT-SE 英文正文；
- `paper/references.bib`：论文引用数据库；
- `paper/emse/main.tex`：扁平、可编辑的 LaTeX 源；
- `output/pdf/schema_order_emse_promptse.pdf`：逐页检查的投稿审阅 PDF；
- `paper/emse/cover_letter.md`：特刊 cover letter 草稿；
- `paper/emse/submission_checklist.md`：投稿检查清单；
- `output/artifact/schema_order_emse_online_resource1.zip`：离线复现材料；
- `paper/claim_evidence_audit.md`：主张—证据映射与措辞边界；
- `PROJECT_HANDOFF.md`：项目状态和下一条本地指令。

## 离线复现

安装论文侧依赖：

```powershell
python -m pip install -r requirements-paper.txt
```

运行完整离线门禁：

```powershell
.\scripts\reproduce_paper_offline.ps1
```

该脚本会编译 Python 源、运行单元测试、从冻结 JSON 报告重建图表、核对正文数字和引用、生成 EMSE LaTeX/PDF，并验证 Online Resource ZIP。它不会调用任何模型 API。

## 通用 Schema 变体工具

输入 JSONL 每行需要 `record_id`、`context`、`question` 和 `json_schema`。生成端文件会拒绝 `ground_truth`、`gold` 或 `answer` 等答案字段，避免泄漏。

```powershell
python src\prepare_schema_metamorphic_tasks.py `
  --input data\public\tasks.jsonl `
  --public-output data\processed\tasks_with_variants.jsonl `
  --manifest-output protocol\tasks_manifest.json `
  --audit-output results\gate\tasks_variant_audit.json `
  --study-name my_schema_test `
  --model-alias model-alias `
  --repeats 5
```

先使用 `--mock` 验证生成、保存、恢复、解析和 Schema 校验链路。API 密钥不得写入命令、代码、日志、截图或论文工件。

## 作者信息与投稿前检查

EMSE 采用 single-blind review。作者信息已经按本人确认填写为：Shengyao Sun，上海交通大学本科生，Shanghai, China，通信邮箱 `sthfornothing@sjtu.edu.cn`。作者目前没有提供 ORCID；ORCID 是可选的永久研究者标识，因此本稿直接省略，不影响投稿。上传前只需再次检查 PDF、LaTeX 和 Editorial Manager 中的信息完全一致。
