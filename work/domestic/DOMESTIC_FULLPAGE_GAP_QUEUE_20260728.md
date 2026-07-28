# 国内来源整本页覆盖缺口队列

本报告对比 PDF 物理页数、OCR manifest 页数和 SQLite 已入库页数。`indexed` 不代表整本完成；只有三者相等才标记为 `page_complete`。报告只读生成，不修改原始文件或 SQLite。

- 来源 PDF：56
- 物理页总数（可识别）：3821
- manifest 页总数：467
- SQLite 入库页总数：467
- 待补物理页（逐文件正缺口合计）：3369
- manifest 超出 pdfinfo 页数：15
- 整本页完整：2
- 选页/部分 OCR：54
- 物理页数未知：0

## 优先级定义

- `A`：同期报刊/原始扫描，优先补齐整本页覆盖；补齐前仍只视为检索草稿。
- `B`：文献汇编或来源书，先补目录、序言、关键文献和可定位页；不能替代同期原件。
- `C`：其他国内来源，按证据价值另行处理。

## 队列统计

| 优先级 | 文件数 |
|---|---:|
| A | 49 |
| B | 5 |
| C | 0 |

## 最大页缺口（前 20）

- `B` 缺 778 页：`data/domestic/sourcebooks/中国民主同盟临时全国代表大会宣言_公开转录.pdf`（物理 789，manifest 11，入库 11）
- `B` 缺 607 页：`data/domestic/sourcebooks/中国民主同盟历史文献_1941-1949_公开扫描.pdf`（物理 622，manifest 15，入库 15）
- `A` 缺 273 页：`data/domestic/press_scans/SSID-13679264_观察_第3卷第1-12期.pdf`（物理 278，manifest 5，入库 5）
- `A` 缺 244 页：`data/domestic/press_scans/NLC511-012031312030001-21906_大公報_第114卷.pdf`（物理 248，manifest 4，入库 4）
- `A` 缺 227 页：`data/domestic/press_scans/NLC511-012031312030001-21905_大公報_第113卷.pdf`（物理 232，manifest 5，入库 5）
- `B` 缺 174 页：`data/domestic/sourcebooks/NLC511-027032013012333-19131_民主同盟文獻_alternate_scan.pdf`（物理 178，manifest 4，入库 4）
- `B` 缺 103 页：`data/domestic/sourcebooks/NLC511-027032016010761-42571_中国民主同盟言论集.pdf`（物理 107，manifest 4，入库 4）
- `A` 缺 69 页：`data/domestic/press_scans/NLC404-00J001436-85454_民憲_第二卷第一期.pdf`（物理 71，manifest 2，入库 2）
- `B` 缺 61 页：`data/domestic/sourcebooks/NLC416-01jh004281-12557_民主同盟文獻_1946.pdf`（物理 176，manifest 115，入库 115）
- `A` 缺 53 页：`data/domestic/press_scans/NLC404-00J001436-85449_民憲_第一卷第八期.pdf`（物理 55，manifest 2，入库 2）
- `A` 缺 51 页：`data/domestic/press_scans/NLC404-00J001436-85446_民憲_第一卷第五期.pdf`（物理 53，manifest 2，入库 2）
- `A` 缺 49 页：`data/domestic/press_scans/NLC404-00J001436-85448_民憲_第一卷第七期.pdf`（物理 51，manifest 2，入库 2）
- `A` 缺 49 页：`data/domestic/press_scans/NLC404-00J001436-85452_民憲_第一卷第十一期.pdf`（物理 51，manifest 2，入库 2）
- `A` 缺 47 页：`data/domestic/press_scans/NLC404-00J001436-85451_民憲_第一卷第十期.pdf`（物理 49，manifest 2，入库 2）
- `A` 缺 45 页：`data/domestic/press_scans/NLC404-00J001436-85443_民憲_第一卷第二期.pdf`（物理 47，manifest 2，入库 2）
- `A` 缺 45 页：`data/domestic/press_scans/NLC404-00J001436-85445_民憲_第一卷第四期.pdf`（物理 47，manifest 2，入库 2）
- `A` 缺 45 页：`data/domestic/press_scans/NLC404-00J001436-85447_民憲_第一卷第六期.pdf`（物理 51，manifest 6，入库 6）
- `A` 缺 45 页：`data/domestic/press_scans/NLC404-00J001436-85450_民憲_第一卷第九期.pdf`（物理 51，manifest 6，入库 6）
- `A` 缺 43 页：`data/domestic/press_scans/NLC404-00J001436-85453_民憲_第一卷第十二期.pdf`（物理 45，manifest 2，入库 2）
- `A` 缺 43 页：`data/domestic/press_scans/NLC404-00J001436-85455_民憲_第二卷第二期.pdf`（物理 45，manifest 2，入库 2）

## 入库门控

1. 先按 `A` 队列逐份保留原 PDF SHA256 和页码映射。
2. 以页为单位运行 PaddleOCR；OCR 结果只能先进入检索草稿层。
3. 关键页必须记录原图定位、版面复核和人工审校结果。
4. 仅在 manifest、pages、page_fts 对齐且证据门控通过后，才提升为引用候选。
