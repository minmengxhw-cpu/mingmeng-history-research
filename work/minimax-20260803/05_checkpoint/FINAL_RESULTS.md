# 国内资料生产线 — 阶段 2 最终结果

**取消时间**: 2026-08-04T22:35:58+08:00
**最后心跳**: iteration 10 (commit d643b30)
**取消 commit**: 0467851
**取消信号**: work/minimax-20260803/_control/STOP_SIGNAL.md

---

## 一、总体规模

| 指标 | 数值 |
|---|---:|
| 候选总数 | **664** |
| L1（原件 + 完整页级定位） | 320 (48.2%) |
| L2（页级定位 / 汇编） | 225 (33.9%) |
| L3（剪报 / 代用件） | 54 (8.1%) |
| LX（无定位残留） | 0 |
| citation_ready | 314 |
| needs_ocr | 249 |

## 二、三类清单

| 桶 | 行数 | 说明 |
|---|---:|---|
| import_ready | **545** | 可直接入库 |
| needs_review | 27 | 需人工复核 |
| exclude | 92 | 重复 / 拒收 |

## 三、质量门 (Quality Gates) — 全部通过 ✅

- ✓ **LX 残留 = 0**（无 LX 无定位件残留）
- ✓ **ocr_draft_cite = 0**（needs_ocr=1 AND citation_ready=1）
- ✓ **ocr_plan_cite = 0**（ocr_plan 中 citation_ready=1）
- ✓ **duplicates = 92**（全部归入 exclude）
- ✓ **lx_promoted = 4**（>=4 阈值）
- ✓ **gate = PASS**

## 四、OCR 与人工复核工作量

| 指标 | 数值 |
|---|---:|
| ocr_plan 总数 | 216 |
| OCR 批次数 | 7 |
| OCR 预计耗时（分钟） | 27.1 |
| needs_review_tasks | 73 |
| 复核预计耗时（分钟） | 851 |

## 五、LX 升级

- verified: **4**
- applied: **4**
- 4 维字段齐全 + wikisource URL 的候选 LX 已全部升级

## 六、Pipeline 状态（11/11 通过）

| # | 脚本 | 状态 |
|---|---|---|
| 1 | inventory | ✓ 664 rows |
| 2 | dedup | ✓ 32 clusters / 92 dup |
| 3 | source_manifest | ✓ gate=PASS |
| 4 | ocr_manifest | ✓ plan=216 / skip=228 / done=69 |
| 5 | staging | ✓ 664 candidates |
| 6 | three_lists | ✓ 545/27/92 |
| 7 | evidence_gap | ✓ 9 events / 8 actionable |
| 8 | ocr_batches | ✓ 7 batches |
| 9 | lx_upgrade | ✓ 0 proposals (无新候选) |
| 10 | lx_apply --apply | ✓ 0 applied |
| 11 | needs_review_tasks | ✓ 73 tasks |

## 七、心跳历程

| Iter | Commit | 说明 |
|---|---|---|
| 2 | 3c9d78d | staging preserves LX upgrades + verify reads lx_apply_report |
| 3 | 59529e6 | refresh staging + lx_apply 4 upgrades |
| 4 | 2f2352f | staging refresh (no new LX upgrades) |
| 5 | a7b46e3 / 9749e2c | lx_apply preserves verified history + 简繁 title match |
| 6 | 456c655 | staging also syncs evidence_grade + citation_ready on LX→L1 |
| 7 | ac2bac8 | staging refresh (no LX to upgrade) |
| 8 | decf93d | staging refresh (no LX to upgrade) |
| 9 | 3f03d33 | staging refresh (no LX to upgrade) |
| 10 | d643b30 | staging refresh (no LX to upgrade) |
| 取消 | 0467851 | stage 2 heartbeat worker cancelled |

## 八、推进判定

- **10 次心跳全部跑通全部 11 个 pipeline + 质量门 100% 通过**
- **LX 升级**: 4 件（iter 3 完成，iter 4-10 维持）
- **OCR 进展**: 0（无新 OCR 完成回灌数据库）
- **needs_review**: 73 任务已生成但未执行（851 分钟预计工作量）
- **实质推进**: 阶段 2 数据建模与质量门稳定期；OCR 批量与人工复核工作已调度但尚未执行
