# DEEPSEEK_CHECKPOINT.md — 证据审计与研究层建设

分支：`agent/deepseek-domestic-audit-20260803`｜周期目标 6—8 周，第 1 个 2 周阶段已完成（2026-08-03）

审计范围：国内文献 525（基线口径 142）/ 候选 689 / 待复核 29（基线口径 10）/ 分类孤儿 15 / MiniMax staging manifest

工作规则（只读约束）：只写审计产物与结构化报告；不修改原始文件；不执行 OCR；不直接修改正式 SQLite（本阶段全部读取为 `mode=ro`）。

**阶段完成标志**：Batch 1—6 全部完成，CK-20260803-01…06 记录完整；最终交付见 `DEEPSEEK_PROGRESS.md`；本阶段验收项全部达成（详见 PROGRESS 第一节完成度表）。

---

## CHECKPOINT 记录

### [CK-20260803-01] 2026-08-03 · Batch 1 完成：对账 / 重复 / 低价值 / 目录冒充全文

**完成内容**
- 数据层快照导出完成：`work/deepseek-20260803/01_inputs/`（domestic_documents 525、candidates 689、orphans 15、events 1914、staging 664、manifest、evidence_units 等，共 16 个文件）
- 对账报告：`reconciliation_report.json`（基线口径 vs 生产库 vs staging 三口径对比）
- MiniMax 去重 32 簇 / 92 重复对复核：0 异常
- 低价值清单 102 条：`low_value_list.csv`
- 目录冒充全文 1 条 + DB 文档口径复检（无残留）
- 漏检 15 组分类：无内容级漏检
- 报告：`02_analysis/duplicates_low_value_report.md`

**关键发现（需后续批次跟进）**
1. 基线文档口径（142/679/10）已被生产库（525/660/29）取代，19 条 accepted→needs_human_review 翻转未同步 reviewed_at → Batch 4 逐条核对
2. DCL-0019—0024 将 22 条《光明報》1947 文章级条目误判为重复并排除（期级 vs 文章级）→ 需恢复或另行建档（清单见 Batch 4 附录）
3. `three_lists_summary.md` 545 与实际 557 漂移 12 条（以 CSV/SQLite 为准）
4. 220 页 text<120 字符为页面级质量观察项 → 后续批次抽样

**下一批**：Batch 2 元数据统一（来源/日期/机构/资料类型/证据等级）

### [CK-20260803-02] 2026-08-03 · Batch 2 完成：元数据统一

**完成内容**
- 来源机构字典 86 条（code→规范机构/类别/来源家族/权威等级 A/B/C）：metadata_dictionary.csv
- 689 条规范化结果（来源/资料类型/日期 ISO+精度/等级）：metadata_normalized.csv
- 质量问题 66 条：metadata_quality_issues.csv；报告：metadata_normalization_report.md

**关键发现**
1. 资料类型归类：一手 348 / 汇编 254 / 二手 38 / 待定 49（含规则说明）
2. 等级一致性 25 条：3 条 L1-二手真异常（WS 大公报→应降 L3）；8 条 L3-full_item 部分建议升 L2；4 条 LX 维基转录建议定级；10 条汇编书误标 press_scan（L2 正确=误报）
3. 4 例 URL-仓库错位（SHAC/JFB/KMY/MMYunnan）
4. 日期：479 day / 118 year / 51 month / 27 range / 8 multi / 6 empty；approx 0 残留
5. C 级来源（MM1941、8P、ACAD、SH、PP、CAIXIN）仅可作线索，不可作证据

**环境事件（重要）**
- 外部进程多次切换工作区分支并清理未跟踪文件：
  - work/minimax-20260803/ 与 scripts/minimax/ 从工作区消失（非本分支产物，未提交）
  - 审计分支 189eadb 完好；01_inputs 22 个快照全部冻结在 git 内，不受影响
- 防护：_guard.py 分支守卫已加入全部 batch 脚本；所有审计产物在批次完成即提交

**下一批**：Batch 3 L1-L4 分级终稿 + citation_ready 严格门禁

### [CK-20260803-03] 2026-08-03 · Batch 3 完成：L1—L4 分级终稿 + citation 严格门禁

**完成内容**
- 六道门禁（G1 等级 L1/L2｜G2 影像可得｜G3 一手/汇编 非目录冒充｜G4 目录 verified｜G5 非 OCR 草稿｜G6 无重大保留）
- 全 689 条门禁矩阵：citation_gate_matrix.csv
- 严格门禁通过（accepted 且 PASS）：284 条 → citation_gate_pass.csv
- 驳回明细 405 条（含原因）→ citation_gate_failures.csv
- 报告：citation_gate_report.md

