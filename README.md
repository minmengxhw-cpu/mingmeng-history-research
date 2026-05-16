# 民盟资料研究平台雏形

当前阶段已完成 FRUS 1941-1950 中国相关卷册的民盟资料抓取、校验、全文索引和页码引用雏形。

## 收录范围与基本原则

本平台只收录 **国外一手原始档案** 的原文与中译，包括：

- **FRUS**（美国对外关系文件集，已上线）
- **Wilson Center 数字档案库**（进行中）
- **CIA FOIA 电子阅览室**（规划中）
- **Hoover Institution 胡佛档案**（规划中）
- **NARA 美国国家档案馆**（规划中）
- **HathiTrust / Internet Archive** 公开学术资源（规划中）

**不收录**：民盟官网、维基百科、政协官网、各级民盟省市委员会网站、新闻报道、研究论文等任何 **二手资料**。

平台内部用于辅助档案翻译的人物姓名标准化档案、术语表、AI 协作说明等工作文档以 `_前缀` 命名（如 `docs/_民盟人物档案_内部研究参考.md`、`docs/_AI协作说明.md`），属于研究编排工具，不构成资料库收录内容。

## 前台展示边界

本平台前台展示遵循民盟史的学术分期与中性表述原则：

- 人物 profile 重点展示学术身份、专业贡献与建国初期职务，不展开 1949 年之后的具体经历
- 关键事件聚焦于 1941-1949 民盟建立、政协斡旋、内战受难、新政协等学术意义清晰的节点
- 阶段标签采用中性、学术化的表述
- 涉及历史敏感性的内容仅作为内部档案翻译的背景参考，不进入对外页面

## 已有数据

- `data/frus_meng/frus_meng_report.md`: FRUS 抓取汇总。
- `data/frus_meng/frus_meng_validation.md`: FRUS 命中校验报告。
- `data/frus_meng/frus_meng_direct_hits.csv`: 直接组织命中。
- `data/frus_meng/frus_meng_person_candidates.csv`: 人物候选命中。
- `data/frus_meng/documents/`: 命中文档的本地 HTML/TXT 快照。
- `data/research_index.sqlite`: 正式研究索引库，支持全文搜索和页码/文档级引用。

## 常用命令

启动本地网页阅读器：

```bash
python3 app.py
```

打开：

```text
http://127.0.0.1:8765
```

文档筛选：

```text
http://127.0.0.1:8765/docs?grade=核心文献
http://127.0.0.1:8765/docs?grade=相关文献
http://127.0.0.1:8765/docs?grade=人物关联
http://127.0.0.1:8765/docs?grade=背景材料
```

重新抓取 FRUS 民盟材料：

```bash
python3 scripts/crawl_frus_meng.py
```

校验 FRUS 命中：

```bash
python3 scripts/validate_frus_meng.py
```

重建研究索引：

```bash
python3 scripts/build_research_index.py
```

全文搜索并返回引用：

```bash
python3 scripts/search_corpus.py 'Kunming assassinations' --limit 5
python3 scripts/search_corpus.py '"Federation of Chinese Democratic Parties"' --limit 5
```

加入一个双语样本翻译并验证中英文并排搜索：

```bash
python3 scripts/add_translation_sample.py
python3 scripts/search_bilingual.py '昆明暗杀' --limit 5
python3 scripts/search_bilingual.py 'Democratic League' --limit 5
```

写入 10 篇 FRUS 批量翻译样本：

```bash
python3 scripts/add_frus_translation_batch.py
```

批量样本说明见 `docs/frus_translation_batch_review.md`，术语表见 `data/translation_glossary.csv`。

继续翻译所有尚未翻译的片段：

```bash
python3 scripts/translate_missing_pages.py
```

也可以先小批量测试：

```bash
python3 scripts/translate_missing_pages.py --limit 5
```

如果在线 API 额度不可用，可以用本地离线模型生成机器初稿：

```bash
.venv/bin/python scripts/translate_missing_pages_argos.py
.venv/bin/python scripts/postedit_argos_translations.py
```

当前 FRUS 416 个页/段落片段已全部有中文译文，其中 403 个为本地机器初稿，13 个为早期批量样本译文。

生成译文质量检查报告：

```bash
python3 scripts/build_translation_quality_report.py
```

输出：

- `data/translation_quality_issues.csv`
- `docs/translation_quality_report.md`

网页入口：

```text
http://127.0.0.1:8765/quality
```

质量检查页可以按严重度和问题类型筛选，并进入单段校订页。校订页保存后会更新中文译文和中文全文检索索引。

研究工作台入口：

```text
http://127.0.0.1:8765/tasks
http://127.0.0.1:8765/people
http://127.0.0.1:8765/topics
http://127.0.0.1:8765/places
http://127.0.0.1:8765/places/南京?grade=core
http://127.0.0.1:8765/organizations
http://127.0.0.1:8765/organizations/中国民主同盟?grade=core
http://127.0.0.1:8765/events
http://127.0.0.1:8765/focus
http://127.0.0.1:8765/dashboard
http://127.0.0.1:8765/cite/128
```

