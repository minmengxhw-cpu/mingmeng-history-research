# 《民主周刊》第三卷第十六期合订册范围探针

本轮只做合订册页身份和边界探针，不做整册 OCR、不做正文入库、不把 OCR 或元数据升级为正式引文。

## 已确认

- 合订册 PDF SHA256：`38e7ca88e6b45efca27c7b685fff1ff57c2dc292ca3c1b8972c05994994e8fae`，共 1279 页。
- 合订册第 1190 页视觉上明确为《民主周刊》第三卷第十六期封面/卷首。
- 第 1205 页仍是该卷首之后的正文版面；第 1206 页明确显示“1945 年 增刊 1-3 期”，形成后续分区锚点。
- 因此暂把 1190—1205 记录为 16 页范围候选，与公开 CADAL 单期 16 页数量相符。
- 第 1190 页与单期封面身份一致；对第 1194/1203 页与单期第 5/14 页的视觉抽样尚未确认一一对应，不能用页码偏移公式替代版本关系。
- 第 1199 页新增一个 review-only 内容候选：竖排题名框可确认“闻一多就是我们的……”前缀，PaddleOCR 草稿以 0.8198 置信度识别出“聞一多就是我們的”；续字和正文尚未逐字校读。

## 证据边界

这不是“1190—1205 已经可以直接引用”的结论。单期封面与合订册封面已对齐，但第 1194/1203 页与单期第 5/14 页的直接对应尚未确认；仍未完成逐页版式/印刷页码对齐，也未对第 1205 页作末页校读。第 1206 页是合订册分区页，不等于第三卷第十七期封面。第 1、5、14 页候选文章仍需人工逐字转录后，才能分别决定 `review_only` 或 `citation_ready`。

稳定探针页图和哈希见：

- `data/domestic/raw/public_sources/nlc_bound_volume/issue16_probe_260dpi/pdf-page-1190.jpg`
- `data/domestic/raw/public_sources/nlc_bound_volume/issue16_probe_260dpi/pdf-page-1205.jpg`
- `data/domestic/raw/public_sources/nlc_bound_volume/issue16_probe_260dpi/pdf-page-1206.jpg`

内容候选登记见：

- `work/domestic/democracy_weekly_bound_volume_issue16_content_candidates_20260821/CONTENT_CANDIDATES.json`
- `work/domestic/democracy_weekly_bound_volume_issue16_content_candidates_20260821/REPORT.md`

## 下一步

1. 对照单期第 1、5、14 页与合订册候选页，建立页级版本关系。
2. 校核第 1205 页印刷页码和末页状态。
3. 在人工转录和日期冲突说明完成前，保持正文 `citation_ready=false`，不写入正式库。
4. 对第 1199 页候选获取更适合逐字校读的图像版本；确认完整题名后，再建立独立页级 provenance，不覆盖单期来源。
