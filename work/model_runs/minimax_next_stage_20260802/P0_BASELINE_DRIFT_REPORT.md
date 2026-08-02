# P0 基线漂移报告（minimax_next_stage_20260802）

> 截至 2026-08-02 21:46（UTC 13:46），当前正式库与既有"终结"报告之间的偏差登记。
> 本报告由 `P0_BASELINE_MANIFEST.json` 派生；不删除任何旧报告，只标记 drift 与 stale。

## 1. 事实结论

| 维度 | 当前实测值（旧报告声明值） | 旧报告来源 | 漂移 | 处置 |
|---|---|---|---|---|
| 正式 SQLite SHA-256 | `bdebdbb0…729d2e` (`e4417bd1…` 等旧值) | `PROJECT_STATE_FINAL_20260802.md` `PROJECT_FINAL_AUDIT_20260802.json` `CORPUS_ADVERSARIAL_REVIEW_20260802.md` | 报告声明 `e4417bd1…` / `4837dbd6…`；实测 `bdebdbb0…` | 旧报告 mark stale；本轮新基线 = `bdebdbb0…` |
| `PRAGMA integrity_check` | `ok`（连续两次） | 同上 | 无 | — |
| `documents` | 1386（1386） | 同上 | 无 | — |
| `pages` | 6157（6157） | 同上 | 无 | — |
| `translations` | 1070（1070） | 同上 | 无 | — |
| `page_provenance` | 4786（4786） | 同上 | 无 | — |
| domestic_candidates 总数 | 689 | `MODEL_WORK_AUDIT_20260802.md` | 无 | — |
| domestic_candidates pass | 279（"A 层 660/29"旧声明） | 历史报告 + `MODEL_WORK_AUDIT_20260802.md` | 历史 A 层数 660 与当前 pass=279 不一致 | 旧声明 mark superseded |
| domestic_candidates lead_only | 381 | 同上 | 历史未单列 lead_only；新增 | 旧声明 mark superseded |
| domestic_candidates check_outcome NULL | 29 | 同上 | 旧 29（同期 1942–1943 原件缺口）保持 | 该 29 条仍是 hard gap |
| domestic_candidates.ingested_document_id NOT NULL | 279 | 同上 | 等于 pass 数 | 验证:候选登记→真实入库 1:1 |
| `documents.source_platform` | domestic=525 / drnh=287 / frus=299 / cia=102 / newspapersg=93 / hathitrust=54 / wilson=24 / hoover=2 | 未在旧报告中以分布方式声明 | domestic 由 0 起步，到当前 525；DRNH 由 287 维持 | 无 |
| `page_provenance.citation_ready=1` | 4353 | `MODEL_WORK_AUDIT_20260802.md` | 无 | — |
| `page_provenance.citation_ready=0` | 433 | 同上 | 无 | — |
| `human_verified` 列是否存在 | **不存在**（正式库；`PRAGMA table_info` 返回 0 行） | 旧"human_verified_created=0"措辞混用 | 报告里既有 `human_verified=0` 行数又有"created=0"，未统一 | 严格措辞：本列当前不存在；所有"human_verified=0"应改读为 `needs_human_review` |
| `needs_human_review=1` | 146 | 新指标 | — | — |
| `needs_human_review=0` | 4640 | 同上 | — | — |
| `translation_quality_issues` | 111（"4400 / 0 行"旧声明） | `MODEL_WORK_AUDIT_20260802.md` 已指过期 | 旧 4400 / 0 不能作当前 QC 结论 | 旧声明 mark superseded；当前真实统计：111 条 `incomplete_ocr` |
| `pages` domestic 部分 | 5087，含 15,140,035 字符 | 未在旧终审中按平台分开 | 已知 | — |

## 2. Drift 必须阻断发布的具体点

