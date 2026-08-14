# mini-task plan：Reader 质量整合

## 实现

1. 扫描普通来源，按顶层目录建立稳定 product key/display name。
2. 读取可选语义候选；只有 source URI/指纹匹配才合并候选正文。语义候选由固定小批量、零重放的受控编译器生成，失败来源保留 fidelity-only 回退。
3. 建立唯一逻辑 `source_id → reader_paths` 映射；无法归属使用 `unclassified/general`，推断原因、指纹和完整身份写 Audit。
4. 生成根入口、产品 index/overview、知识类型入口、模块 index 和 `knowledge/<source>.md`；超过 300 行按顺序拆成 part 页面并互链。
5. 正文用语义候选或保真清理版：去 frontmatter、内部字段、hash 脚注、重复 H1，保留 Markdown、表格、代码、链接和事实顺序。
6. Reader frontmatter 只保留人需要的 title/type/status/description；根索引不输出逐页 signals、hash 或 topic id。
7. 编译后执行覆盖、泄漏、导航、事实保真和行数检查；复用既有 Task3 质量/发布边界，并计算 100 分 Reader 质量代理。
8. 使用 run-scoped 候选目录；检查前不替换旧包。

## 依赖接口

输入 source manifest 的最小字段是 `source_id/source_uri/relative_path/title/content_fingerprint/line_count/validation_status`；语义候选的最小字段是 `source_uri/content_fingerprint/title/summary/body/module/semantic_status`；Audit 映射的最小字段是 `source_id/reader_paths/product/module/mapping_reason/content_fingerprint/semantic_status`。TopicIndex 仅作为可选只读输入，读取 `source_members/source_ids/product/module/object_intent/published_path`。

## 文件边界

- `specs/task3-reader-quality-integration/` 是 WorkflowHub TaskHandle 使用的四份材料镜像，必须与根目录四份材料逐字一致；不另立一套需求。
- 新增 `src/knowledge_digest/reader_compiler.py`。
- 修改 `scripts/task3_full_release.py`，增加 `--raw-input` 模式并保留 `--steps-json`。
- 新增 `scripts/task3_semantic_compile.py` 和 `scripts/task3_reader_comparison.py`，分别负责固定批次语义候选和真实结果对比。
- 新增 acceptance fixture/test，覆盖成功、无法归属兜底、超长拆分、空内容/事实损失、缺源、泄漏、导航逃逸、旧包保护和 80 分代理。
- 同步必要命令说明，不改 Task2-C 合同。

## 测试

先写失败 fixture，再实现；跑相关 acceptance；跑完整 pytest；再用 `/Users/Hugh/Downloads/confluence 原始数据` 写入新的 Downloads 目录；最后用新增的 `scripts/task3_reader_comparison.py` 与 CompanyBrain 对比数量、层级、入口、泄漏和覆盖。

## 回滚

只回滚本 mini-task 新增代码/测试；保留 Task3 基线、失败证据和旧正式包。merge、push、archive、cleanup 不在实现阶段执行。
