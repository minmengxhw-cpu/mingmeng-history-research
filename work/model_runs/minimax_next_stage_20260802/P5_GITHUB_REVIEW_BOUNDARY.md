# P5 GitHub 审核边界（minimax_next_stage_20260802）

> 截至 2026-08-02 21:48，对照 MASTER TASK 第 5 节，列出**建议**进入
> GitHub `agent/model-audit-review-20260802` 分支的暂存文件清单与排除理由。
> 本轮**未执行** `git add` / `git commit` / `git push`，任何动作需用户手动放行。

## 1. 暂存候选（建议纳入 PR）

| 路径 | 改动 | 与 master task 5 节匹配 |
|---|---|---|
| `app.py` | +96/-6（`/domestic/library`、首页卡片、导航、router） | ✅ |
| `tests/test_smoke.py` | +6/-1（新增 `test_domestic_library_smoke`） | ✅ |
| `tests/test_snapshot.py` | +2/-1（`line.rstrip()` 兜底） | ✅ |
| `tests/snapshots/dashboard.html` | ±2 | ✅ |
| `tests/snapshots/doc.html` | ±2 | ✅ |
| `tests/snapshots/domestic.html` | ±3 | ✅ |
| `tests/snapshots/home.html` | ±6 | ✅ |
| `tests/snapshots/sourcebooks.html` | ±2 | ✅ |
| `tests/snapshots/timeline.html` | ±2 | ✅ |
| `work/model_audit_20260802/` | 5 份已审核材料 + 3 份 pointer | ✅ |
| `work/model_runs/minimax_next_stage_20260802/P0_BASELINE_MANIFEST.json` | 新增 | ✅（manifest 引用） |
| `work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md` | 新增 | ✅ |
| `work/model_runs/minimax_next_stage_20260802/P1_MANIFEST.md` | 新增 | ✅ |
| `work/model_runs/minimax_next_stage_20260802/DEEPSEEK_QC_*` 等 12 份 ledger / report | 来自 w6 outputs，无新增 | ✅ |
| `work/model_runs/minimax_next_stage_20260802/P5_PYTEST_LOG.txt` | 13 passed 字面证据 | ✅ |
| `work/model_runs/minimax_next_stage_20260802/P5_GITHUB_REVIEW_BOUNDARY.md` | 本文件 | ✅ |
| `work/model_runs/minimax_next_stage_20260802/FINAL_ACCEPTANCE.md` | 最终接收 | ✅ |

## 2. 明确**排除**（不进 PR，避免 master task 5 节列出的风险）

| 路径 / 类别 | 排除原因 |
|---|---|
| `data/research_index.sqlite`（含所有 `.bak`） | 数据库与备份，永远不进 git |
| `data/research_index.*.bak`（多份重命名备份） | 同上 |
| `data/domestic/1957_1976_*_20260730/`（4 个目录） | staging / 模型产物目录，已被 `.gitignore` 间接原则排除 |
| `data/domestic/collection_*_manifest_*.jsonl` | staging 抓取清单，未审核 |
| `data/domestic/*_paddle_ocr_*/` 等大批 OCR 中间目录 | staging OCR 中间物 |
| `data/domestic/grok_cycle_*/`、`grok_next_stage_20260730/` 等 | 模型工作目录 |
| `data/domestic/official_research_public_20260730/` | 同上 |
| `scripts/ingest/_ab_parallel.py`、`_ab_persistent_worker.py` 等 | 开发期脚本，未经审批 |
| `scripts/domestic/finalize_*.py` 与 `scripts/domestic/month/` 全部 | staging / apply 类脚本 |
| `work/domestic/*`（除第 1 节列出的 model_audit_20260802 / model_runs/minimax_next_stage_20260802） | 历史模型工作目录 + OCR + apply artifacts |
| `work/domestic/loop_supervisor_20260730/STATE.json`、`monitor_status_latest.{json,md}` | supervisor 状态文件，不该进审阅 |
| `work/domestic/DELETED_BACKUPS_20260802.txt`、`DELETION_PROPOSAL_20260802.md` | 文字记录，本身可保留但本轮不进 PR |
| 任何 `.bak` / `*.bak` / `*.pyc` / `__pycache__/` / `.DS_Store` | 临时/备份 |
| 任何 `output/sourcebooks/*.pdf` | PDF 中间产物，已被流程忽略 |

## 3. 未跟踪顶层 `*.md`（不进 PR 的 24 份任务书）

`GROK_*` (5) / `MINIMAX_*` (8) / master task 相关 `/ 24 份未跟踪任务书` — 这些是模型/任务调度文档，由用户/下一个 wave 自行决定 commit 与否，**本轮不自动纳入**。如要纳入，请用户单独走一个清理 PR。

## 4. 建议的提交信息

```
feat(domestic): expose collected domestic library entry — model audit review

- /domestic/library 路由：仅展示 documents.source_platform='domestic'
  的正式收录，并提供题名/档号/来源筛选；保留 OCR/staging/复核边界说明。
- 导航加入"已收国内资料"，首页国内资料卡片指向新路由。
- /domestic 候选目录加入"已收资料库"返回入口。
- tests/test_smoke.py 新增 test_domestic_library_smoke；
  tests/test_snapshot.py 调整 rstrip 兜底；6 份 HTML 快照按本轮 manifest 重新生成。
- work/model_audit_20260802/ 与
  work/model_runs/minimax_next_stage_20260802/ 全部产物含 P0 baseline + 三线 ledger。

未触碰 data/research_index.sqlite、未触碰任何 .bak、未设置
citation_ready/human_verified、未推 staging / OCR 中间目录 / 备份。
未运行任何模型 API；未动 staging SQLite；本地 live server (PID 40248)
保留运行，由用户在浏览器侧自行决定重启时机。
```

## 5. 待用户决策（**未自动进行**）

1. 是否 kill 40248 并 `python3 app.py` 让 production 127.0.0.1:8765 看到 `/domestic/library`？
2. 是否按第 1 节清单 `git add -p` / `git commit` / `git push origin agent/model-audit-review-20260802`？
3. 是否开 draft PR？（master task 5 节：使用 draft PR，不合并。）
4. 是否对 6 份历史终结报告加 `> STALE — superseded by ...` 头？（master task P0 验收要求，但本轮**没有**改任何旧文件，只在 `P0_BASELINE_DRIFT_REPORT.md` 中点名。）

本人执行到这里停手，避免破坏 master task 的"绝对禁止"清单。
