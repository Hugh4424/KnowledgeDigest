# KnowledgeDigest 极简架构重设计 v1

状态：第一轮 3rd-review 为 conditional；方向保留。3rd-review 的设计结果现在只作 advisory，不再要求可认证的 terminal-clean design 结果才能继续实现和真实运行；旧链退役、全量清单、Jina 实际消费、页面身份、Reader/Audit 闭包和质量门仍是硬约束。

## 1. 目标

KnowledgeDigest 是一个人工触发的本地知识消化工具。普通用户只需要：

```bash
digest NEW_DIR KB_DIR
```

工具读取一份用户配置：

```text
~/.config/knowledge-digest/config.json
```

最终只交付可读知识、一个 Home 入口和一个 Audit 入口。用户不需要理解 preflight、projection、quality case、runtime authority、candidate、finalize 或多份中间 ledger。

本次重设计继续满足以下原始要求：

- 事实只来自 `/Users/Hugh/Downloads/confluence 原始数据`；CompanyBrain 只用于验收对照。
- 使用真实 Qwen LLM 和 Jina Embedding。
- Home 按问题和场景进入。
- 页面具有产品、模块、对象、场景、边界五轴。
- 页面类型只有定位、概念、操作、诊断、经验五类。
- Reader 可读，Audit 可回查到原始来源和定位。
- 本次任务仍以冻结的 12 个质量投影中五项全部严格胜过 CompanyBrain 作为 release 条件。

## 2. 关键纠偏

前一版重设计仍然过重：Fact IR、Statement IR、关系图、Projection、独立 Gate、Release 编排都可能形成新的公共概念。它解决了正确性问题，却没有解决产品和维护复杂度。

新方案只保留两层权威对象：

1. `Evidence`：从原文抽取的原子事实和精确来源。
2. `ReaderPage`：面向一个问题/场景的最终业务答案，正文单元直接引用 Evidence；一页可以绑定多个来源。

不再建立 KnowledgeUnit、Relation Graph、StatementFrame、PageProjection、RouteLedger、RenderLedger 等独立公共模型。需要的关联直接保存在 `ReaderPage` 和 `Evidence` 中。

## 3. 产品与验收分离

### 3.1 生产工具

正常 `digest` 只负责：

```text
读取来源 → 提取 Evidence → 编写并验证 ReaderPage → 生成 Home/Reader/Audit → 原子写入
```

生产工具不读取 CompanyBrain，不内置质量投影，不计算 `KD_WIN`，也不提供 `release/finalize` 子命令。

### 3.2 本次任务验收

CompanyBrain 五项比较、六案例、盲审和 `released/not_released` 属于本次改进任务的黑盒验收，不进入正常产品运行路径。

验收读取生产工具已经落盘的实际 Home、Reader 和 Audit，再与冻结的 CompanyBrain 页面比较。验收失败只说明当前候选不能发布，不改变生产工具的接口和正文。

这样新增案例、调整评分或替换 CompanyBrain 基线不会修改 KnowledgeDigest 编译器。

## 4. 唯一应用 Interface

```python
def digest(request: DigestRequest, providers: ProviderAdapters) -> DigestResult:
    ...
```

```python
@dataclass(frozen=True)
class DigestRequest:
    new_dir: Path
    kb_dir: Path
    config_path: Path

@dataclass(frozen=True)
class DigestResult:
    outcome: Literal["completed", "not_released", "blocked", "unavailable", "failed"]
    run_id: str
    home_path: Path | None
    audit_path: Path | None
    reason_code: str | None
```

调用方只需要知道：输入目录、输出目录、配置和最终结果。内部阶段不进入 Interface。

## 5. 三个核心 Module

CLI 只是薄壳，不计为业务 Module。

### 5.1 `compiler`

唯一深 Module。负责把来源编译为完整内存 `CompiledBundle`：

