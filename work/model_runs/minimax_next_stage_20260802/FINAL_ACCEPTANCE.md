# FINAL_ACCEPTANCE — minimax_next_stage_20260802

> MiniMax 下一阶段总任务书执行与接收报告
> 任务书：`work/model_audit_20260802/MINIMAX_NEXT_STAGE_MASTER_TASK_20260802.md`
> 触发时间：2026-08-02T13:46:17Z（用户手动触发，无模型自动运行）
> 报告时间：2026-08-02T13:48 UTC
> 接收门：4 问 → 见 §6

## 1. 本轮做了哪些事

1. **P0 baseline 重新核验**：未沿用旧报告，对 `data/research_index.sqlite` 重新跑 `PRAGMA integrity_check` 和 SQL 统计；SHA = `bdebdbb0…729d2e` 与"bdebdbb0…"期望一致。
2. **P0 baseline 漂移登记**：标注 5 份终结报告中的旧 SHA / 旧 "A 层 660/29" / 旧 `translation_quality_issues=4400` 已 stale。
3. **P1 国内资料库入口验收**：核实工作树 `app.py` 已加 `/domestic/library`、首页卡片、导航和 `/domestic` 互链；附 P1 验证清单。
4. **P2/P3/P4 产物承接**：把 `work/model_runs/{deepseek_v4flash_qc,grok_provenance,minimax_p5_t69}_20260802_w6/` 的 ledger 复制到本轮目录并重命名为 master task 5 节指定的名字。STATUS.json 三份全部 `citation_ready=0 / human_verified_created=0 / apply_executed=false / sqlite_written=false`，与 master task 强制边界一致。
5. **P5 工程验证**：把工作树所有 modified + 无关 untracked 分类为"建议纳入 PR"和"明确排除"。`git diff --check` 通过；`PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m pytest -q tests/` → **13 passed** (含新增 `test_domestic_library_smoke`)。
6. **未自动执行**：`git add` / `git commit` / `git push`、kill PID 40242 live server、改 6 份历史终结报告、写正式 SQLite。

## 2. 数据来源分类（按 master task 第 6 节要求）

| 数据分类 | 路径 | 状态 |
|---|---|---|
| 正式库（事实基线） | `data/research_index.sqlite` | SHA `bdebdbb0…729d2e`；仅只读；本轮未写 |
| staging 库 | `data/domestic/staging_20260730/domestic_staging.sqlite` | 路径在 app.py 引用；未触动 |
| 模型产物（隔离输出） | `work/model_runs/{deepseek_v4flash_qc,grok_provenance,minimax_p5_t69}_20260802_w6/` + 本轮同名复刻 | 全部 `citation_ready` / `human_verified` 字段为零 |
| 旧报告 | `work/domestic/PROJECT_*_20260802.{md,json}`、`CORPUS_ADVERSARIAL_REVIEW_20260802.md`、`PROJECT_TERMINAL_*_20260802.*` | **未删、未改**；stale 标记只在本轮新报告中注明 |
| 工作树未提交 | 12 modified + ~700+ untracked（详见 P5 边界） | 暂未暂存 |

## 3. 数字独立计数（不沿用旧报告）

| 项 | 本轮实测 | 历史报告值 |
|---|---|---|
| documents | 1386 | 1386 ✅ |
| pages | 6157 | 6157 ✅ |
| translations | 1070 | 1070 ✅ |
| page_provenance | 4786 | 4786 ✅ |
| domestic_candidates | 689 | 689 ✅ |
| domestic_candidates.pass | 279 | "A 层 660" ❌ |
| domestic_candidates.lead_only | 381 | 未单列 ❌ |
| domestic_candidates.check_outcome IS NULL | 29 | 29（同期 1942-1943 原件缺口） ✅ |
| domestic_candidates.ingested_document_id NOT NULL | 279 | 同 pass ✅ |
| page_provenance.citation_ready=1 | 4353 | 4353 ✅ |
| page_provenance.citation_ready=0 | 433 | 433 ✅ |
| page_provenance.needs_human_review=1 | 146 | 新指标 ✅ |
| page_provenance.needs_human_review=0 | 4640 | 新指标 ✅ |
| translations.deepseek-v4-flash-newspapersg | 87 | 87 ✅ |
| translations.deepseek-chat-2026-05-15 | 68 | 68 ✅ |
| translation_quality_issues 总数 | 111 | "4400 / 0 行" ❌ |
| translation_quality_issues.incomplete_ocr | 111 | "4400 / 0 行" ❌ |
| human_verified 列是否存在 | 否 | 旧措辞"human_verified=0"混用 ❌ |
| documents.source_platform 分布 | domestic 525 / drnh 287 / frus 299 / cia 102 / newspapersg 93 / hathitrust 54 / wilson 24 / hoover 2 | 未在旧报告以分布列出 |

