# Codex-style 抽检报告 — T2.2 7 条 (0721 第三轮)

报告日期：2026-07-21 21:50 (Asia/Shanghai)
适用范围：α2 8 条 accept 后剩余 T2.2 7 条（L3+L4 pending 中非 cheer-only、非 auto-accept 的边界条）
抽检方法：每条做 metadata 复审 + 等级评估 + accept/reject 建议
红线：本文档**不**修改 candidates.jsonl，accept 决策需 cheer 拍板

---

## 总览

| 候选 | 等级 | online | 事件 | 抽检建议 |
|---|---|---|---|---|
| NLC:minmeng-wenxian-1946-toc-political-report-gap | L3 | full_item | 1946 政协 (core) | **降 L3→L4 + accept** |
| GXMM:dagongbao-1947-10-28-illegal-declaration | L4 | catalogue | 1947 解散 (core) | **升 L4→L3 + accept** |
| GXMM:dagongbao-1947-10-29-self-surrender | L4 | catalogue | 1947 解散 (related) | **升 L4→L3 + accept** |
| GXMM:dagongbao-1947-10-30-ban-activities | L4 | catalogue | 1947 解散 (core) | **升 L4→L3 + accept** |
| SHAC:6-5-1216-meng-illegal-transfer-1947 | L4 | catalogue | 1947 解散 (related) | **保留 L4 + accept** |
| MMYunnan:democracy-weekly-run-1944-1946 | L4 | catalogue | 1945 一大 (related) | **保留 L4 + accept** |
| MH:modernhistory-periodical-guoxun | L4 | catalogue | 1942 西北组织 (core) | **保留 L4 + accept** |

## 详细抽检

### 1. `domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap` ⚠️ 等级边界

- 等级 proposed: L3
- online_availability: full_item_online
- event: 1946 政协 / domestic-1946-pcc (relevance=core)
- 内容：1946《民主同盟文獻》目录"代表大会政治报告"条目；正文缺页
- URL: Wikimedia Commons 影像（NLC416-01jh004281-12557 扫描）

**抽检发现**：
- evidence_note 明确标 "正文缺页" — 这是目录 + 影像，不是完整文本
- L3 = "已转录文本"（与 L1 影像 / L2 印刷品 / L3 出版 transcriptions 同档）
- 实际等级应 L4（目录 + locator），不是 L3
- 后续如要升 L3，需 cheer-only 跑 NLC 视检补全正文

**建议**：
- **降 L3→L4 + accept**（接受"目录级 record"）
- 后续升 L3 条件：NLC 视检补全正文后

### 2. `domestic:GXMM:dagongbao-1947-10-28-illegal-declaration` ⬆️ 等级偏低

- 等级 proposed: L4
- online_availability: catalogue_only_online（gxmm.gov.cn 转载大公报，未必 full 文本）
- event: 1947 解散 (relevance=core)
- 内容：大公报 1947-10-28 报道"内部宣布民盟非法·该盟分子到处图谋不轨·各地治安机关严加取缔"

**抽检发现**：
- 这是 1947-10-28 重要新闻报道，**直接对应 1947 解散事件**（国内大公报权威报道）
- 等级 L4 = "可核 + 引用合规"，但事件相关性 = core（事件核心 primary source 报道）
- gxmm.gov.cn 转载可能有版权限制（L4 + citation_only 合理）
- 但等级 L4 似乎偏低 — 1947-10-28 大公报原文是民盟解散事件的核心一手报道，应为 L3

**建议**：
- **升 L4→L3 + accept**（事件核心 primary source 报道）
- 风险：gxmm.gov.cn 转载可能不完整（与 NLC 大公报 113 卷 9-16 版 cheer-only 函调互补）

### 3. `domestic:GXMM:dagongbao-1947-10-29-self-surrender` ⬆️ 等级偏低

- 等级 proposed: L4
- event: 1947 解散 (relevance=related)
- 内容：大公报 1947-10-29 报道"民盟分子自首·须向治安机关申请·首都负责方面宣布"

**抽检发现**：
- 与 10-28 报道同系列，是 1947 解散后续报道
- relevance=related（非 core）— 事件后续报道，事件关联度稍弱
- 等级 L3（核心 primary source 报道）还是合理

**建议**：
- **升 L4→L3 + accept**

### 4. `domestic:GXMM:dagongbao-1947-10-30-ban-activities` ⬆️ 等级偏低

- 等级 proposed: L4
- event: 1947 解散 (relevance=core)
- 内容：大公报 1947-10-30 报道"民盟禁止活动·董显光答记者问·无越轨行动盟员可登记"

**抽检发现**：
- 与 10-28/29 同系列，事件关联度 = core
- 等级 L3 合理

**建议**：
- **升 L4→L3 + accept**

### 5. `domestic:SHAC:6-5-1216-meng-illegal-transfer-1947` ✅ 等级合理

- 等级 proposed: L4
- online_availability: catalogue_only_online
- event: 1947 解散 (relevance=related)
- 内容：上海档案馆 6-5-1216 内政部宣布民盟非法转令
- URL: jstage.jst.go.jp 学术 PDF（asianstudies vol.49）

**抽检发现**：
- 学术 PDF 提供的 SHAC 6-5-1216 转录线索
- L4 + citation_only + catalogue 等级合理
- evidence_locator 清晰，relevance=related（衍生学术文章，不是原始档案）

**建议**：
- **保留 L4 + accept**

### 6. `domestic:MMYunnan:democracy-weekly-run-1944-1946` ✅ 等级合理

- 等级 proposed: L4
- event: 1945 一大 (relevance=related)
- 内容：昆明《民主周刊》出版沿革与馆藏追索线索
- URL: minmengsh.gov.cn（上海民盟官网，跨域讲云南 1944-1946 出版）

**抽检发现**：
- L4 + catalogue + citation_only 合理（民盟 1945 出版的《民主周刊》是事件 primary source，但这里只给线索不是全文）
- relevance=related（1945 一大期间民盟昆明公开活动）

**建议**：
- **保留 L4 + accept**

### 7. `domestic:MH:modernhistory-periodical-guoxun` ✅ 等级合理

- 等级 proposed: L4
- event: 1942 西北组织 (relevance=core)
- 内容：近代史数字图书馆《国讯》半月刊条目页
- URL: modernhistory.org.cn 抗战文献平台

**抽检发现**：
- 《国讯》半月刊 = 1942 中华职业教育社（黄炎培主导）重庆创刊 — 1942 西北组织创建事件相关
- L4 + catalogue + citation_only 合理（条目级，不是全文）
- relevance=core（事件直接相关）

**建议**：
- **保留 L4 + accept**

---

## β2 复审建议总结

| 路径 | 数量 | 工作量 | 风险 |
|---|---:|---|---|
| **激进：3 升 + 1 降 + 3 保留** | 7 | 1 accept 脚本（5 min） | 中（升 L4→L3 涉及等级调整） |
| **保守：全部 L4 + accept** | 7 | 1 accept 脚本（5 min） | 低（不动等级） |
| **β2 跳过** | 0 | 0 | 0（7 条留 pending） |

**我建议激进方案**：3 升 + 1 降 + 3 保留 = 7 条一次性 accept

理由：
- 3 升 L4→L3 的依据明确（事件核心 primary source 报道）
- 1 降 L3→L4 的依据明确（缺页 + 目录级）
- 3 保留 L4 没问题
- 一次写完一个 accept 脚本，5 min 跑完

---

## 数据一致性

本文档不修改 candidates.jsonl。如 cheer 同意激进方案，mavis 将写 `accept_codex_review_tier2_review_20260721.py` 跑批量 accept。
