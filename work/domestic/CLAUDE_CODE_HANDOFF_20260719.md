# Claude Code 交接文件

**交接日期：** 2026-07-19（Asia/Shanghai）  
**交接方：** Grok（Grok TUI / 主会话 + 多轮 subagent）  
**接手方：** Claude Code（可继续执行 / 复核 / 抽检 accept）  
**项目根目录：** `.`

---

## 0. 一句话

国内民盟史资料库已从「阶段收口」推进到「高密度原刊文章级 + 事件挂接 + cheer-only P0 模板就绪」；**校验全绿**；**五项原件硬缺口仍 OPEN**（需馆藏，勿虚报闭环）。

---

## 1. 当前真实基线（2026-07-19 15:12 实测）

```text
候选 candidates.jsonl     : 425  (failed 0 / unique 425)
accepted                  : 201
needs_human_review        : 224
来源 source_registry      : 89
证据等级                  : L1 323 / L2 50 / L3 8 / L4 40 / LX 4
事件 event_coverage       : 9 个，悬空引用 0
SQLite (ingest 后)        : 89 sources / 425 candidates / 224 pending / 425 decisions
pair_status               : 1 pair_available + 8 pair_partial
missing_paths (audit)     : 0
```

### 事件引用数（约）

| event_id | 引用数 |
|---|---:|
| domestic-1941-formation | 13 |
| domestic-1944-reorganization | 16 |
| domestic-1945-first-congress | 26 |
| domestic-1946-pcc | 28 |
| domestic-1946-refuse-national-assembly | 25 |
| domestic-1946-li-wen | 39 |
| domestic-1947-illegal-dissolution | 80 |
| domestic-1948-third-plenum-may-day | 19 |
| domestic-1949-new-pcc | **167**（已激进瘦身：SAAC L1 + 1949 光明报 + 极少 L4） |

### 启动前必跑

```bash
cd "."
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
python3 scripts/domestic/ingest_domestic.py
python3 scripts/domestic/audit_readiness_20260719.py
# 可选
python3 scripts/domestic/monitor_completion.py
```

期望：`failed=0`，`missing_candidate_references=[]`，`missing_paths=0`。

---

## 2. 主数据路径

| 数据 | 路径 |
|---|---|
| 候选 | `data/domestic/candidates.jsonl` |
| 来源 | `data/domestic/source_registry.json` |
| 事件 | `data/domestic/event_coverage.json` |
| 扫描 PDF | `data/domestic/press_scans/`、`data/domestic/sourcebooks/` |
| SQLite | `data/research_index.sqlite` |
| 页图/工作区 | `work/domestic/` |
| Schema | `docs/domestic/domestic_candidate.schema.json` |
| 校验脚本 | `scripts/domestic/validate_*.py`、`ingest_domestic.py`、`audit_readiness_20260719.py` |

---

## 3. 已完成工作（按主题）

### 3.1 早期基线与页界（0719 前半 + Phase0/1）

- R1：1941 成立宣言 PDF 第 38 页下一件更正为《对时局主张纲领》（非 1944/1945 纲领）
- R2：政治报告本地页图 101—117 齐全（含 111—116）
- 组织规程 L2 accepted（PDF 124—127）
- 政治报告 L2 accepted（MMHIST 101—117）

### 3.2 汇编与互证

| 材料 | 说明 | 等级 |
|---|---|---|
| 1983《历史文献》MMHIST | 核心文件页界已核 | L2 accepted 多条 |
| 1946《民主同盟文獻》NLC416 + **NLC511 交替扫描** | 同书双数字化；政治报告正文仍缺 | L2 / 缺口 L3 |
| **时事研究社《中国民主同盟言论集》** | 政治报告 PDF **19—36**（体文 20—36）；宣言 **14—19**；与 MMHIST 同文双源 | **L2 accepted**（整本+报告+宣言） |

言论集 PDF：  
`data/domestic/sourcebooks/NLC511-027032016010761-42571_中国民主同盟言论集.pdf`  
SHA256：`386faf360e73fd31e39d1f0a584877dddc76855f0d0be6157e01e06ac4234ef1`  
页图：`work/domestic/yanlunji_1945_pages/`

**明确：** 言论集/MMHIST **≠ 1945 原件**；**不填** 1946 文獻「代表大会政治报告」正文硬缺口。

### 3.3 《光明報》高密度文章级（重点）

