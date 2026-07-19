# 页界/题名目视抽检报告 — issue22 第二轮（2026-07-19）

- **执行**：mingmeng-history-research 抽检 agent（grok）
- **范围**：`domestic:NLC:guangmingbao-1947-issue22-*` 文章级候选
- **排除（已在 `subagent_page_boundary_sample_20260719.md` 抽过）**：
  - `…fight-for-human-rights-editorial`
  - `…one-year-war-result-lu`
  - `…cry-recall-xingzhi-deng`
  - `…action-memorial-peng`
  - `…dictators-killed-them-ye`
- **方法**：对照 `work/domestic/continue_pages/1947_22/page-01.png`–`page-20.png` 目视题名、署名、起止页、共页拆分；默认不改 jsonl
- **数据修改**：本轮 **否**（0 条）

## 0. 汇总

| 项 | 数 |
|----|---:|
| 抽检 N | **8** |
| 通过 | **8** |
| 问题（明确错误） | **0** |
| 是否改了数据 | **否** |

### 抽样构成（覆盖多页 / 共页 / 通讯）

| # | 缩写 id | 页界类型 |
|---|---------|----------|
| 1 | `middle-route-again-deng` | 多页 4–5 |
| 2 | `gongpu-still-beside-zhang` | 单页共栏 p10 |
| 3 | `learn-taofen-spirit-hu` | 单页 p11（封面题名微异） |
| 4 | `patriotic-poet-wen-hong` | 单页 p12 |
| 5 | `double-effort-people-shen` | 共页 p14（与彭文） |
| 6 | `wipe-out-killers-li` | 共页 p15（三文） |
| 7 | `gongpu-rest-in-peace-simu` | 共页 p17（与陆诒） |
| 8 | `meixian-recent-look` | 通讯单页 p20 |

---

## 1. 通过列表（8）

**封面复核**（`page-01.png`）：期号 **新二十二號**；日期戳 **AUG 1 1947**；特辑栏 **鄒李聞陶四先烈紀念特輯** — 与登记 `document_date=1947-08-01` 一致。

| # | candidate_id | 登记题名 | 页界 | 目视结论 |
|---|--------------|----------|------|----------|
| 1 | `domestic:NLC:guangmingbao-1947-issue22-middle-route-again-deng` | 再論中間路線問題 | PDF 4—5 | **通过**。p4 右竖大题「再論中間路線問題」+ 鄧初民；p5 续（含「中間階層的政治要求」等节，无新篇大题）；p6 起陸詒《打了一年多以後的結果》→ 止于 5 合理 |
| 2 | `domestic:NLC:guangmingbao-1947-issue22-gongpu-still-beside-zhang` | 公樸，你還在我的身邊 | PDF 10 | **通过**。p10 框题与署名「張曼筠」可辨；同页左栏「我們要學習」**未**并入本条（与 evidence_note 一致）。封面目录作「公樸、我還在你的身邊」措辞微异，以正文为准正确 |
| 3 | `domestic:NLC:guangmingbao-1947-issue22-learn-taofen-spirit-hu` | 習韜奮精神 | PDF 11 | **通过**。p11 大题「習韜奮精神」+ 胡仲持；正文述生活書店/韜奮。封面长题「我們要學習韜奮的精神」与正文短题对应，登记取正文正确。p10 左栏「我們要學習」不宜强并（署名不在同栏） |
| 4 | `domestic:NLC:guangmingbao-1947-issue22-patriotic-poet-wen-hong` | 愛國詩人聞一多 | PDF 12 | **通过**。p12 竖题「愛國詩人聞一多」+ 洪道；封面一致；p13 转萨空了文 → 单页合理 |
| 5 | `domestic:NLC:guangmingbao-1947-issue22-double-effort-people-shen` | 加倍為人民事業努力 | PDF 14 | **通过**。p14「我們的悼念」栏内中栏题名 + 沈志遠；同页彭澤民《用行動來紀念…》已另条，共页拆清 |
| 6 | `domestic:NLC:guangmingbao-1947-issue22-wipe-out-killers-li` | 撲滅殺人的兇手 | PDF 15 | **通过**。p15 右竖题「撲滅殺人的兇手」+ 副行「以紀念鄒李聞陶四先烈」+ 李伯球；同页另有胡繩《過關》、千家駒《李聞週年祭》各为独立候选，栏界可辨 |
| 7 | `domestic:NLC:guangmingbao-1947-issue22-gongpu-rest-in-peace-simu` | 公樸，安眠吧！ | PDF 17 | **通过**。p17 大题 + 思慕；文内「結論」为小节标，非另篇；同页陆诒《一個倒下去千百個起來》另条，拆清 |
| 8 | `domestic:NLC:guangmingbao-1947-issue22-meixian-recent-look` | 梅縣近貌 | PDF 20 | **通过**。p20 框题「梅縣近貌」+ 理晋；p19 为《牧野之戰》（未登），不与本条连续 → 起止页合理。封面通讯栏一致 |

---

## 2. 问题列表

（无）

---

## 3. 非阻断观察（未改数据）

1. **封面 vs 正文题名微异**（登记取正文，正确）：
   - 張曼筠：封面「公樸、我還在你的身邊」↔ 正文「公樸，你還在我的身邊」
   - 胡仲持：封面「我們要學習韜奮的精神」↔ 正文「習韜奮精神」
2. **p10「我們要學習」**：仍无单独 candidate；与 p11 胡文是否同文延伸未在本轮立新条，既有拆分可接受。
3. **p15 / p14 / p16 / p17 共页**：本轮抽到的共页条均已拆清；p16 陈其瑗/宋云彬/陈此生/叶眠（叶眠上轮已抽）栏界与登记一致（本轮未重抽叶眠）。
4. **p18 申公《讀史隨筆》+ 烈風《汕頭的黑色恐怖》**、p16 陈其瑗长题含「總動員」声中等：未列入本 8 条，可作后续抽检池。
5. **p19《牧野之戰》**：题名可辨、署名未稳，仍符合既有「未登」策略。

---

## 4. 数据修改清单

无。

校验：

```text
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
{"records": 405, "failed": 0, "passed": 405}
```

---

## 5. 推荐 accept 清单（本轮通过 8）

> 仅推荐，**未**自行改 `review_status` / accepted。

1. `domestic:NLC:guangmingbao-1947-issue22-middle-route-again-deng`
2. `domestic:NLC:guangmingbao-1947-issue22-gongpu-still-beside-zhang`
3. `domestic:NLC:guangmingbao-1947-issue22-learn-taofen-spirit-hu`
4. `domestic:NLC:guangmingbao-1947-issue22-patriotic-poet-wen-hong`
5. `domestic:NLC:guangmingbao-1947-issue22-double-effort-people-shen`
6. `domestic:NLC:guangmingbao-1947-issue22-wipe-out-killers-li`
7. `domestic:NLC:guangmingbao-1947-issue22-gongpu-rest-in-peace-simu`
8. `domestic:NLC:guangmingbao-1947-issue22-meixian-recent-look`

---

## 6. 返回值（给调度）

| 指标 | 值 |
|------|----|
| 抽检 8 条 ID | 见 §5 |
| 通过数 | **8** |
| 问题数 | **0** |
| 是否改了数据 | **否** |
| 推荐 accept 的 ID 列表 | 同上 8 条 |
| 报告路径 | `work/domestic/subagent_issue22_sample2_20260719.md` |
