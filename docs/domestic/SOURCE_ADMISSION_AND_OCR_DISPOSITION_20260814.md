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
