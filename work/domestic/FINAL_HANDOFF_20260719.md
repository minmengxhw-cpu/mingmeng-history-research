# FINAL_HANDOFF_20260719

接力日期：2026-07-19 10:04 (Asia/Shanghai)  
接力方：Mavis / mavis (root session `mvs_99f6df4cf4454cf3b4bb0cc1d54d087a`)  
接力给：cheer 人工 + Codex（后续 sprint 38+）+ minimax（后续 sprint 38+）+ Grok（备选二次确认）

---

## 0. 一句话总览

mingmeng-history-research 阶段 0718—0719 收口完成；基线 345 候选 / 160 accepted / 185 pending / 9 事件 / 1 pair_available 8 pair_partial；7 件硬缺口 + 6 件 cheer-only 接力 + 6 字段 schema backlog 等后续 sprint 38+。

---

## 1. 已完成（0718—0719）

### 1.1 Grok 0718 阶段

- ✅ Phase 0 脱敏契约审查（`contract_ok: false` + 12 字段建议）
- ✅ Phase 1 公开检索（3 次 cancelled，4 个 L4 候选 minimax 拒绝升级）
- ✅ Phase 3 1941—1947 公开检索（4 回合 cancelled，0 候选）

### 1.2 Minimax 0718 同期

- ✅ Phase 0 独立审查（跟 Grok 一致，5 类问题）
- ✅ Phase 1 4 L4 候选复核（`secondary/L4 / needs_human_review`）
- ✅ 主报告 `minimax_public_search_20260718.md`（15.7 KB，4 任务 15+ finding block）

### 1.3 Minimax 0719 接力（cheer 拍板连续完成 phase 0—5）

- ✅ Phase 0 接管审计（87/337/152/185 baseline + R1 第38页边界纠错 + R2 page-111—116 补齐）
- ✅ Phase 1 1941—1945（组织规程 L2 accepted；公开网负向）
- ✅ Phase 2 1946 光明报文章级（3 L1 accepted + 1 L3 硬缺口卡）
- ✅ Phase 3 1947 三项核心硬缺口（维持）
- ✅ Phase 4 1948—1949（笔谈 / 和平态度 / 台湾解放 L1 accepted）
- ✅ Phase 5 收口（校验全过 + 文档更新）

### 1.4 Codex 0719 统一审核

- ✅ 接受 8 条（4 光明报 1946 + 2 光明报 1948-1949 + organization-regulation + political-report）
- ✅ 维持 2 条 needs_human_review（政治报告 toc-gap / 张澜时代日报 lead）
- ✅ 新拆 1 条 L1 待止页（1946-issue03）
- ✅ 1947 三项分项状态明确（不合并）

### 1.5 Mavis 0719 总复核

- ✅ Grok 0718 净增 0（4 L4 拒绝，0 phase 3 候选）
- ✅ 跨 4 wave 一致性 100%
- ✅ 5 件模板全部落档
- ✅ 校验全过

---

## 2. 关键决策（已拍）

| 决策 | 拍板方 | 内容 |
|---|---|---|
| Grok 0718 4 L4 候选 | minimax 0718 + Codex 0719 + Mavis 0719 | 全部 `secondary/L4 / needs_human_review`，不进入 candidates.jsonl |
| Grok 契约审查 12 字段 | minimax 0718 + Mavis 0719 | schema 4/5 已修；6 字段 backlog 留 sprint 38+ |
| 1941 成立第38页边界 | minimax 0719 phase 0 R1 | 改为《对时局主张纲领》1941-10-10 |
| 政治报告 page-111—116 | minimax 0719 phase 0 R2 | 补齐本地页图 |
| 组织规程新登记 | minimax 0719 phase 1 | `domestic:MMHIST:organization-regulation-1945` L2 needs_human_review → Codex 接受 L2 |
| 1946 汇编政治报告 | minimax 0719 phase 2 | L3 硬缺口卡（目录错位） |
| 1947 三项硬缺口 | minimax 0719 phase 3 | 维持；分项独立不合并 |
| 1946 光明报新三/新六 | minimax 0719 phase 2 | 题名不清，保持整期（codex 0719 新拆新三号 L1 待止页） |
| 1948-1949 台湾解放 | minimax 0719 phase 4 | L1 needs_human_review → Codex 接受 L1 |

---

## 3. 当前 baseline（2026-07-19 10:04 freeze）

```text
候选: 345 (L1 247 / L2 47 / L3 8 / L4 39 / LX 4)
状态: accepted 160 / needs_human_review 185
事件: 9 (1 pair_available + 8 pair_partial)
来源: 87
SQLite: 87 sources / 345 candidates / 185 pending / 345 decisions
校验: validate / event_coverage / ingest / audit / git diff --check 全过
```

