# sleep-curator 管线机制与外部依赖调研报告

## 一、去重→提炼→合并管线，逐步机制

注：sleep-curator 本身**不做"去重"**（去重判同一性是 ovmc 的活，见 DESIGN.md:10）。sleep-curator 管的是"一堆同主题原始记录 → 提炼成一条知识 → （可能）合并进旧知识"。完整链路 = 读簇(cluster_source) → 检索关联旧知识(pipeline Step1) → 判定新建/重写路径(Step2) → 多轮rethink生成(Step3) → 论断级验证(Step4) → 落盘(writer Step5) → 索引同步(index_sync Step6)，由 orchestrator.py 的 `process_one_cluster` 编排。

### Step 0 簇输入：cluster_source.py
- `cluster_source.py:74-90 check_report_freshness`：读 ovmc 产出的 `report.json` 前先查 mtime，超过 `report_max_age_days`（默认7天，config.py:75）直接抛 `ClusterSourceError`，"fail loud" 不静默消费旧聚类结果。
- `cluster_source.py:103-155 load_clusters`：解析 `report.json` 的 `clusters` 字段，每个 cluster 含 `category` + `member_files`，逐个读原始 memory 文件正文（`_read_member_body:93-100`，去掉 MEMORY_FIELDS 注释块），拼成 `ClusterInput(cluster_id, category, members, tier, min/max_similarity)`。
- `_cluster_id:63-71`：cluster_id = sha256(category + 排序后的文件名列表)[:16]，确定性 id，供 journal 断点续跑识别"已处理过"。
- 这一步只读 ovmc 已经跑完聚类算法产出的结果，sleep-curator 自己不做任何相似度计算/去重逻辑。

### Step 1 关联检索：pipeline.py `retrieve_related` (pipeline.py:219-256)
- 对 `curated/` 全库（含 `_pinned/`，不含 `_needs_review/`，见 236 行 `iter_curated_pages(..., include_subdirs=True)`）算 embedding，用 `embedding_client.embed_batch()` 批量转向量（第241行）。
- 用**余弦相似度**（`_cosine`，247-252行，`np.dot(a,b)/(norm(a)*norm(b))`）对新簇文本 vs 每篇旧 curated 页的 `title+body` 打分，取 top-k（默认 k=5，config.py:39）。
- 这是"关联检索"（A-Mem 第一步），不是"去重判同一性"。

### Step 2 演化路径判定：`decide_evolution_path` (pipeline.py:271-291)
- 只看 top-1 命中（不是全部 k 个候选，271-291行注释明确写了这个简化）。
- 调 LLM `judge_evolution_path`（llm_client.py:203-217）判断"新簇是否与这条旧条目高度相关，该原地重写而非新建"，返回 `should_revise: bool`。
- `should_revise=True` → 走 "revise" 路径（原地重写旧页）；否则走 "new" 路径（新建页）。

### Step 3 多轮 rethink 生成（Letta 风格）：`run_rethink` (pipeline.py:324-382)
- 循环调 LLM `rethink_round`（llm_client.py:219-242），每轮把 `source_text + old_body(revise路径才有) + 上一轮草稿` 传给 LLM，让它输出改进后的正文或 `DONE` token。
- 终止条件三选一：① LLM 主动回复 DONE（`_is_done_token`，pipeline.py:301-310）；② 连续两轮输出相似度（`difflib.SequenceMatcher`，313-314行）≥ 0.92（`convergence_similarity_threshold`，config.py:49）判定收敛；③ 硬上限 `max_rethink_rounds=3`（config.py:45，注释说明 v0.2 是10轮，v0.3 因担心长簇上下文溢出改成3轮）强制停止。
- **revise 路径专属：三分类协议** `apply_revise_classification` (pipeline.py:409-474)：调 LLM `classify_claims`（llm_client.py:244-278）把旧页里每条陈述分成 keep/revise/remove_with_reason/unclear 四类，只有 keep/revise 的内容进最终正文，remove 的丢弃且不留"待确认"占位符；`unclear` 只要出现一条，整个候选强制转 `needs_review`（`ReviseOutcome.has_unclear`，397-403行）。之后再用 `split_claims` 从新草稿里挑出旧页没有的全新论断（按相似度去重，阈值0.85，`_NEW_CLAIM_DUPLICATE_SIMILARITY`，406行），补进正文——这就是"合并"的具体机制：不是新旧文本拼接，而是"旧条目逐条分类保留/更新/删除 + 新增内容去重后追加"。

