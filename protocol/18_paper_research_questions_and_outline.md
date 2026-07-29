# 论文研究问题、贡献边界与投稿级大纲

冻结日期：2026-07-18

本文件替代 `protocol/10_topic_selection_decision.md` 中的旧 RQ3/RQ4。旧文件保留为研究过程记录，不追溯修改。

## 推荐标题

首选：

**Equivalent Schemas, Different Distributions: Metamorphic Testing of Schema-Guided JSON Generation under Serialization Reordering**

中文：

**等价模式，不同分布：序列化重排下 Schema 引导 JSON 生成的蜕变测试**

备选：

**When Unordered Schemas Meet Ordered Tokens: Testing Serialization Robustness in Black-Box LLM JSON Extraction**

标题中暂不使用 `Structured Outputs API`，因为实验通过普通 prompt 传入 Schema，而非厂商原生约束解码接口。

## 一句话问题定义

JSON Schema 的若干序列化重排不改变可接受实例集合，但 LLM 逐 token 读取这些表示；我们测试这种规范层等价是否能转化为黑盒生成行为的分布稳健性。

## 冻结研究问题

### RQ1：表示效应

**验证语义等价的 JSON Schema 序列化重排，是否会引起超出同提示随机波动的输出分布变化？**

- 主指标：token-normalized excess disagreement。
- 比较：每个非原始变体对 `original`。
- 证据：Sonnet alias 的两个主要变体达到预注册实用阈值；GPT alias 上有较小的统计信号但未达到实用阈值。

### RQ2：跨系统复现边界

**观察到的表示效应能否在第二个黑盒模型 alias 上达到相同的预注册实用幅度？**

- 证据：未复现预注册实用幅度。
- 允许结论：实用幅度并非在两个测试系统中一致出现。
- 禁止结论：Sonnet 系统显著比 GPT 系统敏感；事后直接模型差异未通过校正检验。

### RQ3：输出质量影响

**等价重排是否改变 Schema 合规、叶值准确率或完整响应准确率？**

- 指标：Schema Pass Rate、leaf Value Accuracy、token F1、Perfect Response Rate。
- 证据：Schema 合规近乎饱和；没有校正后可靠的平均叶值准确率效应。
- 解释：行为分布变化不应自动被表述为质量下降。

### RQ4：可解释的易感性（探索性）

**样本级敏感性是否跨模型稳定，并能否由简单公开 Schema 特征解释？**

- 状态：post-hoc exploratory。
- 已检查：schema 字符数、属性总数、最大深度、description 字符数。
- 证据：没有跨模型稳定的记录级一致性，也没有经校正后可靠的简单特征关联。
- 用途：界定当前解释能力，不作为主要贡献。

## 论文贡献

按重要性排序：

1. **规范驱动的蜕变关系。** 从 JSON 与 JSON Schema 的验证语义出发，定义四类序列化变换，并用规范化语义签名自动拒绝非等价任务。
2. **随机性校正的黑盒测试协议。** 对原始表示和变体都做重复调用，用跨表示分歧减去两侧同表示分歧的平均值，避免把模型自身随机性误判为 schema-order 效应。
3. **多维 oracle。** 分别测量可解析性、Schema 合规、规范化输出分布、叶值准确率和完整响应准确率，避免“字符串不同即错误”的评测伪影。
4. **带失败复现边界的实证结果。** 在两个网关 alias、100 个冻结任务和 5,000 个成功响应上，发现统计可检测但实用幅度不一致的分布变化，同时没有可靠的平均准确率损失。
5. **可复现测试工具。** 发布公开数据侧的变换、调度、断点续跑、解析、验证、统计和哈希清单；不发布受限 gold 或第三方凭证。

第 5 项目前是待完成的论文工程贡献，完成前不应在摘要中写成已经发布。

## 声明词典

### 可以写

- validation-equivalent / semantics-preserving with respect to the accepted instance set
- controlled schema-serialization intervention
- statistically detectable output-distribution shift
- exceeded identical-prompt stochastic disagreement
- met / did not meet a preregistered practical-effect threshold
- no supported average accuracy degradation
- gateway model alias; upstream identity not independently verified
- to our knowledge（仅用于 JSON Schema 重排与重复随机性校正这一完整组合）

