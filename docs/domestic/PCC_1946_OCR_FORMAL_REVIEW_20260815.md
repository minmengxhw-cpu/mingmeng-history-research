# 1946 年《政協文獻》定向页 OCR 检索层验收

日期：2026-08-15

## 本轮完成

对已完成标题/版面视觉确认的 9 个定向页执行了本地 PaddleOCR 3.7.0 小批：

- PDF 页：23、24、52、62、63、101、125、126、206；
- 原始 PDF SHA256：`4b45976ffdea727f0e26f79c4cb2688e01093d5d7901103c17d99823e7e4d50f`；
- OCR 平均置信度范围：约 `0.8341—0.9050`；
- 先经过隔离 staging：1 个文档、9 个页、9 个 FTS 记录，完整性和外键检查通过；
- 再进入正式 SQLite：新增 1 个国内文档、9 个页、9 条 `page_provenance`、9 条专题导航回接；
- 正式库新增页 ID：`20903—20911`；
- 正式库最新 SHA256：`ea2e0e5d4f329621f2e4baec7c531818f53428cd5457752cc20bddfb42e62b0b`。

## 证据边界

这本《政協文獻》属于 L2 汇编/重印层，不是已经确认的独立政协会议原始档案。因此 9 页全部保持：

- `review_status=review_only`；
- `citation_ready=0`；
- `needs_human_review=1`；
- 专题来源地图状态为 `review_only`；
- 只能用于本地检索、标题定位、页级导航和后续人工复核；
- 不得用来关闭“1946 年旧政协正式会议档案、代表发言/提案和完整日期轴”这一 P0 缺口。

## 可复现资产

- 页级 OCR manifest：`work/domestic/pcc_1946_sourcebook_ocr_20260814/PAGE_OCR_MANIFEST.jsonl`；
- staging 导入报告：`work/domestic/pcc_1946_sourcebook_ocr_20260814/APPLY_REPORT.json`；
- 正式库导入报告：`work/domestic/pcc_1946_sourcebook_ocr_20260814/FORMAL_IMPORT_APPLY.json`；
- 专题回接报告：`work/domestic/pcc_1946_sourcebook_ocr_20260814/EVENT_LINK_APPLY.json`；
- 正式库验证：`verify_research_index_manifest.py` 通过，完整性、外键、页表/FTS 对齐和来源文件 SHA 均通过。

原始 PDF、页图和 OCR 正文仍是本地研究资产，不进入 GitHub；公开研究包只输出元数据、来源 SHA、页号和复核状态。

## 下一步

1. 对 9 页逐页人工核对 OCR 文本与页图，记录人审说明；
2. 只在标题、正文边界、页码和来源版本全部确认后，决定是否保留为可引用的汇编页；
3. 继续寻找独立会议记录、提案原件和代表身份材料；
4. 将新发现的独立来源放入 `primary` 层，不把本批 L2 页提升为一手闭环。
