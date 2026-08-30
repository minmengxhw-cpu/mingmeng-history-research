# 国内学术资料层质量审计（2026-08-30 更新）

## 结论

当前国内学术资料层可以作为“研究发现与核验队列”，还不能作为已经完成的学术引文库。索引和全文队列都是元数据级产物：本轮没有读取论文正文，没有写入正式 SQLite，也没有把本地路径或授权文件提交到 GitHub。

机器验收脚本：[`scripts/domestic/validate_academic_layer.py`](../../scripts/domestic/validate_academic_layer.py)。

## 当前规模

### 全量元数据索引

`data/domestic/academic_layer_metadata.json` 共 288 条记录：

| 质量层 | 数量 | 当前含义 |
|---|---:|---|
| S | 42 | 优先核验，通常是机构、出版社或来源链较强的记录 |
| A | 93 | 优先核验，但仍需补足正文、版本和机构证据 |
| B | 152 | 研究背景/发现线索，不自动升格为引文 |
| C | 1 | 暂不进入正式引用工作流 |

另有 15 个同规范化题名重复组、30 条重复相关记录。重复标记只是去重线索，不代表可以直接删除任一版本。

### 全文优先队列

`data/domestic/academic_fulltext_priority_queue.json` 共 23 条：

| 队列 | 数量 | 处理定位 |
|---|---:|---|
| P0 稳定全文 | 5 | 先做版本、作者/机构、出版信息、页码和来源哈希核验 |
| P1 全文候选 | 12 | 先核验入口与权限；只有扫描件才定向 OCR |
| P2 稳定背景 | 1 | 仅作背景交叉参照 |
| P3 候选背景 | 5 | 仅作发现线索，不进入引用级资料 |

其中 6 条标记为 `FULLTEXT_PDF`，17 条标记为 `FULLTEXT_HTML_CANDIDATE`。这表示可执行的来源入口状态，不表示正文已经被读取或已经通过引文复核。

S/A 优先队列共 17 条：其中 14 条机构字段可直接作为核验入口，3 条机构资格仍需补强，0 条机构字段为空。全队列另有 2 条机构字段为“待核”或其他占位值。这里的“可直接作为核验入口”只是字段完整度分类，不等同于独立证明其为 985 高校、中央研究机构或高质量期刊来源。

当前正式 SQLite 的 `domestic_academic_fulltext` 来源层已覆盖队列 16/23 条：P0 为 4/5、P1 为 12/12、P2 为 0/1、P3 为 0/5。尚未进入正式层的 7 条是：

- `GAR-639C5E94AE`：S/P0，《中国民主同盟历史文献（1941—1949）》；
- `GAR-816C31B658`：B/P2，保留为稳定背景；
- `GAR-5B6BAF5007`、`GAR-1002A409DD`、`GAR-97E96CC952`、`GAR-A96823D409`、`GAR-B9150AF5FA`：B/P3，保留为候选背景记录。

`GAR-2677452CA0`（《对抗战建国协进会成立会的回忆——为民盟史研究提供一点史料》）当前不在全文优先队列：其错误页面别名已标记为 `METADATA_OR_WRONG_PAGE` / `WRONG_PAGE_ALIAS_HOLD`，不得按 A/P1 计入正式覆盖。

### GAR-639 的同 SHA 页级 OCR 复用核验（2026-08-30）

`GAR-639C5E94AE` 虽然没有新增 `domestic_academic_fulltext` 来源行，但正式 SQLite 已存在同一来源 SHA 的 `domestic_page_ocr` 文档 `domestic-page/SRC-257bb7be70`：622/622 个 PDF 页号连续、无重复，页面正文长度统计显示 600 页达到至少 100 字符。本轮已确认这是已有页级 OCR 的可复用入口，因此**不重复导入、不重复 OCR 622 页**。

