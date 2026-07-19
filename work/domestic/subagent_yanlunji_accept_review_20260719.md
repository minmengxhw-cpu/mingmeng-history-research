# 《中國民主同盟言論集》抽检与 accept 推荐

执行角色：mingmeng-history-research 抽检 agent（yanlunji accept review）  
访问日期：2026-07-19  
范围：三条 NLC 言论集候选；**不自行改 `review_status=accepted`**。

---

## 1. 对象

| candidate_id | 既有 status | L | 本轮 |
|---|---|---|---|
| `domestic:NLC:minmeng-yanlunji-1945-congress-declaration` | needs_human_review | L2 | **推荐 accept** |
| `domestic:NLC:minmeng-yanlunji-1945-congress-political-report` | needs_human_review | L2 | **推荐 accept**（已更正止页） |
| `domestic:NLC:minmeng-yanlunji-1945-whole` | needs_human_review | L2 | **推荐 accept** |

---

## 2. PDF 与指纹

| 项 | 值 |
|---|---|
| 主路径 | `data/domestic/sourcebooks/NLC511-027032016010761-42571_中国民主同盟言论集.pdf` |
| 页数 | 107 |
| **SHA256（本轮实测）** | `386faf360e73fd31e39d1f0a584877dddc76855f0d0be6157e01e06ac4234ef1` |
| 与三条 `evidence_locator` | **一致** |
| 关键页 | `work/domestic/yanlunji_1945_pages/`（含 001–006、012–040） |
| 印刷页映射 | 印刷页 = PDF 页 − 5（脚码 九／一四／一五／三〇／三一 已核） |

说明页（`page-003.png`）：各文由一九四五年十月一日发刊之《民主星期刊》第一至第七期选编。封面（`page-001.png`）：時事研究社《中國民主同盟言論集》。

---

## 3. 页界复核（目视）

### 3.1 目录（PDF4 / `page-004.png`）

| 条 | 题名 | 目录起印 |
|---|---|---|
| （五） | 中國民主同盟臨時全國代表大會**宣言** | 九 |
| （六） | 中國民主同盟臨時全國代表大會**政治報告** | 一四 |
| — | 《纲领》 | **目录无独立条目**（不拆纲领卡） |

### 3.2 宣言 — PDF **14—19**（印刷 9—14）✓ 无误

| 节点 | PDF | 印刷 | 目视 |
|---|---|---|---|
| 题名 + 正文起 | 14 | 九 | 「中國民主同盟臨時全國代表大會宣言」；「八年長期抗戰已經得到勝利的結束……」 |
| 条款连续 | 15—18 | 10—13 | 经济/政治/国民大会等条款；`page-018` 印「一三」 |
| 收束 + 下一件题名 | 19 | 一四 | 上栏「謹此宣言。」；同页出《政治報告》题名与「編者」 |

### 3.3 政治报告 — PDF **19—36**（印刷 14—31）⚠ 止页已更正

| 节点 | PDF | 印刷 | 目视 |
|---|---|---|---|
| 题名 +「編者」 | 19 | 一四 | 宣言收束后同页 |
| 正文起 | 20 | 一五 | 「諸位到會代表……八年長期抗戰已經得到了最後的勝利」＝ MMHIST PDF101 |
| 旧误「起」 | 27 | 二二 | 中段，非起页（前轮已否） |
| **止（更正）** | **36 上栏** | **三一** | 自 PDF35 末「并不是不辨是非曲直」跨页至 36，以「一句話，就是把中國造成一個十足道地的民主國家。」收束 ＝ MMHIST PDF117／书内 87 |
| 下一文 | **36 同页** | 三一 | 章伯钧《民主與團結是分不開的》 |

**更正原因**：互证轮记止页 PDF35。本轮对照 `page-035`/`page-036` 与 MMHIST `page-117`：末段「独立与中立……乡愿……十足道地的民主国家」跨页，**全文单元应含 PDF36 上栏**。

### 3.4 整册 whole

整册 107 页公开扫描；关键页与 SHA256 充分，作为选辑卷宗级 L2 记录可 accept。

---

## 4. 题名 / 日期充分性

| ID | 题名 | 日期 | 说明 |
|---|---|---|---|
| declaration | 充分（目录+页内大标题） | `1945-10-16` day | 转载页无独立日期行；依 MMHIST / 通行大会系年；`uncertainty_note` 已写 |
| political-report | 充分 | `1945-10-11` day | 同上；MMHIST 起页有日期 1945-10-11 |
| whole | 充分（封面） | `1945-10` month | 说明页锚《民主星期刊》1945-10-01 起选编 |

等级边界不变：**L2 转载/选辑** ≠ 1945 原件 ≠ 1946《民主同盟文獻》政治报告正文硬缺口（仍 OPEN）。

---

## 5. 本轮是否改数据

| 动作 | 内容 |
|---|---|
| **是（最小修正）** | `political-report` 止页 **35→36**；更新 `catalog_reference` / `evidence_note` / `evidence_locator` / `review_note` |
| **是（收紧）** | `declaration` catalog/locator 写明 14—19；三条 `review_note` 写入抽检结论 |
| **是** | `source_registry` `domestic:source:nlc_minmeng_yanlunji_1945` verification_note 同步止页 |
| **否** | **未** 将任一条 `review_status` 改为 `accepted` |
| **否** | 未升 L1；未改 MMHIST 已 accepted 条；未拆纲领 |

---

## 6. 主会话 accept 清单（请主会话执行）

推荐 **L2 记录级 accept**（字段由主会话按 schema 补 `check_outcome` / `authenticity_level_accepted` / `relevance_grade_accepted` / `reviewed_at` / `reviewed_by`）：

1. `domestic:NLC:minmeng-yanlunji-1945-congress-declaration`
2. `domestic:NLC:minmeng-yanlunji-1945-congress-political-report`
3. `domestic:NLC:minmeng-yanlunji-1945-whole`

建议 accepted 等级：

- `authenticity_level_accepted`: **L2**
- `relevance_grade_accepted`: declaration / political-report → **core**；whole → **related**
- `check_outcome`: **pass**

---

## 7. 校验

```text
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
# {"records": 406, "failed": 0, "passed": 406}

python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
# missing_candidate_references: [] ；pair_status_counts 正常
```

---

## 8. 返回摘要（给主控）

| 项 | 结果 |
|---|---|
| 推荐 accept | **3** 条（declaration / political-report / whole） |
| 是否改 jsonl | **是**（政治报告止页 35→36 + 文案同步；未改 accepted） |
| 宣言页界 | PDF **14—19**（确认） |
| 政治报告页界 | PDF **19—36**（体文 20—36 上栏；**止页更正**） |
| 下一文边界 | PDF **36** 章伯钧 |
| SHA256 | 与 locator **一致** |
| validate_candidates | **failed: 0** |
| 升 L1 / 闭合 1946 硬缺口 | **否** |
