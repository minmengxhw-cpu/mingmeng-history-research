# CC OCR 正式入库 Manifest（2026-07-27）

## 口径

- 验收通过：58 个文档。
- 原始 PDF/图像物理页：3598 页。
- SQLite 检索单元：75 条（按 OCR Markdown/chunk，而非伪造逐页记录）。
- 全部保持 `citation_ready=false`、`needs_human_review=true`。

## 排除

- `P3-023`：OCR issue/article boundaries are still an automatic guess。
- `P3-GXMM-SH`：low-resolution trial-database image requires original review。
- `P3-GXMM-TJ`：low-resolution trial-database image requires original review。

## 安全边界

原始扫描件不入 Git；SQLite 正式库按 `.gitignore` 保持本地，GitHub 只提交 manifest、脚本、验收与阶段总结。