1. 固定并验证来源快照；
2. 切分 Markdown 段落、列表、表格、代码和媒体引用；
3. 调 LLM 为每个来源生成短的来源摘要页，并由结构校验保证每条正文都绑定 Evidence；
4. 为每个有来源的产品强制生成一张 `positioning` 总览页；对检测到多个诊断信号的产品强制生成一张 `diagnosis` 入口页；LLM 只负责在这些硬角色之外发现少量模块主题；
5. 用 Embedding 在固定页面类型内部提供语义路由，并让 LLM 仅根据来源摘要规划少量跨来源主题；Embedding 不能把操作页排进诊断入口，也不能把一个产品挤出入口；
6. 调 LLM 把同一产品的相关来源合成真正回答问题的主题页；定位页必须分开产品线/相邻产品的对象、依赖和选择关系，诊断页必须按异常对象或现象分支组织；
7. 对跨来源主题页做独立的通用事实验证，检查事实覆盖、条件、否定、数值、范围和来源绑定；来源页不再额外复制一轮验证请求，避免 89 条全量运行被验证重试拖垮；
8. 从同一 ReaderPage 生成 Home、Reader 和 Audit 字节。

核心规则：Reader 业务正文只能由 LLM 根据 Evidence 生成；后续代码只能接受、拒绝和渲染，不能补写或改写业务句子。

验证器不是第三个 provider seam，也不是规则补丁集。它固定复用 `SemanticModel.generate`，输入 ReaderPage、其引用的 Evidence 和 qualifiers，输出结构化 violation；violation 只能是缺失 Evidence、无依据正文、条件/否定/数值/范围错误和来源绑定错误。来源页在写页时完成结构、字段和 Evidence 闭包校验，不再重复发送第二轮语义验证请求；跨来源主题页必须经过独立的通用事实验证，失败就只进 Audit，不得继续成为读者入口。主题页允许一次有界修复，二次仍失败则 Audit-only。禁止阈值猜测、产品规则、案例规则和 fallback heuristic。

允许一次通用的整页重新生成：验证器把 violation 交回同一个通用写页请求；不得存在按产品、案例、字段名或历史输出编写的修补分支。第二次仍失败则该主题页只进 Audit。应用 Interface 测试必须用固定 Adapter 覆盖“拒绝 → 一次重生 → Audit-only”，不直接测试私有 helper。

### 5.2 `providers`

只保留两个真实外部 seam：

```python
class SemanticModel(Protocol):
    def generate(self, requests: Sequence[ModelRequest]) -> Sequence[ModelResponse]: ...

class Embedder(Protocol):
    def embed(self, texts: Sequence[str]) -> Sequence[Vector]: ...
```

生产 Adapter：Qwen、Jina。测试 Adapter：固定响应、固定向量。Qwen 请求按来源和主题串行发送，避免并发把可用 provider 压成批量超时；Jina 只负责路由，不负责替正文背书。

Adapter 只负责传输、身份、超时、响应解析和 receipt；不能包含 Q-POS、Q-CON、Q-DIA 等业务规则，也不能生成 Reader 修补文本。

每次运行由两个 Adapter 共享一个 `budget.max_provider_calls` 硬上限；请求前预留额度，超限立即 `unavailable`，不得继续发请求。连接超时不做三次长等待式重试；命令行在加载、来源页、主题页、路由和发布阶段输出无密钥进度。

### 5.3 `publisher`

```python
def commit(bundle: CompiledBundle, kb_dir: Path) -> PublicationReceipt:
    ...
```

只负责路径校验、锁、staging、归档、fsync 和原子提交。它不理解页面类型、Evidence、CompanyBrain 或质量分数。

## 6. 跨边界数据

```python
@dataclass(frozen=True)
class SourceDoc:
    source_id: str
    relative_path: str
    content_hash: str
    text: str
    status: Literal["ready", "empty", "duplicate", "invalid"]

@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    claim: str
    qualifiers: tuple[str, ...]
    source_id: str
    start_line: int
    end_line: int
    block_hash: str
    status: Literal["supported", "ambiguous", "conflict"]

@dataclass(frozen=True)
class ReaderPage:
    page_id: str
    title: str
    question: str
    aliases: tuple[str, ...]
    axes: FiveAxes
    page_type: Literal["positioning", "concept", "operation", "diagnosis", "experience"]
    source_ids: tuple[str, ...]
    summary: ReaderUnit
    sections: tuple[ReaderSection, ...]

@dataclass(frozen=True)
class ReaderSection:
    heading: str
    units: tuple[ReaderUnit, ...]

@dataclass(frozen=True)
class ReaderUnit:
    text: str
    evidence_ids: tuple[str, ...]

@dataclass(frozen=True)
class FiveAxes:
    product: str
    module: str
    object: str
    scenario: str
    boundary: str

@dataclass(frozen=True)
class PublicationReceipt:
    committed: bool
    manifest_hash: str | None
    warning_codes: tuple[str, ...]
```