- `tasks`: 将质量提示合并为校订任务队列，按核心文献、严重度、人物和专题线索排序。
- `people`: 人物索引，当前包括罗隆基、张澜、梁漱溟、沈钧儒、黄炎培、章伯钧、史良、张君劢、张东荪、周恩来等。
- `topics`: 核心专题，包括昆明暗杀、1946 年政协、马歇尔调处、第三方面、1949 年北平接触。
- `places`: 地点索引，按南京、昆明、北平、重庆、上海等地点聚合事件线索。
- `organizations`: 机构索引，按中国民主同盟、国民党、中国共产党、美国国务院、美国驻华使馆等机构聚合事件线索。
- `events`: 事件线索，把人物和专题命中的资料压缩成按年份组织的事件节点，并保留摘录卡片、并排阅读、校订和 FRUS 来源入口。
- `focus`: 首页“今日继续研究”清单，可编辑首页入口和高价值事件范围，配置保存于 `data/home_focus.json`。
- `dashboard`: 研究进度仪表盘，汇总文档、译文、事件、质量提示和最近导出。
- `cite/<page_id>`: 生成短引文、参考文献、原文、中文译文、FRUS 来源和页码的摘录卡片。
- `review/<page_id>`: 单段校订页，支持保存校订、下一条校订、保存并进入下一条。

生成事件线索：

```bash
python3 scripts/build_event_timeline.py
```

常用事件页：

```text
http://127.0.0.1:8765/events?person=lo-lung-chi
http://127.0.0.1:8765/events?person=lo-lung-chi&tag=民盟
http://127.0.0.1:8765/events?person=lo-lung-chi&place=南京
http://127.0.0.1:8765/events?person=lo-lung-chi&org=中国民主同盟
http://127.0.0.1:8765/events?topic=kunming-assassinations
http://127.0.0.1:8765/events/cards?person=lo-lung-chi
http://127.0.0.1:8765/events/cards?topic=kunming-assassinations
```

导出专题或人物研究笔记：

```bash
python3 scripts/export_research_notes.py --topic kunming-assassinations
python3 scripts/export_research_notes.py --person lo-lung-chi
```

输出位于 `exports/`，内容按年份分组，包含原文摘录、中文译文、FRUS 链接和片段编号。

导出事件研究卡片：

```bash
python3 scripts/export_event_cards.py --person lo-lung-chi
python3 scripts/export_event_cards.py --topic kunming-assassinations
python3 scripts/export_event_cards.py --place 南京
python3 scripts/export_event_cards.py --organization 中国民主同盟
python3 scripts/export_event_cards.py --person lo-lung-chi --split-by-tag
python3 scripts/export_event_cards.py --person lo-lung-chi --split-by-place --split-by-organization
python3 scripts/build_export_index.py
```

输出位于 `exports/`，内容按年份分组，包含地点、机构、短引文、参考文献、原文摘录、中文译文和本库引用入口。`--split-by-tag` 会按“民盟、政协、马歇尔调处”等标签拆成多份文件；`--split-by-place` 和 `--split-by-organization` 会按地点或机构拆分。
`build_export_index.py` 会生成 `exports/event_cards_index.md` 作为导出目录。

生成待翻译队列：

```bash
python3 scripts/build_translation_queue.py
```

输出：

- `data/translation_queue.csv`
- `data/translation_queue.jsonl`
- `docs/translation_queue_report.md`

按批次导出待翻译材料。每个批次同时生成 CSV 和 JSONL；CSV 适合人工或外部工具翻译后回填 `zh_translation` 列，JSONL 适合程序化翻译：

```bash
python3 scripts/export_translation_batches.py --grade 核心文献 --max-chars 50000 --out-dir data/translation_batches_core
python3 scripts/export_translation_batches.py --max-chars 50000 --out-dir data/translation_batches_all
```

输出：

- `data/translation_batches_core/translation_batches_report.md`
- `data/translation_batches_all/translation_batches_report.md`

把已经完成的批次翻译导回资料库：

```bash
python3 scripts/import_translations_csv.py data/translation_batches_core/batch_001.csv
```

导入时会保留英文原文，并把中文译文写入 `translations` 与中文检索索引。

导入 PDF。如果 PDF 自带文本，会先抽文本；如果是扫描图像，会用本地 OCR：

```bash
python3 scripts/ingest_pdf_ocr.py path/to/file.pdf --title '资料标题' --source-id source-key
```

## 当前校验结果

- 扫描 FRUS 文档：14,109 篇。
- 命中总数：299。
- 高置信：271。
- 中置信：2。
- 人物候选：26。
- 正式索引：299 篇文档，416 个页/段落片段，其中 117 个带官方页码锚点。

## 引用规则

- 有 FRUS 官方页码锚点时，搜索结果返回 `p. N` 和 `https://history.state.gov/...#pg_N`。
- 没有页码锚点时，搜索结果返回 `doc-level`，先引用到 FRUS 文档 URL。
- PDF 入库后按 PDF 页码返回 `p. N`。
- 中文翻译单独存放，不覆盖原文；翻译结果带状态，例如 `sample-review-needed`、`machine-draft`、`human-reviewed`。
