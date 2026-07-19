# 《光明報》1947 中期号首面/目录+关键文拆分报告

- **日期**：2026-07-19  
- **执行**：grok（mingmeng-history-research 执行 agent）  
- **范围**：NLC 10453–10457、10460（新十三—十八、新二十一）  
- **禁令遵守**：不自动 `accepted`；不猜测题名；不删除既有  

## 0. 结果总览

| 项 | 结果 |
|----|------|
| 本轮**新建**文章候选 | **19** |
| 整期日期按封面校正 | **5**（13/14/15/16–17/18；21 原已正确） |
| `validate_candidates` | **通过** 425/425 |
| `validate_event_coverage` | **通过** missing=[] |
| 全部新建 status | `needs_human_review` |
| 全部新建 authenticity | `L1` |

## 1. 整期候选与封面日期（以封面实物为准）

版出日串按 **RTL** 读为「民国三十六年…」——以新二十一号已知正确日期 `日五月七年六十三` → 1947-07-05 为校准。

| NLC 件号 | 文件名卷期 | 封面期号 | 封面出版日（校正后） | 整期 candidate_id | 原登记日 |
|---|---|---|---|---|---|
| 10453 | 1947年13期 | 新十三號 | **1947-01-18** | `…1947-1947-13` | 1947-08-18（误） |
| 10454 | 1947年14期 | 新十四號 | **1947-01-28** | `…1947-1947-14` | 1947-08-28（误） |
| 10455 | 1947年15期 | 新十五號 | **1947-02-08** | `…1947-1947-15` | 1947-09-08（误） |
| 10456 | 1947年16–17期 | 新十六—十七號（合刊标示） | **1947-03-18** | `…1947-1947-16–17` | 1947-10-08（误） |
| 10457 | 1947年18期 | 新十八號 | **1947-05-14** | `…1947-1947-18` | 1947-10-18（误） |
| 10460 | 1947年21期 | 新二十一號 | **1947-07-05** | `…issue21` | 已正确 |

**内容互证（日期校正合理性）**

- 新十三/十四紧接 1947-01 民盟一届二中全会报道、开闭幕词、政治报告；十四号有「迎春晚会」——与 1947 年春节（1 月下旬）一致。  
- 十六—十七号正文《中国民主同盟对时局宣言》文末「中华民国三十六年三月八日」，刊出日 3 月 18 日合理。  
- 新二十一（7 月 5 日）与新二十二（8 月 1 日）编号连续，不再与「八月新十三」冲突。

**uncertainty**：封面期号与 NLC 文件名卷期数字一致（13↔新十三等）；**冲突主要在既往元数据日期**，已按封面更正并写入各整期 `uncertainty_note`。合刊 10456 封面作「号六七十新」式并置，NLC 作 16–17 期——以合刊实物+NLC 双标保留「新十六—十七號」。

页图根目录：`work/domestic/continue_pages/1947_{13,14,15,16-17,18,21}/`（各期至少 page-01…，关键文止页另渲至所需页）。

## 2. 每期新建条数与 IDs

### 2.1 新十三號（10453）— 新建 **4**

| candidate_id | 题名 | PDF 页 |
|---|---|---|
| `…issue13-our-attitude-editorial` | 我們的態度（社論） | 2—2 |
| `…issue13-zhang-lan-plenum-opening` | 民盟張瀾主席在一屆二中全會開幕講詞 | 4—5 |
| `…issue13-zhang-lan-plenum-closing` | 民盟二中全會張瀾主席閉幕詞 | 5—5 |
| `…issue13-plenum-clippings` | 民盟二中全會剪影輯 | 6—6 |

**未拆**：短評栏各则（无独立大题/署名标准不稳）；目录后部马叙伦介绍、萧源通讯等本轮未追止页。

### 2.2 新十四號（10454）— 新建 **4**

| candidate_id | 题名 | PDF 页 |
|---|---|---|
| `…issue14-pcc-anniversary-editorial` | 政協決議一週年（社論） | 2—2 |
| `…issue14-plenum-political-report` | 民盟二中全會政治報告全文（正文注代宣言） | 4—11 |
| `…issue14-shen-zhiyuan-plenum-impression` | 我對於民盟二中全會的觀感（沈志遠） | 12—13 |
| `…issue14-li-boqiu-plenum-gains` | 二中全會的收穫（李伯球） | 14—14 |

**未拆**：短評五则；目录「上海各党各派的迎春晚会」「民盟广东省支部告广东同胞书」等未在本轮 1–4 优先窗内完成止页核读（政治报告已追至 p11）。

### 2.3 新十五號（10455）— 新建 **2**

| candidate_id | 题名 | PDF 页 |
|---|---|---|
| `…issue15-heavier-task-editorial` | 民盟的任務更繁重了（社論） | 2—2 |
| `…issue15-huang-yaomian-pcc-line` | 政協決議與政協路線（黃藥眠） | 4—6 |

**未拆**：短評；张明德/洪泽/晨曦/陆诒/金殿等署名文止页未核。

### 2.4 新十六—十七號（10456）— 新建 **4**

