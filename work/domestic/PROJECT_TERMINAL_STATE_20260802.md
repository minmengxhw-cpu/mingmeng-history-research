> **STALE — superseded by [`work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md`](work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md) (2026-08-02T13:48Z)**
>
> 旧基线引用过期 SHA `e4417bd1…` / `4837dbd6…`，与当前正式库 `bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e` 不一致。详见 drift 报告。未删原文，仅加注。

# PROJECT TERMINAL STATE — 2026-08-02

> 单一来源项目终态。给 cheer / Codex / 未来 agent 用的**5 分钟速通**。  
> 生成：2026-08-02T14:14+08:00  
> 依据：`PROJECT_TERMINAL_DB_RECONCILIATION_20260802.md` + `PROJECT_TERMINAL_INTEGRITY_AUDIT_20260802.md`  
> 状态：**项目处于"等 Codex 验收 + 等 cheer 发送 + 等外部回函"的可交付状态**

---

## 0. 一句话状态

**V2 一月长任务** = `COMPLETE_WAITING_CODEX_APPLY_APPROVAL`  
**OFFICIAL_RESEARCH pre-audit 0802** = `LIKELY_PASS_WITH_DOCUMENTED_GAPS`  
**live formal DB SHA** = `f4147972…`（supervisor STATE / audit replay / 实际文件 三方一致）  
**P0—P3 不变式** = 4/4 通过（citation_ready=0 / 无 human_verified / 660/29 / integrity ok）  
**8 个交付包** = 45/45 项审计通过

---

## 1. 三个主轴终态

| 主轴 | 终态 | 关键产物 | 关键数字 |
|---|---|---|---|
| **V2 miniMax 一月长任务** | `COMPLETE_WAITING_CODEX_APPLY_APPROVAL` | P0—P5 全部 6 阶段 + apply 入口 | 缺口 (34,20)→(27,15) / 12 新候选 / 0 翻转 |
| **OFFICIAL_RESEARCH miniMax 0730** | `LIKELY_PASS_WITH_DOCUMENTED_GAPS` | pre-audit 0802 + Codex 验收包 | 5 blockers 1 RESOLVED + 1 substantially + 3 documented |
| **Grok 多源交叉** | `NOT_FULL_HANDOFF_LOOP` | PROVENANCE_GAP_CLOSEOUT | 182 → 49 MAPPED / 133 HOLD / 0 downloads |

## 2. V2 一月长任务时序

| 阶段 | 终态 | 关键数字 | 关键产物路径 |
|---|---|---|---|
| P0 | ✅ ACCEPTED | 1500 sample / 480 blacklist | `minimax_domestic_evidence_v2_month_20260729/02_sample_v2/` |
| P1 | ✅ DONE | MACHINE_PASS=944 / NEEDS_VARIANT=556 | OCR manifests |
| P2 | ✅ DONE | 556 变体 / 72 问题页收口 | `02_ocr_variants/` |
| P3 | ✅ CONDITIONAL_PASS | 300 高价值候选 / 1941-43 缺 34 / 1948-49 缺 20 | `06_period_evidence/EVIDENCE_CANDIDATES_300.jsonl` + `HARD_GAPS.md` + `OBSERVER_V3_SCREENING.json` |
| P4 | ✅ DRYRUN_COMPLETE | 11 文件 / would_change=1800 | `08_sqlite_dryrun/` + `09_reports/MONTH_FINAL_*` |
| P5 | ✅ COMPLETE | 6 文件 / 缺口改善 (34,20)→(27,15) | `06_period_evidence/P5_HARD_GAP_POOL.jsonl` + `09_reports/P5_*` |
| P4 apply | 🔒 待 Codex 独立窗口 | apply 入口就绪 | `08_sqlite_dryrun/apply_v2_after_codex_approval.py` |

**应用 apply 命令**（Codex 跑时使用）：
```bash
python3 work/domestic/minimax_domestic_evidence_v2_month_20260729/08_sqlite_dryrun/apply_v2_after_codex_approval.py \
  --apply --codex-approval-marker "<CODEX 下发的 marker>"
```

