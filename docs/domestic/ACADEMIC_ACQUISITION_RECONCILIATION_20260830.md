# 国内学术资料来源身份对账（2026-08-30）

## 结论

本轮对 `GAR-2677452CA0` 的全文入口做了身份核对。记录目标是于光远 1992 年的《对抗战建国协进会成立会的回忆——为民盟史研究提供一点史料》，但同一公开入口实际对应的页面标题是《党派史话｜民盟历史知识两则》，与 `GAR-1002A409DD` 相符。该页面只能作为后期转载/背景线索，不能冒充目标文章的完整正文。

因此采取以下收口决定：

- `GAR-2677452CA0` 降为 `METADATA_OR_WRONG_PAGE`，保留原始书目目标和公开入口；
- 将其从可执行的全文取证队列移出，禁止正式学术全文导入；
- `GAR-1002A409DD` 作为独立的 B 类背景记录保留，不与于光远文章合并；
- 不重复 OCR、不写入正式 SQLite、不删除或移动任何本地资料；
- 目标文章仍等待其自身的完整、可复查正文或扫描版本。

对账结论只保留元数据、身份映射和文件 SHA，不提交正文或本地路径。机器验收文件为 [`data/domestic/academic_acquisition_reconciliation.json`](../../data/domestic/academic_acquisition_reconciliation.json)，校验器为 [`scripts/domestic/validate_academic_acquisition_reconciliation.py`](../../scripts/domestic/validate_academic_acquisition_reconciliation.py)。

## 更新后的覆盖口径

| 指标 | 当前值 | 解释 |
|---|---:|---|
| 学术元数据 | 288 | 书目和结构化发现层，未因本轮而减少 |
| 全文取证队列 | 23 | P0 5、P1 12、P2 1、P3 5 |
| S/A 优先队列 | 17 | 其中 16 条有正式学术来源行，GAR-639 复用既有同 SHA 页级 OCR |
| 原始正式来源行覆盖 | 16/23 | GAR-639 和 6 条 B 类背景记录仍不是 `domestic_academic_fulltext` 行 |
| 有效 S/A 优先覆盖 | 17/17 | GAR-639 通过复用审计；这不等于 citation-ready |
| B 类背景记录 | 6 | 继续保留为发现/背景层，不作为优先全文强制缺口 |

“有效 S/A 优先覆盖 17/17”只说明队列已经有正式来源行或可复用的同 SHA 页级入口；所有学术全文仍保持 `citation_ready=0`，不能替代九个专题的一手原件闭环。统一门禁的内容状态继续是 `PASS / OPEN_PRIMARY_GAPS`。

## 验收

```bash
python3 scripts/domestic/validate_academic_acquisition_reconciliation.py
python3 scripts/domestic/validate_academic_layer.py
python3 scripts/domestic/audit_academic_formal_coverage.py
python3 scripts/domestic/validate_unified_research_platform.py \
  --output /tmp/domestic_unified_platform_gate_20260830.json
```

所有命令均只读取版本化元数据、队列和正式库的结构/标识；不会重新读取来源正文、执行 OCR、写正式库或删除文件。
