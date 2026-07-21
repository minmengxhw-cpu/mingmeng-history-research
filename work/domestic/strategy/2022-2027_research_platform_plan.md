# 民盟历史研究平台 2022-2027 长期规划

作者：mavis
落档日期：2026-07-22
适用项目：`/Users/cheer/Documents/mm agent/mingmeng-history-research`
基线日期：2026-07-21 (snapshot_20260721.md)
读者：cheer (项目主理人) / Codex (后续审核收口) / 未来接力团队

---

## 0. Executive Summary

**目标**：在现有海外研究平台基础上，加国内民盟 1941-1949 历史研究平台部分。所有资料必须**第一手**，可作为 5-10 年学术研究基础。

**当前状态 (0721 baseline)**：
- 689 candidates / 450 accepted (58.9%) / 239 pending
- 9 events 覆盖 (1 pair_available + 8 pair_partial)
- 13 个 accept/fix/demote/upgrade 脚本重构完成 (P0-1 ~ P3-14 共 14 个对抗式审查 bug 全修)
- 0 个 cheer-only P0 接力完成

**5 阶段路径 (2026 sprint 39 ~ 2027 sprint 50+)**：

| 阶段 | 目标 | 周期 | 工作量 |
|---|---|---|---|
| Phase 1: 闭环现状 | 消化 239 pending / 跑 5 件 P0 / 8 pair_partial → 闭环 | 2 周 | 10 人天 |
| Phase 2: 影像到全文 | OCR 流水线 + 1941-1947 关键事件 ≥80% 全文 | 3 周 | 20 人天 |
| Phase 3: 多源互证 | 8 events × 4 维度 = 32 个新候选采集验证 | 3 周 | 15 人天 |
| Phase 4: 平台化 | API + UI + 引用规范 + DOI | 2 周 | 15 人天 |
| Phase 5: 持续运营 | 3 镜像 + URL 监控 + 增量采集 | 持续 | 0.5 人天/周 |

**核心约束**：cheer-only 7 件 P0 接力是硬约束，mavis 不能替跑。1 个接力 2-3 周，7 件串行约半年。

**关键决策前置**：4 个问题（范围 / 深度 / 用户 / 可持续）需 cheer 拍板后再启动 Phase 1。

---

## 1. 第一性原理

### 1.1 研究平台 ≠ 数据

数据是原料 (raw)，平台是结构 + 治理 + 持久性的总和。

```
平台 = 数据 + 元数据 + 索引 + 引用 + 备份 + 维护
```

任何一项缺位都会让"研究基础"塌陷。

### 1.2 4 大属性 (第一手是必要不充分)

未来作为研究基础需要 4 个属性：

| 属性 | 含义 | 缺失后果 |
|---|---|---|
| **可发现 (Findable)** | 5 年后能通过关键词/事件/人物找到 | 资料沉没，搜寻效率归零 |
| **可引用 (Citable)** | 学术规范 (Chicago/MLA/BibTeX) + 元数据齐 + 永久 ID | 写论文无法引用，价值打折 |
| **可重现 (Reproducible)** | 别人顺着 citation 能拿到同一份资料 | 学术可验证性丢失，沦为博客 |
| **可持续 (Durable)** | 5/10/20 年后还在，URL 死了有备份 | 5 年后访问不到 = 历史档案变电子垃圾 |

**第一手 (primary source) 是必要条件**，但**不是充分条件**：

| 形态 | 可发现 | 可引用 | 可重现 | 可持续 | 是不是研究基础 |
|---|---|---|---|---|:---:|
| 第一手 + 单 URL | ✓ | ✓ | ✗ | ✗ | ✗ |
| 第一手 + 多镜像 + 元数据齐 + 引用规范 | ✓ | ✓ | ✓ | ✓ | ✓ |

### 1.3 "未来研究" 的真实需求

