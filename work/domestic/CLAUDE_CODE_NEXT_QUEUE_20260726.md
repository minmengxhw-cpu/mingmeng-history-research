# Next Queue — 后续批次优先级（2026-07-26）

日期：2026-07-26
执行者：Claude Code（终端）
等待：Codex 验收通过 → 执行 P0 apply；PID 63188/64599 OCR 完成 → P1 apply；cheer 端补图 → P2 apply。

## P0（Codex 验收后立即可 apply，56 file_id / 3336 pages）

### P0-A ACCEPTED21 GO_SEARCH_DRAFT 子集（14 file_id）

| file_id | source_path | pages | conf | 备注 |
|---|---|---:|---:|---|
| P3-008 | NLC404-01J000514-10834_光明報_1946年1期.pdf | 16 | 0.9173 | 1946 |
| P3-004 | NLC404-01J000514-10431_光明報_1946年10期.pdf | 16 | 0.9016 | 1946 |
| P3-010 | NLC404-01J000514-72818_光明報_1947年12期.pdf | 16 | 0.8789 | 1947 |
| P3-002 | NLC404-01J000514-10460_光明報_1947年21期.pdf | 16 | 0.858 | 1947 |
| P3-005 | NLC404-00J001436-85453_民憲_第一卷第十二期.pdf | 32 | 0.9651 | 1944-1945 |
| P3-007 | NLC404-00J001436-85445_民憲_第一卷第四期.pdf | 32 | 0.9511 | 1944-1945 |
| P3-009 | NLC404-01J000332-6817_观察_1947年3卷11期.pdf | 32 | 0.946 | 1947 |
| P3-021 | LNU_PROFMKCHAN_INDEXLIST_14_光明報_1941.pdf | 16 | 0.9967 | 1941 |
| P3-011 | NLC416-01jh004281-12557_民主同盟文獻_1946.pdf | 256 | 0.9579 | sourcebook |
| P3-012 | NLC511-027032013012333-19131_民主同盟文獻_alternate_scan.pdf | 296 | 0.9767 | sourcebook |
| P3-013 | NLC511-027032016010761-42571_中国民主同盟言论集.pdf | 107 | 0.882 | sourcebook |
| P3-014 | 中国民主同盟临时全国代表大会宣言_公开转录.pdf | 789 | 0.9723 | sourcebook chunked 8 |
| P3-015 | 中国民主同盟历史文献_1941-1949_公开扫描.pdf | 622 | 0.9342 | sourcebook chunked 7 |
| P3-020 | GXMM_大公報_天津版_1947-11-06_第2版_民盟宣布解散_嵌图截取.png | 1 | 0.8633 | 1947 |

### P0-B ACCEPTED21 REVIEW_ORIGINAL 子集（7 file_id）

| file_id | source_path | pages | conf | 备注 |
|---|---|---:|---:|---|
| P3-016 | ROC1947-10-27國民政府公報2964.pdf | 17 | 0.7459 | 公報 |
| P3-017 | ROC1947-10-30國民政府公報2967.pdf | 17 | 0.7646 | 公報 |
| P3-018 | ROC1947-11-06國民政府公報2973.pdf | 9 | 0.723 | 公報 |
| P3-019 | ROC1947-11-07國民政府公報2974.pdf | 17 | 0.7276 | 公報 |
| P3-006 | NLC1080-00N000846-8631_新华日报_1941-10-10.pdf | 6 | 0.6853 | 新华日报 1941 |
| P3-001 | NLC1080-00N000846-8712_新华日报_1941-10-28.pdf | 2 | 0.6743 | 新华日报 1941 |
| P3-003 | NLC404-00J001436-85449_民憲_第一卷第八期.pdf | 32 | 0.8154 | 民憲 1944 |

### P0-C PENDING37 GO_SEARCH_DRAFT 子集（34 file_id）

按 PENDING37 manifest 中 conf ≥ 0.85 的 34 条（剔除 P3-GXMM-SH/TJ/N1080-7606），覆盖：
- 1941 新华日报 1 件
- 1946 光明報 9 件
- 1947 光明報 12 件 + 大剛報 1 件
- 1948—1949 光明報 4 件
- 民憲 第一卷第一/三/五/六/七/九/十/十一期 + 第二卷第一/二期 = 9 件（其中 1 件 P3-N1080-7606 为大剛報 0.7269 REVIEW_ORIGINAL，已剔除）

### P0-D P3-023（accepted_orphan，等 Codex 单独决定）

| file_id | source_path | pages | conf | 备注 |
|---|---|---:|---:|---|
| P3-023 | SSID-13679264_观察_第3卷第1-12期.pdf | 278 | 0.9301 | 1947 观察周刊第3卷1-12期；3 chunks |

建议：P0-D 单独决定，若 Codex 同意，可与 P0-A 一同 apply（合并为 57 file_id / 3614 pages）。

### P0 apply 命令（Codex 验收后）

