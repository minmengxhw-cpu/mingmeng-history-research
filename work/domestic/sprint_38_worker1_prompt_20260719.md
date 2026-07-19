# sprint 38+ Worker 1 prompt — 阶段 1 (1941-1945) minimax 主执行

## 项目

`/Users/cheer/Documents/mm agent/mingmeng-history-research`

## 公共规范

读 `work/domestic/sprint_38_worker_common_20260719.md`（必读）。

## sprint 38+ spec

读 `work/domestic/SPRINT_38_PLUS_SPEC_20260719.md` §3.1 阶段 1 部分。

## 你的角色

minimax 主执行（general agent）。负责 1941-1945 公开网搜索 / 整理 / 候选记录 / 阶段报告。

## 阶段范围

1941-1945 民盟成立及早期活动一手资料补齐。

**不**跨阶段 2/3/4。**不**处理 cheer-only 接力（港大缩微 / 二史馆函调 / NLC 视检 / 孔夫子 / 校史馆 / 民盟中央）— 这些由 cheer 启动，mavis 配合接收回报。

## 任务清单（6 件 MECE）

### 1.1 1946 民盟总部《民主同盟文獻》文章级拆分

- 现有：`domestic:NLC:minmeng-wenxian-1946-whole` L2 needs_human_review
- 目标：拆 1941 成立宣言（PDF 9-11）/ 对时局主张纲领（PDF 12-13）文章级
- L2 维持，**不**升 L1（无原刊）
- 如已有 candidate_id 复用，**不**重复创建
- 已有候选 `domestic:NLC:minmeng-wenxian-1946-formation-declaration`（PDF 9-11）/ `domestic:NLC:minmeng-wenxian-1946-ten-program`（PDF 12-13）— 检查是否需要补全 `evidence_locator` / `evidence_note` / 拆 L2 needs_human_review

### 1.2 民憲多期文章级拆分

- 现有：`domestic:NLC:minxian-v1n10-1944-12-20` L1 整期 needs_human_review + 10+ 期 L1 整期 needs_human_review（详见 `docs/domestic/press_scan_manifest.md`）
- 目标：拆代表性文章（已拆 v1n9 民主政治 vs 非民主政治 1944-11-20，**不**要再拆）
- 至少 3 个新文章级候选（建议 1 1944 + 1 1945 整期文章 + 1 v1n10 文章）
- L1 维持，needs_human_review，**不**改 accepted
- 已有候选参考：`domestic:NLC:minxian-v1n9-democracy-vs-nondemocracy-1944-11-20`

### 1.3 1983 汇编 1941 成立 + 对时局主张纲领 同期印本搜索

- 现有：`domestic:MMHIST:formation-declaration-1941` L2 accepted + `domestic:MMHIST:platform-1945` L2 accepted + `domestic:MMHIST:political-report-1945` L2 accepted + `domestic:MMHIST:congress-declaration-1945` L2 accepted + `domestic:MMHIST:organization-regulation-1945` L2 accepted
- 目标：公开网（Wikimedia Commons / NLC / CADAL / 大学图书馆 / 党史办 / 民主党派历史陈列馆 / 特园）同步搜索同期印本
- 负向结论大概率，**不**写推测页码
- 如有发现 → 新增 L1 needs_human_review 候选 + 留 cheer-only 接力清单
- 如全负向 → 阶段报告 §3 列已检索范围

### 1.4 1944 全国代表会议原始文件搜索

- 现有：无候选
- 目标：公开网 + 校史馆 + 民主党派历史陈列馆 + 民盟中央党史办
- 公开网大概率负向；如全负向 → 阶段报告 §3 列已检索范围
- 关联已有 `domestic:BJDCMM:reorganization-1944` L4 名录

### 1.5 1945 同期印本搜索（政治报告 / 组织规程 / 宣言 / 纲领）

- 现有：L2 已 accepted（1983 汇编）
- 目标：公开网搜索同期印本
- 负向结论大概率

### 1.6 1941 同期《新华日报》3 期（1941-10-10 / 10-16 / 10-28）已负向核查

- **不**重复，复用现有 `domestic:NLC:xinhua-1941-10-10` L4 candidates 即可
- 参考 `work/domestic/nlc_xinhua_1941_early_scans_review_20260719.md`

## 验收清单（5 件）

1. `work/domestic/sprint_38_phase1_report_2026MMDD.md` 阶段报告
2. 新增/修改候选记录（追加到 `data/domestic/candidates.jsonl`，**不**覆盖）
3. 已检索但未找到的来源及检索范围（阶段报告 §3）
4. 来源 URL + 访问日期 + 本地路径 + SHA256 + 页码 + 证据等级（阶段报告 §4）
5. 校验命令及完整结果（阶段报告 §5）— 跑 validate_candidates / validate_event_coverage / ingest / audit / git diff --check

## 6 件禁止（cheer 红线 — 守死）

- ❌ OCR / 目录 / 后人叙述 ≠ 原始一手
- ❌ 不凭推测补日期 / 作者 / 页码
- ❌ 不删除既有资料
- ❌ 不覆盖用户数据
- ❌ 不提交密钥 / Token / 隐私
- ❌ 不擅自改 needs_human_review → accepted（须 codex 审核 + cheer 拍）

## close 边界

阶段 1 完成后 commit + close，**不**续接。续接工作等下次 spawn。

## report-back

完成后：

1. commit 你的变更
2. 写 `work/domestic/sprint_38_phase1_report_2026MMDD.md`
3. 给 parent session（`mvs_99f6df4cf4454cf3b4bb0cc1d54d087a`）发回报

回报格式见公共规范 §report-back 格式。

## 预计耗时

1-2 周（minimax 主执行，不依赖 cheer-only 接力）。

## 风险

- 1941 / 1944 / 1945 同期印本公开网无，大概率全负向
- L2 needs_human_review 拆文章级后保持 needs_human_review，**不**升级
- 已有候选不重复创建
