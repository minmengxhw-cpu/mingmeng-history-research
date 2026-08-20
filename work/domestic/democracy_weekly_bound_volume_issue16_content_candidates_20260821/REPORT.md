# 《民主周刊》第十六期合订本内容候选登记

## 结论

本轮只登记 1 个内容发现候选：合订册 PDF 第 1199 页。页面右侧竖排题名框可人工确认“闻一多就是我们的……”前缀；本地 PaddleOCR 草稿也识别出“聞一多就是我們的”，置信度 0.8198。

续字、完整题名、正文、印刷页码和文章边界尚未人工逐字确认。因此本记录保持 `review_only`，不把 OCR 草稿当作一手正文，不把该页强行对应到 CADAL 单期第 5 页或第 14 页，也不写入正式 SQLite 页级记录。

## 证据边界

- 合订本原始 PDF：`data/domestic/grok_cycle_0006_20260801/pdf/commons_NLC_民主周刊.pdf`
- 260 dpi 稳定探针图：`data/domestic/raw/public_sources/nlc_bound_volume/issue16_probe_260dpi/pdf-page-1199.jpg`
- 600 dpi 高分辨率探针图：`data/domestic/raw/public_sources/nlc_bound_volume/issue16_probe_600dpi/pdf-page-1199.jpg`，SHA256：`71f0f2eea48e14aafd3431e39a0841473182ab0913cd312ab063be77f823ed0b`
- 140 dpi 页身份图：`data/domestic/raw/public_sources/nlc_bound_volume/issue16_page_identity_140dpi/issue16-1199.jpg`
- OCR 草稿：`work/domestic/democracy_weekly_issue16_bound_ocr_140dpi_20260821/issue16-1199.ocr.md`
- 600 dpi 重渲染已完成并通过哈希核验，但原始扫描噪声仍使题名续字达不到逐字人工确认标准；机器识别文本只用于发现候选，不能单独支持正式引文。

## 下一步

1. 获取或生成更适合逐字校读的页面版本，确认题名续字。
2. 核对该页的印刷页码、栏目边界和作者信息。
3. 与 CADAL 单期版本做标题/版式/页码三重对照；确认后再建立页级版本关系。

状态：`REVIEW_ONLY_CONTENT_CANDIDATE`；`citation_ready=false`；`formal_db_written=false`。