未来 5-10 年民盟 1941-1949 学术研究可能的方向：
- 制度史：民盟组织架构演变 / 与中共互动 / 改组前后对比
- 思想史：知识分子政治选择 (梁漱溟 / 张澜 / 闻一多 / 罗隆基) / 自由主义在 1940s
- 事件史：李闻惨案 / 1947 解散 / 1948 三中全会 / 1949 新政协
- 比较史：与农工 / 九三 / 民建 / 致公 / 民进 / 民革 / 台盟的同期对比
- 跨地域：海外 (FRUS / DRNH / Wilson / Hoover) vs 国内 (NLC / 二史馆 / 盟中央)

每条线都需要**原文 + 元数据 + 互证 + 索引**才能做。

---

## 2. 现状盘点 (0721 baseline)

### 2.1 数据基线

| 指标 | 数值 | 来源 |
|---|---:|---|
| candidates | 689 | `data/domestic/candidates.jsonl` |
| accepted | 450 (58.9%) | 0719 sprint 收口 201 + 0719-0721 增量 249 |
| pending | 239 (41.1%) | 需消化的主工作队列 |
| sources | 89 | 89 个独立来源 |
| events | 9 | 1 pair_available + 8 pair_partial |
| validation | 689/689 全过 | `validate_candidates.py` |
| audit | 0 missing_required / 0 missing_paths | `audit_readiness_20260719.py` |

### 2.2 等级分布

| 等级 | total | accepted | pending | 含义 |
|---|---:|---:|---:|---|
| L1 | 325 | 212 | 113 | 原档影像 (highest credibility) |
| L2 | 228 | 183 | 45 | 正式印本 / 影印件 / FRUS 官方 |
| L3 | 88 | 6 | 82 | 目录级 + 引用转录 |
| L4 | 44 | 5 | 39 | 衍生 / lead 文章 (secondary) |
| LX | 4 | 4 | 0 | 备选 |
| **合计** | **689** | **450** | **239** | — |

### 2.3 239 pending 画像 (按等级 × online 拆)

| level \ online | full_item | surrogate | catalogue | not_online | 合计 |
|---|---:|---:|---:|---:|---:|
| L1 | 12 | 101 | 0 | 0 | 113 |
| L2 | 9 | 32 | 4 | 0 | 45 |
| L3 | 8 | 1 | 58 | 15 | 82 |
| L4 | 29 | 3 | 6 | 1 | 39 |
| LX | 4 | 0 | 0 | 0 | 4 (已全清 0) |
| **合计** | **62** | **137** | **68** | **16** | **239** |

### 2.4 9 events 覆盖

| event_id | pair | 候选数 | 关键 gap |
|---|:---:|---:|---|
| 1941 成立 | partial | 13 | 港大缩微原档 (P0 接力 1) |
| 1944 改组 | partial | 22 | FRUS + NLC 1946 民盟文献汇编 |
| 1945 一大 | partial | 26 | NLC 1946 民盟文献 (P0 接力 3 NLC 视检) |
| 1946 政协 | partial | 28 | 1946-09-11 光明報新一至新六 (待完整性) |
| 1946 拒国大 | partial | 25 | 政协决议转录 + 正式汇编 L2 发言 |
| 1946 李闻 | partial | 39 | 闻一多衣冠冢 L1 (已有 9.79MB) + 3 校校史馆函调 (P1) |
| 1947 解散 | partial | 80 | 二史馆 1354 全宗 1947 内政部公函 (P0 接力 2) |
| 1948 三中全会/五一 | **available** | 19 | 唯一 pair_available，作模板 |
| 1949 新政协 | partial | 167 | 1948-1949 光明報代表性原刊 + 大会档案 |

### 2.5 工程能力现状

**已完成**:
- 13 个 accept/fix/demote/upgrade 脚本接 `_accept_lib` (commit `2aef6b0`)
- 14 个对抗式审查 bug 全修 (P0-1 ~ P3-14)
- 6 份工作笔记 + 4 份 codex 复审报告 + 1 份 0721 末态快照
- 6 件 cheer-only P0 模板 (港大 / 二史馆 / NLC 视检 / 孔夫子 / 3 校 / 民盟中央 3 处)
- `.gitignore` 屏蔽 526MB 影像 + 676MB tar.gz + 600MB work/ PNG

