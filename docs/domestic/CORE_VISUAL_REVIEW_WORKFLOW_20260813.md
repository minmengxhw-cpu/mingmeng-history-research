# 国内核心 PDF 页级核验工作流

日期：2026-08-13

核心批次不是自动引用发布器。页级正式引用必须经过：来源文件 SHA256、精确 PDF 页码、原件视觉检查和明确复核说明四道门。

## 只读审计

```bash
python3 scripts/domestic/audit_core_citation_source_pages_20260813.py \
  --render-dir /private/tmp/codex_pdf_review_20260813/pages
```

当前批次中的 108 个 PDF 页里，101 个有精确 `#page=N` 定位并通过来源文件哈希检查；7 个整本书锚点是范围定位或整本 OCR，自动保持待核。当前 101 个精确页已完成授权代理视觉复核并进入正式引用门禁。

## 申请文件

`REVIEW_DECISIONS.json` 必须由审阅者逐页写入 `page_id`、`decision`、`reviewer` 和具体 `note`。说明应记录看到的原 PDF、页码/物理页、来源哈希和任何边界/转录不确定性；不把 OCR 当作原件。

## 应用门禁

默认只读预演：

```bash
python3 scripts/domestic/apply_core_visual_review_20260813.py
```

真正写库时必须显式提供新的备份路径并使用 `--apply`：

```bash
python3 scripts/domestic/apply_core_visual_review_20260813.py \
  --apply \
  --backup /private/tmp/research_index.sqlite.before_core_visual_review_20260813.sqlite
```

脚本会拒绝：数据库 SHA 漂移、来源哈希不匹配、非 PDF、范围页码、缺复核说明或不存在的页级 provenance。应用后重新执行 SQLite integrity、外键和平台回归检查。任何未列入申请文件的页面不会改变。
