# Phase 5 — 入库 dry-run 报告（2026-07-26）

日期：2026-07-26
执行者：Claude Code（终端，长任务第二轮）
目的：在 Codex 验收前，把 21+37+P3-023 三批共 59 个 file_id 的入库计划写清楚；**不执行**任何 SQLite INSERT/UPDATE；所有 candidate 仍标 `citation_ready=false`、`needs_human_review=true`。

## 一、SQLite 现状（Phase 0 重跑结果）

| 指标 | 值 |
|---|---|
| integrity_check | ok |
| documents | 928 |
| pages | 1428 |
| page_fts | 1428 |

数据库未改动；21+37 入库计划建立在 baseline 之上。

## 二、批次边界

| 批次 | file_id 数 | planned docs | planned pages | planned page_fts | updated pages | citation_ready | needs_human_review |
|---|---:|---:|---:|---:|---:|---:|---:|
| accepted21 | 21 | 21 | 2178 | 2178 | 0 | 0/21 | 21/21 |
| pending37 | 37 | 37 | 942 | 942 | 0 | 0/37 | 37/37 |
| accepted_orphan_20260726（P3-023） | 1 | 0 | 0 | 0 | 0 | 0/1 | 1/1 |
| **合计** | **59** | **58** | **3120** | **3120** | **0** | **0/59** | **59/59** |

注：P3-023 在 dry-run 中计入 manifest 候选但不计入实际 apply；等 Codex 单独复核后决定并入 accepted21 还是另立 accepted22 batch。

## 三、跳过原因（skip_reasons）

| file_id | 决策 | skip_reason |
|---|---|---|
| P3-GXMM-SH | REVIEW_ORIGINAL（mean_conf=0.5019） | 置信度过低，需 cheer 提供高清重 OCR；保留 manifest 记录但不进实际 apply |
| P3-GXMM-TJ | REJECT_OCR（mean_conf=0.4575） | 拒绝入库，等 cheer 提供 NLC 试用数据库高清图后重 OCR |
| P3-023 | pending_codex_review | Phase 5 决策缺失（phase5_has_decision=false），单独 orphan batch |

**dry_run_status 分布**：
- 56 candidates `planned`（21 accepted21 + 35 pending37，因 2 件低置信度仍保留 manifest 但 dry-run 中标 planned_with_review）
- 1 candidate `pending_codex_review`（P3-023）
- 2 candidates `planned_with_review`（P3-GXMM-SH/REVIEW_ORIGINAL、P3-GXMM-TJ/REJECT_OCR）

实际写库仍是 0 documents / 0 pages，因为 citation_ready 全为 false。

## 四、备份与回滚命令

```bash
# 备份（apply 前必须执行）
cp -p data/research_index.sqlite \
      data/research_index.sqlite.20260726_phase5.pre.bak

# 回滚（apply 后任何完整性失败时执行）
cp -p data/research_index.sqlite.20260726_phase5.pre.bak \
      data/research_index.sqlite

# 回滚后完整性校验
sqlite3 data/research_index.sqlite "PRAGMA integrity_check;"
# 期望: ok
```

历史 `*.pre.bak` 备份已存在 22 个（20260722—20260723 系列），保留以备回溯。

## 五、apply 后立即回归的关键检索（≥30 条）

按 handoff 第 210 行要求，覆盖五个时期与代表性事件/人名/地名：

| 类别 | 关键词 |
|---|---|
| 1941 时期事件 | 成立宣言、对时局主张纲领、十大纲领、政治报告 |
| 1944—1945 改组 | 民盟改组、民盟一大、临时全国代表大会、民主宪政、五五宪草 |
| 1946 重组 | 政治协商会议、人民主权、国民大会、反对一党独裁 |
| 1947 危机 | 教授联署、民盟总部、非法化、恢复活动、十月三十一日 |
| 1948—1949 转型 | 三中全会、五一号召、新政协、多党合作、共同纲领 |
| 代表性人物 | 张澜、沈钧儒、黄炎培、张君劢、陈启天、李公朴、闻一多、罗隆基、章伯钧 |
| 地域 | 香港、上海、延安、南京、北平、沈阳 |

每个关键词至少做一次 `SELECT count(*) FROM page_fts WHERE page_fts MATCH '...'`；记录 before/after 数字。

## 六、本轮硬性禁止（已严格执行）

- `sqlite3 data/research_index.sqlite "INSERT/UPDATE ..."` — **未执行**
- `python3 scripts/ingest/upgrade_domestic_ocr_pages.py` 实 apply — **未执行**
- `git commit` — **未执行**
- `git push` — **未执行**

## 七、为什么没有正式 apply

1. **citation_ready 全 false**：21+37+P3-023 共 59 个 file_id 全部 `citation_ready=false`，按 handoff 第 232 行硬停止条件，任何 citation_ready=true 都必须 Codex 验收后才能解除。
2. **Phase 5 决策逐项复核未完成**：P3-023 的 `phase5_has_decision=false`；2 件低置信度（P3-GXMM-SH/TJ）需 cheer 端补 NLC 试用数据库高清图。
3. **batch 边界未最终敲定**：21+37 是上一轮混批 manifest 的拆分结果，需要 Codex 确认是否直接接受还是再次整合。
4. **113 卷/114 卷后段 OCR 仍在跑**：上一轮遗留 PIDs 63188/64599 仍未结束，跑完后才能追加 batch jsonl 与决策行。
5. **检索回归未跑**：≥30 条跨时期检索回归本轮作为待办，未在 dry-run 中实际执行；apply 前必须先跑完并比对数字。
6. **长任务交接原则**：本任务是 Codex 验收前的 dry-run；不允许跳过硬性条件。

## 八、产出文件

- `work/domestic/CLAUDE_PHASE5_IMPORT_CANDIDATE_MANIFEST_20260726.jsonl`（59 行候选）
- `work/domestic/CLAUDE_PHASE5_IMPORT_DRYRUN_20260726.json`（结构化 dry-run）
- `work/domestic/CLAUDE_PHASE5_IMPORT_DRYRUN_20260726.md`（本报告）

## 九、移交

- 等 Codex 验收后，按以下顺序操作：
  1. 跑 `cp -p` 备份；
  2. 跑 ≥30 条检索回归，记录 before；
  3. 跑 `upgrade_domestic_ocr_pages.py` apply；
  4. 跑 `PRAGMA integrity_check` + ≥30 条 after 检索；
  5. 比对 before/after，决定是否提交；
  6. Codex 确认后才允许 `git commit` 与 `git push`。
- P3-GXMM-SH/TJ 在 cheer 提供高清重 OCR 后单独追加一轮 batch；
- P3-023 单独 orphan 决策由 Codex 单独确认；
- 113/114 卷完成后追加批次。