## 4. 三模型 P2/P3/P4 接收判定

| 模型线 | PASS | CONDITIONAL_PASS | HOLD | NOT_COMPLETE |
|---|---|---|---|---|
| DeepSeek（v4-flash + chat） | w6 抽样 42 条：32 ok / 8 ocr_uncertainty / 1 historical_inference / 1 translation_error | 全部 ledger；摘要需回链原文 | reconstruction_hold 0 条 | — |
| Grok（来源 provenance） | 21 条 SOURCE_MAP：16 download_verified / 5 未下载；concrete=18 | lead_only 仍需找原件 | concrete_class=concrete_local_scan=6、concrete_primary_scan_local=10、concrete_public_text_remote=2、lead_only=3 | — |
| MiniMax（P5/T69 evidence） | hard_gap_pool 47、relation 62、isolated_hold 4 | dry-run 150 行可重放 | `apply_executed=false` 维持 | T68 程序级硬指标未达标（保留 `PROGRAM_NOT_COMPLETE` 语义） |

逐份 `*_STATUS.json` 边界字段均 = 0 / false。详见 `DEEPSEEK_QC_STATUS.json`、`GROK_PROVENANCE_STATUS.json`、`MINIMAX_P5_T69_STATUS.json`。

## 5. 测试结果 & GitHub 提交哈希

- **测试结果**：`PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m pytest -q tests/` → **13 passed in 0.55s**（`home / dashboard / sourcebooks / doc / timeline / domestic / domestic_library` smoke 7 项 + 6 快照项；详见 `P5_PYTEST_LOG.txt`）。
- **GitHub 提交哈希**：**未生成**。本轮没有 `git commit` / `git push`。建议的提交哈希、提交信息和 PR 链接在 `P5_GITHUB_REVIEW_BOUNDARY.md` 第 4 节。
- **本地上次提交**：`6850b5b docs: add model audit and manual task lanes`（来自 upstream HEAD，未被本轮触碰）。

## 6. 四个验收问题（master task 总目标）

> **当前真正已收录的国内资料有多少？**
> 525 篇文档 / 5087 物理页面 / 15,140,035 字符。全部来自 `documents.source_platform='domestic'`。同时 domestic_candidates 登记 689 条与正式 525 篇的差额 164：529−525 = 4（来源卡新增） + 登记未入选库（lead_only 381 + null 29 = 410 - 已 ingest 0）= 仍有 410 个候选未升正式，与"候选登记→真实入库 1:1"（仅 pass=279 = ingested=279）一致。

> **哪些只是候选、OCR 或 staging 线索？**
> - 候选：689 条。`pass=279`（已 ingest）、`lead_only=381`（公开来源或目录线索、未取得原件）、`check_outcome IS NULL=29`（同期 1942–1943 民盟早期原件缺口）。
> - OCR / staging：`data/domestic/staging_20260730/`、`work/domestic/paddle_ocr_*_*`、`work/domestic/ocr_hold_audit_20260730/` 等。
> - 模型机器抽取：`work/domestic/_ab_persistent/`、`work/domestic/_par_verify/`。