### Step 4 论断级验证：`verify_claims` (pipeline.py:503-621)
- 先用 `split_claims` 把最终正文拆成独立可验证的陈述句（LLM 调用）。
- 简单事实性陈述（引号内容、路径、CLI flag，正则 `_SIMPLE_CLAIM_TOKEN_RE`，pipeline.py:485）先走关键词/子串预筛（`_extract_simple_token`，496-500行）——token 不在原始来源文本里直接判 unsupported，省一次 LLM 调用；其余陈述调 LLM `verify_claim`（llm_client.py:289-301）逐条判 support/unsupported/partial。
- **cascade 规则**：unsupported 比例超过 `unsupported_cascade_ratio`（默认0.5，config无此项默认写在函数签名里，pipeline.py:508）→ 整个候选转 `needs_review`，不允许"部分发布"（614行）。
- **正文重组（"合并"的最后一环）**：验证通过的 claims 不是简单 `"\n\n".join()` 拼接——会调 LLM `synthesize_body`（llm_client.py:303-326）把散落的 claim 重新组织成连贯叙事段落，随后再调 `check_faithfulness`（llm_client.py:328-367）核对合成正文有没有偏离原始 claims，若发现问题就丢弃合成结果、回退到原始 claim 逐条拼接（"宁可难看也不要看起来忠实实则漂移"，pipeline.py:598-611）。

### Step 5 落盘：writer.py
- `prepare_page`（153-182行）根据结果类型分四种写法：needs_review（`_prepare_needs_review`，独占写不覆盖）、新建页（`_prepare_new_page`）、revise 覆盖旧页（`_prepare_revise_target`，CAS 检查）、pinned 页合并（`_prepare_pinned_merge`，只合并 source_uris 不动正文）。
- **CAS 并发控制**（`_check_cas`，280-307行）：写入前重新计算目标文件当前哈希，与 orchestrator 在生成开始前捕获的 `target_before_hash` 比对，不一致就抛 `CasConflict`，绝不强制覆盖。
- 两阶段提交：先写临时文件+fsync（`write_curated_file_to_tmp`，memfile.py:215-236），journal 记录 `prepared` 事件后才调 `finalize_prepared`（185-228行）做原子 rename/link（新建用 `os.link` 拒绝覆盖已存在文件，revise 用 CAS 后 `os.rename`）。

### Step 6 索引同步：index_sync.py
- `orchestrator.py:245-263`：写盘成功（`committed` journal 事件已落）后才调 `index_sync_client.sync_uri(output_uri, mode=...)`，同步失败不回滚已写的文件（DESIGN.md:332 明文规定）。
- 默认走 CLI 接口：`CliIndexSyncClient.sync_uri`（index_sync.py:128-147）实际执行 `subprocess.run(["ov", "reindex", <uri>, "--mode", mode, "--wait", "true"])`。
- `_assert_scoped_uri`（86-118行）强制守卫：URI 必须是具体页面（有文件扩展名、不是 `curated`/`memories`/`user`/`viking:` 等命名空间根路径），**明文禁止全量 reindex**（DESIGN.md §5.6，一次全量 reindex 成本约15000-25000次 embedding 调用）。

## 二、外部依赖清单（"外部依赖太高"具体证据）

