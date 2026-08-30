# 1947 年民盟组织危机同期报刊页级证据复核

日期：2026-08-13

## 结论

本批次将 1947 年 11 月民盟解散前后两页《大剛報》报道，以及《观察》第 3 卷第 11 期三页相关声明/评论升级为 `human_verified / citation_ready`。其中四页接入 `domestic-1947-illegal-dissolution` 专题导航，另保留一页“人身自由的保障问题”作为法治语境证据。它们是同期报刊扫描页，不等同于民盟公告原件、政府公报全文或整期报刊已经逐页核验。

## 来源与数据库变更

- 《大剛報》1947 年 11 月 4 日：`data/domestic/press_scans/NLC1080-00N001037-7604_大剛報_1947年11月04日.pdf`
- 11 月 4 日来源 SHA256：`5176d9591d915124572f7824e3131a1ed682a25cc637b03720fae7a87ee883cb`
- 《大剛報》1947 年 11 月 6 日：`data/domestic/press_scans/NLC1080-00N001037-7606_大剛報_1947年11月06日.pdf`
- 11 月 6 日来源 SHA256：`9b4c22a6e905c40f0efef1ce24aa6f1f447b4eb64a1137513a5f6b6532f83284`
- 《观察》第 3 卷第 11 期：`data/domestic/press_scans/NLC404-01J000332-6817_观察_1947年3卷11期.pdf`
- 《观察》来源 SHA256：`f4232929eca2a91b07b292eea0153528e8bce8e7241499a475e6ecc6d2b0af71`
- 复核前正式库 SHA256：`4cd77f5c8256f0fb6828cc1693f9b292057fa8c095640864de9357c41298cd88`
- 事件导航写入后的正式库 SHA256：`4caa961cc56bf4fe61bec172f201fd2b15c91e8030de0656ae5e61e77fe01c1e`
- 回滚备份：`/private/tmp/research_index.sqlite.before_dissolution_1947_visual_review_20260813.sqlite`、`/private/tmp/research_index.sqlite.before_dissolution_1947_event_link_20260813.sqlite`
- 复核批次：`work/domestic/dissolution_1947_review_20260813/`
- 正文未复制到批次或 Git；OCR 仅作检索辅助，视觉复核以渲染页和来源 SHA/页码 provenance 为准。

## 五个页级锚点

| page_id | 来源 | PDF 页 | 页面事实 | 精确入口 |
| ---: | --- | ---: | --- | --- |
| 1748 | 《大剛報》1947-11-04 | 1 | 页面清晰刊出张群书面通知民盟、应允保障盟员安全及民盟将召开中常会讨论解散等报道入口 | [PDF 第 1 页](https://commons.wikimedia.org/wiki/File:NLC1080-00N001037-7604_%E5%A4%A7%E5%89%9B%E5%A0%B1_1947%E5%B9%B411%E6%9C%8804%E6%97%A5.pdf#page=1) |
| 1752 | 《大剛報》1947-11-06 | 1 | 页面主标题为民盟正式宣告解散，并通告各地盟员停止活动 | [PDF 第 1 页](https://commons.wikimedia.org/wiki/File:NLC1080-00N001037-7606_%E5%A4%A7%E5%89%9B%E5%A0%B1_1947%E5%B9%B411%E6%9C%8806%E6%97%A5.pdf#page=1) |
| 1770 | 《观察》第 3 卷第 11 期 | 3 | 刊出“我们对于政府压迫民盟的看法”，署周炳琳等四十八人 | [PDF 第 3 页](https://commons.wikimedia.org/wiki/File%3ANLC404-01J000332-6817_%E8%A7%80%E5%AF%9F_1947%E5%B9%B43%E5%8D%B711%E6%9C%9F.pdf#page=03) |
| 1771 | 《观察》第 3 卷第 11 期 | 4 | 刊出董时进“我对于政府取缔民盟的感想” | [PDF 第 4 页](https://commons.wikimedia.org/wiki/File%3ANLC404-01J000332-6817_%E8%A7%80%E5%AF%9F_1947%E5%B9%B43%E5%8D%B711%E6%9C%9F.pdf#page=04) |
| 1772 | 《观察》第 3 卷第 11 期 | 5 | 刊出韩德培“人身自由的保障问题”，作为法治和权利语境的同期评论页 | [PDF 第 5 页](https://commons.wikimedia.org/wiki/File%3ANLC404-01J000332-6817_%E8%A7%80%E5%AF%9F_1947%E5%B9%B43%E5%8D%B711%E6%9C%9F.pdf#page=05) |

## 平台接入

`data/domestic/citation_event_links.json` 新增四条保守导航：

1. 1947 年 11 月 4 日《大剛報》解散前报道页；
2. 1947 年 11 月 6 日《大剛報》正式宣告解散页；
3. 《观察》周炳琳等关于政府压迫民盟的声明页；
4. 《观察》董时进关于取缔民盟的感想页。

第 5 页只作为严格可引用的法治语境页保留，不把一般评论强行写成民盟解散事实。

## 当前验收口径

- 正式人工可引用页：`116 → 121`。
- 国内专题页级关联：`516 → 520` 条，覆盖国内物理页 `502 → 506` 个。
- 声明式严格页级专题回链：`16 → 20` 条，覆盖全部 9 个国内专题。
- 总 `research_events`：`2433 → 2437`。
- 来源文件缺失：0；来源 SHA 不匹配：0；SQLite integrity：`ok`；外键违规：0；FTS 未对齐：0。

## 未完成事项

- 仍需把 1947 年 10 月 27 日“宣布非法”、11 月 5—7 日政府/民盟公告与不同城市报刊版本建立逐页版本链。
- 同期报刊报道只能证明报道内容和舆论反应，不能单独替代政府公报、民盟内部会议记录或公告原件。
- 学术文章仍属于解释层；没有稳定全文、页码/章节和人工复核时，不进入 `citation_ready`。
