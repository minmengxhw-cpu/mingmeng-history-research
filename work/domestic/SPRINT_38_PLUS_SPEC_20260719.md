# Sprint 38+ Spec — 5 阶段接力规划

落档日期：2026-07-19 10:43 (Asia/Shanghai)  
项目：`/Users/cheer/Documents/mm agent/mingmeng-history-research`  
接力来源：cheer 10:43 5 阶段指令  
接力方：Mavis (root) 派 minimax worker + Grok pre-flight  
边界：mavis 不发函 / 不登录 / 不付费；阶段执行守死红线（见 §6）

---

## 0. 一句话总览

**sprint 38+ = 5 阶段接力, 严格分阶段, 每阶段输出 5 件, 守死 6 件红线。**  
**前置基线（0718-0719 freeze）：345 候选 / 160 accepted / 185 pending / 9 事件 / 87 来源 / 1+8 pair。**  
**A 层 9 项检查全过；B 层 5 件硬缺口仍 OPEN。**

---

## 1. cheer 5 阶段指令（原文摘要 + 索引标注）

| 阶段 | 范围（cheer 原文） | 跟 monitor B 层映射 | 跟事件时间映射 | 索引一致性 |
|---|---|---|---|---|
| 1 | 1941—1945 成立及早期活动一手资料 | 包含 B1 (1941 光明报) + 部分 1944 + 部分 1945 | ✅ 时间一致 | ✅ |
| 2 | 1946 报刊文章（按标题/作者/日期/版面边界拆分） | 包含 B4 (1946 民主同盟文献 政治报告) | ✅ 时间一致 | ✅ |
| 3 | "1947 年的五个硬缺口" | 列出 B1 / B4 / B5 / B6 / B7 | ⚠️ **不一致**：B1 (1941) 和 B4 (1946) 不属于 1947 年 | ⚠️ |
| 4 | 1948—1949 民盟活动资料 | 不在 B 层硬缺口（已有 pair_available 1948 三中 + 部分 1949） | ✅ 时间一致 | ✅ |
| 5 | 入库 + 校验 + 审计 | 全部 B 层 | ✅ 收口 | ✅ |

### 1.1 cheer 阶段 3 索引不一致 — 三种处理方式（cheer 拍）

| 选项 | 处理 | 优 | 缺 |
|---|---|---|---|
| A | 按 cheer 原文执行（B1+B4+B5+B6+B7 都在阶段 3） | 不擅自改 cheer 指令 | 跟"按时间归类"原则冲突 |
| B | 按时间归类（B1 → 阶段 1, B4 → 阶段 2, 阶段 3 = B5+B6+B7） | 时间线清晰 | 改了 cheer 原文 |
| C | 阶段 3 包含 B5/B6/B7 主追查, 阶段 1/2 同步追查 B1/B4 历史硬缺口 | 时间线 + 完整性兼顾 | 跨阶段协调 |

**建议选项 C**（cheer 拍板）。

---

## 2. sprint 38+ 阶段执行规约（cheer 指令原文）

### 2.1 角色分工

- **MiniMax**：主执行。负责搜索、获取、整理、候选记录、报告。
- **Grok**：独立复核。负责交叉搜索、来源等级判断、负面检索、质量审查。
- **mavis (Mavis)**：中介。负责派 worker、接收回报、校验、收口。
- **Codex**：每阶段末独立审核（沿 sprint 36+ / 0719 模式）。
- **cheer**：每阶段启动 / 收口 拍板。

### 2.2 严格分阶段（cheer 红线）

> "严格分阶段执行，不要一次性改完整个项目"

- 每阶段独立 worker 跑，独立报告
- 不跨阶段合并写报告
- 阶段 5 (入库) 是最后一步，**不**在其他阶段做 SQLite 同步

### 2.3 每阶段必输出 5 件（cheer 红线）

1. `work/domestic/` 下的阶段报告
2. 新增或修改的候选记录
3. 已检索但未找到的来源及检索范围
4. 来源 URL、访问日期、本地路径、SHA256、页码和证据等级
5. 校验命令及完整结果

### 2.4 6 件禁止（cheer 红线 — 守死）

