# JSON Schema 序列化稳健性：相关工作与新颖性审计

审计日期：2026-07-18

## 最终裁决

**CONDITIONAL GO — 保留选题，但缩窄为软件测试与接口稳健性研究。**

当前证据足以支撑一篇诚实的应用型论文继续推进，但不足以支撑“首次发现 LLM 对语义等价格式敏感”或“揭示了内部机制”这类宽泛声明。最可辩护的研究对象是：

> 将 JSON Schema 视为机器可读的软件接口契约，使用验证语义等价的序列化重排作为蜕变关系，测试黑盒 LLM 在 schema-guided JSON extraction 中的表示稳健性，并用重复调用估计和扣除同一提示自身的随机波动。

本项目的 Schema 被作为普通文本嵌入 user prompt。实验没有调用厂商原生 `response_format`、constrained decoding 或 function/tool schema 接口。因此，论文必须使用 **schema-guided JSON generation/extraction**，不能把实验写成原生 **Structured Outputs API** 评测。

## 规范基础

本研究所用变换以“验证结果不变”为语义等价标准：

- RFC 8259 将 JSON object 定义为无序的 name/value 集合。因此，Schema 对象成员以及 `properties` 对象成员的序列化顺序不改变其 JSON 数据模型含义。
- JSON Schema Draft 2020-12 规定，`required` 在且仅在数组中的每个名字都是实例属性名时通过验证；该条件不依赖数组中名字的先后顺序。
- 项目代码对每条记录的每个变体计算规范化语义签名；签名不一致时拒绝生成任务。

这里的“等价”只指 JSON Schema 验证集合等价，不表示两个 token 序列相同，也不表示模型内部处理过程相同。

## 直接相关工作矩阵

| 工作 | 研究对象与主要贡献 | 与本项目的重叠 | 本项目仍可保留的差异 |
|---|---|---|---|
| Sclar et al., ICLR 2024, *Quantifying Language Models' Sensitivity to Spurious Features in Prompt Design* | 量化 few-shot prompt 中意义保持的格式变化，提出 FormatSpread，并发现格式优劣跨模型弱迁移 | 已经建立“一般提示格式会显著影响模型”的核心先例 | 不研究 JSON Schema 接口契约、验证语义等价的 schema 重排或重复随机性校正 |
| Kang et al., Findings EMNLP 2025, *When Format Changes Meaning* | 在固定措辞下改变空格、大小写和分隔符，研究语义不一致，并对开放权重模型做机制分析 | 是最接近的广义新颖性威胁；已覆盖“语义等价格式导致不同预测” | 不研究 JSON Schema key/keyword/`required` 顺序，不把 schema 当作软件接口，不使用本项目的重复测量噪声扣除 |
| Hua et al., EMNLP 2025, *Flaw or Artifact?* | 说明严格字符串匹配可能夸大提示敏感性，采用语义评测后方差明显下降 | 对任何“输出不同即模型有缺陷”的论断构成直接反驳 | 本项目同时报告规范化分布差异、Schema 合规、叶值 gold 准确率；结论明确不把分布变化等同于准确率下降 |
| Ravikumar et al., EACL 2026, *Lost in Formatting* | 比较信息抽取中的多种等价输出格式，显示格式是重要超参数 | 同属结构化信息抽取与格式敏感性 | 改变的是目标输出表示（JSON/XML/tuple 等），不是同一 JSON Schema 的验证等价序列化；研究模型和训练设置也不同 |
| Geng et al., 2025, *JSONSchemaBench* | 比较 constrained decoding 框架的 Schema 覆盖、效率和生成质量 | 同样使用真实 JSON Schema，讨论结构化生成 | 不测试 schema 序列化重排，也不估计同提示随机分歧 |
| Singh et al., 2026, *The Structured Output Benchmark (SOB)* | 提供多模态结构化输出基准，区分 Schema 合规与叶值准确率 | 本项目直接复用其 text test 数据、gold 和指标思想 | SOB 的主榜提示中只用单一 schema 表示；原生结构化解码是单独消融，不测试顺序稳健性或重复测量 |
| Hyun et al., ICST 2024, *METAL* | 用文本扰动和蜕变关系分析 LLM 质量 | 已经建立 LLM 蜕变测试方法类别 | 本项目的蜕变关系来自正式接口规范，oracle 是验证集合等价和 gold 值，而不是一般文本扰动 |
| RFC 8259 与 JSON Schema Draft 2020-12 | 分别规定 JSON object 的无序数据模型及 Schema 关键字验证语义 | 为“等价重排”提供规范依据 | 规范不保证自回归 LLM 对不同序列化具有相同输出分布；这个规范—实现落差正是测试对象 |

## 新颖性分层判断

### 已经不能主张的内容

1. 不能主张首次发现 LLM 对 prompt formatting 敏感。
2. 不能主张首次研究语义等价输入下的模型不一致。
3. 不能主张首次将 metamorphic testing 用于 LLM。
4. 不能主张 schema 顺序普遍降低或提高准确率；当前准确率差异未得到校正后的支持。
5. 不能主张 Sonnet 类模型必然比 GPT 类模型更敏感；配对模型差异未显著。
6. 不能主张内部注意力、位置编码或训练数据是原因；当前只有黑盒行为证据。
7. 不能把网关 alias 当作已验证的官方模型版本。

