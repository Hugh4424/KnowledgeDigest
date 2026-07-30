# Keep reader publication separate from audit data

Status: accepted

正式主题页直接承担读者知识页角色，由根目录 `Home.md` 和分类索引导航；`_digest`、`_queues` 和归档记录继续只用于审计、恢复与运行状态。选择这一结构是为了不复制 Claim、Evidence、Provenance，也不让读者依赖内部运行文件。

## Considered Options

- 复制一套读者投影。未采用：内容和链接会重复，容易漂移。
- 继续把 `_digest` 作为入口。未采用：审计记录不适合日常阅读。

## Consequences

- `kb.structure.md` 必须声明托管目录、读者入口和分类规则；缺少声明时，旧知识库不得被写入。
- 新知识库只创建带 `managed_by: KnowledgeDigest` 的 `Home.md`、分类索引和主题页；旧知识库只新增或更新同一托管范围，绝不删除页面。
- `digest_topic_id` 是稳定更新身份；显示标题和首次确定的可读路径独立保存，标题改变不会自动改路径或破坏链接。
- 离线 Task 1 使用“已有标题、来源 title/H1、文件名”的顺序确定首发标题；默认 LLM 标题属于后续任务。
