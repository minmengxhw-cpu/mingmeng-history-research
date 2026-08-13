# 变更日志

> 记录代码 + 数据结构 + 数据治理的重要变更。
> 数据库本体已脱离 git 追踪，备份在 `data/backups/`。

## 2026-08-14

### DRNH 访客预览与正式引用门禁分离

- DRNH 阅读页现在明确显示“国史馆官方访客预览”和“目录卡片（非正文）”，不再把带重复水印、锁定提示的本地影像称为“原档释读”或“无水印原图”。
- DRNH 的 `/cite/<page_id>` 与国内史料共用严格页级门禁；目录卡片和访客预览不能生成正式引文，只有未来具备 `human_verified`、`citation_ready` 和复核说明的页才可进入引用卡片。
- 新增 DRNH 阅读页和引用门禁回归测试；保持国史馆访客影像只用于档号、页数、页面结构和研究导航确认。
- 同步正式库 manifest：数据库 SHA256 为 `81bfca9f871647044d90b4e3a8fab55f8afe1c6864e12d833c1e306cf996c120`，严格人工可引用页为 129，国内专题事件行数为 528。

### 1949 新政协首批档案影像页级收口

- 新增 `scripts/domestic/apply_saac_visual_review_20260814.py`，以数据库 SHA、来源图片 SHA、页级 provenance 和独立复核决定为门禁；默认干运行，正式写入必须提供不可覆盖的新备份路径。
- 完成 5 个中央档案专题公开扫描影像页的视觉核验并写入正式库：代表名单题名页、民盟代表名单页、民盟代表签名册页、第一届全体会议日程题名页、每日议程页；严格人工可引用页由 124 增至 129。
- 5 页已挂接 `domestic-1949-new-pcc` 事件索引与四层证据链，专题链由 29/18 个页级/严格条目更新为 34/23 个；完整筹备会记录、代表发言和会议档案仍保留为开放目标。
- 原始图片未修改；数据库写入前备份为 `/private/tmp/research_index.sqlite.before_saac_1949_pcc_visual_review_20260814.sqlite`，SQLite integrity 和外键检查均通过。

### 国内专题：拆分导航就绪与一手证据闭环

- `data/domestic/event_coverage.json` 为九个专题补充 `primary_evidence_status`、可读标签和逐专题 `primary_evidence_gap`。
- `scripts/domestic/build_domestic_parity_matrix_20260813.py` 将原先宽泛的 `research_ready` 拆成 `navigation_ready` 与严格的一手闭环统计；当前九个专题为导航就绪、但一手证据部分闭环。
- `/domestic/events`、`/research` 和专题详情页同时显示对位状态、一手证据状态及下一步原件缺口。
- 新增真实数据库回归测试，防止有导航页、严格页或学术元数据时自动宣称关键一手原件已闭环。

### 国内专题：开放主证据目标收口看板

- 新增 `/research/gaps`，从 `topic_evidence_chain.json` 的 `missing_primary` 逐项生成九个专题的原件追索清单。
- 每个开放目标显示研究问题、为什么重要、下一步动作、候选记录和专题详情入口；页面只读元数据，不读取正文，也不把候选或汇编自动升级为原件。
- 证据链校验器现在要求每个开放目标同时具备 `target`、`why_it_matters` 和 `next_action`，避免出现只有口号、没有执行路径的缺口记录。

### 国内专题：加入四层证据链

- 新增 `data/domestic/topic_evidence_chain.json`，为九个专题登记主证据、同期交叉、负向核查和待补原件。
- `/research/<event_id>` 展示证据链条目，并可从已核页级条目回到 `/doc/<doc_key>?page_id=...`；缺口条目保留调档目标和下一步，不伪装为已取得原件。
- 证据链只消费正式库页级元数据和既有复核决定，不读取正文，不改变 `page_provenance` 的引用门禁。
- 新增 `scripts/domestic/validate_topic_evidence_chain.py`；parity 矩阵和完成监控现在会检查证据链是否断链、页号是否漂移以及严格条目是否仍满足正式引用门禁。
- `/research` 专题索引增加证据链页级条目和待补原件目标摘要；当前验收基线为 9/9 链、34 个页级条目、23 个严格条目、9 个开放目标。
- 国内正式引用卡不再套用境外 FRUS 书目模板；现在显示来源版本、PDF/物理/印刷页、页级 URL、文件 SHA256 和人工复核说明，未通过门禁的国内页仍只提供不可直接引用的检索阅读。

