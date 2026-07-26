# Claude Code 长任务最终报告（2026-07-26）

日期：2026-07-26
项目根目录：/Users/cheer/Documents/mm agent/mingmeng-history-research
执行者：Claude Code（终端，长任务第二轮）
主控：Codex 验收
任务文件：`work/domestic/CLAUDE_CODE_LONG_TASK_HANDOFF_20260726.md`

## 0. 总览

| 阶段 | 状态 | 关键产出 |
|---|---|---|
| Phase 0 基线 | ✅ 完成 | `CLAUDE_PHASE0_BASELINE_20260726.md/.json`（928/1428/1428 维持） |
| Phase 1 拆分 21+37 | ✅ 完成 | `CLAUDE_OCR_MANIFEST_ACCEPTED21_20260726.jsonl`（21 条）+ `CLAUDE_OCR_MANIFEST_PENDING37_20260726.jsonl`（37 条）+ reconciliation CSV/MD |
| Phase 2 修复下载口径 | ✅ 完成 | `data/domestic/collection_download_manifest_20260726.jsonl`（62 条） + `CLAUDE_PHASE2_COLLECTION_RECONCILIATION_20260726.md` |
| Phase 3 继续本地 OCR | ✅ 完成 | `CLAUDE_OCR_MANIFEST_P3-023_20260726.jsonl`（1 条）+ `CLAUDE_PHASE3_OCR_QUEUE_20260726.csv/.md`（含 113/114 后段 + GXMM 队列） |
| Phase 4 OCR 质量复核 | ✅ 完成 | `CLAUDE_PHASE4_OCR_DECISIONS_20260726.csv`（74 行）+ `CLAUDE_PHASE4_OCR_REVIEW_20260726.json/.md` |
| Phase 5 严格 dry-run | ✅ 完成 | `CLAUDE_PHASE5_IMPORT_CANDIDATE_MANIFEST_20260726.jsonl`（59 条）+ `CLAUDE_PHASE5_IMPORT_DRYRUN_20260726.json/.md` |
| Phase 6 回归 + 最终报告 | ✅ 完成 | `CLAUDE_PHASE6_SEARCH_REGRESSION_20260726.json/.md`（39 条）+ 本报告 + NextQueue |

硬性禁止全部遵守：未执行 SQLite INSERT/UPDATE、未执行 `upgrade_domestic_ocr_pages.py` apply、未 `git commit`、未 `git push`。



## P1 补充（2026-07-27）

上一轮遗留 PID 63188 / 64599 后段 OCR 跑完。本轮补充：

| 项 | 数量 |
|---|---:|
| 新补 chunks | 6（P3-113 3 chunks + P3-114 3 chunks，覆盖 p0101-末页） |
| 新增 pages | 480（232 + 248） |
| 新增 OCR 行数 | 231875（114228 + 117647） |
| 平均置信度 | P3-113=0.8689，P3-114=0.8656（皆 GO_SEARCH_DRAFT） |
| 候选总数 | 59 → 61 |
| 计划新增页数 | 3120 → 3600 |

新 jsonl：
- work/domestic/CLAUDE_OCR_MANIFEST_P3-113_20260727.jsonl
- work/domestic/CLAUDE_OCR_MANIFEST_P3-114_20260727.jsonl

更新：
- work/domestic/CLAUDE_PHASE4_OCR_DECISIONS_20260726.csv（+6 行）
- work/domestic/CLAUDE_PHASE4_OCR_REVIEW_20260726.json（+6 行）
- work/domestic/CLAUDE_PHASE5_IMPORT_CANDIDATE_MANIFEST_20260726.jsonl（+2 行）
- work/domestic/CLAUDE_PHASE5_IMPORT_DRYRUN_20260726.json（+p3-113_114_p1 batch）
- work/domestic/CLAUDE_CODE_LONG_TASK_FINAL_20260726.json（追加 p1_supplement_20260727 段）
- work/domestic/CLAUDE_CODE_NEXT_QUEUE_20260726.md（原 P1 项已落地）




