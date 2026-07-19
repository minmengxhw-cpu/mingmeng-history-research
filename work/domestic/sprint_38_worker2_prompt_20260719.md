# sprint 38+ Worker 2 prompt — 阶段 2 (1946 报刊文章拆分) minimax 主执行

## 项目

`/Users/cheer/Documents/mm agent/mingmeng-history-research`

## 公共规范

读 `work/domestic/sprint_38_worker_common_20260719.md`（必读）。

## sprint 38+ spec

读 `work/domestic/SPRINT_38_PLUS_SPEC_20260719.md` §3.2 阶段 2 部分。

## 你的角色

minimax 主执行（general agent）。负责 1946 报刊文章拆分（按标题 / 作者 / 日期 / 版面边界）。

## 阶段范围

1946 报刊文章按标题 / 作者 / 日期 / 版面边界拆分；补齐 1946 民主同盟文献政治报告正文（B4 跨阶段 3 也属于此）。

**不**跨阶段 1/3/4。**不**处理 cheer-only 接力。

## 任务清单（7 件 MECE）

### 2.1 1946 光明报新一 / 二 / 四 / 七 / 八号 文章级拆分

- 现有：5 件 L1 整期 needs_human_review
  - `domestic:NLC:guangmingbao-1946-issue01`（已拆 issue01-refounding-editorial L1）
  - `domestic:NLC:guangmingbao-1946-issue02`（已拆 issue02-people-power-editorial L1）
  - `domestic:NLC:guangmingbao-1946-issue04`（已拆 issue04-urgent-situation-editorial L1）
  - `domestic:NLC:guangmingbao-1946-issue07`（已拆 issue07-why-not-national-assembly L1）
  - `domestic:NLC:guangmingbao-1946-issue8`（已拆 issue8-conditional-national-assembly L1）
- 目标：每期至少再拆 1-2 篇文章（首面社论已拆，目录中其他文章级候选）
- L1 维持，needs_human_review，**不**改 accepted
- 复用已有 candidate_id 命名风格（`domestic:NLC:guangmingbao-1946-issue{N}-{slug}`）

### 2.2 1946 光明报新三号 止页完成

- 现有：`domestic:NLC:guangmingbao-1946-issue03-double-ten-task-article` L1 待止页（codex 0719 拆）
- 目标：找止页，完成 L1 accepted
- 题名已知：《為完成雙十節的歷史任務而奮鬥》（李平達）
- 起点 PDF 1 页；止页待核（建议 PDF 2-4 页范围）
- 完成后保持 L1 needs_human_review（**不**改 accepted — codex 审）

### 2.3 1946 光明报新六号 OCR 提升后题名拆分

- 现有：`domestic:NLC:guangmingbao-1946-issue06` L1 整期 needs_human_review
- 目标：OCR 提升（90 DPI → 200 DPI）后，首面社论题名确定后拆 L1
- 题名暂定待核：候选词《论当前时局》《再论国大问题》《评国大延期》等
- 找不到确定题名 → 保持整期

### 2.4 1946 民主同盟文献 政治报告正文互校（B4 跨阶段）

- 现有：`domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap` L3 硬缺口卡
- 目标：1946 汇编其他渠道互校 + 1983 汇编同章节（PDF 101-117）+ 二史馆政治报告（公开学术论文引用）
- 公开学术论文示例：[《中国同郷団体の改造・解体過程（1945—1956年）》](https://www.jstage.jst.go.jp/article/asianstudies/49/3/49_38/_pdf) PDF 第 13 页注 61
- 找到正文 → 新增 L2 needs_human_review 候选
- 找不到 → 保持 L3 硬缺口卡

### 2.5 1946 旧政协其他报刊同期报道

- 现有：21 候选 L1（1946-pcc 事件）
- 目标：公开网搜索《文汇报》《大公报》《新华日报》《申报》同期报道
- 至少 3 个新候选（建议 1 大公报 + 1 文汇报 + 1 申报 / 新华日报）
- L1 needs_human_review（**不**改 accepted）

### 2.6 1946 拒国大其他报刊报道

- 现有：18 候选 L1（1946-refuse-national-assembly 事件）
- 目标：公开网搜索同期报道
- 至少 2 个新候选

### 2.7 1946 李闻事件其他报刊报道

- 现有：14 候选 L1（1946-li-wen 事件）
- 目标：公开网搜索同期报道 + 《观察》3卷11期文章级拆分
- 至少 2 个新候选（其中至少 1 个《观察》文章级）

## 验收清单（5 件）

1. `work/domestic/sprint_38_phase2_report_2026MMDD.md` 阶段报告
2. 新增/修改候选记录（追加到 `data/domestic/candidates.jsonl`，**不**覆盖）
3. 已检索但未找到的来源及检索范围（阶段报告 §3）
4. 来源 URL + 访问日期 + 本地路径 + SHA256 + 页码 + 证据等级（阶段报告 §4）
5. 校验命令及完整结果（阶段报告 §5）

## 6 件禁止（cheer 红线 — 守死）

- ❌ OCR / 目录 / 后人叙述 ≠ 原始一手
- ❌ 不凭推测补日期 / 作者 / 页码
- ❌ 不删除既有资料
- ❌ 不覆盖用户数据
- ❌ 不提交密钥 / Token / 隐私
- ❌ 不擅自改 needs_human_review → accepted

## close 边界

阶段 2 完成后 commit + close，**不**续接。

## report-back

完成后：

1. commit 你的变更
2. 写 `work/domestic/sprint_38_phase2_report_2026MMDD.md`
3. 给 parent session（`mvs_99f6df4cf4454cf3b4bb0cc1d54d087a`）发回报

## 预计耗时

1-2 周（minimax 主执行，不依赖 cheer-only 接力）。

## 风险

- 1946 光明报 OCR 提升后题名仍可能不确定（保持整期）
- 1946 旧政协 / 拒国大 / 李闻 同期报道公开网可能少
- 1946 民主同盟文献 政治报告正文公开网无（保持 L3 硬缺口）