### 1. 依赖 ov (OpenViking) CLI 二进制 —— 强依赖，subprocess 调用
- `index_sync.py:131-136`：`subprocess.run([self._ov_bin, "reindex", uri, "--mode", mode, "--wait", "true"], ...)`，`ov_bin` 默认值 `"ov"`（index_sync.py:124），意味着**必须能在 PATH 里找到 `ov` 命令**，否则每次成功写盘后的索引同步都会失败（虽然失败不回滚写入，但会导致新知识页"写了但搜不到"，索引长期滞后——正是 DESIGN.md:463 pre-mortem 里列的头号失败场景）。
- `index_sync.py` 文件顶部注释（6-9行）承认：OpenViking 官方 URI-scoped reindex 实现 `openviking/service/reindex_executor.py` 在当前环境里根本不存在/不可 import，只能靠 `ov` CLI 或理论上的 HTTP 接口，HTTP 接口（`HttpIndexSyncClient`，index_sync.py:159-187）**未实现**，调用即抛 `NotImplementedError`（180-187行）。
- 也就是说：核心的"写完自动可被检索"这个承诺，完全绑定在一个外部 CLI 工具的可用性和行为稳定性上，且这个 CLI 的 HTTP 等价物工具作者自己都confirm无法访问源码去实现。

### 2. 依赖 embedding 模型 —— 强依赖，但复用 OpenViking 自己的配置
- `pipeline.py:104-107` `EmbeddingClientProtocol`：`embed_batch(texts, batch_size=32)`，Step1检索（retrieve_related, 241行）、Step3 revise路径判定前置检索、reactivation.py 的重新激活相似度计算（reactivation.py:240行）全部依赖它。
- `cli.py:64-76 build_embedding_client`：**直接 `from ovmc.embedding import EmbeddingClient` import 复用 ovmc 工具的类**（69行），说明 sleep-curator 没有自己的 embedding 客户端实现，硬依赖同仓库 `tools/ovmc/ovmc/embedding.py`。
- 具体模型名不在 sleep-curator 里硬编码，而是走 `config.embedding_config()`（config.py:245-250）：默认 `reuse_openviking_config=true`（config.py:88, toml.example:72），读取 OpenViking 自己的 `ov.conf` 文件的 `[embedding.dense]` 段（247行 `self.ov_conf.get("embedding", {}).get("dense")`）——即模型/endpoint 完全由 OpenViking 系统的现有配置决定，sleep-curator 自身不带独立配置项。

### 3. 依赖特定 LLM —— 中等依赖，OpenAI 兼容协议但深度耦合具体 provider 行为
- `llm_client.py` 的 `HttpLlmClient` 是唯一实现，POST 到 `{api_base}/chat/completions`（llm_client.py:174-179），即绑定 OpenAI-compatible chat completions 协议。
- 模型名/endpoint 同样走配置：`config.py:252-265 llm_config()`——优先读 `sleep_curator.toml` 的 `[llm]` 段（model/api_base 均默认空字符串，toml.example:49-50），为空则 fallback 到 OpenViking `ov.conf` 的 `vlm` 段（config.py:257-263）。**没有硬编码具体模型名**，但代码注释里点名了实际测试用的模型是 **DeepSeek**：
  - `llm_client.py:162-166`："DeepSeek's response got cut off mid-JSON-array...Bumped to 16000; DeepSeek allows up to 384K output"
  - `llm_client.py:94-99`："Observed DeepSeek quirk...response occasionally omits the final closing brace"
  - 说明这套 JSON 解析容错逻辑（`_extract_json`，88-122行）是**专门针对 DeepSeek 的输出怪癖调的**，换一个 LLM provider（比如换成 Claude/GPT）不保证这些 workaround 还适用或还需要。
  - 另外还提到 Bailian（阿里云百炼）的 `chat_template_kwargs.enable_thinking` 这类 provider-specific 参数，走 `extra_request_body` 透传（llm_client.py:145-150, config 里对应 `extra_request_body` 字段），说明当前已经在应对至少两家 provider 的私有参数形状。
- 5 个独立 LLM 调用点（judge_evolution_path/rethink_round/classify_claims/split_claims/verify_claim）+ synthesize_body + check_faithfulness，一次簇处理最多可能触发 7+ 次 LLM 调用（revise路径），660 个簇 × 每簇多轮 rethink，DESIGN.md:459 自己承认"数千至一万次 LLM 调用的总耗时和费用未实测"。