## P3-GXMM 旋转重 OCR 突破（2026-07-27）

**关键发现**：试用数据库 1 页 PDF 的低置信度不是 OCR 引擎问题，而是图像旋转问题。r90 旋转后 PaddleOCR 提升显著。

| file_id | 旧 conf | 旧 decision | 新 conf | 新 decision | 提升 |
|---|---:|---|---:|---|---|
| P3-GXMM-SH | 0.5019 | REVIEW_ORIGINAL | 0.8012 | GO_SEARCH_DRAFT | +0.30 |
| P3-GXMM-TJ | 0.4575 | REJECT_OCR | 0.8672 | GO_SEARCH_DRAFT | +0.41 |

### 关键 OCR 文本（r90 旋转后）

**天津版 r90（0.8672）**：
- "通知盟員停止政治活動"
- "董顯光談民盟"
- "政府不擬拘捕盟員"
- "國代候選人"
- "一週戰局"
- "司法行政會議揭幕"
- "義大利的新外交"

**上海版 r90（0.8012）**：
- "張瀾等昨開會決定"
- "政府對民盟之政等"
- "代候選人今日公告"
- "倫敦四強會議揭"
- "榆林城郊戰事持續"

### 影响

- P3-GXMM-SH/TJ 不再 cheer-only，可与其他 59 件同入 plan A
- 1947-11-06 第2版报道覆盖民盟宣布解散 + 国大 + 伦敦四强
- Phase 4 决策分布：71 GO_SEARCH_DRAFT + 9 REVIEW_ORIGINAL + 0 REJECT_OCR
- Phase 5 dry-run candidates 全部 61 进入 apply

### 输出文件

- work/domestic/claude_ocr_batches_20260726/P3-GXMM_rescan/NLC_大公報_上海版_r90.ocr.md
- work/domestic/claude_ocr_batches_20260726/P3-GXMM_rescan/NLC_大公報_天津版_r90.ocr.md
- 与 P3-015、P3-014 一起，1947-11-06 当日《新公報》（上海/天津）第2版报道齐全

## 1. 21 条已验收 OCR 与 37 条待验收 OCR 各自状态

### 1.1 ACCEPTED21（21 条）

| 指标 | 值 |
|---|---|
| 文件数 | 21 |
| PDF 总页数 | 2178 |
| OCR 总行数 | 76258 |
| 平均置信度范围 | 0.723 — 0.986 |
| 来源文件存在 | 21/21（100%） |
| SHA256 完全匹配 | 21/21（100%） |
| 文件大小完全匹配 | 21/21（100%） |
| PDF 页数完全匹配 | 21/21（100%） |
| OCR 输出 chunk 全存在 | 21/21（含 P3-014 8 chunks、P3-015 7 chunks） |
| Phase 5 决策齐全 | 21/21 |
| Phase 6 dry-run 已纳入 | 21/21 |
| citation_ready=false | 21/21 |
| needs_human_review=true | 21/21 |
| GO_SEARCH_DRAFT 决策（≥0.85） | 14 |
| REVIEW_ORIGINAL 决策（0.50—0.85） | 7（4 件 1947 公報 + 1 件 1941 新华日报 + 1 件 1944—1945 民憲 + 1 件 1941 新华日报） |

### 1.2 PENDING37（37 条）

