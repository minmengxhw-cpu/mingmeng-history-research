# 国内来源页链对账与 OCR 停止条件

日期：2026-08-15  
适用范围：`work/domestic/DOMESTIC_COVERAGE_INVENTORY_20260728.csv` 所列 61 个本地来源

## 结论

本轮只读取来源覆盖表和 `data/research_index.sqlite` 的文档/页级元数据，未读取正文、未写 SQLite、未改变 `citation_ready`、未删除或重命名任何本地文件。

对账结果：

| 结论 | 来源数 | 含义 |
|---|---:|---|
| `RECONCILED_CANONICAL_PAGE_CHAIN` | 44 | 已有完整 canonical 页链覆盖物理页，可停止重复 OCR，进入定向内容复核 |
| `RECONCILED_DUPLICATE_COMPLETE_LAYERS` | 15 | canonical 页链与完整 OCR 层都覆盖物理页，额外的一页或多页是层/锚点重复，不是原件多页 |
| `RECONCILED_COMPLETE_OCR_LAYER` | 2 | 试用数据库的单页大公报影像已有完整 OCR 页层，但尚未形成 `domestic-page/` canonical 视觉页链 |

因此，本地现有 61 个来源没有一个需要因为“物理页数异常”而再次整本 OCR。此前队列里的 `formal_page_count_anomaly` 主要来自同一来源同时登记了：

1. 完整的 `domestic-page/` 页级影像链；
2. 完整的 `domestic-ocr/NLC:` 检索层；
3. `COLLECTION:` / `LOCALFULL:` 集合或入口锚点。

例如《光明报》1947 年第 13 期：PDF 16 页，canonical 页链 16 页，完整 OCR 层 16 页，另有两个一页入口锚点。不能把 16+1+1 解释为 PDF 有 18 页，也不能因此启动第三次 OCR。

## 对平台的实际影响

- OCR 不再是当前国内平台的主要瓶颈；当前瓶颈是原件层级、事件关联、专题页的人工/机器复核，以及 1941、1946、1947 等 P0 原始证据缺口。
- `domestic-page/` 是展示与页级定位层；`domestic-ocr/NLC:` 是检索/比对层；集合锚点只承担入口作用。三者不互相升级证据等级。
- 15 个重复完整层来源应保留两种层：视觉层支持页级核读，OCR 层支持检索；但后续工作只能做定向复核，不再整本导入。
- 两个试用数据库单页来源先保留现状。只有在授权允许、且确实需要视觉核读时，才补建 canonical 页链；否则已有 OCR 记录足够承担检索入口，不因“没有 canonical”强行复制。

## 可复现命令

```bash
python3 scripts/domestic/reconcile_source_page_counts.py \
  --output-json work/domestic/source_reconciliation_20260815/SOURCE_PAGE_RECONCILIATION.json \
  --output-md work/domestic/source_reconciliation_20260815/SOURCE_PAGE_RECONCILIATION.md
```

该命令是元数据审计，不读取正文、不写正式库、不自动改变真实性等级，也没有删除动作。

## 下一阶段门禁

1. 资料处理：只做目标页/目标事件定向复核；电子文本直接解析，已有完整页链的来源跳过整本 OCR。
2. 研究入库：每条事实必须绑定来源层级、来源文件 SHA、PDF 页码/物理页号和复核状态；汇编重刊、后期转录、报刊报道不能替代行政/组织原件。
3. 平台验收：国内专题页可以达到“导航可用”和“证据链可追溯”，但只有取得并核验原始政府公函、民盟总部公告或独立同期底本后，才关闭相应 `primary_evidence_gap`。
4. 存储治理：不删除低价值或重复文件；先在 manifest/准入层标注 `navigation_only`、`review_only`、`duplicate_complete_layers` 等状态，物理清理必须另行授权并保留可恢复备份。
