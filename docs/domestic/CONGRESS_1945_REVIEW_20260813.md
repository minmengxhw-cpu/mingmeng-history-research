# 1945 年临时全国代表大会页级证据复核

日期：2026-08-13

## 结论

本批次将 1945 年民盟临时全国代表大会的四个页级锚点升级为 `human_verified / citation_ready`，并把政治报告标题页和宣言标题页接入 `domestic-1945-first-congress` 专题导航。它证明的是列出的四个 PDF 页面可由本地扫描件和精确 provenance 回溯，不证明政治报告、宣言全文已经逐页复核，也不证明该公开编纂扫描件就是 1945 年档案馆原件。

## 来源与数据库变更

- 来源文件：`data/domestic/sourcebooks/中国民主同盟历史文献_1941-1949_公开扫描.pdf`
- 来源 SHA256：`257bb7be70abe374be9864ec451b5a4a90e2442ae8c877b15f4e6bbb8bb30be3`
- 复核前正式库 SHA256：`76a60514e1c0d3e3b8bde4b7874d2852d92298312ba88b3318078e6f77603a17`
- 复核四页后、事件导航写入后的正式库 SHA256：`4cd77f5c8256f0fb6828cc1693f9b292057fa8c095640864de9357c41298cd88`
- 回滚备份：`/private/tmp/research_index.sqlite.before_congress_1945_visual_review_20260813.sqlite`、`/private/tmp/research_index.sqlite.before_congress_1945_event_link_20260813.sqlite`
- 复核批次：`work/domestic/congress_1945_review_20260813/`
- 正文未复制到批次或 Git；OCR 仅作为检索辅助，页面视觉复核以渲染页和来源 SHA/页码 provenance 为准。

## 四个页级锚点

| page_id | 文档 | PDF 页 | 印刷页 | 页面事实 | 精确入口 |
| ---: | --- | ---: | ---: | --- | --- |
| 1443 | `MMHIST:political-report-1945` | 101 | 71 | 《中国民主同盟临时全国代表大会政治报告》标题页，日期一九四五年十月十一日 | [PDF 第 101 页](https://www.marxists.org/chinese/pdf/history_of_international/china/mzhtm1.pdf#page=101) |
| 1444 | `MMHIST:political-report-1945` | 117 | 87 | 政治报告后段连续页，可见对民盟历史、独立性与中立性的回顾 | [PDF 第 117 页](https://www.marxists.org/chinese/pdf/history_of_international/china/mzhtm1.pdf#page=117) |
| 1445 | `MMHIST:congress-declaration-1945` | 118 | 88 | 《中国民主同盟临时全国代表大会宣言》标题页，日期一九四五年十月十六日 | [PDF 第 118 页](https://www.marxists.org/chinese/pdf/history_of_international/china/mzhtm1.pdf#page=118) |
| 1446 | `MMHIST:congress-declaration-1945` | 123 | 93 | 宣言结尾页，可见教育部分收束及“谨此宣言” | [PDF 第 123 页](https://www.marxists.org/chinese/pdf/history_of_international/china/mzhtm1.pdf#page=123) |

## 平台接入

`data/domestic/citation_event_links.json` 新增两条保守导航：

1. 政治报告标题页（page_label `101`）；
2. 宣言标题页（page_label `118`）。

导航只提供专题进入点，不改变其他页状态，不把机器 OCR 或目录记录升级成正式引文。

## 当前验收口径

- 正式人工可引用页：`112 → 116`。
- 国内专题页级关联：`514 → 516` 条，覆盖国内物理页 `500 → 502` 个。
- 声明式严格页级专题回链：`14 → 16` 条，覆盖全部 9 个国内专题。
- 总 `research_events`：`2431 → 2433`。
- 来源文件缺失：0；来源 SHA 不匹配：0；SQLite integrity：`ok`；外键违规：0；FTS 未对齐：0。

## 未完成事项

- 仍需获取或核验 1945 年政治报告、宣言的更接近原始档案的版本、馆藏信息、档号和版本关系。
- 若要把两份文件作为全文级研究对象，必须逐页建立原件/页图/哈希/人工复核链；本批次四页不能代替该工作。
- 学术文章仍属于解释层；没有稳定全文、页码/章节和人工复核时，不进入 `citation_ready`。
