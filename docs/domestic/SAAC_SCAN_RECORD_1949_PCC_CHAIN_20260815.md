# 国家档案局 1949 年新政协核心链条扫描记录（2026-08-15）

## 结论

本批次把国家档案局“从「五一口号」到开国大典档案文献专辑”中的 3 个官方专题页、8 张官方扫描图纳入国内研究平台：

- 中国人民政治协商会议第一届全体会议主席团第一次会议纪要（1949-09-21）：3 页，正式文档 ID `1593`，页面 ID `20916–20918`。
- 谭平山关于中国人民政治协商会议筹备会第二小组工作的报告（1949-09-22）：2 页，正式文档 ID `1594`，页面 ID `20919–20920`。
- 周恩来关于中国人民政治协商会议共同纲领草案的起草经过及其特点的报告（1949-09-22）：3 页，正式文档 ID `1595`，页面 ID `20921–20923`。

3 个候选均已与正式文档关联，8 个页面均已写入全文检索和页级 provenance。所有页面保持 `review_only`、`citation_ready=0`，本批次不构成可直接引用的转录文本。

## 官方入口

- [主席团第一次会议纪要（1949-09-21）](https://www.saac.gov.cn/daj/gqzt/content/05/05_20.html)
- [谭平山关于筹备会第二小组工作的报告（1949-09-22）](https://www.saac.gov.cn/daj/gqzt/content/05/05_23.html)
- [周恩来关于共同纲领草案起草经过及特点的报告（1949-09-22）](https://www.saac.gov.cn/daj/gqzt/content/05/05_24.html)

清单同时登记每张官方图片 URL、下载后的 SHA-256、OCR 草稿 SHA-256、行数、平均置信度和本地路径；权威清单为：
`data/domestic/saac_scan_manifest_1949_pcc_chain_20260815.json`。

## 本地材料与 OCR 边界

原始扫描图位于：
`data/domestic/raw/saac_scans/sec05_05-20/`、`sec05_05-23/`、`sec05_05-24/`。

OCR 草稿位于：
`work/domestic/saac_1949_pcc_chain_ocr_20260815/`。

OCR 由本地 CPU 上的 PaddleOCR 3.7.0（`PP-OCRv6_medium_det + PP-OCRv6_medium_rec`）生成，仅作检索、定位和后续人工复核底稿。05_24 的原始扫描图文字方向为横置页面，使用派生的 270° 旋转图生成 OCR；原始官方图不变，清单明确记录 `ocr_rotation_degrees=270`。该页第 3 张图平均置信度约 `0.5190`，应优先人工核对。

## 导航层

8 个页面已追加到专题 `domestic-1949-new-pcc`。导航事件摘要只说明“官方扫描图 OCR 检索入口、正文与人名数字待人工复核”，不复制 OCR 正文，也不把专题关联误当作事实确认。

## 可引用性与下一步

当前可引用对象是官方专题页和官方图片入口；平台中的 OCR 文本不能直接作为正式引文。下一阶段应按页进行人工图文校对，记录校对者、校对时间、差异说明和引用页码，完成后再由独立门禁决定是否将具体页面提升为 `citation_ready=1`。低置信度页面不得因模型输出完整而自动提升。

## 机器记录

- 批次：`saac-scan-chain-20260815`
- 备份（入库前）：`<local-user>/<local-checkout>/formal-db-backups/research_index.sqlite.saac-chain-20260815.pre.bak`
- 备份（导航追加前）：`<local-user>/<local-checkout>/formal-db-backups/research_index.sqlite.saac-chain-events-20260815.pre.bak`
- 入库后正式库 SHA-256：`7ea39b1ae62ceb8daae8c434224215382fe0b85dba57906606a75e42ebe7271a`
- 自动校验：SQLite integrity check 通过；外键违规 0；新增页面缺 FTS 0；新增 provenance 8；citation-ready 页面 0。
