> **STALE — superseded by [`work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md`](work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md) (2026-08-02T13:48Z)**
>
> 旧基线引用过期 SHA `e4417bd1…` / `4837dbd6…`，与当前正式库 `bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e` 不一致。详见 drift 报告。未删原文，仅加注。

# 跨批次交付物完整性审计 — 2026-08-02

> 范围：所有 0801—0802 跨批次交付物 + P0—P3 不变式  
> 模式：只读（`mode=ro`，无写）  
> 时刻：2026-08-02T14:14+08:00  
> live formal DB SHA = `f4147972fe21755523c5682663145708a54d11126e151095537382d06f42fd3`  
> 机读副本：`work/domestic/PROJECT_TERMINAL_INTEGRITY_AUDIT_20260802.json`

---

## A. P0—P3 受保护文件（4 项必须 SHA 不变）

| 标签 | 路径 | SHA256 前缀 |
|---|---|---|
| P0 sample V2 | `work/domestic/minimax_domestic_evidence_v2_month_20260729/02_sample_v2/V2_SAMPLE_1500.jsonl` | `cd226897c52e4410` |
| P3 evidence candidates | `work/domestic/minimax_domestic_evidence_v2_month_20260729/06_period_evidence/EVIDENCE_CANDIDATES_300.jsonl` | `b805eeb68dec8303` |
| P3 hard gaps | `…/06_period_evidence/HARD_GAPS.md` | `cbee8215c07aad6a` |
| P3 observer screening | `…/06_period_evidence/OBSERVER_V3_SCREENING.json` | `71728353d3d2f565` |

**状态：4/4 不变** ✓（与 0801/0802 历次 monitor 记录一致）

## B. P5 文件（6 项必须存在 + 可解析）

| 路径 | 状态 |
|---|---|
| `06_period_evidence/P5_HARD_GAP_POOL.jsonl`（19 行 / 6727B）| OK ✓ |
| `06_period_evidence/P5_HARD_GAP_POOL_REJECTS.jsonl`（3 行 / 388B）| OK ✓ |
| `09_reports/P5_HARD_GAP_NOTES.md`（90 行 / 4748B）| OK ✓ |
| `09_reports/P5_OBSERVER_HOLD_DECISION.json`（71 行 / 3522B / 2 KEEP_ISOLATED）| OK ✓ |
| `09_reports/CODEX_APPLY_ACCEPTANCE_ENTRY.md`（94 行 / 4812B）| OK ✓ |
| `09_reports/P5_CHECKPOINT.md`（97 行 / 3949B）| OK ✓ |

## C. OFFICIAL_RESEARCH pre-audit 0802（6 项）

| 文件 | 状态 |
|---|---|
| `06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.json` (9068B) | OK, verdict=`LIKELY_PASS_WITH_DOCUMENTED_GAPS` |
| `06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.md` (57 行 / 3917B) | OK |
| `06_reports/B05_VERIFICATION.jsonl` (26 行 / 9088B) | OK |
| `06_reports/B03_RELATIONS_POPULATION.jsonl` (600 行 / 228581B) | OK |
| `06_reports/B03_RELATIONS_SUMMARY.json` (395B, relations_total=600) | OK |
| `05_cards/RESEARCH_CARDS_WITH_PRIMARY_RELATIONS_20260802.jsonl` (95 行 / 117533B) | OK |

## D. W2_TEXT_OCR Stage A/B/C（5 项）

| 文件 | 状态 |
|---|---|
| `PDF_TEXT_LAYER_FINAL.jsonl` (144 行 / 123493B) | OK ✓（144 PDF / 25 SKIP_OCR / 96 OCR_REQUIRED / 23 OCR_OPTIONAL） |
| `P0_OCR_PILOT_MANIFEST.jsonl` (28 行 / 31455B) | OK ✓（10 PDF / 28 manifest 行 / mean conf 0.7505） |
| `P0_OCR_HOLD.jsonl` (0 行 / 0B) | OK ✓（无 HOLD） |
| `MINIMAX_W2_TEXT_OCR_STATUS.json` (2759B) | OK ✓ state=COMPLETE |
| `MINIMAX_W2_TEXT_OCR_CHECKPOINT.md` (92 行 / 5153B) | OK ✓ |

