# 国内学术研究层工作流（2026-08-13）

## 定位

国内平台分成三层：

1. 一手/准一手资料：会议文件、同期报刊、声明、档案条目、第一人称材料。它回答“原文是什么”。
2. 学术研究资料：论文、专著、档案指南、文献整理本和民盟中央/官方历史研究。它回答“如何解释、如何定位争议”。
3. 研究导航：专题对读卡、关键词、时间线和缺口清单。它回答“下一步去哪里找”。

学术研究层不能越级替代一手材料。专题页将国内、境外和学术材料并列展示，但每条材料仍回到自己的来源链。

## 当前 staging 验收快照

本次只读取 `domestic_research_materials` 的书目信息，不读取正文原件，也不写正式库：

- 研究/官方资料：288 条；其中学术研究层 155 条、官方回顾层 133 条。
- 学术文章：99 条；S/A 优先学术记录：120 条。
- 来源等级：S 42、A 93、B 152、C 1。
- 全文状态：182 条仍为 `METADATA_ONLY`；`FULLTEXT_PDF` 6 条、`FULLTEXT_HTML_CANDIDATE` 18 条，其余状态仍需按来源链处理。
- staging `citation_ready` 和 `human_verified` 均为 0；这些条目目前是研究导航和补证队列，不是正式可引用页。
- 规范化题名重复组 15 组、涉及 30 条记录；同文不同版本需要保留版本关系，不能按条目数重复计算论据。
- 机构字段中出现中国社会科学院、民盟中央或高校信号，但这只是元数据匹配，不是独立的985认定或作者任职核验。
- 正式 SQLite 当前已有 16 条学术全文文档：12 条 HTML、3 条可按页提取的 PDF 和 1 条本地 PaddleOCR 扫描 PDF，共 76 页；全部是 `review_only / citation_ready=0`。另外 2 条 S/A PDF（29 页、622 页）无可用电子文本，继续留在 OCR HOLD。
- 清洁 checkout 若没有私有 staging SQLite，`/domestic/academic` 会读取提交的 `data/domestic/academic_layer_snapshot.json` 展示 288 条审计元数据，并同时标出正式 SQLite 的 16 条 `review_only` 全文；快照不含正文、私有路径或授权文件，不会改变任何引用门禁。
- 清洁 checkout 的 `/domestic/search?scope=research` 和专题学术交叉索引同时读取 `data/domestic/academic_layer_metadata.json`，因此 288 条资料可按题名、作者、机构、时期和结构化主题检索；该索引由 `scripts/domestic/export_academic_metadata_index_20260820.py` 从 staging 只读导出，明确排除正文、OCR 文件和本地路径。
- 研究资料检索还支持 `tier=S|A|B|C` 与 `availability=fulltext|candidate|discovery` 筛选：先找高质量候选，再处理全文状态；筛选结果仍明确显示 `citation_ready=0`，不会把稳定全文误标为正式引文。
- 版本化的 `data/domestic/academic_fulltext_priority_queue.json` 从同一份学术元数据索引生成 24 条全文取证队列：P0 稳定全文 5 条、P1 全文候选 13 条、P2 稳定背景 1 条、P3 候选背景 5 条。队列只包含安全书目字段和下一步动作，不读取正文、不包含本地路径、不写正式库，并优先排列 S/A 记录。
- 统一平台门禁在 staging 审计报告不可用时也回退到同一份快照，并在报告中标注 `source=tracked_metadata_snapshot`；因此页面统计和门禁统计不会因 checkout 是否挂载私有 staging 而分叉。

## 分级与引用链

分级口径见 `data/domestic/academic_source_policy.json`。每条学术资料按以下顺序推进：

`研究记录 → 来源入口/目录 → 本地文件或稳定全文 → 页码/章节 → SHA-256 → 复核状态 → citation-ready`

缺任一关键环节时，保留在元数据、全文候选或待核队列；摘要、目录页、聚合页、机器 OCR 和转载链不能自动进入正式引文。

## 与九个专题的连接

`data/domestic/topic_comparison_cards.json` 为九个专题提供解释卡，明确：

- 国内资料可回答什么；
- 境外资料可回答什么；
- 哪些内容不能直接互证；
- 学术文章在该专题中承担什么解释职责；
- 下一步要补哪一类原件、页码或档号。

专题页入口：`/research`；学术层入口：`/domestic/academic`；研究资料检索：`/domestic/search?scope=research`。

常用筛选入口：

```text
/domestic/search?scope=research&tier=S
/domestic/search?scope=research&tier=S&availability=candidate
/domestic/search?scope=research&availability=fulltext
```

筛选只是研究队列排序，不是证据等级提升；正式引用仍需来源入口、稳定全文、页码/章节、SHA-256、复核状态和 `citation-ready` 全部闭合。

全文取证队列可复现：

```bash
python3 scripts/domestic/build_academic_fulltext_priority_queue_20260821.py \
  --input data/domestic/academic_layer_metadata.json \
  --output data/domestic/academic_fulltext_priority_queue.json
```

