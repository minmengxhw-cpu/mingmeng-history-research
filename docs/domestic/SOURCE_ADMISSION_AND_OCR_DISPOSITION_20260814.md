# 国内资料准入与 OCR 分流（2026-08-14）

## 为什么要单独设这一层

国内资料目前同时存在正式扫描、同期报刊、汇编、目录、机器 OCR 和学术元数据。把它们全部当作“已收集资料”会产生两个错误：

1. 电子文本被重复 OCR，消耗时间并制造重复记录；
2. OCR 页数、目录命中或转载图被误当成原件闭环。

因此平台把“是否有研究价值”“是否已经取得来源”“是否需要 OCR”“是否可以正式引用”拆成四个独立判断。分流脚本只读取覆盖清单，不读取正文，不写正式 SQLite，也不删除或重命名任何本地文件。

## 运行

在有本地资料覆盖清单的电脑上运行：

```bash
python3 scripts/domestic/build_source_admission_queue.py \
  --inventory work/domestic/DOMESTIC_COVERAGE_INVENTORY_20260728.csv \
  --output-dir work/domestic/source_admission_20260814
```

如果覆盖表中存在 `formal_page_count_anomaly`，先运行页链对账，再把对账结果传回分流器：

```bash
python3 scripts/domestic/reconcile_source_page_counts.py \
  --output-json work/domestic/source_reconciliation_20260815/SOURCE_PAGE_RECONCILIATION.json \
  --output-md work/domestic/source_reconciliation_20260815/SOURCE_PAGE_RECONCILIATION.md

python3 scripts/domestic/build_source_admission_queue.py \
  --reconciliation work/domestic/source_reconciliation_20260815/SOURCE_PAGE_RECONCILIATION.json \
  --output-dir work/domestic/source_admission_20260815
```

这样，已经由 canonical 页链覆盖物理页的来源会从“暂停对账”转为“不重复 OCR、定向复核”；目录/索引规则优先级不变，不会因为存在页链就被误当成正文证据。

输出：

- `SOURCE_ADMISSION_QUEUE.json`：机器可读的逐来源分流结果；
- `SOURCE_ADMISSION_QUEUE.jsonl`：逐行工作单；
- `SOURCE_ADMISSION_QUEUE.md`：人可读统计和硬门禁。

这些输出属于本地工作产物，不应替代正式库，也不应把正文/OCR上传到 GitHub。

## 2026-08-20 当前刷新

已用最新页链对账结果重新生成 [`source_admission_20260820`](../../work/domestic/source_admission_20260820/)：

- 来源行：61；同 SHA 复核组：0；正式库未被写入；没有自动删除；
- `RETAIN_FORMAL_PAGE_CHAIN`：58；`RETAIN_TARGETED_REVIEW`：2；`RETAIN_NAVIGATION_ONLY`：1；
- 58 个来源明确不需要重复 OCR；2 个来源只使用已有 OCR 做定向复核；1 个索引/导航来源不做全文 OCR。

这说明当前国内资料层的主要瓶颈不是“再跑一遍 OCR”，而是取得并核验仍缺失的原件级来源，尤其是 1941 年成立和 1947 年非法化/解散两条 P0 主线。

## 2026-08-24 复核结果

使用当前覆盖表和页链对账结果做了一次只读重放，输出暂存于
`/tmp/source_admission_20260824/`，未读取正文、未写正式 SQLite、未删除或重命名任何本地文件：

- 来源行：61；同 SHA 复核组：0；`auto_delete=false`；`formal_db_written=false`；
- `RETAIN_FORMAL_PAGE_CHAIN`：58；动作均为 `NO_REPEAT_OCR_FORMAL_PAGES_EXIST`；
- `RETAIN_TARGETED_REVIEW`：2；动作均为 `USE_EXISTING_OCR_TARGETED_REVIEW`；
- `RETAIN_NAVIGATION_ONLY`：1；动作为 `NO_FULL_OCR_INDEX_ONLY`。

本次复核没有发现需要扩大整本 OCR 的来源。后续只有两类动作可以进入执行队列：

1. 对两个已有 OCR 页层的来源做目标页视觉核验，并在确有引用价值时补建 canonical 页链；
2. 对 1941 年成立、1947 年非法化/解散等 P0 缺口取得新的原件或正式复制件，再做定向提取。

该结果只证明资料分流稳定，不改变任何 `citation_ready`、真实性等级或 `research_ready` 状态。

## 分流规则

| 情形 | 平台动作 | OCR 动作 |
|---|---|---|
| 明确声明可靠电子文本 | 保留为电子文本候选 | 跳过 OCR |
| 已有完整正式页链 | 转页级人工引用复核 | 不重复 OCR |
| 已有完整 OCR 草稿但正式页链未闭合 | 保留为定向复核目标 | 使用现有草稿，不整本重跑 |
| 物理页数与 manifest/正式页不一致 | 暂停准入 | 先对账，不得用 OCR 数量掩盖冲突 |
| 来源文件本身明确是索引、目录、finding aid | 只保留导航价值 | 不做全文 OCR，不当正文证据 |
| 只有来源线索或未绑定文件 | 保留在候选/追索队列 | 先补来源、权利和 SHA，再决定 OCR |

## 不可越过的门禁

- 同 SHA 文件只建立版本/重复关系，不能自动删除任何副本。
- 分流不改变 `authenticity_level_*`、`review_status`、`human_verified` 或 `citation_ready`。
- OCR 永远是检索和定位辅助；正式引用必须回到原图、页码、来源 SHA 和人工复核。
- 低价值或重复线索采用“排除正式层/保留追溯记录”，不采用物理删除。
- 资料价值按专题问题和来源层级判断，不按文件大小、OCR 页数或搜索命中数判断。
- 期刊整册中出现“目录页”不等于整份来源是目录；只有来源文件本身的文件名/来源类型明确标记为索引、馆藏目录或 finding aid，才按导航来源分流。

## 与国内外统一平台的关系

境外平台已经把原档、页级定位、翻译和引用门禁分开；国内资料也必须遵循同一条链：

`来源家族 → 文件/影像 → 页级 provenance → 人工门禁 → 事件 → 研究问题 → 国内外对读`

准入分流只解决“应该把力气花在哪里”，不把任何候选自动变成一手证据。专题完成度仍以 `data/domestic/event_coverage.json`、`topic_evidence_chain.json` 和页级 provenance 为准。
