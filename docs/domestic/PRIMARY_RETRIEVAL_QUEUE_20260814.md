# 国内九专题原件追索队列（2026-08-14）

## 定位

这份队列把 `event_coverage.json` 中九个专题的 `missing_primary` 目标，与候选记录、官方访问审计和正式库页级元数据对齐。它回答的是“下一步去哪里取得或核验原件”，不是“这些候选已经证明了事件”。

机器路由分为：

- `PUBLIC_ITEM_CANDIDATE`：公开原件/影像候选，仍需下载后核对字节、页数和 SHA256；
- `OFFICIAL_VIEWER_LOCKED`：官方查看器可达但访客锁定，必须通过有权限账户取得影像；
- `ACCESS_REQUEST_REQUIRED`：需要登录、现场或机构权限；
- `PUBLIC_SURROGATE`：公开替代本或转录，必须继续回追原件；
- `CATALOGUE_OR_FINDING_AID`：目录、说明或索引，只作定位；
- `RELATED_CONTEXT_ONLY`：与专题有关但没有命中当前开放目标的直接锚点，只作背景对读；
- `PUBLIC_NAVIGATION_LEAD` / `UNRESOLVED_LEAD`：公开导航或尚未形成稳定取得路径的线索。

## 正式库元数据叠加层

生成脚本默认以只读方式打开 `data/research_index.sqlite`，仅统计候选对应的正式文档数、页数、provenance 页数、文件哈希锚定页数和严格引用页数。它不读取正文、不写 SQLite、不下载文件，也不改变开放目标状态。

候选的 `formal_ingest_status` 有以下含义：

- `FORMAL_NOT_FOUND`：候选尚未在正式库中找到对应记录；可以继续追索或下载，但仍要走准入门禁；
- `NOT_INGESTED` / `FORMAL_METADATA_ONLY`：有候选记录但还没有正式页；
- `FORMAL_PAGES_REVIEW_ONLY`：正式库已有页，但尚未通过严格页级引用门禁；先复核 provenance，不要重复 OCR 或下载；
- `FORMAL_STRICT_PAGES_PRESENT`：已有严格引用页；先核对版本/原件关系，不能因为已有页就关闭仍开放的主证据目标；
- `NOT_CHECKED`：当前环境没有可用正式库，队列退回纯元数据路由模式。

目标项的 `formal_page_count` 和 `formal_strict_citation_page_count` 是候选路由的只读汇总。它们用于分流工作，不是“原件闭环”判定。

## 生成

```bash
python3 scripts/domestic/build_primary_retrieval_queue.py \
  --db data/research_index.sqlite \
  --output data/domestic/primary_retrieval_queue.json
```

脚本只读事件覆盖、证据链、候选元数据、访问审计和正式库结构化元数据；会按开放目标的事件/文种锚点标记 `target_match`，不读取正文，不下载文件，不写 SQLite，不自动把 `primary_evidence_status` 改为 closed。

## 当前第一优先级

1. 1947 解散专题：处理已经确认存在官方数字查看器、但访客锁定的国史馆条目；授权后建立原件 SHA、页级 provenance 和人工复核。
2. 1946 拒绝参加国民大会：把同期《光明報》页级材料与正式声明/函电/会议记录分开，优先补正式文种。
3. 1941 成立专题：继续追索《光明報》原刊、成立会议记录和版本关系，不能让1946汇编重刊单独承担成立原件。
4. 1948—1949 转型专题：把中央档案专题公开影像、会议记录、名册和完整日程逐项对齐。

## 硬门禁

- 锁定查看器不等于已取得原件；
- 目录、后期盟史网页、OCR 和转载图不自动升级为主证据；
- 任何路由都不改变 `citation_ready`、`human_verified` 或真实性等级；
- 本地低价值或重复资料不物理删除，只可排除正式层并保留追溯关系。
