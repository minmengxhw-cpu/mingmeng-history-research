# MiniMax 阶段0接管审计

审计日期：2026-07-19（Asia/Shanghai）  
执行方：Grok（按 `docs/domestic/Minimax分阶段执行交接_20260719.md` 阶段0任务）  
审计范围：当前候选、来源、事件覆盖、SQLite、关键页界与 Git 脏状态  
约束：只报告事实和风险；**不改变候选状态、不新增候选、不覆盖用户已有数据文件**

## 一、基线核对

| 指标 | 交接期望 | 实测 | 结果 |
|---|---:|---:|---|
| 来源（source_registry） | 87 | 87 | 通过 |
| 候选总数 | 337 | 337 | 通过 |
| `candidate_id` 唯一 | 337 | 337 | 通过 |
| `accepted` | 152 | 152 | 通过 |
| `needs_human_review` | 185 | 185 | 通过 |
| 事件数 | 9 | 9 | 通过 |
| 事件悬空候选引用 | 0 | 0 | 通过 |
| 建议证据等级 L1/L2/L3/L4/LX | 242/46/7/38/4 | 242/46/7/38/4 | 通过 |
| SQLite 来源/候选/编辑决策 | 87/337/337 | 87/337/337 | 通过 |
| SQLite pending_review | 185 | 185 | 通过 |
| 必填字段缺失 | 0 | 0 | 通过 |
| 定位声明但本地不存在的文件 | 0 | 0 | 通过 |

字段说明：状态字段为 `review_status`；证据等级字段为 `authenticity_level_proposed`。  
已接受记录中 `authenticity_level_accepted` 分布：L1 147、L2 5（仅记录级接受，不等于原件/全文闭环）。

### 验证命令输出（2026-07-19 实测）

```text
validate_candidates:
{"records": 337, "failed": 0, "passed": 337}

validate_event_coverage:
{"candidate_ids": 337, "events": 9, "missing_candidate_references": [],
 "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}

ingest_domestic:
{"domestic_sources": 87, "domestic_candidates": 337, "pending_review": 185,
 "editorial_decisions": 337}

audit_readiness_20260719:
{"records": 337, "missing_required": 0, "missing_paths": 0,
 "accepted_records": 152,
 "report": ".../docs/domestic/收口审计_20260719.md"}
```

`git diff --check`：无输出（通过）。

### 事件引用计数（`domestic_candidate_ids`）

| event_id | 引用数 |
|---|---:|
| domestic-1941-formation | 7 |
| domestic-1944-reorganization | 11 |
| domestic-1945-first-congress | 17 |
| domestic-1946-pcc | 21 |
| domestic-1946-refuse-national-assembly | 17 |
| domestic-1946-li-wen | 12 |
| domestic-1947-illegal-dissolution | 46 |
| domestic-1948-third-plenum-may-day | 8 |
| domestic-1949-new-pcc | 9 |

## 二、Git 脏状态（接管时）

分支：`main`（HEAD `60b569f feat: 香港报刊开放源登记 /hk-press`）  
`git status --porcelain` 约 14 行，主要为：

**已跟踪修改（与 domestic 主数据无直接关系，勿覆盖）：**

- `app.py`、`key_events.py`
- `data/first_person_acquisition.csv`、`data/hk_press_sources.csv`、`data/l1_upgrade_queue.csv`
- `scripts/ingest/ingest_drnh_images.py`

**未跟踪（国内资料库主体，全部未入库 Git）：**

- `data/domestic/`（含 candidates、source_registry、event_coverage、扫描 PDF）
- `docs/domestic/`、`scripts/domestic/`、`prompts/`、`work/`
- 另有 `data/mingmeng_corpus_data_20260713.tar.gz`、PRD 与协作计划文档

风险：国内资料库成果目前几乎全部在 untracked 树中；阶段执行不得 `git reset --hard`、不得删除用户已有文件、不得自动 commit。

## 三、关键页界目视抽查

本地页图目录与交接一致：

- `work/domestic/mmhist_formation_1941_pages/`
- `work/domestic/mmhist_platform_1945_pages/`
- `work/domestic/mmhist_congress_1945_pages/`

源 PDF：`data/domestic/sourcebooks/中国民主同盟历史文献_1941-1949_公开扫描.pdf`（存在，约 18.1 MB）。

### 3.1 已接受 L2：1941《中国民主政团同盟成立宣言》

| 项 | 结果 |
|---|---|
| candidate_id | `domestic:MMHIST:formation-declaration-1941` |
| review_status | `accepted` / L2 |
| PDF 第35页 | 标题《中国民主政团同盟成立宣言》，日期一九四一年十月十日；书内第5页 |
| PDF 第37页 | 宣言正文收束（「国人其惠教之」）；书内第7页 |
| PDF 第38页（边界） | **见风险 R1** |

### 3.2 已接受 L2：1945《中国民主同盟纲领》

| 项 | 结果 |
|---|---|
| candidate_id | `domestic:MMHIST:platform-1945` |
| review_status | `accepted` / L2 |
| PDF 第96页 | 标题《中国民主同盟纲领》，「一九四五年十月临时全国代表大会通过」；书内第66页 |
| PDF 第100页 | 妇女章末，正文结束；书内第70页 |
| PDF 第101页 | 转入《中国民主同盟临时全国代表大会政治报告》；书内第71页 |

页界与候选 `evidence_note` **一致**。

### 3.3 待复核 L2：1945 政治报告

| 项 | 结果 |
|---|---|
| candidate_id | `domestic:MMHIST:political-report-1945` |
| review_status | `needs_human_review` / L2（未写 `authenticity_level_accepted`） |
| PDF 第101页 | 报告首页，日期一九四五年十月十一日；书内第71页 |
| PDF 第117页 | 报告收束（「把中国造成一个十足道地的民主国家」）；书内第87页；**未进入宣言** |
| PDF 第118页 | 已是《临时全国代表大会宣言》起页；书内第88页 |

