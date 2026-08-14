# 变更日志

> 记录代码 + 数据结构 + 数据治理的重要变更。
> 数据库本体已脱离 git 追踪，备份在 `data/backups/`。

## 2026-08-14

### 1949 新政协与 1947 解散专题：回接已核验页级材料

- 将已完成人工视觉复核、但尚未完整回接研究链的 1949 年中央档案公开扫描 12 页（代表名单、签名册、北上邀请电报、筹备会概要、主席团名单、会议日程）和 1947 年同期报刊 6 页纳入 `topic_evidence_chain.json`；这些页只开放页身份、页序、来源哈希和受限复核范围。
- 证据链由 100/89 条增至 118/107 条；1949 专题现在有 17 个中央档案公开扫描页级锚点，1947 专题新增 6 个同期报刊交叉页；不把机器 OCR、姓名识别、手写签名或报刊报道升级为事件定义原件。
- 8 条此前未回接的 1949 页级导航关联写入正式事件索引；4 条同批关联原本已存在，数据库总量由 559/545 增至 567/553，写入前 SHA256 为 `214fb3785bffb2430585e590acd49aaa73258d286634d8ab2d478bd9ae19fa36`，写入后为 `f8f47a750007bf0739e885425f1a63206fbe1844444d7d0a8b2a4980bb700e84`。
- 写入前备份为 `/private/tmp/mingmeng_research_index_20260814_followup_event_links_1438.bak`；正文、OCR、图片和 PDF 均未修改或删除，9 个专题证据链、研究包和公开边界继续保留原有门禁。

### 1948 三中全会/五一口号：七页官方公开扫描影像接入证据链

- 对中央档案公开扫描影像中的正式页 `20665`—`20671` 完成本地视觉复核，写入页级来源文件、SHA256、页面 URL、物理页和受限复核范围；批次为 `work/domestic/saac_1948_mayday_review_20260814/`。
- 7 页从 `review_only` 保守升级为 `human_verified` / `citation_ready` 的页级身份门禁，严格人工可引用页由 189 增至 196；不保存正文，不把 OCR 当作正式转录，不宣称取得档案全宗原件或完整会议档案。
- 7 页回接 `domestic-1948-third-plenum-may-day` 专题事件索引和 `topic_evidence_chain.json`；证据链由 93/82 条增至 100/89 条，专题事件索引由 552/538 增至 559/545，写入幂等复跑为 0 条重复新增。
- 数据库写入前备份分别为 `/private/tmp/mingmeng_research_index_20260814_saac_1948_mayday.bak` 和 `/private/tmp/mingmeng_research_index_20260814_saac_1948_links.bak`；写入后 SHA256 为 `214fb3785bffb2430585e590acd49aaa73258d286634d8ab2d478bd9ae19fa36`。正文、OCR、图片和 PDF 均未修改或删除，SQLite、外键、FTS、manifest、证据链、研究包、专题 parity 和问题基准均通过。

### 1947 同期报刊六页视觉复核与导航摘要治理