- ❌ 把 OCR、目录、后人叙述当作原始一手证据
- ❌ 凭推测补日期、作者、页码
- ❌ 删除既有资料
- ❌ 覆盖用户数据
- ❌ 提交密钥、Token 或隐私
- ❌ 未经核验把 `needs_human_review` 改成 `accepted`

---

## 3. 5 阶段 MECE 任务清单

### 3.1 阶段 1：1941—1945 一手资料

**目标：** 补齐 1941 成立 / 1944 改组 / 1945 一大 的一手原刊 / 同期印本。

**当前状态：**
- 候选 7+11+19=37 件（1941-formation 7 / 1944-reorganization 11 / 1945-first-congress 19）
- pair_partial（8 事件中包含 1941/1944/1945 三个 pair_partial）
- 1983 汇编 L2 已 accepted（成立宣言 / 纲领 / 政治报告 / 组织规程 / 宣言）
- 1946 民盟总部《民主同盟文獻》L2 needs_human_review（多个文件级候选）
- 民憲多期 L1 整期 needs_human_review
- B1 (1941 光明报原刊) OPEN — 唯一公开网外来源是港大缩微

**MiniMax 主执行：**

| 任务 | 现有候选 ID | 期望动作 |
|---|---|---|
| 1.1 港大缩微预约配合 (cheer 启动后) | `domestic:HKU:guangmingbao-1941-microform-holdings` L2 | cheer 启动后 mavis 配合接收回报 |
| 1.2 1946 民盟总部《民主同盟文獻》文章级拆分 | `domestic:NLC:minmeng-wenxian-1946-whole` L2 | 拆分 1941 成立宣言 / 对时局主张纲领 文章级（PDF 9-13） |
| 1.3 民憲多期 文章级拆分 | `domestic:NLC:minxian-v1n10-1944-12-20` 等 L1 整期 | 拆分代表性文章（已拆 v1n9 民主政治 vs 非民主政治 + 1944-11-20） |
| 1.4 1983 汇编 1941 成立 + 对时局主张纲领 同期印本搜索 | `domestic:MMHIST:formation-declaration-1941` L2 accepted | 公开网 + 馆际互借 同步搜索 1941 同期印本 |
| 1.5 1944 全国代表会议原始文件搜索 | （无候选） | 公开网 + 校史馆 + 民主党派历史陈列馆 同步搜索 |
| 1.6 1945 同期印本搜索（政治报告 / 组织规程 / 宣言 / 纲领） | L2 已 accepted | 公开网同步搜索 |

**Grok 独立复核：**
- 交叉搜索 minimax 漏检的来源
- 复核每条新增候选的等级判断（L0/L1/L2/L3/L4/LX）
- 负面检索：每条"未找到"结论的可复查性
- 契约审查：每条新候选 schema 合规

**Codex 审核：**
- 阶段末独立审核新候选接受 / 维持
- 复检 R1 (1941 成立第38页边界) / R2 (政治报告 page-111—116) 仍正确

**mavis 配合：**
- 派 minimax worker (1 件 worker, 1 阶段)
- 派 Grok pre-flight (1 件 worker, 1 阶段)
- 收 Codex 审核
- 写 `work/domestic/sprint_38_phase1_report_2026MMDD.md` 阶段报告
- 跑校验 5 步

**cheer 拍板：**
- 启动阶段 1 (minimax 接力)
- 启动港大缩微预约（chear-only 接力 1）

---

### 3.2 阶段 2：1946 报刊文章拆分

**目标：** 1946 报刊文章按标题 / 作者 / 日期 / 版面边界拆分；补齐 1946 民主同盟文献政治报告正文（B4）。

**当前状态：**
- 候选 23+18+14+21+1=77 件（1946-pcc 23 / 1946-refuse-national-assembly 18 / 1946-li-wen 14 / 1946 旧政协 21 / 等等）
- pair_partial（1946-pcc / 1946-refuse-national-assembly / 1946-li-wen）
- 1946 光明报新一-十号整期 L1 needs_human_review（部分已 article-level L1 accepted: 新五/新九/新十/新三拆 L1 待止页）
- 1946 民主同盟文献 多文件级候选 L2 needs_human_review（含政治报告 toc-gap L3 硬缺口卡）
- B4 (1946 民主同盟文献政治报告正文) OPEN — 公开网无, 1946 汇编印刷页 49 = 纲领正文, 目录错位

