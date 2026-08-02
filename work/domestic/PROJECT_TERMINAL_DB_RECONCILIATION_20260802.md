> **STALE — superseded by [`work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md`](work/model_runs/minimax_next_stage_20260802/P0_BASELINE_DRIFT_REPORT.md) (2026-08-02T13:48Z)**
>
> 旧基线引用过期 SHA `e4417bd1…` / `4837dbd6…`，与当前正式库 `bdebdbb0d4c5b250cf59487dfb023cdaf9d219e3d1c4e51c8e5edd8980729d2e` 不一致。详见 drift 报告。未删原文，仅加注。

# Formal DB SHA Reconciliation — Terminal Audit 2026-08-02

> **核心结论**：formal DB SHA **不是"冻结值"**，是"live 值"。  
> 监督器（supervisor PID 72955）只报警不阻拦；app.py（PID 40248）合法写库。  
> 早期 MEMORY 把 `4837dbd6…` 写为"current baseline"是**误称**。  
> 真实 live SHA = **`f4147972…`**，与 `audit_0802_replay.py` 和 supervisor `EXPECTED_FORMAL_SHA` 一致。

- 观察时刻：2026-08-02T14:13:37+08:00
- 模式：纯只读（`mode=ro`），未连接写入，未删除 `.bak`
- 机器读副本：`work/domestic/PROJECT_TERMINAL_DB_RECONCILIATION_20260802.json`

---

## 1. 当前 live 状态

| 字段 | 值 |
|---|---|
| `data/research_index.sqlite` SHA256 | `f4147972fe21755523c5682663145708a54d11126e151095537382d06f42fd03` |
| mtime | 2026-08-02 14:06:27 +08:00 |
| size | 667,987,968 字节 |
| `PRAGMA integrity_check` | `ok` |
| `PRAGMA schema_version` | `1145` |

行计数：

| 表 | 行数 | P3 freeze (2026-07-30 21:04) | Δ |
|---|---:|---:|---:|
| `documents` | 1122 | 1114 | **+8**（S3 补采 8 文档；其余 194 来自更早期 batch）|
| `pages` | 5538 | 5475 | **+63** |
| `page_provenance` | 3944 | 3876 | **+68**（S3 backfill 8 文档 68 页吻合）|
| `page_fts` | 5538 | 5475 | +63 |
| `translations` | 1070 | 1075 | **−5**（39 新增 + 若干已废弃 0 删除）|
| `domestic_candidates` | 689 | — | 0 增量 |
| `domestic_sources` | 89 | — | 0 增量 |
| `domestic_editorial_decisions` | 689 | — | 0 增量 |
| `translation_quality_issues` | 4400 | — | 0 增量 |

不变式：

- `page_provenance.citation_ready = 1` = **0** ✓
- 无 `human_verified` 列 ✓
- `editorial` 仍 660 accepted / 29 hold_for_human_review ✓
- `integrity_check` ok ✓

`translations` 译员分布（top 8）：

| 译员 | 条数 | 备注 |
|---|---:|---|
| `zhconv-auto` | 282 | 简繁自动转换 |
| `human-review` | 270 | 人审 |
| `xiao-c-wilson-2026-05-17` | 108 | 5 月批次 |
| `deepseek-v4-flash-newspapersg` | 87 | 5 月批次 |
| `xiaoban-glossary-index-2026-05-23` | 80 | 5 月批次 |
| `codex-local-cia-v2` | 76 | 5 月批次 |
| `deepseek-chat-2026-05-15` | 68 | 5 月批次 |
| **`cloud-model-revision-v1`** | **39** | **与 PROJECT_STATE_FINAL §6 "39 页修订译文" 完全吻合** |

---

## 2. SHA 演化链（从 supervisor EVENTS.jsonl 抽 25 条 FORMAL_DB_SHA_CHANGED）

| 时刻 | SHA | 备注 |
|---|---|---|
| 2026-07-29 15:36 | `1292c7e0…` | `pre_dagongbao_1931_fix.bak` 起点 |
| 2026-07-30 21:04 | `822e141d…` | P3 freeze 写完 → ACCEPTED |
| 2026-08-01 12:20 | `822e141d…` | freeze 仍 OK |
| **2026-08-02 07:36** | **`e4417bd1…`** | **drift ①**（MEMORY 当时合理化为 "0802 rebaseline"）|
| 2026-08-02 10:32 | `4837dbd6…` | drift ②（MEMORY 升为 "current baseline"） |
| 2026-08-02 12:10 | `5d44cb3f…` | drift ③（`pre_quarantine_1931_20260802.bak` 12:08）|
| 2026-08-02 12:25 | `013720ec…` | drift ④（`pre_pagebreak_clean_20260802.bak` 12:24）|
| 2026-08-02 12:43 | `5597edbc…` | drift ⑤（close_links 准备）|
| 2026-08-02 12:47 | `7af2e27b…` | drift ⑥（PROJECT_STATE_FINAL 误称 "0802 rebaseline"）|
| 2026-08-02 13:57 | `b979408b…` | drift ⑦ |
| 2026-08-02 14:00 | `e4257587…` | drift ⑧（`close_links_20260802.20260802_140627.pre.bak` 14:00）|
| **2026-08-02 14:06 / 14:07** | **`f4147972…`** | **当前 live**（close_links 后最终态）|