- 对《大剛報》1947-11-04、1947-11-06及《观察》第三卷第十一期共 6 页做本地高分辨率页图复核；正式 provenance 现在同时绑定原始 PDF、PDF 页码、页图 SHA256、OCR 派生文件和复核范围。
- 批次为 `work/domestic/nlc_1947_visual_review_20260814/`，通过 `scripts/domestic/apply_nlc_1947_visual_review_20260814.py` dry-run 后写入；正文、OCR 文本和原始资产未修改，严格人工可引用页由 183 增至 189。
- 写入前数据库 SHA256 为 `d309ce966121bdce6341171c1a467b6caac4946de3c836c8ebb32d9f3905b997`，写入后为 `331dc2e7f02e29959200abcbcae3ccf0b6061e87faf6eb673ad9a3cbfa1d1b37`；备份为 `/private/tmp/mingmeng_research_index_20260814_nlc_1947_visual.bak`。
- 6 个页级导航入口已纳入 `data/domestic/citation_event_links.json`；它们只用于同期报刊/公共评论导航，不替代 1947 年政府公文、民盟公告或内部会议文件。
- 修复旧事件索引的正文泄漏：`scripts/domestic/repair_event_navigation_summaries_20260814.py` 将 552 条国内导航摘要统一为正文-free，保留所有事件行、页 ID、人物和标签，删除行数为 0。清理前 SHA256 为 `331dc2e7f02e29959200abcbcae3ccf0b6061e87faf6eb673ad9a3cbfa1d1b37`，清理后为 `52550c3e10c9061eea1f8ac5cde53ad95b42e66e383e9d1489d7850d39564127`；备份为 `/private/tmp/mingmeng_research_index_20260814_event_summary.bak`。
- 当前 manifest 已同步：来源文件 639 个、682,380,426 bytes；完整性、外键、FTS 和来源哈希均通过。

### 1949 新政协：追加四页页级视觉复核

- 对北上邀请电报、筹备会概要、代表名单连续页和主席团名单各一页做本地图像视觉复核，严格人工可引用页由 179 增至 183。
- 批次为 `work/domestic/saac_1949_pcc_followup_20260814/BATCH_NEXT.json`；只写页级身份、来源 SHA256、页序和复核范围，不保存正文或 OCR 文本。
- 写入前数据库 SHA256 为 `93c3cce2e2d119d981d99ad2fd158b34c2c8313a9020bd87c4dc62ae26038edc`，写入后为 `dae8eb8a6afa2da8753e6506532669f1ac0aaa02e12938b17b5866285c6605a2`；备份为 `/private/tmp/mingmeng_research_index_20260814_saac_followup_next.bak`。
- 这四页只增强 1949 专题的页级导航和有限事实核对，不替代完整新政协会议档案、民盟代表发言或完整代表名册。
- 四页随后回接 `domestic-1949-new-pcc` 专题事件索引，新增 4 条导航关联；写入前 SHA256 为 `dae8eb8a6afa2da8753e6506532669f1ac0aaa02e12938b17b5866285c6605a2`，写入后为 `d309ce966121bdce6341171c1a467b6caac4946de3c836c8ebb32d9f3905b997`，备份为 `/private/tmp/mingmeng_research_index_20260814_saac_followup_next_links.bak`。

### 固化国内学术对读元数据快照

- 新增 `data/domestic/academic_topic_crosswalk.json`，保存九个国内专题的 159 条学术匹配计数、质量层级和不含正文的记录标识。
- parity 矩阵默认读取该版本化快照，不再依赖 `work/` 下的临时 crosswalk；换电脑或只从 GitHub 恢复代码时，国内外研究导航不会错误退化为“无学术匹配”。
- 快照不包含学术正文、OCR、绝对路径或本地私有文件清单；完整 staging 数据和全文继续留在本地数据盘，学术层仍不能替代国内一手页级证据。

### 1949 新政协：追加 8 页视觉复核并更新正式库 manifest

- 对正式库中 1949 年国家档案局公开扫描的 8 页做本地图像视觉复核：代表名单连续页 4 页、代表签名册 2 页、第一届全体会议日程连续页 2 页。
- 复核批次为 `work/domestic/saac_1949_pcc_followup_20260814/`；批次只保存页级身份、来源 SHA256、页序和复核说明，不保存正文或 OCR 文本。
- 通过 `scripts/domestic/apply_saac_visual_review_20260814.py` 的 dry-run 后正式写入，严格人工可引用页由 171 增至 179；数据库新 SHA256 为 `93c3cce2e2d119d981d99ad2fd158b34c2c8313a9020bd87c4dc62ae26038edc`。
- 备份为 `/private/tmp/mingmeng_research_index_20260814_saac_followup.bak`；原始图片未覆盖或删除，SQLite integrity、外键、FTS、来源文件哈希、专题链、研究包和 36 个问题基准均重新通过。
- 这 8 页只增强 1949 专题的页级导航和有限事实核对，不关闭“完整新政协会议档案、民盟代表发言和完整会议记录”这一主证据缺口。

