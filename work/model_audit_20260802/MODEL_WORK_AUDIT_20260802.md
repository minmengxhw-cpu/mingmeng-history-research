# DeepSeek / MiniMax / Grok 工作验收与 GitHub 审核基线

审计日期：2026-08-02
审计对象：当前工作树、已提交历史、正式 SQLite、`work/domestic/` 模型任务产物、模型调用脚本与可追溯翻译字段。
审计原则：模型产物可以作为机器辅助结果，但不能仅凭模型报告、任务完成标记或候选登记表，升级为正式证据、`human_verified` 或可直接引用的一手材料。

## 1. 总结结论

| 模型线 | 当前结论 | 可以认可的范围 | 不能认可的范围 |
|---|---|---|---|
| DeepSeek / v4-flash | `CONDITIONAL_PASS` | 已落库且有 translator/status 标记的翻译批次；翻译脚本、术语表和 QC 流程 | 把机器译文当人工定稿；从破损 OCR 重构出的内容当逐字翻译；未经逐条复核的事实摘要 |
| MiniMax | `CONDITIONAL_PASS / PROGRAM_NOT_COMPLETE` | P0-P5 控制面、dry-run、HOLD 台账、OCR/关系候选和接力包 | T68 目标完成、正式库 apply、`citation_ready`、`human_verified`，以及把 25 个 dossier 当完整证据包 |
| Grok | `CONDITIONAL_PASS_WITH_GAPS` | 重分类、来源发现、候选队列、页面链和 handoff 资料 | 把 lead-only 记录当已取得原件；把“完成波次”当作完整公开原件交付；未经本地字节与 SHA 的下载声明 |

本次没有触发 DeepSeek、MiniMax 或 Grok。本文只验收仓库现有结果，并准备下一轮供用户手动触发的任务书。

## 2. 当前正式库事实基线

以下数字来自 2026-08-02 对 `data/research_index.sqlite` 的只读检查，而不是沿用旧报告：

- SHA-256：`bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e`
- `PRAGMA integrity_check`：`ok`
- `documents=1386`，`pages=6157`，`translations=1070`，`page_provenance=4786`
- `domestic_candidates=689`：`pass=279`、`lead_only=381`、`check_outcome IS NULL=29`
- `domestic_candidates.ingested_document_id IS NOT NULL=279`
- `documents.source_platform`：`domestic=525`、`drnh=287`、`frus=299`、`cia=102`、`newspapersg=93`、`hathitrust=54`、`wilson=24`、`hoover=2`
- `page_provenance`：`citation_ready=1` 共 4353；`citation_ready=0` 共 433；没有 `human_verified` 字段，不能把报告里的 `human_verified=0` 当作当前正式库列值
- 当前 `translation_quality_issues=111`，类型为 `incomplete_ocr`；历史报告中“4400 行 / 0 行”的结论已过期

### 必须阻断发布的基线失配

1. `work/domestic/PROJECT_STATE_FINAL_20260802.md` 和 `PROJECT_FINAL_AUDIT_20260802.json` 仍引用 `e4417bd1…` / `4837dbd6…`，与当前正式库 `bdebdbb0…` 不一致。
2. 历史报告中的 `A 层 660/29` 与当前数据库 `pass=279、lead_only=381、NULL=29` 不一致；候选登记与真实入库必须分开报告。
3. 旧报告中的 `translation_quality_issues=4400` 已不能作为当前 QC 结论；当前表是 111 条 `incomplete_ocr`。
4. 仓库有 728 个未跟踪路径和 3 个已修改路径。数据库、扫描文件、OCR 中间物、备份和运行日志不属于本次 GitHub 审核包。

在重新生成正式库 manifest、同步所有 `EXPECTED_FORMAL_SHA`、复跑查询验收前，正式库不能被称为“冻结发布基线”。

## 3. DeepSeek 产物验收

### 可追溯证据

- 入口脚本：`scripts/translate/translate_newspapersg_deepseek.py`、`retranslate_with_deepseek.py`、`translate_wilson_qc.py`、`translate_cia_meng.py`、`translate_domestic_english_pages.py` 等。
- v4-flash 精读/抽取脚本：`scripts/build/summarize_cia_for_paper.py`、`summarize_wilson_for_paper.py`、`summarize_hathitrust_for_paper.py`、`summarize_drnh_for_paper.py`、`refine_cia_translations_llm.py`。
- 当前数据库中有 `translator='deepseek-v4-flash-newspapersg'` 的 87 行，以及 `translator='deepseek-chat-2026-05-15'` 的 68 行；另有 6 行旧 glossary-index 结果复用了 NewspaperSG 的状态名。数据库实际不是“所有 93 行均有同一 translator 值”。
- NewspaperSG 的 93 行状态为 `machine-reviewed-newspapersg-deepseek-2026-06-02`，但译者字段和状态字段存在历史批次混用，不能替代逐页质量验收。

### 通过项

- API 入口、模型名、术语表和输出状态在脚本中可追溯。
- 译文保留原文 URL、标题、日期和 translator/status 字段，具备重新抽样的入口。
- 机器产物没有被本审计自动升级为人工核验或正式证据。

### 保留项 / 风险项

- 多条 NewspaperSG 译者注明确写有“根据标题、上下文或历史常识重构”，这类内容应标为机器重构或待人工复核，不能作为逐字翻译。
- `cloud-model-revision-v1` 的 39 行只说明云模型修订，不足以证明由 DeepSeek 完成；模型归属应保持未知，不要反推。
- `summarize_*` 输出属于研究辅助摘要，不是页面级引文。摘要必须能回链到原文页、原始 URL 和 OCR 质量窗口。

