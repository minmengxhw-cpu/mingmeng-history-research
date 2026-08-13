# MINIMAX PROGRESS — 国内资料生产线

> **分支**：`agent/minimax-domestic-production-20260803`
> **周期**：2026-08-03 起 6—8 周；本轮第 1 阶段（2 周）已完成 baseline。
> **目标**：1941—1943 / 1944—1945 / 1946—1950 三个重点期
> **角度**：民盟自身原始文件 + 国内党政机关记录 + 政协/统一战线 + 同期公共舆论
> **位置**：所有产出在 `work/minimax-20260803/`，不直接写入 `data/research_index.sqlite`

---

## 0. 关键数字

| 指标 | 数值 |
|---|---:|
| 输入 candidates | 689 |
| 接受（accepted） | 660 |
| 待人工复核（needs_human_review） | 29 |
| 拒收 / 重复 | 0 |
| 重点期（1941-1950）内 candidates | 664 |
| 唯一 source_url | 498 |
| OCR 计划行 | 216 |
| OCR 跳过（已 full_item_online） | 228 |
| 物理书 / 调档项 | 10 |
| 去重簇 | 32（92 个 duplicates） |
| Staging candidates 入库 | 664 |
| 可入库（import_ready） | 545 |
| 待复核（needs_review） | 27 |
| 应排除（exclude） | 92 |
| 可直接进 citation 级（citation_ready=1） | **233** |
| Gate 检查 | **PASS** |

---

## 1. 阶段产出

```
work/minimax-20260803/
├── 01_inventory/
│   ├── inventory_full.jsonl            # 664 行：每份资料 + 来源 + 期间
│   ├── inventory_summary.json
│   ├── provenance_full.jsonl           # 664 行：每份资料的 provenance
│   ├── period_breakdown.csv            # 时期 × 等级 / 介质 / 复核分布
│   └── repository_breakdown.csv        # 机构分布
├── 02_manifests/
│   ├── duplicate_clusters.json         # 32 个簇、92 duplicates
│   ├── duplicate_report.csv            # 92 行：canonical / duplicate
│   ├── source_manifest.jsonl           # 664 行：包含 SHA256 / page_count / OCR 标记
│   ├── source_manifest_summary.md
│   └── import_dryrun.json              # 干运行：gate / 3 bucket / 时期统计
├── 03_ocr/
│   ├── ocr_plan.jsonl                  # 216 行：page-level provenance / citation_ready=false
│   ├── ocr_skip_manifest.jsonl         # 228 行：已 full_item_online 不重复 OCR
│   ├── ocr_done_manifest.jsonl         # 69 行：download_manifest 已下载
│   ├── acquisition_required.jsonl      # 10 行：物理书 + 无 URL → 调档
│   ├── ocr_manifest_summary.json
│   └── ocr_manifest_summary.md
├── 04_staging/
│   ├── staging.sqlite                  # 2.0 MB：不依赖 research_index.sqlite
│   ├── import_ready.csv                # 545 行
│   ├── needs_review.csv                # 27 行
│   ├── exclude.csv                     # 92 行
│   └── three_lists_summary.md
└── 05_checkpoint/
    ├── MINIMAX_PROGRESS.md             # 本文件
    ├── MINIMAX_CHECKPOINT.md           # 阶段 1 检查点
    ├── evidence_gap_summary.csv        # 9 事件 4 维覆盖度
    ├── evidence_gap_*.md               # 每个事件的缺口报告
    ├── evidence_gap_actionable.json    # 可下批任务
    ├── ocr_batches.{json,md}           # OCR 批次调度（7 批 / 216 文件 / 27.1 分钟）
    ├── lx_upgrade_proposals.{md,json}  # 4 条 LX 升级提案
    ├── lx_apply_report.json            # 4 条 LX 实际升级结果
    ├── needs_review_tasks.{csv,md}     # 27 条 needs_review 拆分 73 任务
    └── 阶段 2 入口
```

脚本在 `scripts/minimax/`：