### 国内外统一研究平台：固化项目执行路线

- 新增 `docs/PROJECT_EXECUTION_ROADMAP_20260814.md`，明确国内外统一研究路径、九个 P0 原件目标、学术解释层、OCR 分流、角色边界和机器可验收完成条件。
- 主计划的权威口径更新为：导航 9/9、一手证据闭环 0/9、严格人工可引用页 179；旧的 `work/` 报告不得覆盖正式库和当前生成的 parity matrix。

### 国内原件追索队列：接入正式库只读元数据叠加层

- `scripts/domestic/build_primary_retrieval_queue.py` 可只读查询正式库中的候选文档数、页数、provenance、文件哈希锚定页和严格引用页；不读取正文、不写 SQLite、不下载文件。
- 队列新增 `FORMAL_NOT_FOUND`、`FORMAL_PAGES_REVIEW_ONLY`、`FORMAL_STRICT_PAGES_PRESENT` 等状态，并在开放目标层汇总已有正式页，明确提示“先复核”或“不要重复 OCR/下载”。
- 该叠加层只用于工作分流，不改变 `primary_evidence_status`、`citation_ready`、`human_verified` 或真实性等级；已有严格页也不能自动关闭仍开放的原件目标。
- 访问权限阻塞优先级高于已有页：`AUTHORIZED_VIEWER_REQUIRED` / `ACCESS_REQUEST_REQUIRED` 仍要求取得原件，已有同期报刊或汇编只能标为交叉材料，不能覆盖授权追索动作。
- 新增回归测试覆盖：正式库已有页时仍保持主证据缺口开放，且队列明确保持 metadata-only 和 `formal_db_written=false`。
- `/research/gaps` 现在显示每条候选的正式页/严格引用页状态；该内部收口看板加入公开模式隐藏路径，避免把授权追索和私有候选暴露给公开访问者。

### 公开专题研究入口：统一页级授权边界

- `/research`、专题详情、`/research/packets` 和 `packet.json` 现在与国内资料库共用同一个公开文档谓词；共享专题事件索引、四层证据链和研究问题矩阵不会绕过 `rights_status=public` 与 L0--L3 门禁。
- 公开研究包仍只导出题目、页级身份、来源哈希、复核范围和回链；未授权国内页不会进入证据链、矩阵页级链接或专题事件样本，正文、OCR、译文和逐字引文继续不导出。
- 内部模式的数据口径不变：93 个证据链页、548 个国内专题事件页；公开模式验收口径为 5 个明确授权的证据链页、9 个专题事件页，未授权页不渲染。
- 新增公开专题页与公开研究包边界回归测试；真实 HTTP 验收覆盖 `/research`、专题详情、`/research/packets` 和 `packet.json`，均返回 200。

### 国内资料准入与 OCR 分流

- 新增 `data/domestic/source_admission_policy.json` 和 `scripts/domestic/build_source_admission_queue.py`，把电子文本跳过 OCR、已有页链不重复导入、OCR 草稿定向复核、页数异常先对账、索引仅作导航等规则机器化。
- 分流只读取元数据覆盖清单，输出本地工作单；不读取正文、不写正式 SQLite、不删除文件、不自动改变 `citation_ready` 或真实性等级。
- 国内质量页新增分流策略区块；详细口径见 `docs/domestic/SOURCE_ADMISSION_AND_OCR_DISPOSITION_20260814.md`。

### 九专题原件追索队列

