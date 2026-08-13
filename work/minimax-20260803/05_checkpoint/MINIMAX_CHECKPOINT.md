# MINIMAX CHECKPOINT — 国内资料生产线 · 阶段 1 收口 + 阶段 2 入口

> **批次**：`minimax-20260803-phase1-inventory / phase2-source-manifest / phase3-ocr-manifest / phase4-staging / phase5-three-lists / phase6-lx-upgrade / phase7-ocr-batches / phase8-needs-review-tasks / phase9-evidence-gap`
> **时间**：2026-08-03
> **承接**：codex 已沉淀的 689 条国内 candidates + 89 条 sources + 9 个关键事件
> **不依赖**：`data/research_index.sqlite`（未触读、未触写）

---

## 1. 阶段 1 收口数量

| 阶段 | 产出 | 数量 |
|---|---|---:|
| **Inventory** | inventory_full.jsonl | 664 |
| | provenance_full.jsonl | 664 |
| | period_breakdown.csv | 3 行时期 × 等级 |
| | repository_breakdown.csv | 80+ 行机构 |
| **Dedup** | duplicate_clusters.json | 32 簇 |
| | duplicate_report.csv | 92 duplicates |
| **Source Manifest** | source_manifest.jsonl | 664 |
| | import_dryrun.json | gate=PASS |
| **OCR Manifest** | ocr_plan.jsonl | 216（含 page-level provenance） |
| | ocr_skip_manifest.jsonl | 228（full_item_online 不重复 OCR） |
| | ocr_done_manifest.jsonl | 69（已下载） |
| | acquisition_required.jsonl | 10（物理书 + 无 URL） |
| **Staging** | staging.sqlite | 2.0 MB / 8 表 |
| | import_ready.csv | 545 |
| | needs_review.csv | 27 |
| | exclude.csv | 92 |
| **LX 升级** | lx_upgrade_proposals.json | 4 条 |
| | lx_apply_report.json | 4 条已应用 |
| **OCR 批次** | ocr_batches.json | 7 批 |
| **Evidence Gap** | evidence_gap_summary.csv | 9 事件 |
| | evidence_gap_actionable.json | 9 任务 |
| **Needs Review 拆分** | needs_review_tasks.csv | 73 任务 / 14.2 小时 |

---

## 2. 阶段 2 入口就绪

### 2.1 LX 升级（已完成 4/4）

| 候选 | 原 | 升级 | 验证 |
|---|---|---|---|
| domestic:WS:democratic-league-declaration-1941 | LX | L1 | HTTP 200 + title_match=True |
| domestic:WS:peace-building-program-1946 | LX | L1 | HTTP 200 + title_match=True |
| domestic:WS:pcc-national-assembly-resolution-1946 | LX | L1 | HTTP 200 + title_match=True |
| domestic:WS:pcc-government-reorganization-1946 | LX | L1 | HTTP 200 + title_match=True |

升级写入 staging 库 + import_log。LX 残留 = 0。

### 2.2 OCR 批次（7 批 / 216 文件 / 27.1 分钟）

按 30 分钟/批切分：
- p1 + 1946-1950（174 文件）— 23.2 min
- p2 + 1944-1945（7 文件）— 0.7 min
- p2 + 1941-1943（15 文件）— 1.5 min
- p2 + 1946-1950（12 文件）— 1.2 min
- p3 + 1944-1945（5 文件）— 0.3 min
- p3 + 1941-1943（2 文件）— 0.1 min
- p3 + 1946-1950（1 文件）— 0.1 min

### 2.3 Evidence Gap（9 事件）

| 事件 | 缺口 | 阶段 2 任务 |
|---|---|---|
| 1941 成立 | L1 缺失 | ✅ 已通过 LX 升级 1 条 |
| 1944 改组 | 缺 政协 | cheer 接力政协 / 中央社 |
| 1945 一大 | 缺 政协/公共 | 跑中央统战部 / 中共党史 |
| 1946 旧政协 | 缺 政协 + needs_review 3 | LX 升级已完成；3 条 needs_review 拆为 9 任务 |
| 1946 拒国大 | needs_review 4 | 拆为 12 任务 |
| 1946 李闻 | needs_review 3 | 拆为 9 任务 |
| 1947 取缔 | OK | — |
| 1948 三中 | 缺 L2 + 政协 | cheer 接力 L2 汇编 |
| 1949 新政协 | 缺 L2 + 政协 | cheer 接力 L2 汇编 |

### 2.4 needs_review 27 条 → 73 任务

按缺口类型：
- archive_id_missing: 27 条（每条）
- level_review: 27 条
- uncertainties_clarify: ~12 条
- 其他: ~7 条

按优先级：
- p1: 54 任务（351 分钟）
- p2: 16 任务
- p3: 3 任务

---

## 3. 失败 / 风险项

### 3.1 已知 OCR 阻塞（17 项）

| 时期 | 优先级 | 候选 | 原因 |
|---|---|---|---|
| 1944-1945 | p2 | domestic:MMHIST:program-draft-1944-09-19 | marxists.org PDF 已 full_item_online 但 medium=hybrid，标记 needs_ocr 不重复 OCR |
| 1946-1950 | p1 | domestic:NLC:guangmingbao-1947-issue22（22 个 articles） | 共享同一份 PDF 的不同文章，OCR 一次覆盖多个 candidate |
| 1946-1950 | p1 | domestic:SAAC:1949-index-c*（30 件档案） | landing URL 到达，但影像缓存未在仓库 |

### 3.2 物理书 / 调档清单（10 项）

