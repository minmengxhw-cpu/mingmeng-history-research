# DRNH 287 文档归因报告（2026-08-02T08:53:18+00:00）

## 根因

DRNH（國史館檔案史料文物查詢系統 https://ahonline.drnh.gov.tw）是 **SPA 模式** 的档案目录查询网站，
搜索结果页与详情页都通过 JS 异步加载真实扫描件。公开 REST API 不可用（`act=Archive/*` 所有端点
返回相同搜索 SPA 首页，无扫描件直链）。

DRNH 详情页暴露但不可访问的字段：
- `span class='option online'` 含 `data-code='001000004560A001-050060-00007-001'`、
  `apply='0'`、`acckey='fcb1e3bdda699ae9af4f971fa9f0a524'`，以及
  `數位檔／線上閱覽` 文字链接
- 但**真实扫描件 URL 不在 HTML 中暴露**——需要 JS 弹 viewer，且通常需要会员登录。

这意味着：**当前 287 个 DRNH 文档的 pages.text 是「文档级标题」误当作 full-text 正文入错库**，
而非 OCR 失败或导入 pipeline bug。`local_html` / `local_txt` 都为空（从未抓取过原 HTML），
`page_provenance` 全为 0（之前就没建立元数据）——三处口径一致地印证"采集 pipeline
当时策略为：只登记搜索元数据"。

## 处置

本页 287 篇 DRNH 文档重写为**目录卡片 (catalogue card)**：

- pages.page_label：'doc-level' → 'catalogue-card'
- pages.text：title → 结构化目录卡片（含标题、档号、全宗、年代、检索词、URL、获取说明）
- page_provenance：0 → 287 条（每页 1 条，`review_status='metadata_only'`）
- needs_human_review：1 → 0（结构化目录已完成）
- citation_ready：0（保留 0，catalog card 不是 primary source，不参与学术引用）
- documents.hit_type：'a_drnh' / 'b_drnh' → 'drnh_catalogue'
- FTS（page_fts + page_fts_bigram）：同步重建
- translations (zh-CN)：同样重写

## 价值

- **保留检索价值**：287 篇档案目录依然可搜索（title、年代、关键人物）
- **避免误导**：从「full-text page」改为「catalogue card」，搜索结果与实际内容形式一致
- **未来升级通道保留**：未来若取得会员/扫码件，可重新填充 `pages.text` 转为 full-text
  并把 `hit_type='drnh_catalogue'` 改回 `drnh_scan`

## 执行

- 脚本：`scripts/domestic/finalize_drnh_catalogue_20260802.py`
- 备份：`data/research_index.sqlite.pre_drnh_catalogue_20260802.bak`
- 入库步骤：287 页改写 + 287 page_provenance + 287 translations
