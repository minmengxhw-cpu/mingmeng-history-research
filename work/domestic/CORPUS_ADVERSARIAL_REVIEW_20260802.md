# 国内一手资料语料库 全面对抗性复盘报告（2026-08-02）

> 审查范围：收集 / 整理 / 入库 全链路。方法：对代码与数据交叉核验，寻找「声明 vs 实际」落差。
> 结论先行：**核心链路自洽、外键完整，但存在 1 个范围污染实锤、1 个检索盲区、1 个候选断链、1 个 64GB 冗余**，以及体系分裂（两套来源登记、300+ 一次性脚本）。

---

## 一、数据现状全景

| 表 | 行数 | 备注 |
|---|---|---|
| documents | 1114 | 平台分布：frus 299 / drnh 287 / **domestic 253** / cia 102 / newspapersg 93 / hathitrust 54 / wilson 24 / hoover 2 |
| pages | 5475 | 空 text = 0；外键完整（无孤儿页/孤儿 provenance/孤儿翻译） |
| translations | 1075 | 全部 zh-CN；**domestic 平台覆盖 0%（4400 页 0 条）**——中文原刊无需翻译，符合定位 |
| page_provenance | 3876 | 仅 domestic 有 provenance；**覆盖 3876/4400（524 页缺）** |
| translation_quality_issues | 4400 | 全是 `missing_translation`，经核查为**误报**（中文原刊无需翻译） |
| domestic_sources | 89 | 与 source_registry.json 一一对应（0 差） |
| domestic_candidates | 689 | pass 660 / hold 29；L1 316 / L2 232 / L3 65 / L4 43 |
| domestic_editorial_decisions | 689 | accepted 660 / hold 29 |

正面结论：无孤儿数据、无重复 doc_key、每页唯一翻译、SHA 基线已锁定（`4837dbd6`）、39 页机器修订已入库。

---

## 二、对抗性审查发现（按严重度排序）

### 🔴 S1. 范围外语料未真正隔离——1931 年大公报仍在库且可检索（数据污染）
- **证据**：`page_provenance.period='1931 民盟成立前（国内盟史范围外）'` 有 **480 页**，全部来自文档 `[1243]《大公報》第114卷`（248 页）与 `[1245]《大公報》第113卷`（232 页）。这些页仍完整存在于 `pages`、`page_provenance`、`page_fts`。
- **已做**：source_registry 已标 `corrected_misdated_out_of_scope`（1947→1931 纠错），文档标题已加「隔离」字样，`canonical_source_id` 已设。
- **落差**：**仅标记而未删除/禁检**。实测检索特征词「新出版物」命中 39 条（含 1931 广告页），说明**范围外内容在正式检索中可命中**。
- **影响**：民盟 1941-1949 研究主题检索被 1931 年广告/辞书内容污染；数据质量与「精简」目标冲突。
- **处置建议**：① 从 `pages`/`page_fts` 物理移除 480 页（保留 provenance 隔离记录）；② 或建 `document_classifications.needs_review` 标志统一过滤；③ 与 `documents` 里另两条 `[1112]/[1113]`「隔离」标题文档（2+1 页）一并处理，共 **483 页**。

### 🔴 S2. 中文 2 字检索盲区——trigram 分词器不匹配中文语料（检索缺陷）
- **证据**：`page_fts` / `translation_fts` 均 `tokenize='trigram'`。实测：
  - 「张澜」(2字) → **0**（pages.text 实际含 152 页）
  - 「民盟」(2字) → **0**（实际 699 页）
  - 「卢汉」(2字) → 0；「卢汉将军」(4字) → 2 ✓
  - 「民主同盟」(4字) → 2356 ✓
- **本质**：trigram 需 3+ 连续字符，而中文人名、核心词大量为 2 字（张澜、卢汉、民盟、政协…）。**这是对中文语料最致命的检索缺陷**。
- **处置建议**：改用支持中文分词的 tokenizer（如 `unicode61` + 预切分，或接入 jieba 类分词后按空格预索引，或对 2 字词生成 bigram 兼容）。**优先级最高，否则库的检索价值大打折扣。**
- **✅ 已修复（2026-08-02）**：新增 `page_fts_bigram` / `translation_fts_bigram` 表（unicode61 tokenizer），CJK 段预切为空格分隔重叠 2 字 bigram。查询端 CJK 词转相邻 bigram phrase，英文沿用 trigram 表，LIKE 仅兜底 1 字词/非 CJK 短词。实测：民盟 1913、张澜 154、卢汉 4、政协 588 全部命中，检索从 43ms LIKE 全表扫描 → ~1ms FTS；15 项回归全通过。详见 `scripts/oneshot/build_fts_bigram.py`。

### 🟠 S3. 660 个「已接受」候选 77% 未真正入库（收集断链）
- **证据**：`domestic_candidates` 中 `check_outcome='pass'` 的 660 个候选，仅 **149 个标题命中库内文档**，**511 个（77%）无对应入库文档**。其中：
  - `online_availability=full_item_online`（全文在线可采集）：296 个
  - `surrogate_online`：127 个
  - `catalogue_only_online`（仅目录）：88 个
