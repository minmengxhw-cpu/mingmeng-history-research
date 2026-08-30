# 1947 年民盟 P0 本地原件清查（2026-08-30）

## 目的与边界

本轮对当前代码 checkout、数据 checkout 与既有 P0 接收记录做文件名、文件大小、SHA256、PDF 页数和来源登记级清查，目的在于排除“目标原件已经落地但没有被接收门禁发现”的情况。

本轮不读取 PDF 正文、不执行 OCR、不写入 `data/research_index.sqlite`，也不删除、移动或覆盖本地文件。文件名含 `1947`、`解散`、`非法`、`民盟` 的 PDF 只作为发现入口；文件名命中不等于文件身份成立。

## 清查到的本地 PDF

| 文件 | 文件级事实 | 身份判断 |
|---|---|---|
| `data/domestic/academic_public_20260730/pdf/中国民主同盟历史文献_1941-1949_marxists.pdf` | 622 页；18,131,353 bytes；SHA256 `257bb7be70abe374be9864ec451b5a90e2442ae8c877b15f4e6bbb8bb30be3`；FreePic2Pdf；未加密 | 与数据 checkout 中的 `data/domestic/sourcebooks/中国民主同盟历史文献_1941-1949_公开扫描.pdf` 同 SHA 的 1983 年正式汇编扫描；含 1947 相关文本重刊，但不是 1947 年政府公函或民盟总部公告原件 |
| `data/domestic/raw/public_sources/nlc_dagongbao_hankow_1947-11-06.pdf` | 4 页；8,704,911 bytes；SHA256 `9b4c22a6e905c40f0efef1ce24aa6f1f447b4eb64a1137513a5f6b6532f83284` | 1947-11-06 汉口版《大公报》同期报刊；属于报道/转引链，不是总部公告底本 |
| `data/domestic/raw/public_sources/roc_gazette_1947-10-30_2967.pdf` | 13 页；953,781 bytes；SHA256 `61eef4effac2abda2812a1ec507e7e9bb9bed219b31426dd07415b60c36f83e5` | 1947-10-30 公报扫描；不是 10-27 目标行政文件，保留为负向/导航材料 |
| `data/domestic/raw/public_sources/roc_gazette_1947-11-07_2974.pdf` | 17 页；1,040,687 bytes；SHA256 `5e04a2d4ecc2ebe9ae09b978127bcb9cd11481e9966fe8a9eb0b4be9bb592` | 1947-11-07 公报扫描；不是 11-06 目标总部公告，保留为负向/导航材料 |

另有 sibling checkout 中已经登记的 1947-10-27、1947-11-06 两期国民政府公报负向样本；其既有审计结论不变，不重复复制或 OCR，详见 `P0_ALTERNATE_CHECKOUT_AUDIT_20260829.md`。

## 结论

1. 未发现 `P0-1947-10-27-GOVERNMENT-ADMINISTRATIVE-ORIGINAL` 的行政原件。
2. 未发现 `P0-1947-11-06-MM-HEADQUARTERS-DISSOLUTION-ANNOUNCEMENT` 的民盟总部公告原始底本。
3. 622 页汇编是高价值的汇编重刊/检索入口，但它不能替代两个 P0 原件；相关页级引用必须继续保留“汇编版本”边界。
4. 现有 622 页同 SHA OCR 检索草稿可继续复用；没有理由再次整本 OCR。只有出现新的原件、明确页身份或需要定向抽查时，才做增量处理。

## 当前门禁与下一步

P0 接收目录、显式原件映射和正式库写入仍为 0；两个目标继续保持 `WAITING_FOR_LOCAL_ORIGINAL`，研究内容状态继续保持 `OPEN_PRIMARY_GAPS`。

下一次可以关闭 P0 的输入必须同时具备：记录号或档号、原始文件或正式复制件、文件 SHA256、页数/页身份、来源与权限说明，以及与现有汇编重刊/报刊报道的版本关系。收到之前，不把“汇编重刊”“同期报道”或网页摘录升级为原件。