- 新增 `data/domestic/primary_retrieval_queue.json` 和 `scripts/domestic/build_primary_retrieval_queue.py`，把 9 个 `missing_primary` 目标与公开原件候选、需机构权限、官方查看器锁定、目录线索和背景材料分层连接。
- 路由按目标锚点做 `target_match`；相关材料不会因为属于同一专题就被误报为直接原件路径。已审计的官方锁定条目强制保留在 1947 解散专题路由中。
- 研究缺口看板显示“原件路由”和对应取得动作；队列保持 `body_read=false`、不下载、不写正式库、不自动关闭一手缺口。

### 公开模式国内资料边界

- `/domestic`、`/domestic/library`、统一搜索、文档列表、来源页、年表和事件线索在公开模式下只显示同时满足 `rights_status=public` 和 L0–L3 的国内文档；统计数字、核心精选和页数均使用同一公开文档谓词。
- 国内质量、调档、学术和 staging 路由加入公开模式隐藏边界；正式库已有 OCR 或 provenance 不再被误当成公开授权。
- 新增 `tests/test_public_domestic_boundary.py`，覆盖公开 SQL、私有核心文档不渲染和内部路由隐藏。

### 国内证据缺口看板：优先呈现可行动线索

- 缺口看板候选排序改为“访问审计状态 → 档案/原刊/正式文件 → 核心相关性 → 真实性等级 → 审核状态”，让已确认存在官方查看器、但仍受访客权限限制的原件线索优先出现。
- 兼容正式库候选表中没有独立 `evidence_type` 字段的历史记录，改以 `document_type` 的保守关键词分级；不改变候选状态、证据链、正文、OCR 或数据库内容。

### 国内专题收口：精选 11 页高价值材料回接证据链

- 从 95 个已人工核验但尚未回接专题链的候选页中，只精选 11 页：1945 年大会前国民大会立场前史 4 页（1501—1504）、1946 年民盟发言人/代表政协发言 5 页（1512—1516）和 1947 年组织受压与公共活动转移 2 页（1583—1584）。
- 11 页均已有真实 PDF、来源 SHA256、精确页 URL 和 `human_verified`/`citation_ready` provenance；全部进入“同期交叉”层，不升级为成立原件、政协完整会议档案、正式拒参声明或政府解散公文。
- 国内证据链由 82 个页级条目、71 个严格条目增至 93 个页级条目、82 个严格条目；9 个专题仍为 `navigation_ready=9`、`research_ready=0`，9 个事件定义原件缺口继续保留。
- 研究问题矩阵同步增加这些页级入口，研究包、证据链校验和 parity 基准均已重跑通过；正式 SQLite、原始 PDF、OCR 和 `work/` 临时材料未修改或删除。

### 精选页回接专题事件索引

- 将上述精选页中的 10 页新增为专题事件索引导航行（1945 年 4 页、1946 年 5 页、1947 年 1 页；另 1 页此前已存在），使证据链与专题检索入口一致；不改变正文、来源 provenance 或严格引用门禁。
- 正式库仅新增 10 条可回滚的专题关联：`research_events=2465`、`domestic_research_event_rows=548`、`domestic_research_event_pages=534`；数据库 SHA256 为 `9aaada2c3f193dc0b0102032c6c483181441aacbd82c89b45e77bc330e321cd2`。
- 写入前备份为 `/private/tmp/research_index.sqlite.before-topic-page-links-20260814.sqlite`；完整性、外键、manifest、专题 parity 和 36 个研究问题基准均通过；原始 PDF、OCR、图片、正文和 `work/` 临时材料未修改或删除。

### 1947 年国史馆 P0 原件访问审计

- 通过本机 Chrome 只读打开国史馆条目 `002-020400-00012-067`，确认官方目录标注“数位档／线上阅览”，并成功进入 2 页数字影像查看器。
- 当前仍为访客会话，影像带锁定提示且“下载影像”控件不可用；因此只登记为 `official_viewer_locked`，不计算本地文件 SHA、不写入正文、不升级 `citation_ready`。
- 新增 `docs/domestic/DRNH_1947_ACCESS_AUDIT_20260814.md`，明确目录卡、官方查看器和本地文件三种状态，以及用户完成授权后所需的原件闭环门禁。
- 新增 `scripts/domestic/validate_primary_evidence_access_audit.py` 及回归测试；它检查候选是否存在于正式库和专题覆盖表，并强制 `official_viewer_locked` 不得拥有本地原件、下载完成或 `citation_ready` 状态。

