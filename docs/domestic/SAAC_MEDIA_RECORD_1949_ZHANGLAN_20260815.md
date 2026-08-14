# 国家档案局官方媒体记录：张澜政协讲话（1949-09-21）

## 记录范围

本记录对应国家档案局“从『五一口号』到开国大典档案文献专辑”中的条目：

- 题名：中国民主同盟主席张澜在中国人民政治协商会议第一届全体会议上的讲话
- 日期：1949 年 9 月 21 日
- 官方条目页：<https://www.saac.gov.cn/daj/gqzt/content/05/05_11.html>
- 官方媒体地址：<https://www.saac.gov.cn/daj/gqzt/sp/5-11.mp4>
- 候选 ID：`domestic:SAAC:1949-09-21-05`

官方条目页当前提供的是讲话视频入口，而不是逐页扫描件或公开逐字稿。因此本次按“官方媒体原件”处理，没有把它误导入为 OCR 正文。

## 本地资产与正式库

- 本地媒体：`data/domestic/raw/saac_media/SAAC-1949-09-21-zhanglan-5-11.mp4`
- 文件大小：17,841,248 bytes
- SHA256：`474c4e44f04b031c99b3e95cb2ff71d2f964bc75b5dae39c88461d4c269f33f7`
- 技术信息：166.229002 秒；H.264 856×480；AAC 44.1 kHz 双声道
- 正式文档 ID：`1591`
- 正式页 ID：`20912`
- 正式库记录：`domestic-media/SAAC:domestic:SAAC:1949-09-21-05`
- 入库后正式库 SHA256：`06ff37956dcdb2bccc0831045a9055fb0d023dedd6122c83c5564fe63692ae6b`
- 入库前备份：`/Users/cheer/Documents/mm agent/formal-db-backups/research_index.sqlite.saac-media-20260815.pre.bak`

候选与文档已双向关联，页级 FTS 与 `page_provenance` 已建立。媒体页保持 `review_only`、`citation_ready=0`、`needs_human_review=1`，并明确标注 `transcript_status=not_acquired`。

## 使用边界

当前记录可以支持来源发现、官方媒体观看、题名/日期/形成者核对和检索定位；它不能代替逐字稿、扫描页或人工核听。后续若取得官方文字稿，或完成可追溯的人工核听与时间码记录，应新增转写版本并保留本媒体原件，不覆盖本记录。

## 可复现入口

```bash
python3 scripts/domestic/import_saac_media_metadata_20260815.py --dry-run
```

该脚本默认只读；正式写入需要显式提供数据库当前 SHA 和新的备份路径。原始视频由本地 `data/domestic/raw/` 忽略规则保管，不提交到 Git。
