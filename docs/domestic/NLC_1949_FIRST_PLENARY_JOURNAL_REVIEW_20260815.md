# 1949 年政协一届全体会议会刊：国内一手资料路线复核

## 结论

本轮取得并核验了一份高价值的 1949 年正式会议出版物扫描：

- 题名：中国人民政治协商会议第一届全体会议会刊
- 出版/编印单位：中国人民政治协商会议第一届全体会议新闻处
- 来源链：国家图书馆馆藏标识，经 Wikimedia Commons 提供公开扫描入口
- 本地文件：`data/domestic/raw/public_sources/nlc_1949_first_plenary_conference_journal.pdf`
- 文件规模：276 页，17,174,315 bytes
- SHA256：`20069c88dd8520e034f47beb614bca4c1c86ae6b8baf41aaf1988a13f95c7e4a`

公开入口：[Commons 文件页](https://commons.wikimedia.org/wiki/File:NLC416-18jh000828-104705_%E4%B8%AD%E5%9C%8B%E4%BA%BA%E6%B0%91%E6%94%BF%E6%B2%BB%E5%8D%94%E5%95%86%E6%9C%83%E8%AD%B0%E7%AC%AC%E4%B8%80%E5%B1%86%E5%85%A8%E9%AB%94%E6%9C%83%E5%88%8A.pdf)。本地元数据快照见 [`nlc_1949_first_plenary_conference_journal_20260815.json`](../../data/domestic/metadata_snapshots/nlc_1949_first_plenary_conference_journal_20260815.json)。

## 已做页级视觉检查

| PDF 页 | 发现 | 当前状态 |
|---:|---|---|
| 1 | 会刊封面，标明 1949 年、第一期至第十二期 | `review_only` |
| 17 | 第一届全体会议开幕式程序，日期 1949-09-21 | `review_only` |
| 30 | 主席团名单；可见张澜、沈钧儒、章伯钧、张东荪、史良、沙千里等人物 | `review_only` |
| 31–32 | 第一届全体会议议事规则 | `review_only` |
| 220 | 第一届全体会议宣言（草案），日期 1949-09-30 | `review_only` |
| 242–243 | 正式会议刊物中的电文、纪念碑奠基和会议影像语境 | `review_only` |

## 使用边界

这份会刊能补强“1949 年新政协/一届全体会议存在正式会议出版物记录”这一层，并提供开幕程序、主席团名单、议事规则和宣言草案的页级追索入口。但它目前不能单独证明：

1. 连续的筹备会议记录已经完整取得；
2. 1949 年完整代表名册已完成逐人转录和民盟成员对位；
3. 民盟代表的发言、场次、版本和会议页已经完成闭环。

因此本轮只写入元数据和来源地图，不写入 SQLite 正式正文，不生成 OCR 正文，也不把专题状态改成 `primary_evidence_closed`。

Wikisource 的同名索引和页面可作发现、页码对读和人工复核辅助；页面 30 已标示校对，页面 220 仍未校对。转录层不能替代本地 PDF 页面作为正式证据，尤其不能直接复制未校对正文。[Wikisource 索引](https://zh.wikisource.org/wiki/Index:NLC416-18jh000828-104705_%E4%B8%AD%E5%9C%8B%E4%BA%BA%E6%B0%91%E4%B8%BB%E6%94%BF%E5%8D%94%E5%95%86%E6%9C%83%E8%AD%B0%E7%AC%AC%E4%B8%80%E5%B1%86%E5%85%A8%E9%AB%94%E6%9C%83%E5%88%8A.pdf)、[页面 30](https://zh.wikisource.org/wiki/Page:NLC416-18jh000828-104705_%E4%B8%AD%E5%9C%8B%E4%BA%BA%E6%B0%91%E6%94%BF%E6%B2%BB%E5%8D%94%E5%95%86%E6%9C%83%E8%AD%B0%E7%AC%AC%E4%B8%80%E5%B1%86%E5%85%A8%E9%AB%94%E4%BC%9A%E8%AD%B0%E6%9C%83%E5%88%8A.pdf/30)、[页面 220](https://zh.wikisource.org/wiki/Page:NLC416-18jh000828-104705_%E4%B8%AD%E5%9C%8B%E4%BA%BA%E6%B0%91%E6%94%BF%E5%8D%94%E5%95%86%E6%9C%83%E8%AD%B0%E7%AC%AC%E4%B8%80%E5%B1%86%E5%85%A8%E9%AB%94%E6%9C%83%E5%88%8A.pdf/220)。

## 下一步

按“原件身份 → 页级 provenance → 人工复核 → 正式库/FTS → 专题门禁”的顺序处理选定页；先做第 30 页主席团名单和第 17 页开幕程序的页级核对，再决定是否扩展到连续页。任何 OCR 仍只能作为检索草稿，不能自动升级为可引用正文。
