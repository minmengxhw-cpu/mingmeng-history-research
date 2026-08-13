# DEEPSEEK_PROGRESS.md — 证据审计与研究层建设（最终交付）

分支：`agent/deepseek-domestic-audit-20260803`｜阶段：第 1 个 2 周阶段（2026-08-03 完成）
审计范围：国内文献 525 / 候选 689 / 待复核 29 / 分类孤儿 15 / 事件 1914

---

## 一、阶段目标与完成度

| 验收项 | 状态 | 产出 |
|---|---|---|
| 10 条待复核结论（基线口径，实为 29 条全量） | 完成 | review_dispositions.csv |
| 15 条分类孤儿归属/保留理由 | 完成 | orphan_dispositions.csv |
| 重复/低价值清单 | 完成 | dedup_clusters_review.csv + low_value_list.csv |
| citation 严格门禁报告 | 完成 | citation_gate_pass.csv (284) / failures.csv (405) / report |
| 二手学术 bibliography | 完成 | bibliography_secondary.csv (13 部) |
| 事件—人物—机构—主题关联（1941—1950） | 完成 | relations_*.csv (8 表) |
| 一手/目录线索/二手区分 | 完成 | metadata_normalized.csv（一手 348 / 汇编 254 / 二手 38 / 待定 49） |
| DEEPSEEK_PROGRESS.md + CHECKPOINT | 完成 | 本文档 + DEEPSEEK_CHECKPOINT.md（CK-01…13） |
| 短页面队列复核与 citation 降级 | 完成 | Batch12：220 页处置 + 82 条 citation_ready 降级 |
| 重 OCR 建议 / 抽检 / provenance 补桩 | 完成 | Batch13：69 建议 + 22 抽检 + 11 桩 |

## 二、阶段结论（关键发现汇总）

### 1. 基线口径已被生产库取代
- 基线验收报告（20260728）：142 文档 / 679 候选 / 10 待复核 → 生产库实际：525 文档 / 660 accepted / 29 待复核
- 19 条 accepted→needs_human_review 翻转未同步 `reviewed_at`（staging 侧问题）

### 2. 重复与低价值
- MiniMax 去重 32 簇 / 92 重复对：0 异常；漏检 15 组均判容器/同站非内容重复
- 低价值 102 条（83 目录级 / 15 离线 / 4 LX）
- **重大异常**：DCL-0019—0024 将 22 条《光明報》1947 文章级条目误判为重复并排除（期级 vs 文章级），需恢复建档

### 3. 元数据与证据等级
- 3 条 L1-二手真异常（WS 大公报 → 降 L3）；4 例 URL-仓库错位；10 条汇编误标 press_scan（误报）
- C 级来源（MM1941、8P、ACAD、SH、PP、CAIXIN）仅可作线索

### 4. Citation 门禁（六道关）
- 严格门禁通过 284 条；staging 声称 citation_ready=yes 的 229 条中仅 203 通过
- 26 条被驳（目录级无影像、官网史志页二手、surrogate 转录）；正式库 citation_ready 仍为 0

### 5. 待复核 29 条处置
- 8 条 1946 政协/拒国大/李闻报道 → 降 L3（无原刊核验）；《观察》1947 v3n11 可升级
- 方志 7 条 / 盟贤 5 条 / 资料汇编 3 条 → L4 二手保留；七君子 1937 照片 2 条 → 范围外归档

### 6. 孤儿 15 条
- 12 CIA + 3 archive.org，均为去重删除文档行的外键残留；根因 SQLite FK 未强制
- 建议：开 FK、删除时级联清理分类行

### 7. 关联表（1941—1950）
- 人物 Top：罗隆基 485 / 张澜 256 / 张君劢 217；机构：中共 1395 / 民盟 1064 / 国民党 974
- 主题：马歇尔调处 830 / 政协 718 / 北平接触 533

## 三、交付物清单

`work/deepseek-20260803/`
- `01_inputs/`：22 个只读快照（git 冻结）
- `02_analysis/`：reconciliation_report.json、dedup_clusters_review.csv、missed_duplicates.csv、low_value_list.csv、catalog_as_fulltext.csv、metadata_dictionary.csv、metadata_normalized.csv、metadata_quality_issues.csv、citation_gate_matrix/pass/failures.csv、review_dispositions.csv、orphan_dispositions.csv、relations_*.csv（8 表）、bibliography_secondary.csv、short_pages_quality_audit.csv、entity_alias_map.csv、relations_*_canonical.csv、short_pages_batch12_*.csv、batch1—12 报告 md
- `03_reports/`：DEEPSEEK_CHECKPOINT.md（CK-01…12）、DEEPSEEK_PROGRESS.md（本文件）
- `04_migration/`：batch9/10/12 apply 结果与 dry-run 副本

`scripts/deepseek/`：export + batch1—13 脚本（均带分支守卫；batch9/10/12/13 含 migrate）

## 四、遗留事项（下一 2 周阶段）

1. 正式库落地已完成：29 条审核结论写回、15 条分类孤儿清理；284 条 citation PASS 完成页面级对账，未盲目晋升
2. 《光明報》22 条误排条目已核验恢复：正式库原已存在独立文档/正文/provenance，已撤销 duplicate 结论
3. bibliography 已补录冻结来源中的稳定链接/ISBN/出版年；仍缺稳定链接 9、ISBN 11、出版年 2，待权威书目或版权页核验
4. 同义异名实体规范映射已在研究层完成；正式库落地仍待审批
5. **Batch12 已完成**：220 短页深层处置；82 条不安全 `citation_ready=1` 已降级为 0；空文本 6 条已盖审计章
6. **Batch13 已完成**：69 条重 OCR 参数建议；22 条人工抽检清单待回填；11 条短页 provenance 桩已插入；PNG 伪文本 1 条已清空
7. D7 短正文候选 103 条仍须人工影像抽检后方可个案解除 citation 禁令
8. 国内页无 provenance 全量约 588 条（非短页）待专项补档
9. 重 OCR 尚未执行：需审批后对 P3 手写/空文本 5 条做受控试验

## 五、环境安全记录

- 外部进程多次切分支/删未跟踪文件；审计产物全部提交 git 冻结，01_inputs 快照不受影响
- 恢复命令：`git checkout -f agent/deepseek-domestic-audit-20260803`
- 全部只读约束遵守：未改原始文件、未 OCR、未直接改正式 SQLite