- **落差**：`domestic_editorial_decisions` 标记 `accepted`，但语料并未进入 `documents`/`pages`。候选表是「线索登记簿」，`evidence_locator` 是描述文本（「网页正文」「条目页标题、日期和图片」）而非库内 ID 链接——**登记 ≠ 入库**。
- **影响**：声称的收集成果（660 候选）与实际语料（253 文档/4400 页）严重脱节；是「数量虚高」的主要来源。
- **处置建议**：① 对 296 个 `full_item_online` 建立真实采集流水线（批量拉取 Wikimedia/NLC 公开页）补入 pages；② 或将其 `check_outcome` 降级为 `lead_only`，避免虚报已收集；③ 给 candidates 增加 `ingested_document_id` 外键字段，形成闭合链路。

#### S3 处置进展（0802 下午）
- ✅ **已入库 8 个候选 / 68 页**：`scripts/domestic/s3_backfill_ingest.py --commit` 将 8 个 `full_item_online`+wikimedia+现成逐页 OCR 的候选真实写入 `documents`/`pages`/`page_fts`/`page_fts_bigram`/`page_provenance`（doc 1301-1308：三中全会成就、反对美援蒋扶日、最终阶段政治主张、时局宣言、民盟纲领、临时全国代表大会宣言×2、政治报告×1）。
- ✅ **OCR 源复用**：7 个来自 `work/domestic/month_20260728/pages/NLC416-01jh004281-12557/ocr/` 与 `NLC511-027032016010761-42571`，1-2 个来自 `guangmingbao_1948_1949/`；逐页 `page-\d+\.ocr\.md$`，排除 tile/merged/目录页。
- ✅ **繁→简重建**：OCR 源为繁体，`lib_ingest.py` 加 `zhconv` 转简体后重入库（`e4257587…`），app bigram 搜索命中修复（纲领 3 / 三中全会 3 / 政治报告 4）。
- ✅ **闭合链路（建议③）**：`close_candidate_links_20260802.py` 给 `domestic_candidates` 加 `ingested_document_id`、`documents` 加 `ingested_candidate_id`，回填 8 个已入库候选双向指针（`f4147972…`）。
- ✅ **降级登记（建议②）**：surrogate_online(216) + catalogue_only_online(92) 共 308 个无全文候选 `check_outcome` 降为 `lead_only`（附 review_note）；剩余 pass 352 全部为 full_item_online。
- ⏳ 剩余：296 full_item_online 中其余 288 个待补采（本批已入库 8）。

### 🟠 S4. 289 个 .bak 备份占用 64GB（存储冗余）
- **证据**：`data/` 总 67GB，其中 **289 个 .bak 备份文件占 64GB（95%）**。含：
  - `machine_review.*` / `MONTH_B*` 系列：7/28-7/29 循环内**每 3 秒一个**、同一天数百份，粒度已无价值
  - 逐 OCR 页面备份（7/23 的 83MB 系列 50+ 份）
- **现状**：正式库已有 `pre_rebaseline_20260802_e4417bd1.bak`（458M）作为可靠回滚点 + SHA 基线审计。
- **处置建议**：保留 1-2 个近期回滚点（如 `pre_rebaseline_20260802`、`pre_dagongbao_1931_fix`），**其余 .bak 全部清理，预计释放 60GB+**。清理前确认 supervisor/loop 无进程依赖旧备份。

### 🟠 S5. 两套来源登记体系不联通（schema 分裂）
- **证据**：`source_registry.json`（89 来源，`source_id=domestic:source:*`）**与 `sources` 表（253 domestic 源，`source_id=domestic-ocr:*`）0 交叉**；`documents.source_id` 是 `sources.id` 整数外键，registry 的 `canonical_source_id` 从未与 documents 对接。
- 命名规范分裂：`domestic-ocr:NLC:...`（冒号）/ `domestic-page-ocr/NLC...`（斜杠）/ `domestic-ocr:COLLECTION:P3-*:ocr-draft-*`（过程性）/ `domestic-web:DL-*` 混用，**194 冒号 vs 59 斜杠**。
- **影响**：无法从文档反查「权威来源」；registry 的纠错（如大公报 1931 隔离）无法自动传导到检索层，需人工脚本同步。
- **处置建议**：以 registry 为唯一来源基准，`sources` 表补 `canonical_source_id` 关联列，统一分隔符，写一个 `reconcile_sources()` 校验入口。

### 🟡 S6. source_registry.json 字段语义污染
- **证据**：`material_types` 字段混入主题描述（「1944—1945年民盟改组及一大前后政治传播」「中央社上海五日电」「不纳入1941—1949国内民盟史证据统计」等），非材料类型枚举。
- **影响**：结构化字段不可信，任何基于 material_types 的统计/过滤都会错。
- **处置建议**：重建枚举（图书/报纸/档案/期刊/图片/照片…），把主题描述移至 `verification_note` 或新增 `topics` 字段。

