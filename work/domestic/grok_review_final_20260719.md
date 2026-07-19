# Grok 0718 阶段正式复核落地

复核日期：2026-07-19 10:04 (Asia/Shanghai)  
复核方：Mavis / mavis  
执行方：grok-4.5-build  
项目：`/Users/cheer/Documents/mm agent/mingmeng-history-research`

---

## 0. 复核范围与边界

**输入：**
- `work/domestic/grok/phase_0_public_probe_review.md`（脱敏契约审查）
- `work/domestic/grok/phase_1_public_search_status.md`（公开检索状态）
- `work/domestic/grok/phase_1_verified_pages.json`（4 个 L4 候选）
- `work/domestic/grok/research/phase_3_early_report.md`（1941—1947 公开检索）

**对照基线：**
- `work/domestic/minimax/reviews/phase_0_public_probe_review.md`（同期 minimax 独立 phase 0）
- `work/domestic/minimax/reviews/phase_1_grok_page_classification.md`（同期 minimax 独立 phase 1 复核）
- `work/domestic/minimax_phase0_audit_20260719.md` 至 `minimax_phases_2_to_5_final_20260719.md`（0719 接力）
- `work/domestic/codex_unified_review_20260719.md`（codex 0719 统一审核）

**当前 schema 实测：** `data/domestic/candidates.jsonl` + `docs/domestic/domestic_candidate.schema.json`  
**当前 baseline：** 345 候选 / 160 accepted / 185 needs_human_review / 9 事件 / 1 pair_available + 8 pair_partial

---

## 1. 总评

`verified_status: 复核通过, 净增 0`

Grok 0718 这一轮是**探索性 pre-flight**：

- 契约审查跟 minimax 0718 独立得出同一结论（互证价值）
- 4 个 L4 候选经 minimax 0718 复核 + codex 0719 统一审核，**不进入 candidates.jsonl**
- 1941—1947 公开网负向结论跟 minimax 0719 phase 1+3 完全一致，**不重复跑**

**Grok 边界定调（后续 sprint 参考）：**
- ✅ 适合：契约审查 / 二次确认 / 负向检索冗余
- ❌ 不适合：主执行方（cancel 率高、公开网稳定性差、模型自标 `primary` 跟实际不符）

---

## 2. Phase 0 脱敏契约审查 — `contract_ok: false`

### 2.1 Grok 5 类阻塞问题

1. 候选状态与验收状态没有分离
2. 访问条件与再利用权利没有分离
3. 在线/线下、原件/替代件、目录页/内容页没有分离
4. 证据与研究推断仅靠自由文本，无法机器校验
5. 只有 `*_proposed`，缺少复核后的冻结等级

### 2.2 Grok 12 字段建议 vs 当前 schema 落地

| Grok 字段 | 落地状态 | 当前字段 | 备注 |
|---|---|---|---|
| `candidate_status` | 🟡 partial | `review_status` | enum: candidate/needs_human_review/accepted/rejected/duplicate |
| `authenticity_level_accepted` | ❌ 缺 | 仅有 `_proposed` | 现有用 `review_status=accepted` 二元组实现 |
| `relevance_grade_accepted` | ❌ 缺 | 仅有 `_proposed` | 同上 |
| `medium` | ✅ 已落 | `medium` | enum: physical/digital/hybrid/unknown |
| `online_availability` | ✅ 已落 | `online_availability` | enum: full_item_online/surrogate_online/catalogue_only_online/not_online/unknown |
| `reuse_rights` | ✅ 已落 | `reuse_rights` | enum: public_domain/open_license/citation_only/no_republication/unknown |
| `rights_basis` | ✅ 已落 | `rights_basis` | 自由文本 + enum 兼容 |
| `sensitivity_class` | ❌ 缺 | 无 | 真缺 |
| `evidence_basis` | 🟡 partial | `evidence_type` + `evidence_locator` + `evidence_note` | 三字段兼任 |
| `field_provenance` | ❌ 缺 | 无 | 真缺 |
| `inference_flag` | ❌ 缺 | 无 | 真缺 |
| `source_url_role` | ✅ 已落 | `source_url_role` | enum: item_digital/item_surrogate/finding_aid/bibliography/institution_home/none/unknown |
| `check_outcome` | 🟡 partial | `checked_by` + `checked_at` | 二字段兼任 |