- `minimax_20260803_inventory.py`
- `minimax_20260803_dedup.py`
- `minimax_20260803_source_manifest.py`
- `minimax_20260803_ocr_manifest.py`
- `minimax_20260803_staging.py`
- `minimax_20260803_three_lists.py`
- `minimax_20260803_evidence_gap.py`     # 阶段 2 入口 1
- `minimax_20260803_ocr_batches.py`      # 阶段 2 入口 2
- `minimax_20260803_lx_upgrade.py`       # 阶段 2 入口 3
- `minimax_20260803_lx_apply.py`         # 阶段 2 入口 3（apply）
- `minimax_20260803_needs_review_tasks.py`  # 阶段 2 入口 4

---

## 2. 三个重点期 × 进展

### 2.1 1941—1943 民盟成立与早期活动

| 等级 | 数量 | 备注 |
|---|---:|---|
| L1 | 4（升级 1 条） | 1941-10-10 成立宣言（L1，wikisource 公开转录）|
| L2 | 40 | 汇编本为主（含 1941-10-10 成立宣言 / 1943-07 梁漱溟访谈） |
| L3 | 20 | 同期报刊（L3）需补版面 |
| L4 | 7 | 盟史综述 |
| **小计** | **68** | import_ready |

**OCR 任务**：1941-1943 现有 17 个 OCR 计划项（p2:15, p3:2），全部为 L2 汇编类。
**关键缺口**：
- 1941-10-10 香港《光明報》创刊号原刊
- 1941-11-16 茶会原档
- 1943-07-31 FRUS 246.d.232/272/d.329 等文件英文原文

### 2.2 1944—1945 抗战后期与组织发展

| 等级 | 数量 | 备注 |
|---|---:|---|
| L1 | 14 | 民宪 1944 第一卷各期已 landing URL |
| L2 | 38 | 1944-09-19 改组 + 1945-10 临时一大文件 |
| L3 | 18 | 1944-12 改组后昆明等地报刊 |
| L4 | 11 | 后期盟史 |
| **小计** | **81** | import_ready |

**OCR 任务**：1944-1945 现有 12 个 OCR 计划项（p2:7, p3:5）。
**关键缺口**：
- 1944-09-19 改组决议原始签署版
- 1945-10 临时全国代表大会 4 项文件（政治报告、宣言、纲领、规程）原件
- 1945-07-04 延安会谈记录同期副本

### 2.3 1946—1950 政协、联合政府与历史转折

| 等级 | 数量 | 备注 |
|---|---:|---|
| L1 | 232（升级 3 条） | 12 个光明报 issue、SAAC 30 件档案、多个大公报版面 |
| L2 | 139 | 1946 文献汇编、1947 解散公告、1948 五一口号响应 |
| L3 | 7 | 同年期刊转录 |
| L4 | 19 | 后期回忆 |
| **小计** | **396** | import_ready |

**OCR 任务**：1946-1950 现有 187 个 OCR 计划项（p1:174, p2:12, p3:1）。
**关键缺口**：
- 1948-01-05 一届三中全会紧急声明原稿
- 1948-05-01 毛泽东亲笔信影印件
- 1949-09-21 政协一届全体会议主席团名单 / 签到簿原件

---

## 3. 阶段 2 入口（已就绪）

### 3.1 LX 4 条升级（已完成 ✅）

| 候选 | 原等级 | 升级后 | 验证 |
|---|---|---|---|
| domestic:WS:democratic-league-declaration-1941 | LX | L1 | HTTP 200 + title_match |
| domestic:WS:peace-building-program-1946 | LX | L1 | HTTP 200 + title_match |
| domestic:WS:pcc-national-assembly-resolution-1946 | LX | L1 | HTTP 200 + title_match |
| domestic:WS:pcc-government-reorganization-1946 | LX | L1 | HTTP 200 + title_match |

升级后：citation_ready 增加 4，LX 残留 = 0。

### 3.2 OCR 批次调度（7 批 / 216 文件 / 27.1 分钟）

