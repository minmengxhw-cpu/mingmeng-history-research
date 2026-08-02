# FRUS 译文质量修订报告（2026-08-02）

## 背景
早前 FRUS 译文由 deepseek-chat 机译（status=`human-reviewed`），存在两类质量问题：
1. **威妥玛拼音/OCR 残留**：正文直接夹带英文拼音（如 `Kiangsu`、`苏ch`、`hsien`、`RR线`）。
2. **混排硬伤**：机翻碎片与英文单词杂糅，个别核心文献页（page 300）严重。

精确定位检测（复刻 QC `english_residue` 逻辑、排除术语索引/括号/书名号后）：
- FRUS 12 页含拼音残留，其中 page 126 最重（5 处）。
- 「中文句中夹英文」硬残留逐条甄别后，真实需修 6 页 + 1 页全文重译。

## 修订交付
`data/domestic/zh_translation_revisions_frus_core.csv`（7 条，列：page_id, zh_translation, translator_note, translator, status）

| page | 文献 | 修订类型 |
|---|---|---|
| 126 | FRUS 1946 马歇尔-周恩来会谈纪要（核心） | 拼音→译名 10 处 + 错译修正 + 脚注重排 |
| 107 | FRUS 1946 马歇尔与八代表会议（相关） | Hwong→黄先生 |
| 168 | FRUS 1946 马歇尔-俞大维会谈（核心） | 皮将军/承德/热河/徐州/大同/删 OCR 噪声 |
| 228 | FRUS 1946 马歇尔-司徒雷登会面（人物关联） | hsien→县、Chefoo→芝罘、杜聿明等 |
| 301 | FRUS 1947 孙科谈话报告（人物关联） | Sun→孙博士、Milks→米尔克斯 |
| 40 | FRUS 1945 协调委员会报告（相关） | 缅甸/河北/宋子文/台湾等 9 处 |
| 300 | FRUS 1947 司徒雷登第三党运动报告（核心） | **按英文原文全文重译**（人名/地名/术语标准化） |

修订后 7 页正文均 0 英文残留（已脚本校验）。

## 判定为「合法保留、不修」的项
- 机构缩写：SWNCC、ECA、CIO、LST、CNRRA（正文已附中文名）。
- 档案编号/出处：CD No、APRF、History and Public Policy Program Digital Archive。
- 罗马数字页码：`iii`、`xvi`。
- 术语索引行刻意保留英文原文对照（如 `CC Clique：CC系`）。

## 待确认
1. **应用方式**：修订 CSV 与 `scripts/lib/import_translations_csv.py` 兼容，但导入会对正式库 DELETE+INSERT 并重建 FTS → 再次引发 SHA 漂移。正式库现处于 `e4417bd1` 漂移待批状态（FROZEN for subagents）。建议：
   - 方案 A：仅提交 CSV 与报告到 git（不动正式库），后续由主流程统一 rebaseline 时合并导入。
   - 方案 B：先批准 `e4417bd1` 新基线，再执行导入并提交。
2. 是否继续对 FRUS 其余核心文献页（如 94/379/387 等已确认残留较少的页）也做抽样重译。