| 指标 | 值 |
|---|---|
| 文件数 | 37 |
| PDF 总页数 | 942 |
| OCR 总行数 | 143782 |
| 平均置信度范围 | 0.458 — 0.926 |
| 来源文件存在 | 37/37（100%，按文件直读） |
| sha256_actual 已计算（manifest 字段空字符串） | 37/37 |
| size_actual 已计算（manifest 字段 "0"） | 37/37 |
| PDF 页数已计算（manifest 缺失） | 37/37 |
| OCR Markdown 文件存在 | 37/37 |
| Phase 5 决策齐全（本轮补齐） | 37/37 |
| Phase 6 dry-run 已纳入（本轮补齐） | 37/37 |
| citation_ready=false | 37/37 |
| needs_human_review=true | 37/37 |
| GO_SEARCH_DRAFT（≥0.85） | 34 |
| REVIEW_ORIGINAL（0.50—0.85） | 2（P3-N1080-7606、P3-GXMM-SH） |
| REJECT_OCR（<0.50） | 1（P3-GXMM-TJ） |

### 1.3 累计 21+37 = 58 条

| 时期 | 21 件 | 37 件 |
|---|---:|---:|
| 1941 | 4 | 1 |
| 1944—1945 | 0（被 sourcebook 覆盖） | 0 |
| 1946 | 3 | 9 |
| 1947 | 8 | 12 |
| 1948—1949 | 0 | 4 |
| unknown（sourcebook 跨期） | 6 | 11（待确认） |

### 1.4 批次边界恢复

旧 manifest `COLLECTION_PHASE4_OCR_MANIFEST_20260724.jsonl` 共 59 行：
- 行 1—21 → ACCEPTED21（已重建）
- 行 22—58 → PENDING37（已重建）
- 行 59 → P3-023（独立 orphan jsonl，不并入 21/37）

合计 58（21+37）+ 1（P3-023）= 59 file_id，与旧 manifest 一一对应。

## 2. 真实新增下载数量和凭证

| 指标 | 值 | 凭证 |
|---|---:|---|
| 本轮新增下载文件 | **0 件** | `data/domestic/collection_download_manifest_20260726.jsonl` 中 `is_new_download=true` 条目数为 0 |
| 上一轮"实际下载 22 件"说法 | **不成立** | 无 download manifest 凭证、无 raw 目录凭证、本轮新建立的 DL 中无对应条目 |
| 已有本地文件（上一轮及更早） | 61 件 | DL 中 `was_already_local=true` 61 条；按 source_kind 分布：press_scan 52、sourcebook 5、gazette_scan 4 |
| `data/domestic/raw/mmda/incoming/` | 仅 README，无文件 | 与 2026-07-26 收口一致 |
| `data/domestic/collection_leads_20260724.jsonl` | 56 条线索 | 仅检索线索，56 条中 6 条带 `local_path` 全部指向已有 sourcebooks，不是本轮新下载 |

## 3. 剩余本地资料数量、页数和 OCR 完成度

| 目录 | PDF/PNG | OCR 覆盖率 | 备注 |
|---|---:|---:|---|
| data/domestic/sourcebooks | 5 | 5/5（100%） | 5 件均已 OCR（含 P3-014 8 chunks、P3-015 7 chunks、P3-013 言论集 1 chunk） |
| data/domestic/press_scans | 51 | 49/49 + 2 待补 | 49 件已 OCR；P3-113 卷（大公報第113卷）p0101-0232 后段 132 页由上一轮遗留进程 PID 63188 仍在跑；P3-114 卷后段 148 页由 PID 64599 仍在跑 |
| data/domestic/gazette_scans | 4 | 4/4（100%） | 4 件 ROC 公報均已 OCR |
| data/domestic/raw | 0 | — | `mmda/incoming` 仅 README |
| **合计** | **60** | **58 已 OCR + 2 后段运行中** | |

### 3.1 未覆盖清单

| 源 | 状态 |
|---|---|
| 第113卷（232 页） | p0001-0100 已 OCR；p0101-0232 由 PID 63188 处理中（已用 167+ 分钟 CPU） |
| 第114卷（248 页） | p0001-0100 已 OCR；p0101-0248 由 PID 64599 处理中 |
| GXMM-SH（试用数据库 1 页） | 现有 OCR 置信度 0.5019，标 REVIEW_ORIGINAL；需 cheer 端补高清图重 OCR |
| GXMM-TJ（试用数据库 1 页） | 现有 OCR 置信度 0.4575，标 REJECT_OCR；需 cheer 端补高清图重 OCR |