| candidate_id | 题名 | PDF 页 |
|---|---|---|
| `…issue16-17-li-jishen-situation-views` | 李濟深將軍對時局意見（轉載） | 2—2 |
| `…issue16-17-minmeng-situation-declaration` | 中國民主同盟對時局宣言 | 3—3 |
| `…issue16-17-respond-li-jishen-editorial` | 響應李濟深先生對時局主張（社論一） | 4—4 |
| `…issue16-17-moscow-conference-china-editorial` | 莫斯科會議應該討論中國問題（社論二） | 4—4 |

**未拆**：李伯球/林楚/千家驹/萨空了/陆诒及盟务通讯等；目录「社论（一）（二）」与正文题名对应以正文为准已记 uncertainty。

### 2.5 新十八號（10457）— 新建 **3**

| candidate_id | 题名 | PDF 页 |
|---|---|---|
| `…issue18-people-cannot-endure-editorial` | 老百姓是再也不能忍耐了（社論） | 2—3 |
| `…issue18-nantotal-press-reception` | 民盟南總支部招待中外記者誌詳（本報記者） | 2—2 |
| `…issue18-peng-zemin-statement` | 民盟南總支部申明態度——主任委員彭澤民發表書面談話 | 4—4 |

**未拆**：短評五则；黄药眠/陆诒等后续署名文。

### 2.6 新二十一號（10460）— 新建 **2**

| candidate_id | 题名 | PDF 页 |
|---|---|---|
| `…issue21-critique-dictatorship-new-policy-editorial` | 評獨裁派的所謂「新政策」（社論） | 2—2 |
| `…issue21-deng-chumin-middle-route` | 中間路線沒有現實的根據（鄧初民） | 4—6 |

**未拆**：短評；黄药眠巴黎三外长会议等 p7 起未纳入本轮「首面优先」建卡清单（题名清晰但非本轮强制）。

## 3. event_tags 与 coverage

- 新建 19 条均挂 **`1947民盟被宣布非法`**（非法化前机关报/路线表达语境；与既有整期一致）。  
- **未**挂 `1946李闻事件`（非纪念特辑；李闻材料仍在新二十二）。  
- `event_coverage` 中 `domestic-1947-illegal-dissolution` 已追加 19 个新 ID；`domestic_status` 已更新。

## 4. 校验

```text
$ python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
{"records": 425, "failed": 0, "passed": 425}

$ python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
{"candidate_ids": 425, "events": 9, "missing_candidate_references": [], "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}
```

| 指标 | 值 |
|------|---:|
| records | 425 |
| failed | 0 |
| accepted | 198 |
| needs_human_review | 227 |
| L1 / L2 / L3 / L4 / LX | 323 / 50 / 8 / 40 / 4 |
| events | 9 |
| missing_candidate_references | [] |

## 5. 新建 IDs 完整列表（19）

1. `domestic:NLC:guangmingbao-1947-issue13-our-attitude-editorial`  
2. `domestic:NLC:guangmingbao-1947-issue13-zhang-lan-plenum-opening`  
3. `domestic:NLC:guangmingbao-1947-issue13-zhang-lan-plenum-closing`  
4. `domestic:NLC:guangmingbao-1947-issue13-plenum-clippings`  
5. `domestic:NLC:guangmingbao-1947-issue14-pcc-anniversary-editorial`  
6. `domestic:NLC:guangmingbao-1947-issue14-plenum-political-report`  
7. `domestic:NLC:guangmingbao-1947-issue14-shen-zhiyuan-plenum-impression`  
8. `domestic:NLC:guangmingbao-1947-issue14-li-boqiu-plenum-gains`  
9. `domestic:NLC:guangmingbao-1947-issue15-heavier-task-editorial`  
10. `domestic:NLC:guangmingbao-1947-issue15-huang-yaomian-pcc-line`  
11. `domestic:NLC:guangmingbao-1947-issue16-17-li-jishen-situation-views`  
12. `domestic:NLC:guangmingbao-1947-issue16-17-minmeng-situation-declaration`  
13. `domestic:NLC:guangmingbao-1947-issue16-17-respond-li-jishen-editorial`  
14. `domestic:NLC:guangmingbao-1947-issue16-17-moscow-conference-china-editorial`  
15. `domestic:NLC:guangmingbao-1947-issue18-people-cannot-endure-editorial`  
16. `domestic:NLC:guangmingbao-1947-issue18-nantotal-press-reception`  
17. `domestic:NLC:guangmingbao-1947-issue18-peng-zemin-statement`  
18. `domestic:NLC:guangmingbao-1947-issue21-critique-dictatorship-new-policy-editorial`  
19. `domestic:NLC:guangmingbao-1947-issue21-deng-chumin-middle-route`  

## 6. 后续建议（非本轮范围）

1. Codex/cheer 复核五期封面日期校正（RTL 读法）是否写入 accepted 字段或二次确认。  
2. 新十九/新二十封面日期建议同样按 RTL 重核（可能同属元数据偏差）。  
3. 各期短評、通讯与其余署名文可按「题名+署名+止页」标准继续拆。  
4. 政治报告（p4—11）与《对时局宣言》优先全文转录。  