### DeepSeek 验收结论

`CONDITIONAL_PASS`：可以继续承担翻译、术语一致性和机器 QC；所有事实性改写、破损 OCR 重构和摘要结论继续保持人工复核门，不得直接写入正式证据层。

## 4. MiniMax 产物验收

### 可追溯证据

- 主任务：`work/domestic/minimax_domestic_evidence_v2_month_20260729/`、`work/domestic/minimax_autonomous_research_20260730/`、`work/domestic/minimax_official_research_20260730/`。
- 关键验收：`MINIMAX_V2_PHASE5_SPEC_20260801.md`、`T68_COMPREHENSIVE_FINAL_REPORT_20260801.md`、`PRE_CODEX_AUDIT_BLOCKERS_20260802.md`。
- 当前控制面 `STATE.json` 显示 MiniMax 为 `READY_NEXT_CYCLE`，最近完成任务为 T68；545 个物理 OCR 页、25 个 dossier、447 条关系，`citation_ready_created=0`、`human_verified_created=0`。

### 通过项

- P5 的 hard-gap、isolated-hold、apply dry-run 和 rollback 入口具备明确文件边界。
- 任务报告诚实记录了本地 wall、API 429、关系 HOLD 和目标未达，不应把中间指标包装成完整研究证据。
- 现有任务设计保留了“不能写正式库、不能设 citation_ready/human_verified”的安全门。

### 未通过 / 待处理

- T68 报告明示程序级硬指标未达标，25 个 dossier 不是完整证据包；OCR 页规模相对长期目标仍明显不足。
- P4 formal apply 仍是锁定状态。没有独立授权、基线 manifest 和回滚演练，不得 apply。
- OFFICIAL_RESEARCH 的 5 个 blocker 仍是 documented gaps；“likely pass”不是最终验收。
- MiniMax 产物与当前正式库 SHA 不一致，不能据此证明未发生库外部变化，也不能替代当前库重新验收。

### MiniMax 验收结论

`CONDITIONAL_PASS / PROGRAM_NOT_COMPLETE`：可以继续做证据候选、OCR 队列、关系台账和 dry-run；不得直接进入正式库，下一轮必须先解决基线失配和 hard gaps。

## 5. Grok 产物验收

### 可追溯证据

- 主任务：`work/domestic/grok_next_stage_20260730/`、`work/domestic/grok_month_20260729/`、`work/domestic/grok_parallel_20260729/`。
- 当前控制面记录 Gate 0 重分类、上海波次、非上海 gap wave、页面链和 handoff 均完成或带缺口完成。
- `FINAL_REPORT.md` 明确写有 `COMPLETE_WITH_GAPS`、lead-only 不计配额、未改正式 SQLite、未声明 `citation_ready/human_verified`。

### 通过项

- 来源发现、重分类、页面链、缺口与 handoff 的产物分层清晰。
- 结果中区分 concrete 与 lead-only，并对 1942–1943 原件缺口保持 HOLD，符合证据纪律。
- Grok 线没有以模型文字代替本地原件 SHA；当前状态适合继续做来源侦察和 provenance 收口。

### 未通过 / 待处理

- `COMPLETE_WITH_GAPS` 不是完整交付：当前控制面仍有大量 lead-only（primary 2600、scholarly 3016），fulltext gap 仍在。
- 早期 provenance closeout 的 182 → 49 mapped / 133 hold / 0 downloads 不能与后续 gap wave 的统计直接相加；必须按批次、输入快照和 manifest 分开复算。
- 任何“已下载”结论都必须同时提供本地路径、magic/MIME、文件大小、SHA-256、页数和对应 source row。

### Grok 验收结论

`CONDITIONAL_PASS_WITH_GAPS`：可以继续做公开来源发现、硬缺口检索和 provenance mapping；不可将候选或搜索结果直接视为已取得史料。

## 6. 共同审计结论

- 模型工作大多停留在“候选、机器文本、摘要、OCR、关系台账、handoff”层；真正的引用级证据仍需要原件、页码、来源和人工复核闭环。
- 当前最大技术风险不是模型调用失败，而是“历史报告与当前正式库不一致”以及“候选 accepted/pass 与真实入库不一致”。
- 本次 GitHub 审核只上传本审计文件、三条手动任务书和已验证的 T1 测试基线；不上传 SQLite、原始扫描、OCR 中间目录、备份、日志、API 密钥或未审核研究草稿。
- 后续模型任务必须默认只写隔离输出目录；只有人工审查、manifest 校验、`PRAGMA integrity_check`、回滚演练和独立放行全部通过后，才允许讨论正式库 apply。

## 8. 本地回归验证

- `PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m py_compile tests/*.py`：通过。
- 受控本地 HTTP 服务下 `PYTHONPYCACHEPREFIX=/tmp/codex_pycache python3 -m pytest -q`：`12 passed`。
- 4 份 HTML 快照已按当前正式库重新生成；快照更新只涉及 `tests/snapshots/`，没有修改 SQLite 或研究原件。

## 7. 审核后推荐顺序

1. 先由人工确认当前正式库 `bdebdbb0…` 是否是新基线，并重新生成数据库 manifest。
2. DeepSeek 做翻译/QC 小样本复核，优先处理“重构”与人名、日期、否定词风险。
3. Grok 做 hard-gap 原件检索与下载 provenance，严格输出 HOLD/可验证来源。
4. MiniMax 在隔离目录推进 P5/T69 hard gaps 和关系台账，不 apply。
5. 由人工对三线输出做交叉验收，再决定是否进入下一次正式库变更窗口。
