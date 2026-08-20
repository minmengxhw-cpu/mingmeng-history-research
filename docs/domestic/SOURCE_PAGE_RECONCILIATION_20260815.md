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

## 2026-08-21 单页试用库视觉核验补充

上海版、天津版《大公報》1947年11月6日第2版单页已完成来源文件和渲染页的只读核验：

- 两个 PDF 均为单页，源文件 SHA、页图 SHA 和页级身份已登记在 [`PAGE_IDENTITY_REVIEW.json`](../../work/domestic/dagangbao_page_identity_review_20260821/PAGE_IDENTITY_REVIEW.json)；
- 版面均可见《大公報》报面及民盟解散相关标题，现有 OCR 只作为检索草稿，不重新整本 OCR；
- 两页继续作为 `contemporary_newspaper_page / L1` 的同期报道使用，`citation_ready` 状态不因本次核验扩大到行政原件或民盟总部公告；
- 1947 年 P0 缺口仍是独立的 1947-10-27 政府公函和 1947-11-06 民盟总部解散公告，不能由两版报刊报道替代。

## 2026-08-21 三中全会公开扫描候选补充

- 对 `data/domestic/grok_cycle_0011_20260801/pdf/commons_NLC_中国民主同盟三中全会.pdf` 完成封面、题名页、正文起始页和尾页抽样视觉核验；SHA256 为 `f9099aa01475c7509d8c82013c8f8ec19333ae3e0fcab66eeaa8a3f9151fe9c7`，PDF 共 33 页。
- 题名页显示《中国民主同盟三中全会》和民国三十七年一月；正文起始页显示“紧急声明／政治报告／宣言”，但出版者、版本关系和全部印刷页连续性尚未完成核定。
- 已在 1948 专题来源地图登记为 `public_sourcebook_scan_candidate / L2` 公开追索入口；无页级记录，不进入正式引文，`primary_evidence_closed` 仍为 `false`。

## 2026-08-21 1945大会官方转载图像入口

- 北京民盟东城区官方盟史页 `https://www.bjdcmm.org.cn/01msjs/20040310/02.htm` 展示了“临时全国代表大会宣言和纲领”影像剪影，图片入口为 `https://www.bjdcmm.org.cn/01msjs/20040310/lsl10.jpg`。
- 该路线已登记为 `official_curated_reproduction / L1`，但没有原刊日期、报头、版次、档号或完整页码；它只扩展公开追索路径，不进入正式引文，也不关闭 1945 年大会原件缺口。

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