**MiniMax 主执行：**

| 任务 | 现有候选 ID | 期望动作 |
|---|---|---|
| 2.1 1946 光明报新一/二/四/七/八号 文章级拆分 | 5 件 L1 整期 | 文章级 L1（题名 / 作者 / 起止页） |
| 2.2 1946 光明报新三号 止页完成 | `domestic:NLC:guangmingbao-1946-issue03-double-ten-task-article` L1 待止页 | 找止页, 完成拆 L1 accepted |
| 2.3 1946 光明报新六号 OCR 提升后题名拆分 | `domestic:NLC:guangmingbao-1946-issue06` L1 整期 | OCR 提升, 题名确定后拆 L1 |
| 2.4 1946 民主同盟文献 政治报告正文互校（B4） | `domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap` L3 硬缺口卡 | 1946 汇编其他渠道互校 / 1983 汇编同章节 / 二史馆政治报告 |
| 2.5 1946 旧政协其他报刊同期报道 | （无候选） | 公开网搜索《文汇报》《大公报》《新华日报》《申报》同期报道 |
| 2.6 1946 拒国大其他报刊报道 | （无候选） | 公开网搜索 |
| 2.7 1946 李闻事件其他报刊报道 | （部分候选） | 公开网搜索 + 《观察》3卷11期文章级拆分 |

**Grok 独立复核：**
- 每条新增文章级候选的题名 / 作者 / 日期 / 起止页 交叉验证
- 等级判断交叉搜索

**Codex 审核：**
- 阶段末独立审核文章级 L1 接受

**mavis 配合：**
- 派 minimax worker
- 派 Grok pre-flight
- 收 Codex 审核
- 写 `work/domestic/sprint_38_phase2_report_2026MMDD.md` 阶段报告
- 跑校验 5 步

**cheer 拍板：**
- 启动阶段 2

---

### 3.3 阶段 3：1947 五件 B 层硬缺口（按 cheer 原文）

**目标：** 1947 五件 B 层硬缺口（B1 + B4 + B5 + B6 + B7）分项独立追查。

**当前状态：**
- 候选 47 件 (1947-illegal-dissolution)
- pair_partial（核心难点）
- 1983 汇编 L2 (B5 解散公告 + B6 宣布非法)
- 1946 民盟总部《民主同盟文獻》 L2/L3 needs_human_review
- 上海/天津/汉口版 1947-11-06 第 2 版 完整原刊影像（低清试用导出）
- B1 / B4 / B5 / B6 / B7 全部 OPEN

**MiniMax 主执行（按 cheer 原文 5 件分项独立）：**

| 任务 | 现有候选 ID | 期望动作 |
|---|---|---|
| 3.1 B1 1941 光明报原刊（cheer 指令） | `domestic:HKU:guangmingbao-1941-microform-holdings` L2 | cheer 启动港大缩微预约 + mavis 配合（跨阶段 1） |
| 3.2 B4 1946 民主同盟文献 政治报告正文（cheer 指令） | `domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap` L3 | 1946 汇编其他渠道互校 + 1983 同章节 + 二史馆政治报告（跨阶段 2） |
| 3.3 B5 1947-10-27 内政部非法化公函 | `domestic:MMHIST:league-banned-1947-10-27` L2 | cheer 启动二史馆函调 + mavis 配合 |
| 3.4 B6 1947-11-06 总部解散公告独立印本 | `domestic:MMHIST:league-dissolution-announcement-1947-11-06` L2 | cheer 启动二史馆函调 + 张澜时代日报 L4 出处线索（不同件, 独立） |
| 3.5 B7 1947-11-04 北平《新民报》原版 | `domestic:GXMM:xinminbao-professors-statement-1947-11-04` L4 | cheer 启动孔夫子询价 + 校史馆函调 + NLC 视检《新民报》1947-11-04 |

**Grok 独立复核：**
- 每项 B 层硬缺口的可复查性（cheer 跑外部 + mavis 跑公开网）
- 等级判断交叉搜索

**Codex 审核：**
- 阶段末独立审核（如有 cheer 跑回结果, mavis 登记后 codex 接受 / 维持）

