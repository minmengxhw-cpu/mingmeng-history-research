# 手动任务线 C：MiniMax P5/T69 证据工程

## 目标

在隔离目录推进 MiniMax V2 的 hard gaps、两条 isolated hold 和 T69 证据工程，产出可由人工审查的候选包、关系台账和 SQLite dry-run；不执行正式 apply。

## 优先对象

- 1941–1943 与 1948–1949 hard-gap pool
- `SSID-13679264#p0001`、`SSID-13679264#p0002` 两个 isolated hold
- T68 报告中仍为 `HOLD_UNSUPPORTED` 的关系
- OFFICIAL_RESEARCH 五个 blocker 的来源补强，但不把 likely verdict 当最终验收

## 输入

- `work/domestic/MINIMAX_V2_PHASE5_SPEC_20260801.md`
- `work/domestic/minimax_autonomous_research_20260730/T68_COMPREHENSIVE_FINAL_REPORT_20260801.md`
- `work/domestic/minimax_domestic_evidence_v2_month_20260729/08_sqlite_dryrun/`
- `work/domestic/minimax_official_research_20260730/06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.md`
- 当前正式库只读快照；当前 SHA 以 `MODEL_WORK_AUDIT_20260802.md` 为准

## 输出

写入隔离目录，例如 `work/model_runs/minimax_p5_t69_YYYYMMDD/`：

1. `HARD_GAP_POOL.jsonl`：来源、时间、对象、获取状态、证据级别、URL/本地路径和 HOLD 原因。
2. `ISOLATED_HOLD_DECISION.json`：两条 observer hold 的保留/拒绝理由，禁止 promotion。
3. `RELATION_LEDGER.jsonl`：实体关系、来源页、支持/反驳/未知、证据定位和置信级别。
4. `SQLITE_DRYRUN_MANIFEST.json`：只记录将来可能 apply 的新增/更新/回滚，不执行写入。
5. `SUMMARY.md`：目标数、实际数、缺口、失败、429/配额和下一步。

## 强制边界

- 不写 `data/research_index.sqlite`，不运行正式 apply，不使用 `CODEX_APPLY_TOKEN`。
- 不设置 `citation_ready=true`、`human_verified=true`，不把 OCR 草稿提取为正式 claims。
- 不制造候选、不把关系 HOLD 变成 provisional 以外的级别。
- 所有来源必须有 URL 或本地路径；没有原件只保留为 lead/HOLD。
- 报告中的数量必须从本轮 manifest 重新计算，不能沿用过期的 660/29、旧 SHA 或旧 QC 行数。

## 人工验收门

- hard-gap pool 与当前数据库候选逐条去重。
- 两条 isolated hold 仍保持隔离且没有 promote 记录。
- dry-run 可重放，包含 before/after、唯一键、回滚方式和当前 DB SHA。
- `PRAGMA integrity_check` 只对副本或隔离库执行；正式库保持只读。