`ReaderPage` 是唯一答案权威。Home 和 Audit 都从它派生，不能拥有第二套正文。每个产品至少有一个产品级 `positioning` 入口；当来源中存在明确的异常、失败、根因或排查证据时，至少有一个 `diagnosis` 入口，即使只有一个来源。证据不足时显示“原始资料未明确”，不能用其他页型顶替。

实际页面章节按读者职责固定：定位为“当前结论/服务对象与入口/产品关系与选择/边界与未明确”；概念为“使用场景/对象与组成/关系与生效规则/边界与容易混淆”；操作额外明确“预期结果/验证方式”；诊断额外明确“处理动作/升级边界”；经验额外明确“经验教训/适用边界”。摘要也必须带 Evidence ID，不能出现“正文可回查、摘要不可回查”的断链。

`ModelRequest`、`ModelResponse` 和 `Vector` 是 `providers` 内部传输类型；`CompiledBundle` 是 `compiler` 私有提交载体。它们不进入应用 Interface，也不成为新的知识权威。

## 7. 最终知识目录

```text
KB_DIR/
  Home.md
  Audit.md
  products/
    <product>/
      index.md
      <可读主题或来源标题>.md
  _digest/
    run.json
    evidence.jsonl
  _archive/              # 仅更新旧知识库时出现
```

- Home 同时提供按问题、按场景和按产品浏览；每个问题入口只展示对应的页面类型，并保证每个有该类型页面的产品至少保留一个入口。
- Reader 页面先给业务答案，再给适用边界和 Audit 链接。产品定位页和诊断入口页是强制角色；主题页优先回答跨来源问题，来源摘要页负责保留未被主题页覆盖的细节。单来源也可以生成定位或诊断入口，但必须把证据不足写明，不能伪装成跨来源结论。
- Audit.md 是人读回查入口。
- `evidence.jsonl` 合并来源、Evidence、页面绑定和 provider receipt；不再拆成十几份互相引用的机器文件。
- `run.json` 只保存输入 hash、配置身份（不含密钥）、调用统计、来源终态、文件统计和最终状态。

## 8. 配置收敛

运行时只读取：

1. 用户 `~/.config/knowledge-digest/config.json`；Task5 只允许文件中的 `llm.model` 为 `qwen3.8`，不能把其他模型伪装成 `qwen3.8`；
2. 一个随代码发布的 `reader-policy.json`。

`reader-policy.json` 只定义五类页面必需章节、五轴字段和通用正文限制。它不能包含六案例答案、CompanyBrain verdict、产品专用规则或可执行修补文本。

89 源 manifest 和质量 benchmark 属于本次验收材料，不是通用产品配置。

## 9. 明确删除

新 Interface 通过真实 89 源验收后，一次性删除旧 Task5 活跃路径：

- `scripts/task5_reader_quality.py`
- `task5_runtime.py`
- `task5_provider.py`
- `task5_provider_config.py`
- `task5_projection.py`
- `task5_projection_rules.py`
- `task5_quality_gate.py`
- `task5_root_cause.py`
- `task5_semantic_model.py`
- `task5_source_model.py`

42 个 `config/task5-*.json` 不再参与 runtime；仍需留存的历史证据移入归档。

同时清点并删除已经没有真实消费者的旧并行 Reader 栈。不得长期保留“新 Compiler 包裹旧 Task5”的兼容层。

## 10. 简洁性硬约束

