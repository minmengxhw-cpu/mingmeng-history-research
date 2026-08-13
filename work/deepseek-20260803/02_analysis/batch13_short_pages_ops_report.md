# Batch 13 · 重 OCR 建议 / 人工抽检 / 无 provenance 补档计划

- 正式库只读路径：`/Users/cheer/Documents/mm agent/mingmeng-history-research/data/research_index.sqlite`
- 生成时间：2026-08-07T15:05:01Z
- 重 OCR 队列：**69**（priority≥2，来自 Batch12）
- 人工抽检样本：**22**
- 短页无 provenance 拟补桩：**11**
- 国内页无 provenance 全量（观察）：**588**（本批仅处理短页 11 条）
- **本批不执行 OCR**（审计分支约束）

## 重 OCR 队列构成

| disposition | 数量 |
|---|---:|
| D6_OCR_GARBLED | 64 |
| D0_EMPTY_HANDWRITING | 4 |
| D0_EMPTY_NEEDS_REOCR | 1 |

| priority | 数量 |
|---:|---:|
| 3 | 5 |
| 2 | 64 |

## 引擎与参数总则

1. 默认引擎：现网已用 PaddleOCR；重跑建议 PP-OCRv4 + `use_angle_cls=true`。
2. 手写签到（4 页）：降低 det 阈值、保留灰度，优先人工著录人名。
3. 空文本大图（1 页）：标准重跑；空文本小图（1 页）：先目检是否空白。
4. 乱码 64 页：提高 `det_limit_side_len`、deskew；报纸双栏先切栏。
5. 二进制伪文本：先清 `pages.text`，再按图 OCR。
6. 任何重 OCR 结果须重新过 citation 门禁；默认 `citation_ready=0`。

## 人工抽检样本分层

| sample_id | page_id | code | title |
|---|---:|---|---|
| S13-01 | 20708 | D0_EMPTY_LIKELY_BLANK | 中国人民政治协商会议筹备会第二次全体会议记录（1949-09-17） |
| S13-02 | 20718 | D0_EMPTY_NEEDS_REOCR | 新政治协商会议筹备会关于召开成立会的通知（1949-06-14） |
| S13-03 | 20762 | D0_EMPTY_HANDWRITING | 政协一届全体会议代表签到（1949-09-21） |
| S13-04 | 20763 | D0_EMPTY_HANDWRITING | 政协一届全体会议代表签到（1949-09-21） |
| S13-05 | 20623 | D1_BINARY_GARBAGE | 《民盟宣布解散·公告与政府洽商之经过·通知盟员停止政治活动·一律免除登记可享合法 |
| S13-06 | 20338 | D2_LIBRARY_STAMP | 《民主同盟文獻》 |
| S13-07 | 20463 | D2_LIBRARY_STAMP | 《中國民主同盟言論集》 |
| S13-08 | 16802 | D3_ISSUE_HEADER | 《民憲》第一卷第三期 |
| S13-09 | 16843 | D3_ISSUE_HEADER | 《民憲》第一卷第十二期 |
| S13-10 | 20337 | D4_COVER_TITLE | 《民主同盟文獻》 |
| S13-11 | 20462 | D4_COVER_TITLE | 《中國民主同盟言論集》 |
| S13-12 | 17505 | D5_AD_OR_CARTOON | 《民憲》第二卷第一期 |
| S13-13 | 18463 | D5_AD_OR_CARTOON | 《觀察》第三卷第一至十二期合订本 |
| S13-14 | 16778 | D6_OCR_GARBLED | 《光明報》1948 年1卷1期 |
| S13-15 | 18605 | D6_OCR_GARBLED | 《觀察》第三卷第一至十二期合订本 |
| S13-16 | 20148 | D6_OCR_GARBLED | 时局宣言 |
| S13-17 | 20326 | D6_OCR_GARBLED | 《光明報》1948年1卷12期（1948-08-16） |
| S13-18 | 16714 | D7_SHORT_BODY_CANDIDATE | 《光明報》1949 年2卷1期 |
| S13-19 | 17625 | D7_SHORT_BODY_CANDIDATE | 《民主同盟文獻》1946 |
| S13-20 | 17641 | D7_SHORT_BODY_CANDIDATE | 《民主同盟文獻》1946 |
| S13-21 | 17772 | D7_SHORT_BODY_CANDIDATE | 《民主同盟文獻》1946 |
| S13-22 | 17802 | D7_SHORT_BODY_CANDIDATE | 《民主同盟文獻》另一扫描本 |

## 无 provenance 短页 11 条

| page_id | code | clear_binary | doc_key |
|---:|---|---|---|
| 1650 | D6_OCR_GARBLED | no | `domestic-ocr/NLC:guangmingbao-1948-v1n12-full-ocr` |
| 1775 | D2_LIBRARY_STAMP | no | `domestic-ocr/NLC:minmeng-wenxian-1946-alternate-front-ocr` |
| 1776 | D2_LIBRARY_STAMP | no | `domestic-ocr/NLC:minmeng-wenxian-1946-alternate-front-ocr` |
| 1778 | D4_COVER_TITLE | no | `domestic-ocr/NLC:minmeng-yanlunji-1945-front-ocr` |
| 20623 | D1_BINARY_GARBAGE | yes | `domestic-web/DL-20260802-049` |
| 1486 | D7_SHORT_BODY_CANDIDATE | no | `domestic-ocr/NLC:minmeng-wenxian-1946-early-group:ocr-pilot` |
| 1626 | D7_SHORT_BODY_CANDIDATE | no | `domestic-ocr/NLC:guangmingbao-1948-v1n1-full-ocr` |
| 1690 | D7_SHORT_BODY_CANDIDATE | no | `domestic-ocr/NLC:guangmingbao-1949-v2n12-full-ocr` |
| 1777 | D4_COVER_TITLE | no | `domestic-ocr/NLC:minmeng-wenxian-1946-alternate-front-ocr` |
| 1779 | D2_LIBRARY_STAMP | no | `domestic-ocr/NLC:minmeng-yanlunji-1945-front-ocr` |
| 1780 | D7_SHORT_BODY_CANDIDATE | no | `domestic-ocr/NLC:minmeng-yanlunji-1945-front-ocr` |

## 产出

- `batch13_reocr_recommendations.csv`
- `batch13_human_sample_checklist.csv`
- `batch13_missing_provenance_stubs.csv`
- `batch13_short_pages_ops_report.md`（本文件）

## 迁移（batch13_migrate）

- 为 11 条短页插入 `page_provenance` 桩（citation_ready=0, needs_human_review=1）
- 对 page_id=20623 清空 PNG 伪文本（若仍存在）
- 不跑 OCR、不晋升 citation