复用审计的机器验收脚本是 [`scripts/domestic/audit_academic_source_reuse.py`](../../scripts/domestic/audit_academic_source_reuse.py)，不含正文和本地路径的映射是 [`data/domestic/academic_formal_reuse_map.json`](../../data/domestic/academic_formal_reuse_map.json)。当前页级状态为：`human_verified=24`、`machine_verified=563`、`review_only=26`、`unreadable=9`；24 页 `citation_ready` 且有人工复核备注，另有 35 页仍需人工复核。严格的 `page_provenance.printed_page` 字段尚未登记（0/622），但 17 页已经在展示用 `pages.page_label` 中带有 `pdf-… / printed-…` 标签，且这 17 页均为已核验页；两种字段必须分开看。学术层页面现已从 GAR-639 队列卡片回链到这份既有页级 OCR 入口，并显式标注“不重复 OCR”。该复用只解决检索和页级定位入口，不把汇编重刊升格为 1941—1949 同期原件，也不关闭九专题的一手原件缺口。

因此，学术层的**原始正式来源行覆盖仍是 16/23**；在应进入正式全文核验的 S/A 优先队列中是 16/17，另有 1 条（GAR-639）已通过同 SHA 复用审计，统一覆盖报告给出“有效优先覆盖 17/17”。GAR-267 不属于当前队列，继续保持错误页面别名 HOLD；另外 6 条 B/P2/P3 保留为背景/发现层，不作为正式学术全文的强制缺口。两种层级不能混合后宣称“学术引文库完成”。

对 GAR-267 的本地 HTML 正式导入 dry-run 已完成：SHA 校验通过，但可见正文只有 216 字符，低于导入器的最小正文阈值，因此没有写入 SQLite，也没有 OCR；该记录继续等待完整、可复查的正文入口。其余本轮扫描到的 S/A HTML 候选均已在正式库中存在，未产生重复记录。

16 条正式层记录仍是 `review_only` 研究工作对象，不能据此宣称 16 条已经 citation-ready。覆盖审计只读取 source/document/page 的标识和数量，不读取页面正文；复用命令：

```bash
python3 scripts/domestic/audit_academic_formal_coverage.py \
  --report /tmp/domestic_academic_formal_coverage.json
```

## 价值判断与入库边界

1. `S/A` 是优先级，不是最终可信度。只有补齐作者、机构、出版物/期刊、版本、页码、来源 URL、文件 SHA 和页级 provenance 后，才可以申请 `citation_ready`。
2. 题名含“历史文献”“回忆”“史料”的出版物，可能是一手文献汇编或回忆材料，不应误标成普通学术论文；应保留 `research_type`，分别进入一手资料层或学术解释层。
3. B/C 记录不等于“没有价值”。它们可用于发现、背景和交叉检索，但不能绕过证据门禁进入正式引文。是否归档或缩减存储，需等来源绑定、去重和可重建审计完成后再决定；本轮不删除任何资料。
4. 已有可检索电子版时不重复 OCR。OCR 只针对确认没有可靠文本层的扫描页，并且必须保留原图、页码、OCR 引擎/版本、参数、输出哈希和人工复核状态。
5. 任何 `citation_ready=0`、`human_verified=0` 的记录均保持待核状态。机器脚本通过，只代表结构、字段和安全边界通过，不代表学术事实已经核实。

## 下一步执行顺序

1. 先处理 5 条 P0：GAR-639 直接复用既有 622 页 OCR，优先补 printed-page 身份和关键页复核；其余 P0 核验正文版本、作者/机构、出版物信息、页码和来源哈希；有文本层则直接抽取，不做 OCR。
2. 再处理 12 条 P1：确认公开全文或授权入口；仅对扫描件建立定向 OCR 页队列，禁止整库 OCR。
3. 对 3 条机构资格待补强记录，补充机构官网/出版物目录/期刊卷期等独立元数据；在补强前保持 `hold_metadata`。
4. 对每条拟进入正式库的资料执行页级 provenance 和引用门禁；正文未读、页码未定、来源哈希未登记的资料只保留在研究发现层。
5. 处理 15 个重复组时先建立版本关系和保留理由，不因题名相同或文件大小相同而删除。

## 验收命令

```bash
python3 scripts/domestic/validate_academic_layer.py \
  --report /tmp/domestic_academic_layer_validation.json
```

该命令只读两个版本化 JSON，输出结构化分类和错误列表，不读取正文、不 OCR、不写正式库、不删除文件。
