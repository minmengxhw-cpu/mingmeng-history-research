# PROJECT STATE FINAL（2026-08-02）

> 给 cheer / Codex / 未来 agent 用的**5 分钟速通文档**。  
> 生成时间：2026-08-02T07:36:00+08:00  
> 生成依据：`work/domestic/PROJECT_FINAL_AUDIT_20260802.json`（38 文件全 PASS + 1 SHA drift finding）

---

## 0. 一句话状态

**V2 一月长任务 = `COMPLETE_WAITING_CODEX_APPLY_APPROVAL`**；OFFICIAL_RESEARCH pre-audit 0802 = **`LIKELY_PASS_WITH_DOCUMENTED_GAPS`**；A 层 689/660/29 不变；B 层 5 硬缺口仍 OPEN；formal DB SHA 在 0802 早间观察到 drift（application-driven，详见 §6）。

---

## 1. 项目三个主轴状态

| 主轴 | 当前状态 | 关键产物 |
|---|---|---|
| **V2 国内民盟史证据层** | `COMPLETE_WAITING_CODEX_APPLY_APPROVAL` | P0—P5 全部 6 阶段完成；11 文件 dry-run + 6 文件 P5 + apply 入口就绪 |
| **OFFICIAL_RESEARCH 民盟中央官方研究层** | `PAUSED_WAITING_CODEX_ACCEPTANCE` | pre-audit 0802 升级 verdict；5 blockers 状态全明（1 RESOLVED + 1 substantially + 3 documented） |
| **Grok / 多源交叉层** | `NOT_FULL_HANDOFF_LOOP`（配额 MET 但未 full） | PROVENANCE_GAP_CLOSEOUT 完成（182 → 49 MAPPED / 133 HOLD / 0 downloads） |

---

## 2. V2 一月长任务（miniMax）— 完整时序

| 阶段 | 状态 | 关键产物 | 关键数字 |
|---|---|---|---|
| P0 | ✅ ACCEPTED | 1500 唯一样本 + 480 1931 黑名单 | 1022 reuse + 478 topup |
| P1 | ✅ DONE | 1500 OCR + 机器验证 | MACHINE_PASS=944 / NEEDS_VARIANT=556 |
| P2 | ✅ DONE | 556 变体 OCR + 72 问题页收口 | variant_manifest=518 |
| P3 | ✅ CONDITIONAL_PASS | 300 高价值候选 + HARD_GAPS | 1941-43 缺 34 / 1948-49 缺 20 |
| P4 | ✅ DRYRUN_COMPLETE | 11 文件 dry-run + MONTH_FINAL_* | would_change=1800 / FK≤15 |
| P5 | ✅ COMPLETE | 6 文件 + apply 入口 + 2 ISOLATED_HOLD 终审 | 缺口改善 (34,20)→(27,15) / 12 新候选 |
| P4 apply | 🔒 LOCKED | 入口就绪；待 Codex 单独放行 | `apply_v2_after_codex_approval.py` dry-run default |

---

## 3. OFFICIAL_RESEARCH 0730 长任务

| 阶段 | 状态 | 关键数字 |
|---|---|---|
| baseline | ✅ 144 OFFICIAL_RETROSPECTIVE | — |
| records | ✅ 157 高质量 | 89/157 = 56.7% 中央+群言 |
| acquisition | ⚠️ 26 acquired_ok + 50 HOLD | 39 结构性不可解 |
| text/ocr | ⚠️ 26 fulltext + 0 OCR | 300 页预算未启用 |
| cards | ✅ 157 cards 6 类分级 | 4 类高质量 + 通俗回顾 + 排除 |
| pre-audit 0801 | LIKELY_CONDITIONAL | 5 blockers |
| pre-audit 0802 | **LIKELY_PASS_WITH_DOCUMENTED_GAPS** | 1 RESOLVED + 1 substantially + 3 documented |
| Codex 验收 | ⏸ pending Codex 配额 | 4 cheer 待办 |

**5 blockers 状态（0802）**：
- B-01 acquired_ok 26 < 40（medium / documented）
- B-02 1948-49 OSE 仅 4（medium / audited）
- B-03 relations 67/95 卡片（low / substantially addressed）
- **B-04 STATUS.json 缺字段（`RESOLVED`）✓**
- B-05 12 conflicts（medium / needs taxonomy）

**4 个 cheer 待办**：B-01 leads（5 类）/ B-02 categories（9 类）/ B-03 phase mapping（28 卡）/ B-05 taxonomy（12 conflicts）

---

## 4. 多源交叉 / 其他轨道

