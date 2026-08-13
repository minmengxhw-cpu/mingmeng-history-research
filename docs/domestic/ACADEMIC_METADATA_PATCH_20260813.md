# 学术元数据增量验收（2026-08-13）

本增量只解决专题解释层的两个精确书目缺口，不把学术文章变成一手史料。

## 入选记录

| external_id | 专题作用 | 等级 | 当前状态 |
|---|---|---:|---|
| `ACADEMIC-20260813-LIU-DAYU-CONSTITUTIONAL-NATIONAL-ASSEMBLY` | 直接解释民盟抵制制宪国大 | B | 书目元数据；作者单位、全文待核 |
| `ACADEMIC-20260813-LIU-DAYU-PCC-PARTICIPATION` | 解释旧政协前后民盟政治参与与国大争议 | B | 书目元数据；作者单位、全文、页码待核 |
| `ACADEMIC-20260813-LU-WENPEI-STATE-BUILDING` | 1945 一大政治建国方案的背景回链 | A | 期刊书目页；页面参考文献列出1945年政治报告，正文未入库 |

1945 年一大另外复用了 staging 中已有的方敏《民盟设计的议会民主制度的特点》元数据；专题卡新增 `民盟政制`、`议会民主制度`，没有重复建同一条记录。

## 证据边界

- 本轮只读取公开书目页、期刊目录页和页面中可见的参考文献元数据；`body_read=false`。
- 三条新增记录均为 `METADATA_ONLY`、`citation_ready=0`、`human_verified=0`。
- 这些记录只出现在国内学术解释层和专题导航层；正式引文仍必须回到国内一手页、稳定全文、页码/章节、SHA256 和人工复核。
- 论文来源入口、期号和页面状态保存在 JSON 元数据中；未把聚合页或摘要伪装成原始全文。

## 可复现应用

```bash
python3 scripts/domestic/import_academic_metadata_patch_staging_20260813.py \
  --db /path/to/work/domestic/staging_20260730/domestic_staging.sqlite \
  --output work/domestic/academic_source_audit_20260813/ACADEMIC_METADATA_PATCH_DRYRUN.json

python3 scripts/domestic/import_academic_metadata_patch_staging_20260813.py \
  --db /path/to/work/domestic/staging_20260730/domestic_staging.sqlite \
  --backup /private/tmp/domestic_staging.sqlite.before_academic_metadata_patch_20260813.sqlite \
  --apply \
  --output work/domestic/academic_source_audit_20260813/ACADEMIC_METADATA_PATCH_APPLY.json
```

脚本拒绝覆盖已有 `external_id`，默认只 dry-run；应用只写私有 staging 表并重建其 FTS，不写正式 `data/research_index.sqlite`，不复制或删除任何正文文件。此次应用后 staging 为 288 条，`PRAGMA integrity_check=ok`。

## 交叉审计

- 9/9 专题有国内页级导航、严格可引用页、学术元数据匹配和境外事件入口。
- `citation_gap=0`、`navigation_gap=0`。
- 总学术专题候选 159 条；1945 一大 6 条 A 级匹配，1946 拒绝国民大会 2 条 B 级直接书目匹配。