P0 的“稳定全文”只表示已有可访问的 PDF/HTML 入口，仍要核对版本、页码、作者/机构和哈希；P1 的“全文候选”先做来源入口、权限和版本核验，只有确认是扫描件时才做定向 OCR。已有电子文本的资料不重复 OCR，任何候选都不会自动变成正式引文。

学术层总览同时展示版本化的 `academic_topic_crosswalk.json`：按 9 个国内专题显示学术匹配数量，并可直接回到专题对读和国内一手覆盖页；交叉表只使用书目/结构化元数据，`body_read=false` 不变。

## 可复现检查

```bash
python3 scripts/domestic/validate_topic_comparison_cards.py
python3 scripts/domestic/audit_academic_source_layer_20260813.py \
  --db work/domestic/staging_20260730/domestic_staging.sqlite \
  --output work/domestic/academic_source_audit_20260813/REPORT.json
```

审计脚本只读元数据，`body_read=false` 是硬性输出；它不会把学术资料写入正式库，也不会改变 citation gate。

## 下一阶段完成标准

1. S/A 层中与九专题直接相关的条目完成作者、机构、日期、DOI/ISBN或稳定 URL 的补齐。
2. 同文/版本重复组完成关系标注，检索结果不再把转载误计为独立证据。
3. 优先的全文候选完成页码或章节定位；无页码的网页只保留为研究入口。
4. 学术资料与国内一手页级证据在专题页形成可点击的对读关系。
5. 任何学术条目只有在独立来源、稳定全文/页码、哈希和复核齐全后，才可申请正式引用；否则继续保持研究层状态。

专题页的学术候选匹配使用 `events`、`historical_periods`、`people`、`places` 等结构化元数据，并辅以题名/作者/机构字段；它不是正文语义判断。每条候选都提供“研究资料”“一手对照”和来源入口，读者可以从解释层回到对应专题的一手证据区。研究资料检索结果还会在正式全文已入库时显示“正式全文页”；没有 staging 的清洁 checkout 会回退到正式 SQLite 的学术全文索引。

```bash
python3 scripts/domestic/audit_academic_topic_crosswalk_20260813.py \
  --db work/domestic/staging_20260730/domestic_staging.sqlite \
  --output work/domestic/academic_source_audit_20260813/TOPIC_CROSSWALK.json
```

交叉审计报告必须保留 `body_read=false`；某专题匹配为 0 时应显示为资料缺口，而不是用宽泛关键词强行填充。

## 2026-08-13 学术元数据增量

- 1945 年一大新增 `民盟政制`、`议会民主制度` 专题词，复用现有首都师范大学方敏学术记录，不重复建库。
- 1945 年一大新增 1 条中国科学技术大学作者书目，期刊页面的参考文献直接列出 1945-10-11 民盟临时全国代表大会政治报告；该条仍是背景解释和回链入口。
- 1946 年拒绝国民大会新增刘大禹、王球云两条 2012 年论文书目，分别为《论民盟与国民党的“制宪国大”》和《旧政协前后民盟的政治参与（1945—1946）》。两条暂为 B 级、`METADATA_ONLY`，作者单位、全文和页码仍待核。
- 增量清单见 `data/domestic/academic_metadata_additions_20260813.json`；应用脚本默认 dry-run，正式应用需显式 `--apply --backup`，不写 formal SQLite、不复制正文。

交叉审计结果：9 个专题均有学术元数据候选，合计 159 条；其中 1945 年一大 6 条 A 级、1946 年拒绝国民大会 2 条 B 级直接书目匹配。`citation_ready=0` 和 `human_verified=0` 仍保持不变。

## 2026-08-22 学术层角色清理

本轮复核将 2 条“真实缺口说明”从学术研究记录中单独标为 `RESEARCH_GAP_NOTE`：

- `GAR-220939F16F`：1942—1943 民主政团同盟组织扩展专文公开缺口说明。
- `GAR-C36FE834C9`：章伯钧、胡愈之、邹韬奋民盟专论 CNKI 待补缺口说明。

这两条记录保留在元数据索引中，用于追踪尚未取得的材料，但不计入学术专题交叉、全文取证队列或高质量文章展示。当前索引仍为 288 条，原始学术研究记录 155 条、文章 99 条、S/A 记录 120 条；全文取证队列仍为 24 条（P0 5、P1 13、P2 1、P3 5），交叉表仍为 9 个专题、159 条匹配。这样既不丢失缺口信息，也避免把“没有找到资料”的任务记录误当成学术成果。

验收要求：`academic_crosswalk_eligible=false` 的记录不得出现在 `academic_topic_crosswalk.json` 的 `shown_record_ids`，不得进入 `academic_fulltext_priority_queue.json`，且应用检索页必须显示其为研究缺口说明，而不是可引用文章。`citation_ready=0`、`human_verified=0` 和 9 个国内一手缺口继续保持原状。