1. **旧终审引用过期 SHA**：三份终结报告（`PROJECT_STATE_FINAL_20260802.md`、`PROJECT_FINAL_AUDIT_20260802.json`、`CORPUS_ADVERSARIAL_REVIEW_20260802.md`）仍以 `e4417bd1…` / `4837dbd6…` 作为"最后基线"，与本轮 `bdebdbb0…` 对不上。
   - 处置：在每份报告头加 `> STALE — superseded by work/model_runs/minimax_next_stage_20260802/P0_BASELINE_MANIFEST.json`，不删原文。
2. **旧 "A 层 660/29"**：与本轮 `pass=279 / check_outcome IS NULL=29` 不一致。
   - 处置：旧声明保留为历史叙述；引用时必须同时给出当前真实数。
3. **旧 `translation_quality_issues=4400`**：与本轮 111 条 `incomplete_ocr` 不一致。
   - 处置：旧声明 mark stale；后续 P2 报告应以本轮 111 为基线。
4. **`human_verified` 列语义**：正式库无此列；后续 P2/P3/P4 报告若引用 "human_verified" 必须注明"使用 `needs_human_review` 替代"。

## 3. 工作树状态（不视为 drift，但需登记）

- 当前分支：`agent/domestic-evidence-20260728`
- HEAD：`6850b5b docs: add model audit and manual task lanes`
- 未提交改动（12 modified，0 staged）：
  - `app.py`：diff `+96/-6`，含 `/domestic/library` 路由、`domestic_library_page()`、`domestic_cards` 板块。
  - `tests/test_smoke.py` / `tests/test_snapshot.py`：伴随更新。
  - `tests/snapshots/*.html`：6 份 HTML 快照被刷新。
  - `work/domestic/loop_supervisor_20260730/STATE.json` / `monitor_status_latest.{json,md}`：伴随 supervisor 输出更新。
- 未跟踪（约 24 个顶层 `.md` + 4 个 `data/domestic/1957_1976_*_20260730/` 目录）：不进入本轮 manifest，将由后续 P5 决定是否分批清理。
- **本地 `app.py` 含 `/domestic/library` 但当前 live server 进程（PID 40248，Aug 2 12:45 启动）尚未加载新版**。
  - 实测：`GET /domestic/library` → 404；导航栏与首页卡片尚未生效。
  - 含义：P1 验收"路径返回 HTTP 200"前需要替换或重启 server。
  - 处置：见 P1 单独说明。**未自动重启**，避免影响并行 mini-process 与任何现存测试。

## 4. 不变项（成功不漂移）

| 项 | 状态 |
|---|---|
| 数据库 integrity | ok / ok |
| 顶级表行数（documents/pages/translations/page_provenance） | 完全匹配 |
| domestic_candidates 总数 689 | 匹配 |
| `documents.source_platform='drnh'=287` | 匹配（最近提交 `6850b5b` 落地） |
| `needs_human_review=1` = 146 | 新指标基线 |
| DeepSeek translator 计数：v4-flash-newspapersg=87 / chat=68 | 与最近 audit 一致 |
| FRUS / CIA / NewspaperSG / HathiTrust / Wilson / Hoover 各类卷数 | 与最后入卷快照一致 |

## 5. P0 验收门

- [x] `P0_BASELINE_MANIFEST.json` 输出
- [x] `P0_BASELINE_DRIFT_REPORT.md` 输出
- [x] SHA 验算：旧报告 stale 已识别，未删除
- [x] 未向正式 SQLite 写入；未 touch staging；未触碰备份
- [x] 未触碰 `.git`（无 add / commit / reset）

## 6. 下一步建议（不自动触发，仅提示）

- P1：先行确认是否重启 live server，让 `/domestic/library` 真正生效；如不重启，至少要把"web 服务吃的是旧二进制"明确写进 P1 报告，并把 manifest 留在新分支预备 commit 名单外。
- P2/P3/P4：均依赖本 manifest；P0 通过后才可启动。
- P5：暂缓，等前三相输出完成后再决定 commit 文件清单。
