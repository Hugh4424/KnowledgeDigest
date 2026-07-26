# B4 — LLM 提炼生成器 执行报告

验收：`uv run pytest tests/ -q` → **111 passed**（B4 前 87）。当时未单独 commit；已随 Phase 2.5 closeout 合入 `c075570`。

## 验收命令实测

| 命令 | 结果 |
|---|---|
| `uv run pytest tests/ -q` | 111 passed |
| `wc -l llm.py` | 198 行（超 ≤150 目标 48 行，见下） |
| `grep -c "^import\|^from" llm.py` | 7，全标准库（json/os/urllib.error/urllib.request/typing + 本地 errors） |
| `grep -rn "openai\|anthropic" pyproject.toml` | 零匹配 |

**零网络证明**：临时在 `tests/conftest.py` 加 autouse fixture 把 `socket.socket.connect` /
`socket.create_connection` 全部替换成抛 AssertionError，111 passed 不变，证明没有任何真实请求。
验证后已删除该临时文件。

**行数说明**：198 行里 `_PROMPT_RULES` 常量占 33 行（6 条防丢失约束 + JSON schema），
纯代码约 165 行。已做的压缩：合并三个 env 校验分支为循环、去掉 `_request_payload` 的
无用 tuple 返回、`build_generator` 内联。剩下的都是必要路径（两种格式的
endpoint/header/body/解析 + 6 类错误分支）。要压到 150 只能删 prompt 约束或错误分支，
两者都是本批次的核心要求，所以没删。

## 关键判断点：硬门拒绝率实测（重点）

用 5 条真实形态 claim（含表格行、错误码、why 陈述）跑 7 种真实 LLM 常见改写：

| 改写形态 | 硬门结果 | 丢失 claim |
|---|---|---|
| 重排 + 加标题 | PASS | 0/5 |
| 合并成段（换行变空格） | PASS | 0/5 |
| 加 markdown 列表符 | PASS | 0/5 |
| 行内多一个空格 | **FAIL** | 1/5 |
| 中英标点互换（. → 。） | **FAIL** | 3/5 |
| 改一个词（3 times → three times） | **FAIL** | 1/5 |
| 表格改散文 | **FAIL** | 1/5 |

**7 种里 4 种被拒，且失败的全是"语义完全等价"的表面改写。**

`_validate_candidate:400` 是 `claim["text"] in candidate["final_body"]` 纯子串判断，
对空格、标点、任何一个字符零容忍。真实 LLM 默认就会规范化标点和空白，
所以**默认 prompt 下拒绝率会接近 100%，LLM 路径形同虚设**（每次都落 fallback，
最终页面 = claim 拼接，和恒等函数产出无区别）。

**但这不是无解**：PASS 的三种说明只要 LLM 严格逐字保留 claim 文本，
"重排 + 加标题 + 加解释性上下文"这类真正有价值的提炼是能过门的。
所以 prompt 里把"逐字"约束写到最强（第 3 条明确说"any paraphrase is rejected
and the whole refinement is discarded"）是有效缓解，但**不能保证**。

**未自行放宽硬门**（按剧本 363 行要求），`_validate_candidate` 一行未动。
交给用户拍板的选项：
1. 保持逐字（防漂移最强，但要求 prompt 极严 + 可能高 fallback 率）
2. 放宽为 normalize 后比对（复用 `faithfulness.normalize_claim`：whitespace 折叠 + casefold）
   —— 能救"多空格"和大小写，救不了标点和改词
3. 放宽为语义校验（需要第二次 LLM 调用做 judge，成本翻倍，且 judge 本身可能漂移）

建议 2，因为 whitespace 差异是 LLM 最高频且最无害的偏差，
而标点/改词确实应该继续拒绝。

## 第二个发现：丢 claim 有个真实漏洞（非本批引入）

`_validate_candidate` 的所有门都在遍历 **candidate 返回的 claims**，
从不断言 `source_claims ⊆ candidate_claims`。

后果：LLM 只要"少返回一条 claim + coverage_mapping 也同步少一行"，就能**合法通过**校验，
那一行内容直接不进页面。丢失只体现在 round record 的
`unsupported_claim_count=1` / `retained_input_unit_ratio=0.5`，没有任何门拦它。

已用 `test_llm_dropping_a_claim_is_accepted_today_and_loses_that_line` 把当前行为钉住
（断言 selected_round==1 且 "Claim two." 不在 final_body），并在 docstring 写明这是 FINDING。
补 retention 门属于新增校验逻辑，本批次明确禁止，**留给用户拍板**。

注：更常见的丢失形态（claims 列表照报、final_body 里少了那行）是能被逐字门抓到的，
已用 `test_llm_dropping_a_claim_while_keeping_coverage_rows_is_rejected` 覆盖，
走 fallback 且端到端不丢内容。

## 「LLM 产出与恒等输出无区别」问题

**存在，但有条件**：一旦落 fallback，产出就是 claim 拼接，与恒等路径无实质区别。
考虑到上面实测的拒绝率，默认配置下这会是常态。

已加正向端到端断言防止这个问题变成不可观测：
`test_end_to_end_accepted_llm_body_reaches_the_committed_page` 断言
`## Refined by the model` 真的出现在落盘 md 里，
`test_llm_reorganization_that_keeps_claim_text_verbatim_passes_the_hard_gate`
断言模型加的解释性内容被保留。这两条测试一旦挂，说明 LLM 路径退化成恒等函数。

## 改动文件

| 文件 | 改动 |
|---|---|
| `src/knowledge_digest/llm.py` | 新增，198 行 |
| `src/knowledge_digest/config.py` | `llm_enabled`/`llm_format` 字段、白名单 2 键、`_require_bool`、env 读取、format 校验 |
| `src/knowledge_digest/draft.py` | 新增 `resolve_generator()`；context 加 `target_page`；`generator or resolve_generator(settings)` |
| `src/knowledge_digest/pipeline.py` | `audit_run`/`_audit_run_locked` 加 `generator` 参数并传给 `draft()`（552 行） |
| `src/knowledge_digest/cli.py` | `--llm-format` / `--no-llm`，`--llm-format` 隐含启用，`--no-llm` 优先 |
| `tests/acceptance/test_phase25_llm.py` | 新增，24 个用例 |

`_validate_candidate` 与 `faithfulness_check` fallback 分支：**一行未动**。

## 注入链实测

- `--no-llm` → 离线跑通，1 formal output committed
- `--llm-format bedrock` → argparse 拒绝
- `KD_LLM_FORMAT=openai` 无 key → `validate: stage=llm; failed input KD_LLM_API_KEY` 退出，**不静默降级**

## dry-run 说明

dry-run 路径（pipeline.py:525）没传 generator：`draft(dry_run=True)` 走 `_planned_draft` 提前
return，根本不会调 generator。传了也是死参数，故未传。