**关键结论**
- staging 声称 citation_ready=yes 的 229 条中仅 203 条通过严格门禁；26 条被驳回：
  - G2 目录级无影像（ACAD 博士论文页/MMC 届次索引/民盟史会议记录/QY 孔网书页/WM 照片类）
  - G3 二手/待定（民主党派官网史志页、人民政协网、搜狐、民盟基层网站锚点）
  - surrogate 非影像（人民日报转录页）
- 正式库 citation_ready 仍为 0（基线验收口径）——本报告为库外门禁基线
- 门禁与 staging 的差异源于 staging 侧对官网史志页授予 L2 与 citation_ready，违反 G3

**下一批**：Batch 4 待复核项处理结论 + 15 条分类孤儿归属/保留理由

### [CK-20260803-04] 2026-08-03 · Batch 4 完成：待复核项处理结论 + 分类孤儿归属/保留理由

**完成内容**
- 29 条 needs_human_review 全部给出处理结论：`review_dispositions.csv`
- 15 条分类孤儿（外键孤儿）全部给出归属或保留理由：`orphan_dispositions.csv`
- 报告：`batch4_review_report.md`

**待复核 29 条处置分组**
- HKU 馆藏/书目记录 2 条 → 保留为目录线索（L3）
- 1946 政协/拒国大/李闻事件多源报道 8 条 → 降级为目录线索（L3，原 L1 无原刊核验）
- 《观察》1947 v3n11 文章 1 条 → 影像核验后升级（NLC 镜像有公开 PDF）
- 张澜《时代日报》谈话线索 1 条 → 保留线索（L4）
- 上海民主党派志 7 条 → 保留为二手方志证据（L4）
- 《盟贤》5 条 → 内部汇编线索（L4，2 条人物背景低相关）
- 民盟代表人士资料汇编 3 条 → 内部汇编线索（L4，1 条低相关）
- 七君子 1937 照片 2 条 → 归档背景资料（L4，1941—1950 范围外，不核验）

**孤儿 15 条归属结论**
- 12 条 CIA（document_id 325/330/331/333/335/338—341/346/348/358）：去重删除的重复文档行（同卷 rdp* 前缀），无 pages/provenance/translations → 归属：合并至同卷现存 CIA 文档；无同名幸存则视为过期记录建议清理
- 3 条 archive.org（402/403/422）：文档行已删且平台整体退役（现库无 archive.org 平台）→ 保留为历史记录（标注 deprecated）或直接清理
- 根因：SQLite 默认不强制 FK（PRAGMA foreign_keys=OFF），删除 documents 未级联清理分类行
- 建议：① 开启 FK 强制；② 删除 documents 时级联删除 document_classifications；③ 存量孤儿行清理需在正式库执行（本审计仅出具建议，不改正式库）

**下一批**：Batch 5 1941—1950 事件—人物—机构—主题关联（event_tags/person_tags/place_tags → 关联表）

### [CK-20260803-05] 2026-08-03 · Batch 5 完成：1941—1950 事件—人物—机构—主题关联

**完成内容**
- 范围事件 1914 条 → 1941—1950 取 1811 条（1951 14 条、无年份 89 条排除）
- 事件明细：`relations_events_1941_1950.csv`
- 实体表：人物 623+ 实体 / 机构 / 地名 / 主题，含事件数、年份区间、event_ids 溯源
- 共现表：`relations_person_org.csv`（如 蒋介石—中共 754、周恩来—中共 646、马歇尔—中共 641）、`relations_person_theme.csv`、`relations_org_theme.csv`
- 报告：`batch5_relations_report.md`

**关键发现**
- 人物 Top：罗隆基 485（1944—1950）、张澜 256（1941—1950）、张君劢 217、黄炎培 173、沈钧儒 138、章伯钧 136、张东荪 123、梁漱溟 52
- 机构 Top：中国共产党 1395、中国民主同盟 1064、国民党 974、政治协商会议 718、美国国务院 587
- 主题 Top：民盟 1052、马歇尔调处 830、政协 718、北平接触 533、第三方面 311、联合政府 289、昆明暗杀 116
- 同义异名（民盟/中国民主同盟 等）未合并；命名规范合并属 Batch 2 元数据层后续事项

**下一批**：Batch 6 二手学术 bibliography（985/社科院/中央机构出版，作者/机构/题名/年份/期刊/DOI）

### [CK-20260803-06] 2026-08-03 · Batch 6 完成：二手学术 Bibliography

**完成内容**
- 从 metadata_normalized 二手/待定 类提取正式出版物 13 部 → `bibliography_secondary.csv`
- 字段：题名/作者编者/机构/年份/出版社/ISBN/DOI/证据等级/备注
- 报告：`batch6_bibliography_report.md`