```bash
cd "/Users/cheer/Documents/mm agent/mingmeng-history-research"
# 1. 备份
cp -p data/research_index.sqlite data/research_index.sqlite.20260726_phase5.pre.bak
# 2. 跑 before 检索回归（与 CLAUDE_PHASE6_SEARCH_REGRESSION_20260726.json 比对）
# 3. 升级（注意：此为示意，必须先 review Phase 4 决策并确认 P0 子集）
python3 scripts/ingest/upgrade_domestic_ocr_pages.py \
    --candidates work/domestic/CLAUDE_PHASE5_IMPORT_CANDIDATE_MANIFEST_20260726.jsonl \
    --batch accepted21,pending37 \
    --no-p3-023 \
    --dry-run  # 仍先 dry-run
# 4. 实际 apply（Codex 批准后才解除 --dry-run）
# 5. integrity + after 检索回归
sqlite3 data/research_index.sqlite "PRAGMA integrity_check;"
# 6. 比对 before/after
```

## P1（P3-113/114 后段 OCR 完成后追加，2 file_id / 280 pages）

等待 PID 63188 / 64599 完成后追加：

| file_id | source_path | pages_pending | conf_pending | output_dir |
|---|---|---:|---:|---|
| P3-113 | NLC511-012031312030001-21905_大公報_第113卷.pdf | 132 (p0101-0232) | TBD | work/domestic/ocr_collection_phase4/ |
| P3-114 | NLC511-012031312030001-21906_大公報_第114卷.pdf | 148 (p0101-0248) | TBD | work/domestic/ocr_collection_phase4/ |

**预估完成时间**：按 CPU 速率 ~1.1 min/页：
- 113 卷剩余 132 页 ≈ 145 min（其中 p0101-0200 已开跑，剩余 32 页 ≈ 35 min）
- 114 卷剩余 148 页 ≈ 163 min（其中 p0101-0200 已开跑，剩余 48 页 ≈ 53 min）

预计 ~1—2 小时内完成。

完成后操作：
1. 在 `work/domestic/CLAUDE_OCR_MANIFEST_P3-113_20260726.jsonl` 与 `CLAUDE_OCR_MANIFEST_P3-114_20260726.jsonl` 写新 manifest 入口；
2. 跑 Phase 4 质量复核，追加 decision 行；
3. 跑 Phase 5 dry-run 追加 2 个 candidate；
4. Codex 单独验收后 apply。

## P2（cheer 端补图后追加，2 file_id / 2 pages）

| file_id | source_path | 期望 conf | cheer action |
|---|---|---:|---|
| P3-GXMM-SH | NLC_大公報_上海版_1947-11-06_第2版_完整影像_试用数据库.pdf | ≥ 0.80 | 浏览器访问 NLC 试用数据库下载高清图，本地重 OCR |
| P3-GXMM-TJ | NLC_大公報_天津版_1947-11-06_第2版_完整影像_试用数据库.pdf | ≥ 0.80 | 同上 |

cheer 完成后操作：
1. cheer 把新文件放到 `data/domestic/press_scans/` 并更新 `collection_download_manifest_20260726.jsonl`（is_new_download=true，access_status=downloaded_locally_new）；
2. 跑 PaddleOCR 重做；
3. 写新 manifest 入口 + Phase 4 复核 + Phase 5 dry-run + Codex 单独验收。

## P3（1944—1945 时期新增资料，等 cheer 端补充）

当前 21+37 中 1944—1945 时期 chunks = 0（被 sourcebook P3-014/P3-015 覆盖）。Phase 3 priority 4 列出：
- 1944 民憲后续期号（如第一卷第二期以后）
- 1945 临时全国代表大会相关一手档案
- 1945 重庆谈判 / 政协相关报刊报道

具体 cheer-only 项：
- 1944 民憲 第一卷第二/三/五/六/七/九/十/十一期（已在 21+37 中）
- 1945 重庆谈判《新华日报》 /《大公报》报道（如需要补强）
- 1945 政治协商会议前导文件

## P4（页面级 citation_ready 提升）

apply 后，逐页/逐 chunk 提升 citation_ready=true：
1. 拉取 `ACCEPTANCE_OCR_LEDGER_20260726.csv` 的 page_id；
2. Codex 人工抽检 30% 页；
3. 对每页运行 `recommended_action` 决策（GO_SEARCH_DRAFT / REVIEW_ORIGINAL / REJECT_OCR）；
4. 通过抽检的页面更新 `pages.text` 加 `citation_ready=true` 标记（**这需要一个新的字段而非仅 boolean**）；
5. 不通过抽检的页面维持 `citation_ready=false` + `needs_human_review=true`。

本任务不进入 P4；下一轮 Codex 验收通过后单独发起。

## 移交文件

```
work/domestic/
├── CLAUDE_CODE_LONG_TASK_FINAL_20260726.md   # 最终报告
├── CLAUDE_CODE_LONG_TASK_FINAL_20260726.json # 结构化摘要
└── CLAUDE_CODE_NEXT_QUEUE_20260726.md        # 本文件
```