| 卷期 | 状态 |
|---|---|
| 1946 新一—十一等 | 大量文章级 L1；部分 accepted |
| **NLC 72818**（文件名写 12 期） | 封面实为 **新二十號 1947-01-08**；文章级 **11/11 accepted**；ID 仍含 `1947-12` 字符串（历史命名，日期字段已纠正） |
| **新二十二號 1947-08-01** 邹李闻陶特辑 | 相关 **23/23 accepted** |
| 新十三—十八、二十一 | **+19** 文章 L1/`needs_human_review`；**封面日期已按实物校正为 1–5 月序列**（勿改回 8–10 月误读） |

#### 1947 中期封面日期（以实物为准）

| 期 | document_date |
|---|---|
| 新十三 | **1947-01-18** |
| 新十四 | **1947-01-28** |
| 新十五 | **1947-02-08** |
| 新十六—十七 | **1947-03-18** |
| 新十八 | **1947-05-14** |
| 新二十一 | 1947-07-05 |

页图：`work/domestic/continue_pages/1947_{13,14,15,16-17,18,21,22}/` 与 `1947_12/`（实为新二十 01-08）。

### 3.4 事件挂接

- 九事件全量补挂一轮；1949 经**激进瘦身** 173→171→**167**（保留 SAAC L1 + 1949 光明报 + 1 条 L4）
- 李闻 / 1947 事件引用显著增加（特辑与中期文章）

### 3.5 Cheer-only P0（模板就绪，**未代发函**）

| 文件 | 用途 |
|---|---|
| `work/domestic/cheer_P0_dual_launch_20260719.md` | **双路径一页总册（优先读）** |
| `work/domestic/cheer_action_hku_microform_20260719.md` | 港大缩微执行清单 |
| `work/domestic/cheer_action_shac_1354_20260719.md` | 二史馆 1354 执行清单 |
| `work/domestic/hku_guangmingbao_1941_request_template_20260719.md` | 港大邮件模板 v2.1 |
| `work/domestic/shac_1354_request_template_20260719.md` | 二史馆模板 v1.1 |
| `work/domestic/cheer_only_queue_20260719.md` | 6 件 cheer-only 总表 |

港大邮箱：**`libspeco@hku.hk`**；索书号 **`HKC 951 G91 M`**。

---

## 4. 硬缺口（全部仍 OPEN）

| ID | 目标 | 最强现证 | 下一步 |
|---|---|---|---|
| B1 | 1941-10-10/16 香港《光明報》原刊 | 港大缩微 L2 馆藏 | cheer 港大预约 |
| B2 | 1946《民主同盟文獻》政治报告**正文** | 双扫描目录错位 L3 卡 | 他书/馆藏；言论集**不填**此缺口 |
| B3 | 1947-10-27 内政部公函/公报原页 | 汇编 L2 + 公报 2963–2966 负向 | 二史馆 1354 |
| B4 | 1947-11-06 总部解散独立印本 | 汇编 L2 + 报纸互证 | 二史馆/民盟档案 |
| B5 | 1947-11-04 北平《新民报》原版 | 《观察》重刊 ≠ 原版；L4 出处 | 孔夫子/校史馆 |

缺口卡示例：

- `domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap`（L3）
- `domestic:MMHIST:league-banned-1947-10-27`（L2）
- `domestic:MMHIST:league-dissolution-announcement-1947-11-06`（L2）
- `domestic:GXMM:xinminbao-professors-statement-1947-11-04`（L4）

---

## 5. 关键纠错记忆（勿回退）

1. **NLC404-01J000514-72818**：文件名「12期」误导 → 封面 **新二十號 / 1947-01-08**；与 `10459`（另 SHA、另登记 6 月新二十）是**不同文件**。  
2. **新十三–十八** 旧登记 8–10 月为误读 → 已改为 **1–5 月**（见上表）。  
3. 新二十二社论正式题名：**《為爭取基本的人權而奮鬥》**，页界 **PDF 2—3**。  
4. `accepted` = 记录身份/页位/目录入口通过 **≠** 原件 provenance / 全文转录 / 权利闭环。  
5. 禁止：OCR/目录/后期盟史网页升 L1 原件；猜测页码作者；`git reset --hard`；自动 commit 密钥。

---

## 6. 报告索引（必读顺序）

### 总览

1. **本文件** `CLAUDE_CODE_HANDOFF_20260719.md`  
2. `FINAL_HANDOFF_20260719.md`（更早收口，基线已过时，仅作历史）  
3. `cheer_P0_dual_launch_20260719.md`（馆藏启动）  
4. `docs/domestic/阶段性Review_20260718.md`（末段有各波摘要）

### 分波多智能体

