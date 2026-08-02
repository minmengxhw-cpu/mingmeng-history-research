# MiniMax 下一阶段总任务书：国内资料库、三线验收与 GitHub 审核

版本：2026-08-02  
执行者：MiniMax  
协调者：用户 / Codex  
执行方式：用户手动触发；本任务书本身不触发模型、不自动运行。

## 一、总目标

把当前民盟历史文献研究项目从“模型产物、候选目录、正式库和网页入口分散”推进为一套可审计的国内资料工作流：

1. 统一正式数据库、网页和报告的事实基线。
2. 完成首页国内资料入口，使其与境外平台入口一致。
3. 验收 DeepSeek、MiniMax、Grok 的既有产物，但不把机器结果直接升级为引用级证据。
4. 生成三条后续模型线的隔离输出和 manifest。
5. 将代码和审核材料安全推送到 GitHub 审核分支，不覆盖既有远端历史。

最终交付必须能回答四个问题：

- 当前真正已收录的国内资料有多少？
- 哪些只是候选、OCR 或 staging 线索？
- 三个模型各自完成了什么、哪些还不能采信？
- GitHub 上审核的代码和报告是否能在不依赖本地数据库的情况下复核？

## 二、执行边界与安全门

### 绝对禁止

- 不删除本地任何文件、数据库、备份、缓存、日志或模型产物。
- 不执行 `git reset --hard`、`git checkout --`、递归删除或覆盖远端历史。
- 不使用 `git add -A`。
- 不把 SQLite、扫描原件、OCR 中间目录、API key、运行日志或未审核研究草稿推送 GitHub。
- 不向正式 `data/research_index.sqlite` 写入任何模型结果。
- 不设置 `citation_ready=true`、`human_verified=true`，不把 OCR 草稿提取为正式 claims。
- 不把搜索结果、候选登记、目录页、现代回顾当作 contemporaneous primary source。

### 可以执行

- 只读检查正式 SQLite、staging SQLite、报告、脚本和网页输出。
- 在隔离目录生成 manifest、审计报告、QC ledger、dry-run 文件和测试输出。
- 修改首页、国内资料库路由、测试、快照和审核文档。
- 使用明确路径逐项暂存代码和审核材料。
- 推送新的 GitHub 审核分支；如需创建 PR，使用 draft PR，不合并。

## 三、当前事实基线（执行前重新验证）

执行前不要直接相信旧报告，先运行只读检查并把结果写入本轮 manifest。

当前已观察到的基线：

- 正式库：`data/research_index.sqlite`
- 预期当前 SHA：`bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e`
- `PRAGMA integrity_check`：应为 `ok`
- documents：1386
- pages：6157
- translations：1070
- page_provenance：4786
- 国内 documents：525
- 国内 pages：5087
- domestic_candidates：689
- 当前候选状态：`pass=279`、`lead_only=381`、`check_outcome IS NULL=29`
- `ingested_document_id IS NOT NULL=279`
- `citation_ready=1`：4353；正式库没有 `human_verified` 列
- `translation_quality_issues=111`，当前类型为 `incomplete_ocr`

若实测数字或 SHA 不同，以实测为准，并将差异写入 `BASELINE_DRIFT_REPORT.md`；禁止静默覆盖旧报告。

## 四、执行阶段

### P0：正式库和报告基线统一

输入：

- `data/research_index.sqlite`
- `work/domestic/PROJECT_STATE_FINAL_20260802.md`
- `work/domestic/PROJECT_FINAL_AUDIT_20260802.json`
- `work/domestic/PROJECT_POST_0802_SUMMARY.md`
- `work/domestic/CITATION_GRADE_20260802.md`
- `work/domestic/CORPUS_ADVERSARIAL_REVIEW_20260802.md`

动作：

1. 运行 `PRAGMA integrity_check`。
2. 生成表规模、source_platform、候选状态、provenance 状态和翻译状态统计。
3. 计算正式库 SHA-256。
4. 对比旧报告，列出 SHA、候选数量、QC 行数和 citation 状态漂移。
5. 生成 `work/model_runs/minimax_next_stage_20260802/P0_BASELINE_MANIFEST.json`。
6. 生成 `P0_BASELINE_DRIFT_REPORT.md`。

验收：

- 所有后续报告只引用本轮 manifest。
- 旧报告不删除，只标记 stale 或 superseded。
- 未写正式 SQLite。

### P1：国内资料库网页入口

目标：主页入口进入“已收国内资料”列表，候选目录仍单独存在。

应完成：

1. 首页国内卡片链接到 `/domestic/library`。
2. 新增 `/domestic/library`，仅展示 `documents.source_platform='domestic'` 的正式收录文档。
3. 页面显示文档数、页面数、来源数和当前筛选结果。
4. 支持按题名、档号或来源筛选。
5. 国内候选目录 `/domestic` 增加返回已收资料库的入口。
6. 导航增加“已收国内资料”。
7. 保留 OCR、候选、staging 和人工复核边界说明。

验收：

- `/`、`/domestic/library`、`/domestic` 返回 HTTP 200。
- 页面无 traceback 或 Internal Server Error。
- `/domestic/library` 不显示 `lead_only` 候选作为正式文档。
- 数据库缺失时页面可明确提示或测试 skip，不伪造数字。

### P2：DeepSeek 既有产物验收与后续 QC 线

既有输入：

- `scripts/translate/`
- `scripts/build/summarize_*_for_paper.py`
- `data/newspapersg/zh_translations.csv`
- `data/domestic/zh_translation_revisions_frus_core.csv`
- `data/domestic/zh_translation_revisions_hathitrust_mix.csv`
- `data/research_index.sqlite` 中 translator/status 字段

动作：

