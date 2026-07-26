## KnowledgeDigest 开放问题

权威副本：`.omc/plans/open-questions.md`（实施会话写入处）。本文件与之同步，供 `docs/plans/` 读者查阅。

### phase2.5-slim-and-llm — 2026-07-26

- [ ] `_validate_candidate` 逐字硬门（draft.py）与 LLM 改写冲突 — 若实测拒绝率高，放宽为语义校验还是保持逐字？决定 LLM 提炼是否真正生效，还是绕一圈仍是恒等输出
- [ ] LLM 环境变量命名 `KD_LLM_FORMAT/BASE_URL/API_KEY/MODEL` 是否与用户其他工具冲突 — 影响配置一致性
- [ ] 归档只增不删后磁盘持续增长 — 是否需要单独 `kd-gc` 子命令（本轮删了 90 天清理）
- [ ] 约 11 个纯形状检查测试（只 assert callable/exists/查 --help）保留还是换成行为测试 — 影响验收测试数字的含金量

### 历史（非本项目）

下方条目属于「记忆巩固/清理工具」设计，与 KnowledgeDigest 无关，仅保留以免误删历史记录：

1. [x] 是否要求物理删除环节——已拍板软删除满 90 天后再物理删除
2. [x] Consolidate 前须调研 OpenViking 批量更新 API
3. [x] 「N 天未召回自动降权」早期局限——用户接受
4. [ ] LLM 合并 prompt 反向校验阈值——留待实施时定
5. [ ] 第二期 sessions 归档清理——留待实施时定