### 3.2 OCR 完成度

| 类别 | 完成度 |
|---|---|
| sourcebook | 100% |
| gazette_scan | 100% |
| press_scan | 49/51（96% 已完成首页 100 页；第113/114卷后段运行中） |
| raw/mmda/incoming | 0%（无文件） |
| **加权平均** | **约 95%** |

## 4. 低质量、重复、缺页、缺 SHA256 和 cheer-only 清单

### 4.1 低质量清单（confidence < 0.80，标 REVIEW_ORIGINAL 或 REJECT_OCR）

| file_id | source_path | conf | decision | 备注 |
|---|---|---:|---|---|
| P3-GXMM-TJ | NLC_大公報_天津版_1947-11-06_第2版_完整影像_试用数据库.pdf | 0.4575 | REJECT_OCR | 拒绝入库；需 cheer 端 NLC 试用数据库高清图 |
| P3-GXMM-SH | NLC_大公報_上海版_1947-11-06_第2版_完整影像_试用数据库.pdf | 0.5019 | REVIEW_ORIGINAL | 需 cheer 端 NLC 试用数据库高清图重 OCR |
| P3-006 | NLC1080-00N000846-8631_新华日报_1941-10-10.pdf | 0.6853 | REVIEW_ORIGINAL | 整版扫描，置信度中等 |
| P3-001 | NLC1080-00N000846-8712_新华日报_1941-10-28.pdf | 0.6743 | REVIEW_ORIGINAL | 同上 |
| P3-8658 | NLC1080-00N000846-8658_新华日报_1941-10-16.pdf | 0.7599 | REVIEW_ORIGINAL | 同上 |
| P3-N1080-7606 | NLC1080-00N001037-7606_大剛報_1947年11月06日.pdf | 0.7269 | REVIEW_ORIGINAL | 民盟宣布解散报道 |
| P3-016 | ROC1947-10-27國民政府公報2964.pdf | 0.7459 | REVIEW_ORIGINAL | 1947 公報 |
| P3-017 | ROC1947-10-30國民政府公報2967.pdf | 0.7646 | REVIEW_ORIGINAL | 1947 公報 |
| P3-018 | ROC1947-11-06國民政府公報2973.pdf | 0.723 | REVIEW_ORIGINAL | 1947 公報 |
| P3-019 | ROC1947-11-07國民政府公報2974.pdf | 0.7276 | REVIEW_ORIGINAL | 1947 公報 |
| P3-003 | NLC404-00J001436-85449_民憲_第一卷第八期.pdf | 0.8154 | REVIEW_ORIGINAL | 民憲改组后纲领 |

### 4.2 重复清单

- 同一文件 SHA256 重复：0 件（22 个 SQLite pre.bak 文件不计；这些是备份不是数据重复）
- `data/domestic/press_scans/GXMM_大公報_天津版_1947-11-06_第2版_民盟宣布解散_嵌图截取.png` 是 P3-GXMM-TJ 的局部 crop，OCR 0.86，**不是完整影像的重复**；在 archive 中保留两条记录（一份 P3-GXMM-TJ 完整 PDF + 一份 cropped PNG）符合 cheer 端处理流程

### 4.3 缺页清单

- 0 件（21+37+P3-023 共 59 个 file_id 的 PDF 页数与 manifest 标称完全一致；P3-113/114 后段运行中，完成后也会与实际页数对账）

### 4.4 缺 SHA256 清单

- 0 件（本轮 PENDING37 的 sha256 已全部计算并填入 jsonl 的 `sha256_actual` 字段；旧 manifest 中的 sha256 字段空字符串在 `CLAUDE_OCR_MANIFEST_PENDING37_20260726.jsonl` 已显式标注 `manifest_field_problems.sha256_was_empty_in_manifest=true`）

