# Batch 10 · 事件孤儿清理与《光明報》22 条恢复核验

执行时间：2026-08-03 15:54

## 1. Research events

删除事件 ID 315—319，共 5 条。判断依据：

- 页面引用均已不存在；
- 内容仅为 `--- page break ---` 或模型对空分页符的提示语；
- 无人物、机构、地点和主题实体；
- 不构成历史事件，也不应迁移至其他页面。

删除后 `PRAGMA foreign_key_check` 为零行。

## 2. 《光明報》22 条文章级记录

DCL-0019—0024 的 22 条记录曾因与期级容器共享 PDF URL 而被判为 duplicate。正式库核验显示：

- 22/22 候选均存在；
- 22/22 均有独立 `documents`；
- 22/22 均有文章页面与正文；
- 22/22 均已有 citation-ready provenance；
- 因此不需要重复创建文档，而是将其审核结论明确改为 `false_duplicate_recovered`。

明细见 `guangmingbao_22_recovery_verification.csv`。

## 3. 安全记录

- 写入前 SHA：`e8df06ae53fbe8a4d997e57472d21e0d24fe913ffa26ff76d271de97899329ec`
- 写入后 SHA：`fb7cefcf70fcee92fb9d020d20b1c610d102f14aa6aaaf004d34f50237859295`
- 备份：`research_index.sqlite.pre_deepseek_batch10_20260803T155421.bak`
- `integrity_check=ok`
- `foreign_key_check=0`