### 不可以写

- same prompt（Schema 字节已经改变）
- deterministic effect
- universal order bias
- accuracy degradation（没有得到支持）
- Sonnet is more sensitive than GPT（模型差异没有建立）
- attention/position encoding causes the effect
- official Claude/GPT model（除非获得可核验上游证明）
- native structured outputs / constrained decoding experiment
- first prompt-sensitivity study / first LLM metamorphic test

## 论文结构

### Abstract

用六句完成：

1. 工程背景：JSON Schema 常作为 LLM JSON 生成的接口契约。
2. 缺口：验证语义忽略若干顺序，但自回归模型消费有序 token；现有 structured-output benchmark 与 prompt-format 工作没有评估这一规范—实现落差并校正随机性。
3. 方法：四种等价重排、100 条 SOB 任务、两个黑盒 gateway alias、每条件五次，共 5,000 个成功响应。
4. 主结果：Sonnet alias 两个变体超过预注册 0.05 实用阈值；GPT alias 有更小统计信号但未复现实用阈值。
5. 负结果：没有可靠的平均叶值准确率变化；不能把分布不稳健等同于质量下降。
6. 意义：schema-guided 系统测试应同时检查序列化变体和同提示随机基线。

### 1. Introduction

- 以软件契约的例子解释：validator 认为等价，生成器未必行为等价。
- 区分语法合规、语义正确、分布稳定三件事。
- 指出一般 prompt sensitivity 已被广泛研究，本文只解决 JSON Schema 接口的窄问题。
- 给出 RQ1–RQ4 和贡献列表。
- 在引言末尾主动说明跨模型实用幅度未复现，这是结果而不是隐藏的缺陷。

### 2. Background and Related Work

#### 2.1 JSON 与 JSON Schema 的顺序语义

- RFC 8259 的 object/array 区分。
- `required` 的验证定义。
- “验证等价”不等于 token 等价。

#### 2.2 Structured-output evaluation

- JSONSchemaBench：约束解码覆盖、效率、质量。
- SOB：Schema 合规与 Value Accuracy；本项目的数据来源。
- 强调 SOB headline runs 是 prompt-only，structured decoding 是消融；本项目同样是 prompt-based。

#### 2.3 Prompt/format sensitivity

- Sclar 2024、Kang 2025、Ravikumar 2026。
- Hua 2025 的 evaluation artifact 反驳。
- 明确本文不争夺一般格式敏感性的首创权。

#### 2.4 Metamorphic testing of LLMs

- METAL 等一般框架。
- 本文差异：MR 来自机器可读规范，oracle 可自动验证，并显式建模随机性。

### 3. Method

#### 3.1 Problem formulation

- 输入 context、question、Schema `S`，黑盒生成器 `G`。
- 变换 `T_k(S)` 满足接受实例集合 `L(S) = L(T_k(S))`。
- 研究的是输出分布 `P_G(.|S)` 与 `P_G(.|T_k(S))`，不是仅比较单次字符串。

#### 3.2 Metamorphic relations

- `properties_reversed`
- `required_reversed`
- `keywords_reversed`
- `descriptions_first`
- 对两条 `descriptions_first` no-op 记录执行 intent-to-treat，并报告 applicability。

#### 3.3 Prompt and generation interface

- 固定 system prompt、context、question 与其余模板。
- Schema 作为 user prompt 中的 JSON 文本。
- 不传 sampling parameters；这是网关兼容选择，也是有效性威胁。
- 记录 requested alias、returned alias、response ID、prompt hash、时间和 token。

#### 3.4 Repeated-measures design

- 100 records × 5 representations × 5 repeats × 2 aliases。
- SHA256 确定交错顺序；失败请求保留并重试；成功 key 唯一。
- 记录为 cluster，不能把重复调用当作独立样本扩大 n。

#### 3.5 Metrics and inference

