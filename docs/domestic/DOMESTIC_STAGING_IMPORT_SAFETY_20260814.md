# 国内资料 staging 导入安全规则（2026-08-14）

## 目的

让授权下载的 MM1941 文件、公开扫描和 OCR 草稿都先进入隔离 staging，再决定是否进入正式研究层。导入器现在强制要求显式指定 SQLite 路径，并拒绝 `data/research_index.sqlite`（包括指向它的符号链接解析路径）。

脚本：

```text
scripts/ingest/import_domestic_ocr_batch.py
```

## 固定流程

### 1. 先准备 manifest

每条记录至少包含：

- `record_id`、`title`、`document_date`、`source_kind`；
- `source_path`、`source_sha256`；
- `pages[].page_label`、`pages[].ocr_markdown`、`pages[].ocr_status`；
- `source_kind` 只能是 `public_scan` 或 `authorized_mmda`。

来源文件和每个 OCR 页必须在本地存在，来源 SHA256 不匹配时导入器直接失败。

### 2. dry-run

```bash
python3 scripts/ingest/import_domestic_ocr_batch.py \
  --manifest /path/to/BATCH.jsonl \
  --db /path/to/staging.sqlite \
  --batch-id mm1941-p0-20260814 \
  --report /path/to/DRY_RUN.json
```

不加 `--apply` 时只校验 manifest、来源文件和 OCR 文本，不写 SQLite。`--db` 仍必须显式填写，但不能指向正式库。

### 3. staging apply

只有人工检查 dry-run 报告和来源范围后，才允许对 staging 副本加 `--apply`：

```bash
python3 scripts/ingest/import_domestic_ocr_batch.py \
  --manifest /path/to/BATCH.jsonl \
  --db /path/to/staging.sqlite \
  --batch-id mm1941-p0-20260814 \
  --apply \
  --report /path/to/APPLY.json
```

应用前自动创建不覆盖的备份，并验证备份 SHA256；提交前自动验证：

- `PRAGMA integrity_check`；
- `PRAGMA foreign_key_check`；
- `pages_without_fts=0`；
- `fts_without_pages=0`。

报告同时记录 before/after SHA256、备份路径和 `formal_db_written=false`。

## 已完成的 smoke 验收

使用仓库内合成 fixture（不是历史正文）验证：

- dry-run `PASS`；
- 对正式库路径明确拒绝；
- 对正式库副本 apply 成功写入 1 条/1 页 staging 记录；
- integrity、外键和 FTS 对齐全部通过；
- 正式库 SHA256 未改变：`8a8cfb830ec06004d01c626a3cab59d4bd158157d1b820d4868575a2115107ea`。

fixture 位于 `tests/fixtures/domestic_ocr_batch_smoke.jsonl`，其中 PDF 和 OCR 文本仅用于程序测试，不是研究材料。

## 研究状态边界

staging 导入不等于严格引用：

- OCR 仍是检索/定位草稿；
- `citation_ready`、`human_verified` 不因导入自动升级；
- 必须回到原图、页码、来源 SHA256 和人工视觉复核；
- 没有完整来源链时，专题 `open_targets` 不得关闭；
- 不删除或覆盖用户本地原件、备份和 OCR 文件。
