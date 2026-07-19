# 页界/题名目视抽检报告 — 72818 / guangmingbao-1947-12-*（2026-07-19）

- **执行**：mingmeng-history-research 抽检 agent（grok）
- **范围**：`domestic:NLC:guangmingbao-1947-12-*` 文章级候选 **全量 9 条**
- **排除（已 accepted）**：`domestic:NLC:guangmingbao-1947-12-congratulate-second-plenum-editorial`（社论《祝民盟二中全會》）
- **原刊**：`NLC404-01J000514-72818`（NLC 文件名误标「1947年12期」）
- **页图**：`work/domestic/continue_pages/1947_12/page-01.png` … `page-16.png`
- **关键约束（本轮强制）**：封面为 **新二十號** + **民國三十六年一月八日** → `document_date` 必须是 **1947-01-08**（不是十二號 / 不是 08-08）
- **不自动 accepted**

## 0. 汇总

| 项 | 数 |
|----|---:|
| 抽检 N | **9** |
| 通过（页界/题名） | **9** |
| 问题（明确错误，需修数据） | **1 类**（catalog 仍写「新十二號」；胡愈之条 evidence 残留「8月刊」措辞） |
| 是否改了数据 | **是**（9 条最小修正；**未**改 `review_status`） |
| validate_candidates | **405/405** passed |
| 推荐 accept | **9** 条（见 §5；主会话执行，本 agent 不 auto-accept） |

### 封面复核

| 项 | 目视 |
|----|------|
| 期号 | 竖排 **號 二 十 新** → **新二十號**（非「十二」） |
| 出版日 | **版出日八 月 一 年六十三** → 民國三十六年一月八日 → **1947-01-08** |
| 内页刊头 | page-05/07/09/11/13/15 等可见 **• 號二十新 •** / **新二十號** |
| 与 NLC 文件名 | 文件名「1947年12期」为 **误标**；candidate_id 前缀 `1947-12` 仅作历史 id，**不以 id 当实物期号** |
| 与 10459 | 另文件 `NLC404-01J000514-10459`（另登 1947-06-23 新二十號）与 72818 **不同卷**（既有 SHA 说明保留） |

---

## 1. 通过列表（9）

全部 `document_date=1947-01-08` 与封面一致；页界对照 `continue_pages/1947_12` 目视。

| # | candidate_id | 登记题名 / 署名 | 页界 | 目视结论 |
|---|--------------|-----------------|------|----------|
| 1 | `…12-si-tan-guo-shi` | 肆談國事 / 陳此生 | PDF 4—6 | **通过**。p4 竖大题「肆談國事」+陳此生；「一、詐風不止…」起；p5 续（二）（三）；p6「四、兩種民主和和平」与黄药眠文**共页**，止于 6 合理 |
| 2 | `…12-respond-anti-us-military` | 響應反對美軍暴行運動 / 黃藥眠 | PDF 6—7 | **通过**。p6 大题+黃藥眠；p7 无新篇大题、正文续至「歡迎批評／歡迎定閱」；p8 起胡愈之 → 止于 7 合理 |
| 3 | `…12-second-plenum-domestic-situation` | 民盟二中全會與國內局勢 / 胡愈之 | PDF 8—9 | **通过**。p8 右栏大题+胡愈之+「轉載」；同页左栏「民主運動在南洋」短讯**未**并入；p9 续政论、无本篇新大题；p10 转王健访谈 |
| 4 | `…12-interview-shen-junru` | 訪問沈鈞儒先生 / 王健 | PDF 10—11 | **通过**。p10 大题+王健；访谈体（記者／沈）；p11 右栏续访谈，左栏转入声明 → 共页止于 11 合理 |
| 5 | `…12-statement-one-sided-constitution` | 對於片面憲法民盟發表聲明 / 中国民主同盟 | PDF 11 | **通过**。p11 左栏大题+「民主文獻」栏花；与访问沈钧儒文共页但栏界可分；登记仅声明栏正确 |
| 6 | `…12-qingmo-democracy-two-paths` | 清末民主運動的兩條路線 / 晨曦 | PDF 12—13 | **通过**。p12 大题+副题「—民主運動史話之二」+晨曦；p13 无新篇大题、史话续；p14 转黎洪 → 止于 13 合理 |
| 7 | `…12-oppose-us-atrocities-shanghai` | 反對美軍暴行 / 黎洪 | PDF 14—15 | **通过**。p14「反對美軍暴行！」+「上海通訊」+黎洪；p14–15 下栏为民主人士意见辑（另条）；p16 左栏叙事相近但右栏已是学生致杜鲁门书 → **止于 15 保守正确** |
| 8 | `…12-shanghai-democrats-on-us-atrocities` | 滬民主人士對美軍暴行意見 / 《光明報》辑 | PDF 14—15 | **通过**。p14 下框李濟深/郭沫若/沈鈞儒/鮮英等；p15 下框续「滬民主人士對美軍暴行意見」+馬敘倫/張申府/沈志遠/劉王立明；与黎洪栏可分 |
| 9 | `…12-students-letter-to-truman` | 學生致杜魯門總統書 / 上海學生抗議美軍暴行聯合會 | PDF 16 | **通过**。p16 右栏大题+「民主文獻」+联合會署名；文末「三十六年一月一日 上海市」可辨；左栏他文不并入 |