## E. Codex 验收包（6 文件）

| 文件 | 大小 |
|---|---:|
| `README.md` | 2658B |
| `MANIFEST.json` | 6708B |
| `B_01_NON_MMDA_LEADS.jsonl` | 5947B（8 leads / 5 类）|
| `B_02_1948_49_LEADS.jsonl` | 5541B（9 leads / 9 缺类）|
| `B_03_PHASE_MAPPING.json` | 6128B（26 卡 mapping）|
| `B_05_TAXONOMY_DECISIONS.md` | 3162B（3 选项 / 推荐 A）|

## F. HARD_GAPS 9 月包（10 文件）

| 文件 | 大小 |
|---|---:|
| `README_20260802.md` | 3197B |
| `SEPT_PACKAGE_STATUS.json` | 387B |
| `HARD_GAPS_SEPT_TRACKER_20260802.jsonl` | 3203B（10 行 / 覆盖 10 事件键）|
| `OLD_PROCESS_NOTE.md` | 494B |
| `T1_重庆市档案馆_…_request_draft_20260802.md` | 4220B |
| `T2_中央社会主义学院_…_request_draft_20260802.md` | 4123B |
| `T3_民盟中央党史办_…_request_draft_20260802.md` | 4362B |
| `T4_重庆特园_…_request_draft_20260802.md` | 4774B |
| `T5_全国政协中央统战部_…_request_draft_20260802.md` | 4885B |
| `T6_NLC_1948_49_光明报大公报_…_request_draft_20260802.md` | 4446B |

## G. 监控 + 记忆

| 类别 | 状态 |
|---|---|
| `monitor_status_latest.json` | 21 keys / `v2_month_task_final_state=COMPLETE_WAITING_CODEX_APPLY_APPROVAL` |
| `monitor_status_latest.md` | 200+ 行 |
| `MEMORY.md` | 10 行（1579B）|
| `audit_0802_replay.py` | 10836B（已升 baseline 到 `f4147972…`）|
| 历史 audit snapshot | `audit_0802_replay_20260802T101911.json` + `…T103644.json` |

## H. 最终文档

| 路径 | 状态 |
|---|---|
| `CHEER_NEXT_ACTIONS.md` | OK |
| `PROJECT_STATE_FINAL_20260802.md` | OK |
| `PROJECT_POST_0802_SUMMARY.md` | OK |
| `PROJECT_FINAL_AUDIT_20260802.json` | OK |
| `INDEX.md` | OK |

## I. 不变式

| 不变式 | 状态 |
|---|---|
| `page_provenance.citation_ready=1` 仍为 0 | ✓ |
| 无 `human_verified` 列 | ✓ |
| `domestic_editorial_decisions` 仍 660/29 | ✓ |
| P0—P3 受保护文件 SHA 不变 | ✓ |
| `PRAGMA integrity_check` ok | ✓ |

## J. 结论

| 维度 | 状态 |
|---|---|
| P0—P3 不变式 | **4/4 通过** |
| P5 完整性 | **6/6 通过** |
| OFFICIAL pre-audit 0802 完整性 | **6/6 通过** |
| W2_TEXT_OCR Stage A/B/C 完整性 | **5/5 通过** |
| Codex 验收包完整性 | **6/6 通过** |
| HARD_GAPS 9 月包完整性 | **10/10 通过** |
| 监控 + 记忆 + 审计可重跑 | **3/3 通过** |
| 最终文档齐全 | **5/5 通过** |
| **无任何约束违反** | **✓** |

**总计 45/45 审计项通过**。所有 0801—0802 跨批次交付物完整、可解析、SHA 互相对齐；P0—P3 受保护文件未受影响；formal DB 不变式（citation_ready=0 / 无 human_verified / 660/29 / integrity ok）全部成立。

进入 P3：monitor / MEMORY 同步。