**未完成**:
- OCR 流水线 (影像到全文 = 0%)
- 全文检索 (FTS = 0%)
- 引用规范 (BibTeX/Chicago 模板 = 0)
- 永久 ID (DOI/handle = 0)
- 公网 UI/API (0)
- 3 镜像备份 (1 份 GitHub，2 份待建)

---

## 3. 5 阶段路径 (2026 sprint 39 ~ 2027 sprint 50+)

### Phase 1: 闭环现状 (sprint 39-40, ~2 周)

**目标**：把 689 候选从"种子"变"骨架"，完成 8 pair_partial events 中至少 5 个的 cheer-only 接力

**Sprint 39 (1 周)**:
1. 消化 239 pending：
   - L1 113 hybrid：批量 codex 抽检 (target 50% accept) → 30-50 新 accept
   - L2 45：codex 抽检 surrogate 32 + catalogue 4 → 10-15 accept
   - L3 79 (8 full + 58 catalogue - 1 not_online 改 L4 降级) + L4 39：codex 抽检 → 5-10 accept
   - 16 not_online → 标记 cheer-only
2. 跑 5 件 cheer-only P0 启动 (港大 / 二史馆 / NLC / 3 校 / 民盟中央 任选)
3. 元数据 schema 升 v2 (新字段：transcription_status / access_audit_date / citation_key)
4. 写 citation 模板 (BibTeX + Chicago + 民国规范 各 1 份)

**Sprint 40 (1 周)**:
1. 接收 5 件 cheer-only 回报 (cheer 跑馆内 / 函调)
2. 入库 + 升级 L3 → L2 / L2 → L1
3. 写"事件 × 等级"覆盖矩阵 (9 events × 4 levels = 36 cells)
4. 5 pair_available events 收口 (从 8 partial 降)
5. Phase 1 收口报告

**Phase 1 验收标准**:
- [ ] accepted ≥ 550 (从 450)
- [ ] pending ≤ 139 (从 239)
- [ ] 5 events pair_available (从 1)
- [ ] 5 件 cheer-only P0 启动 + 1 件完成
- [ ] schema v2 落地
- [ ] 引用模板 3 套

**工作量**: 1 人天/天 × 10 天 = **10 人天**

### Phase 2: 影像到全文 (sprint 41-43, ~3 周)

**目标**：L1 影像从"看图"变"全文检索"，1941-1947 关键事件 ≥80% 全文覆盖

**Sprint 41 (1 周) — OCR 流水线搭建**:
1. 选 OCR 工具栈 (候选: Tesseract 5 / PaddleOCR / 自训)
2. 搭 batch OCR 脚本 (input: PDF/PNG → output: text + position)
3. 人工校对工具 (按 page 校对，标注低置信度区段)
4. 优先队列: 1941 光明报 (10-10 / 10-16 / 10-28 期) → 1946 民盟文献汇编 → 1947 光明报全套

**Sprint 42-43 (2 周) — 转录执行**:
1. 1941 光明报 全 22 期 (已 NLC 扫描，1 期 ≈ 8 页 = 176 页)
2. 1946 民盟文献汇编 (NLC 416 卷) ≈ 400 页
3. 1947 光明报 全 22 期 ≈ 176 页
4. 1944 民憲 全 11 期 ≈ 88 页
5. 1948-1949 光明報 代表期 ≈ 100 页
- 总计: ~940 页 ≈ **10 人天 OCR + 10 人天校对**

**Sprint 43 末**:
1. 全文 → SQLite FTS5 索引
2. 简单 CLI 检索 (`mm-search "梁漱溟 1943"`)
3. 转录引用规范 (哪一页 / 哪一行 / OCR 置信度)

