# 国内学术研究层工作流（2026-08-13）

## 定位

国内平台分成三层：

1. 一手/准一手资料：会议文件、同期报刊、声明、档案条目、第一人称材料。它回答“原文是什么”。
2. 学术研究资料：论文、专著、档案指南、文献整理本和民盟中央/官方历史研究。它回答“如何解释、如何定位争议”。
3. 研究导航：专题对读卡、关键词、时间线和缺口清单。它回答“下一步去哪里找”。

学术研究层不能越级替代一手材料。专题页将国内、境外和学术材料并列展示，但每条材料仍回到自己的来源链。

## 当前 staging 验收快照

本次只读取 `domestic_research_materials` 的书目信息，不读取正文原件，也不写正式库：

- 研究/官方资料：285 条；其中学术研究层 152 条、官方回顾层 133 条。
- 学术文章：96 条；S/A 优先学术记录：119 条。
- 来源等级：S 42、A 92、B 150、C 1。
- 全文状态：179 条仍为 `METADATA_ONLY`；`FULLTEXT_PDF` 6 条、`FULLTEXT_HTML_CANDIDATE` 18 条，其余状态仍需按来源链处理。
- staging `citation_ready` 和 `human_verified` 均为 0；这些条目目前是研究导航和补证队列，不是正式可引用页。
- 规范化题名重复组 15 组、涉及 30 条记录；同文不同版本需要保留版本关系，不能按条目数重复计算论据。
- 机构字段中出现中国社会科学院、民盟中央或高校信号，但这只是元数据匹配，不是独立的985认定或作者任职核验。
- 正式 SQLite 当前已有 15 条学术全文文档：12 条 HTML、3 条可按页提取的 PDF，共 47 页；全部是 `review_only / citation_ready=0`。另外 2 条 S/A PDF（29 页、622 页）无可用电子文本，继续留在 OCR HOLD。

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
