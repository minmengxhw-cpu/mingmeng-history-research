# Batch 3 · L1—L4 分级终稿与 citation_ready 严格门禁报告

## 1. 门禁规则（六道）

G1 等级 ∈ L1/L2 ｜ G2 availability=full_item_online|surrogate_online(影像) ｜ G3 资料类=一手|汇编 且非目录冒充全文 ｜ G4 catalog_reference 非空且 verified ｜ G5 非 OCR 草稿 ｜ G6 uncertainty 无重大保留

## 2. 结果总览

| 指标 | 数量 |
|---|---:|
| 候选总数 | 689 |
| 严格门禁 PASS | 284 |
| 严格门禁 FAIL | 405 |
| accepted 且 PASS（可入 citation 层） | 284 |
| staging 声称 citation_ready=yes | 229 |
| 其中通过严格门禁 | 203（26 条被严格门禁打回） |

## 3. FAIL 原因分布

| 门禁 | 失败数 |
|---|---:|
| G5_ocr_draft | 246 |
| G6_uncertain | 105 |
| G2_avail=catalogue_only_online | 96 |
| G1_level=L3 | 82 |
| G3_class=待定 | 49 |
| G1_level=L4 | 44 |
| G3_class=二手 | 38 |
| G2_avail=surrogate 但证据类型非影像 | 18 |
| G2_avail=not_online | 16 |
| G4_catref_status=unpublished | 15 |
| G4_catref_status=pending | 12 |
| G1_level=LX | 4 |

## 4. 结论与处置

- 现行 229 条 citation_ready=yes 中 203 条通过严格门禁，26 条被驳回（多为 G1 等级不足 / G4 目录状态未 verified / G6 不确定性保留）
- 通过名单 → `citation_gate_pass.csv`；驳回明细 → `citation_gate_failures.csv`
- 正式库侧 citation_ready 仍为 0（0702 验收口径）；本报告是库外门禁基线，正式库门禁由生产轮次执行
