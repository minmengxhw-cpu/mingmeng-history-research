# 页界/题名目视全量抽检报告 — issue22 剩余 needs_human_review（2026-07-19）

- **执行**：mingmeng-history-research 抽检 agent（grok / mingmeng-history-research 抽检）
- **范围**：全部 `domestic:NLC:guangmingbao-1947-issue22-*` 且 `review_status=needs_human_review`
- **页图**：`work/domestic/continue_pages/1947_22/page-01.png`–`page-20.png`（及 `crops/*_top.png` 辅助）
- **方法**：目视题名、署名、起止页、共页拆分；对照封面目录交叉核对
- **数据修改**：本轮 **否**（0 条 jsonl 修正）
- **accepted**：本轮 **未** 自行改 `review_status`（由主会话统一 accept）

## 0. 汇总

| 项 | 数 |
|----|---:|
| 剩余条数（全量目视） | **13** |
| 通过 | **13** |
| 问题（明确错误） | **0** |
| 是否改了数据 | **否** |
| validate_candidates | **405/405 通过** |

### 与前轮关系

| 前轮 | 本轮状态 |
|------|----------|
| `subagent_page_boundary_sample` 已抽 5 条 issue22 | 其中 4 条已 accept；仍 `needs_human_review` 且本轮重验：**one-year-war / cry-recall / action-memorial / dictators**（4） |
| `subagent_issue22_sample2` 已抽 8 条 | 该 8 条均已 accept；不在本池 |
| 从未目视 | **9** 条（hengshe / pass-the-test / liwen-anniversary / painful / mourn / dare-not-forget / one-falls / history-essays / shantou） |

---

## 1. 封面锚点

`page-01.png` / `crops/p01_toc.png`：

- 期号：**新二十二號**
- 特辑栏：**鄒李聞陶四先烈紀念特輯**
- 目录条目与下文各文题名/署名大体一致（个别封面措辞与正文微异，以正文为准）

---

## 2. 通过列表（13）

| # | candidate_id | 登记题名 | 署名 | 页界 | 目视结论 |
|---|--------------|----------|------|------|----------|
| 1 | `…issue22-one-year-war-result-lu` | 打了一年多以後的結果 | 陸詒 | PDF 6—8 | **通过**。p6 大题+陸詒；p7「二、華北戰局」等续文、无新篇大题；p8 仍政治议论；p9 转入特辑《哭憶行知》→ 止于 8 合理 |
| 2 | `…issue22-cry-recall-xingzhi-deng` | 哭憶行知 | 鄧初民 | PDF 9 | **通过**。p9 大题「哭憶行知」+ 副题「兼哭李公樸、聞一多先生」+「鄧初民先生」；右栏「鄒、李、聞、陶，四先烈紀念特輯」；p10 起张曼筠 → 单页合理 |
| 3 | `…issue22-hengshe-tonghua-sa` | 由衡舍桐花談起 | 薩空了 | PDF 13 | **通过**。p13 横题「由衡舍桐花談起」+ 中点署「空了」；封面「薩空了」补全正确；p14 转「我們的悼念」栏 → 单页合理 |
| 4 | `…issue22-action-memorial-peng` | 用行動來紀念鄒李聞陶四先生 | 彭澤民 | PDF 14 | **通过**。p14 横题+彭澤民；直栏总题「我們的悼念」；同页沈志遠《加倍…》另条（已 accept）拆清 |
| 5 | `…issue22-pass-the-test-hu-sheng` | 過關 | 胡繩 | PDF 15 | **通过**。p15 左栏大题「過關」+ 胡繩；与李伯球、千家駒共页，栏界可辨 |
| 6 | `…issue22-liwen-anniversary-qian` | 李聞週年祭 | 千家駒 | PDF 15 | **通过**。p15 中栏「李聞週年祭」+ 千家駒；p16 起陈其瑗等 → 单页合理 |
| 7 | `…issue22-painful-memorial-chen` | 沉痛紀念鄒李聞陶四先生 | 陳其瑗 | PDF 16 | **通过**。p16 上栏双行题「「總動員」聲中／沉痛紀念鄒李聞陶四先生」+ 陳其瑗；登记取正题（略眉题）可接受，evidence_note 已记连读 |
| 8 | `…issue22-mourn-and-spur-song` | 悼念逝者，鞭策自己 | 宋雲彬 | PDF 16 | **通过**。p16 中栏题名+ 简署「雲彬」；封面「宋雲彬」补全正确 |
| 9 | `…issue22-dare-not-forget-chen` | 不敢忘 | 陳此生 | PDF 16 | **通过**。p16 右栏题「不敢忘」+ 陳此生；封面目录未单列，据正文补登合理，独立短文可辨 |
| 10 | `…issue22-dictators-killed-them-ye` | 是獨裁者殺死了他們！ | 葉眠 | PDF 16 | **通过**。p16 下栏题名+葉眠；文末「一九四七年七月十五日發自香港」；封面有对应条 |
| 11 | `…issue22-one-falls-thousands-rise-lu` | 一個倒下去千百個起來 | 陸詒 | PDF 17 | **通过**。p17 右栏竖题+陸詒；文末「一九四七·七·十六·於香港」；同页思慕《公樸，安眠吧！》另条（已 accept）拆清 |
| 12 | `…issue22-history-essays-shen-gong` | 讀史隨筆 | 申公 | PDF 18 | **通过**。p18 框题「讀史隨筆」+ 申公；同页通讯栏另文不并入 |
| 13 | `…issue22-shantou-black-terror` | 汕頭的黑色恐怖 | 烈風 | PDF 18 | **通过**。p18「汕頭的黑色恐怖」+「（汕頭通訊）」+ 烈風；封面通讯栏一致；与申公文共页拆清 |