### 封面目录对照（导航，非正文页界）

| 目录题名 | 对应 candidate |
|----------|----------------|
| 肆談國事 陳此生 | #1 |
| 響應反對美軍暴行運動 黃藥眠 | #2 |
| 民盟二中全會與國內局勢 胡愈之 | #3 |
| 民主運動在南洋 | **未拆**（短讯栏，既有策略保留） |
| 清末民主運動的兩條路線 晨曦 | #6 |
| 訪問沈鈞儒先生 王健 | #4 |
| 反對美軍暴行（上海通訊） 黎洪 | #7 |
| 滬民主人士對美軍暴行意見 | #8 |
| 文件：對片面憲法民盟發表聲明 | #5 |
| 上海學生致杜魯門總統書 | #9 |
| （目录未单列）社論《祝民盟二中全會》 | 已 accepted，本轮排除 |

---

## 2. 问题列表（已最小修改）

### P1. catalog / 残留措辞仍写「新十二號」或「8月刊」（元数据，非页界）

- **事实**：封面与内页刊头均为 **新二十號 / 1947-01-08**；`document_date` 九条均已是 `1947-01-08`。
- **错误残留**：
  - 9 条 `catalog_reference` 仍写「《光明報》**新十二號**PDF…」
  - `…second-plenum-domestic-situation` 的 `evidence_note` 仍有「本稿为**8月刊**转载政论」——与实物一月号冲突
- **处置（最小修改 jsonl）**：
  - 9 条 `catalog_reference`：`新十二號` → **`新二十號`**
  - 胡愈之条 `evidence_note`：`本稿为8月刊转载政论` → **`本稿为本期（1947-01-08）转载政论`**
  - 9 条 `review_note` 追加抽检通过说明
  - **未改** `review_status`（仍为 `needs_human_review`）
  - **未改** `candidate_id`（前缀 `1947-12` 保留以免断链；实物期号以 catalog/date 为准）
  - **未动** 已 accepted 社论条（不在本轮范围）

---

## 3. 非阻断观察（建议，未另改数据）

1. **多文共页**（p6 陈/黄；p11 王/声明；p14–15 黎/意见辑；p16 通讯续/学生书）：起止页可接受；正式 accepted 后栏切/全文转录另核。
2. **黎洪是否延至 p16 左栏**：叙事口吻相近，但同页右栏已是《學生致杜魯門總統書》；现止于 p15 正确，左栏归属可另轮复审。
3. **黎洪正文题名带叹号**「反對美軍暴行！」；目录与登记无叹号——**以登记无叹号可接受**（不构成题名错误）。
4. **「民主運動在南洋」** 仍未单独立条（短讯+与胡文共页），符合既有「页界不充分不拆」策略。
5. **p3《短評》** 多则并列，本池未建文；正确。
6. 已 accepted 社论条 `catalog_reference` 仍可能写「新十二號」——**建议主会话顺手改**，不在本 agent 范围。

---

## 4. 数据修改清单

| candidate_id | 字段 | 旧 → 新 |
|--------------|------|---------|
| 本池 9 条全部 | `catalog_reference` | 新十二號 → **新二十號** |
| `…second-plenum-domestic-situation` | `evidence_note` | 「8月刊转载」→ **「本期（1947-01-08）转载」** |
| 本池 9 条全部 | `review_note` | 追加 subagent_72818 抽检说明 |
| 本池 9 条全部 | `review_status` | **未改**（仍 `needs_human_review`） |

校验：

```text
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
{"records": 405, "failed": 0, "passed": 405}

python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
{"candidate_ids": 405, "events": 9, "missing_candidate_references": [],
 "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}
```

---

## 5. 推荐 accept IDs（主会话执行；本 agent 不写入 accepted）

页界/题名/日期均已对齐封面 **新二十號 1947-01-08**，建议主会话批量 accept：

1. `domestic:NLC:guangmingbao-1947-12-si-tan-guo-shi`
2. `domestic:NLC:guangmingbao-1947-12-respond-anti-us-military`
3. `domestic:NLC:guangmingbao-1947-12-second-plenum-domestic-situation`
4. `domestic:NLC:guangmingbao-1947-12-interview-shen-junru`
5. `domestic:NLC:guangmingbao-1947-12-statement-one-sided-constitution`
6. `domestic:NLC:guangmingbao-1947-12-qingmo-democracy-two-paths`
7. `domestic:NLC:guangmingbao-1947-12-oppose-us-atrocities-shanghai`
8. `domestic:NLC:guangmingbao-1947-12-shanghai-democrats-on-us-atrocities`
9. `domestic:NLC:guangmingbao-1947-12-students-letter-to-truman`

说明：accepted 只表示记录身份与页级入口；不表示全文转录或复制权利完成。共页栏界与 p16 左栏归属可在 accept 后作为 uncertainty 保留。

---

## 6. 返回值（给调度）

| 指标 | 值 |
|------|----|
| 抽检 N | **9** |
| 通过数 | **9**（页界/题名） |
| 问题数 | **1 类元数据残留**（已修：catalog 期号 + 胡文 8月刊措辞） |
| 是否改了数据 | **是**（9 条最小修正；**未** auto-accept） |
| 推荐 accept 数 | **9** |
| 报告路径 | `work/domestic/subagent_72818_articles_sample_20260719.md` |