| 时期 | 机构 | 资料 |
|---|---|---|
| 1941-1943 | SC | 《四川民盟史》 |
| 1941-1943 | SN | 《陕西民盟史》 |
| 1944-1945 | FJ | 《中国民主同盟福建简史》（苏增添主编 2018） |
| 1944-1945 | GD | 《广东民盟史》（李竟先 2012） |
| 1944-1945 | GZ | 《贵州民盟史》（2013） |
| 1944-1945 | HB | 《湖北民盟史》（向必武 2014） |
| 1944-1945 | HN | 《湖南民盟人物》（2020） |
| 1944-1945 | JS | 《江苏民盟史稿》（2004） |
| 1944-1945 | JS | 《中国民主同盟江苏简史》（2012） |
| 1944-1945 | YN | 《云南民盟史》（2021） |

### 3.3 needs_human_review 27 条

主要在 1941-1943（11 条）、1946-1950（10 条）。**已拆分为 73 个具体任务**（详见 `needs_review_tasks.md`）。

---

## 4. 已守住的不变量

- ✅ **OCR 草稿不标 citation_ready**：`needs_ocr=1 AND citation_ready=1` 数量为 **0**。
- ✅ **Gate 检查**：OCR 草稿未通过 citation 门 → **PASS**。
- ✅ **可入库不含 duplicates**：92 个 duplicates 全部归入 `exclude`。
- ✅ **原始文件只读**：未触碰 `data/research_index.sqlite`、`data/domestic/sourcebooks/`、`data/domestic/press_scans/`、`data/domestic/raw/`。
- ✅ **未触动 raw 文件**：所有 PDF / 影像未读取复制。
- ✅ **staging 独立**：`work/minimax-20260803/04_staging/staging.sqlite` 不连带 `research_index.sqlite`，互不污染。
- ✅ **可追溯**：每个 candidate 含 `source_url`、`url_host`、`archive_fonds`、`archive_series`、`archive_file`、`archive_item`、`catalog_reference` 全栈字段。
- ✅ **CLAUDE/STAGING 兼容**：staging schema 与 `ingest_domestic.py` 对齐，可后续一次性 `apply` 到 `research_index.sqlite`。
- ✅ **LX 升级可验证**：每条 L1 升级通过 HEAD 请求 200 + title_match=True 验证。
- ✅ **LX 残留 = 0**：4 条 LX 全部升级，0 条残留。

---

## 5. 阶段 2 路线图

### 5.1 第一周：OCR 优先

- 跑 p1 + 1946-1950（174 文件 / 23.2 min）
- 升级 30+ 个 L1 citation_ready
- 重新生成 staging + three_lists

### 5.2 第二周：needs_review 人工任务

- 跑 p1 任务 54 任务（351 分钟 ≈ 6 小时）
- 重点：HKU 缩微 / SAAC 1947-1948 / SHDPZ 1942-1943
- 升级 27 条 needs_review 中的 6-10 条

### 5.3 第三周：cheer-only 接力

- 港大 Special Collections（HKU 缩微）— 1941 香港《光明報》原刊
- 二史馆 1354 全宗 — 1947-10-27 内政部公函
- NLC 视检 — 1947-11-06 大公报高分辨率

### 5.4 第四周：人物同期函电索引

- 罗隆基、章伯钧、沈钧儒、张澜等核心人物
- 同期函电、组织文件、声明
- 人物 × 事件 × 史料对位

---

## 6. 决策日志

- **2026-08-03**：建立 `agent/minimax-domestic-production-20260803` 分支。
- **2026-08-03**：基础盘点（664 in-scope）确认。
- **2026-08-03**：去重算法采用 Union-Find，按 (catalog + page)、(catalog_page + 标题前缀)、(URL + 日期 + 页码) 三重聚类；同一 PDF 内的不同文章不合并。
- **2026-08-03**：citation_ready 规则：OCR 草稿一律 `False`；L1 + full_item_online 为 `True`；L2 + 已有 catalog_reference/page 为 `True`。
- **2026-08-03**：OCR 草稿门控件：检测 `needs_ocr AND citation_ready` 组合，必须为 0。
- **2026-08-03**：staging 数据库独立建立，schema 与 `ingest_domestic.py` 兼容。
- **2026-08-03**：LX 4 条升级提案：基于 4 维字段完整 + URL 主机为 wikisource。
- **2026-08-03**：LX 升级 apply：4 条全部通过 HEAD 200 + title_match 验证，升级为 L1。
- **2026-08-03**：OCR 批次切分：按 30 分钟/批 + 优先级 + 时期。
- **2026-08-03**：Evidence Gap：9 事件 4 维覆盖度评估。
- **2026-08-03**：needs_review 27 条拆分 73 任务 / 14.2 小时。
- **2026-08-03**：阶段 1 完成后，未对 `research_index.sqlite` 写入任何数据。

---

## 7. 引用口径

- **可入库**：545 条（`import_ready`）。本轮阶段 1 完成后不直接 apply 到 production。
- **可用于 citation**：233 条（`citation_ready=yes`，含 4 条新升级 LX）。其中 L1 233、L2 0（按 staging 库统计）。需人工复核后引用。
- **需复核**：27 条（LX / needs_human_review），已拆为 73 任务。
- **应排除**：92 条（cluster duplicates）。
- **调档清单**：10 条（物理书）。
- **OCR 计划**：216 条 → 7 批（27.1 分钟）。
- **OCR 跳过**：228 条（已 full_item_online）。
- **OCR 已完成**：69 条（download_manifest 已下载）。
- **LX 升级**：4 条 LX → L1（HTTP 200 + title_match）。
- **Evidence Gap**：9 事件 + 9 actionable 任务。
