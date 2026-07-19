# 《光明報》新二十二號文章级拆分报告

- **日期**：2026-07-19  
- **执行**：grok（mingmeng-history-research 国内资料库 subagent）  
- **对象**：NLC404-01J000514-10483《光明報》新二十二號（1947-08-01，邹李闻陶四烈士纪念特辑）  
- **PDF**：`data/domestic/press_scans/NLC404-01J000514-10483_光明報_1947年22期.pdf`（20 页）  
- **页图**：`work/domestic/continue_pages/1947_22/page-01.png` … `page-20.png`

## 1. 工作摘要

| 项 | 结果 |
|----|------|
| 本轮新增文章候选 | **21** |
| 既有整期 + 社论 | 2（未改 status） |
| issue22 相关合计 | 23 |
| 认证等级 | 全部新增为 **L1** |
| review_status | 全部新增为 **needs_human_review**（不自动 accepted） |
| event_tags | `1946李闻事件` |
| event_coverage | 已挂入 `domestic-1946-li-wen` |
| 校验 | **通过**（见 §5） |

## 2. 渲染

- 既有：`page-01.png`–`page-06.png`
- 本轮 pymupdf（2×）补渲：`page-07.png`–`page-20.png`
- 现共 20 页 PNG，与 PDF 页数一致
- 辅助裁切（仅导航，不作引文）：`work/domestic/continue_pages/1947_22/crops/`

## 3. 新增列表（题名 / 署名 / 起止页）

页码均为 **PDF 页序**（与 `page-NN.png` 一致）。题名、署名以正文目视为准；封面目录作交叉核对。

| # | candidate_id | 题名 | 署名 | 起–止 |
|---|--------------|------|------|-------|
| 1 | `…issue22-middle-route-again-deng` | 再論中間路線問題 | 鄧初民 | 4–5 |
| 2 | `…issue22-one-year-war-result-lu` | 打了一年多以後的結果 | 陸詒 | 6–8 |
| 3 | `…issue22-cry-recall-xingzhi-deng` | 哭憶行知 | 鄧初民 | 9–9 |
| 4 | `…issue22-gongpu-still-beside-zhang` | 公樸，你還在我的身邊 | 張曼筠 | 10–10 |
| 5 | `…issue22-learn-taofen-spirit-hu` | 習韜奮精神 | 胡仲持 | 11–11 |
| 6 | `…issue22-patriotic-poet-wen-hong` | 愛國詩人聞一多 | 洪道 | 12–12 |
| 7 | `…issue22-hengshe-tonghua-sa` | 由衡舍桐花談起 | 薩空了 | 13–13 |
| 8 | `…issue22-action-memorial-peng` | 用行動來紀念鄒李聞陶四先生 | 彭澤民 | 14–14 |
| 9 | `…issue22-double-effort-people-shen` | 加倍為人民事業努力 | 沈志遠 | 14–14 |
| 10 | `…issue22-wipe-out-killers-li` | 撲滅殺人的兇手 | 李伯球 | 15–15 |
| 11 | `…issue22-pass-the-test-hu-sheng` | 過關 | 胡繩 | 15–15 |
| 12 | `…issue22-liwen-anniversary-qian` | 李聞週年祭 | 千家駒 | 15–15 |
| 13 | `…issue22-painful-memorial-chen` | 沉痛紀念鄒李聞陶四先生 | 陳其瑗 | 16–16 |
| 14 | `…issue22-mourn-and-spur-song` | 悼念逝者，鞭策自己 | 宋雲彬 | 16–16 |
| 15 | `…issue22-dare-not-forget-chen` | 不敢忘 | 陳此生 | 16–16 |
| 16 | `…issue22-dictators-killed-them-ye` | 是獨裁者殺死了他們！ | 葉眠 | 16–16 |
| 17 | `…issue22-gongpu-rest-in-peace-simu` | 公樸，安眠吧！ | 思慕 | 17–17 |
| 18 | `…issue22-one-falls-thousands-rise-lu` | 一個倒下去千百個起來 | 陸詒 | 17–17 |
| 19 | `…issue22-history-essays-shen-gong` | 讀史隨筆 | 申公 | 18–18 |
| 20 | `…issue22-shantou-black-terror` | 汕頭的黑色恐怖 | 烈風 | 18–18 |
| 21 | `…issue22-meixian-recent-look` | 梅縣近貌 | 理晋 | 20–20 |

完整 id 前缀：`domestic:NLC:guangmingbao-1947-`

### 既有（本轮不重登、不改 accepted）

| candidate_id | 题名 | 页 | status |
|--------------|------|----|--------|
| `domestic:NLC:guangmingbao-1947-issue22` | 《光明報》新二十二號（整期） | 1–20 | accepted |
| `domestic:NLC:guangmingbao-1947-issue22-fight-for-human-rights-editorial` | 為爭取人權而奮鬥 | 2–3（社论） | needs_human_review |

说明：封面与第 2–3 页大字连读题名实为「**為爭取基本的人權而奮鬥**」；既有候选作「為爭取人權而奮鬥」，本轮**不改题**，仅在报告中注明。

## 4. 页界与版面要点

