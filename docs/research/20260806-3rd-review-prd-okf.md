# PRD v1.3：OKF 接入与任务安排盲审记录（历史路由）

> 路由更正：本报告对应上一轮显式临时 provider 组合，**不是** `/Users/Hugh/.config/3rd-review/config.json` 的默认首层，因此其中的 `claude-code/opus` 不能被解释为默认 3rd-review provider。正确默认首层复审见 [20260806-3rd-review-routing-audit.md](./20260806-3rd-review-routing-audit.md)。

日期：2026-08-06  
审查材料：`bundle/prd.md`、`bundle/okf-research.md`、`bundle/task2-replan.md`、`bundle/original-design.md` 及当前 PRD diff  
审查合同：只读、异源、禁止访问宿主路径和网络；重点检查 OKF profile、Task 2-A/2-B/2-C/Task 3 的依赖和读者质量门。

## Provider 终态

| Provider | 结果 | 是否采纳 |
|---|---|---|
| `claude-code/opus` | `completed`，输出完整审查 | 是 |
| `pi/k3` | 首轮因附件逻辑路径错误无法读取；修正版 `PROVIDER_OUTPUT_INVALID` | 否 |
| `cursor/grok` | 两轮均 `PROCESS_EXIT_NONZERO` | 否 |

因此本记录只有一份有效异源意见，不宣称三方共识。Opus 使用的材料 hash 与其他 provider 相同；首轮附件投递问题已修正后再次尝试，仍没有产生第二份有效意见。

## 有效意见结论

### 方向正确

- OKF 被定位为输出 profile，而不是 KnowledgeDigest runtime、数据库、固定 taxonomy 或 `Attested Computation`，方向正确。
- `sources[].id` 与 `digest_claim_ids` 分离、`generated`/`verified` 分离、`status` 与 `published/degraded`、`released/not_released` 分离，方向正确。
- `Task 2-A → 2-B → 2-C → Task 3` 的总体顺序正确：先文件合同，再正文编译，再读者质量，最后全量。
- 不应引入 OKF reference agent、Knowledge Catalog、trust score、数据库或静态 viewer。

### 必须补强

1. **固定正式页面路径映射**：明确三类 page type 的 canonical path；`index.md` 永远是索引，不承载 concept 身份；`overview.md` 不得无条件生成空壳。
2. **定义 `references/` 身份**：当前一处写“可选”，另一处固定为 `references/sources.md`。必须明确它是 `type: Reference` 的确定性投影，还是非 concept 索引，不能留给 Task 2-A 临时决定。
3. **纠正 `verified` 语义**：结构 lint 不能自证来源内容。`verified` 只能记录真正针对来源/资源的机器回查、蕴含检查或人工核验；结构检查进入 `digest_*`/audit。
4. **增加可读性 oracle**：每个必需 section 至少有一条可解析 source attribution；加入历史低质量页面的 golden-negative fixture；增加同页/跨页近重复检测，不能只靠占位字符串黑名单。
5. **定义内容 hash 和时间字段**：`digest_content_hash` 的覆盖范围、`generated.at` 何时更新、`verified[].at` 是否排除、YAML 输出排序/折行策略必须固定，否则重复运行无法证明幂等。
6. **修正原始方案的防丢失边界**：失败来源不能进入 Reader 的 `sources` 投影；重要表格、图片和视觉引用不能只留 Audit，否则读者仍需打开原文才能理解关键内容。

### 任务安排建议

- 2-A 不应要求真实正文的 claim footnote；只能验证 fixture 级 `sources[].id` 解析。真实正文归因应由 2-B 验收。
- 确定性 frontmatter、路径、index/log、信号投影和 validator 应集中在 2-A；2-C 主要保留人工读者门、独立性记录和 exit manifest，避免重复修改同一 writer/navigation 代码。
- Concept Contract 建议采用 `v1-draft`（2-A）→ 一次受控修订（2-B）→ `v1` 冻结（2-C）的生命周期；否则 2-B 会被迫静默改变 2-A 合同。
- 读者阈值不能由 2-C 在退出时自行决定。应在 Task 0 题集 manifest 或 2-B 启动前冻结；2-B 不做人工读者判定，2-C 作为唯一读者门归属。

## 主代理筛选结论

上述建议与原始需求一致，尤其是路径映射、`verified` 独立性、golden-negative 和阈值冻结；它们直接针对“结构合法但知识不可读”的复发风险。暂未修改 PRD，等待用户确认是否把这些审查建议写入 v1.4。
