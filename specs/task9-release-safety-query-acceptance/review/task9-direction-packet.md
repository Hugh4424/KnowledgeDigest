# KnowledgeDigest task9 / K3 方向审查包（direction-advice 输入）

## 任务
- project: KnowledgeDigest；task: `task9-release-safety-query-acceptance`（母任务 task6 PRD 的 K3 卡：「安全地交出去」= 发布安全 + 真实查询集验收）
- 工作目录（只读审查）：`/Users/Hugh/Hugh/Project/KnowledgeDigest-task9-release-safety-query-acceptance`
- 母任务材料：`specs/archive/task6-effect-gap-and-architecture-reset/prd.md` 与 `decision-log.md`；ADR：`docs/adr/0013-write-into-existing-semantic-layer.md`、`docs/adr/0014-real-query-set-acceptance.md`
- K1（已完成）：`specs/archive/task7-semantic-layer-compiler/`；K2（已完成）：`specs/archive/task8-entry-navigation/`

## 已收敛的方向（用户真实答复）
1. **发布单元**：整个知识库根目录一次性原子切换（整库原子）。
2. **流程**：两条命令——发布一条、回滚一条，均无人工确认闸门（继承母任务 T-010=B 全自动、RISK-005 已接受）。
3. **last-known-good**：发布前备份当前版本，保留最近 1 个可回滚版本；切换失败自动恢复；另有显式回滚命令。
4. **失败与成本**：失败运行必须留下 原因码 + 耗时 + 调用数 + token/成本，三项真实非 null；真 0 合法但须附 reason（cache_hit / no_provider_call_yet / provider_unavailable）；null 判失败。
5. **冻结**：三份冻结物（89 份输入清单+指纹、改造前产物快照、对照知识库快照）各自做不可变内容快照 + 逐文件 sha256 清单（不依赖 git）。
6. **发布写权**：新建独立发布根目录（自带结构声明与只写路径列表），不写现有 CompanyBrain（1347 个 md），不改停摆流水线。
7. **范围**：以 K3 为主，允许修发布/验收链路暴露的 K1/K2 缺陷，但必须先记录再修、不重做 K1/K2 核心能力（编译语义、导航生成）。
8. **区分度**：在基线缺陷样本上双向验证——同一问题集能查到「已知坏产物」，同时对正确结果不误判。
9. **出题方式（争议项）**：用户选 C「从资料自动生成题目」；母任务 OPEN-002 要求「用户参与出题」，ADR-0014 写明 acceptance 需要 `human-authored question set`。

## 关键事实（已核实，带证据）
- `full_release.atomic_release`（`src/knowledge_digest/full_release.py:1142-1281`）：整包替换；锁=`kb_lock`（`lock.py:14-35`）；staging=`copytree` 到父目录；切换=`os.replace(formal→rollback)` + `os.replace(stage→formal)`；失败自动恢复旧版并写 `.task3-release-failure-*.json`；**支持保留旧版**；formal 允许「不存在但父目录在」或「已存在且是完整包」。
- `publisher.commit`（`publisher.py:33-256`）：要求目标**不存在或为空目录**，**不保留旧版**；失败 quarantine。当前生产路径调 `commit`（`compiler.py:7922` 等），`atomic_release` **无生产调用**（仅测试）。
- `observed_calls=null` 的确切位置：`publisher.py:113`（`quarantine()` 写 failure.json 时硬编码 null）。
- 成本三项来源：`observed_calls`←`compiler.py:2067-2071` / `task5_runtime.py:3003`；耗时←`semantic_compiler.py:1384-1427`（`elapsed_ms`）；token←`semantic_compiler.py:178-190/805-815/957-999`，缺失时报 `provider_usage_unavailable`。
- K1 批次：`_audit/page-manifest.json` schema=`task7-page-manifest.v1`，`publish_status` 在 K1 只允许 `not_released`（写 `released` 直接 ValueError），`run_status∈{complete,blocked,interrupted}`；K2 把 `navigation={navigation_status,success_pages,blocked_sources,blocked_reasons}` 写回同一 manifest（`semantic_navigation.py:126-146`）。
- **磁盘上没有真实 K1 批次**（`/Users/Hugh/Downloads/KD测试` 为空）；89 份语料在 `/Users/Hugh/Downloads/confluence 原始数据`（1.4 MB，4 个顶层目录：GoInsight / emm for android / emm for ios / merchant system）。
- gbrain：外部检索层，规则为「删除全部非 ASCII，同 slug 按导入覆盖」；本卡不写 gbrain 配置与索引。
- 失败注入点已有先例：`tests/acceptance/test_task3_quality_release.py:815-875`（fail_second_replace / corrupt_staged_replace / busy_lock / fail_install_and_restore）；`atomic_release` 路径**无 fsync**，崩溃一致性未被测试覆盖。

## 审查要求
- **只读**：不要修改仓库任何文件；不要调用任何 provider。
- 这是 **advice**，不是 pass 门；请给出真实、可反驳的意见。
- 输出写到 `/tmp/kd-task9-direction-red.md`（红队）或 `/tmp/kd-task9-direction-blue.md`（蓝队），全文 ≤2 页。
- 每条 finding 用固定一行格式：`severity | 位置(引用 OI/FR/文件:行) | 问题（大白话） | 建议`，severity ∈ blocking|major|minor。
- 允许并鼓励给出 `counterexample`：什么情况下这个方向会产出错误结果。
- 最后给一段 ≤500 字的总结：最关键的 1–3 条 + 你判断为 blocking 的条目编号。
