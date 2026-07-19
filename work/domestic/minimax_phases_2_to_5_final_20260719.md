# 阶段2—5 连续执行总报告（统一审核用）

完成日期：2026-07-19（Asia/Shanghai）  
执行方：Grok  
审核方：待 Codex / 人工统一审核（按用户「先继续，全部做完后一起审核」）

前置已完成：阶段0审计、阶段1（R1/R2 + 组织规程 L2 + 1941—1945 原件追索负向）

---

## 一、最终基线（阶段5实测）

| 指标 | 阶段1结束 | 阶段5结束 | 变化 |
|---|---:|---:|---|
| 来源 | 87 | **87** | 0 |
| 候选 | 338 | **344** | +6 |
| accepted | 152 | **152** | 0（未擅自接受） |
| needs_human_review | 186 | **192** | +6 |
| 事件 | 9 | 9 | 悬空引用 0 |
| L1 / L2 / L3 / L4 / LX | 242/47/7/38/4 | **246/47/8/39/4** | +4 L1, +1 L3, +1 L4 |

### 校验命令全部通过

```text
validate_candidates: {"records": 344, "failed": 0, "passed": 344}
validate_event_coverage: missing_candidate_references: []
ingest_domestic: sources 87, candidates 344, pending 192, decisions 344
audit_readiness: missing_required 0, missing_paths 0, accepted 152
git diff --check: clean
```

---

## 二、本轮新增候选一览（6）

| ID | 阶段 | 等级 | 状态 | 说明 |
|---|---|---|---|---|
| `domestic:NLC:guangmingbao-1946-issue05-beijing-comrades-editorial` | 2 | L1 | needs_human_review | 為赴京的同盟同志們！ |
| `domestic:NLC:guangmingbao-1946-issue9-anti-civil-war-conscription-editorial` | 2 | L1 | needs_human_review | 反對內戰，反對徵兵！ |
| `domestic:NLC:guangmingbao-1946-issue10-guangdong-kmt-protest-editorial` | 2 | L1 | needs_human_review | 向廣東國民黨當局抗議 |
| `domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap` | 2 | L3 | needs_human_review | 目录有政治报告、正文错位硬缺口 |
| `domestic:SHPRESS:zhanglan-shidai-ribao-1947-11-07-lead` | 3 | L4 | needs_human_review | 张澜谈话出处线索（非总部公告） |
| `domestic:NLC:guangmingbao-1948-1949-v2n12-taiwan-liberation` | 4 | L1 | needs_human_review | 談台灣解放問題 |

### 修改（非新增）

- 1949 v2n1 / v2n12 两篇既有文章：补页界与本地整期转图路径  
- 1947 三项核心既有卡：追加阶段3负向检索 `review_note`  
- （阶段1已改）成立宣言第38页边界；政治报告 page-111—116；组织规程新卡

---

## 三、分阶段结论

### 阶段2 — 1946

- 文章级：3 篇首面社论可入库为 L1 待审  
- 新三/新六：题名不清，**不猜题**，保持整期  
- **硬确认**：1946《民主同盟文獻》目录「代表大会政治报告」印刷页49处实为纲领正文 → L3 缺口卡  

### 阶段3 — 1947 三项

| # | 目标 | 结果 |
|---|---|---|
| 1 | 内政部公函/公报原页 | 负向；2964号负向仍有效 |
| 2 | 总部解散公告独立印本 | 负向；L2汇编+报纸互证 |
| 3 | 北平《新民报》11-04原版 | 负向；观察重刊≠原版 |

### 阶段4 — 1948—1949

- 四期锚点整期仍 accepted  
- 笔谈页界：PDF第2页；和平态度：PDF第2—3页  
- 新拆台湾解放问题；全时间轴不缩成1947  

### 阶段5

- 校验、幂等入库、收口审计已刷新  
- 文档：`阶段性Review`、`external_search_log`、`收口审计_20260719` 已更新  

---

## 四、分报告索引

| 文件 |
|---|
| `work/domestic/minimax_phase0_audit_20260719.md` |
| `work/domestic/minimax_phase1_1941_1945_pursuit_20260719.md` |
| `work/domestic/minimax_phase2_1946_articles_20260719.md` |
| `work/domestic/minimax_phase3_1947_core_gaps_20260719.md` |
| `work/domestic/minimax_phase4_1948_1949_20260719.md` |
| 本文件 |

---

## 五、请 Codex 统一审核的检查清单

1. **证据边界**：有无把汇编/OCR/目录/盟史网页误升为原件？  
2. **重复**：6 条新 ID 是否与旧卡近似重复？  
3. **页界**：1946 三篇社论是否同意记录级接受？1949 两篇页界是否充分？  
4. **硬缺口卡**：政治报告 L3 目录错位表述是否准确？  
5. **1947 分项**：三项是否仍清楚分开、负向是否可复查？  
6. **组织规程**（阶段1）：`domestic:MMHIST:organization-regulation-1945` 是否可 L2 记录级 accept？  
7. **政治报告**（1983）：页图 101—117 齐后是否可 L2 accept（仍非原件）？  

---

## 六、仍未闭环的硬缺口（全项目）

1. 1941-10-10/16《光明報》原刊（港大缩微待调）  
2. 1944 全国代表会议原始文件  
3. 1945 大会政治报告/组织规程/宣言/纲领**同期印本**  
4. 1946 汇编内政治报告**正文**  
5. 1947-10-27 内政部公函或公报原页  
6. 1947-11-06 总部解散公告独立印本  
7. 1947-11-04 北平《新民报》原版  

**结论：** 阶段0—5 执行链路已跑完并可复查；资料库「未完成原件闭环」，进入审核队列而非结题。