**mavis 配合：**
- 派 minimax worker (5 项分项, 每项独立 worker)
- 派 Grok pre-flight (1 件)
- 收 Codex 审核
- 写 `work/domestic/sprint_38_phase3_report_2026MMDD.md` 阶段报告
- 跑校验 5 步

**cheer 拍板：**
- 启动阶段 3
- 启动 5 项 cheer-only 接力 (港大缩微 / 二史馆函调 / NLC 视检 / 孔夫子询价 / 校史馆函调)

---

### 3.4 阶段 4：1948—1949 民盟活动资料

**目标：** 补齐 1948 三中全会 / 五一口号 / 1949 新政协筹备 / 第一届政协 / 开国大典。

**当前状态：**
- 候选 8+10=18 件 (1948-third-plenum-may-day 8 / 1949-new-pcc 10)
- **1948-third-plenum-may-day pair_available**（唯一闭环事件）
- 1948 光明报 v1n1/v1n12 / 1949 v2n1/v2n12 L1 整期 accepted
- 1949 v2n1 笔谈 / v2n12 和平态度 / 台湾解放 文章级 L1 accepted
- 五一口号 L4 已记录（需要原始印本 + 公开原稿核验）
- 第一届政协 L1 已记录（多文件级 + 共同纲领 L2）

**MiniMax 主执行：**

| 任务 | 现有候选 ID | 期望动作 |
|---|---|---|
| 4.1 1948 五一口号 原始印本搜索 | L4 已记录 | 公开网 + 二史馆 / 中央档案馆 |
| 4.2 1948 光明报 v1n1/v1n12 文章级拆分 | 2 件 L1 整期 accepted | 文章级 L1 |
| 4.3 1949 光明报 v2n1/v2n12 文章级拆分 | 2 件 L1 整期 + 3 文章级 accepted | 补齐剩余文章 |
| 4.4 1949 新政协筹备 同期报刊报道 | （部分候选） | 公开网搜索 |
| 4.5 1949 开国大典 同期原刊 / 影像 | （部分候选） | 公开网搜索 + 校史馆 |
| 4.6 1949 第一届政协 同期原刊 / 影像 | L1 已记录 | 补齐共同纲领 / 政协组织法 / 中央人民政府组织法 文章级 |

**Grok 独立复核：**
- 1948-1949 资料等级判断交叉搜索
- 公开网来源负面检索

**Codex 审核：**
- 阶段末独立审核文章级 L1 接受

**mavis 配合：**
- 派 minimax worker
- 派 Grok pre-flight
- 收 Codex 审核
- 写 `work/domestic/sprint_38_phase4_report_2026MMDD.md` 阶段报告
- 跑校验 5 步

**cheer 拍板：**
- 启动阶段 4

---

### 3.5 阶段 5：入库 + 校验 + 审计

**目标：** sprint 38+ 阶段 1-4 全部新候选 / 修改 走 ingest_domestic 同步到 SQLite；跑 5 步校验；写收口审计。

**边界：**
- ❌ 不删除既有数据
- ❌ 不覆盖用户数据
- ❌ 不擅自改 `needs_human_review` → `accepted`（必须 codex 审核 + cheer 拍板）

**MiniMax 主执行：**
- ❌ minimax 不跑 ingest（这步 mavis 跑）

**Grok 独立复核：**
- ❌ Grok 不跑 ingest（这步 mavis 跑）

**Codex 审核：**
- 阶段 1-4 全部新候选 / 修改 codex 统一审核
- 接受 8 件 / 维持 / 拆 L1 待止页（沿 0719 模式）

**mavis 配合：**
- 跑 ingest_domestic.py
- 跑 validate_candidates.py
- 跑 validate_event_coverage.py
- 跑 audit_readiness_20260719.py
- 跑 git diff --check
- 写 `work/domestic/sprint_38_phase5_report_2026MMDD.md` 阶段报告 (收口)
- 更新 `docs/domestic/收口审计_YYYYMMDD.md`
- 更新 `work/domestic/monitor_status_latest.json` (B 层 5 件状态)
- 更新 memory (跨 sprint 38+ reusable)

**cheer 拍板：**
- 启动阶段 5
- 收口拍板

---

## 4. sprint 38+ 5 阶段总体时间线（建议）

