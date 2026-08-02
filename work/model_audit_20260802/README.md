# 2026-08-02 模型审核包

本目录是供 GitHub 审核和后续人工手动触发模型的最小材料包。

- `MODEL_WORK_AUDIT_20260802.md`：DeepSeek、MiniMax、Grok 现有产物验收和当前正式库事实基线。
- `DEEPSEEK_V4FLASH_MANUAL_TASK.md`：翻译与 QC 线。
- `GROK_MANUAL_TASK.md`：公开来源、硬缺口和 provenance 线。
- `MINIMAX_MANUAL_TASK.md`：P5/T69 证据工程和 dry-run 线。

三条任务线均要求隔离输出、保留 HOLD、禁止直接写正式 SQLite，且本轮不会自动触发任何模型。
