# L1 文章级 accept 推荐清单（guangmingbao / minxian）

复核日期：2026-07-19  
复核角色：mingmeng-history-research 只读复核 agent（Grok）  
范围：`review_status=needs_human_review` ∧ `authenticity_level_proposed=L1` ∧ `candidate_id` 含 `guangmingbao` 或 `minxian`  
数据源：`data/domestic/candidates.jsonl`  
边界：**未改**任何 `review_status`；全部 `work/` 路径均已存在，**未改** `evidence_locator`。

---

## 0. 筛选结果

| 项 | 数 |
|---|---:|
| 命中（L1 + needs_human_review + guangmingbao/minxian） | **7** |
| 其中 guangmingbao | 7 |
| 其中 minxian | **0**（minxian 全部 L1 已为 `accepted`，整期 15 条） |
| 推荐 Codex 可直接 accept | **5** |
| 暂缓 | **2** |
| locator 指向缺失路径（已修正） | 0 |

说明：非 L1 的 guangmingbao NHR（L2/L3/L4 线索卡 5 条）不在本轮 accept 队列内。

---

## 1. 总表

| candidate_id | 题名 | 页界（登记 / 目视） | 本地路径是否存在 | 推荐 accept? | 理由 |
|---|---|---|---|---|---|
| `domestic:NLC:guangmingbao-1946-issue03-double-ten-task-article` | 為完成雙十節的歷史任務而奮鬥 | PDF 第1页（闭合；第2页他文） | 是 | **是** | 第1页中栏竖排大题与署名李平達清楚；第2页转入停战电文，止页闭合 |
| `domestic:NLC:guangmingbao-1946-issue03-ceasefire-telegram` | 民盟呼吁停战恢复和平电文 | PDF 第2页（闭合；第3页他文） | 是 | **是** | 第2页右侧大栏题名清楚；第3页为《关于和谈…》等，止页可闭合（原 uncertainty 已目视消解） |
| `domestic:NLC:guangmingbao-1948-1949-v1n1-current-tasks-zhangbojun` | 略論民主同盟當前的任務 | PDF 第5页（第4/6页边界） | 是 | **是** | 第5页大题《畧論…》署章伯鈞；第4页沈钧儒《成就》、第6页高集《駁胡適…》 |
| `domestic:NLC:guangmingbao-1948-1949-v1n1-refute-hu-shi-gaoji` | 駁胡適《國際形勢裏的兩個問題》 | PDF 第6—8页（第9页边界） | 是 | **是** | 第6页大题+高集；7—8连续正文；第9页郭沫若近影/他文 |
| `domestic:NLC:guangmingbao-1948-1949-v1n12-three-premises-li-xiangfu` | 三個前提與五項原則 | PDF 第3—5页（第2页边界） | 是 | **是** | 第3页大题+李相符；第2页《反對美國援蔣扶日》；第5页续文收束并见本期目录列本篇 |
| `domestic:NLC:guangmingbao-1947-12-congratulate-second-plenum-editorial` | 祝民盟二中全會 | 登记：新十二號 PDF 第2页；封面实物：新二十號 | 是 | **否** | 题名与第2页社论一致、第3页转入短評故**正文页界可闭**；但 **NLC404-01J000514-72818 封面印刷为「新二十號」+「民國三十六年一月八日」**，与候选 `document_date=1947-08-08` /「新十二號」冲突，不可带错期号日期直接 accept |
| `domestic:NLC:guangmingbao-1947-issue22-fight-for-human-rights-editorial` | 為爭取人權而奮鬥 | 登记：PDF 第2页；目视：至少第2—3页 | 是 | **否** | 题名不稳：封面目录近「為爭取基本的人權而奮鬥」、第2页大题「為爭取基本權利」、候选「為爭取人權而奮鬥」；且第3页页眉续「的人權而奮鬥」，第4页已转入鄧初民《再論中間路線問題》→ **止页应为 2—3，登记缺止页** |

---

## 2. 推荐 accept 明细（5）

### 2.1 `guangmingbao-1946-issue03-double-ten-task-article`

- 题名：為完成雙十節的歷史任務而奮鬥（副题：紀念雙十節第三十五週年；署 李平達）
- 日期：1946-10-08（新三號）
- 页界：PDF 第1页单页
- 路径：
  - `work/domestic/guangmingbao_1946_phase2_pages/issue03/page-01.png`（正文）
  - `work/domestic/guangmingbao_1946_phase2_pages/issue03/page-02.png`（边界）
- 整期 PDF：`data/domestic/press_scans/NLC404-01J000514-10424_光明報_1946年3期.pdf`
- accept 含义：记录级（题名/署名/日期/页界/本地入口）；**非**全文转录、非权利无条件确认

### 2.2 `guangmingbao-1946-issue03-ceasefire-telegram`

- 题名：民盟呼吁停戰恢復和平電文（候选简体「停战」= 报面繁体）
- 页界：PDF 第2页单页（本轮扩读第3页，确认为他文，止页闭合）
- 路径：`work/domestic/guangmingbao_1946_phase2_pages/issue03/page-02.png`
- 备注：同页另有短评栏及《评彭学沛…》；本卡仅登记电文栏

### 2.3 `guangmingbao-1948-1949-v1n1-current-tasks-zhangbojun`

- 题名：略論民主同盟當前的任務（报面「畧」= 略；署 章伯鈞）
- 日期：1948-03-01（第一卷第一期）
- 页界：PDF 第5页
- 路径：`work/domestic/guangmingbao_1948_1949/v1n1_pages/page-05.png`（边界 page-04 / page-06）