- 一个用户命令。
- 一个用户配置。
- 一个应用 Interface。
- 三个核心 Module。
- 两个外部 seam。
- 两个知识权威对象：Evidence 和 ReaderPage。
- 活跃生产 Python 文件不超过 8 个。
- 活跃运行配置不超过 2 个。
- `_digest` 的机器索引固定为 `run.json` 和 `evidence.jsonl`；原始快照目录是不可变的 Audit 回查材料，不是读者知识目录。
- 不允许 `taskN_*` 生产模块。
- 不允许 case-specific Python 分支。
- 不允许生成后字符串修补、raw-copy fallback 或静默 Jaccard fallback。
- Provider 的 408/429/5xx 只允许有限重试；单次 Reader 请求有明确输出上限，避免大响应长期占住全量运行。
- 测试只跨应用 Interface 和两个 provider seam；不测试私有 helper。

文件数是防止再次膨胀的守卫，不是代码质量指标。若未来需求确实需要突破，必须先说明删除测试、真实新 seam 和用户可见收益。

## 11. 失败边界

- 输入、配置或输出路径错误：`blocked`，零 provider call。
- 全局 Qwen/Jina 不可用或预算不足：`unavailable`，不生成伪 Reader；单个来源、主题或路由失败：保留可回查产物并返回 `not_released`。
- 单源抽取失败：该来源只能进 Audit；整次仍可生成候选但不能通过本次验收。主题页不得假装覆盖缺失来源。
- Evidence 含糊或冲突：正文不得给确定结论，只在 Audit 展示。
- ReaderUnit 缺 Evidence、丢条件、反转否定或改变数值范围：跨来源主题页拒绝；一次重生仍失败则 Audit-only。来源页遇到结构或 Evidence 闭包错误时直接 Audit-only，不额外调用语义验证器。
- 写入前失败：旧知识库完全不变。
- 原子提交完成后清理失败：结果保持 completed，记录 warning。
- 提交状态无法判断：`failed`，不能声称完成。
- 用户在提交前中断：CLI 退出码 130，旧知识库不变；中断不伪装成业务结果。
- 存在 Audit-only 来源、页面校验失败或路由失败：运行返回 `not_released`，`run.json` 记录 warning 和来源清单；它不等于本次任务可 release。

## 12. 本次任务的黑盒验收

验收不调用生产内部 helper，只读取真实产物：

1. 同一新 Compiler 完成垂直切片和 89 条全量；
2. 89 条来源全部有终态，无静默遗漏；
3. 对 89 条来源机械验证终态和来源闭包；对六案例人工走读 Home → 跨来源 Reader 主题页 → 来源摘要页 → Audit → 原始来源；
4. 六案例逐实际渲染页面比较五项；
5. 每项都必须严格 `KD_WIN`，`TIE/UNKNOWN/CB_MISSING` 都不通过；
6. 两名独立盲审者读取同一个候选 hash；
7. 只有上述全部通过，任务产物才标记 released。

评分脚本和审查证据放在 `quality/acceptance/`，不进入 `src/knowledge_digest`，也不随正常 `digest` 执行。

验收合同固定 Home、Reader 和 Audit 的标题、必需章节、Evidence 链接及五轴字段读取约定。评分始终读取真实渲染 Markdown；`evidence.jsonl` 只用于核对来源闭包，不能替代 Reader 可读性评分。布局约定变化必须显式更新验收合同，不能静默改变分数。

## 13. 迁移方式

1. 先冻结新应用 Interface 和黑盒验收。
2. 复用现有 Qwen/Jina HTTP 实现作为两个薄 Adapter。
3. 新 Compiler 在隔离输出目录完成垂直切片和 89 源；不得写旧 KB。
4. 新旧实现可以复用同一 provider response 做只读对照，但不能长期双轨运行。
5. 新实现通过真实验收后切换正式 CLI。
6. 同一个变更中删除旧 Task5 活跃模块、配置和私有函数测试。

不采用“先保留旧实现，再逐步增加新包装层”的迁移方式，因为那会永久增加复杂度。

## 14. 非目标

- 不做后台任务平台、数据库、向量库或 AgentMemory 集成。
- 不做插件系统或通用工作流引擎。
- 不为未来可能的模型、存储或页面类型预建 seam。
- 不要求正常用户每次运行都证明胜过 CompanyBrain。
- 不要求 89 条来源生成 89 个页面；要求每条来源都有明确终态和 Evidence 闭包。