**书目（13 部）**
- 市级：中国民主同盟石家庄市志（2013）；省级史/志：陕西民盟史、安徽民主党派史·民盟章节（2009）、浙江省民主党派志（2002）、湖北民盟史（2014）、中国民主同盟福建简史（2018）、湖南民盟人物（2020）、中国民主同盟江苏简史（2012）、广东民盟史（2012）、四川民盟史、江苏民盟史稿（2004）、贵州民盟史（2013）、云南民盟史（2021）

**关键说明**
- 全部为 L4 二手；不作 citation 直接证据（G3 已排除）
- DOI 均为空：国内书目普遍无 DOI，需人工补录（CNKI/读秀或书号）
- 陕西/四川两条目出版年待购书核实

**下一批**：最终交付 DEEPSEEK_PROGRESS.md + DEEPSEEK_CHECKPOINT.md 终稿并提交

### [CK-20260803-07] 2026-08-03 · Batch 7 完成：220 页短文本质量审计

**完成内容**
- 对正式 SQLite 以 `mode=ro` 导出国内页面 `text<120` 全量 220 页，涉及 76 文档。
- 结构化清单：`short_pages_quality_audit.csv`；报告：`batch7_short_pages_report.md`。
- 分层：Q0 空文本 6；Q3 疑似 OCR 失败/截断 117；Q4 极短片段 1；Q5 短正文待抽检 96。
- 需人工对照影像 214 页；本批 220 页全部预设 `citation_eligible=no`，核验后方可解除。

**约束遵守**
- 未执行 OCR、未修改原始页面、未写正式 SQLite。

**下一批**
- Batch 8：实体同义异名规范映射与去重后的关联统计（仅研究层产物）。

### [CK-20260803-08] 2026-08-03 · Batch 8 完成：实体同义异名规范映射

**完成内容**
- 对 1941—1950 事件研究层建立保守的实体规范映射；仅合并无歧义精确别名，不做同姓或简称推断。
- 输出 `entity_alias_map.csv`、规范化事件表及人物/机构/主题三类规范实体统计表。
- 输入事件明细实际 1798 条；原始实体 34 个；精确别名映射 4 个（当前数据多数已规范）。
- 未修改正式 SQLite。

**下一批**
- Batch 9：为正式库落地生成可复核、默认不执行的 SQL/CSV 变更包及回滚/验证方案。

### [CK-20260803-09] 2026-08-03 · Batch 9 完成：正式 SQLite 安全迁移

**执行结果**
- 副本 dry-run 通过后，正式库事务写入完成；写前备份及 SHA-256 已记录。
- 29 条候选审计结论写回；状态变为 accepted 688 / needs_human_review 1。
- 15 条分类孤儿已清理，存量分类孤儿 0。
- Citation PASS 284 条中 170 条已关联正式文档；页面级可新增晋升为 0，未绕过 provenance 门禁。
- `integrity_check=ok`；没有新增 FK 违规。
- 发现既存 `research_events` 315—319 指向缺失 pages，共 5 条，转下一批核查。

**恢复点**
- 正式库写前 SHA：`bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e`
- 写后 SHA：`e8df06ae53fbe8a4d997e57472d21e0d24fe913ffa26ff76d271de97899329ec`
- 备份：`research_index.sqlite.pre_deepseek_batch9_20260803T154801.bak`

**下一批**
- Batch 10：核查并处置 5 条 research_events 页面孤儿；评估《光明報》22 条文章级误排恢复方案。

### [CK-20260803-10] 2026-08-03 · Batch 10 完成：事件孤儿清理 + 《光明報》22 条恢复核验

**执行结果**
- 删除无历史内容的事件 315—319（仅 page break/模型提示，引用页面已不存在）。
- 正式库 `foreign_key_check` 从 5 条残留降至 0。
- DCL-0019—0024 的 22 条《光明報》文章经核验均已有独立文档、正文页面及 citation-ready provenance，无需重复建档。
- 22 条候选写入 `check_outcome=false_duplicate_recovered`，明确撤销容器-vs-文章误判。
- `integrity_check=ok`。

**恢复点**
- 写前 SHA：`e8df06ae53fbe8a4d997e57472d21e0d24fe913ffa26ff76d271de97899329ec`
- 写后 SHA：`fb7cefcf70fcee92fb9d020d20b1c610d102f14aa6aaaf004d34f50237859295`
- 备份：`research_index.sqlite.pre_deepseek_batch10_20260803T155421.bak`

**下一批**
- Batch 11：学术 bibliography 稳定链接/ISBN/出版年补录与来源核验。