### 国内外统一研究入口：搜索结果补充页级证据状态

- `/search` 的国内命中现在显示 `国内史料` 标签，并从 `page_provenance` 补充“正式可引用”“机器可阅”“原件已锚定·待复核”或“证据待补”。
- 国内状态只读 `page_provenance` 的门禁字段，不读取或修改正文，不会把机器 OCR、源文件存在或候选 accepted 自动升级为正式引用。
- 新增真实数据库回归测试 `test_unified_search_labels_domestic_evidence`；完整测试为 `32 passed`。
- 统一平台长期路线记录于 `docs/PLATFORM_UNIFIED_RESEARCH_PLAN_20260814.md`。

## 2026-05-20

### 数据治理：DRNH 平台 1941 时间硬切

- 删除 81 篇 DRNH 文档（1933-1940 + 无日期 + `0000`）及其 pages / translations / classifications / drnh_images / FTS 索引。
- 原因：研究主线为 1941-1950 中国大陆境外一手档案，早期川局军政电报与民盟相关度低。
- 备份：`data/backups/research_index_pre_drnh_purge_20260520_152323.sqlite` + `drnh_pre1941_purge_*.tsv` + `*_sql.sql`（含 url/doc_key 可重抓）。
- 二次恢复：从备份恢复 4 篇与民盟创盟人物强相关的 1935/1937 档案（沈钧儒七君子案、罗隆基入川相关），保留原 id 699/700/701/777，附带原已写好的 200-250 字人工释读。

### 数据治理：DB 脱离 git 追踪

- `git rm --cached data/research_index.sqlite`（commit `2272a74`）。
- `.gitignore` 排除：`data/research_index.sqlite` + `-journal/-wal/-shm` + `data/backups/`。
- 本地文件保留，未来 DB 变更不再产生 git blob，避免每次 push 68MB+ 二进制。
- 2026-05-21 已用 `git filter-repo` 清理历史 blob，并强推远端；仓库历史不再保留 `data/research_index.sqlite`。

### 六源体系正式定型

| 平台 | 文档数 | 状态 |
|---|---|---|
| FRUS | 299 | ✅ |
| DRNH（台北档案史料） | 287 | ✅（1941 边界 + 4 件人物特例） |
| CIA | 102 | ✅ |
| HathiTrust | 54 | ✅ |
| Wilson Center | 24 | 🟡 Cloudflare 拦截待破 |
| Hoover Institution | 2 | 🚫 命中过少，已否决 |
| **合计** | **768 篇** | 1059 段 / 99% 复核 |

### 首页 UI 修复（commits `92d8a55` → `2b35930`）

- 顶部 LOGO 副标 + 页脚数据来源补齐六源（之前停留在 FRUS/Wilson/CIA 三源时代）。
- FRUS 卡片"人工复核覆盖率"从 65% 修正为 100%：`platforms_panel_html()` 中 `frus_pages/frus_zh/frus_human` 改用 JOIN documents 限定 `source_platform='frus'`，避免被 DRNH 自动转写译文稀释。
- 平台卡片按真实文档数降序展示（已上线优先）。
- 恢复 hero 顶部 eyebrow（"1941 — 1950 · 中国大陆境外一手档案"）和平台卡片上方的 section-head 章节标题"档案研究平台"。

### Notion + Google Drive 集成原型入仓（commit `04e537f`）

- `notion-drive-worker/` 29 文件 / 4762 行入仓，作为后续档案影像 → Notion 单条目同步的原型。

### DRNH 原图解析现状盘点

- 共 287 篇 DRNH 文档，**已下载原图 + 已写人工释读** 5 篇：id 648（1946 张澜呈国民政府）+ id 699/700/701/777（1935-1937 沈钧儒/罗隆基相关）。
- 待处理 282 篇均无图，其中 1946 年 149 篇为下一步重点（政协 + 内战爆发 + 民盟对美舆论战）。
- 下载管线尚未脚本化：之前 5 件为人工通过浏览器开发者工具反推 `object_code` + `page_codes` 下载，需逆向 DRNH `ahonline.drnh.gov.tw` 影像接口后才能批量化。
