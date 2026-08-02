# 手动任务线 B：Grok 公开来源与 provenance 收口

## 目标

围绕国内民盟史 B 层硬缺口和当前 lead-only 队列，寻找可公开验证的一手来源或官方目录，建立可复核的来源链；搜索结果、现代回顾和目录导航必须与 contemporaneous primary source 分开。

## 优先对象

- 1941–1943 早期活动缺口
- 1948–1949 三中全会、新政协、共同纲领相关缺口
- 1947-10-27、1947-11-04、1947-11-06 等已有任务书标出的硬缺口
- `domestic_candidates` 中 `lead_only` 且有公开来源线索的记录

## 输入

- `work/domestic/grok_next_stage_20260730/`
- `work/domestic/minimax_official_research_20260730/06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.md`
- `work/domestic/CHEER_NEXT_ACTIONS.md`
- `work/domestic/grok_month_20260729/`

## 输出

写入隔离目录，例如 `work/model_runs/grok_provenance_YYYYMMDD/`：

1. `SOURCE_MAP.csv`：candidate_id、题名、事件日期、机构、原始 URL、页面 URL、来源类型、access 状态、MIME、文件大小、SHA-256、页数、对应页链、判断依据。
2. `HARD_GAPS_REPORT.md`：每个缺口的已证实来源、HOLD 原因、下一步人工动作。
3. `DOWNLOAD_MANIFEST.jsonl`：只有本地确实存在的文件才可写 `downloaded_verified=true`。

## 强制边界

- 搜索结果不等于已取得原件；目录页不等于正文。
- 现代官方回顾只能标为 `official_retrospective`，不能标为 contemporaneous primary。
- 没有本地字节、magic/MIME、大小和 SHA-256 时不得写“已下载”。
- 不写正式 SQLite，不改变候选的 `check_outcome`，不设置 `citation_ready` 或 `human_verified`。
- 访问受限、页面失效、登录要求和版权限制全部进入 HOLD，不猜 URL、不伪造页码。

## 人工验收门

- 随机抽查 10 条 SOURCE_MAP，逐条打开 URL 并核对本地文件 SHA。
- 统计 concrete、lead-only、HOLD，不能把三者相加成“已完成”。
- 每条硬缺口至少给出一个可复核的下一步，不得只输出搜索摘要。