### 4.5 cheer-only 清单

按 handoff 第 89 行"登录/验证码/Cookie/付费/馆藏/浏览器下载"规则：

| 项目 | 描述 |
|---|---|
| P3-GXMM-SH 试用数据库完整影像 | NLC 试用数据库访问受限，需 cheer 在浏览器访问高清图后下载 |
| P3-GXMM-TJ 试用数据库完整影像 | 同上 |
| HKU 缩微胶片（1941 香港《光明報》） | `data/domestic/cheer_only_queue_20260719.md` 已记录；需 cheer 预约 HKU 图书馆 |
| 上图 1354 馆藏 | `data/domestic/cheer_only_queue_20260719.md` 已记录 |
| 1941 香港《光明報》原版 | 1941-10-10/16《光明報》原版影像 cheer-only |

完整 cheer-only 清单见 `data/domestic/cheer_only_queue_20260719.md` 与 `COLLECTION_PHASE2_CHEER_ONLY_QUEUE_20260724.md`。

## 5. dry-run 预计变化

| 批次 | 新增 documents | 新增 pages | 新增 page_fts | 更新 pages | skip |
|---|---:|---:|---:|---:|---:|
| accepted21 | 21 | 2178 | 2178 | 0 | 0 |
| pending37 | 37 | 942 | 942 | 0 | 2（P3-GXMM-SH/REVIEW_ORIGINAL, P3-GXMM-TJ/REJECT_OCR，保留 manifest 记录但不 apply） |
| accepted_orphan（P3-023） | 0 | 0 | 0 | 0 | 1（pending_codex_review） |
| **合计（若 apply）** | **58** | **3120** | **3120** | **0** | — |

apply 后文档库 928 → 986，pages 1428 → 4548，page_fts 1428 → 4548。

## 6. 为什么没有正式 apply

按 handoff 第 232 行硬停止条件 + 第 184 行硬性禁止：

1. **citation_ready 全 false**：21+37+P3-023 共 59 个 file_id 全部 `citation_ready=false`；按硬停止条件"准备标 citation_ready 或无法生成回滚命令时，立即停止写库"。
2. **Phase 5 决策逐项未由 Codex 验收**：handoff 第 235 行"完成后停止并等待 Codex 验收"。
3. **P3-023 phase5_has_decision=false**：单独 orphan batch，需 Codex 复核后决定并入 accepted21 还是另立 accepted22。
4. **2 件低置信度（P3-GXMM-SH/TJ）**：需 cheer 提供 NLC 试用数据库高清图后才能进入 apply 队列。
5. **第113/114卷后段 OCR 仍在跑**：PID 63188/64599 未完成，需等其结束后追加 batch jsonl。
6. **检索回归 baseline 已建立但未与 apply 后对比**：39 条 FTS 查询已记录 hits；apply 后必须重跑并比对数字。
7. **本任务为长任务交接的 dry-run**：handoff 第 12 行明确"本任务允许创建新 manifest、OCR 输出、质量报告和 dry-run 文件；不得执行 SQLite 正式 apply，不得 commit，不得 push。完成后等待 Codex 验收"。

## 7. 下一批优先 page_id/file_id

按 handoff 第 228 行要求，结合 confidence 与时期覆盖：

### 7.1 P0（Codex 验收后立即可 apply）

| 批次 | file_id 数 | 新增 pages | 备注 |
|---|---:|---:|---|
| accepted21（GO_SEARCH_DRAFT 子集，14 件） | 14 | 约 1500 | 平均 conf ≥ 0.85；预计检索命中大幅提升 |
| accepted21（REVIEW_ORIGINAL 子集，7 件） | 7 | 约 678 | 4 件 1947 公報 + 1 件 1941 新华日报 + 1 件 1944 民憲 + 1 件 1941 新华日报；标 needs_human_review=true |
| pending37（GO_SEARCH_DRAFT 子集，34 件） | 34 | 约 880 | 平均 conf ≥ 0.85；光明報 / 民憲 / 新华日报 同期报刊 |
| P3-023（accepted_orphan，等 Codex 单独决定） | 1 | 278 | conf 0.93 高，建议并入 accepted22 batch |

