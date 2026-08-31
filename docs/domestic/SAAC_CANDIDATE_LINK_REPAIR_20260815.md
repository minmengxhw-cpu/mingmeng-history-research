# SAAC 官方档案候选—正式文档链路修复（2026-08-15）

## 结论

本批没有新增正文，也没有改变任何页面的 OCR 审核状态或 `citation_ready` 状态。正式库中已经存在的 SAAC 官方扫描/OCR 文档，原来有 8 条新的核心候选记录没有回指对应文档；本次用显式、可复核的文档 ID 映射补齐了双向关联：

- `domestic_candidates.ingested_document_id`：279 → 287；
- `documents.ingested_candidate_id`：215 → 223；
- 新增映射：8 条候选 ↔ 8 篇正式文档；
- `strict_human_citation_pages` 保持 201，不因链路修复而增加；
- 页面 provenance、OCR 文本、`review_only`/人工复核状态均未改动。

## 显式映射

| 候选 | 正式文档 ID | 内容范围 |
|---|---:|---|
| `domestic:SAAC:1948-05-01-01` | 1510 | 1948-05-01 召开政治协商会议电报 |
| `domestic:SAAC:1948-08-01-01` | 1514 | 1948-08-01 新政协时间地点电报 |
| `domestic:SAAC:1948-10-01-01` | 1537 | 1948-10-01 沈钧儒、谭平山等电报 |
| `domestic:SAAC:1949-02-01-01` | 1513 | 1949-02-01/02 56 名民主人士电报及复电 |
| `domestic:SAAC:1949-09-21-01` | 1538 | 政协一届全体会议单位及代表名单 |
| `domestic:SAAC:1949-09-21-02` | 1539 | 政协一届全体会议代表签名册 |
| `domestic:SAAC:1949-09-21-03` | 1542 | 政协一届全体会议程序 |
| `domestic:SAAC:1949-09-21-04` | 1543 | 政协一届全体会议主席团名单 |

映射写入脚本为 [`link_existing_saac_candidates_20260815.py`](../../scripts/domestic/link_existing_saac_candidates_20260815.py)。脚本拒绝标题相似度推断，只接受文件内的显式映射；运行前检查候选来源为 `saac.gov.cn`、正式文档为 SAAC OCR、页数与页级 provenance 对齐，并在 apply 前要求数据库 SHA 和新备份路径。

## 验收证据

- dry-run：`work/domestic/saac_candidate_links_20260815/DRY_RUN.json`，8/8 映射通过；
- apply：`work/domestic/saac_candidate_links_20260815/APPLY.json`，`integrity_check=ok`、外键违规 0、页/FTS 对齐；
- apply 前数据库 SHA256：`ea2e0e5d4f329621f2e4baec7c531818f53428cd5457752cc20bddfb42e62b0b`；
- apply 后数据库 SHA256：`29182122722f2b8ee64f78e266fb79d89fab6e640498d8a1590e25681c848f26`；
- 备份：`<local-user>/<local-checkout>/formal-db-backups/research_index.sqlite.saac-links-20260815.pre.bak`；
- manifest 校验：`scripts/closeout/verify_research_index_manifest.py` PASS；
- 全平台门禁：`work/domestic/unified_platform_gate_after_saac_links_20260815/REPORT.json` PASS，9/9 研究包通过，36/36 问题路径可达，研究内容状态仍为 `OPEN_PRIMARY_GAPS`。

## 证据边界

这次修复只回答“已在库中的 SAAC 记录究竟对应哪个候选”的数据治理问题。它不表示所有 SAAC 目录项均已取得正文，也不表示机器 OCR 已成为正式引文。尚未有正式文档的核心候选仍保留在获取队列中；下一步应继续补充 1941/1944/1946/1947 的独立原始记录，并对已有 `review_only` 页面做人工页级复核。