**Phase 2 验收标准**:
- [ ] OCR 流水线 端到端跑通
- [ ] 1941-1947 关键事件 全文覆盖 ≥ 80%
- [ ] 全文索引 (CLI) 可用
- [ ] 转录规范文档

**工作量**: ~**20 人天** (含 OCR 工具评估 + 流水线 + 转录 + 校对)

### Phase 3: 多源互证 + 横向扩展 (sprint 44-46, ~3 周)

**目标**：8 pair_partial events → 全部 pair_available，每个事件 ≥4 来源维度

**来源维度定义**:
1. L1 原档影像 (NLC / 二史馆 / 校史馆 / 盟中央印本)
2. L2 正式印本 (民盟文献汇编 / 1983 历史文献 / 同期原刊影印)
3. L3 目录级 (馆藏目录 / 同期报刊索引)
4. 外方档案 (FRUS / DRNH / Wilson / Hoover)

**Sprint 44-46 任务**:
- 8 pair_partial events × 4 维度 = 32 个新候选采集验证
- 优先: 1941 成立 (3 来源差 1) > 1944 改组 (差 1) > 1945 一大 (差 1) > 1947 解散 (差 2)
- 横向扩展: 8 民主党派同期资料 (民革 / 民建 / 民进 / 农工 / 致公 / 九三 / 台盟 各 1-3 候选)
- 横向: 知识分子 (闻一多 / 李公朴 / 梁漱溟 / 张澜 / 罗隆基) 私人档案

**Phase 3 验收标准**:
- [ ] 9 events 全部 pair_available
- [ ] 每事件 ≥ 4 来源维度
- [ ] 横向扩展 ≥ 24 个新候选 (8 党派 × 3)
- [ ] 知识分子档案 ≥ 5 个新候选

**工作量**: ~**15 人天** (采集 + 验证 + 互校)

### Phase 4: 平台化 (sprint 47-48, ~2 周)

**目标**：从"项目 repo"变"研究平台"，公网或内网可访问

**Sprint 47 (1 周) — API + UI**:
1. FastAPI / Flask 暴露 candidates / events / sources / fts 检索
2. Web UI: 时间线 + 事件 + 人物 + 全文检索
3. 公开 API 文档 (OpenAPI 3)

**Sprint 48 (1 周) — 学术化**:
1. BibTeX / Chicago / MLA 引用导出
2. Zenodo 镜像 → 申请 DOI
3. handle.net 申请 (如果 Zenodo 不够)
4. 集成 OpenAlex / Wikidata (linked open data)

**Phase 4 验收标准**:
- [ ] 公开 API 200 OK
- [ ] Web UI 时间线 + 事件 + 人物 + FTS 4 视图
- [ ] 3 套引用模板 (BibTeX/Chicago/MLA) 落地
- [ ] Zenodo DOI 申请 (每个 candidate 或每个 event)
- [ ] 镜像 backup ≥ 2 处

**工作量**: ~**15 人天** (含 UI 设计 + DOI 申请 + 元数据规范)

### Phase 5: 持续运营 (sprint 49+ , 0.5 人天/周)

**目标**：5/10/20 年后还在，且学术影响力持续

**每周 0.5 人天投入**:
1. URL 监控 (每月 webfetch 抽样 5% 候选，失效标记 + 备份补救)
2. 增量采集 (新文献 / 新档案 / cheer-only 接力回报入库)
3. 学术更新 (新研究 / 新解读 / 错纠正录)
4. 文档化 (每次 sprint 1 份工作笔记)
5. 镜像同步 (GitHub + Gitee + 私有云 + 物理硬盘)

**持续验收标准**:
- [ ] URL 失效 < 5% (月监控)
- [ ] 月新增候选 ≥ 10
- [ ] 季度学术引用 ≥ 1 篇 (PubScholar / Google Scholar 跟踪)
- [ ] 月度镜像同步 OK

---

## 4. 关键 Inflection Points (决定成败)