1. 确认 DeepSeek 模型、translator、status 和批次边界。
2. 抽取至少 20 条跨 Newspapersg、FRUS、HathiTrust 的样本。
3. 检查人名、机构、日期、否定词、术语、OCR 残缺和历史重构。
4. 生成 `DEEPSEEK_QC_LEDGER.jsonl`、`DEEPSEEK_QC_SUMMARY.md`、`RECONSTRUCTION_HOLD.jsonl`。

验收：

- 每一条建议都能回链原文页或原文窗口。
- 破损 OCR 重构单独进入 HOLD。
- 不修改正式数据库。
- 不把机器 QC 变成人工复核结论。

### P3：Grok 来源与 provenance 线

既有输入：

- `work/domestic/grok_next_stage_20260730/`
- `work/domestic/grok_month_20260729/`
- `work/domestic/minimax_official_research_20260730/06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.md`
- `work/domestic/CHEER_NEXT_ACTIONS.md`

动作：

1. 优先处理 1941—1943、1948—1949 硬缺口。
2. 复核 lead-only 与 concrete 的边界。
3. 对每个真实可取得来源记录 URL、机构、日期、访问状态、MIME、大小、SHA、页数和页链。
4. 现代官方回顾、目录、搜索结果、原件正文分开分类。
5. 生成 `GROK_SOURCE_MAP.csv`、`GROK_HARD_GAPS_REPORT.md`、`GROK_DOWNLOAD_MANIFEST.jsonl`。

验收：

- 没有本地字节和 SHA 的对象不得标记 `downloaded_verified=true`。
- 无法访问、登录限制、版权限制和 404 全部进入 HOLD。
- 不修改候选状态和正式数据库。

### P4：MiniMax P5/T69 证据工程线

既有输入：

- `work/model_audit_20260802/MINIMAX_MANUAL_TASK.md`
- `work/domestic/MINIMAX_V2_PHASE5_SPEC_20260801.md`
- `work/domestic/minimax_autonomous_research_20260730/T68_COMPREHENSIVE_FINAL_REPORT_20260801.md`
- `work/domestic/minimax_domestic_evidence_v2_month_20260729/08_sqlite_dryrun/`
- `work/domestic/minimax_official_research_20260730/06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.md`

动作：

1. 建立 1941—1943 和 1948—1949 hard-gap pool。
2. 保持 `SSID-13679264#p0001/#p0002` 两条 isolated hold 隔离。
3. 复核 T68 关系台账中的 `HOLD_UNSUPPORTED`。
4. 生成 SQLite dry-run manifest 和 rollback 说明。
5. 生成 `MINIMAX_P5_T69_SUMMARY.md`。

验收：

- 不执行正式 apply。
- 不使用 `CODEX_APPLY_TOKEN`。
- 不生成 `citation_ready`、`human_verified` 或正式 claims。
- 所有数量由本轮 manifest 重新计算。

### P5：统一验收和 GitHub 审核

动作：

1. 运行 `PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile app.py tests/*.py`。
2. 运行受控本地测试：`PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m pytest -q`。
3. 目标为全部测试通过；当前基线包含新增国内资料库 smoke，目标至少 `13 passed`。
4. 运行 `git diff --check`。
5. 只暂存以下明确文件：
   - `app.py` 中国内资料库入口、首页卡片、导航和路由相关 hunks
   - `tests/test_smoke.py`
   - `tests/test_snapshot.py`
   - `tests/snapshots/`
   - `work/model_audit_20260802/`
   - T1 CI 配置和依赖文件（如本轮尚未提交）
6. 明确排除数据库、备份、扫描、OCR、日志、临时目录和未审核报告。
7. 创建新提交，例如：`feat(domestic): add collected domestic library entry`。
8. 推送到 `agent/model-audit-review-20260802` 或新的 review 分支，不覆盖现有远端历史。

验收：

- GitHub 分支指针与本地提交一致。
- 提交文件清单可逐项解释。
- 混合工作树中的其他改动仍保留在本地，不被暂存或删除。
- 不自动合并 PR。

## 五、最终交付目录

建议所有 MiniMax 本轮输出集中于：

`work/model_runs/minimax_next_stage_20260802/`

至少包含：

- `P0_BASELINE_MANIFEST.json`
- `P0_BASELINE_DRIFT_REPORT.md`
- `DEEPSEEK_QC_LEDGER.jsonl`
- `DEEPSEEK_QC_SUMMARY.md`
- `RECONSTRUCTION_HOLD.jsonl`
- `GROK_SOURCE_MAP.csv`
- `GROK_HARD_GAPS_REPORT.md`
- `GROK_DOWNLOAD_MANIFEST.jsonl`
- `MINIMAX_HARD_GAP_POOL.jsonl`
- `MINIMAX_ISOLATED_HOLD_DECISION.json`
- `MINIMAX_RELATION_LEDGER.jsonl`
- `MINIMAX_SQLITE_DRYRUN_MANIFEST.json`
- `MINIMAX_P5_T69_SUMMARY.md`
- `FINAL_ACCEPTANCE.md`

## 六、最终报告必须明确写出

- 哪些数据来自正式 SQLite，哪些来自 staging，哪些只是模型产物。
- 当前正式库 SHA 和旧报告 SHA 的差异。
- 已收文档、候选线索、lead-only、HOLD、citation-ready 的独立数量。
- 三个模型各自的 PASS、CONDITIONAL_PASS、HOLD 和 NOT_COMPLETE 项。
- 测试结果和 GitHub 提交哈希。
- 未完成事项、人工决策点和下一次可手动触发的任务。

本任务完成的定义不是“生成了很多文件”，而是：事实基线一致、网页入口可用、模型产物可追溯、正式库未被越权写入、GitHub 审核内容可复查。
