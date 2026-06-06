# CIA 卷扩展扫描 v2 · 阶段 3 后续期复核报告

> 民盟历史文献研究库 · CIA 卷查漏补缺第 2 轮 · 2026-06-05

## 一、复核范围

本阶段处理阶段 1 中 1950-1957 年的 104 篇 CIA Reading Room 扩展候选。这批候选主要来自 `third force`、`third party`、`minor parties`、`coalition government`、`Political Consultative`、`Democratic Parties` 等宽关键词。

## 二、执行结果

| 项目 | 数量 |
|---|---:|
| 候选 | 104 |
| OCR 成功 | 102 |
| OCR 待补 | 2 |
| 直接核心文献 | 0 |
| 相关文献 | 1 |
| 背景材料 | 68 |
| 排除 | 33 |
| 本阶段新增入库 | 0 |

本阶段未发现新的 CIA 核心民盟档案。唯一相关文献为：

| 日期 | identifier | 判断 | 平台状态 |
|---|---|---|---|
| 1951-04-13 | `cia-readingroom-document-cia-rdp80-00809a000600390004-4` | 相关文献 | 已在库，`相关文献`，译文状态 `human-reviewed-cia-v2-2026-05-31` |

该篇题为 `COUNTERREVOLUTIONARY ACTIVITIES IN CHINA`，并非民盟组织活动核心档，但在西南地区镇反叙述中提到李公朴、闻一多遇害，以及“杜斌丞，西安民盟官员”被杀。它可作为民盟人物受迫害叙事的旁证材料，不宜升为核心文献。

## 三、两个 OCR 待补候选

| 日期 | identifier | 标题 | 初步判断 |
|---|---|---|---|
| 1950-03-20 | `cia-readingroom-document-cia-rdp82-00457r004500500008-3` | `DENIAL OF NEWS REPORTS BY CHANG FA-KNEI` | 仅弱命中 `"third party" Chiang Kai-shek`，待补 OCR |
| 1954-11-06 | `cia-readingroom-document-cia-rdp74-00297r000601240024-6` | `THE MYSTERIOUS DOINGS OF CIA` | 仅弱命中 `"third force" China`，待补 OCR |

两篇在 archive.org metadata 中可见 `_djvu.txt` 文件，但本轮脚本下载时未稳定取到文本。它们均为弱概念命中，不影响“未发现新增核心民盟档”的阶段性结论。后续网络条件稳定后可单独补跑。

## 四、学术判断

阶段 1 曾估计 CIA v2 可能补入 30-60 篇，这一估计偏高。阶段 2 和阶段 3 的 OCR 复核显示，宽关键词会大量命中战后欧洲、菲律宾、韩国、一般冷战政治、反革命镇压、国际宣传和 CIA 机构评论材料。

对中国民主同盟研究而言，CIA 卷目前最有价值的主体仍是既有 102 篇中的核心与相关文献，尤其是 1946-1952 年关于海外分支、香港总部、罗隆基、张澜、沈钧儒、民盟地方组织和新政协代表名单的材料。本轮扩展的主要价值是排除了大批噪声，证明不应为了“扩量”牺牲研究范围的准确性。

## 五、已落产物

| 文件 | 内容 |
|---|---|
| `data/cia_extended_v2_llm_review_1950_1957.csv` | 1950-1957 年 104 篇候选复核结果 |
| `data/cia_extended_v2_ocr_cache/` | CIA v2 OCR 缓存，目前含关键期与后续期已抓文本 |
| `scripts/build/cia_extended_v2_llm_review.py` | 支持 `--year-from`、`--year-to`、`--out` 参数；缺 OCR 候选会写入 CSV |

