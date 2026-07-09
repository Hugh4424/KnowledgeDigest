# ovmc 工具分析：聚类判断机制 + 资源瓶颈

调查时间：2026-07-05
仓库位置：`/Users/Hugh/Hugh/Project/OpenViking/tools/ovmc/`

---

## 1. 聚类判断流程：输入 → 判断逻辑 → 输出

### 1.1 总体流水线（Stage A → Stage B → Rule Engine）

```
gather_category()          -- ovmc/gather.py:63
  ├─ 读取 memories/<category>/*.md 文件
  ├─ 计算 content_hash（精确去重，独立于聚类）
  └─ 对 body 长度 >= 20 字符的文件调用 embedder.embed_batch()
       -> ovmc/embedding.py:32 EmbeddingClient.embed_batch()
       -> HTTP POST {api_base}/embeddings （OpenAI 兼容协议）

build_clusters()            -- ovmc/dedup.py:110
  ├─ 计算 NxN 余弦相似度矩阵 (embedding.py:64 cosine_similarity_matrix)
  ├─ complete-linkage 分组 (_complete_linkage_groups, dedup.py:50)
  │    - 按相似度降序处理 pair，只有该候选与组内所有已有成员都
  │      >= threshold 才能入组（拒绝 union-find 式传递链式合并，
  │      避免 A~B~C~D 弱链导致 450 文件误合并的历史事故）
  ├─ 先在 similarity_high(0.90) 阈值下跑一轮 -> tier="auto_candidate"
  └─ 剩余未被认领的文件，再在 similarity_review(0.80) 阈值下跑一轮
       -> tier="needs_review"

build_merge_plans() -> MergePlan（每个 cluster 一个）-- dedup.py:176

[需人工复核层] classify_cluster()  -- ovmc/rules.py:434
  仅对 tier="needs_review" 的 cluster 生效（auto_candidate 走 LLM
  review + content merge 的独立老路径，见 cli.py:322-369）
  7 个特征，全部按 worst-pair(min) 聚合到 cluster 级：
    F1 embedding相似度(复用Stage A) F2 词汇Jaccard F3 TF-IDF余弦
    F4 结构化字段(trajectory_name/backlinks/outcome) F5 时间戳间隔
    F6 标题相似度(difflib) F7 LLM语义判分(默认开启，可降级为None)
  决策树 6 分支（rules.py:434-560 完整列出），输出三态：
    AUTO_MERGE / KEEP_SEPARATE / INSUFFICIENT_SIGNAL

输出:
  - report.py 生成 dry-run 报告（merge plan 列表）
  - INSUFFICIENT_SIGNAL 簇写入 regret_queue.jsonl（cli.py:271）
    供未来人工标注扩充标定集
  - MergePlan.executable（dedup.py:211）最终决定是否可执行合并，
    但真正落盘还要过 safety.index_sync_verified 三重闸门
    （cli.py:393-410），当前默认 False，dedup --execute 恒被
    降级为 dry-run
```

### 1.2 关键事实：needs_review 层当前 100% 走不通

`ovmc/rules.py:82-167`（RuleThresholds docstring）记录了 2026-07-03 的标定结论：
用 80 条 LLM 标注的金标准簇（same/partial/different）标定 F1-F7 全部特征，
发现在真实语料上 **same 簇和 partial 簇的特征值范围完全重叠**（例如 F3
TF-IDF：所有 same 簇最高分 0.728，比某个 partial 簇的 0.809 还低）。

按用户明确指示"宁可漏合并也不要错合并"，所有 AUTO_MERGE 分支的阈值被
故意设置在全部 80 个观测样本范围之外，导致：
- 660 个真实 needs_review 簇 **100% 落入 INSUFFICIENT_SIGNAL**
- 规则引擎能跑，但对当前语料没有实际自动合并能力，全部进入人工复核队列
- 这不是 bug，是显式记录在案的、验证过 false_merge_rate=0/40 的保守选择

---

## 2. 资源大头：38.6GB 内存疑点未被证实

### 2.1 确认结论

**未在仓库内或本机运行进程中找到与"38.6GB"匹配的证据。** 具体核查如下：

- ov.conf 配置的 dense embedding 模型：`openai/jina-embeddings-v5-text-small-retrieval-mlx`
  （`/Users/Hugh/Hugh/Project/OpenViking/ov.conf:8`），经 litellm 代理，
  api_base = `http://localhost:7777/v1`
- 该模型由本机独立 macOS 应用 **oMLX.app** 提供服务（不在本仓库代码内，
  没有任何启动脚本/docker-compose/plist 属于此仓库）：
  - `oMLX.app` 主进程 PID 6354，`omlx-server` 子进程 PID 54705，
    `lsof -i :7777` 确认 LISTEN
  - 实测 RSS：oMLX 主进程 31.7MB，omlx-server 77.3MB（空闲态，均远小于 38.6GB）
- 模型权重实体文件位置：
  `/Users/Hugh/Hugh/Project/olmx/jinaai/jina-embeddings-v5-text-small-retrieval-mlx/model.safetensors`
  所在目录总大小 **1.1GB**（非 38.6GB）
- 模型架构（config.json）：`Qwen3ForCausalLM` 改造为 embedding 用途，
  hidden_size=1024，28 层，属于 0.6B 级小模型量级，1.1GB 磁盘占用符合预期