## 15. 独立审查记录

- 工具：3rd-review。
- 有效审查 provider：`opencode/v4flash`。
- 冻结材料 hash：`ae3440b158eb080f81440beed914e23bdd85aa524cf3b0aff11ca83353e88ed0`。
- runtime：`8af68da0-28d2-4eea-aaa6-971b86d5077b`。
- 结论：`approve`；保留整体架构，补清通用验证机制、跨模块类型、终态与验收读取约定。
- 审查通过只表示架构方向可执行，不表示代码完成、真实 89 条通过或知识质量已胜过 CompanyBrain。

## 16. 2026-08-31 3rd-review 纠偏

第一轮新的独立审查确认了方向，但拒绝把这份设计直接当成实现授权。必须补齐以下约束；它们是本设计的组成部分，不是下一轮临时补丁。

### 16.1 只有一条真实生产入口

用户可执行的写入入口固定为：

```text
digest NEW_DIR KB_DIR --config ~/.config/knowledge-digest/config.json
  -> compiler.digest()
  -> providers
  -> publisher.commit()
```

`task5_runtime.py`、`task5_provider.py`、旧 Task5 evaluator 和旧的巨型 Audit writer 不得再被任何生产命令导入。迁移完成前，若它们仍保留，只能放在 `legacy/` 作为不可导入的历史材料；CI 增加 import/entrypoint 检查，发现真实运行触碰旧模块立即失败。不能用“新 compiler 包一层旧 runtime”作为过渡完成状态。

### 16.2 全量清单是机器对象，不是第三套知识权威

保留两个语义权威对象 `Evidence`、`ReaderPage`，另加一个只负责运行闭包的 `RunManifest`：

```text
RunManifest.sources[89]
  source_id, raw_hash, status, evidence_ids, reader_page_ids, failure
RunManifest.routes[*]
  query_id, question/scene, selected_page_ids, embedding_receipt
RunManifest.pages[*]
  page_id, page_key, page_type, axis values, source closure, surface hash
```

`RunManifest` 不是业务事实，也不产生正文；它只回答“89 条是否逐条有终态、哪些页面由哪些来源构成、Jina 选了什么、最终字节是什么”。`Audit.md`、`_digest/run.json`、`_digest/evidence.jsonl` 均从这三个对象一次派生，禁止第二个 writer 自己拼一份来源或页面关系。

### 16.3 固定页面身份和缺失语义

每个页面都有稳定 `page_key`：

- 来源摘要：`source:<source_id>`；
- 业务答案：`answer:<question_id>:<page_type>`。

公开文件名只使用经过安全校验的可读标题；同名时按 `page_key` 稳定加 `-2`、`-3`，不把 hash 放入文件名。Home 的 route rows 和页面清单都由 `RunManifest.pages` 生成，缺少声明的页面直接成为 `missing_page`，不得靠另一个页面顶替。

来源状态只有 `ready`、`known_empty`、`duplicate_alias`、`provider_failed`、`unsupported` 五类。`known_empty/provider_failed/unsupported` 不出现在 Reader/Home，不生成空模板或原文页，只在 Audit 记录原始 hash、块定位、失败原因和可回查内容；89 条闭包仍必须完整。`duplicate_alias` 必须绑定 canonical source 的 hash 和 Reader link，不能静默合并掉自身审计记录。

### 16.4 Jina 必须改变真实路由输入

Jina 不是只写一份调用收据。每个问题/场景入口先生成 query embedding，再对 89 条来源摘要/证据描述做候选排序；`RunManifest.routes` 保存 query hash、候选 page/source id、分数、rank、selected 原因。只有 selected closure 进入对应 Qwen 业务答案请求；Home 只链接被 route 验证通过的 `ReaderPage`。没有 selected page、向量维度不符、route receipt 与实际 Qwen 输入不一致时，当前 route 失败并阻断发布。

切片和全量均使用同一规则。切换一个固定测试向量后，选中的页面必须变化；如果输出页面和 Qwen 输入完全不变，该测试判定 Jina 未被消费。Jina 只负责候选路由，不负责事实正确性；事实仍由 Evidence 和 Qwen typed page 共同约束。