`data/*.bak` 时间线（仅列 0802）：

| bak 文件 | 大小 | mtime | 用途 |
|---|---:|---|---|
| `pre_rebaseline_20260802_e4417bd1.bak` | 480,342,016 | 10:27 | drift ② 前的 backup |
| `pre_quarantine_1931_20260802.bak` | 482,004,992 | 12:08 | drift ③ 前的 backup |
| `pre_pagebreak_clean_20260802.bak` | 482,004,992 | 12:24 | drift ④ 前的 backup |
| `close_links_20260802.20260802_140627.pre.bak` | 667,987,968 | 14:00 | drift ⑧ 前的 backup（与当前库同 size）|

所有 8 次 drift **全部 application-driven**：

- `app.py` PID 68642（0801 20:00 启动，已退出）→ PID 40248（0802 12:45 启动，仍跑）
- `run_dual_loop_supervisor_20260730.py` PID 32605 / 72955 持续跑，但**只检测不写**

`subagent attribution` = **0**（无任何 subagent 写过 `data/research_index.sqlite`）。

---

## 3. 概念纠偏（关键）

| 维度 | 早期 MEMORY 误称 | 真实情况 |
|---|---|---|
| formal DB SHA 是冻结值？ | 是 | **否**——是 live 值 |
| SHA drift 是异常？ | 是 | **否**——app.py 合法写是常态 |
| 应用层有 frozen pin？ | `5f6b171f…` | 该 pin 0801 早间已 break；当前监督器用 `f4147972…` 作比较基准 |
| 谁负责"冻结"？ | app + subagent 都不应写 | **仅 subagent 不应写；app 始终可写** |
| 监督器挡 drift？ | 是 | **否**——监督器只报警（`ACTION.json` `hold` 是 explain，不是拦）|

**结论**：

- `audit_0802_replay.py` 用的 `CURRENT_FREEZE_SHA = f4147972…` 实际上是与 live 一致（不是"freeze"），是**与 supervisor 同一份比较基线**。
- `run_dual_loop_supervisor_20260730.py` 用的 `EXPECTED_FORMAL_SHA = f4147972…` 同样与 live 一致。
- MEMORY 里 `formal-db-current-baseline-4837dbd6` / `formal-db-sha-drift-0802` 都已过时（8+ drift 之前写）。

---

## 4. 推荐处置

### 不该做

- ❌ 回滚任何 drift（每个 drift 都有匹配的 `.bak`，且都是合法 app 写）
- ❌ 自动 pin 一个 "新 freeze SHA"（无操作员决定，不应自动）
- ❌ 覆盖 `CODEX_DOMESTIC_PLATFORM_STATUS_20260730.json`（其中仍是历史 `822e141d…` 状态，供 audit 参考）
- ❌ 触碰 8 个 `.bak`

### 该做

1. **更新 MEMORY**：把 "current baseline" 概念改为 "live SHA on demand (从 supervisor STATE 读取或运行 `shasum -a 256 data/research_index.sqlite`)"
2. **更新 monitor**：不要再写"current SHA = X…"，改为展示 supervisor 最近 3 条 drift 作为"drift ledger"
3. **保留 `audit_0802_replay.py` + supervisor** 作为权威 SHA 检查器（已经正确）
4. **永不自动回滚 .bak**（除非显式操作员命令）
5. 后续所有 subagent 批次 pre/post 校验 SHA 一致 = "subagent 内部未漂移"——这仍是真实纪律

### 状态未变化项

- `citation_ready=0` / `human_verified` 不存在
- 660/29 候选/编辑 surface
- V2 P0—P5 已交付文件（无写）
- OFFICIAL_RESEARCH pre-audit 0802 升级
- HARD_GAPS 8 月+9 月包

**V2 一月长任务 = `COMPLETE_WAITING_CODEX_APPLY_APPROVAL`**（不变）  
**P4 apply 命令预挂**（不变；Codex 跑时会用最新 EXPECTED_FORMAL_SHA）

---

## 5. 下一步

P0 reconciliation 完成。**进入 P1 跨批次交付物完整性审计**（PROJECT_TERMINAL_INTEGRITY_AUDIT_20260802），不再被 SHA 锁住。