**落地统计：**
- ✅ 6 个完全落地（`medium` / `online_availability` / `reuse_rights` / `rights_basis` / `source_url_role` / `access_mode`）
- 🟡 3 个部分落地（`candidate_status` / `evidence_basis` / `check_outcome`，用既有字段兼任）
- ❌ 3 个真缺（`sensitivity_class` / `field_provenance` / `inference_flag`）
- 🟡 2 个 `_accepted` 字段缺（`authenticity_level_accepted` / `relevance_grade_accepted`，现有 `_proposed` + `review_status=accepted` 二元组替代，但 schema 未显式区分）

### 2.3 跟 minimax 0718 同期独立审查的一致性

| 阻塞项 | Grok 0718 | Minimax 0718 |
|---|---|---|
| 候选/验收分离 | 缺 `candidate_status` | 缺 `acceptance_status` + `verification_status` |
| 访问/权利分离 | 缺 `reuse_rights` / `rights_basis` | 缺 `rights_reuse` / `rights_basis` |
| 在线/原件/目录分离 | 缺 `medium` / `online_availability` | 同建议 |
| 证据/推断分离 | 缺 `evidence_basis` / `inference_flag` | 缺 `evidence_level` / `inference_level` / `tag_evidence_ref` |
| `*_proposed` vs `*_accepted` | 缺 `*_accepted` 字段 | 同建议 |
| L0 校验 | 未提 | 缺 L0 档案层级校验 |

**结论：** 两份审查独立得出同一结论（5 类阻塞），仅字段命名略有差异。Grok 字段偏 schema 设计；minimax 字段偏生命周期管理（`acceptance_status` / `verification_status`）。

**schema 层 4/5 问题已修**（仅剩证据/推断分离 + `_accepted` 字段为真缺）。

### 2.4 schema backlog（后续 sprint 拍板，不动当前）

| 字段 | 优先级 | 落地难度 | 建议路径 |
|---|---|---|---|
| `authenticity_level_accepted` | 中 | 低 | schema 加 enum 字段，Codex 审核通过后写入 |
| `relevance_grade_accepted` | 中 | 低 | 同上 |
| `sensitivity_class` | 低 | 中 | 需先定义 enum（public/internal/restricted/confidential） |
| `evidence_basis` | 中 | 中 | 现有 `evidence_type` 扩展为结构化对象 |
| `field_provenance` | 高 | 中 | 每字段标注来源（人工/汇编/原刊/OCR/推断） |
| `inference_flag` | 高 | 低 | boolean + 推断来源 + 置信度 |

**判断：** 不动当前 sprint 37+ production schema，留待 sprint 38+ 拍。

---

## 3. Phase 1 公开检索 — 3 次 cancelled, 4 个 L4 候选

### 3.1 4 个候选正式拒绝理由

| Grok candidate_id | 题名 | 发布机构 | 日期 | Grok 自标 | 拒绝理由 |
|---|---|---|---|---|---|
| `mmgk-3da6fe99` | 历史沿革 | 民盟 | 2008-12-08 | `primary` | (1) 官方后设叙述，非同期一手；(2) 缺文献汇编书目信息；(3) Grok `model_classification=primary` 跟 minimax `secondary/L4` 冲突 |
| `mmgk-3d1a262d` | 民盟上海组织历届领导 | 民盟 | 2017-04-07 | `primary` | (1) 名录页，非选举公告/会议原件；(2) 缺会议纪要/委员会名单原文 |
| `jyjd-25ee39cd` | 12处上海民盟传统教育基地合集 | 民盟市委宣传部 | 2019-10-17 | `primary` | (1) 教育基地介绍页，非挂牌决定/批复原件；(2) 缺挂牌文件/现场影像 |
| `sx-20240512-144526` | 从南京西路到陕西北路——民盟上海市委机关办公地址的变迁 | 上海盟讯 | 2024-05-12 | `secondary` | (1) 数字报回顾文章，非同期机关文件；(2) 缺产权/租赁/机关通告原文 |

### 3.2 namespace 风格冲突

Grok 用 hash 风格 ID（`mmgk-3da6fe99` / `jyjd-25ee39cd` / `sx-20240512-144526`），
跟项目既有的 `domestic:ORG:topic` 命名空间（`domestic:NLC:guangmingbao-1946-issue05-...`）不一致。

