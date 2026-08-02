# 手动任务线 A：DeepSeek v4-flash 翻译与 QC

## 目标

对已有机器译文做“原文对照式”质量复核，找出人名、机构名、日期、否定词、语气、OCR 误读和未经标记的重构；输出可逐条复核的差异清单，不做证据等级判断。

## 输入

- `data/newspapersg/zh_translations.csv`
- `data/domestic/zh_translation_revisions_frus_core.csv`
- `data/domestic/zh_translation_revisions_hathitrust_mix.csv`
- `data/research_index.sqlite` 中与 DeepSeek translator/status 对应的行，只读读取
- `config/glossary.json` 或仓库现行术语表

## 输出

写入隔离目录，例如 `work/model_runs/deepseek_v4flash_qc_YYYYMMDD/`：

1. `QC_LEDGER.jsonl`：每条包含 page_id/doc_key、原文窗口、现译文、建议译文、问题类型、严重度、依据和是否需要人工复核。
2. `SUMMARY.md`：样本数、问题数、按错误类型统计、无法判断项。
3. `RECONSTRUCTION_HOLD.jsonl`：凡原文 OCR 不足以支持逐字翻译的条目单列 HOLD。

## 强制边界

- 不写 `data/research_index.sqlite`，不改 `translations`，不改 `page_provenance`。
- 不设置 `citation_ready`、`human_verified`、`accepted`。
- 不把历史知识补写成原文内容；不能确认就写 HOLD。
- 每个建议必须保留原文定位；没有原文窗口的建议无效。
- 明确区分 `translation_error`、`ocr_uncertainty`、`historical_inference` 和 `style_preference`。

## 人工验收门

- 至少 20 条跨 Newspapersg、FRUS、HathiTrust 的混合样本。
- 100% 检查人名、日期、机构名、否定词和“据标题/常识重构”标记。
- 任一条无法回链原文或页码，整条保持 HOLD。
- 只提交 ledger 和报告，不提交数据库写入。