### 国内外统一研究体验：新增研究问题—证据矩阵

- 新增 `data/domestic/topic_research_matrix.json`：九个国内专题、36 个子问题，逐题登记页级证据入口、证据范围、边界、开放缺口和下一步动作。
- `/research/<event_id>` 和元数据-only 研究包现在都展示矩阵；研究者可以从子问题直接回到 `/cite/<page_id>`，按页级人工复核范围决定是否引用。
- 矩阵不复制正文/OCR/译文/逐字引文，不改变四层证据链或 `primary_evidence_status`；当前仍是 9 个专题导航可用、9 个专题一手证据部分闭环。
- 新增完整性回归：36 个子问题、96 个页级引用均必须能回到现有证据链和正式数据库页号；研究包校验器增加矩阵正文导出门禁。
- 新增 `data/domestic/topic_foreign_crosswalk.json`：36 个子问题逐项声明境外关系类型、可用入口、机器命中范围和对读边界；“暂无同命题境外专题”也作为显式状态展示，避免把境外背景或关键词命中误报为双边互证。
- 专题详情页和研究包新增“国内—境外子问题对读”区块，国内页级证据与境外专题入口分层展示，研究包增加境外对读正文导出门禁。

### 国内专题：回接已核验的 1941 与 1945 页级证据

- 将已通过人工引用门禁、但此前只停留在文档层的 6 页正式回接到专题研究链：1941 成立宣言连续页 1474—1475、早期政治主张页 1476—1477，以及 1945 一大政治报告末页 1444、宣言末页 1446。
- 1941 专题研究包由 2 条页级记录增至 6 条，严格门禁页由 1 条增至 5 条；1945 专题研究包由 34 条增至 36 条，严格门禁页保持 36 条，补足政治报告/宣言的首尾页级范围。
- 新增 9 条专题导航关联，数据库结构、文档和页面数量不变；SQLite 写入前备份为 `/private/tmp/research_index.sqlite.before-topic-links-20260814.sqlite`，新数据库 SHA256 和事件计数已同步 manifest。
- 仍不把汇编重刊当作独立原件，不复制正文/OCR/逐字引文；1941 成立原件、1945 大会完整档案和版本关系继续保持开放缺口。

### 国内平台：首个专题研究包和页级研究工作流

- 新增 `scripts/domestic/research_packet.py` 与 `scripts/domestic/validate_research_packet.py`，把研究问题、国内/境外对读、四层证据链、页级 provenance、学术解释候选和开放原件目标编排为元数据-only 研究包。
- `/research/<event_id>/packet` 提供可读研究包，`/research/<event_id>/packet.json` 提供可复核 JSON 下载；专题索引和专题详情均可进入研究包。
- 1945 年民盟第一次全国代表大会首个样板验收：34 条页级证据链记录全部解析，34 条严格页级记录通过门禁；每条都带原文页/引用门禁回链、来源 SHA256 和复核范围。当前 staging 数据盘可提供 6 条学术解释候选，未挂载 staging 时按 README 的外部路径配置恢复。
- 研究包显式保证不导出正文、OCR、译文或逐字引文；新增回归测试验证 `body_text_included=false` 等边界，避免“研究包”被误解为正文复制或自动引文。
- 国内来源地图标题补充“国内研究平台”和“国内史料层”识别，修正过时测试口径；完整专题 HTTP 回归为 37 passed。

### 国内同期报刊：1946《光明報》新八号、新十一号页级收口

