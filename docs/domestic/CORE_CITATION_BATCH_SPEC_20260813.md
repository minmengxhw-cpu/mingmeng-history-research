# 国内核心引用批次规范

日期：2026-08-13

## 目的

国内资料目前已经足够支撑一个可操作的核心样板，但正式引用页仍必须逐页对照原 PDF 或原图。这个批次的任务是把“值得优先核对的资料”固定成一份可重算、可审计、不会把 OCR 误报成正式引文的队列。

生成命令：

```bash
python3 scripts/domestic/build_core_citation_batch_20260813.py
```

默认输出到 `work/domestic/core_citation_batch_20260813/`。该目录属于本地工作产物，不提交正文原件，也不写入主库。

## 选择规则

- 主体只选 `domestic_candidates.review_status=accepted` 且有效真实性等级为 `L0/L1/L2` 的候选；另外纳入已有本地 PDF、但尚未完成候选关联的 `domestic_ocr_pilot` 试点对象，单独标记为 `selection_basis=file_backed_ocr_pilot`，不能把它们误读为已接受候选。
- 必须能回接到正式库中的 `documents/pages`，并至少有一页物理页记录。
- 首轮尽量覆盖 `data/domestic/event_coverage.json` 的九个国内专题，再按等级、候选事件关联、页级 provenance、原图路径和可读文本量补齐。
- 默认目标为 20–30 篇、100–200 页；如果数据库变化导致超出范围，报告会显式给出提示，不静默伪装成达标。
- 选择结果只包含标题、日期、候选 ID、专题、页码和来源元数据，不复制正文；试点对象的候选 ID 可以为空，但必须有本地来源文件和 SHA256 记录。

## 页级验收门槛

每一页都先保持 `review_gate=hold_until_human_source_comparison`，即使来源 SHA256 已匹配，也不自动变成正式引用。人工复核至少要确认：

1. 原 PDF/原图确实存在且与数据库记录一致；
2. 文档标题、日期、形成者和页面/版面边界一致；
3. `physical_page_no`、印刷页码或 PDF 页码可以让第三方回到原件；
4. OCR 只是检索和阅读辅助，缺字、错字、跨页和文章边界已经记录；
5. 平台证据复核页写入不少于 12 个字符的人工说明后，才可以考虑 `human_verified`。

`page_image_kind=ocr_or_text` 的记录不能视作原图；它们需要继续寻找原 PDF/扫描图。`citation_ready` 由人工门禁控制，批次生成器不会修改它。当前批次的 101 个精确 PDF 页已由授权代理完成视觉复核并写入正式门禁；7 个范围锚点和 92 个 OCR-only 页仍未升级。

## 交付物

本地生成目录包含：

- `BATCH.json`：数据库 SHA256、选择统计、专题覆盖、页级来源审计和人工门禁状态；不含正文。
- `DOCUMENTS.csv`：文档级批次清单。
- `PAGES.csv`：页级来源、页码、OCR provenance 和 SHA256 核验结果。
- `README.md`：复核顺序和下一步说明。

后续闭环分三步：先核对本批次，再只把有明确原件定位的页面送入平台复核页，最后重新生成 manifest、SQLite integrity、FTS 对齐和平台回归报告。没有原件的条目继续保留为待核或缺口，不因 OCR 数量增长而升级。
