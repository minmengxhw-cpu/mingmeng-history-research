# 国内 OCR 检索草稿入库验收（2026-07-28）

## 批次范围

- 来源：本机已通过 SHA256、页数和 OCR chunk 存在性核对的规范化 manifest。
- 入库记录：52 个来源、67 个 OCR chunk 检索单元。
- 对应物理范围：3338 页；数据库中的 67 页是 chunk 检索单元，不等同于 3338 个物理页。
- 7 个低置信度来源未自动入库：4 份官方公报、1941 年《新华日报》一条、两张大公报问题图。
- 所有新记录保持 `citation_ready=false`、`needs_human_review=true`，并标注 `page_scope=ocr_chunk_not_physical_page`。

## SQLite 验收

| 指标 | 入库前 | 入库后 |
|---|---:|---:|
| documents | 1003 | 1055 |
| pages | 1532 | 1599 |
| page_fts | 1532 | 1599 |
| 国内文档 | 142 | 194 |

- `PRAGMA integrity_check`：`ok`
- `pages` 缺失 FTS：0
- FTS 孤立行：0
- 自动备份：`data/research_index.sqlite.domestic-full-draft-20260728.pre.bak`
- dry-run：`PASS`
- 入库后覆盖对账：61 个来源、3878 个物理页均有本地 OCR 草稿；SQLite 当前为 539 个检索单元，仍有 3369 个物理页需要页级正式化。

## 运行时回归

- `/`、`/domestic`、`/domestic/review`、`/dashboard`：均返回 200。
- `/search?q=张澜&platform=domestic`：返回 200，并能看到 `OCR检索草稿` 结果。
- `/search?q=民主政治&platform=domestic`：返回 200，并能检索国内 OCR 草稿结果。

## 未完成门禁

这一步只完成“可检索草稿入库”，没有把 OCR 变成引用级正文。下一步仍需：

1. 对 67 个 chunk 建立物理页级映射，避免把整卷草稿当成单页引用。
2. 对关键人名、日期、版面边界进行原图人工复核。
3. 逐页通过 `pages/page_fts` 对齐和证据等级门控后，才允许 `citation_ready=true`。
4. MMDA 1942—1943 三条 P1 原件仍等待授权登录后取得正文。