### 4. 强绑定 OpenViking 专有数据格式与目录结构 —— 强依赖，贯穿全链路
- **MEMORY_FIELDS 格式**（不是 YAML frontmatter）：`memfile.py:1-17` 明确"格式确认对照 `tools/ovmc/ovmc/memfile.py`"，正文后跟 `<!-- MEMORY_FIELDS {json} -->` 注释块。写（`CuratedPage.render`, memfile.py:108-112）和读（`parse_curated_text`, 133-202）全部按这个专有格式硬编码解析，换一种存储格式（比如纯 Markdown + YAML frontmatter）完全不兼容。
- **viking:// URI scheme**：`memfile.py:47-58 canonicalize_uri`、`cluster_source.py:53-60 _member_uri`、`writer.py:115-122 _page_uri` 都硬编码 `viking://user/{user}/memories/{category}/{filename}` 格式，`index_sync.py:106` 的 `_assert_scoped_uri` 也按这个 URI 形状做校验。
- **目录结构硬编码**：`config.py:143-186 WorkspacePaths` 硬编码路径拼接规则：`data_root/viking/{space}/user/{user}/memories/curated/`，以及 `_pinned/`、`_needs_review/`、`_recall/recall_log.jsonl` 等固定子目录名。换成任何非 OpenViking 的知识库（DESIGN.md §10 提到的"未来扩展到 Obsidian vault"）这套路径/格式假设全部要重写。
- **依赖 ovmc 内部模块**：`freshness.py:53 from ovmc.recall_index import is_recall_index_coverage_sufficient`——sleep-curator 读 fresh/stale 状态直接 import ovmc 私有模块的函数，不是走公共 API。DESIGN.md §10 自己也承认"当前只服务 OpenViking 一个知识库"，特意标注这是"未来如果要扩展的记录，不是当前要构建的能力"。

### 5. 其他外部依赖
- **文件锁**：`lock.py`（未详读但被 orchestrator.py:59 import 为 `FileLock`），每簇处理需要文件系统锁（`config.py:184-185 lock_path`, `188-199 run_lock_path`），依赖底层文件系统支持排他锁语义。
- **journal.jsonl 崩溃恢复协议**：四事件协议（started/prepared/committed/index_synced）依赖 journal 文件的顺序追加写 + 崩溃后重放逻辑（orchestrator.py 大段注释描述这个协议的脆弱边界，比如 Codex Critical#2 fix），本质上是自建的轻量事务系统，没有真正的数据库事务保证，靠严格的写入顺序 + 幂等重放来模拟。
- **网络请求**：LLM 调用（`requests.post`，llm_client.py:174）和 embedding 调用都是同步阻塞 HTTP 请求，无重试队列（`config.py` 的 `[retry]` 段提到 `max_attempts=3`/`base_delay_seconds`，但这是调用层的退避策略，本质仍是对外部网络服务可用性的强依赖）。
- **known gap**：`index_sync_status` 目前是 write-only（index_sync.py:39-51），没有任何自动重试机制去补偿失败的索引同步——这是一个已知但未处理的运维依赖缺口。

## 三、结论摘要
"外部依赖太高"最核心的四条：
1. 索引同步100%依赖外部 `ov` CLI 二进制子进程调用，HTTP 等价路径未实现（连作者都拿不到源码去实现）。
2. embedding 客户端直接 import 复用 `ovmc/embedding.py`，配置默认读 OpenViking 自己的 `ov.conf`，不带独立的 embedding 层。
3. LLM 客户端虽然协议通用（OpenAI-compatible），但已有的容错代码是针对 DeepSeek 输出怪癖精调的，换 provider 不保证行为一致。
4. 数据格式（MEMORY_FIELDS 注释块）、URI scheme（viking://）、目录结构（viking/{space}/user/{user}/memories/curated/）三层全部硬编码为 OpenViking 专有形态，且直接 import ovmc 私有模块（`ovmc.recall_index`），没有抽象层，DESIGN.md §10 自己承认这是"当前只服务 OpenViking 一个库"的既定选择，扩展需要重写整条链路的存储适配层。