**政治报告截止第117页：确认。** 第118页不属于政治报告。

本地页图缺口：`mmhist_platform_1945_pages/` 有 page-096—110 与 page-117，**缺 page-111—116**。端点（101、117）与下界（118）已核；连续中间页本地影像未齐（风险 R2）。

### 3.4 已接受 L2：1945 临时全国代表大会宣言

| 项 | 结果 |
|---|---|
| candidate_id | `domestic:MMHIST:congress-declaration-1945` |
| review_status | `accepted` / L2 |
| PDF 第118页 | 标题《中国民主同盟临时全国代表大会宣言》，日期一九四五年十月十六日 |
| PDF 第123页 | 以「谨此宣言」收束；书内第93页 |
| PDF 第124页 | 转入《中国民主同盟组织规程》；书内第94页 |

页界与候选 **一致**。

## 四、风险与异常（不改数据，仅登记）

### R1 — 1941 成立宣言「下一件」题名写错（高）

目视 `work/domestic/mmhist_formation_1941_pages/page-038.png`：

- 实际标题：**《中国民主政团同盟对时局主张纲领》**
- 实际日期：**一九四一年十月十日**
- **不是**「1944 年纲领」，也**不是**「《中国民主同盟纲领》」

但下列文本把第38页写成错误下一件：

1. 候选 `domestic:MMHIST:formation-declaration-1941` 的 `evidence_note`：  
   「第38页已转入下一份《中国民主同盟纲领》」
2. 交接文件 `docs/domestic/Minimax分阶段执行交接_20260719.md` 第二节：  
   「PDF 第38页转入下一件 1944 年《纲领》」
3. 本目录下旧版阶段0报告（此前 MiniMax-M3 草稿）亦沿用错误表述

**影响：** 成立宣言正文页界 35—37 本身仍正确；错误在「边界下一件」元数据。  
**阶段0处理：** 不改正候选、不改交接文档（避免与「只报告、不改状态」冲突）；建议 Codex/后续阶段在人工确认后修正 `evidence_note` 与交接文案。

### R2 — 政治报告本地中间页图不齐（中）

候选声称 PDF 第101—117 连续核读，但本地只缓存 101—110 与 117。端点与第118页边界已目视确认；若需独立复查连续中间页，应补导 page-111—116，或直接打开源 PDF。

### R3 — 旧版阶段0报告基线过时（中）

磁盘上原 `minimax_phase0_audit_20260719.md` 写 accepted=150、needs_human_review=187，与当前 152/185 不一致，且含错误的第38页表述。**本文件已按当前实测覆盖重写**，不新增候选、不改 `candidates.jsonl`。

### R4 — accepted 语义边界（持续）

`accepted` = 记录身份/页位/目录入口审核通过。  
**不得**自动解读为：原件 provenance 完成、全文逐字转录完成、异文整理完成、复制权利闭环。  
当前 L1 242 条同样表示「有原刊/档案影像或接近原件的直接影像证据」，不等于权利与全文闭环。

### R5 — 核心原件硬缺口（阶段1—3 输入，非阶段0阻塞）

与交接及 `阶段性Review` 一致，仍待取得：

1. 1941-10-10/16《光明報》成立相关原刊  
2. 1944 全国代表会议原件 / 改组正式文件原载体  
3. 1945 政治报告与组织规程同期印本（现有为 1983 汇编 L2）  
4. 1947-10-27 内政部非法化原始公函/同期官方公报原页  
5. 1947-11-06 总部解散公告独立原始印本  
6. 1947-11-04 北平《新民报》教授联署声明原版  

## 五、本阶段未执行事项（刻意）

- 未修改 `data/domestic/candidates.jsonl` / `source_registry.json` / `event_coverage.json`
- 未新增、删除、合并任何 `candidate_id`
- 未将任何 `needs_human_review` 改为 `accepted`
- 未把汇编记录升级为「原件」
- 未提交 Git、未运行破坏性 git 命令
- 未进入阶段1检索/下载

`ingest_domestic.py` 仅做幂等同步，实测数字与交接一致，无额外候选写入迹象。

## 六、阶段0完成标准对照

| 标准 | 结果 |
|---|---|
| 基线数字一致 | **通过**（87 / 337 / 152 / 185 / 9 事件 / L 分布一致） |
| 政治报告截止第117页 | **通过**（目视 117 收束，118 为宣言） |
| 没有重复新增候选 | **通过**（337 唯一 ID，未改写候选文件） |

## 七、结论与建议下一步

阶段0接管审计**完成**。当前仓库国内主数据与交接基线一致，校验与入库链路可重跑；政治报告页界端点正确。

**进入阶段1前建议用户确认：**

1. 是否授权 Codex/下一阶段修正 R1（成立宣言第38页下一件题名）——属元数据纠错，不是证据升级。  
2. 是否补导政治报告 page-111—116 本地页图（R2）。  
3. 确认阶段1仅追索 1941—1945 原始载体，且不得用 1983/1946 汇编冒充原刊。

建议调用顺序保持：阶段0（本报告）→ 用户确认 → 阶段1。

## 八、阶段0后续并行处理状态（2026-07-19）

- **R1**：已在候选 `domestic:MMHIST:formation-declaration-1941` 与交接文件中更正第38页下一件为《对时局主张纲领》（1941-10-10）。
- **R2**：已补导 `mmhist_platform_1945_pages/page-111.png`—`page-116.png`，政治报告本地 101—117 齐全。
- 详见 `work/domestic/minimax_phase1_1941_1945_pursuit_20260719.md`。

