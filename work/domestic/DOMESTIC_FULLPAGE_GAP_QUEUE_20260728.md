# 国内来源 OCR 草稿与正式入库队列

本报告区分本地 OCR 草稿和 SQLite 正式页层。完整 OCR 草稿优先进入 formalize/review，不重复 OCR；报告只读生成，不修改 SQLite 或原始文件。

- 来源文件：61
- 物理页总数（可识别）：3878
- 本地 OCR 草稿页总数：2178
- SQLite 入库页总数：472
- 仍需生成 OCR 草稿页：1700
- 已有 OCR 草稿但待正式化页：1981
- 整本页完整：3
- 待处理来源：58
- 物理页数未知：0

## 优先级定义

- `A`：同期报刊/原始扫描，优先补齐整本页覆盖；补齐前仍只视为检索草稿。
- `B`：文献汇编或来源书，先补目录、序言、关键文献和可定位页；不能替代同期原件。
- `C`：其他国内来源，按证据价值另行处理。

## 队列统计

| 状态 | 文件数 |
|---|---:|
| draft_ready_formal_gap | 16 |
| draft_partial_formal_gap | 0 |
| indexed_partial_no_draft | 27 |
| formal_page_count_anomaly | 15 |

| 优先级 | 文件数 |
|---|---:|
| A | 53 |
| B | 5 |
| C | 0 |

## 下一步队列（前 20）

- `draft_ready_formal_gap` / `A`：`data/domestic/press_scans/NLC404-00J001436-85449_民憲_第一卷第八期.pdf`（物理 55，OCR草稿 55，正式入库 2，待OCR 0，待正式化 53）
- `draft_ready_formal_gap` / `A`：`data/domestic/press_scans/NLC404-00J001436-85445_民憲_第一卷第四期.pdf`（物理 47，OCR草稿 47，正式入库 2，待OCR 0，待正式化 45）
- `draft_ready_formal_gap` / `A`：`data/domestic/press_scans/NLC404-00J001436-85453_民憲_第一卷第十二期.pdf`（物理 45，OCR草稿 45，正式入库 2，待OCR 0，待正式化 43）
- `draft_ready_formal_gap` / `A`：`data/domestic/press_scans/NLC404-01J000514-10834_光明報_1946年1期.pdf`（物理 24，OCR草稿 24，正式入库 2，待OCR 0，待正式化 22）
- `draft_ready_formal_gap` / `A`：`data/domestic/gazette_scans/ROC1947-10-27國民政府公報2964.pdf`（物理 17，OCR草稿 17，正式入库 1，待OCR 0，待正式化 16）
- `draft_ready_formal_gap` / `A`：`data/domestic/gazette_scans/ROC1947-11-07國民政府公報2974.pdf`（物理 17，OCR草稿 17，正式入库 1，待OCR 0，待正式化 16）
- `draft_ready_formal_gap` / `A`：`data/domestic/press_scans/NLC404-01J000332-6817_观察_1947年3卷11期.pdf`（物理 20，OCR草稿 20，正式入库 5，待OCR 0，待正式化 15）
- `draft_ready_formal_gap` / `A`：`data/domestic/press_scans/NLC404-01J000514-10431_光明報_1946年10期.pdf`（物理 16，OCR草稿 16，正式入库 2，待OCR 0，待正式化 14）
- `draft_ready_formal_gap` / `A`：`data/domestic/press_scans/NLC404-01J000514-10460_光明報_1947年21期.pdf`（物理 16，OCR草稿 16，正式入库 2，待OCR 0，待正式化 14）
- `draft_ready_formal_gap` / `A`：`data/domestic/gazette_scans/ROC1947-10-30國民政府公報2967.pdf`（物理 13，OCR草稿 13，正式入库 1，待OCR 0，待正式化 12）
- `draft_ready_formal_gap` / `A`：`data/domestic/gazette_scans/ROC1947-11-06國民政府公報2973.pdf`（物理 9，OCR草稿 9，正式入库 1，待OCR 0，待正式化 8）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/SSID-13679264_观察_第3卷第1-12期.pdf`（物理 278，OCR草稿 0，正式入库 5，待OCR 278，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC511-012031312030001-21906_大公報_第114卷.pdf`（物理 248，OCR草稿 0，正式入库 4，待OCR 248，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC511-012031312030001-21905_大公報_第113卷.pdf`（物理 232，OCR草稿 0，正式入库 5，待OCR 232，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC404-00J001436-85454_民憲_第二卷第一期.pdf`（物理 71，OCR草稿 0，正式入库 2，待OCR 71，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC404-00J001436-85446_民憲_第一卷第五期.pdf`（物理 53，OCR草稿 0，正式入库 2，待OCR 53，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC404-00J001436-85447_民憲_第一卷第六期.pdf`（物理 51，OCR草稿 0，正式入库 6，待OCR 51，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC404-00J001436-85448_民憲_第一卷第七期.pdf`（物理 51，OCR草稿 0，正式入库 2，待OCR 51，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC404-00J001436-85450_民憲_第一卷第九期.pdf`（物理 51，OCR草稿 0，正式入库 6，待OCR 51，待正式化 0）
- `indexed_partial_no_draft` / `A`：`data/domestic/press_scans/NLC404-00J001436-85452_民憲_第一卷第十一期.pdf`（物理 51，OCR草稿 0，正式入库 2，待OCR 51，待正式化 0）

## 入库门控

1. `draft_ready_formal_gap`：复核本地 OCR 草稿的来源 SHA256、页码映射和页级边界，再做 SQLite dry-run。
2. `draft_partial_formal_gap`/`ocr_needed`：只对缺失页运行 PaddleOCR，保留页级 manifest。
3. 关键页必须记录原图定位、版面复核和人工审校结果。
4. 仅在 manifest、pages、page_fts 对齐且证据门控通过后，才提升为引用候选。