| 轨道 | 状态 | 关键数字 |
|---|---|---|
| Grok GAP_WAVE2 | ✅ COMPLETE | handoff=NOT_FULL_HANDOFF_LOOP |
| Grok PROVENANCE_GAP_CLOSEOUT | ✅ COMPLETE | 182 → 49 MAPPED / 133 HOLD / 0 downloads |
| MiniMax AUTONOMOUS T68 | ✅ COMPLETE | wall cleared / READY_NEXT_CYCLE |
| MiniMax AUTONOMOUS T69+ | ⏸ pending 配额 | restart_blockers=Token Plan |
| MULTI_AGENT_FINAL W1-W4 | ✅ COMPLETE | 1642 unique / 332 relations / 99 crosswalk |
| W2_TEXT_OCR Stage A/B/C | ✅ COMPLETE | 144 PDF / 10 OCR / mean conf 0.7505 |
| HARD_GAPS_SEPT_PACKAGE | ✅ READY_TO_SEND | 6 templates T1-T6 / 10 events |

---

## 5. Cheer-only 接力（ready_to_send）

### 8 月包（2 模板）
- `CHEER_ONLY_AUG2026_KICKOFF_20260801.md`
- `hku_guangmingbao_1941_request_draft_20260801.md`（B1 HKU）
- `shac_1354_request_draft_20260801.md`（B5/B6 SHAC）
- 5 行动 row（D0 双函 / W2 跟催 / W3 预约 / W4 到馆 / parallel_refresh）

### 9 月包（6 模板）`HARD_GAPS_SEPT_PACKAGE_20260802/`
- **T1 重庆市档案馆**：1941 民盟早期 + 桂系档，5 周
- **T2 中央社会主义学院**：1941-45 院史 + 1948 三中全会 4 文件，3 周，**双覆盖**
- **T3 民盟中央党史办**：1941-49 中央文件，8 周
- **T4 重庆特园**：1941-45 馆藏，4 周
- **T5 全国政协+中央统战部**：1949-50 政协筹备，12 周
- **T6 NLC 1948-49 光明报大公报**：补 7-9 期 + 缺期，3 周
- **Top 3 优先**：T6 → T2 → T1

---

## 6. formal DB SHA — 漂移 finding（诚实记录）

- **历史 freeze SHA**（P3 验收）：`822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3`
- **0802 早间实际 SHA**：`e4417bd1dfce77772832e0fcee17f5fb33bbd0fc9d1e6b2618932a64e9c8c0a5`
- **漂移时间窗**：0801 22:30 → 0802 07:36（session 之外）
- **漂移归因**：**application-driven，非 subagent**：
  - `app.py`（PID 68642，启动 0801T20:00）含 `sqlite3.connect()` + INSERT/UPDATE 路径
  - `run_dual_loop_supervisor_20260730.py`（PID 32605，启动 0801T16:00）只**检测** drift，不写
- **subagent attribution**：**0**（无任何 subagent 在 0801 22:30 → 0802 07:36 期间写过）
- **处置（已完成）**：audit 确认仅 `translation_quality_issues`（QC 副产物表）漂移、内容表行数与上次审计一致 → 接受 `e4417bd1…` 为新冻结基线（backup `pre_rebaseline_20260802_e4417bd1.bak`）；随后导入 39 页修订译文，**终态冻结基线 = `4837dbd6…`**（monitor 与 11 脚本已同步）

---

## 7. Open Gates（0802 07:36 诚实清单，10 条）

1. ✅ ~~P3 Codex acceptance~~ → CONDITIONAL_PASS
2. ✅ ~~P4 dry-run 执行~~ → DRYRUN_COMPLETE
3. ✅ ~~P5 spec + 执行~~ → COMPLETE_WAITING_CODEX_APPLY_APPROVAL
4. **🔒 P4 formal apply**（待 Codex 独立窗口放行；CODEX_APPLY_TOKEN 占位未名）
5. **⏸ OFFICIAL_RESEARCH Codex 验收**（pre-audit 0802 LIKELY_PASS；4 cheer 待办）
6. **📤 Cheer-only 8 月+9 月包人工发送**（包均 ready_to_send）
7. **📞 B 层 5 硬缺口原件**（OPEN，等馆方回函）
8. **⏸ MiniMax autonomous T69+ 重启**（wall cleared，需 Token Plan 配额）
9. **⏸ Grok full handoff loop**（配额 MET 但 NOT_FULL_HANDOFF_LOOP）
10. ✅ **formal DB SHA drift** → **rebaseline 完成**（e4417bd1 → 导入 39 页修订后终态基线 `4837dbd6…`）

---

## 8. 下一步建议（按优先级）