事件覆盖：
- `1941-formation` 7 候选 / pair_partial
- `1944-reorganization` 11 候选 / pair_partial
- `1945-first-congress` 19 候选 / pair_partial
- `1946-pcc` 23 候选 / pair_partial
- `1946-refuse-national-assembly` 18 候选 / pair_partial
- `1946-li-wen` 14 候选 / pair_partial
- `1947-illegal-dissolution` 47 候选 / pair_partial（核心难点）
- `1948-third-plenum-may-day` 8 候选 / **pair_available**（唯一闭环）
- `1949-new-pcc` 10 候选 / pair_partial

---

## 4. 未完成 / 接力给后续 sprint 38+

### 4.1 7 件硬缺口（cheer-only 路径）

1. 1941-10-10/16 香港《光明報》原刊 → 港大缩微预约
2. 1944 全国代表会议原始文件 → 民盟中央 / 民主党派历史陈列馆 / 特园
3. 1945 政治报告 / 组织规程 / 宣言 / 纲领同期原始印本 → 同上
4. 1946《民主同盟文獻》目录「代表大会政治报告」正文 → 1946 汇编其他渠道互校
5. 1947-10-27 内政部公函 → 二史馆 1354 全宗函调
6. 1947-11-06 民盟总部解散公告独立原始印本 → 同上
7. 1947-11-04 北平《新民报》教授联署声明原版 → 孔夫子 / 校史馆

详细清单见 `work/domestic/cheer_only_queue_20260719.md`。

### 4.2 6 字段 schema backlog（sprint 38+ 拍）

| 字段 | 优先级 | 落地难度 |
|---|---|---|
| `authenticity_level_accepted` | 中 | 低 |
| `relevance_grade_accepted` | 中 | 低 |
| `sensitivity_class` | 低 | 中 |
| `evidence_basis` | 中 | 中 |
| `field_provenance` | 高 | 中 |
| `inference_flag` | 高 | 低 |

不动当前 sprint 37+ production。

### 4.3 待 Codex 后续拆分

- 1946 光明报 新三号《為完成雙十節的歷史任務而奮鬥》止页（已拆 L1 起页待止页）
- 1946 光明报 新六号社论题名（OCR 提升后拆）
- 1946 光明报 新一/二/四/七/八号 文章级拆分（高 ROI 候选）

### 4.4 待 minimax 后续

- sprint 38+ 阶段 6 接力（如 cheer 启动港大缩微，minimax 配合 OCR + 互校）
- sprint 38+ 阶段 7 接力（如 cheer 启动二史馆函调，minimax 配合目录核读）

### 4.5 Grok 边界定位

- ✅ 适合：契约审查 / 二次确认 / 负向检索冗余
- ❌ 不适合：主执行方（cancel 率高、公开网稳定性差）

---

## 5. 给后续 sprint 38+ 的接力 checklist

### 5.1 sprint 38+ 启动前必跑

```bash
cd "/Users/cheer/Documents/mm agent/mingmeng-history-research"
python3 -B scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
python3 -B scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
python3 -B scripts/domestic/ingest_domestic.py --db data/research_index.sqlite --sources data/domestic/source_registry.json --candidates data/domestic/candidates.jsonl
git diff --check
```

预期：345 / 0 failed / 9 events / 87 sources / 185 pending / clean。

### 5.2 sprint 38+ 关键路径（mingmeng-history-research）

1. **P0**：cheer 启动港大缩微预约（1 件接力）
2. **P0**：cheer 启动二史馆函调（1 件接力）
3. **P1**：cheer 启动 NLC 视检（大公报 113 卷 9-16 版）
4. **P1**：codex 继续文章级拆分（1946 光明报新一/二/四/七/八号 + 新六号 OCR 提升后）
5. **P1**：schema 6 字段落地
6. **P2**：cheer 启动校史馆 / 民盟中央 / 孔夫子 3 件接力

### 5.3 sprint 38+ 不应做

- ❌ 不应跑 Grok 做主执行（cancel 率高）
- ❌ 不应把 L4 升级为 L1（除非有原刊影像）
- ❌ 不应把汇编 / OCR / 目录 / 盟史网页升为「原件」
- ❌ 不应改 accepted 语义边界（accepted = 记录身份/页位/目录入口审核通过，**不** = 原件 provenance 完成 / 全文逐字转录完成 / 异文整理完成 / 复制权利闭环）

---

## 6. 跨项目状态（双线 sprint 同步）

### 6.1 mllm-wiki-kb-submit sprint 36+ / 37+ 状态