| 时间点 | 决定 | 失败模式 |
|---|---|---|
| **现在** | 是否启动 cheer-only 7 件 P0 | 等 cheer 启动后再排 Phase 1 — 6-12 月停滞 |
| **Phase 1 末** | 接受"目录级 record"还是强求 L1/L2 | 强求 L1/L2 → L3 永远 pending → 8 events 闭环不可达 |
| **Phase 2 中** | OCR 工具栈选型 (Tesseract vs PaddleOCR) | 选错导致精度<70% → 20 天浪费 |
| **Phase 2 末** | 全文覆盖率到多少 (60% vs 80% vs 95%) | 60% 的话检索能力打折，95% 工作量 ×3 |
| **Phase 4 中** | 公网 vs 学术内网 | 公网=版权/数据安全风险；内网=可见性/引用率低 |
| **Phase 5 持续** | 是否有团队/学生接力 | 5 年后无接力 = 平台死掉 = 全部工作归零 |

---

## 5. 隐性成本 (按第一性原理)

### 5.1 cheer-only 是硬约束

mavis 不能替 cheer 跑 NLC/二史馆/港大/校史馆/盟中央/孔夫子/上海书店的:
- 现场阅档
- 函调
- 借阅
- 拍照 / 复制
- 平台 cookie 登录

**1 个 P0 接力 5-7 工作日 + 1-2 周到位 ≈ 2-3 周/件**。7 件 P0 串行约半年。如果 cheer 跑 1-2 件/月，则需 4-7 个月。

### 5.2 OCR 是劳动力密集

- 影像 1000 页 ≈ 1 人天 (Tesseract 跑完)
- 校对 1000 页 ≈ 3-5 人天 (人工 + 二次 OCR 比对)
- Phase 2 总计 ~940 页 ≈ **10 + 30 = 40 人天** (含校对)

### 5.3 持久化成本

- 当前: 526MB 影像 + 600MB work/ = 1.2GB
- 3 年增长 (Phase 1-3 后): 估算 5GB
- 3 镜像 × 5GB = 15GB (便宜但要 commit 持续同步)
- 10 年: 估算 20GB (同样便宜，但需要定期核查镜像)

### 5.4 学术规范

- BibTeX 模板: 0.5 人天
- Chicago 注脚: 0.5 人天
- 民国引文规范 (中华书局 1958 / 1987 各种规范): 0.5 人天
- 合计: 1.5 人天 (一次性)

### 5.5 维护人力

Phase 5 持续 0.5 人天/周 = 你或团队需要 commit 持续投入。

| 人力来源 | 可行性 | 风险 |
|---|---|---|
| cheer 自己 | ✓ (现役) | 长期 burnout |
| 学生 (本科生) | 短期可 | 毕业 = 流失 |
| 学生 (研究生) | 长期可 | 课题结束 = 流失 |
| 学术合作者 | 可 | 优先级冲突 |
| 团队接力 | 难 | 团队不易组建 |
| AI agent | 部分可 (Phase 5 大部分) | 仍有 cheer-only 硬约束 |

---

## 6. 决策前置问题 (cheer 拍板)

启动 Phase 1 前必须回答 4 个问题：

### Q1: 范围
- **A**: 只民盟 1941-1949 (当前 focus, 工作量 ×1)
- **B**: 扩到 8 民主党派同期 (工作量 ×3)
- **C**: 扩到民国政治史 (工作量 ×5-10)
- **D**: 缩到 1941 成立 + 1947 解散 2 事件 (工作量 ×0.5)

### Q2: 深度
- **A**: 一次性 book / article 出版 (1-2 年, Phase 1+2)
- **B**: 5 年研究平台 (Phase 1-4 + 部分 Phase 5)
- **C**: 10+ 年持续平台 (Phase 1-5 全部)

### Q3: 用户
- **A**: 只自己用 (轻量, 简单 metadata)
- **B**: 团队协作 (中等, 多账号 + 引用追溯)
- **C**: 公开 (重, 公网 UI + DOI + 学术规范)
- **D**: 学术内网 (中等, 内网 UI + 引用)

