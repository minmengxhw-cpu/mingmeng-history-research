# 全量翻译运行状态

> 截至 2026-05-26

## 当前覆盖

- 档案源数：**6**（FRUS / CIA / Wilson / Hoover / HathiTrust / 台北 DRNH）
- 入库文档总数：**845 篇**
- 页/段落片段总数：**1059**
- 已有中文译文片段：**1059（100%）**

## 各档案源译文情况

| 档案源 | 文档数 | 页段数 | 中译覆盖 |
|---|---:|---:|---:|
| 台北 DRNH | 364 | 364 | 100% |
| FRUS（含 11 个分卷） | 299 | 416 | 100% |
| CIA Reading Room | 102 | 102 | 100% |
| HathiTrust / Internet Archive | 54 | 54 | 100% |
| Wilson Center | 24 | 121 | 100% |
| Hoover Institution | 2 | 2 | 100% |

## 译文状态分布

| 状态 | 含义 | 后续动作 |
|---|---|---|
| `human-reviewed` | 人工已审 | 可直接学术引用 |
| `human-excerpt` / `reference-summary` | 人工撰写的摘译 / 摘要（DRNH 案由学术导读多归此类） | 维持现状 |
| `machine-draft-review-needed` | 机器初稿，需复审 | 抽查 / 入队 retranslate |
| `machine-draft-local-review-needed` | 本地 LLM 初稿，需复审 | 入质量队列 |
| `pending-deepseek-retranslate` | 排队等 DeepSeek 重译 | 跑 `retranslate_with_deepseek.py` |

## 5 月（5/13–5/26）主要工程

- **5/13–5/20**：完成 6 源全量入库；建立 1059 页中译；FTS5 全文索引（含繁简自动展开 + trigram）；研究卡片 + 引用导出；事件骨架 1548 条；DRNH 364 篇 + 265 份案由学术导读
- **5/21**：FRUS 史料长编（按时间线编排、双语对照、出版级 PDF）；6 平台史料长编生成器
- **5/22**：DRNH 自动转写校订分层队列建立（重点 136 / 常规 13 / 背景 133）
- **5/23**：译文质量分诊工作台 + 校订与调档工作台接入；外部档案获取优先队列（29 个 Kew / HKPRO / 中研院 / Hoover 目标）
- **5/26**：CIA 译文修复（5 篇 hardcode 重写 + 6 篇局部替换 + 模型应答前言通用清除 + 民盟成员上海撤离档案补译）；CIA 通用清理覆盖剩余 28 篇文档（自动清 CIA 元数据 / 威氏拼音人名对照表 / markdown 残留）；新增 translation_failed 检测 + DRNH 跳过 length 检测

## 当前质量监控

`build_translation_quality_report.py` 输出多类 issue（按严重度从高到低）：

| 类型 | 严重度 | 说明 |
|---|---:|---|
| `translation_failed` | **4** | 译文是模型应答 / 拒绝消息，**必须重译**（5/26 新增检测） |
| `missing_translation` | 3 | 完全缺少中译 |
| `length_too_short` / `known_bad_term` | 3 | 译文偏短 / 含已知错术语 |
| `length_short` | 2 | 译文可能偏短 |
| `english_residue`（≥4 处） | 2 | 英文残留较多 |
| `length_long` | 1 | 译文可能偏长（DRNH 学术导读已跳过此检测） |
| `english_residue`（< 4 处） | 1 | 个别英文词残留 |

> **5/26 修复要点**：
> 1. 原先 DRNH 案由学术导读被错标为 `length_long`（中文长出英文几倍）—— 已跳过 DRNH 文档的 length 检测
> 2. 新增 `translation_failed` 检测捕获 wilson:111240 这类模型拒绝失败（"抱歉，您似乎只提供了 --- page break ---..."）

## 一键扫地

```bash
bash scripts/build/run_polish.sh
```

一次跑通：CIA 残留清理 → 重生成质量报告 → DRNH 校订分层 → 外部档案队列 → HathiTrust 分诊 → 优先翻译问题处理 → 术语索引注解。

## 校订流程

1. **重灾**：先看 `data/translation_quality_issues.csv` 中 severity ≥ 3 的（translation_failed / missing_translation / known_bad_term）
2. **抽查**：核心文献中民盟 / 政协 / 第三党 / 昆明暗杀 / 1949 年北平接触等高频主题
3. **回扫**：发现的术语错加入 `data/translation_glossary.csv` 或后处理规则
4. **升级**：对正式引用文档升级状态为 `human-reviewed`
5. **重译**：translation_failed / 严重残留 → `scripts/translate/retranslate_with_deepseek.py`

## 数据真实性提示

- 中文译文当前用于：全文检索、快速阅读、定位原文页码、史料长编自动汇编、学术导读底稿
- **正式学术引用**：仍应回溯原文（FRUS / CIA / Wilson / DRNH 原档）
- DRNH 中"案由学术导读"标注「机器初拟，待人工校订」，不替代真实档案内容
