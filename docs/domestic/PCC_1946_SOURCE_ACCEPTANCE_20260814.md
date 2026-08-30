# 1946 年《政協文獻》公开扫描接收记录（2026-08-14）

## 接收结论

已将一份公开的国家图书馆民国图书扫描暂存到本地 `data/domestic/sourcebooks/`，完成文件格式、大小、页数、加密状态和 SHA256 核验。目标地图本身仍是 sourcebook/staging 导航；2026-08-15 另有 9 张定向页以独立文档身份进入正式 SQLite，并完成页身份、页界、来源哈希和精确 PDF 页定位的视觉复核，进入汇编层 `strict_citation`。这不等于 OCR 正文逐字校订，也不等于独立政协会议档案已经取得。

这是一部 1946 年出版的政协文献汇编，不等同于政协会议档案馆原卷或各代表手中的独立底稿；但其目录明确包含会议经过、代表名单、民盟代表张澜开幕词、罗隆基关于政府改组的民盟意见、民盟提案、章伯钧关于国民大会的民盟意见及五项协议，具有直接缩小 `domestic-1946-pcc` 原件缺口的价值。

## 来源与本地文件

| 字段 | 值 |
|---|---|
| 题名 | 《政協文獻》 |
| 馆藏编号 | `NLC416-01jh004019-12949` |
| 编选者 | 历史文献社编选 |
| 出版信息 | 中华民国三十五年（1946） |
| 官方馆藏身份 | 中国国家图书馆民国时期文献记录（通过 Wikimedia Commons 公开扫描入口） |
| Commons 页面 | [File:NLC416-01jh004019-12949 政協文獻.pdf](https://commons.wikimedia.org/wiki/File:NLC416-01jh004019-12949_%E6%94%BF%E5%8D%94%E6%96%87%E7%8D%BB.pdf) |
| 原始文件入口 | [upload.wikimedia.org PDF](https://upload.wikimedia.org/wikipedia/commons/e/e6/NLC416-01jh004019-12949_%E6%94%BF%E5%8D%94%E6%96%87%E7%8D%BB.pdf) |
| 本地路径 | `data/domestic/sourcebooks/NLC416-01jh004019-12949_政協文獻_1946.pdf` |
| 文件大小 | `25,429,109` bytes |
| 页数 | `247` |
| PDF 加密 | 否 |
| SHA256 | `4b45976ffdea727f0e26f79c4cb2688e01093d5d7901103c17d99823e7e4d50f` |

## 可用于专题的目录锚点

Commons 页面提供的目录包含以下目标文种，后续应按扫描页和印刷页分别建立映射：

- 政治协商会议经过、会议日程、代表名单和各分组委员会名单；
- 民主同盟代表张澜开幕词；
- 民主同盟代表张君劢闭幕词；
- 罗隆基报告民主同盟意见；
- 军事问题部分的民主同盟提案；
- 国民大会问题部分的章伯钧说明民主同盟意见；
- 五项协议及其讨论发言。

这些目录锚点支持“会议制度—民盟代表表达—协议文本”的研究路径，但尚未证明每一项正文都已完成页级核读。

## 视觉与完整性抽查

已对封面、前置/目录区域和正文样页进行渲染抽查。文件可以正常打开，页面有原书版式；部分扫描页存在旋转版式、手写标记或近空白/版面异常，不能用少量抽查代替整本页序核对。异常页应进入 `page_anomaly` 记录，不得直接当作缺页或正文缺失。

## 目录锚点的定向视觉页映射（staging）

以下页码是本轮按本地 PDF 渲染图进行的 1-based 视觉定位：`PDF 页` 是文件页序，`印刷页` 是页面右侧原书页码。它们只确认标题出现位置，不等于已经完成全文 OCR、正文录入或事件回链；相邻页的边界仍须逐页核对。

| 目录目标 | 标题起始 PDF 页 | 印刷页 | 定向观察 | 当前状态 |
|---|---:|---:|---|---|
| 民主同盟代表张澜开会词（开幕词） | 23 | 16 | PDF 24／印刷页 17 为已核连续页 | `page_identity_boundary_verified / strict_citation` |
| 民主同盟代表张君劢闭会词 | 52 | 45 | 标题页身份与页界已核 | `page_identity_boundary_verified / strict_citation` |
| 罗隆基报告民主同盟意见 | 62 | 55 | PDF 63／印刷页 56 为已核连续页，页末进入下一条目 | `page_identity_boundary_verified / strict_citation` |
| 民主同盟的提案 | 101 | 94 | 标题页身份与页界已核 | `page_identity_boundary_verified / strict_citation` |
| 章伯钧说明民主同盟的意见 | 125 | 116 | PDF 126／印刷页 117 为已核连续页 | `page_identity_boundary_verified / strict_citation` |
| 民盟主席张澜三月二十一日的重要谈话 | 206 | 197 | 标题、标注日期与页界已核 | `page_identity_boundary_verified / strict_citation` |

派生渲染图不进入 Git，也不作为正文发布；本轮已经将 9 张定向页图的页码、渲染参数、SHA256 和视觉复核状态登记到 `data/domestic/pcc_1946_sourcebook_render_manifest.json`。该清单只证明本地复核资产可重建；9 个正式页的页级引用范围限于汇编版本、页界、PDF/印刷页号和来源哈希，不包含 OCR 正文逐字校勘。整本目标地图仍属于 `sourcebook_scan`；另有 9 个 OCR 页通过专门导入器进入正式检索，其中页级状态已由 `review_only` 收口为汇编层 `strict_citation`。

结构化页图入口已登记在 `data/domestic/pcc_1946_sourcebook_targets.json`，页图哈希清单位于 `data/domestic/pcc_1946_sourcebook_render_manifest.json`。本地应用通过 `/domestic/sourcebook/1946-pcc` 提供元数据和定向阅读入口；原始 PDF 和派生页图仍留在本机，不进入 GitHub。该应用入口在公开模式下会被隐藏，避免把本地 staging 资产误当成公开研究正文。

## 当前证据层级与边界

- 当前建议层级：整本 `L2 / sourcebook_scan`；9 个定向页为 `strict_citation / page_identity_and_boundary`；
- 可作为 1946 旧政协专题的高价值同期汇编和页级交叉来源；
- 不能直接宣称是政协原始会议档案、代表原始手稿或独立原刊；
- OCR 正文仍未逐字复核，不得把页级 `strict_citation` 误解为正文已校勘；
- 本轮未执行整本 OCR，已将 9 个定向页写入 SQLite 并完成页级回链，未改变 `primary_evidence_status`。

## 下一步定向处理

1. 只对目录页和上述民盟相关标题对应页做定向 OCR/人工定位，不对 247 页整本重 OCR；
2. 为每个目标页记录 PDF 页、印刷页、页图 SHA256、源文件 SHA256和版面异常状态；
3. 与现有 1946 年《光明報》、民盟人物发言和境外政协记录逐条对位；
4. 通过 `staging → 视觉复核 → provenance → 事件回链` 后，再评估是否能缩小 `domestic-1946-pcc` 的开放目标；
5. 只有主证据、同期交叉、负向核查、版本关系和研究包全部满足，才允许专题进入 `research_ready`。

## 不变量

目标地图的 `body_read=false`、`formal_db_written=false`、`auto_download=false`、`auto_promote_primary_closed=false` 保持不变；这里的 `formal_db_written=false` 表示地图构建过程不写 SQLite，不否认已经完成的 review-only OCR 导入。原始 PDF 留在本地，不推送到 GitHub；GitHub 只记录来源身份、哈希和处理边界。