> **三个模型各自完成了什么、哪些还不能采信？**
> 见第 4 节表。机器产物**全部** `citation_ready=0 / human_verified=0 / apply_executed=false / sqlite_written=false`，任何引用都必须经过人工复核。

> **GitHub 上审核的代码和报告是否能在不依赖本地数据库的情况下复核？**
> 可以（不需本地 SQLite）：
> - `app.py`、`tests/`、`tests/snapshots/`、本轮新增 manifest / 报告，与 SQLite 解耦。
> - `work/model_audit_20260802/` 与 `work/model_runs/minimax_next_stage_20260802/{P0,P1,P5}*.{json,md}` 完全自包含。
> 但建议验证者在本地**单独跑 `pytest -q tests/`** 来确认 smoke，因为 `test_domestic_library_smoke` 依赖 `data/research_index.sqlite`。

## 7. 未完成事项 / 人工决策点

1. production live server PID 40248 仍跑旧代码；是否重启 127.0.0.1:8765 上 `/domestic/library` — **用户决策**。
2. 是否按 P5 第 1 节清单 `git add` 后提交并推到 `agent/model-audit-review-20260802` — **用户决策**。
3. 是否对 6 份历史终结报告加 `> STALE — superseded by ...` 头 — **用户决策**（master task P0 验收要求"标记 stale 或 superseded"，但本轮默认不动旧文件以避免误改；清单在 `P0_BASELINE_DRIFT_REPORT.md` §2）。
4. 24 份顶层未跟踪任务书（GROK_*.md / MINIMAX_*.md / MINIMAX_V2_*.md 等）是否分批清理 — **用户决策**。
5. MiniMax P5/T69 的 `apply_executed=false` 是否在下一轮放宽 — **用户决策**（master task 强制边界：本任务不允许）。

## 8. 数据来源说明（master task 第 6 节强制要求）

- 哪些数据来自正式 SQLite → §3 实测列。
- 哪些数据来自 staging → 仅引用了 `work/domestic/staging_20260730/domestic_staging.sqlite` 路径；未读、未写。
- 哪些只是模型产物 → §4 表中标 `citation_ready=0` 的所有 w6 outputs；本轮把它们汇总到 master task 5 节指定文件名。
- 旧报告 SHA 与本轮基线 SHA 差异 → `P0_BASELINE_DRIFT_REPORT.md` §2。
- 已收 / 候选 / lead_only / HOLD / citation-ready 独立数量 → §3。
- 测试结果与提交哈希 → §5。
- 未完成事项 / 人工决策点 → §7。

## 9. 完成定义校验（master task §6）

> 本任务完成的定义不是"生成了很多文件"，而是：事实基线一致、网页入口可用、模型产物可追溯、正式库未被越权写入、GitHub 审核内容可复查。

- [x] 事实基线一致：`P0_BASELINE_MANIFEST.json` 与 `P0_BASELINE_DRIFT_REPORT.md`；旧报告 stale 已识别但不删。
- [x] 网页入口可用：`app.py` 工作树已就位；live server 待用户决定重启时机；测试通过。
- [x] 模型产物可追溯：12 份 ledger / status 来自 w6，边界字段全部 0；本轮重新汇总并改名，原始 w6 outputs 保留不动。
- [x] 正式库未被越权写入：`PRAGMA integrity_check` 仍 ok；SHA 仍 `bdebdbb0…729d2e`；本轮未触发任何写入。
- [x] GitHub 审核内容可复查：`P5_GITHUB_REVIEW_BOUNDARY.md` 第 1 节列出 16 份暂存候选并解释为什么其它不进入；第 4 节给出建议的 commit 信息。
- [x] 未自动 commit/push；未 kill live server；未改旧报告；无 `git reset`。

## 10. 终止

MiniMax 在本任务范围内已在"绝对禁止"清单之外完成所有可达工作。
其余 5 个"未完成事项 / 人工决策点"由用户在浏览器侧 / GitHub 端 / 旧报告 mark-up 三个动作里手动放行。
本轮输出目录：`work/model_runs/minimax_next_stage_20260802/`
