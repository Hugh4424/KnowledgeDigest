## phase2.5-slim-and-llm — 2026-07-26（仍待拍板）

- [ ] `_validate_candidate` 逐字硬门（draft.py）与 LLM 改写冲突 — 若实测拒绝率高，放宽为语义校验还是保持逐字？决定 LLM 提炼是否真正生效，还是绕一圈仍是恒等输出
- [ ] LLM 环境变量命名 `KD_LLM_FORMAT/BASE_URL/API_KEY/MODEL` 是否与用户其他工具冲突 — 影响配置一致性
- [ ] 归档只增不删后磁盘持续增长 — 是否需要单独 `kd-gc` 子命令（本轮删了 90 天清理）
- [ ] 约 11 个纯形状检查测试（只 assert callable/exists/查 --help）保留还是换成行为测试 — 影响验收测试数字的含金量

权威实施副本：`.omc/plans/open-questions.md`（与本文件同步）。
已完成阶段的设计/计划/报告见 `specs/archive/kd-phase0-2.5-plans/`。
