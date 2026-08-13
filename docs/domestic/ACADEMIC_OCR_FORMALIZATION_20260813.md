# 学术扫描 PDF 正式化流程

日期：2026-08-13

## 用途

将已经通过本地 PaddleOCR 页级检查的 S/A 学术扫描 PDF 放入正式 SQLite 检索层。该流程只增加解释层全文，不把 OCR 结果变成正式引文。

## 固定门禁

- staging 元数据必须标为 `FULLTEXT_PDF`，质量等级必须为 S 或 A。
- 本地 PDF 的 SHA256 必须与 staging 一致。
- OCR manifest 必须覆盖连续的 PDF 物理页，并逐页有页图 SHA、OCR Markdown 和识别质量字段。
- 导入页统一为 `review_only=1`、`citation_ready=0`、`needs_human_review=1`。
- 任何已经存在的 `doc_key` 都拒绝重复导入。
- 导入前必须提供当前数据库 SHA 和仓库外备份路径；事务完成后必须通过 SQLite integrity、外键和 FTS 对齐检查。

## 当前批次

对象：`GAR-9EAACC89D5`《国共斗争下的自由主义（1941—1949）》。

- 源文件：`data/domestic/academic_public_20260730/pdf/bulk2_59a819121b70.pdf`
- 源 SHA256：`a97bdf981bbbfac4504a69ecf1ad879cdbb4c9698805d02261f573f0f57ffcf0`
- 页数：29；OCR 字符数：33,246；页级平均置信度范围：0.982147–0.993770。
- 正式库状态：16 篇学术解释层全文、76 页，全部 `review_only / citation_ready=0`。

## 可恢复命令

在拥有外部 staging 数据盘的工作树中，先执行 dry-run：

```bash
python3 scripts/domestic/import_academic_ocr_formal_20260813.py \
  --staging-db /path/to/staging_20260730/domestic_staging.sqlite \
  --source-root /path/to/mingmeng-history-research \
  --ocr-dir work/domestic/academic_ocr_sinica_batch_20260813 \
  --report work/domestic/academic_ocr_sinica_formal_20260813/DRY_RUN.json
```

只有 dry-run 通过、并核对当前 SHA 后才能加 `--apply --expected-db-sha ... --backup /private/tmp/...`。

## 不重复入库的版本

`GAR-639C5E94AE`《中国民主同盟历史文献（1941—1949）》是正式出版的一手文献汇编。项目已经有 622 页国内公开扫描/OCR 页级链，因此不再按学术候选复制一份；后续应补版本/出处关系，而不是增加重复页面。

## 引用边界

学术扫描 OCR 只能帮助检索、定位和理解研究论证。正式引用必须回到 PDF 原页，确认作者、刊物/卷期、页码、文字和版本，并写入人工复核说明；任何机器置信度都不能替代该门禁。