### 可以谨慎主张的内容

基于本次检索，尚未发现一项工作同时覆盖以下组合；论文应写成“to our knowledge”，而非绝对首创：

1. 以 JSON Schema 验证语义为依据构造 `properties`、schema keyword、`required` 和 description-position 等价重排；
2. 在同一 schema-guided JSON extraction 任务上，固定任务和提示其余部分，只干预 schema 序列化；
3. 对每种表示做相同次数的独立黑盒调用，并用
   `cross(A,B) - 0.5 * (within(A) + within(B))`
   区分表示变化效应与模型本身的随机波动；
4. 同时报告 Schema 合规、叶值准确率、完整响应准确率和规范化输出分布变化；
5. 预注册实用效应阈值，并保留第二个模型未达到该阈值的负复现结果。

## 当前证据对新颖性的实际贡献

正式实验包含 100 条冻结记录、5 种表示、每种 5 次独立调用、2 个网关模型 alias，共 5,000 个成功响应。

- `claude-sonnet-5` alias：`properties_reversed` 和 `keywords_reversed` 的规范化 excess disagreement 达到预注册的 0.05 实用阈值，且置信区间与 Holm 校正检验通过。
- `gpt-5.5` alias：相同方向存在统计可检测的小效应，但两个主要变体均未达到 0.05 的预注册实用阈值。
- 两个 alias 上均没有得到校正后可靠的叶值准确率变化。
- 事后配对分析没有建立显著的模型间效应差异、稳定的跨模型易感样本，也没有找到经校正后可靠的简单 Schema 特征解释。

因此，论文的中心发现不是“重排让答案更差”，而是：

> 验证等价不保证黑盒 LLM 的输出分布等价；这种差异可超出同提示随机性，但其实用幅度具有模型依赖性，并且未必转化为可检测的平均准确率损失。

## 审稿风险

| 风险 | 严重度 | 当前处理 | 投稿前门槛 |
|---|---:|---|---|
| 被视为一般 prompt sensitivity 的窄案例 | 高 | 改投软件测试/接口稳健性叙事；突出规范驱动的 metamorphic oracle 与重复噪声校正 | 将测试框架整理成可复用工具，并给出至少一项独立于现象描述的工程价值 |
| 两个模型均来自未验证第三方网关 | 高 | 所有文件均保留 returned alias、时间戳和 response ID；不声称官方权重 | 最好取得上游身份说明，或增加至少一个可核验官方 API/固定开放权重系统复现 |
| 默认采样配置不透明、模型可能漂移 | 高 | 调用时间、prompt hash 和完整响应已保存；不把结果推广到其他版本 | 论文中明确作为外部有效性威胁；若再实验，冻结可控采样参数或固定 checkpoint |
| 只有 100 个任务 | 中高 | 每条 25 次调用，统计以 record cluster 为单位而不是把 2,500 次当独立样本 | 扩样只能在新预注册后进行；优先扩大记录数，不继续增加同记录重复次数 |
| 研究不是原生 structured decoding | 中 | 已核对代码和 SOB 官方说明 | 标题、摘要、方法全文统一写 prompt-based schema-guided generation |
| 效应没有转化为平均准确率下降 | 中 | 将准确率结果作为重要负结果报告 | 不再以“性能损失”为主标题；突出测试/稳定性而非质量提升 |
| 缺少机制解释 | 中 | 不声称机制 | 机制实验必须独立标为 exploratory；不是当前投稿前的必需条件 |

## 投稿准备裁决

当前状态不是“可立即投稿”，而是 **novelty audit passed with major repositioning**。进入论文工程阶段的条件是：

1. 使用新标题和新 RQ，废弃旧的错误预警/AUROC 主线；
2. 把现有代码整理为可复用的 schema serialization metamorphic tester；
3. 在写作前解决或如实暴露模型来源不可验证问题；
4. 任何新增 API 实验都必须先说明它回答哪个冻结 RQ，不能为了找阳性模型而追加。

## 核心来源

- RFC 8259: https://www.rfc-editor.org/rfc/rfc8259
- JSON Schema Validation Draft 2020-12: https://json-schema.org/draft/2020-12/json-schema-validation
- Sclar et al., ICLR 2024: https://proceedings.iclr.cc/paper_files/paper/2024/hash/6c0e99d736da621403018ca7b32b1a4d-Abstract-Conference.html
- Kang et al., Findings EMNLP 2025: https://aclanthology.org/2025.findings-emnlp.143/
- Hua et al., EMNLP 2025: https://aclanthology.org/2025.emnlp-main.1006/
- Ravikumar et al., EACL 2026: https://aclanthology.org/2026.eacl-long.256/
- JSONSchemaBench: https://arxiv.org/abs/2501.10868
- SOB: https://arxiv.org/abs/2604.25359
- METAL: https://arxiv.org/abs/2312.06056

