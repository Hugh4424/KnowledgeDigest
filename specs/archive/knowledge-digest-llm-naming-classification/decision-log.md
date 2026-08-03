[[31mERROR[0m] - (starship::print): Under a 'dumb' terminal (TERM=dumb).
# KnowledgeDigest Task2：知识发布语义层

## 问题

Task1 已经能安全地保留来源、Claim、Evidence 和 Provenance，但发布结果仍然像内部中间产物：主题标题和分类不够语义化，读者无法从 Home 和目录快速理解知识结构。目标不是再做一个 Markdown 重写器，而是在现有可靠消化管线之上增加一个可读、可导航、可追溯的知识发布层，效果按读者可见结果与 `CompanyBrain` 参考比较。

## 已确认方向

1. LLM 只提出语义建议：标题、分类、Summary、Why、Version 等发布字段由模型建议，程序负责 schema 校验、Claim/Evidence 对齐、敏感事实保真、路径稳定、分页、溯源和安全写回。
2. 分类采用受控两级分类表。分类表必须版本化；一次运行只能映射到当前分类，新增分类必须显式修改分类表并升级版本，不允许每次运行让模型自由生成分类体系。
3. 语义建议只在知识消化/发布构建阶段生成。发布后的知识库必须完全离线可读，不依赖模型服务。
4. 语义建议不合格或模型不可用时只做局部回退：保留确定性主题页、Claim、Evidence、Provenance，并将该来源标记为待复核；不能因为一个来源失败而丢失其他来源。
5. 项目 LLM 配置只允许用户指定的 `qwen3.6` 和 `jina-embeddings`；凭据只从环境变量读取，不写入仓库、报告、知识库或日志；DeepSeek 禁止作为主模型或 fallback。

## 范围

- 在现有 S1–S6 和 Task1 发布合同之上增加 semantic publication 层。
- 为主题生成可读、稳定、可检索的标题和路径。
- 生成并校验两级分类、Home 导航、分类导航和来源索引。
- 生成 Summary、Why、Version 等字段；字段必须能回指已有 Claim/Evidence，不能创造无来源事实。
- 保持分页、写前归档、原子发布、来源索引、batch/resume 和 fail-closed 约束。
- 以同一份 89 篇语料做 Task1/Task2 对比：读者导航、标题/分类质量、Summary/Why/Version 完整性、来源可达性、内容无损、页长、耗时、调用量和失败回退。

## 非目标

- 不重写 S1–S6 的 Claim、Evidence、Provenance 主流程。
- 不引入数据库、向量数据库、CAS、journal、调度器、后台守护进程或 AgentMemory。
- 不做阅读时实时问答；阅读阶段只消费已发布的离线文件。
- 不让 LLM 直接决定最终文件路径、分类表或写入权限。
- 不以 Claim 数量、文件数量或模型输出字数作为质量替代指标。

## 质量合同

- 每个正式主题页都有语义标题、一个有效的两级分类、Summary、Evidence、Why、Version 和 Provenance。
- Home → 分类页 → 主题页 → 来源索引可达；不再把所有页面堆在单一 `pages/digest` 目录下。
- 所有原始有效 Claim、Evidence 和来源指纹保留；语义建议失败不得造成内容丢失。
- 页面仍遵守 300 行上限，分页不重复 Claim，不产生孤儿索引。
- 发布结果脱离模型服务即可阅读；模型失败时能在批次级/来源级恢复。
- 同一输入、同一分类表版本和同一配置重复运行应产生稳定标题、分类和路径。

## 评审与事实

- `make-decision/direction` 正式评审：`pass`；实际覆盖 `kimi/k3`、`cursor/grok`、`antigravity/flash`，3/3 完成，无 DeepSeek。
- 评审指出的有效风险已转为本记录约束：模型调用时机和离线发布、CompanyBrain 只按读者可见指标比较、分类表版本与所有权、Task1 主流程复用、非目标和模型不可用回退。
- 评审中关于已选方向混入盲审材料的证据属于材料边界问题，不改变用户已确认的方向；后续 detail review 使用本记录，不能再把 approved direction 当作 direction 盲审事实。

## 主要风险

- qwen3.6/jina-embeddings 端点不可用：必须保留确定性结果，并明确报告 provider 状态；不能换成 DeepSeek。
- 模型返回无法验证的标题、分类或摘要：拒绝该字段，使用确定性字段并标记待复核。
- 分类表扩张导致导航碎片化：分类表版本、变更记录和最小页面/来源阈值在 build-spec 中冻结。
- Summary/Why/Version 变成重复正文：限制字段职责并用 Claim/Evidence 引用校验。

## build-spec 冻结结果

- taxonomy 唯一事实来源是 `kb.structure.md` 的 `publication_categories`；初始版本 `1.0.0`、owner、两级分类、别名和 SemVer 变更规则已写入 spec。
- JSON schema、固定提示词四段、字段长度、Claim/Evidence 保真门、局部回退和 `needs-review` 状态已冻结。
- 稳定 topic ID、首次路径锁定、主题先聚合后分页、来源索引只存索引和三跳读者入口已冻结。
- batch/resume 绑定来源清单、taxonomy/model identity；89 篇预算为默认 8 篇批次、180 秒请求硬超时、30 分钟目标、60 分钟安全上限。
- CompanyBrain 对比采用五类各 4 个主题的 20 行抽样表，机器证据与人工判断分开。

本记录与 `spec.md` 是当前材料；后续 plan/code 不得把上述待冻结项重新变成运行时自由选择。
