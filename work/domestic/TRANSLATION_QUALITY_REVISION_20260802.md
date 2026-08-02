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

## 抽样重译比对评估（补充，2026-08-02）

对 FRUS/CIA/wilson/hoover/hathitrust/newspapersg 全部 356 页核心文献做系统扫描后：

### 英文残留
- FRUS/CIA 核心文献 277 页：仅 page 126/168/387 有残留，其中 126/168 已修订、387 为合法罗马数字页码（iii/xvi）。
- 其余平台（wilson/hoover/hathitrust/newspapersg）核心 79 页：全部 0 英文残留。

### 机翻痕迹
- 「相邻重复短语」精确扫描：0 真实命中（page 82 的「三三三比例」是 3-3-3 正确译法）。
- 早期 regex 高分区（page 94/437 等）经逐条核实均为**合法缩写**（SWNCC/CNRRA）或 CIA 原文转写固有内容，非译错。

### 抽样译文质量（人工抽查）
- page 670 米高扬-毛泽东会谈：优秀，人名/术语规范。
- page 886 张君劢致魏德迈信：优秀，文言得体。
- page 215 马歇尔-司徒雷登与第三方面会谈：优秀，人名准确（吴铁城/邵力子/雷震）。
- page 437 CIA 名单：名单音译与史实人名有出入（刘亚子→柳亚子等），但属 CIA 原始转写固有内容，译文忠实。

### 结论
核心文献机译质量总体良好，无系统性重译需求。已修订的 7 页（126/107/168/228/301/40/300）覆盖了全部真实英文残留。个别报纸页（如 836）存在版面混排，属 OCR/原文问题而非翻译问题，建议标记为「需版面复核」而非重译。

## 非核心文献页修订 + 报纸混排标注（补充 2，2026-08-02）

### 非核心页真实残留（新增 4 页）
对全部 432 页非核心文献页（相关文献/背景材料/人物关联/前台不展示）扫描，真实残留集中 8 页，其中 4 页（40/107/228/301）已在上轮修订覆盖；本轮新增修复 4 页：
- **151**（相关）：Lu Han/吕汉→卢汉（云南省政府主席）
- **332**（相关）：Chanf-Kwei→张发奎、Kwangsi→广西、光通/关东→广东、光西→广西、柳乔→柳州
- **783**（前台不展示）：discord→分歧
- **839**（相关）：battalion→营

修订后累计 11 页入 `data/domestic/zh_translation_revisions_frus_core.csv`。

### hathitrust 报纸版面混排（28 页标注）
hathitrust 整版报纸 OCR 中 29 页确认混排（混入法国/意大利/希腊/德国/捷克/匈牙利/朝鲜/美国国会等无关版面报道），newspapersg 93 页全部正常。已有 1 页（838）此前标注，本轮为其余 28 页追加【校订说明】标注，输出 `data/domestic/zh_translation_revisions_hathitrust_mix.csv`。
