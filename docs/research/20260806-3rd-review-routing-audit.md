# 3rd-review 路由核对与 PRD 默认首层盲审

日期：2026-08-06  
对象：`knowledge-digest-knowledge-publication-prd.md` v1.3   
审查材料：PRD、OKF 官方研究、Task2 重排审计、原始设计和当前 PRD diff

## 先说结论

`3rd-review` 默认配置没有错误：默认首层确实是：

```text
pi/k3 + opencode/v4flash + antigravity/flash
```

上一轮出现 `claude-code/opus` 是调用方错误：我使用了显式临时 provider 组合，绕过了默认 `tiers`。不应把上一轮结果说成默认配置的三方盲审。

本次已用默认配置重新审查，三路均完成：

| Provider | 结果 | 运行时间 |
|---|---|---:|
| `pi/k3` | completed | 189.5 秒 |
| `opencode/v4flash` | completed | 297.9 秒 |
| `antigravity/flash` | completed | 39.7 秒 |

runtime：`54182a52-da2d-46a7-abfd-e47561724ab8`；`selected_tier=0`；三路材料 hash 一致；没有调用 `claude-code/opus`。

## 为什么会出现 Opus

有两套路由，不能混为一谈：

1. **直接调用 3rd-review**  
   `/Users/Hugh/.config/3rd-review/config.json:15-19` 的 `tiers` 决定默认路由。`claude-code/opus` 虽在 `providers` 注册表中（`:40-48`），但不在任何 tier，所以默认 `run` 不会自动选它。

2. **WorkflowHub 的 wh-review**  
   `/Users/Hugh/.config/workflowhub/config.json:56-59` 的 `build-plan.initial` 明确包含 `claude-code/opus`。如果通过 WorkflowHub 的 build-plan，而不是直接 3rd-review，Opus 是阶段配置主动选入的。

3rd-review 的实现也证实这一点：默认无 allowlist 时只遍历 `config.tiers`（`3rd-review/lib/broker.mjs:623-631`）；若 request 带 `provider_allowlist`，则允许显式覆盖（`3rd-review/lib/broker.mjs:344-352`）。上一轮错误发生在调用层：为了复用旧上下文，我创建/使用了包含 Opus 的临时组合，没有先按默认首层执行。

## 当前配置的真实风险

- `claude-code/opus`、`cursor/grok` 仍在 3rd-review `providers` 注册表，但不在默认 tier。它们不会自动运行，却仍可被临时 config、`provider_allowlist` 或旧 runtime continuation 选中。
- `cursor/grok` 已弃用，但仍是 `enabled: true`；这是配置卫生问题，应在确认没有历史 continuation 依赖后禁用或移除。
- `config.example.json` 仍展示旧的 Claude/Kimi/Codex 首层，容易误导维护者；它不是当前运行配置，但应同步文档。
- 继续旧 runtime 会沿用旧 provider 选择；要更换 provider，必须新建首轮 runtime，不能 continuation 旧的 Opus/Cursor session。

一次性审查最稳的做法是：使用默认 config，不传 `provider_allowlist`；若只想审 `opencode/v4flash`，request 中明确写完整 ID `provider_allowlist: ["opencode/v4flash"]`，不要写 bare `opencode`。

## 默认首层三方审查对 PRD 的结论

### 已确认合理

- `Task 2-A → Task 2-B → Task 2-C → Task 3` 顺序正确，不应合并或调换。
- OKF 作为输出 profile，而不是 runtime、数据库、固定 taxonomy、GraphRAG 或 Attested Computation，边界正确。
- `sources[].id`、`digest_claim_ids`、`generated`、`verified`、`status`、`stale_after` 分离，方向正确。
- 不应加入 trust score、全局正文复制率硬阈值、永久人工队列、七类页面、数据库或图服务。

### 进入实施前必须修的合同缺口

1. **统一入口文件和 concept 身份**：明确 `README.md`、`Home.md`、`references/sources.md` 是带 `type` 的 concept，还是正式豁免文件；把豁免写进 validator。固定产品级但无 module 的 concept 放置规则。
2. **统一 topic key**：PRD 的 `v1` 三元组与 Task 1 实际 `v2` 四元组不一致；补版本迁移/兼容规则，以及 `knowledge_type → concept type` 的确定性映射。
3. **修正 verified 语义**：结构 lint 不能自证内容。机器结构门进入 `digest_*` 或精确的 machine event；`verified` 只能记录真实的来源/内容回查或人工核验，不能用泛化的 `process:knowledge-digest-machine-gates` 冒充内容确认。
4. **拆开 2-B 和 2-C 的读者门**：2-B 只做机器诊断（归因、section、占位、命令/参数保真）；2-C 是唯一人工读者门。题集、抽样 seed 和最低阈值在 2-C 启动前冻结，不能由退出时临时自定。
5. **定义可重放的 hash/YAML 规则**：固定 `safe_dump` 参数、排序、Unicode、折行和 `digest_content_hash` 覆盖范围；明确 `generated.at`、`verified` 追加、release 状态是否属于易变字段。否则“重复运行稳定”和人工修改保护互相冲突。
6. **补内容质量 oracle**：section 级归因覆盖、golden-negative 低质量 fixture、连续原文块/命令/端口保真、索引零悬挂、同页近重复检查。不能只靠“有 frontmatter”和占位字符串黑名单。
7. **在 Task 2 结束前跑一次真实语义路径**：固定 provider、model、预算和失败记录；否则 Task 3 会第一次才暴露 LLM 编译问题。
8. **核实 OKF 互操作声明**：增加离线第三方/最小外部解析器 smoke；做不到就把对外表述从 `OKF-compatible` 降成 `OKF-inspired profile`。

### 可直接采纳的可读性细节

- 正文脚注只在段落末尾或关键结论处出现，避免逐句脚注把阅读打碎。
- 重要命令、端口、配置参数和表格/图片信息必须保留在 Reader 内容或结构化引用中，不能全部丢到 Audit。
- `index.md` 必须提供场景/能力说明和真实可达链接，不能只是文件名罗列。
- `digest_release_status` 若写入每页，必须定义易变字段和受管 hash 排除规则；更简单的选择是把包级 release 状态放在 manifest。

## 不应修改的方向

不因 OKF 接入引入数据库、图谱、中心 taxonomy、runtime attestation、reference agent、viewer 运行时、永久人工工单、trust_score 或全局复制率阈值；这些都会把“文件型知识发布器”重新做重。

## 证据状态

- 本报告是默认首层的有效三方复审记录。
- [旧盲审记录](./20260806-3rd-review-prd-okf.md)保留作历史证据，但已标明其使用了临时 provider 组合，不能代表默认路由。
- 本次只读审查未修改 PRD；是否把上述建议写入 v1.4，需单独决定。
