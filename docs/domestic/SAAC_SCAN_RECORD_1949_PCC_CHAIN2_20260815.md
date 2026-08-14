# 国家档案局 1949 年政协核心链条续批记录（2026-08-15）

## 结论

本批次继续沿同一官方专题页补入 3 份材料、7 张官方扫描图：

- 主席团常委会第一次会议记录（1949-09-22）：2 页，正式文档 ID `1596`，页面 ID `20924–20925`。
- 第一届全体会议会刊第二期（1949-09-22）：2 页，正式文档 ID `1597`，页面 ID `20926–20927`。
- 第一届全体会议第三天会议记录（1949-09-23）：3 页，正式文档 ID `1598`，页面 ID `20928–20930`。

3 个候选均在入库前已通过记录级准入；7 个页面均已写入 SQLite、FTS 和页级 provenance，并与专题 `domestic-1949-new-pcc` 建立导航关联。全部保持 `review_only`、`citation_ready=0`。

## 官方入口

- [主席团常委会第一次会议记录（05_27）](https://www.saac.gov.cn/daj/gqzt/content/05/05_27.html)
- [第一届全体会议会刊第二期（05_29）](https://www.saac.gov.cn/daj/gqzt/content/05/05_29.html)
- [第一届全体会议第三天会议记录（05_39）](https://www.saac.gov.cn/daj/gqzt/content/05/05_39.html)

每张原图的官方图片 URL、SHA-256、OCR 草稿路径、OCR SHA-256、行数和平均置信度均记录在：
`data/domestic/saac_scan_manifest_1949_pcc_chain2_20260815.json`。

## 本地原件和 OCR

原始扫描图位于：

- `data/domestic/raw/saac_scans/sec05_05-27/`
- `data/domestic/raw/saac_scans/sec05_05-29/`
- `data/domestic/raw/saac_scans/sec05_05-39/`

OCR 草稿位于：
`work/domestic/saac_1949_pcc_next_ocr_20260815/`。

处理引擎为本机 CPU 上的 PaddleOCR 3.7.0（`PP-OCRv6_medium_det + PP-OCRv6_medium_rec`），只用于检索和定位。平均置信度范围为 `0.7817–0.8893`；05_29 第 1 页和 05_39 第 2 页置信度相对较低，人工复核优先级更高。原始官方图片没有旋转或覆盖修改。

## 证据边界

官方扫描图是原件入口，OCR 不是正式转录。页面文字、人名、数字和会议记录内容均未逐字人工复核，因此本批次不提升任何引用门禁。专题事件索引只写入不含 OCR 正文的安全导航摘要，不把导航关系当作事实确认。

## 机器记录

- 批次：`saac-scan-chain2-20260815`
- 入库前数据库备份：`/Users/cheer/Documents/mm agent/formal-db-backups/research_index.sqlite.saac-chain2-20260815.pre.bak`
- 导航追加前数据库备份：`/Users/cheer/Documents/mm agent/formal-db-backups/research_index.sqlite.saac-chain2-events-20260815.pre.bak`
- 入库和导航完成后正式库 SHA-256：`3fea4b32b10bde60f0017fb19918e3f90bb4220872932df3beafd5bfc0b1e8f8`
- 自动校验：SQLite integrity check 通过；外键违规 0；新增页面缺 FTS 0；新增 provenance 7；新增 citation-ready 页面 0。