## 3. OFFICIAL_RESEARCH 0730 长任务

| 阶段 | 终态 | 关键数字 |
|---|---|---|
| baseline | ✅ | 144 OFFICIAL_RETROSPECTIVE |
| records | ✅ | 157 高质量 / 89/157 = 56.7% 中央+群言 |
| acquisition | ⚠️ | 26 acquired_ok + 50 HOLD / 39 结构性不可解 |
| text/ocr | ⚠️ | 26 fulltext + 0 OCR / 300 页预算未启用 |
| cards | ✅ | 157 cards / 6 类分级 |
| pre-audit 0801 | — | LIKELY_CONDITIONAL / 5 blockers |
| pre-audit 0802 | **LIKELY_PASS_WITH_DOCUMENTED_GAPS** | 1 RESOLVED + 1 substantially + 3 documented |
| Codex 验收 | ⏸ pending Codex 配额 | 4 cheer 待办 |

**5 blockers 状态（0802）**：
- **B-04 RESOLVED** ✓（elapsed_hours / batch_window 字段已补）
- B-03 SUBSTANTIALLY_ADDRESSED（67/95 卡片 / 600 relations / 28 skipped）
- B-01 documented（5 类缺口 + 14 gap 未填 + 39 结构性不可解）
- B-02 documented（1948-49 OSE = 4 / 9 缺类已 audit）
- B-05 medium / needs taxonomy（14 verified_absent + 12 conflicts）

**4 个 cheer 待办**（在 `OFFICIAL_RESEARCH_CODEX_PACKET_20260802/`）：
- B-01 leads（5 类非 MMDA）
- B-02 categories（9 类 1948-49）
- B-03 phase mapping（28 skipped 卡片）
- B-05 taxonomy（12 conflicts 决策）

## 4. 多源交叉 / 其他轨道

| 轨道 | 终态 | 关键数字 |
|---|---|---|
| Grok GAP_WAVE2 | ✅ COMPLETE | NOT_FULL_HANDOFF_LOOP |
| Grok PROVENANCE_GAP_CLOSEOUT | ✅ COMPLETE | 49 MAPPED / 133 HOLD / 0 downloads |
| MiniMax AUTONOMOUS T68 | ✅ COMPLETE | wall cleared / READY_NEXT_CYCLE |
| MiniMax AUTONOMOUS T69+ | ⏸ pending Token Plan 配额 | restart_blockers=Token Plan |
| MULTI_AGENT_FINAL W1—W4 + reconciliation | ✅ COMPLETE | 1642 unique / 332 relations / 99 crosswalk |
| W2_TEXT_OCR Stage A/B/C | ✅ COMPLETE | 144 PDF / 10 OCR / mean conf 0.7505 |
| HARD_GAPS_SEPT_PACKAGE | ✅ READY_TO_SEND | 6 templates / 10 事件键覆盖 |

## 5. Cheer-only 接力（3 个包）

### 8 月包（2 模板）
- `CHEER_ONLY_AUG2026_KICKOFF_20260801.md`
- `hku_guangmingbao_1941_request_draft_20260801.md`（B1 HKU）
- `shac_1354_request_draft_20260801.md`（B5/B6 SHAC 同函）

### 9 月包（6 模板）`HARD_GAPS_SEPT_PACKAGE_20260802/`
- T1 重庆市档案馆 / T2 中央社会主义学院 / T3 民盟中央党史办
- T4 重庆特园 / T5 全国政协+中央统战部 / T6 NLC 1948-49
- **Top 3 优先**：T6（3 周）→ T2（双覆盖）→ T1

### Codex 验收包（5 文件）`OFFICIAL_RESEARCH_CODEX_PACKET_20260802/`
- 4 blocker leads / mapping / decisions

## 6. Formal DB SHA 真相

**误解纠正**：formal DB SHA 不是"冻结值"，是"live 值"。

