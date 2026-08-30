# GAR-639 页码身份候选审计与局部登记（2026-08-30）

## 结论

GAR-639《中国民主同盟历史文献（1941—1949）》已经存在于正式 SQLite 的既有页级 OCR 入口中：622/622 页 PDF 页号连续、物理页号连续、来源 SHA256 唯一。基于已归档的逐页视觉身份清单，17 页已经登记明确的书内页码；其余 605 页仍未登记。已有展示层 `pages.page_label` 中有 17 页带书内页码，24 页具有人工作证据状态。

本轮对 PDF 首页、目录/正文分界和分布在 1941—1949 时段的 11 个页码锚点做了定向视觉与本地 OCR 核验。锚点均符合：

```text
printed_page = pdf_page_no - 30
```

现有 OCR 页尾数字启发式在 PDF 第 31—622 页的 592 页窗口中识别出 551 页数字尾行，其中 524 页符合上述偏移，27 页不符合，另有 41 页没有可用数字尾行。这个统计只能作为辅助信号，不能把 OCR 误识别、漏识别或正文中的数字当成书内页码。

因此本轮只将清单中的 17 页登记到 `page_provenance.printed_page`，并把连续 -30 偏移继续保留为 `CANDIDATE_NOT_REGISTERED` 的全范围候选；没有批量改写其余 605 页，没有改变 `citation_ready`，也没有把汇编重刊升格为 1941—1949 年同期原件。登记脚本为 [`scripts/domestic/register_mmhist_explicit_printed_subset_20260830.py`](../../scripts/domestic/register_mmhist_explicit_printed_subset_20260830.py)，数据库备份只保留在本地 `work/`，不入仓。

## 验收边界

校验器为 [`scripts/domestic/validate_academic_gar639_page_identity_candidate.py`](../../scripts/domestic/validate_academic_gar639_page_identity_candidate.py)。它检查候选映射、正式库的来源/文档/页级聚合字段、分布式锚点，以及“全范围未登记、17 页显式登记”的双重状态；不会写 SQLite、不会复制正文、不会删除本地文件。

```bash
python3 scripts/domestic/validate_academic_gar639_page_identity_candidate.py
python3 scripts/domestic/validate_unified_research_platform.py \
  --output /tmp/domestic_unified_platform_gate_20260830_gar639.json
```

## 下一步

若要继续登记其余页面，必须为每个新增分段保留 dated SQLite backup，并提交新的逐页图像核验清单；不得用连续 -30 偏移直接覆盖剩余 605 页。27 个冲突和 41 个缺失尾码仍是全范围候选的未决证据。书内页码登记不等于正文逐字校读，不改变 `citation_ready` 计数，也不关闭九个专题仍开放的 P0 原件缺口。

## 本轮登记范围

登记页为 PDF 第 145、147—165 页中的 17 个清单页，对应书内第 115、117—135 页；PDF 第 146、154—156 页没有被登记，因为它们不在已审清单中。登记前备份哈希为 `aa76c9c3077cdfb40f9c254dd2d03dd9369e9e2f8a68aab8da8f3632426bf7f2`，SQLite 完整性检查和外键检查均通过。