- HuggingFace 缓存目录 `~/.cache/huggingface/hub/models--jinaai--jina-embeddings-v5-text-small-retrieval-mlx`
  只是个 4KB 空壳（实际权重在上面 olmx 路径）

**结论：38.6GB 这个数字目前查无实据。** 可能来源：
1. 用户记错的是另一次不同任务/不同模型的内存观测
2. 峰值内存（实际跑 embedding 请求时 MLX 统一内存瞬时占用）——本次未触发
   真实推理请求，无法验证峰值
3. 与 oMLX.app 整体磁盘缓存/多模型共存有关（本次未逐一排查该 app 内其他模型）

若该数字来自另一处（如系统监控截图、Activity Monitor），需要用户提供具体
观测时间点或触发方式以便复现验证。

### 2.2 能否替换成小模型/外部 API

**结构上完全可以，但当前有一处"死配置"必须先修。**

- `ovmc/config.py:199-204` `Config.embedding_config()`：
  ```python
  def embedding_config(self) -> dict[str, Any]:
      if self.get("embedding", "reuse_openviking_config", default=True):
          dense = self.ov_conf.get("embedding", {}).get("dense")
          if dense:
              return dense
      return self.get("embedding", default={})
  ```
  只读取 `ov_conf["embedding"]["dense"]` **顶层字段**（provider/model/
  api_base/api_key），**从未读取 `dense.credentials[]` 数组**。
- ov.conf 里其实已经配置了第二个 credentials 候选——外部 API：
  `/Users/Hugh/Hugh/Project/OpenViking/ov.conf:20-25`：
  ```json
  {"provider": "litellm", "model": "openai/jina-embeddings",
   "api_base": "https://llm.paxszapp.com/v1", "api_key": "pass1234"}
  ```
  但这是**死配置**，任何代码路径都不会读到它。

**要切换到外部 API 或更小模型，两种做法：**
1. 最小改动：直接把 ov.conf 顶层 `embedding.dense.{provider,model,api_base,api_key}`
   改成外部 API 的值（或换成任意更小的 embedding 模型），ovmc 无需改代码，
   因为它就是走 OpenAI 兼容 `/embeddings` REST 协议（embedding.py:41-61），
   与后端具体是什么模型无关。
2. 若想保留"本地优先、外部兜底"的双通道语义，需要改
   `Config.embedding_config()` 增加对 `credentials[]` 的 fallback 遍历逻辑
   （目前完全没有这个降级路径，纯粹读顶层字段）。

---

## 3. 外部依赖清单

### 3.1 ovmc 自身 Python 依赖（pyproject.toml）
- numpy>=1.24（相似度矩阵、向量运算）
- requests>=2.28（embedding/LLM HTTP 调用）
- dev: pytest>=7.0
- 无 faiss/hnswlib/sklearn 等 ML 库依赖——`embedding.py:64-75` 明确注释：
  当前规模（每类目千级文件）用 numpy 稠密 O(n²) 矩阵已够用，
  未来 2700+ 文件规模需要引入 ANN 库才会成为问题

### 3.2 外部服务/模型（通过 HTTP 调用，非 Python 依赖）
| 用途 | 模型/服务 | 地址 | 配置位置 |
|---|---|---|---|
| Embedding (F1 相似度) | jina-embeddings-v5-text-small-retrieval-mlx | localhost:7777 (oMLX.app 本地服务) | ov.conf:8 |
| Embedding 备用(死配置，未生效) | jina-embeddings | llm.paxszapp.com | ov.conf:20-25 |
| LLM (F7 语义判分 + Stage B review) | 见下 | 见下 | ov.conf `vlm` 段 + ovmc.toml `[llm]` |
| LLM 实际标定用后端 | dashscope qwen3.6 | dashscope | rules.py 文档字符串引用的标定记录 |
| sleep-curator 工具当前用 LLM | DeepSeek 官方 API | api.deepseek.com | sleep_curator.toml:32-39（因本地MLX"烧过多token"+其他两个后端不可达而切换） |

### 3.3 运行时外部程序调用
- `ov mv` CLI（可选路径，`move_with_ov_cli`，dedup.py:314）——保持
  OpenViking vectordb 索引同步，默认关闭（默认走 shutil.move 直接文件移动）

---

## 附：关键文件索引

| 文件 | 作用 |
|---|---|
| `tools/ovmc/ovmc/dedup.py` | Stage A 聚类核心 + MergePlan + 归档移动 |
| `tools/ovmc/ovmc/rules.py` | needs_review 层确定性规则引擎（F1-F7 决策树）|
| `tools/ovmc/ovmc/embedding.py` | Embedding HTTP 客户端 + 余弦相似度矩阵 |
| `tools/ovmc/ovmc/config.py` | ovmc.toml 加载 + ov.conf 自动发现/合并 |
| `tools/ovmc/ovmc/gather.py` | 文件读取 + embedding 批量调用入口 |
| `tools/ovmc/ovmc/cli.py` | 全流程编排（scan/dedup/prune 命令）|
| `tools/ovmc/ovmc/llm_review.py` | Stage B LLM 复核 + F7 语义判分 |
| `ov.conf` (repo root) | embedding.dense / vlm 后端配置源 |
| `tools/ovmc/ovmc.toml` | ovmc 自身配置（阈值/gates/safety）|