- parse、Schema pass、leaf accuracy、token F1、perfect response。
- exact 与 token-normalized disagreement。
- `excess = cross(original, variant) - 0.5(within(original)+within(variant))`。
- record-cluster bootstrap、within-record label permutation、Holm correction。
- 预注册实用阈值 0.05。

### 4. Results

#### 4.1 Operational validity

- 两系统各 2,500 个唯一成功请求。
- Schema Pass：Sonnet 99.9%，GPT 99.7%。
- 分别报告 11 和 3 条暂时网络错误及最终恢复情况，避免制造“零失败”假象。

#### 4.2 RQ1: representation sensitivity

- 主表放 normalized excess、95% CI、Holm p。
- Sonnet：properties 0.083、keywords 0.070；两个主要效应过门槛。
- 其他结果完整报告，主次假设标签不可删除。

#### 4.3 RQ2: cross-system replication

- GPT：properties 0.039、keywords 0.029；未过 0.05 实用阈值。
- 明确“一个显著、一个不显著”不等于模型差异显著。
- 事后模型差异只放次表或附录，并标 exploratory。

#### 4.4 RQ3: correctness and compliance

- 展示 leaf accuracy、token F1、perfect、Schema pass。
- 结论：没有校正后支持的平均 leaf accuracy 变化。

#### 4.5 RQ4: exploratory susceptibility

- 记录级 Spearman 与 Schema 特征关联放附录为主。
- 主文一句总结没有经校正证据。

### 5. Discussion

#### 5.1 对开发者意味着什么

- 单一 Schema 序列化的测试可能低估输出可变性。
- 测试至少需要：一个规范等价变体、同提示重复基线、语义 oracle。
- 不建议根据当前结果宣称某一种顺序总是更好。

#### 5.2 为什么分布变化不等于准确率下降

- 多个不同答案可以同样错误、同样正确，或只在表面 token 上不同。
- 本项目的 normalized metric 与 gold 指标分别回答不同问题。

#### 5.3 实用幅度的模型依赖性

- 将负复现解释为结论边界，而不是阈值失败后改规则。
- 不能从现有数据推断模型架构机制。

### 6. Threats to Validity

- Construct：规范化仍可能把某些语义等价表述判为不同；用 gold 指标与 token F1 缓解。
- Internal：网关默认采样、服务端更新、网络重试；用随机交错、哈希、时间戳和重复测量缓解。
- External：100 条 medium/hard SOB text 任务、两个 alias、prompt-only Schema；不能推广到原生约束解码、工具调用或所有模型。
- Reproducibility：上游身份不可独立核验是高风险限制，不得淡化。
- Statistical：记录才是独立分析单位；多重检验与探索/确认标签必须保留。

### 7. Conclusion

- 重申规范层等价不自动保证生成分布稳健。
- 重申实用幅度没有在第二 alias 上复现，准确率损失也没有建立。
- 提出 schema serialization metamorphic testing 作为上线前测试补充，而不是新排序优化法。

## 图表清单

主文建议只放四项：

1. 方法图：Schema `S` → 四个等价变体 → 重复黑盒调用 → 随机性校正比较。
2. 主结果森林图：两个 alias × 四个变体的 normalized excess 与 95% CI，标出 0.05 实用阈值。
3. 质量表：Schema pass、leaf accuracy、perfect response。
4. 复现边界表：预注册条件、Sonnet 结果、GPT 结果、裁决。

附录放完整 p 值、exact disagreement、record-level concordance、feature associations、prompt、变换伪代码、样本清单和哈希。

## 下一实验门槛

当前不立即追加第三个闭源 alias。优先顺序：

1. 将变换与评测封装为可复用 CLI，并补充性质测试；
2. 生成论文所需的冻结统计表和森林图，不重新计算主结论；
3. 争取一个来源可核验的官方 API 或固定开放权重复现；
4. 若能获得第 3 项，先新建预注册，目标是“外部有效性 characterization”，不得替代 GPT 的失败复现；
5. 若无法获得，则如实以两个 gateway alias 投稿，并接受其显著降低录取概率。