- 完成《光明報》新八號第 1 页及新十一號第 1、3 页本地 PDF 视觉核验，确认期号、日期、PDF/物理页、版面和标题锚点。
- 将正式库页 `16367`、`16634`、`16636` 绑定到真实 PDF 的精确页级 URL，并开放 `periodical_issue_identity_editorial_title` 受限引用范围；不开放未经逐字校勘的 OCR 正文。
- 三页加入 1946 年拒参专题的同期交叉链和研究入口；专题的正式拒参声明/函电/会议档案缺口仍保持开放。
- 新增 `scripts/domestic/apply_guangmingbao_1946_issue8_11_visual_review_20260814.py`，默认 dry-run，正式写入要求新的不可覆盖备份；原始 PDF、OCR、图片和正文均未修改。
- 1947 年第 2974 号公报完成逐页负向视觉核查并登记在专题链；负向核查不等于证明目标公文不存在。

### 国内同期报刊：1946《光明報》首版页级范围修正

- 将正式库页 `16351` 的引用范围标签细化为“刊名、期号、出版日、PDF 页码、版面及社论题名”，页面不再套用目录页的提示语。
- 保留《光明報》1946 年新七號作为 1946 年拒参专题的同期交叉页级入口；不把社论题名升级为民盟正式拒参声明，不输出未经逐字校勘的 OCR 正文。
- 新增 `scripts/domestic/patch_guangmingbao_1946_issue7_scope_20260814.py`，只改 provenance 标签，正式写入前要求数据库 SHA 和不可覆盖备份；正文、OCR、PDF、页数和事件关联均未修改。
- 数据库写入前备份为 `/private/tmp/research_index.sqlite.before_guangmingbao_1946_issue7_scope_20260814.sqlite`；manifest 已同步新的数据库 SHA。

### 国内平台：36 个真实研究问题基准

- 新增 `scripts/domestic/build_research_question_benchmark_20260814.py`，按九个国内专题各 4 个问题，检查正式库检索、专题证据链、严格引用门禁和开放主证据状态。
- 基准只输出元数据、页号样本和计数，不复制页面正文；36/36 问题进入国内检索与专题链，16/36 查询直接带出严格可引用页，九个专题仍明确为 `primary_evidence_status=partial`。
- 新增回归测试，防止“检索路径可用”被误报为“一手证据闭环”；详细口径写入 `docs/PLATFORM_UNIFIED_RESEARCH_PLAN_20260814.md`。

### 1945《民主同盟文獻》纲领与大会宣言页级边界核验

- 对《民主同盟文獻》（民盟总部编印，1946）PDF 第 48—72 页和第 73—78 页完成本地影像页序与边界核验：前一组为《中国民主同盟纲领》，后一组为《中国民主同盟临时全国代表大会宣言》；篇名页、标注日期、连续页序和收束页均已核对，真实 PDF SHA256 已登记。
- 将正式库页 `20149`—`20179` 从 OCR-only 导航记录绑定到真实 PDF 页级 provenance，开放严格引用门禁；引用范围限于官方汇编版本、篇名、标注日期、PDF 页码和页界，不等同于独立 1945 大会原件、底本关系或未经校勘的 OCR 正文。
- 1945 专题证据链增加 31 个官方汇编页级交叉条目，形成“1983公开扫描大会文件 + 1946官方汇编纲领/宣言”的双版本入口；完整大会档案、独立原件和版本关系仍保留为开放主证据缺口。
- 引用卡的汇编年份改为按页级 `evidence_role` 动态显示，避免 1945 汇编页沿用 1944 标签；新增可复现批次构建脚本 `scripts/domestic/build_minmeng_wenxian_1945_batch_20260814.py`。正文、OCR 文件和原始 PDF 均未修改。
- 数据库写入前备份为 `/private/tmp/research_index.sqlite.before_minmeng_1945_program_review_20260814.sqlite`；manifest 已同步新的数据库 SHA、来源文件去重统计和严格引用页数。

### 1944《民主同盟文獻》官方汇编页级边界核验