完整 id 前缀：`domestic:NLC:guangmingbao-1947-`

---

## 3. 问题列表

（无。无题名错误、无页界张冠李戴、无误并邻文。）

---

## 4. 非阻断观察（未改数据）

1. **陈其瑗**：正文眉题「「總動員」聲中」+ 正题「沉痛紀念…」；登记题名为正题，与前轮策略一致。
2. **简署补全**（登记已做且合理）：空了→薩空了；雲彬→宋雲彬。
3. **陳此生《不敢忘》**：封面目录无对应条，仅正文可辨；独立短文栏界清楚，可 accept。
4. **p15 三文 / p16 四文 / p17 二文 / p18 二文**：共页拆分均与登记一致，栏界目视可分。
5. **p19《牧野之戰》**：仍未登（署名未稳），与本 13 条无关。
6. **已 accept 的 issue22 文章**（本轮不重登、不改）：社论、邓初民中間路線、张曼筠、胡仲持、洪道、沈志远、李伯球、思慕、理晋梅县等。

---

## 5. 数据修改清单

无。

校验：

```text
$ python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
{"records": 405, "failed": 0, "passed": 405}
exit=0
```

---

## 6. 推荐 accept 清单（本轮通过 13）

> 仅推荐，**未**自行改 `review_status` / accepted。

1. `domestic:NLC:guangmingbao-1947-issue22-one-year-war-result-lu`
2. `domestic:NLC:guangmingbao-1947-issue22-cry-recall-xingzhi-deng`
3. `domestic:NLC:guangmingbao-1947-issue22-hengshe-tonghua-sa`
4. `domestic:NLC:guangmingbao-1947-issue22-action-memorial-peng`
5. `domestic:NLC:guangmingbao-1947-issue22-pass-the-test-hu-sheng`
6. `domestic:NLC:guangmingbao-1947-issue22-liwen-anniversary-qian`
7. `domestic:NLC:guangmingbao-1947-issue22-painful-memorial-chen`
8. `domestic:NLC:guangmingbao-1947-issue22-mourn-and-spur-song`
9. `domestic:NLC:guangmingbao-1947-issue22-dare-not-forget-chen`
10. `domestic:NLC:guangmingbao-1947-issue22-dictators-killed-them-ye`
11. `domestic:NLC:guangmingbao-1947-issue22-one-falls-thousands-rise-lu`
12. `domestic:NLC:guangmingbao-1947-issue22-history-essays-shen-gong`
13. `domestic:NLC:guangmingbao-1947-issue22-shantou-black-terror`

---

## 7. 返回值（给调度）

| 指标 | 值 |
|------|----|
| 剩余条数 | **13** |
| 通过数 | **13** |
| 问题数 | **0** |
| 是否改了数据 | **否** |
| 推荐 accept 的完整 ID 列表 | 见 §6（13 条） |
| 报告路径 | `work/domestic/subagent_issue22_remaining_sample_20260719.md` |