| 批次 ID | 优先级 | 时期 | 文件数 | 页数 | 估计时间 |
|---|---|---|---:|---:|---:|
| OCR-BATCH-p1-1946-1950-01 | p1 | 1946-1950 | 174 | 174 | 23.2 min |
| OCR-BATCH-p2-1944-1945-02 | p2 | 1944-1945 | 7 | 7 | 0.7 min |
| OCR-BATCH-p2-1941-1943-03 | p2 | 1941-1943 | 15 | 15 | 1.5 min |
| OCR-BATCH-p2-1946-1950-04 | p2 | 1946-1950 | 12 | 12 | 1.2 min |
| OCR-BATCH-p3-1944-1945-05 | p3 | 1944-1945 | 5 | 5 | 0.3 min |
| OCR-BATCH-p3-1941-1943-06 | p3 | 1941-1943 | 2 | 2 | 0.1 min |
| OCR-BATCH-p3-1946-1950-07 | p3 | 1946-1950 | 1 | 1 | 0.1 min |

### 3.3 Evidence Gap（9 事件）

| 事件 | L1 | L2 | L3 | L4 | 缺口 |
|---|---:|---:|---:|---:|---|
| 1941 成立 | 0 | 4 | 2 | 4 | L1 缺失 → ✅ 已通过 LX 升级 1 条 |
| 1944 改组 | 11 | 9 | 0 | 2 | 缺 政协/统一战线 |
| 1945 一大 | 4 | 15 | 4 | 3 | 缺 政协/统一战线 + 公共数字化 |
| 1946 旧政协 | 11 | 10 | 0 | 1 | 缺 政协/统一战线 + needs_review 3 |
| 1946 拒国大 | 16 | 3 | 0 | 1 | needs_review 4 |
| 1946 李闻 | 28 | 5 | 1 | 2 | needs_review 3 |
| 1947 取缔 | 51 | 10 | 0 | 18 | ✅ 4 维均覆盖 |
| 1948 三中 | 17 | 0 | 1 | 1 | 缺 L2 + 政协/公共数字化 |
| 1949 新政协 | 166 | 0 | 0 | 1 | 缺 L2 + 政协/公共数字化 |

### 3.4 needs_review 27 条 拆分（73 任务 / 14.2 小时）

按缺口类型分布：
- archive_id_missing: 高频
- level_review: 高频
- uncertainties_clarify: 中
- period_unclear: 中

---

## 4. 关键质量门

- ✅ **OCR 草稿不标 citation_ready**：`needs_ocr=1 AND citation_ready=1` 数量为 0。
- ✅ **可入库不含 duplicates**：92 个 duplicates 全部归入 `exclude`。
- ✅ **gate=PASS**：OCR 草稿未通过 citation 门。
- ✅ **原始文件只读**：未触碰 `data/research_index.sqlite` 与 `data/domestic/` 字段。
- ✅ **未触动 raw 文件**：所有 PDF / 影像 / 图片缓存未读写。
- ✅ **OCR 草稿全部 `citation_ready=false`**：216 条 plan + 69 条 done。
- ✅ **agency 来源溯源**：每个 candidate 包含 `source_url` / `url_host` / `archive_fonds` / `archive_series` / `archive_file` / `archive_item`。
- ✅ **LX 升级**：4 条 LX 全部升级为 L1（HTTP 200 + title_match）；LX 残留 = 0。

---

## 5. 下一步（阶段 2 推进）

1. **第一周**：跑完 p1 + 1946-1950 OCR 批次（174 文件），升级 30+ 个 L1 citation_ready。
2. **第二周**：执行 needs_review 73 任务（14 小时），重点补 HKU 缩微 / SAAC 1947-1948 / SHDPZ 1942-1943。
3. **第三周**：拓展 cheer-only 接力（港大 + 二史馆 + NLC 视检），为 1941-1943 关键事件闭环。
4. **第四周**：人物同期函电索引（罗隆基、章伯钧、沈钧儒、张澜等），完成人物交叉对位。

---

## 6. 复审边界

- 本批的 545 条 `import_ready` 中，已 `citation_ready=yes` 233 条可立刻进入前台；
  其余 312 条仅作线索 / 检索级。**禁止**让 L1_needs_review / L3_press_surrogate / L4_secondary
  在不再次人工复核的情况下进入正式引用。
- `needs_review` 27 条已拆分为 73 个具体人工任务（详见 `needs_review_tasks.md`）。
- `exclude` 92 条保留 `cluster_id` + `canonical_id`，原始 manifest 仍可追溯。
- 已升级 4 条 LX → L1，但 status 标记 `promoted_pending_real_artifact_comparison`，需后续与原件影像核对。
