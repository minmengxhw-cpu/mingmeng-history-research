# 《民憲》第一卷第九期文章页级复核记录

## 本轮结论

本轮只处理一项可独立闭环的国内资料：国家图书馆公开扫描的《民憲》第一卷第九期（1944-11-20）中《民主政治與非民主政治》文章页组。

- PDF 第 16—19 页、印刷页 13—16：已完成原图视觉复核，页序、刊期、文章连续性和页位可作为严格页级引用。
- PDF 第 20 页、印刷页 17：原图显示文章与下一篇文章存在版面交界；未完成栏位级切分，继续保留 `review_only`，不纳入严格文章页组。
- 文章的证据等级是同期公共论述的 L1 原刊页，不是 1944 年改组会议记录、改名决定或组织内部正式文件。
- 1944 年改组/更名的主证据缺口仍然开放；本轮没有关闭该缺口，也没有把同期政论升级为改组原件。

## 来源与边界

- 来源文件：`data/domestic/press_scans/NLC404-00J001436-85450_民憲_第一卷第九期.pdf`
- 来源 SHA256：`b6e123c4d90e4b2b596a61e70758f3d0be22cbfbf63ee6ac7853f682de62d5df`
- 正式库页号：`17291`—`17295`
- 严格引用页：`17291`—`17294`
- 交界待复核页：`17295`

页级来源地图见 [`1944_reorganization_source_map.json`](../../data/domestic/1944_reorganization_source_map.json)，专题证据链见 [`topic_evidence_chain.json`](../../data/domestic/topic_evidence_chain.json)。

## 正式库变更

已在备份、精确 SHA 门禁和 SQLite 完整性检查通过后，向 `research_events` 增加 4 条专题导航关联，并将第 20 页正式库复核状态校正为 `review_only`。关联和状态校正只保存来源定位与边界说明，不复制正文，不改变 OCR 层，也没有把第 20 页提升为严格引用。

- 严格引用页总数：`216 → 220`
- 新增事件导航关联：`4`
- 主证据闭环：仍为 `9` 个专题开放、`0` 个专题关闭
- 应用前数据库 SHA256：`5a7237115bfc0efbd600e6a2030aef053923a96dadb21b984229b412aba62cdf`
- 事件关联应用后数据库 SHA256：`2859cc3a0070954715100b4dd523bfb12da92fe071a623e9148e2836f9b9228a`
- 边界状态校正后数据库 SHA256：`75312b9c1cfe7d8978f64c572b4c32b7ab443fb507eabfd3b2fce47031d2109e`
- 备份文件：`formal-db-backups/research_index.sqlite.before_minxian_v1n9_event_links_20260816.sqlite`、`formal-db-backups/research_index.sqlite.before_minxian_v1n9_boundary_review_20260815.sqlite`

## 下一步

下一步不是继续扩大 OCR，而是沿 `data/domestic/primary_gap_closure_matrix.json` 中的 P0 目标追索 1944 年改组会议记录、改名决定和组织内部正式文件；同期刊物文章只作为公共论述与时间线交叉证据。对 PDF 已有可靠电子版的资料继续保留原件和页级 provenance，避免重复 OCR。