即使接受，**也必须重命名**才能进 `candidates.jsonl`。但 4 条均为 L4 入口，无证据升级价值，**整体拒绝**。

### 3.3 跟 minimax 0718 + codex 0719 一致性

- Minimax 0718 `phase_1_grok_page_classification.md`：4 条全部判 `secondary/L4 / needs_human_review` ✅ 一致
- Codex 0719 `codex_unified_review_20260719.md` 接受 8 条（4 光明报 1946 + 2 光明报 1948-1949 + organization-regulation + political-report），**未接收**这 4 条 ✅ 一致
- 最终 accepted = 160 候选中**无** Grok 提交的 ID

**结论：** 4 个 L4 候选**不**进 `candidates.jsonl`，净增 0。

---

## 4. Phase 3 1941—1947 公开检索 — 4 回合 cancelled, 0 候选

### 4.1 跟 minimax 0719 phase 1+3 一致性

| 目标 | Grok 0718 结果 | Minimax 0719 phase 1/3 结果 | 一致性 |
|---|---|---|---|
| 1941-10-10《光明報》成立原刊 | 公开网无 | 公开网无；港大缩微 `HKC 951 G91 M` 待调 | ✅ 一致 |
| 1941-10-16《光明報》社论 | 公开网无 | 公开网无；同上 | ✅ 一致 |
| 1944 全国代表会议文件原件 | 公开网无 | 公开网无；民憲多期 L1 整期语境；BJDCMM L4 | ✅ 一致 |
| 1945 政治报告原始印本 | 公开网无 | 1983 汇编 101—117 L2 accepted；非原件 | ✅ 一致 |
| 1945 宣言/纲领同期印本 | 公开网无 | 1983 汇编 L2 accepted；1946 汇编 needs_human_review；SHCM L3 实物名录 | ✅ 一致 |
| 1947-10-27 内政部公函 | 公开网无 | 硬缺口维持；公报 2964 号负向；L2 汇编 PDF390 | ✅ 一致 |
| 1947-11-06 总部解散公告 | 公开网无 | 硬缺口维持；张澜时代日报 L4 出处线索（非总部公告） | ✅ 一致 |
| 1947-11-04 北平《新民报》 | 公开网无 | 硬缺口维持；《观察》3卷11期重刊 ≠ 原版 | ✅ 一致 |

**8/8 一致**，Grok 跟 minimax 公开网负向结论完全互证。

### 4.2 Grok 找到的 `sdmm.org.cn/list.php?fid=139&page=2`

- 网络请求失败，未形成可核验记录级候选
- 保留为**未决线索**（不写 candidates.jsonl）
- 后续 sprint 可重试

---

## 5. 总结论

| 维度 | 结果 |
|---|---|
| 跟 minimax / codex 结论一致性 | 100% 一致（无冲突） |
| 净增候选 | **0**（4 L4 不入，0 phase 3 候选） |
| 净增页界 / 档号 / 影像 | 0 |
| schema 增量 | 6 字段 backlog（`authenticity_level_accepted` / `relevance_grade_accepted` / `sensitivity_class` / `evidence_basis` / `field_provenance` / `inference_flag`） |
| 新越权 / 误升级 | 0（phase 1 4 条标 `primary` 但 minimax + codex 都拦住了） |
| Grok 边界定位 | 探索性 pre-flight / 二次确认 / 负向冗余；不作为主执行方 |

**Grok 0718 阶段正式 ack 收口。**

---

## 6. 附录：Grok 提交物索引（保留作历史）

| 文件 | 状态 | 用途 |
|---|---|---|
| `work/domestic/grok/phase_0_public_probe_review.md` | 保留 | 契约审查历史 |
| `work/domestic/grok/phase_1_public_search_status.md` | 保留 | 公开检索状态（cancelled） |
| `work/domestic/grok/phase_1_verified_pages.json` | 保留但**不**进 candidates.jsonl | 4 L4 候选（已拒绝） |
| `work/domestic/grok/research/phase_3_early_report.md` | 保留 | 1941—1947 公开检索负向（已跟 minimax 互证） |

`phase_1_verified_pages.json` 不删除（cher 委托纪律："不删除、覆盖或重写已有材料"），但加 `superseded_by: minimax_0718_phase1_review + codex_0719_unified_review` 注释待后续 sprint 处理。