### Q4: 可持续
- **A**: cheer 自己长期 commit
- **B**: 团队接力 (学生 / 同事)
- **C**: 学术机构托管 (高校 / 图书馆)
- **D**: 不确定 / 看 Phase 1 反馈

**我的推荐**: A+A+B+A (范围民盟 / 深度 5 年平台 / 自己用 + 后期转公开 / 自己 commit) — **风险最低 + 价值最高**。

但如果 cheer 答 C / D / B 等激进选项，mavis 可以配合调整。

---

## 7. Sprint 滚动计划 (Phase 1 详细)

### Sprint 39 (1 周) — 现状消化 + 启动 cheer-only

| Day | 任务 | 验收 |
|---|---|---|
| Mon | 239 pending 全量 codex 复审 + 标记 accept / 降级 / cheer-only | 复审报告 |
| Tue | L1 113 hybrid 批量 accept (50% target = 56 accept) | accepted ≥ 506 |
| Wed | L2 45 抽检 (10-15 accept) + L3 79 + L4 39 复审 (5-10 accept) | accepted ≥ 526 |
| Thu | 启动 cheer-only 第 1 件 P0 (港大缩微推荐) | cheer 启动 |
| Fri | schema v2 草拟 + citation 模板 1 套 | schema/cite doc |

### Sprint 40 (1 周) — cheer-only 回报 + 收口

| Day | 任务 | 验收 |
|---|---|---|
| Mon | cheer-only 第 1 件回报入库 + 升级 | 1 件 P0 闭环 |
| Tue | 启动 cheer-only 第 2 件 (二史馆) | cheer 启动 |
| Wed | 启动 cheer-only 第 3 件 (NLC 视检) | cheer 启动 |
| Thu | 事件覆盖矩阵 + Phase 1 收口报告 | 5 events pair_available |
| Fri | Phase 1 收口 + Phase 2 启动准备 | report |

### Phase 1 关键风险

- cheer 启动 P0 不及时 → 1-2 周 idle
- 239 pending 消化时遇到数据问题 (level_accepted 缺失) → 0.5 天解决
- schema v2 升级不兼容 → 1-2 天返工

---

## 8. 成功指标 (5 阶段)

| 阶段 | 成功指标 | 测量方式 |
|---|---|---|
| Phase 1 | accepted ≥ 550, 5 events pair_available, 5 P0 启动, 1 P0 完成 | sprint 收口报告 |
| Phase 2 | OCR 流水线跑通, 1941-1947 关键事件 ≥80% 全文, FTS 可用 | Phase 2 收口报告 |
| Phase 3 | 9 events pair_available, ≥ 32 新候选, 8 党派 + 5 知识分子 | Phase 3 收口报告 |
| Phase 4 | 公网 API + UI, 3 套引用, DOI, 2 镜像 | Phase 4 收口报告 |
| Phase 5 (5 年) | URL 失效 < 5%, 月新增 ≥ 10, 季度引用 ≥ 1, 3 镜像 | 月度 / 季度运营报告 |

---

## 9. 关联文档

- `work/domestic/snapshot_20260721.md` — 0721 末态快照 (现状基线)
- `work/domestic/codex_review_20260721.md` — 125 pending 复审
- `work/domestic/codex_review_tier2_20260721.md` — 89 remaining 复审
- `work/domestic/codex_review_tier2_review_20260721.md` — T2.2 7 条详细
- `work/domestic/cheer_only_queue_20260719.md` — 7 件 P0/P1 模板
- `docs/domestic/收口审计_20260719.md` — 0719 收口报告
- `work/domestic/claude_session_20260721_extended_closeout.md` — 0721 收口

---

## 10. 附录: 后续 sprint 滚动计划 (待补)

Phase 2-5 详细 sprint 计划在 Phase 1 收口后补。每 sprint 收口时更新本文档的对应章节。

---

落档版本：v1.0 (2026-07-22)
下次更新：sprint 39 收口后