| 阶段 | 范围 | 预计耗时 | 阻塞依赖 |
|---|---|---|---|
| 1 | 1941-1945 | 1-2 周 (minimax) + cheer 港大 (4-6 周) | 港大 cheer 启动 |
| 2 | 1946 拆分 | 1-2 周 (minimax) | 无 |
| 3 | 1947 5 件 B 层 | 1-2 周 (minimax) + cheer 二史馆 (4-8 周) | 二史馆 / 孔夫子 / 校史馆 cheer 启动 |
| 4 | 1948-1949 | 1 周 (minimax) | 无 |
| 5 | 入库 + 校验 + 审计 | 1 天 (mavis) | 阶段 1-4 全部 codex 接受 |

**总预计：1-2 周 minimax 主执行（不依赖 cheer-only） + 4-8 周 cheer-only 接力（cheer 启动）**

---

## 5. cheer 拍板启动哪一阶段

| 选项 | 范围 | 适合 |
|---|---|---|
| A | 启动阶段 1 (1941-1945 minimax 接力) | cheer 港大还没启动, 但 minimax 可先做其他 1944/1945 任务 |
| B | 启动阶段 2 (1946 报刊文章拆分) | 已有新三/新六 待 OCR, 文章级拆分 ROI 高 |
| C | 启动阶段 1+2 并行 (minimax 2 worker) | 不推荐, 资源分散 |
| D | 启动阶段 3 (1947 5 件 B 层, 全部 cheer-only 配合) | 阻塞 5 件 cheer-only 接力 |
| E | 全部开跑 (阶段 1-4 并行) | 5 minimax worker + 5 cheer-only 接力, 跨 sprint 风险高 |
| F | 暂不启动, 收口 sprint 38+ spec 等 cheer 拍板 | 跟 cheer "等拍" 模式一致 |

**建议选项 A 或 B（cheer 拍板）。**

---

## 6. 6 件禁止（cheer 红线 — 守死）

- ❌ 把 OCR、目录、后人叙述当作原始一手证据
- ❌ 凭推测补日期、作者、页码
- ❌ 删除既有资料
- ❌ 覆盖用户数据
- ❌ 提交密钥、Token 或隐私
- ❌ 未经核验把 `needs_human_review` 改成 `accepted`

mavis 守死 + minimax worker prompt 必含 4 件（边界 / 验收清单 / close 边界声明 / report-back 格式）+ Grok 必含 4 件（交叉搜索 / 等级判断 / 负面检索 / 质量审查）。

---

## 7. 文件命名约定

```
阶段报告:  work/domestic/sprint_38_phase{N}_report_2026MMDD.md
候选文件:  data/domestic/candidates.jsonl  (追加, 不覆盖)
来源文件:  data/domestic/source_registry.json  (追加, 不覆盖)
事件文件:  data/domestic/event_coverage.json  (追加, 不覆盖)
校验输出:  work/domestic/sprint_38_phase5_validation_2026MMDD.md
收口审计:  docs/domestic/收口审计_YYYYMMDD.md  (更新, 不覆盖)
状态监控:  work/domestic/monitor_status_latest.{json,md}  (更新)
```

---

## 8. 跟 sprint 0718-0719 收口的关系

- sprint 0718-0719 已完成 A 层 9 项检查 + Grok 0718 ack 收口
- sprint 38+ 接力的是 B 层 5 件硬缺口 + 文章级 L1 拆分 + 6 字段 schema backlog
- sprint 38+ spec 落档后, monitor_status_latest 仍保持 `A_LAYER_COMPLETE=true, B_LAYER_OPEN=true`
- sprint 38+ 收口后, B 层 5 件可能仍 OPEN (如 cheer-only 接力未拍) — 监控不虚报闭环

---

## 9. 等 cheer 拍板

- 启动哪一阶段 (A / B / C / D / E / F)
- cheer 阶段 3 索引不一致 (5 件 B 层 vs 1947 三件) — 选项 A/B/C
- cheer-only 接力启动哪件 (6 件)
- sprint 38+ minimax 接力并发数 (1 / 2 / 3 — 3 并行是 daemon 临界点)

mavis 接到拍板后按 §3 阶段执行 + 写阶段报告。
