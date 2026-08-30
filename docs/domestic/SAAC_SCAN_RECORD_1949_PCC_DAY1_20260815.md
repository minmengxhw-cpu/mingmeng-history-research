# 国家档案局扫描记录：第一届政协第一天会议记录（1949-09-21）

## 来源

- 题名：中国人民政治协商会议第一届全体会议第一天会议记录
- 日期：1949 年 9 月 21 日
- 官方条目页：<https://www.saac.gov.cn/daj/gqzt/content/05/05_18.html>
- 候选 ID：`domestic:SAAC:1949-09-21-06`
- 官方扫描图：3 张，来源路径为 `img/a05/18/01.jpg` 至 `03.jpg`

这是国家档案局公开专题中的扫描图条目，属于可视原件入口；不是经过出版校勘的文字版。页面图像为手写会议记录，适合核对会议时间、地点、出席情况、议程和代表名单等结构性信息。

## 本地与 OCR 资产

- 原图目录：`data/domestic/raw/saac_scans/sec05_05-18/`
- OCR 草稿目录：`work/domestic/saac_1949_pcc_day1_ocr_20260815/`
- OCR：本地 PaddleOCR 3.7.0，PP-OCRv6 medium，CPU
- 页数：3
- 平均置信度：0.8522、0.8384、0.8861
- 原图和 OCR 草稿的逐文件 SHA 见 [扫描 manifest](../../data/domestic/saac_scan_manifest_1949_pcc_day1.json)。

## 正式库状态

- 文档 ID：`1592`
- 页 ID：`20913`、`20914`、`20915`
- 文档键：`domestic-ocr/SAAC:domestic:SAAC:1949-09-21-06`
- 候选与文档已建立双向 provenance 链路。
- 三页已完成页身份、页序和页面边界的人工视觉复核，当前为 `strict_citation`、`citation_ready=1`、`needs_human_review=0`。
- 这里的严格状态只覆盖官方扫描版本、页身份、页序和可重放定位；OCR 仍只进入检索层，不等同于人工校订正文。

## 视觉复核记录（2026-08-15）

- 批次：`saac_1949_pcc_day1_visual_review_20260815`
- 复核页：`20913`、`20914`、`20915`
- 复核范围：题名/日期线索、手写记录格式、物理页序、连续页关系和页面边界；不转录手写正文、人名或数字。
- 批次文件：[BATCH.json](../../work/domestic/saac_1949_pcc_day1_visual_review_20260815/BATCH.json)
- 复核决定：[REVIEW_DECISIONS.json](../../work/domestic/saac_1949_pcc_day1_visual_review_20260815/REVIEW_DECISIONS.json)
- 入库备份：`/Users/cheer/Documents/mm agent/formal-db-backups/research_index.sqlite.saac-1949-day1-visual-20260815.pre.bak`
- 复核后数据库 SHA-256：`a2e845460552ffaf09219709030375ad753661a7004378cbeb63e263dd7172e7`

## 研究边界

本批资料已经解决“官方扫描图是否可取得、是否可按页定位”的问题，并完成了页级引用门禁；但没有解决“逐字转录可引用”或“1949 年完整会议档案已收齐”的问题。下一步仍应以原图为准单独校勘人名、数字、议程和正文；不得把 OCR 文本中的疑似错字当作史实。

## 可复现入口

```bash
python3 scripts/domestic/import_saac_scan_review_20260815.py --dry-run
```

脚本默认只读；正式导入必须提供当前正式库 SHA 和新的备份路径。