### 16.5 Qwen 是唯一业务正文作者，生产链不做语义重生成

Qwen 返回版本化 JSON，必填 `page_key/question/page_type/five_axes/summary/sections/answer_units`；每个 `answer_unit` 只引用当前 Evidence ID。未知字段、缺字段、额外事实、丢条件/否定/数字、原文整段复制都拒绝。生产 renderer 只做格式、链接、锚点和分页，不做第二次业务改写；失败就 Audit-only/not_released。需要重新生成时由用户重新运行同一个 `digest`，不是由 renderer 内藏 retry/overlay。

这样删除“通用重生成”这个可能变成补丁的暗门，换取更简单且可解释的失败：模型结果不合格就是不合格，不用代码猜测怎么修正文。

### 16.6 真实实施顺序

1. 先让 `digest` 实际调用新 `compiler.digest()`，并用固定 Adapter 证明旧 Task5 模块没有被 import。
2. 实现 `Evidence → ReaderPage → RunManifest` 单向编译；先做一个业务页面和一个 source page 的端到端 golden test。
3. 接入 Jina 的 selected closure，再接 Qwen typed JSON；加入非法 JSON、空 route、证据错绑、原文复制和失败源负例。
4. 接入单一 renderer/publisher，产出固定的 Home、Reader、Audit 和三个 machine files；跑垂直切片后继续同一命令完成 89 条全量。
5. 真实运行只写新的 Downloads 目录；先做 Reader/Audit/source closure 检查，再做 CompanyBrain 五维逐 projection 比较和两名独立审查。任一失败保持 `not_released`。

这五步是同一个任务的实施顺序，不是新增任务；每一步都必须证明真实消费者已经换成新链，才允许进入下一步。

## 17. 3rd-review 纠偏补充（2026-08-31，规范性）

本节优先于本文此前任何“保留旧实现”“可选回退”“修复重试”的表述。

### 17.1 迁移终态

切换完成后，仓库中只允许 `digest -> compiler.digest -> providers -> publisher.commit` 作为写入链。`task5_runtime.py`、`task5_provider.py`、旧 Task5 写入脚本和旧巨型 Audit writer 必须从源码工作树删除；历史证据只能留在 `quality/evidence/`，不能放在可导入的 `legacy/` 包中。CI 用 AST/import 检查生产入口，命中这些模块即失败。`--no-llm` 是独立离线命令，不得调用新链，也不得被真实 provider 验收当作生产路径。

### 17.2 Canonical 序列化与身份

所有哈希统一使用 UTF-8、NFC、LF、JSON `sort_keys=true`、`separators=(",", ":")`；路径统一 POSIX 相对路径。定义如下：

- `source_id = "src-" + sha256(relative_path + "\\0" + raw_bytes)[:20]`；
- `question_id = sha256(NFC(question) + "\\0" + NFC(scene))[:20]`；
- `page_key` 只允许 `source:<source_id>` 或 `answer:<question_id>:<page_type>`；
- `payload_sha256` 哈希的是实际发送给 Qwen 的完整序列化 JSON，不是候选 source id 列表；
- `surface_sha256` 哈希最终 UTF-8 Markdown 字节；`tree_sha256` 哈希按相对路径排序的 `sha256(bytes)  relative_path` 清单。

`RunManifest` 是严格 JSON 对象，未知字段、重复 source/page/route、缺少必填字段、状态与列表不一致都失败。最小结构为：

```json
{
  "schema_version": "knowledge-digest-run-manifest.v1",
  "source_count": 89,
  "sources": [{"source_id":"...","raw_hash":"...","status":"ready|known_empty|duplicate_alias|provider_failed|unsupported","evidence_ids":[],"reader_page_ids":[],"failure":null}],
  "routes": [{"query_id":"...","question":"...","scene":"...","candidate_source_ids":[],"selected_source_ids":[],"selected_page_ids":[],"scores":[],"embedding_receipt":{"model":"...","input_sha256":"..."},"qwen_payload_sha256":"...","status":"ready|failed","failure":null}],
  "pages": [{"page_id":"...","page_key":"source:...|answer:...","page_type":"...","source_ids":[],"surface_sha256":"..."}],
  "tree_sha256":"..."
}
```

