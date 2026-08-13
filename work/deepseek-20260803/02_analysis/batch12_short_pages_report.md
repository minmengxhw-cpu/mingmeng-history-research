# Batch 12 · 短页面队列复核与深层处置

- 正式库只读路径：`data/research_index.sqlite`
- 刷新时间：2026-08-07T15:02:10Z
- 短页面总数：**220**（与 Batch7 对齐）
- 优先队列（Q0+Q3+Q4 或 citation 冲突）：**201**
- 重 OCR 队列（priority≥2）：**69**
- citation_ready=1 冲突待降级：**82**
- 无 page_provenance：**11**

## Batch7 分层（刷新后）

| 分层 | 数量 |
|---|---:|
| Q0_EMPTY | 6 |
| Q3_OCR_SUSPECT | 117 |
| Q4_FRAGMENT | 1 |
| Q5_SHORT_REVIEW | 96 |

## 深层处置码

| 处置码 | 数量 |
|---|---:|
| D7_SHORT_BODY_CANDIDATE | 103 |
| D6_OCR_GARBLED | 64 |
| D3_ISSUE_HEADER | 17 |
| D2_LIBRARY_STAMP | 11 |
| D4_COVER_TITLE | 10 |
| D5_AD_OR_CARTOON | 8 |
| D0_EMPTY_HANDWRITING | 4 |
| D0_EMPTY_LIKELY_BLANK | 1 |
| D0_EMPTY_NEEDS_REOCR | 1 |
| D1_BINARY_GARBAGE | 1 |

## 优先队列

| 队列 | 数量 |
|---|---:|
| P0_EMPTY | 6 |
| P1_OCR_OR_FRAGMENT | 118 |
| P2_SHORT_BODY | 96 |

## P0 空文本 6 条明细

| page_id | doc_key | page | 影像 | size | 处置 |
|---:|---|---|---|---:|---|
| 20708 | `domestic-ocr/SAAC:domestic:SAAC:51koukou-p03-dde03-f1` | page-04 | yes | 29989 | D0_EMPTY_LIKELY_BLANK |
| 20718 | `domestic-ocr/SAAC:domestic:SAAC:51koukou-p04-dde01-i3` | page-02 | yes | 204620 | D0_EMPTY_NEEDS_REOCR |
| 20762 | `domestic-ocr/SAAC:domestic:SAAC:51koukou-p05-dde05-i3` | page-02 | yes | 351412 | D0_EMPTY_HANDWRITING |
| 20763 | `domestic-ocr/SAAC:domestic:SAAC:51koukou-p05-dde05-i3` | page-03 | yes | 297257 | D0_EMPTY_HANDWRITING |
| 20764 | `domestic-ocr/SAAC:domestic:SAAC:51koukou-p05-dde05-i3` | page-04 | yes | 226676 | D0_EMPTY_HANDWRITING |
| 20766 | `domestic-ocr/SAAC:domestic:SAAC:51koukou-p05-dde05-i3` | page-06 | yes | 199180 | D0_EMPTY_HANDWRITING |

## 处置规则（本批）

1. **不晋升**：任何 text<120 页面不得新设 `citation_ready=1`。
2. **应降级**：已是 `citation_ready=1` 的短页面一律降为 0，并标记 `needs_human_review=1`（见 migrate）。
3. **空文本**：影像在则入重 OCR 队列；影像 <50KB 标为疑似空白；签到类标手写优先。
4. **二进制伪文本**（如 PNG 头写入 text）：清理伪文本槽，不按正文引用。
5. **馆藏章/卷期头/封面/广告**：结构保留，citation 禁止。
6. **D7 短正文候选**：仅允许人工抽检后个案解除，本批仍 `citation_eligible=no`。
7. 本分析脚本只读；正式库写入由 `deepseek_20260803_batch12_migrate.py` 执行。

## 产出文件

- `short_pages_batch12_refresh.csv` — 全量刷新
- `short_pages_dispositions.csv` — 处置摘要
- `short_pages_priority_queue.csv` — P0/P1 + citation 冲突
- `short_pages_reocr_queue.csv` — 重 OCR 优先队列
- `short_pages_citation_demote.csv` — 待降级 citation_ready 清单