```
p1  封面目录（新二十二號；鄒李聞陶四先烈紀念特輯）
p2–3  社论《為爭取基本的人權而奮鬥》+ 同页短评栏（未全拆）
p4–5  鄧初民《再論中間路線問題》
p6–8  陸詒《打了一年多以後的結果》
p9    特辑起：鄧初民《哭憶行知》
p10   張曼筠《公樸，你還在我的身邊》；左栏「我們要學習」（未单立）
p11   胡仲持《習韜奮精神》
p12   洪道《愛國詩人聞一多》
p13   薩空了《由衡舍桐花談起》
p14   「我們的悼念」栏：彭澤民、沈志遠等
p15   李伯球、胡繩、千家駒
p16   陳其瑗、宋雲彬、陳此生、葉眠
p17   思慕、陸詒（「一個倒下去…」）
p18   申公《讀史隨筆》；烈風《汕頭的黑色恐怖》（通訊）
p19   《牧野之戰》等（署名未稳，未登）
p20   理晋《梅縣近貌》（通訊）
```

### 封面目录（RTL 竖排解读，供对照）

- （社論）為爭取基本的人權而奮鬥；短評四則  
- 鄧初民｜再論中間路線問題  
- 陸詒｜打了一年多以後的結果  
- **特輯**：初民｜哭憶行知；張曼筠｜公樸…；胡仲持｜我們要學習韜奮的精神；洪道｜愛國詩人聞一多；薩空了｜由衡舍桐花談起；彭澤民｜用行動來紀念…；沈志遠｜加倍為人民事業努力；李伯球｜撲滅殺人的兇手…；胡繩｜過關；千家駒｜李聞週年祭；陳其瑗｜沉痛紀念…；宋雲彬｜悼念逝者・鞭策自己；葉眠｜是獨裁者殺死了他們；思慕｜公樸，安眠吧！；陸詒｜一個倒下去，千百個起來  
- 申公｜讀史隨筆；烈風｜汕頭的黑色恐怖（通訊）；梅縣近貌（通訊）

## 5. 未拆 / 未登原因

| 版面现象 | 原因 |
|----------|------|
| 第 2 页《為什麼特輯再來一次？》《魏特邁將軍此來何為？》《總動員就是搜刮》等 | 题名可辨，**署名未共现**；疑属「短評四則」，不猜测作者 |
| 第 3 页「廣東也應要求自治」「香港工商業家的自救之路」等栏 | 题名/作者/页界未同时稳固确认 |
| 第 10 页左栏「我們要學習」 | 与封面胡仲持长题可能相关，但**本页未与署名同栏共现**；胡文仅锁第 11 页 |
| 第 19 页《牧野之戰》 | 题名可见，**署名未稳** |
| 广告「有利刊物」等 | 非文章 |
| 全文转录、异体校对 | 明确不在本轮范围；OCR 仅导航、不作正式引文 |

## 6. 校验输出

```text
$ python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
{"records": 394, "failed": 0, "passed": 394}
exit=0

$ python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
{"candidate_ids": 394, "events": 9, "missing_candidate_references": [], "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}
exit=0
```

## 7. candidate_id 完整列表（本轮新增 21）

1. `domestic:NLC:guangmingbao-1947-issue22-middle-route-again-deng`
2. `domestic:NLC:guangmingbao-1947-issue22-one-year-war-result-lu`
3. `domestic:NLC:guangmingbao-1947-issue22-cry-recall-xingzhi-deng`
4. `domestic:NLC:guangmingbao-1947-issue22-gongpu-still-beside-zhang`
5. `domestic:NLC:guangmingbao-1947-issue22-learn-taofen-spirit-hu`
6. `domestic:NLC:guangmingbao-1947-issue22-patriotic-poet-wen-hong`
7. `domestic:NLC:guangmingbao-1947-issue22-hengshe-tonghua-sa`
8. `domestic:NLC:guangmingbao-1947-issue22-action-memorial-peng`
9. `domestic:NLC:guangmingbao-1947-issue22-double-effort-people-shen`
10. `domestic:NLC:guangmingbao-1947-issue22-wipe-out-killers-li`
11. `domestic:NLC:guangmingbao-1947-issue22-pass-the-test-hu-sheng`
12. `domestic:NLC:guangmingbao-1947-issue22-liwen-anniversary-qian`
13. `domestic:NLC:guangmingbao-1947-issue22-painful-memorial-chen`
14. `domestic:NLC:guangmingbao-1947-issue22-mourn-and-spur-song`
15. `domestic:NLC:guangmingbao-1947-issue22-dare-not-forget-chen`
16. `domestic:NLC:guangmingbao-1947-issue22-dictators-killed-them-ye`
17. `domestic:NLC:guangmingbao-1947-issue22-gongpu-rest-in-peace-simu`
18. `domestic:NLC:guangmingbao-1947-issue22-one-falls-thousands-rise-lu`
19. `domestic:NLC:guangmingbao-1947-issue22-history-essays-shen-gong`
20. `domestic:NLC:guangmingbao-1947-issue22-shantou-black-terror`
21. `domestic:NLC:guangmingbao-1947-issue22-meixian-recent-look`

## 8. 后续建议

1. 人工复审第 6–8 页陆诒文是否在第 8 页中段另起他文。  
2. 补认第 2–3 页短评四则题名+是否署编辑部。  
3. 第 10 页「我們要學習」与第 11 页胡仲持是否应合并页界。  
4. 既有社论题名是否升为「為爭取基本的人權而奮鬥」。  
5. 全文转录与 L1→accepted 另走人工队列。  
