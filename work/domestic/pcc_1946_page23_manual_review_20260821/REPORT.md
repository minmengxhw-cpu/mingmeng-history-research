# 1946 年旧政协文献第 23 页人工核验

## 已核验

- 来源为《政協文獻》1946 年扫描本，PDF 第 23 页，来源 SHA256 与既有 manifest 一致。
- 页图右侧印刷页码可核对为 16。
- 目标标题区域可视觉确认“民盟代表张澜开会词（沈钧儒代）”，与目标地图中的 `zhang-lan-opening` 相符。
- 目标从本页标题处开始；标题上方仍有前置内容，不能把整页 OCR 文字直接归入目标正文。
- 主库已有 page_id 20903 的页级记录，但正文仍未达到 `citation_ready`。

## 保留的限制

本轮只确认页身份、目标标题和印刷页码，没有逐字校读张澜开会词正文。PaddleOCR 输出仍是发现和检索草稿，繁简、异体字及字符误识别风险未消除。第 24 页需要继续核验，确认是否为目标正文的连续页。

状态：`TITLE_AND_PAGE_IDENTITY_HUMAN_VERIFIED_BODY_REVIEW_OPEN`；`citation_ready=false`；未修改 SQLite。

另登记了标题下方开头句的检索片段候选，使用 600 dpi 本地重渲染进行了第二次视觉核对。第二次核对确认该句的字符、分句标点和句末标点，片段级 `quote_safe=true`；整页正文仍未逐字校读，不能扩展为整页或完整开会词：[`FRAGMENT_SECOND_PASS.json`](./FRAGMENT_SECOND_PASS.json)。原始候选记录保留用于审计：[`FRAGMENT_CANDIDATE.json`](./FRAGMENT_CANDIDATE.json)。