| 文件 | 内容 |
|---|---|
| `multiagent_task_graph_20260719.md` | 第一波任务图 |
| `multiagent_wave2_20260719.md` | 抽检/瘦身 |
| `multiagent_wave3_123_parallel_20260719.md` | issue22 + 1949 + P0 |
| `multiagent_wave4_continue_20260719.md` | issue22 全 accept + 72818 + 言论集 |
| `multiagent_wave5_123_parallel_20260719.md` | 言论集 accept + 中期 19 文 + dual launch |

### 专项 subagent 报告（抽样）

- `subagent_1947_issue22_articles_20260719.md` / `*_sample2_*` / `*_remaining_sample_*`  
- `subagent_1947_issue12_articles_20260719.md` / `subagent_72818_articles_sample_20260719.md`  
- `subagent_1947_mid_issues_split_20260719.md`  
- `subagent_yanlunji_crosswalk_20260719.md` / `subagent_yanlunji_accept_review_20260719.md`  
- `subagent_hard_gap_probe_20260719.md`  
- `subagent_event_link_audit_20260719.md`  
- `subagent_1949_event_aggressive_slim_20260719.md`  
- `subagent_l1_accept_queue_20260719.md` / `subagent_page_boundary_sample_20260719.md`

### Sprint38 分阶段

`sprint38_phase1_*.md` … `sprint38_phase5_closeout_20260719.md`

---

## 7. 建议 Claude Code 下一轮任务（按 ROI）

### P0（质量）

1. **抽检** 新十三–十八、二十一的 **19 条** `needs_human_review` 文章 → 通过则记录级 accept（模式同 issue22）。  
2. 抽检报告写到 `work/domestic/claude_mid1947_accept_sample_YYYYMMDD.md`。  
3. 每阶段结束跑 §1 校验四件套。

### P1（扩展）

4. 新十九 / 其他未拆 1946–47 期：仅题名清晰才拆。  
5. 1949 事件 167 是否再压（仅当你认为 SAAC 过宽）。  

### P0 cheer（原件）

6. 用户执行 `cheer_P0_dual_launch_20260719.md` 发港大 + 二史馆。  
7. 回传扫描后：新 L1 候选 + SHA256 + 页界；**不得**把未到手的原件写成已取得。

### 不要做

- 把 L4/汇编自动升 L1 原件  
- 回退 72818 / 新十三–十八 的封面日期纠正  
- 删除用户已有文件 / 提交密钥  
- 为「闭环」猜测 1947 公函页码  

---

## 8. 候选字段与 accept 约定

- 状态字段：`review_status` ∈ `needs_human_review` | `accepted` | …  
- 证据：`authenticity_level_proposed`（L0–L4, LX）；accept 时写 `authenticity_level_accepted`  
- 枚举必须过 `validate_candidates.py`（勿自造 `secondary_review` 等非法 enum）  
- 本地路径写在 `evidence_locator`，审计用正则抓 `data|work|index` 下文件  

记录级 accept 文案模板（中文）：

```text
通过记录级同期原刊/汇编影像审核：题名、日期、页界与本地页图已核对；
accepted 只表示记录身份和页级入口通过，不表示全文逐字转录、异文整理或复制权利已经完成。
```

---

## 9. 工具环境备注（给 Claude Code 机器）

| 工具 | 状态 |
|---|---|
| `python3 scripts/domestic/*` | 主校验链路 |
| Grok `spawn_subagent` | 仅 Grok TUI 会话内 |
| `minimax` CLI（MiniMax Code） | 本机曾坏链；且用户称**无额度** |
| `mmx`（Homebrew MiniMax API CLI） | 本机可用（`mmx text chat` 等），**非**完整 coding agent |
| Claude Code | 本交接目标环境 |

---

## 10. 交接确认清单

接手后请勾选：

- [ ] 四校验全过，数字与 §1 一致或可解释增量  
- [ ] 读过硬缺口 §4 与 P0 dual launch  
- [ ] 知悉 72818 = 新二十 1947-01-08；中期期号 1–5 月日期表  
- [ ] 知悉 issue22 特辑与 72818 卷文章已基本 accepted  
- [ ] 下一项任务从 §7 P0 抽检 19 条中期文开始（或用户另指定）  

---

## 11. 总结论

**已完成：** 可重复校验的国内库、高密度 1946–48 光明报文章级、李闻特辑与 1947-01 新二十整卷 accept、言论集/MMHIST 双源 L2、事件挂接、cheer P0 发函包。  

**未完成：** 五项原件硬缺口；19 条中期新文待抽检 accept；schema 6 字段 backlog；部分 ID 命名历史包袱（`1947-12-*` 实为新二十）。  

**Claude Code 可直接开工，无需重复 Phase0 基线建设。**