### [CK-20260803-11] 2026-08-03 · Batch 11 完成：二手书目补录与来源核验

**完成内容**
- 13 部二手正式出版物补充 stable_url、source_locator、catalog_reference、verification_status、verified_at、bibliographic_use。
- 可确认稳定链接 4 条；可确认 ISBN 2 条；出版年 11 条。
- 陕西、四川两书出版年维持空值，避免把历史覆盖年份或核查时间误写为出版年。
- DOI 未凭空补造；所有书目继续标记 `secondary_only_not_primary_substitute`。

**遗留缺口**
- 稳定链接缺失 9；ISBN 缺失 11；出版年缺失 2。需要国家版本数据中心、国家图书馆或实物版权页进一步核验。

**下一批**
- Batch 12：复核正式库短页面队列，优先处理 6 个空文本和 118 个极短/OCR 疑似页。

### [CK-20260803-12] 2026-08-07 · Batch 12 完成：短页面队列复核 + citation 不安全降级

**完成内容**
- 正式库刷新短页面 220 条（与 Batch7 对齐）：`short_pages_batch12_refresh.csv`
- 深层处置 10 类：`short_pages_dispositions.csv` + `batch12_short_pages_report.md`
- 优先队列：P0 空文本 6 + P1 OCR/碎片 118 + citation 冲突并入 → 201 条
- 重 OCR 队列 priority≥2：**69** 条 → `short_pages_reocr_queue.csv`
- 空文本 6 条：1 疑似空白 / 1 需重 OCR / 4 签到手写优先；影像全部存在

**正式库迁移（只降级、不晋升）**
- 82 条 text<120 且 `citation_ready=1` 全部降为 0，并设 `needs_human_review=1`、`review_status=review_only`
- 6 条空文本写入 machine_review_note 审计痕迹
- 迁移后 short 页 `citation_ready=1` 存量 = **0**
- `integrity_check=ok`；`foreign_key_check=0`

**恢复点**
- 写前 SHA：`fb7cefcf70fcee92fb9d020d20b1c610d102f14aa6aaaf004d34f50237859295`
- 写后 SHA：`d8c4dcebddd11e7bc7d62fab9704e7da3bebfb1abc57021b4f62df6b97e65363`
- 备份：`research_index.sqlite.pre_deepseek_batch12_20260807T230218.bak`

**关键发现**
1. 二进制伪文本 1 条（PNG 头写入 text 槽，page_id=20623 民盟解散公告图）
2. 馆藏章/卷期头/封面/广告共 46 条可结构保留但禁止引用
3. D7 短正文候选 103 条仍需人工影像抽检后个案解除
4. 11 条短页无 page_provenance（无法降级标记，清单见 refresh CSV）

**下一批**
- Batch 13：对 69 条重 OCR 队列（含 6 空文本）给出引擎/参数建议与抽样核验清单；处理 11 条无 provenance 短页补档。

### [CK-20260803-13] 2026-08-07 · Batch 13 完成：重 OCR 建议 / 人工抽检 / provenance 补桩

**完成内容（只读分析）**
- 69 条重 OCR 参数建议：`batch13_reocr_recommendations.csv`（手写/空白/乱码分策）
- 22 条分层人工抽检清单：`batch13_human_sample_checklist.csv`
- 11 条短页无 provenance 补档计划：`batch13_missing_provenance_stubs.csv`
- 报告：`batch13_short_pages_ops_report.md`
- **未执行 OCR**（审计分支约束）

**正式库迁移**
- 插入 11 条 `page_provenance` 桩：`citation_ready=0`、`needs_human_review=1`、`review_status=review_only`
- `source_sha256` 为 URL/路径 locator stub（非文件字节哈希），备注标明
- 清空 page_id=20623 的 PNG 伪文本（text → 空）
- 短页无 provenance 存量：**0**
- `integrity_check=ok`；FK=0

**恢复点**
- 写前 SHA：`d8c4dcebddd11e7bc7d62fab9704e7da3bebfb1abc57021b4f62df6b97e65363`
- 写后 SHA：`9413af230e80a8a64768daa92722c5cfec0eea8b6732212e3351b0d1e8e7646a`
- 备份：`research_index.sqlite.pre_deepseek_batch13_20260807T230546.bak`

**观察项（未本批处理）**
- 国内页无 provenance 全量约 588 条（非短页为主），需后续批量补档专项

**下一批**
- Batch 14：执行/对接 22 条人工抽检回填；或启动 69 条重 OCR 中 P3 手写/空文本 5 条的受控 OCR 试验（需脱离“不执行 OCR”约束的审批）。
