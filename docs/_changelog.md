# 变更日志

> 记录代码 + 数据结构 + 数据治理的重要变更。
> 数据库本体已脱离 git 追踪，备份在 `data/backups/`。

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