### 2.4 `guangmingbao-1948-1949-v1n1-refute-hu-shi-gaoji`

- 题名：駁胡適《國際形勢裏的兩個問題》（署 高集）
- 页界：PDF 第6—8页
- 路径：`work/domestic/guangmingbao_1948_1949/v1n1_pages/page-06.png` 至 `page-08.png`（边界 page-09）

### 2.5 `guangmingbao-1948-1949-v1n12-three-premises-li-xiangfu`

- 题名：三個前提與五項原則（署 李相符；副题涉新政协共同施政纲领）
- 日期：1948-08-16（第一卷第十二期）
- 页界：PDF 第3—5页
- 路径：`work/domestic/guangmingbao_1948_1949/v1n12_pages/page-03.png` 至 `page-05.png`（边界 page-02）
- 备注：第5页下半为目录栏，正文止点以目视续文收束为准

---

## 3. 暂缓明细（2）

### 3.1 `guangmingbao-1947-12-congratulate-second-plenum-editorial` — 期号/日期与封面冲突

| 字段 | 候选登记 | 封面/PDF 实物（NLC404-01J000514-72818） |
|---|---|---|
| 期号 | 新十二號（文件名「1947年12期」） | **新二十號** |
| 日期 | 1947-08-08 | **民國三十六年一月八日（1947-01-01 → 一月八日 = 1947-01-08）** |
| 社论题名 | 祝民盟二中全會 | 第2页中央竖排大题一致 |
| 页界 | PDF 第2页 | 第3页为短評栏 → 社论单页可闭 |

路径均存在：

- `work/domestic/continue_pages/1947_12/page-01.png` / `page-02.png` / `page-03.png`
- `data/domestic/press_scans/NLC404-01J000514-72818_光明報_1947年12期.pdf`（SHA256 与候选一致：`f61c0388…001dd`）

**暂缓原因（不可直接 accept）：** 记录级 accept 要求题名+日期+页界同时可靠；本条日期/期号与封面印刷冲突（可能源自 NLC/Commons 文件名「12期」误标，整期卡 `domestic:NLC:guangmingbao-1947-1947-12` 亦同源）。  
**建议下一步（不在本 agent 范围）：** 以封面实物改 `document_date` / 题注期号，并与另一份已登记「新二十號 / 1947-06-23」材料区分；改完后可再入 accept 队列。题名本身稳定。

### 3.2 `guangmingbao-1947-issue22-fight-for-human-rights-editorial` — 题名不稳 + 缺止页

| 来源 | 题名形态 |
|---|---|
| 候选 title | 為爭取人權而奮鬥 |
| 封面目录（竖排） | 近「為爭取基本的人權而奮鬥」（社論） |
| 第2页正文大题 | **為爭取基本權利** |
| 第3页页眉 | 的人權而奮鬥（续文） |
| 第4页 | 鄧初民《再論中間路線問題》（他文） |

路径均存在：`work/domestic/continue_pages/1947_22/page-01.png` … `page-04.png`；整期 PDF `…10483_…22期.pdf`。

**暂缓原因：**

1. **题名不稳**：候选 / 目录 / 正文大题三者不一致，accept 前须统一以正文大题或完整标题写回 `title`。  
2. **止页未闭**：登记仅 PDF 第2页；目视社论至少跨第2—3页，第4页他文 → 页界应改为 PDF 第2—3页并补 locator。

**建议下一步：** 改 title（建议以第2页大题「為爭取基本權利」为准，或补全完整题）、`evidence_locator` 扩至 page-03、uncertainty 改写后再 accept。

---

## 4. Codex 可直接执行清单（复制用）

```
ACCEPT (5):
- domestic:NLC:guangmingbao-1946-issue03-double-ten-task-article
- domestic:NLC:guangmingbao-1946-issue03-ceasefire-telegram
- domestic:NLC:guangmingbao-1948-1949-v1n1-current-tasks-zhangbojun
- domestic:NLC:guangmingbao-1948-1949-v1n1-refute-hu-shi-gaoji
- domestic:NLC:guangmingbao-1948-1949-v1n12-three-premises-li-xiangfu

HOLD (2):
- domestic:NLC:guangmingbao-1947-12-congratulate-second-plenum-editorial
  reason: cover=新二十號/1947-01-08 vs registered 新十二號/1947-08-08
- domestic:NLC:guangmingbao-1947-issue22-fight-for-human-rights-editorial
  reason: title unstable + end page at least p2–p3 not p2 only
```

accept 语义对齐既有整期/文章惯例：

- 仅记录级：题名、日期、署名（如有）、页界、本地原刊入口  
- 保持 `authenticity_level_accepted=L1`  
- **不**等于全文转录完成、权利无条件开放、或等同民盟正式文件原件  

---

## 5. 元数据 / locator 处置

| 动作 | 结果 |
|---|---|
| 修正缺失 work/ 路径 | 无需（7/7 主路径 + 边界页均存在） |
| 改 review_status | **未改**（默认只读） |
| 改 document_date / title | **未改**（HOLD 两条建议由后续 worker 写回后再 accept） |

---

## 6. 返回摘要

| 指标 | 值 |
|---|---|
| 推荐 accept | **5** |
| 暂缓 | **2** |
| 报告路径 | `work/domestic/subagent_l1_accept_queue_20260719.md` |
