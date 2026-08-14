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
- 三页均为 `review_only`、`citation_ready=0`、`needs_human_review=1`。
- OCR 只进入检索层，不等同于人工校订正文。

## 研究边界

本批资料已经解决“官方扫描图是否可取得、是否可按页检索”的问题，但没有解决“逐字可引用”的问题。下一步应以原图为准人工复核人名、数字、议程和页码；复核前不得把 OCR 文本中的疑似错字当作史实。

## 可复现入口

```bash
python3 scripts/domestic/import_saac_scan_review_20260815.py --dry-run
```

脚本默认只读；正式导入必须提供当前正式库 SHA 和新的备份路径。