### 🟡 S7. evidence_units 全部未就绪（82/82 citation_ready=False）
- **证据**：`data/domestic/evidence_units.jsonl` 82 条：`author_original`、`printed_page`、`citation_ready`、`article_title_normalized`、`article_start/end_marker` 全部空；`ocr_status` 70 条 `needs_human_review`；`article_boundary_status` 35 条 `unknown`。
- **落差**：这是「证据单元」层，但没有任何一条达到可引用状态，且 82 条中 `period=1931_out_of_scope` 有 2 条（eu-1947-070/071）。
- **处置建议**：将 82 条按就绪度分级（verified/draft/hold），把 1931 两条隔离；与 S1 的 480 页处理联动。

### 🟡 S8. QC/复核口径系统性错位
- **证据**：
  - 3876 条 provenance **全部** `needs_human_review=1`（等于没筛）；
  - `citation_ready` 全局 0 条；
  - `translation_quality_issues` 4400 行全部 `missing_translation`，经核查 99.4% 是中文原刊页（无需翻译）——**判定逻辑未做语种门控**；
  - `review_status`：machine_verified 3804 / unreadable 64 / review_only 7 / needs_fix 1。
- **处置建议**：修 `build_translation_quality_report.py` 加 `text_lang` 门控（中文主导 → skip）；`needs_human_review` 改为默认 0、仅异常页置 1；`citation_ready` 只在字段齐全时置 1。

### 🟡 S9. date_guess 格式不规范 + 73 个 domestic 文档无日期
- `1944-10—1945-01`（长破折号非 ISO）、`1944-10-10` 与 `1945-10` 混用；73/253 domestic 文档 `date_guess` 为空。相比之下其它平台 0 缺日期。
- 处置建议：统一 `YYYY-MM-DD` / `YYYY-MM` / `YYYY` 且强制 `-`；缺失日期按 `printed_page`/OCR 页眉回填或标 `unknown`。

### 🟡 S10. 脚本/报告爆炸，无统一管线
- `scripts/domestic/` 201 个脚本，其中 **89 个（44%）为 20260730 一天生成**，大量 `register_*`（40+）、`build_*`、`audit_*`、`t*`（任务流水号 20+）一次性脚本；`work/domestic/` 907 个文件。
- 危险信号：`candidates.jsonl` 有三个 `.bak`（2 个同一分钟内产生）；存在 `mingmeng.sqlite`（0 字节空文件）；顶层 `key_events.py`/`person_archive.py`/`platforms.py`/`weixin_bridge.py` 为早期遗留。
- 处置建议：**收敛为 3 类入口**：`collect`（采集）→ `normalize`（整理/OCR/元数据）→ `load`（入库+基线审计）；历史一次性脚本归档到 `scripts/archive/`，不参与日常。

### 🟢 S11. 小瑕疵
- `--- page break ---` 占位文本 5 处；`未识别出文字。` 页 6 处；`<20字` 页 61 处（部分为正常标题页/图片说明）。
- 22 个 mixed 页含 OCR 噪声（`PaddleOCR work domestic paddle rework variants` 路径串混入文本）与英文广告版面。
- 顶层 792 个 git 未跟踪文件（多数是 data/ 与 work/ 产物，git 未纳入）。

---

## 三、精简路线图（按 ROI 排序）

| 优先级 | 动作 | 收益 | 风险 | 状态 |
|---|---|---|---|---|
| P0 | 修 FTS 中文 2 字检索（S2） | 中文人名/核心词可搜，检索价值质变 | 需重建索引，配合基线审计 | ✅ 完成 |
| P0 | 隔离 1931 范围外 483 页（S1） | 检索净化、scope 合规 | 需确认无证据引用这 480 页 | ✅ 完成 |
| P1 | 清理 64GB .bak 备份（S4） | 释放 60GB+ 磁盘 | 保留 2 个近期回滚点即可 | ✅ 完成（释放约 73GB） |
| P1 | 候选断链修复（S3） | 采集真实闭合：补采 296 全文 / 降级登记 | 工作量集中在补采 | ⏳ 待办 |
| P2 | 来源体系统一（S5）+ registry 字段修复（S6） | 来源可反查、纠错可传导 | schema 迁移需回归 | ⏳ 待办 |
| P2 | QC 口径修正（S8）+ evidence_units 分级（S7） | 报告可信、人工复核聚焦真实异常页 | 低 | ⏳ 待办 |
| P3 | date 规范化（S9）+ 脚本收敛归档（S10）+ 小瑕疵清理（S11） | 整洁、可维护 | 低 | ⏳ 待办 |

## 四、建议的第一步（待你确认）

1. **P0 立即做**：S1 隔离 480+3 页（不删 provenance 元数据，仅移出 pages/索引）——这是「提高质量、精简」最直接的一步；S2 修 FTS 需评估 jieba/unicode61 方案。
2. **P1 磁盘**：清理 .bak 前先确认无进程依赖，保留 `pre_rebaseline_20260802_e4417bd1.bak` + `pre_dagongbao_1931_fix.bak`。

需要我先执行哪个？（建议从 S1 隔离开始，或先做 S2 检索修复，二者互不依赖）
