# Batch 7 · 国内短页面质量审计（text < 120）

- 正式库只读路径：`/Users/cheer/Documents/mm agent/mingmeng-history-research/data/research_index.sqlite`
- 短页面总数：**220**
- 涉及文档：**76**
- 需人工影像抽检：**214**
- 门禁原则：本批全部预设 `citation_eligible=no`，直至人工核验完成。

## 分层结果

| 分层 | 数量 |
|---|---:|
| Q0_EMPTY | 6 |
| Q3_OCR_SUSPECT | 117 |
| Q4_FRAGMENT | 1 |
| Q5_SHORT_REVIEW | 96 |

## hit_type 分布（Top 20）

| hit_type | 数量 |
|---|---:|
| domestic_page_ocr | 142 |
| saac_page_ocr | 67 |
| domestic_ocr_pilot | 10 |
| domestic_web | 1 |

## 短页面最多的文档（Top 20）

| doc_key | 数量 |
|---|---:|
| domestic-page/SRC-257bb7be70 | 35 |
| domestic-page/SRC-088458899f | 24 |
| domestic-page/NLC511-027032013012333-19131 | 12 |
| domestic-page/NLC416-01jh004281-12557 | 9 |
| domestic-page/SSID-13679264 | 9 |
| domestic-ocr/S3:domestic:NLC:minmeng-yanlunji-1945-whole | 7 |
| domestic-page/NLC511-027032016010761-42571 | 7 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p05-dde02 | 6 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p05-dde05-i3 | 6 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p03-dde03-f1 | 5 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p03-dde04-f1 | 5 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p03-dde02-f1 | 4 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p06-dde03-f1 | 4 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p06-dde08-f1 | 4 |
| domestic-ocr/NLC:minmeng-wenxian-1946-alternate-front-ocr | 3 |
| domestic-ocr/NLC:minmeng-yanlunji-1945-front-ocr | 3 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p01-dde14 | 3 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p01-dde20 | 3 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p01-dde21 | 3 |
| domestic-ocr/SAAC:domestic:SAAC:51koukou-p05-dde01-i3 | 3 |

## 处置规则

1. Q0/Q3/Q4/Q5 在人工对照影像前禁止引用。
2. Q1 仅作目录线索，不得冒充全文。
3. Q2 可保留版式/结构用途，但不作为正文证据。
4. 本批未执行 OCR、未修改页面、未写正式 SQLite。