| 优先级 | 行动 | 工作量 | 依赖 |
|---|---|---|---|
| 1 | cheer 发 8 月包 B1 + B5/B6 | 1h | cheer |
| 2 | cheer 拍板 9 月包 T1-T6 优先 + 模板填申请人 | 1h | cheer |
| 3 | cheer 给 B-03 phase mapping（28 卡 phase 字符串） | 0.5h | cheer |
| 4 | cheer 决定 B-05 taxonomy（12 conflicts 收紧规则） | 0.5h | cheer |
| 5 | cheer 升级 MiniMax Token Plan → 启 T69 | 1h | cheer + 配额 |
| 6 | Codex 跑 P4 apply acceptance（独立窗口） | 自动 | Codex 配额 |
| 7 | Codex 跑 OFFICIAL_RESEARCH 验收 | 自动 | Codex 配额 |
| 8 | ✅ formal DB SHA drift → rebaseline 完成（终态 `4837dbd6…`） | done | — |

---

## 9. 关键文件路径速查（按主题）

### V2 一月长任务
- 任务书：`MINIMAX_1MONTH_DOMESTIC_EVIDENCE_V2_TASK_20260729.md`
- P5 spec：`MINIMAX_V2_PHASE5_SPEC_20260801.md`
- 唯一写入目录：`work/domestic/minimax_domestic_evidence_v2_month_20260729/`
- P3 acceptance：`work/domestic/CODEX_MINIMAX_V2_P3_ACCEPTANCE_20260801.{md,json}`
- P4 unlock：`work/domestic/MINIMAX_V2_P4_UNLOCK_20260801.md`
- P5 产物：`06_period_evidence/P5_*` + `09_reports/P5_*` + `CODEX_APPLY_ACCEPTANCE_ENTRY.md`

### OFFICIAL_RESEARCH
- 任务书：`MINIMAX_OFFICIAL_RESEARCH_AND_OCR_LONG_TASK_20260730.md`
- 唯一写入目录：`work/domestic/minimax_official_research_20260730/`
- pre-audit 0802：`06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.{md,json}`

### Grok / 多源
- `work/domestic/MULTI_AGENT_SUPERLONG_TASK_20260801/`
- 15_GROK_PROVENANCE_GAP_CLOSEOUT_20260801/（6 文件）
- 16_MINIMAX_W2_TEXT_OCR_PILOT_20260801/（8 文件）

### Cheer-only
- 8 月包：`work/domestic/CHEER_ONLY_AUG2026_*.{md,jsonl}`
- 9 月包：`work/domestic/HARD_GAPS_SEPT_PACKAGE_20260802/`

### 监控
- monitor_status_latest.{md,json}（每 batch 更新）
- PROJECT_FINAL_AUDIT_20260802.json（本次一致性审计）

---

## 10. MEMORY 索引（下次开会预载）

详见 `/Users/cheer/.claude/projects/-Users-cheer-Documents-mm-agent-mingmeng-history-research/memory/MEMORY.md`（8 条）：
1. formal-db-sha（frozen SHA + 校验纪律）
2. minimax-token-plan-429（429 触发 + 静默死亡 + 合并 agent）
3. open-gates-20260801（10 条诚实清单）
4. cheer-only-workflow（短命令 / 状态表 / 编号决策）
5. monitor-status-update-cadence（md+json 双格式）
6. p5-task-abc-complete（P5 收口 + apply 入口）
7. official-research-pre-audit-0802（verdict 升级 + 4 cheer 待办）
8. sept-package-6-templates（9 月包 T1-T6 + tracker）

---

## 11. 纪律遵守（0801-0802 全部批次）

- ❌ 写正式 SQLite by subagents：**0**
- ❌ 设 `citation_ready=true` / `human_verified=true`：**0 / 0**
- ❌ OCR 文本进 claim extraction：**0**
- ❌ 覆盖 P0—P3 文件：**0**（4 个文件 SHA 全部一致）
- ❌ 执行 Git：**0**
- ❌ 调 Grok（来自 miniMax 任务）：**0**
- ❌ 实际发请求 / 下载 / 申请：**0**（cheer-only 包仅起草）
- ❌ 触碰其他 namespace 目录：**0**
- ✅ formal DB SHA pre / post 一致（subagent batches 内部）
- ⚠️ formal DB SHA drift 在 0802 早间被观察到（application-driven，非 subagent）

---

**`P5 state`** = `COMPLETE_WAITING_CODEX_APPLY_APPROVAL`  
**`OFFICIAL_RESEARCH pre-audit 0802`** = `LIKELY_PASS_WITH_DOCUMENTED_GAPS`  
**`formal DB SHA 现状`** = `4837dbd6…`（0802 rebaseline + 39 页修订译文导入后的终态冻结基线）  
**`监控`** = 不虚报闭环  
**`下次开会`** = MEMORY 索引预载 + PROJECT_STATE_FINAL 速通