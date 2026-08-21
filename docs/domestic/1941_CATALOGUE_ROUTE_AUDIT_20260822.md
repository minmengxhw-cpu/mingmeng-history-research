# 1941《光明報》馆藏路线核验

## 结论

当前本地两份与 1941《光明報》相关的 PDF 都不是《光明報》逐期原刊影像，但香港大学目录已经确认了题名级馆藏范围：

| 文件角色 | 文件元数据 | 可以证明 | 不能证明 |
|---|---|---|---|
| 香港大学目录 | `data/domestic/official_research_public_20260730/pdf/domestic:HKU:guangmingbao-1941-microform-holdings__光明報_1941年9月18日_12月12日馆藏缩微胶卷记录_075.pdf`；3 页；190224 bytes；SHA256 `7b9b1d8c3de9396ffd0dd5e58c75e8f70c07142671109aef4c1cb6df1b10e52a` | 目录第 21 项确认《光明報》为 Microform，1941-09-18 至 1941-12-12，`With Gaps=Nil` | 不能单凭目录提供逐期原刊影像、版次页码、正文或复制权 |
| 岭南大学索引 | `data/domestic/press_scans/LNU_PROFMKCHAN_INDEXLIST_14_光明報_1941.pdf`；2 页；545386 bytes；SHA256 `7ff54b899dddbbfe4f089aca87c3ca98b4de1fcd0074e0ae571f598bdcceb3a9` | 有一条《光明報，1941》剪报/索引导航记录 | 不能证明成立宣言原刊影像、版次、完整页链或正文可引用 |

香港大学文件标题是 `Hong Kong Newspapers - Chronological List 1940s`，第 2 页列出《光明報》；岭南文件是 `香港工運剪報索引列表` 的题名页。两者都应停留在馆藏/导航层，不进入原件池，不重复 OCR，不改变 `primary_evidence_closed`。

## 平台处理

- `data/domestic/1941_formation_source_map.json` 将香港大学记录保留为 `university_catalogue_access_route`，并记录目录覆盖范围。
- 两条路线均保持 `citation_ready=false`，不写入正式正文，不关闭 1941 成立专题缺口。
- 下一步是按已确认的馆藏范围申请/调取缩微胶卷，优先取得 1941-10-10 原刊影像及许可信息；取得前不安排全文 OCR。

## 可执行调取单

1. 以香港大学 Primo 记录 `HKU_IZ21440249790003414` 为馆藏核对入口，先确认实际 call number/馆藏前缀。
2. 向 HKU Special Collections 预约 Microform Scanner；如需闭架调取，按馆方要求提前通过 `libspeco@hku.hk` 申请，并填写书名、call number、到访日期和预约时段。
3. 首批只申请 1941-10-10，同时可把 1941-09-18 和 1941-10-16 作为相邻期对照，不申请整卷批量扫描。
4. 接收时逐项记录：馆藏题名、期日、胶卷/载体标识、扫描文件 SHA256、物理页/印刷页、是否完整、复制许可；未经这些字段复核，不进入 OCR 或正式 SQLite。

官方流程入口：

- [HKU 1940s Hong Kong Newspapers 目录](https://lib.hku.hk/sites/all/files/files/hkspc/pathfinders/newspaper_1940s_update_072021.pdf)
- [HKU Special Collections 材料申请](https://lib.hku.hk/hkspc/requesting_materials.html)
- [HKU Special Collections 设施与微缩扫描](https://lib.hku.hk/hkspc/facilities.html)