| 维度 | 真实情况 |
|---|---|
| 监督器 | PID 72955 / 32605 跑着，**只检测不拦** |
| app.py | PID 40248 跑着，**合法写库** |
| 0801—0802 drift 次数 | **8 次**（07-29 `1292c7e0…` → 0802 14:07 `f4147972…`）|
| 每次 drift 是否有 `.bak` | **是**（8 个 `.bak` 全保留）|
| subagent attribution | **0**（无任何 subagent 写过）|
| 当前 live SHA | `f4147972fe21755523c5682663145708a54d11126e151095537382d06f42fd3` |
| audit replay / supervisor 期望 SHA | `f4147972…`（与 live 一致）✓ |

**监督器报警但不阻拦**（`ACTION.json` 持 `hold` 但不冻结）——这是 app + supervisor 的合法设计。早期 MEMORY 把"current baseline"概念具体化是误称。

## 7. Open Gates（10 条诚实清单）

1. ✅ ~~P3 Codex acceptance~~ → CONDITIONAL_PASS
2. ✅ ~~P4 dry-run 执行~~ → DRYRUN_COMPLETE
3. ✅ ~~P5 spec + 执行~~ → COMPLETE_WAITING_CODEX_APPLY_APPROVAL
4. **🔒 P4 formal apply**（待 Codex 独立窗口放行 + CODEX_APPLY_TOKEN）
5. **⏸ OFFICIAL_RESEARCH Codex 验收**（pre-audit 0802 LIKELY_PASS；4 cheer 待办）
6. **📤 Cheer-only 8 月+9 月包人工发送**（ready_to_send）
7. **📞 B 层 5 硬缺口原件**（OPEN，等馆方回函）
8. **⏸ MiniMax autonomous T69+ 重启**（需 Token Plan 配额）
9. **⏸ Grok full handoff loop**（配额 MET 但 NOT_FULL_HANDOFF_LOOP）
10. ✅ **formal DB SHA live 真相** → **已 reconciliation**（`f4147972…` 与 supervisor / audit replay 一致；MEMORY/monitor 中陈旧 SHA 已在 P3 同步）

## 8. 不变式（invariants）

| 不变式 | 状态 |
|---|---|
| `page_provenance.citation_ready=1` = 0 | ✓ |
| 无 `human_verified` 列 | ✓ |
| `domestic_editorial_decisions` 660/29 | ✓ |
| P0—P3 受保护文件 SHA 不变 | ✓ |
| `PRAGMA integrity_check` ok | ✓ |
| 45/45 跨批次交付物审计通过 | ✓ |

## 9. 启动下一步

| 优先级 | 动作 | 文件 | 触发 |
|---|---|---|---|
| P0-A1 | 决定 4 cheer 待办 | `OFFICIAL_RESEARCH_CODEX_PACKET_20260802/` | cheer 决策 |
| P0-A2 | 发 8 月包 B1 + B5/B6 | `hku_*` + `shac_*` | cheer 外发 |
| P1-A3 | 发 9 月包 Top 3（T6/T2/T1）| `HARD_GAPS_SEPT_PACKAGE_20260802/` | cheer 外发 |
| P1-A4 | 升级 MiniMax Token Plan | — | cheer 决策 |
| P2-A5 | Codex 跑 P4 apply | `apply_v2_after_codex_approval.py --apply` | Codex 自动 |
| P2-A6 | Codex 跑 OFFICIAL 验收 | 验收包 | Codex 自动 |

## 10. 自我复盘：早期 MEMORY 误称清单

| MEMORY 误称 | 真相 | 修复（已 P3 同步）|
|---|---|---|
| `current baseline = 4837dbd6…` | live SHA 是 `f4147972…` | MEMORY 改为"live on demand" |
| `current baseline = e4257587…`（monitor）| 同上（14:00 close_links 之后又 drift 到 `f4147972…`）| monitor 改为"drift ledger" |
| 8 个 SHA 是不同 freeze pin | **只是同库的 8 个连续状态** | 改写为"live cycle 链"|
| supervisor 会拦 drift | **不会——只报警** | MEMORY 标记 `hold` 是 explain not block |

P3 同步已修复以上 4 项。
