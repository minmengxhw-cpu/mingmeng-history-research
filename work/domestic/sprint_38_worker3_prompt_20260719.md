# sprint 38+ Worker 3 prompt — 阶段 3 (1947 五件 B 层硬缺口) minimax 主执行

## 项目

`/Users/cheer/Documents/mm agent/mingmeng-history-research`

## 公共规范

读 `work/domestic/sprint_38_worker_common_20260719.md`（必读）。

## sprint 38+ spec

读 `work/domestic/SPRINT_38_PLUS_SPEC_20260719.md` §3.3 阶段 3 部分。

## 你的角色

minimax 主执行（general agent）。负责 5 件 B 层硬缺口公开网负面检索 + L1 已有原刊影像的等级评估。

## 阶段范围

5 件 B 层硬缺口分项独立追查（cheer 原文：B1+B4+B5+B6+B7）。

**不**跨阶段 1/2/4。**不**处理 cheer-only 接力（cheer 启动后 mavis 配合）— 但 5 件 B 层的**公开网负面检索**你**做**（这是 mavis 可推进部分）。

## 任务清单（5 件 B 层 MECE）

### 3.1 B1 1941《光明報》原刊影像

- 现有：`domestic:HKU:guangmingbao-1941-microform-holdings` L2 needs_human_review + `domestic:LNU:guangmingbao-index-1941` L3 needs_human_review + `domestic:WS:democratic-league-declaration-1941` LX
- 目标：公开网负面检索（再次确认无 1941 香港《光明報》原刊影像可下载）
- 检索范围：
  - Wikimedia Commons（再次核 NLC 民国报纸清单）
  - NLC 民国期刊数据库（远程访问授权如有）
  - CADAL（大学数字图书馆国际合作计划）
  - 香港公共图书馆旧报数据库
  - 中山大学 / 广东省立中山图书馆 / 暨大数据库
  - 维基文库（已 LX）
  - LNU 1941 剪报索引（已 L3 负向）
  - 国立公文書館 (日本) / 美国国会图书馆 / 大英图书馆 民国报纸
- 负向结论 → 阶段报告 §3 列已检索范围
- 新发现 → 新增 L4 needs_human_review 候选（**不**升级 L1）

### 3.2 B4 1946《民主同盟文獻》政治报告正文

- 现有：`domestic:NLC:minmeng-wenxian-1946-toc-political-report-gap` L3 硬缺口卡
- 目标：1946 汇编其他渠道互校 + 1983 汇编同章节（PDF 101-117）+ 二史馆政治报告 + 公开学术论文
- 检索范围：
  - 1983 陆定一主编《中国民主同盟历史文献 1941-1949》PDF 622 页（marxists.org）— 政治报告 PDF 101-117
  - 公开学术论文（如《中国同郷団体の改造・解体過程（1945—1956年）》JSTAGE PDF 第 13 页注 61）
  - 民主党派历史陈列馆 / 民盟中央党史办 公开目录
  - 国家图书馆 / 二史馆 民国期刊数据库
- 找到正文 → 新增 L2 needs_human_review 候选
- 找不到 → 保持 L3 硬缺口卡

### 3.3 B5 1947-10-27 内政部非法化公函

- 现有：`domestic:MMHIST:league-banned-1947-10-27` L2 needs_human_review
- 目标：公开网负面检索 + 已有公报扫描复检
- 检索范围：
  - 维基共享资源国民政府公报 2964/2967/2973/2974 号扫描（**已负向**）
  - 立法院法律资料库（公开访问）
  - 国民政府公报检索系统
  - 二史馆 1354 全宗公开目录（如有）
  - 公开学术论文引用
- 负向结论 → 阶段报告 §3 列已检索范围
- 新发现 → 新增 L4 needs_human_review 候选

### 3.4 B6 1947-11-06 民盟总部解散公告独立印本

- 现有：`domestic:MMHIST:league-dissolution-announcement-1947-11-06` L2 needs_human_review + `domestic:SHPRESS:zhanglan-shidai-ribao-1947-11-07-lead` L4 needs_human_review
- 目标：公开网负面检索 + 已有 5 件同期原刊影像等级评估
- 检索范围：
  - 上海/天津/汉口版 1947-11-06 第 2 版（已有低清试用导出 + 后期官方文章嵌图截取）
  - 上海/天津/汉口版 1947-11-04 / 11-05 / 11-07（前后报道）
  - 1947 11 月其他上海报纸（《文汇报》《新闻报》《申报》）同日同主题
  - 公开学术论文引用
- **新增任务 3.4.1**：上海/天津/汉口版 1947-11-06 第 2 版 已有原刊影像等级评估
  - 上海版：现有 L1 needs_human_review — cheer NLC 现场视检**前**保持 needs_human_review，**不**改 accepted
  - 天津版：现有 L1 needs_human_review — 同上
  - 汉口版：现有 L1 needs_human_review — 同上
- 负向结论 → 阶段报告 §3 列已检索范围
- 新发现 → 新增 L4 needs_human_review 候选

### 3.5 B7 1947-11-04 北平《新民报》原版

- 现有：`domestic:GXMM:xinminbao-professors-statement-1947-11-04` L4 needs_human_review
- 目标：公开网负面检索
- 检索范围：
  - 孔夫子旧书网（cheer 跑）
  - 清华 / 北大 / 燕京 校史馆 公开目录（cheer 跑）
  - 国家图书馆民国期刊数据库
  - 北平版《新民报》其他月份（语境参考）
  - 公开学术论文引用
- 负向结论 → 阶段报告 §3 列已检索范围
- 新发现 → 新增 L4 needs_human_review 候选

## 验收清单（5 件）

1. `work/domestic/sprint_38_phase3_report_2026MMDD.md` 阶段报告
2. 新增/修改候选记录（追加到 `data/domestic/candidates.jsonl`，**不**覆盖）
3. 已检索但未找到的来源及检索范围（阶段报告 §3 — 5 件 B 层**每件**列已检索范围）
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

阶段 3 完成后 commit + close，**不**续接。

## report-back

完成后：

1. commit 你的变更
2. 写 `work/domestic/sprint_38_phase3_report_2026MMDD.md`
3. 给 parent session（`mvs_99f6df4cf4454cf3b4bb0cc1d54d087a`）发回报

## 预计耗时

1 周（公开网负面检索 + 已有原刊影像等级评估，不依赖 cheer-only 接力）。

## 风险

- 5 件 B 层公开网大概率全负向（除 B4 1983 汇编同章节可能找到 L2）
- 已有 L1 needs_human_review 上海/天津/汉口版 1947-11-06 第 2 版 保持 needs_human_review，**不**改 accepted（cheer NLC 视检**后**才能升）
- 独立 cheer-only 接力由 cheer 启动，mavis 配合 — 你**不**处理