### 17.3 来源状态与 89 条闭包

状态判定顺序固定为：先判 `known_empty`；再按完整原始字节哈希判 `duplicate_alias`；再判扩展名/编码是否 `unsupported`；provider 或 typed contract 失败为 `provider_failed`；其余为 `ready`。重复内容的首个稳定路径为 canonical，后续路径为 alias；alias 不发 Qwen 请求，但必须有自己的 source row、raw hash、`duplicate_of`、Audit 记录和 canonical Reader link。空源必须写 `failure.code=known_empty_source`；provider 失败必须写 `provider_failed`；不支持格式必须写 `unsupported_format`。

89 条预期集合不是代码里的隐含数字：运行前从冻结 `config/task5-source-page-manifest-v2.json` 读取 `relative_path/raw_hash/expected_status`，必须逐项等于输入快照；缺失、增加、哈希漂移或状态漂移立即 `blocked`，不得生成半套 Reader。发布后 `RunManifest.sources` 必须恰好 89 行；每个非空 canonical source 至少有一次 Qwen source compile 尝试，alias 按上面规则豁免；任何 source 无终态都是失败。单个 route/provider 失败不抹掉候选：该 route 写 `status=failed`、非空 `failure`，整包只能 `not_released`。

### 17.4 Jina 的真实消费

Jina 的 descriptor 只能由当前 raw source 的路径、产品结构、Evidence 摘要和固定 query 组成，禁止使用已生成 Reader 文本，避免路由循环。每个 route 必须保存候选全序列、分数、选中原因、embedding 请求/响应哈希和实际 Qwen payload 哈希。`selected_source_ids` 必须与 Qwen payload 中的 source closure 完全相等，并且与该 ReaderPage 的 `source_ids`、Home route 行完全相等；只写 receipt 不算消费。固定向量负例必须使 selected closure 改变并使 payload hash 改变，否则失败。

### 17.5 Qwen typed contract 与不可重写

Qwen 输出必须包含 `page_key/question/page_type/five_axes/summary/sections`，且每个 ReaderUnit 至少有一个当前 Evidence ID；Evidence ID 必须属于当前 source closure，正文不得出现 closure 外事实、整段原文复制、未裁决否定/数值/范围或未知字段。解析失败、证据错绑、缺字段、违反页面类型均为 `failed`/Audit-only。renderer 只能做 Markdown 排版、链接、锚点和确定性的分页，禁止补写、改写、overlay、业务化兜底或隐藏 retry；恢复只能由用户重新执行 `digest`。

### 17.7 2026-09-03 用户合同修订

Task5 的生产 LLM 固定使用用户配置中的 `https://dashscope.in.whatspos.cn/v1` / `qwen3.8`，embedding 继续使用配置中的 `jina-embeddings`。此前关于 `qwen3.6` 的文字只保留为历史记录，不得作为当前 provider 身份。

用户明确选择继续推进，不再把 3rd-review 是否产出可认证的 terminal-clean design 结果作为实现、真实消化或 M402 的硬前置。若设计审查结果存在，只作为 advisory 风险记录；`parent_design_review` 可以为空。实现审查、89 条来源终态、Qwen/Jina 真实消费、Reader/Audit 闭包和 12 个质量投影的五项全 `KD_WIN` 仍是独立硬门，未满足时只能 `not_released`，不能借设计审查豁免。

### 17.6 实施步骤的可执行验收

步骤 1 必须证明 `digest` 的 import graph 不含旧 Task5 模块；步骤 2 必须有固定 Adapter 的 source page + answer page + Home + Audit + atomic publish golden test；步骤 3 必须证明 89 行 source manifest 和 source/page closure；步骤 4 必须证明 live Qwen/Jina receipt、payload equality 和 embedding mutation negative test；步骤 5 必须在 Downloads 新目录完成真实运行。任一步骤没有对应测试或字节证据，不得进入下一步，也不得写 `released`。