- HEAD: `b124f1a` (分支 `minimax/daylong-kb-closeout-t181-t200-2026-07-12`)
- KB_score: **54.13%** (M1 100% / M2 0% / M3 100% / M4 18% / M5 0% / M6 66.7% / M7 66.7% / M8 56.7% / M9 100%)
- pytest: 547 PASS / 17 SKIP / 0 FAIL
- 核心瓶颈: M2 = 0/968 verified (cheer-only 卡死)
- sprint 37+ spec 落档 `f33748f` (12 件 T213-T224, 14 cheer-only 红线, 11 BLOCKED)
- 已落地：T213-T215 wave 1 (m2 import / packet / handoff skeleton)
- 待 cheer 拍：sprint 37+ wave 2-4 派单

### 6.2 mingmeng-history-research sprint 0718—0719 状态

- HEAD: `60b569f` (分支 `main`, feat: 香港报刊开放源登记 /hk-press)
- 候选: 345 / accepted 160 / pending 185
- 校验全过 / git diff --check clean
- 6 件 cheer-only 接力 + 7 件硬缺口 + 6 字段 schema backlog
- Grok 0718 净增 0（已正式 ack 收口）

### 6.3 双线 sprint 互不干扰

- mllm-wiki-kb-submit 是 mavis 主线，54% → 60% → 80% → 100% KB_score
- mingmeng-history-research 是并行线，依赖 cheer-only 拍板
- 两者不共享 worktree / 不共享候选 / 不共享 sprint 节奏

---

## 7. 风险登记（持续）

| 风险 | 等级 | 缓解 |
|---|---|---|
| cheer-only 接力长期不拍 | **高** | 6 件清单已落档；触发命令已写；模板已备 |
| Grok 公开网 cancel 率高 | 中 | 主执行用 minimax + Codex；Grok 仅做 pre-flight |
| 1947 三项原件卡死 | **高** | 二史馆 / NLC / 孔夫子 / 校史馆 4 路径并行 |
| schema backlog breaking | 中 | sprint 38+ 拍；当前 sprint 37+ 不动 |
| 双线 sprint 资源争抢 | 低 | 不共享 worktree；不共享 cron；不共享 cheer 节奏 |
| minimax 0719 接力上下文丢失 | 低 | 全部报告落档 `work/domestic/minimax_phase*_20260719.md` |
| Codex 0719 接力节奏断 | 中 | codex_unified_review_20260719.md 已落档；下轮 codex 可衔接 |

---

## 8. 后续 sprint 38+ 启动模板

```text
# 给 cheer 启动 sprint 38+

cheer 拍：
1. 港大缩微预约 — 启动 / 暂缓 / 改路径
2. 二史馆函调 — 启动 / 暂缓 / 改路径
3. NLC 视检 大公报 113 卷 9-16 版 — 启动 / 暂缓 / 改路径
4. sprint 38+ minimax 接力范围 — 全开 / 部分 / 暂缓
5. schema 6 字段落地 — 启动 / 暂缓 / 部分
6. codex 接力范围 — 全部 / 仅 1946 光明报 / 仅 1948-1949 / 暂缓

mavis 接到拍板后：
- 写 sprint 38+ spec 落档
- 派 minimax worker / Codex worker / Grok pre-flight
- 同步更新 mllm-wiki-kb-submit sprint 37+ / 38+ 状态
- 跑校验 + 落档
- 写 sprint 38+ 收口报告
```

---

## 9. 文件索引（本阶段收口）

| 类别 | 文件 |
|---|---|
| Grok 0718 提交 | `work/domestic/grok/phase_0_*.md`, `phase_1_*.md`, `phase_1_verified_pages.json`, `research/phase_3_early_report.md` |
| Minimax 0718 同期 | `work/domestic/minimax/reviews/phase_0_*.md`, `phase_1_grok_page_classification.md` |
| Minimax 0718 主报告 | `work/domestic/minimax_public_search_20260718.md` |
| Minimax 0719 接力 | `work/domestic/minimax_phase0_audit_20260719.md` ... `minimax_phases_2_to_5_final_20260719.md` |
| Codex 0719 统一审核 | `work/domestic/codex_unified_review_20260719.md` |
| **Mavis 0719 总复核** | `work/domestic/grok_review_final_20260719.md` |
| **收口总报告** | `work/domestic/phase_closeout_0718_0719_20260719.md` |
| **Cheer-only 接力** | `work/domestic/cheer_only_queue_20260719.md` |
| **FINAL_HANDOFF** | `work/domestic/FINAL_HANDOFF_20260719.md`（本文件） |

---

## 10. 总结论

**mingmeng-history-research 阶段 0718—0719 正式收口。**

- 跨 4 wave 一致性 100%
- 校验全过（5 步）
- 0 越权 / 0 重复 / 0 丢失
- 6 件 cheer-only 接力已就绪
- 7 件硬缺口已登记
- 6 字段 schema backlog 已落档
- Grok 边界已定位（pre-flight / 二次确认 / 负向冗余）

**等 cheer 拍板启动 sprint 38+。**
