# 1946 年《政協文獻》定向页 OCR 与页级视觉复核验收

日期：2026-08-15

## 本轮完成

对已完成标题/版面视觉确认的 9 个定向页执行了本地 PaddleOCR 3.7.0 小批：

- PDF 页：23、24、52、62、63、101、125、126、206；
- 原始 PDF SHA256：`4b45976ffdea727f0e26f79c4cb2688e01093d5d7901103c17d99823e7e4d50f`；
- OCR 平均置信度范围：约 `0.8341—0.9050`；
- 先经过隔离 staging：1 个文档、9 个页、9 个 FTS 记录，完整性和外键检查通过；
- 再进入正式 SQLite：新增 1 个国内文档、9 个页、9 条 `page_provenance`、9 条专题导航回接；
- 正式库新增页 ID：`20903—20911`；
- 随后对 9 页逐页查看本地 270dpi 渲染图，确认标题页、连续页和页末条目切换边界；视觉复核不读取 OCR 正文作依据；
- 9 页页级审核决策全部通过 dry-run，并写入正式库的页级 `human_verified` 状态；
- 正式库最新 SHA256：`d0c4b40a523d3a2b1dc963e0ba3d8cde74e522331922f74bb73ac86efb104b89`；正式库严格页级人工复核计数由 201 增至 210；
- 写入前备份：`formal-db-backups/research_index.sqlite.pcc-1946-visual-20260815.pre.bak`。

## 证据边界

这本《政協文獻》属于 L2 汇编/重印层，不是已经确认的独立政协会议原始档案。因此 9 页现在保持：

- `review_status=human_verified`；
- `citation_ready=1`；
- `needs_human_review=0`；
- 专题来源地图状态为 `strict_citation`；
- 可用于复现汇编版本、PDF/印刷页号、页界和来源哈希的页级引用定位；
- OCR 仍只是检索草稿，不能据此声称正文已经逐字校订；
- 不得用来关闭“1946 年旧政协正式会议档案、代表发言/提案和完整日期轴”这一 P0 缺口。

## 可复现资产

- 页级 OCR manifest：`work/domestic/pcc_1946_sourcebook_ocr_20260814/PAGE_OCR_MANIFEST.jsonl`；
- staging 导入报告：`work/domestic/pcc_1946_sourcebook_ocr_20260814/APPLY_REPORT.json`；
- 正式库导入报告：`work/domestic/pcc_1946_sourcebook_ocr_20260814/FORMAL_IMPORT_APPLY.json`；
- 专题回接报告：`work/domestic/pcc_1946_sourcebook_ocr_20260814/EVENT_LINK_APPLY.json`；
- 视觉复核批次：`work/domestic/pcc_1946_sourcebook_visual_review_20260815/BATCH.json`、`REVIEW_DECISIONS.json`、`APPLY_REPORT.json`；
- 正式库验证：`verify_research_index_manifest.py` 通过，完整性、外键、页表/FTS 对齐和来源文件 SHA 均通过。

原始 PDF、页图和 OCR 正文仍是本地研究资产，不进入 GitHub；公开研究包只输出元数据、来源 SHA、页号和复核状态。

## 下一步

1. 继续寻找独立会议记录、提案原件和代表身份材料；
2. 将新发现的独立来源放入 `primary` 层，不把本批 L2 页提升为一手闭环；
3. 对 OCR 正文如需逐字引用，另行建立逐页正文复核批次，不把本次页级视觉复核误当成全文校勘。
