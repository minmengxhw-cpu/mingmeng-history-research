# CIA 卷扩展扫描 v2 · 阶段 2 关键期复核报告

> 民盟历史文献研究库 · CIA 卷查漏补缺第 2 轮 · 2026-06-05

## 一、复核范围

本阶段只处理阶段 1 中 1946-1949 年民盟关键期的 22 篇 CIA Reading Room 新候选。该范围对应民盟从政协谈判、被国民政府宣布为非法组织、香港临三中全会重建，到参加新政协前后的核心时段。

## 二、执行方法

- 从 archive.org 下载 22 篇候选的 `djvu.txt` OCR，全数下载成功。
- 因当前环境未设置 `DEEPSEEK_API_KEY`，未调用外部 LLM；本轮改用本地规则复核，并在 CSV 中保留证据窗口。
- 直接入库线：出现 `China Democratic League`、`Chinese Democratic League`、`Federation of Chinese Democratic Parties`，或出现罗隆基、章伯钧、沈钧儒、张君劢、张澜、梁漱溟、黄炎培、史良、胡愈之、李公朴、闻一多、杜斌丞、张东荪、陶行知、马寅初、高崇民等民盟核心人物威氏拼音。
- 排除线：命中 Malayan / Taiwan / Korean / Burmese Democratic League，或 WFDW 等非中国民主同盟组织。
- 背景线：仅出现 `third force`、`third party`、`minor parties`、`coalition government`、`Political Consultative` 等泛政治概念，但无民盟组织名或核心人物。

## 三、结果

| 项目 | 数量 |
|---|---:|
| 关键期候选 | 22 |
| OCR 下载成功 | 22 |
| 直接涉中国民主同盟 | 0 |
| 背景相关但未达入库线 | 16 |
| 排除 | 6 |
| 本阶段新增入库 | 0 |

本轮 22 篇没有发现中国民主同盟、民盟前身“中国民主政团同盟”或民盟核心人物的直接 OCR 命中。命中的关键词主要来自英美情报报告中对法国、意大利、菲律宾、苏联/东欧或一般中国内战语境的 `third force`、`minor parties`、`coalition government` 等泛概念使用。

## 四、重要判断

阶段 1 的 1946-1949 关键期候选看似贴近民盟史时段，但阶段 2 OCR 复核显示，多数属于关键词漂移：`third force` 和 `coalition government` 在战后欧洲政治报告中出现频率很高，`minor parties` 也常用于菲律宾、欧洲议会和一般党派结构，并不等同于中国民主同盟。

因此，本阶段不应为了扩大数量而强行入库。CIA v2 下一步更有价值的是继续处理 1950-1957 年的 104 篇候选，特别是阶段 1 已标为强信号的 Shih Liang / Hu Yu-chih 等民盟人物命中项。

## 五、已落产物

| 文件 | 内容 |
|---|---|
| `data/cia_extended_v2_llm_review.csv` | 22 篇关键期候选复核结果、判定、证据窗口 |
| `data/cia_extended_v2_ocr_cache/` | 22 篇候选 OCR 缓存 |
| `scripts/build/cia_extended_v2_llm_review.py` | 阶段 2 复核脚本；有 API key 时可 LLM 精读，无 API key 时本地规则复核 |

