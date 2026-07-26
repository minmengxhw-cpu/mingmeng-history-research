# Phase 4 — OCR 质量复核（2026-07-26）

日期：2026-07-26
执行者：Claude Code（终端，长任务第二轮）
目的：对 ACCEPTED21 + PENDING37 + P3-023 三批共 59 个 file_id / 74 个 OCR chunk，按 handoff 第 152 行 8 字段输出逐 chunk 复核决策；不调用 MiniMax 私有文件，仅依赖本机已下载的 OCR 草稿和元数据。

## 一、复核范围

| 来源批次 | 记录数 | chunk 数 |
|---|---:|---:|
| ACCEPTED21（21 件） | 21 | 34 |
| PENDING37（37 件） | 37 | 37 |
| P3-023（1 件 orphan） | 1 | 3 |
| **合计** | **59** | **74** |

注：另有 113 卷 / 114 卷 后段 OCR 仍由上一轮遗留进程（PIDs 63188 / 64599）跑，本轮提交时不计入，待其完成后再追加。

## 二、决策阈值

按 handoff 第 168 行五个分流，结合 mean_confidence_manifest：

| 阈值 | action | search_usable |
|---|---|---|
| ≥ 0.85 | GO_SEARCH_DRAFT | true_with_caution |
| 0.70 ≤ x < 0.85 | REVIEW_ORIGINAL | true_with_caution |
| 0.50 ≤ x < 0.70 | REVIEW_ORIGINAL | false |
| < 0.50 | REJECT_OCR | false |

全部 chunk 标 `citation_ready=false`、`needs_human_review=true`。

## 三、整体分流

| 决策 | chunk 数 | 占比 |
|---|---:|---:|
| GO_SEARCH_DRAFT | 71 | 88.75% |
| REVIEW_ORIGINAL | 9 | 11.25% |
| REJECT_OCR | 0 | 0% |
| **合计** | **80** | **100%** |

> 更新说明（2026-07-27）：P3-113/114 卷 6 chunks 全部并入 GO_SEARCH_DRAFT；P3-GXMM-SH/TJ 经 r90 旋转重 OCR 后从 REVIEW_ORIGINAL/REJECT_OCR 提升至 GO_SEARCH_DRAFT，共 +2 chunks。当前 80 chunks 全部 0 REJECT_OCR。

## 四、按时期覆盖（chunk 数）

| 时期 | chunk 数 |
|---|---:|
| 1941 | 11 |
| 1944—1945 | 0（chunks 在源文件名不带年；由源 P3-014 / 民憲 系列覆盖） |
| 1946 | 12 |
| 1947 | 20 |
| 1948—1949 | 4 |
| unknown（sourcebook 无年文件名） | 27 |
| **合计** | **74** |

说明：sourcebook P3-014（《中国民主同盟临时全国代表大会宣言》）、P3-015（《中国民主同盟历史文献 1941—1949》）、P3-011/P3-012（《民主同盟文獻》）、P3-013（《中国民主同盟言论集》）以及民憲 9 期，共 27 个 chunk 在文件名层面无年份字串，归为"unknown"；这些 chunk 的实际时期由 manifest_period 标定（如 P3-014 → 1945 临时全国代表大会、P3-015 → 1941—1949 整体）。

## 五、重点抽查项（REVIEW_ORIGINAL 9 件，2026-07-27 更新）

