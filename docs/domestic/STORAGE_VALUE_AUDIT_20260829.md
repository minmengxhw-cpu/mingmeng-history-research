# 国内资料存储与价值分层审计（基线更新：2026-08-30）

## 结论

当前体积主要来自工作区的可恢复中间资产，不是 GitHub 代码或正式结构化资料。对正式 checkout 做元数据级盘点得到：

| 层 | 文件数/体积 | 判定 |
|---|---:|---|
| `data/` | 1,628 个文件，901,958,752 bytes（约 860.0 MiB） | 正式数据、来源文件、结构化元数据和索引，保留 |
| `work/domestic/` | 1,455 个文件，2,960,778,059 bytes（约 2.76 GiB） | 工作批次、审计、渲染、OCR 派生和备份，分层处理 |
| `work/domestic/backups/` | 4 个 SQLite，各 703,549,440 bytes；合计 2,814,197,760 bytes（约 2.62 GiB） | 历史恢复点，不能按“同大小”直接判定重复 |
| 其他工作产物 | 146,580,299 bytes（约 139.8 MiB） | OCR/渲染、审计报告和批次中间结果，先保留并建立复建/保留依据 |

## SQLite 备份复核

当前正式库和 `work/domestic/backups/` 中的 4 份快照均通过 `PRAGMA integrity_check=ok`，且 SHA256 不同。`data/research_index.sqlite` 在本 checkout 中是指向另一 checkout 正式库的符号链接；本轮审计已把这个已知挂载目标计入 `data/` 总量，但不会跟随任意符号链接。正式库的版本化 manifest 也已与当前文件匹配：

| 文件 | SHA256 | 关键行数（documents / pages / page_fts / research_events / domestic_candidates） |
|---|---|---|
| `data/research_index.sqlite` | `2079d6309ac9138123c31c099d36ceac5165ba26c5d98a2fcecc1bd28aa41e7c` | 1415 / 6277 / 6277 / 2556 / 693 |
| `work/domestic/backups/research_index.sqlite.before_mmhist_printed_subset_20260830.sqlite` | `aa76c9c3077cdfb40f9c254dd2d03dd9369e9e2f8a68aab8da8f3632426bf7f2` | 1415 / 6277 / 6277 / 2556 / 693 |
| `work/domestic/backups/research_index_before_nlc_1949_journal_20260815.sqlite` | `75312b9c1cfe7d8978f64c572b4c32b7ab443fb507eabfd3b2fce47031d2109e` | 1413 / 6266 / 6266 / 2520 / 690 |
| `work/domestic/backups/research_index_before_nlc_1949_page_identity_20260815.sqlite` | `25624cc9b9713a72e3777c515571b26fc322444bf2101b0e9e72bcbe8802fee0` | 1414 / 6274 / 6274 / 2528 / 690 |
| `work/domestic/backups/research_index_before_source_registry_nlc_1949_20260815.sqlite` | `7135c635f92429bd14ba09420e5532e3a09f83f336d53e609f791a17f83e701b` | 1414 / 6274 / 6274 / 2528 / 690 |

它们是不同时间点的恢复快照，不应因为文件大小相同就删除。当前正式库与 `before_mmhist_printed_subset` 快照的行数相同，但 SHA256 不同，仍需保留其批次语义；其他快照的文档、页、事件和候选行数不同，具有明确回滚价值。另有 `work/domestic/pcc_1946_sourcebook_ocr_20260814/pcc_1946_ocr_staging.sqlite`（9 页 staging OCR）通过完整性检查，但它不是正式库恢复快照。

### 快照元数据对账

为避免仅凭文件大小或 SHA256 判断重复，本轮新增 [`scripts/domestic/compare_sqlite_snapshot_metadata.py`](../../scripts/domestic/compare_sqlite_snapshot_metadata.py)，只比较白名单结构化表，排除页面正文、翻译正文、全文索引和长叙述列，不输出任何行值。对账结果如下：

- 当前正式库与 `before_mmhist_printed_subset` 快照共有 5,493 条 `page_provenance`；无新增或删除页，只有 17 条的 `printed_page` 与 `updated_at` 不同。因此该快照对应真实的页码登记批次，不能当作字节级重复删除。
- 与 `before_nlc_1949_journal`、`before_nlc_1949_page_identity`、`before_source_registry_nlc_1949` 三份旧快照相比，`documents`、`pages`、`research_events`、候选和来源表均出现结构化差异；它们各自保留回滚价值。

复核命令：

```bash
python3 scripts/domestic/compare_sqlite_snapshot_metadata.py \
  --output /tmp/domestic_sqlite_snapshot_metadata.json \
  --quiet
```

## 价值/保留分层

### A. 正式研究资产：保留

- `data/research_index.sqlite`、manifest、source registry、候选与事件映射；
- `data/domestic/raw/` 中已登记来源文件；
- `data/domestic/sourcebooks/` 中作为版本参照的汇编扫描；
- 已绑定来源 SHA、页级 provenance、研究包和验证脚本。

### B. 可重建派生层：暂保留

- OCR 文本、页图渲染、切片和局部复核输出；
- 只有在确认正式库页链、manifest 和复建命令均可用后，才可考虑把重复派生层压缩归档。

### C. 恢复层：保留至少一个可用快照，其余只可在单独授权后处理

4 个备份目前都完整可读且哈希不同，且元数据对账确认它们不是可直接互换的副本。后续若要节省空间，安全顺序应是：

1. 为每个快照登记对应提交/批次和恢复验证结果；
2. 将不常用快照移动到外部归档介质或压缩包，并保留 SHA256；
3. 重新验证“当前库可从保留快照恢复”；
4. 取得明确的物理清理授权后，才讨论删除；默认不自动删除。

### D. 未知工作产物：只标记，不删除

`work/domestic` 下的报告、批次目录和模型输出不能仅凭名称判断无价值。先标注 `review_only`、`rebuildable`、`source_bound` 或 `stale_candidate`，再逐批决定归档策略。

## 可复现命令

```bash
python3 scripts/domestic/audit_storage_layers.py \
  --hash-sqlite \
  --output-json /tmp/domestic_storage_audit.json \
  --output-md /tmp/domestic_storage_audit.md
```

该脚本只读取文件元数据并对 SQLite 做哈希/完整性检查，不读取正文、不写正式库、不 OCR、不删除或移动文件。GitHub 只提交脚本和本报告，不提交本地原件、OCR 产物或 SQLite 备份。

## 当前处理决定

- 本轮不删除任何本地资料。
- 不把工作区备份复制进正式数据层。
- 不把 OCR/渲染产物当成新的来源文件。
- 后续继续优先处理研究价值和证据缺口，存储压缩放在 manifest/恢复验证之后。