- 对《民主同盟文獻》（民盟总部编印，1946）PDF 第 22—25 页完成本地影像核验；四页连续显示《对抗战最后阶段的政治主张》，页眉日期为 1944-10-10，真实 PDF 为 176 页，SHA256 已登记。
- 将正式库页 `20141`—`20144` 从 OCR-only 导航记录绑定到真实 PDF 页级 provenance，开放严格引用门禁，但证据角色明确为“官方汇编中的 1944 文本”，不等同于 1944 改组会议原件或独立同期底本。
- 引用卡仅开放题名、日期、页码、版本和来源哈希；机器识别文本只作定位，不输出为未经逐字校勘的正文引文。新增 `scripts/domestic/apply_minmeng_wenxian_1944_platform_review_20260814.py`，正文、OCR 和 PDF 均不修改。
- 1944 专题证据链增加 4 个汇编页级交叉条目；改组会议记录、改名决定、同期独立原刊和版本关系仍保留为开放主证据缺口。
- 复核后修正 4 页的非正文标签：视觉核验的是页身份和页界，不是 OCR 全文准确度，因此 `ocr_status` 保持 `real_page_ocr`；新增 `scripts/domestic/correct_minmeng_1944_platform_metadata_20260814.py`，仅修改该标签并重新生成 manifest，正文、哈希、引用门禁和原始 PDF 不变。

### 1944《民憲》同期目录页绑定真实 PDF provenance

- 对《民憲》第一卷第一期、第六期、第九期的目录页（正式库页 `20286`、`20288`、`20290`）完成本地 PDF 第 2 页视觉核验，并将页级 provenance 从 OCR 派生 Markdown 切换到对应整期 PDF，登记 PDF 页码、物理页、文件大小和 SHA256。
- 三页只开放“刊名、卷期、出版日、目录页身份”范围内的正式引用；明确标为 1944 年同期政论刊物交叉材料，不宣称是改组会议记录、改名决定、正式政治报告或已核验的文章正文。
- 1944 专题证据链由 1 个待复核目录入口更新为 3 个严格可引用目录页；1944 事件索引不重复插入，改为沿用既有页级导航关联。严格人工可引用页由 129 增至 132。
- 新增 `scripts/domestic/apply_minxian_1944_contents_review_20260814.py`，默认 dry-run，正式写入要求数据库 SHA 和三份 PDF SHA 匹配，并要求新的不可覆盖备份路径；正文、OCR 文件和原始 PDF 均未修改。
- 数据库写入前备份为 `/private/tmp/research_index.sqlite.before_minxian_1944_contents_20260814.sqlite`；manifest 已同步新的数据库 SHA、来源文件去重统计和严格引用页数。

### 国内文档入口与境外模板边界修正

- 国内文档总页不再沿用 FRUS 的“学术引用”书目模板，改为“国内史料入口（页级引用）”；文献级入口明确提示正式引用必须回到具体页级卡片。
- 国内文档每个页面现在显示“正式可引用”“原件已锚定 · 待复核”或“不可直接引用”，与统一搜索、专题页和 `/cite/<page_id>` 的门禁口径一致。
- 增加国内文档入口回归测试；本轮本机页面冒烟验证覆盖国内文档页、1944 专题页、页级引用卡和境外文档路由。
- 对本批三张目录页增加“范围受限”引用输出：引用卡保留 PDF/页码/SHA/人工复核说明，机器识别文本仅作定位，不再进入可复制的“原文摘录”，避免把未逐字校勘的 OCR 当作文章正文引文。

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
- 研究平台：新增九专题研究包批量验收、统一研究包索引和“证据链页/专题事件回接页/候选回接页”分层统计；研究问题基准新增专题严格页路由指标，避免把关键词未命中误报为没有严格证据。
- 研究平台：专题详情页和可读研究包新增专题事件索引页区，直接展示页级 provenance、严格门禁和原文/引用回链；索引层不读取或导出正文。
