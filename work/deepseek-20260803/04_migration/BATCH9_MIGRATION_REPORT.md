# Batch 9 · 正式 SQLite 安全迁移报告

执行时间：2026-08-03 15:48

## 执行范围

1. 将 29 条 `needs_human_review` 审计结论写回 `domestic_candidates`；
2. 清理 15 条已确认的 `document_classifications` 外键孤儿；
3. 将 citation gate 284 条与正式库文档/页面 provenance 对账；
4. 全程先副本 dry-run，再备份、事务写入正式库。

## 安全记录

- 写入前 SHA-256：`bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e`
- 写入后 SHA-256：`e8df06ae53fbe8a4d997e57472d21e0d24fe913ffa26ff76d271de97899329ec`
- 备份：`data/research_index.sqlite.pre_deepseek_batch9_20260803T154801.bak`
- `PRAGMA integrity_check`：`ok`
- 分类孤儿：15 → 0
- 正式候选状态：accepted 688 / needs_human_review 1

## Citation 对账

- 严格门禁 PASS：284 candidates
- 正式库已关联 documents：170
- 可新晋升 provenance：0

未新增 citation-ready 页面不是失败：170 个已关联文档下的可核验页面已经处于 citation-ready，或剩余页面仍受 `needs_human_review/review_status` 门禁约束。本迁移拒绝按候选级结论盲目提升未经页面级验证的 provenance。

## 已知既存外键问题

写入前后均存在 5 条 `research_events → pages` 外键残留：event IDs 315—319。它们不属于本批分类孤儿范围，迁移没有新增外键违规。下一批单独核查其事件内容及页面归属后再决定重连或删除。

## 回滚

需要回滚时，停止应用后，以备份文件覆盖正式库，并核验备份 SHA-256 等于写入前 SHA。
