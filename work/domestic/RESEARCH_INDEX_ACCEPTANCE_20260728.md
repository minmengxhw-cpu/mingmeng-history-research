# 国内盟史资料阶段验收（2026-07-28）

## 当前库状态

- documents：1003；pages：1532；page_fts：1532
- 国内文献（source_platform=domestic）：142
- 《观察》封面/目录 review-only 入库：12 期文档、24 页
- 候选：accepted 679；needs_human_review 10
- integrity_check：ok
- pages_without_fts：0；fts_without_pages：0
- 历史分类外键孤儿：15（遗留问题，本轮未扩增）

## 核心证据集

- 40 条：1941=8, 1944-1945=10, 1946=5, 1947=4, 1948-1949=8, 1942-1943=5
- citation_ready=true：0；全部仍需原件/页码/人工复核门禁。

## 《观察》

- 已确认并切分 12 期，覆盖卷3第1—12期；首轮封面/目录 OCR 产出 24 个 Markdown，并以 review-only 方式入库。
- 全刊正文尚未导入正式库；原始 PDF 与派生 issue PDF 均保留 SHA256 溯源。

## 结论

- 数据库完整性与 FTS 对齐通过。
- 1942—1943 已从“空白”变为 5 条目录级核心入口，但还不能当作全文一手证据。
- 下一道门槛是补齐 1942—1943 原件，以及对《观察》首轮 OCR 进行抽样人工复核后再决定是否扩大正文 OCR。
