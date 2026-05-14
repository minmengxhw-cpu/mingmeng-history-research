# 全量翻译运行状态

## 当前覆盖

- 页/段落片段总数：416
- 已有中文译文片段：416
- 尚待翻译片段：0

## 已完成

- 中文译文表 `translations` 已建立。
- 中文全文检索表 `translation_fts` 已建立。
- 术语表 `data/translation_glossary.csv` 已建立。
- 10 篇高价值 FRUS 文档已写入人工风格样本译文。
- 403 个其余片段已用本地离线英译中模型生成机器初稿。
- 机器初稿已按术语表和历史名词规则统一回扫。
- 未翻译队列已重建，当前为空。

## 译文状态

| 来源 | 状态 | 片段 |
|---|---|---:|
| `codex-batch-v1` | `machine-draft-review-needed` | 13 |
| `argos-en-zh-local` | `machine-draft-local-review-needed` | 403 |

## 质量说明

当前中文译文可用于全文检索、快速阅读和定位原文页码；正式引用仍应以 FRUS 原文为准。离线机器翻译已做术语统一，但人名、地名、机构名仍需要在重点文档中继续抽样校订。

## 后续校订流程

1. 先从核心文献中抽查民盟、政协、第三党、昆明暗杀、1949 年北平接触等高频主题。
2. 把发现的错误加入 `data/translation_glossary.csv` 或本地后处理规则。
3. 运行 `scripts/postedit_argos_translations.py` 回扫既有译文。
4. 对特别重要文档升级状态为 `human-reviewed`。
