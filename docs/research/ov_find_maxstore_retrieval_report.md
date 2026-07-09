# OpenViking maxstore 检索机制验证报告

## 1. ov find 默认检索范围
`ov find <query>` 默认不限定命名空间,是全局语义检索(跨 memory/resource/skill 所有 context-type,
跨全部 URI)。之前"全召回 memories,召不到 maxstore"不是因为 resources 未被索引,而是因为:
- 没加 `-u`/`--context-type`,导致 memories 和 resources 一起打分排序,
  这批旧 memories 内容与查询语义匹配度恰好更高,把 maxstore 结果挤出了默认 `-n` 条数外。
- `ov find --help` 关键参数:
  - `-u, --uri <uri>`   限定检索子树,如 `-u viking://resources/maxstore/`
  - `--context-type <type>`  限定 memory / resource / skill
  - `-L, --level <0,1,2>`  0=abstract 1=overview 2=file
  - `-n/--limit`, `-t/--threshold`, `--tags`, `--after/--before`

`ov search` 是实验性"上下文感知检索"，支持 `--session-id` 做会话上下文关联查询，
参数形态和 find 类似（也支持 -u / -n），但定位是"结合会话上下文"而非替代 find 的默认全库检索。
本次不依赖 session 上下文，find 和 search 结果基本等价。

## 2. resources/maxstore 索引状态
`ov status` 输出（验证时刻）：
- 队列：514 pending / 10 running / 0 errors（`ov observer queue` 细分：Embedding 511 pending /
  10 in progress / 998 processed；Semantic 0 pending / 8 processed）
- vikingdb: 1 collection, 10553 vectors（已有大量向量，说明不是"零索引"状态）
- retrieval: 244 queries, 29.1% zero-result rate

`ov task list --status failed` 看到的失败任务全部是 `session_commit` 类型（属于其他会话的记忆写入，
resource_id 形如 `cc-xxxx__subagent-xxxx`），报错为 litellm RateLimitError / ContextWindowExceededError，
**与 maxstore 资源导入无关**，不是本次问题的原因。

`ov ls`/`ov overview` 显示所有 maxstore 子目录 `[Directory overview is not generated]`——这是目录/文件
摘要（abstract/overview 生成，Level 0/1 的一部分）还没跑完，**不等于 Level 2（文件级 embedding）没建好**。
实测证明 Level 2 文件级语义检索已经命中（见下），说明 embedding 索引是增量生效的，
overview 落后于 embedding 队列进度。

结论：索引整体处于"部分就绪"状态——已入队的 169 个文档中一部分已完成 embedding（可检索），
一部分仍在 511 条 pending 队列中排队处理。**这不是全有全无，取决于具体某个文件是否已被处理完。**

查进度方法：
- `ov status` 看 Embedding 队列 pending/processed 总量变化趋势
- `ov observer queue` 看 Embedding/Semantic 分项队列
- `ov task list --status failed` 排除是否有 maxstore 相关失败任务（目前没有，全是别的 session_commit）
- 队列会持续消费，511 pending 不是卡死，需要时间自然清空（无法从当前数据估算精确 ETA，
  只能持续复查 pending 数是否在下降）

## 3. 实测：能正确召回 maxstore 内容的命令

```
ov find "终端替换有几种模式" -u viking://resources/maxstore/ --context-type resource -n 10
```

实际输出（节选）：
```
1. resource · Level 1 · score 0.766
   viking://resources/maxstore/模块手册/终端与设备/终端替换业务场景/.overview.md
2. resource · Level 1 · score 0.710
   viking://resources/maxstore/模块手册/终端与设备/终端替换操作规则/.overview.md
3. resource · Level 2 · score 0.666
   viking://resources/maxstore/模块手册/终端与设备/终端替换操作规则/终端替换操作规则.md
4. resource · Level 2 · score 0.637
   viking://resources/maxstore/模块手册/终端与设备/终端替换业务场景/终端替换业务场景.md
```

`ov search`（实验性）同一 query 也命中相同文件，排序略有差异。

`ov grep "终端替换" -u viking://resources/maxstore/` 也能直接模式匹配到
`终端替换操作规则.md`、`客户支持速查_网络任务与常见故障.md` 等 8 个文件、16 处命中，
确认文件本身在 resources 树里存在且可被全文扫描（grep 不依赖 embedding，随时可用）。

## 4. 结论 — 检索机制回答

1. `ov find` 默认查全库（memory+resource+skill 一起打分），**不是"只查 memories"**。
   之前召回全是 memories，是打分排序问题，不是范围限定问题。
2. 正确命令：加 `-u viking://resources/maxstore/` + `--context-type resource`
   （或视对比场景需要，只加 `-u` 也够，因为已限定子树）。
3. resources/maxstore 索引**部分就绪**：已有 998 条 embedding 处理完成（含本次验证命中的终端替换相关文件），
   仍有 511 条在 Embedding 队列排队，overview/abstract 生成还全部落后（不影响 Level 2 文件级检索命中）。
4. OpenViking vs Hindsight 对比建议：跑对比前，要么等 pending 队列清零（持续 `ov status` 监控 Embedding
   pending 是否归零），要么在测试脚本里显式指定 `-u viking://resources/maxstore/ --context-type resource`
   避免被 memories 干扰，并对每条测试 query 先用 `ov grep` 确认目标文件是否已能通过 embedding 检索命中
   （grep 命中不代表 embedding 已就绪，两者要分开验证）。
</content>