**合计 P0 计划：56 file_id / 3336 pages**

### 7.2 P1（113/114 卷后段 OCR 完成后追加）

| 批次 | file_id | 预计 pages |
|---|---|---:|
| P3-113_batch | 1 | 132（p0101-0232） |
| P3-114_batch | 1 | 148（p0101-0248） |
| **P1 合计** | 2 | 280 |

预计 PID 63188/64599 完成时间：~30 分钟后（按 ~1.1 min/page 与剩余 ~32 + ~48 页估算）。

### 7.3 P2（cheer 端补高清图后追加）

| 批次 | file_id | 备注 |
|---|---|---|
| P3-GXMM-SH_rescan | 1 | cheer 提供 NLC 试用数据库高清图后重 OCR |
| P3-GXMM-TJ_rescan | 1 | 同上 |

**P2 合计：2 file_id / ~2 pages**

### 7.4 P3（1944—1945 时期新增资料，等 cheer 端补充）

当前 21+37 中 1944—1945 时期 chunks = 0（被 sourcebook 覆盖）。等 cheer 提供：
- 1944 民憲 后续期号（如第一卷第二期以后）
- 1945 临时全国代表大会相关一手档案
- 1945 重庆谈判 / 政协相关报刊报道

## 8. 关键文件清单

```
work/domestic/
├── CLAUDE_PHASE0_BASELINE_20260726.md/.json
├── CLAUDE_OCR_MANIFEST_ACCEPTED21_20260726.jsonl
├── CLAUDE_OCR_MANIFEST_PENDING37_20260726.jsonl
├── CLAUDE_OCR_MANIFEST_P3-023_20260726.jsonl
├── CLAUDE_PHASE1_MANIFEST_RECONCILIATION_20260726.csv/.md
├── CLAUDE_PHASE2_COLLECTION_RECONCILIATION_20260726.md
├── CLAUDE_PHASE3_OCR_QUEUE_20260726.csv/.md
├── CLAUDE_PHASE4_OCR_DECISIONS_20260726.csv
├── CLAUDE_PHASE4_OCR_REVIEW_20260726.json/.md
├── CLAUDE_PHASE5_IMPORT_CANDIDATE_MANIFEST_20260726.jsonl
├── CLAUDE_PHASE5_IMPORT_DRYRUN_20260726.json/.md
├── CLAUDE_PHASE6_SEARCH_REGRESSION_20260726.json/.md
├── CLAUDE_CODE_LONG_TASK_FINAL_20260726.md (本报告)
└── CLAUDE_CODE_LONG_TASK_FINAL_20260726.json

data/domestic/
└── collection_download_manifest_20260726.jsonl (62 条)
```

## 9. 移交与等待 Codex

本轮提交后停止并等待 Codex 验收。Codex 验收通过后，按以下顺序操作：

1. 备份：`cp -p data/research_index.sqlite data/research_index.sqlite.20260726_phase5.pre.bak`
2. 跑 39 条检索回归（已记录 baseline）
3. 跑 `upgrade_domestic_ocr_pages.py` apply（先 P0 子集 56 file_id / 3336 pages）
4. 跑 `PRAGMA integrity_check` + 重跑 39 条 after 检索
5. 比对 before/after，决定是否提交
6. Codex 确认后才允许 `git commit` 与 `git push`

P3-GXMM-SH/TJ cheer-only 补图后单独追加一轮；
P3-113/114 后段完成后追加一轮；
P3-023 由 Codex 单独确认后并入 accepted21 或另立 accepted22。

**结束本轮提交，等待 Codex 验收。**