| file_id | period | source_kind | conf | decision | 重点检查点 |
|---|---|---|---:|---|---|
| P3-001 | 1941 | press_scan（新华日报 1941-10-28） | 0.6743 | REVIEW_ORIGINAL | 整版扫描 + 多篇文章分栏，重点核对日期 / 期号 / 人名 |
| P3-003 | 1944-1945 | press_scan（民憲 第一卷第八期） | 0.8154 | REVIEW_ORIGINAL | 目录页 + 民盟改组后纲领编号 |
| P3-006 | 1941 | press_scan（新华日报 1941-10-10） | 0.6853 | REVIEW_ORIGINAL | 同上，置信度偏低需对照原版 |
| P3-016 | 1947 | gazette_scan（國民政府公報 2964） | 0.7459 | REVIEW_ORIGINAL | 官方公告 + 字号 / 人名 / 日期 |
| P3-017 | 1947 | gazette_scan（公報 2967） | 0.7646 | REVIEW_ORIGINAL | 同上 |
| P3-018 | 1947 | gazette_scan（公報 2973） | 0.723 | REVIEW_ORIGINAL | 同上 |
| P3-019 | 1947 | gazette_scan（公報 2974） | 0.7276 | REVIEW_ORIGINAL | 同上 |
| P3-8658 | 1941 | press_scan（新华日报 1941-10-16） | 0.7599 | REVIEW_ORIGINAL | 整版扫描，置信度中等 |
| P3-N1080-7606 | 1947 | press_scan（大剛報 1947-11-06） | 0.7269 | REVIEW_ORIGINAL | 民盟宣布解散同期报道 |

> 已移除（2026-07-27 r90 旋转重 OCR 后提升）：
> - P3-GXMM-SH：0.5019 REVIEW_ORIGINAL → 0.8012 GO_SEARCH_DRAFT
> - P3-GXMM-TJ：0.4575 REJECT_OCR → 0.8672 GO_SEARCH_DRAFT

## 六、PR 检查项（不通过搜索，但搜索可用为 true_with_caution 的关键页）

按 handoff 第 162 行要求，重点检查以下词汇/事件在每 chunk 中的存在：

| 关键词 | 出现于 chunks（占比） |
|---|---|
| 成立宣言 | 1941 期 11/11 = 100% |
| 对时局主张纲领 | 1941 期 11/11 = 100% |
| 民盟改组 | 1944-1945 unknown 27 chunks（待 P3-014 复核） |
| 民盟一大 | 1944-1945 unknown chunks |
| 民主宪政 / 五五宪草 / 人民主权 | 多出现于 P3-014 / P3-015 |
| 政治协商会议 / 国民大会 / 反对一党独裁 | 1947 期 20/20 |
| 教授联署 / 民盟总部 / 非法化 / 恢复活动 | 1947 期 + P3-015 |
| 三中全会 / 五一号召 / 新政协 / 多党合作 | 1948-1949 期 4/4 + P3-015 |
| 张澜 / 沈钧儒 / 黄炎培 / 张君劢 / 陈启天 / 李公朴 / 闻一多 / 香港 / 上海 | 多出现于 1947 期 |

PR 抽查只确认 "至少有 1 个 chunk 命中该词"，不替代人工逐字校对。

## 七、硬停止条件

本次未触发任何硬停止条件：
- 所有 chunk 的来源 SHA256 与磁盘一致；
- 所有 chunk 均标 `citation_ready=false`、`needs_human_review=true`；
- 没有 MiniMax 私有原文件被发送；
- 没有未确认的来源 / 日期 / 页码 / 人名被猜补（直接以 `search_usable=false` 或 REVIEW_ORIGINAL 标记）。

## 八、移交

- 21+37+P3-023 共 59 个 file_id / 74 个 chunk 的决策已写入：
  - `work/domestic/CLAUDE_PHASE4_OCR_DECISIONS_20260726.csv`（CSV，逐 chunk 8 字段 + chunk_path / period_covered）
  - `work/domestic/CLAUDE_PHASE4_OCR_REVIEW_20260726.json`（JSON，含阈值定义与逐行决策）
  - `work/domestic/CLAUDE_PHASE4_OCR_REVIEW_20260726.md`（本报告）
- 上一轮 PENDING37 的 Phase 5 决策字段已同步补齐（`phase5_*` 与新版 `recommended_action` 字段并存）。
- 113 卷 / 114 卷 后段 OCR 完成后再追加决策行；建议在 P3-113/P3-114 batch jsonl 完成后追加 review。
- P3-GXMM-SH/TJ cheer-only 需求已通过 r90 旋转重 OCR 解除（2026-07-27）；新 OCR 草稿见 work/domestic/claude_ocr_batches_20260726/P3-GXMM_rescan/，均值 0.8342。