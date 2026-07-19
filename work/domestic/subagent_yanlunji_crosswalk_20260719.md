# 《中國民主同盟言論集》× 1983 MMHIST 政治报告互证对照

执行角色：mingmeng-history-research 执行 agent（yanlunji crosswalk）  
访问日期：2026-07-19  
原则：同文 L2 双源可互校；**不等于** 1945 原件；**不填** 1946《民主同盟文獻》政治报告正文硬缺口；默认不 accept。

---

## 1. 本地 PDF 与指纹

| 项 | 值 |
|---|---|
| 主路径 | `data/domestic/sourcebooks/NLC511-027032016010761-42571_中国民主同盟言论集.pdf` |
| 工作副本 | `work/domestic/hard_gap_probe_20260719/NLC511_中国民主同盟言论集.pdf` |
| 页数 | 107（未加密，纯影像无文字层） |
| **SHA256** | `386faf360e73fd31e39d1f0a584877dddc76855f0d0be6157e01e06ac4234ef1` |
| 双副本一致性 | 主路径与工作副本 SHA256 **一致** |
| Commons | [NLC511-027032016010761-42571 中國民主同盟言論集.pdf](https://commons.wikimedia.org/wiki/File:NLC511-027032016010761-42571_%E4%B8%AD%E5%9C%8B%E6%B0%91%E4%B8%BB%E5%90%8C%E7%9B%9F%E8%A8%80%E8%AB%96%E9%9B%86.pdf) |
| 来源说明 | 時事研究社据一九四五年十月一日发刊之《民主星期刊》第一至第七期选编（PDF 第 3 页） |

对照汇编（1983）：

| 项 | 值 |
|---|---|
| 路径 | `data/domestic/sourcebooks/中国民主同盟历史文献_1941-1949_公开扫描.pdf` |
| SHA256 | `257bb7be70abe374be9864ec451b5a4a90e2442ae8c877b15f4e6bbb8bb30be3` |
| 政治报告候选 | `domestic:MMHIST:political-report-1945`（已 accepted / L2） |
| MMHIST 页界 | PDF **101—117**（扫描书内 **71—87**）；PDF118 起为大会宣言 |

印刷页码映射（言论集）：**印刷页 = PDF 页 − 5**（已用页脚「九／一四／二二／三〇」等复核）。

---

## 2. 关键页渲染

目录：`work/domestic/yanlunji_1945_pages/`

| 用途 | 文件 |
|---|---|
| 封面 | `page-001.png` |
| 说明页（《民主星期刊》选编说明） | `page-003.png` |
| 目录 | `page-004.png`、`page-005.png` |
| 宣言起 / 中 / 末 | `page-014.png` … `page-019.png` |
| 政治报告题名+编者 / 正文 / 末 | `page-019.png` … `page-035.png` |
| 下一文（章伯钧）边界 | `page-036.png` |

（另保留 hard_gap 探针页 `evidence_p27_start.png` 等，仅作历史探针，**页界以本轮更正为准**。）

---

## 3. 页界结论（言论集）

### 3.1 目录（PDF4）

| 条 | 题名 | 本轮页界 |
|---|---|---|
| （五） | 中國民主同盟臨時全國代表大會**宣言** | PDF **14—19**（印刷 9—14） |
| （六） | 中國民主同盟臨時全國代表大會**政治報告** | 题名 PDF **19**；正文 PDF **20—35**（印刷 15—30）；含题名计 **19—35** |
| — | 《纲领》 | **目录无独立条目**，本卷不拆纲领卡 |

### 3.2 政治报告（更正）

| 节点 | PDF | 印刷 | 目视 |
|---|---|---|---|
| 题名 +「編者」按语 | 19 | 14 | 宣言「謹此宣言」后同页出报告题名 |
| 正文起（对齐 MMHIST） | 20 | 15 | 「諸位到會代表……八年長期抗戰已經得到了最後的勝利」 |
| 旧误标「起页」 | 27 | 22 | 实为中段「結束十八年來一黨專政的黨治……」 |
| 正文末 | 35 | 30 | 同盟史回顾 +「把中國造成爲一個十足道地的民主國家」 |
| 下一文 | 36 | 31 | 章伯钧《民主與團結是分不開的》 |

**更正说明**：hard_gap 探针曾将 PDF27—35 记为政治报告全文；本轮据题名页、与 MMHIST PDF101 起文逐段对照，将起页前移至 **PDF19/20**，止页仍为 **PDF35**。

### 3.3 宣言（新建文件级）

| 节点 | PDF | 印刷 | 目视 |
|---|---|---|---|
| 题名 + 正文起 | 14 | 9 | 「中國民主同盟臨時全國代表大會宣言」 |
| 连续正文 | 15—18 | 10—13 | 条款式宣言体 |
| 收束 | 19 | 14 | 「謹此宣言」；同页转入政治报告题名 |

---

## 4. 与 1983 MMHIST 政治报告互证对照（同文 L2 双源）

| 锚点 | 言论集（NLC 选辑） | 1983 MMHIST | 判定 |
|---|---|---|---|
| 题名 | 臨時全國代表大會政治報告 | 同 | 同文题名 |
| 起文 | PDF20：「諸位到會代表……召集臨時全國代表會議……八年長期抗戰已經得到了最後的勝利」 | PDF101／书内71：同段（简体排印） | **对齐** |
| 国际环境段 | PDF20—21：一次大战威尔逊口号、民主与法西斯阵线 | PDF102／书内72：同段 | **对齐** |
| 中段 | PDF27 一带：「結束十八年來一黨專政的黨治……」及政治会议／联合政府等 | MMHIST 中段对应论述 | **同文展开**（言论集无独立标题页，分段靠正文） |
| 收束 | PDF35：民国三十年成立、改组扩大、独立性与中立性、「十足道地的民主國家」 | PDF117／书内87：同文收束 | **对齐** |
| 下一件 | PDF36 章伯钧个人文章 | PDF118 起为**大会宣言**（另一文件） | 汇编编排不同，不影响本篇同文判定 |

### 等级边界（强制）

```
言论集转载（1945 选辑）  +  1983 正式汇编
        \                    /
         \                  /
          →  同文 L2 双源互证
                    │
                    ├─ ≠ 1945 大会原始印本 / 原始记录
                    ├─ ≠ 《民主星期刊》原期封面+卷期影像（仍待追）
                    └─ ≠ 1946 总部《民主同盟文獻》所收政治报告正文
                         （硬缺口 2 仍 OPEN；见 subagent_hard_gap_probe）
```

宣言亦可与 `domestic:MMHIST:congress-declaration-1945`（PDF118—123，以「谨此宣言」收束）作同文 L2 双源对照；体例同上，**不升 L1**。

---

## 5. 候选与事件变更

| candidate_id | 动作 | review_status | L |
|---|---|---|---|
| `domestic:NLC:minmeng-yanlunji-1945-whole` | 更新 evidence_locator / review_note | **needs_human_review**（保持） | L2 |
| `domestic:NLC:minmeng-yanlunji-1945-congress-political-report` | **更正页界** 19—35；互证说明 | **needs_human_review**（保持） | L2 |
| `domestic:NLC:minmeng-yanlunji-1945-congress-declaration` | **新建** 文件级宣言 | **needs_human_review** | L2 |
| `domestic:MMHIST:political-report-1945` | 未改（已 accepted L2） | accepted | L2 |

- **是否改 accepted**：**否**（言论集三条均保持 `needs_human_review`；留给主会话）。
- **是否升 L1 原件**：**否**。
- **纲领拆分**：**否**（本卷目录无纲领）。
- **事件** `domestic-1945-first-congress`：新挂 3 条（whole + political-report + declaration）；`domestic_candidate_ids` 现 26。
- **source_registry** `domestic:source:nlc_minmeng_yanlunji_1945`：verification_note 已改为更正后页界。

---

## 6. 校验

```text
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
```

（执行结果见本轮终端输出；应 `failed: 0` / 无 dangling references。）

---

## 7. 返回摘要（给主控）

| 项 | 结果 |
|---|---|
| 新建 | **1** 条：`domestic:NLC:minmeng-yanlunji-1945-congress-declaration` |
| 政治报告页界（言论集） | PDF **19—35**（正文 **20—35**）；旧 27—35 已更正 |
| 宣言页界（言论集） | PDF **14—19** |
| MMHIST 政治报告页界 | PDF **101—117**（未改） |
| 是否 accept | **否**（默认留给主会话） |
| 是否升 L1 | **否** |
| 1946 文獻硬缺口 | **仍 OPEN**（明确不闭合） |
| 事件挂接 | 已挂 `domestic-1945-first-congress`（+3） |
| 关键页目录 | `work/domestic/yanlunji_1945_pages/` |
