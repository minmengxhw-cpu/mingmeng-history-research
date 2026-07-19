# Grok 候选目录审查

你是数据质量工程师。只审查，不改写候选内容。

## 输入

- `docs/domestic/domestic_candidate.schema.json`
- `work/domestic/minimax/candidates/` 下的 JSONL/JSON/CSV
- `docs/PRD_国内一手史料库.md`
- `docs/_collection-standards.md`

## 检查

1. JSON Schema 和字段类型；
2. URL 是否存在、域名是否属于记录的权威机构；
3. `L0—L4` 是否与证据说明相符；
4. 是否把二手材料误标为一手材料；
5. 档号、日期、标题、形成者的完整性；
6. 标题、日期、来源 URL 和人物的重复项；
7. 与现有数据库文献的潜在重复；
8. `rights_status` 和 `access_mode` 是否有依据；
9. 九个关键事件覆盖情况。

## 输出

只写入 `work/domestic/grok/`：

- `candidate_validation_report.json`
- `candidate_validation_report.md`

每条问题标记 `BLOCKER`、`MAJOR`、`MINOR` 或 `NOTE`，不得直接删除候选记录。
