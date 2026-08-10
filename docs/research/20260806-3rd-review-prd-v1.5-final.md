# PRD v1.5–v1.7 默认首层盲审与修订记录

日期：2026-08-06  
审查对象：`docs/plans/knowledge-digest-knowledge-publication-prd.md` v1.5–v1.7 及 OKF/Task2/原始设计研究材料  
路由：3rd-review 默认首层，不传 `provider_allowlist`  
Runtime：首轮 `b6ce80c9-86b1-4efc-9cc8-bdfda7fab135`；第二轮 `c2e5a44c-4dd4-408d-8b65-313bfc90126a`；最终 v1.6 复核 `8a733e45-ad5d-4536-897e-ff8f5837d771`  
结果：三轮三路均 `completed`，实际默认首层为 `pi/k3`、`opencode/v4flash`、`antigravity/flash`，没有调用 Opus 或 Cursor

## Provider 结果

| Provider | 结果 | 主要意见 |
|---|---|---|
| `pi/k3` | completed | 语义 exit、版本 oracle、样本代表性 |
| `opencode/v4flash` | completed | topic id、契约修订边界、旧路径映射 |
| `antigravity/flash` | completed | Task 0 样本绑定、OKF 降级字段、脚注路径 |

## 共同确认的优点

- `Task 2-A → 2-B → 2-C → Task 3` 顺序合理，Task 2 样本包不覆盖旧正式结果。
- OKF 被限制为文件格式和信号 profile，没有引入数据库、图谱、runtime attestation 或 trust score。
- Reader/Audit 分包、`index.md` 渐进导航、三类页面、`claim_id`/`sources[].id` 回查、`published/degraded` 与 `released/not_released` 分离方向正确。
- `verified` 不再由结构 lint 自证，Task 2-B 机器诊断和 Task 2-C 人工读者门职责清楚。
- AGENTS/CONTEXT/README、inventory、归档和清理收口覆盖充分。

## 采纳并已写入 PRD v1.5

1. 删除实施语境中的三元 `topic_key_v1`，唯一权威规则改为 `topic_key_v2(knowledge_type, product, module, object_intent)`；旧 v1 仅作迁移记录。
2. Reader Bundle 树明确包含 `Home.md` 和 `references/sources.md`，并固定为 profile 豁免投影。
3. `digest_release_status` 改为 manifest-only；concept 页不再携带会在读者门之后变更的包级状态。
4. `digest_content_hash` 排除自身、时间、verified 追加和 release manifest；Claim ID 列表固定排序并去重。
5. 固定 `knowledge_type → digest_page_type → OKF type` 映射表；未映射直接 `degraded`。
6. Task 2-C answerable 子集采用冻结确定性规则，至少 8 个正向问题，覆盖产品/模块和页面类型；不足即 `not_released`。
7. 增加 Task 2-C reviewer independence 规则和受控 defect loop，禁止通过失败重开时降门槛或扩范围。
8. 增加可计算质量 oracle：section 归因、命令/端口/配置/表格/图片保真、连续原文块、近重复、golden-negative。
9. `verified` 只允许白名单事件，并要求事件回指 fingerprint、检测器和审计记录。
10. 明确 degraded 只进入 Audit/Archive 的 `_digest/degraded/`，不进入 Reader 或导航。
11. OKF parser smoke 必须记录固定来源/版本、fixture hash、未知字段行为和预期结果；无法固定则改名为 `OKF-inspired profile`。
12. Task 3 对比矩阵必须标明 `comparable` 或 `N/A`，禁止主观补齐 CompanyBrain 没有的字段。

## 仍保留为实施注意事项

- 具体 OKF consumer/parser 的固定版本必须在 Task 2-A 启动前落入 exit manifest；这不是 PRD 文字可以替代的运行证据。
- 12–20 篇样本中的可答性标签必须来自 Task 0 冻结 manifest，不能由编译器临时选择。
- Task 2-B 的 Normalizer 必须实际对账父子页、FAQ、表格、图片、双语、版本和噪声结构，不能只做文本清洗。

## 第二轮意见已落实到 v1.6

修订后复核仍要求实现前明确以下合同，已写入 PRD v1.6：

- `digest_topic_id` 沿用 TopicIndex `topic_id`，重复运行稳定；
- 2-B semantic exit 至少 6 个 machine-passing concept，覆盖三类页面和样本结构；Jaccard 不得替代语义成功；
- 版本提取优先级、可接受格式、冲突/缺失行为和 `stale_after` 规则固定；
- 断言提取器必须确定性或固定 model/temperature/seed；必需 section 的事实断言归因 100%；
- Task 0 先证明 12–20 篇样本可答至少 8 题；Task 2-C 还必须覆盖 inventory 中出现的特殊结构；
- `digest_content_hash` 排除字段完整列举，旧 `verified` 在受管内容变化后失效；
- machine `verified` actor grammar、relation kinds、affected set、old-path alias/deprecated 映射和归档恢复演练已分配到具体任务；
- `OKF-inspired profile` 不再输出 `okf_version`；脚注只解析本页 frontmatter 的 `sources[].id`。

## 最终 v1.6 复核发现与 v1.7 处理

最终 runtime 的三路审查均完成。审查没有推翻路线，但指出以下实施前合同风险：

- source entry 用一个 locator 关联多个 Claim 会造成事实归因歧义；
- 非 `products` 类型、无 module 产品、degraded 页的 Reader/Audit 位置需要明确；
- “每个 section 至少一条”不能替代事实断言 100% 归因；
- Task 0/Task 1 已完成的 exit artifact、样本可行性和 provider/评审/失败重放规则需要可验证记录。

这些意见已写入 PRD v1.7：

1. `sources[].digest_claims[]` 改为逐 Claim 的 `claim_id + fragment_locator` 显式映射，机器门按单一归因对账。
2. Reader v1 明确只发布 `products` 三类 concept；非 products 及冲突项进入 Audit/Archive `_digest/degraded/`，没有 module 时不生成空 `modules/index.md`。
3. 必需 section 的事实断言归因固定为 100%；“至少一条”仅保留为结构诊断。
4. Task 2-A 增加 Task 0/Task 1 exit manifest 路径、hash、版本和 backfill gate；Task 0 样本必须预先保证至少 6 个可通过机器门的候选。
5. Task 2-B 增加有限 defect loop、offline baseline 与 semantic release 的边界；Task 3 增加失败重放和增量题集经济规则。
6. 固定标题/描述来源优先级、产品级/模块级索引生成条件、评审人独立性记录和 provider 运行 manifest，避免实现阶段临时解释。

## 最终结论

三轮默认首层盲审没有推翻架构，只发现可执行合同的遗漏；这些遗漏已形成 PRD v1.7 的最终实施前修订。开始 Task 2-A 前仍必须完成 Task 0/Task 1 exit manifest、固定 OKF parser 版本和 fixture hash；不能把本报告或 PRD 文本本身当作实现通过证据。

## v1.7 修改后的主代理复核

- `git diff --check`：通过。
- KnowledgeDigest：`388 passed, 3 skipped`。
- 3rd-review：`257 passed`；doctor 通过，材料协议为 v5，当前默认首层读回为 `pi/k3`、`opencode/v4flash`、`antigravity/flash`。
- 静态合同复核：逐 Claim locator、非 products/degraded 路径、无 module 索引、Task 0/1 artifact gate、三类 page fixture、100% 事实归因、失败重放、offline/semantic 边界、评审独立性和增量题集规则均已落入 PRD v1.7。
- 本次只修改 PRD 和研究记录，没有声称 Task 2 代码已实现，也没有用测试绿灯替代语义发布证据。
