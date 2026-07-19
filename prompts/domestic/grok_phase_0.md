# Grok 阶段 0：国内史料工程基线

你是本项目的工程负责人。工作目录是当前项目根目录，目标是为“国内一手史料库”建立可验证的工程基础。

## 必读

1. `AGENTS.md`
2. `README.md`
3. `docs/PRD_国内一手史料库.md`
4. `docs/国内史料_Grok_Minimax协作执行计划.md`
5. `docs/_collection-standards.md`
6. `platforms.py`
7. `app.py` 中数据库连接、来源页、检索和引用卡片相关代码

## 任务

1. 审查现有 SQLite schema、`sources`、`documents`、`pages`、`document_classifications`、`research_events` 的兼容性。
2. 审查现有 `source_platform` 设计是否足以承载国内来源；只提交设计报告，不要立即改核心表。
3. 审查 `data/first_person_acquisition.csv`、`data/external_acquisition_queue.csv` 和相关脚本，指出哪些可以复用。
4. 审查 PRD 中的数据字段，提出最小迁移方案。
5. 编写或补充国内候选记录 JSON Schema 校验器，但只能写入 `scripts/domestic/` 和 `work/domestic/grok/`。
6. 运行只读测试和 schema 校验样例。

## 严格边界

- 不修改 `app.py`、`platforms.py`、SQLite、扫描件、压缩包。
- 不提交 Git，不推送远端。
- 不猜测档号、页码、日期、来源和权利状态。
- 发现不确定性时写入报告，不绕过约束。

## 交付

写入：

- `work/domestic/grok/phase_0_engineering_report.md`
- `work/domestic/grok/phase_0_schema_risks.json`
- 必要时 `scripts/domestic/validate_candidates.py`

报告必须包含：现状、兼容性风险、推荐迁移步骤、可复用脚本、测试命令、未决问题。
