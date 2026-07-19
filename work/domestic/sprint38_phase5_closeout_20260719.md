# Sprint38 阶段5：入库、校验与审计收口

执行日期：2026-07-19  

## 一、命令与结果

```bash
cd "/Users/cheer/Documents/mm agent/mingmeng-history-research"
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
# {"records": 348, "failed": 0, "passed": 348}

python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
# events 9, missing_candidate_references []

python3 scripts/domestic/ingest_domestic.py
# sources 88, candidates 348, pending_review ~, decisions 348

python3 scripts/domestic/audit_readiness_20260719.py
# missing_required 0, missing_paths 0

python3 scripts/domestic/monitor_completion.py
git diff --check
```

## 二、最终基线（本 sprint 结束）

| 指标 | FINAL_HANDOFF 冻结 | 本 sprint 结束 |
|---|---:|---:|
| 来源 | 87 | **88** |
| 候选 | 345 | **348** |
| accepted | 160 | **160**（未擅自升级） |
| needs_human_review | 185 | **188** |
| 事件 / 悬空 | 9 / 0 | 9 / 0 |

证据等级约：L1 249、L2 47、L3 8、L4 40、LX 4（以实测 Counter 为准）。

## 三、本 sprint 全阶段产出索引

| 阶段 | 报告 |
|---|---|
| 1 | `work/domestic/sprint38_phase1_1941_1945_20260719.md` |
| 2 | `work/domestic/sprint38_phase2_1946_articles_20260719.md` |
| 3 | `work/domestic/sprint38_phase3_hard_gaps_20260719.md` |
| 4 | `work/domestic/sprint38_phase4_1948_1949_20260719.md` |
| 5 | 本文件 |

## 四、净增摘要

1. 来源：NLC511《民主同盟文獻》交替扫描  
2. 候选：+CPPCC 梁漱溟 L4 线索；+新三號停战电文 L1；+章伯钧「当前任务」L1  
3. 修改：wenxian whole/gap 补交替扫描；issue03 双十文止页闭合  
4. **未**将任何硬缺口升为原件；**未**自动 accepted  

## 五、硬缺口（仍 OPEN）

1. 1941《光明報》原刊  
2. 1946 汇编政治报告正文  
3. 1947-10-27 内政部公函/公报原页  
4. 1947-11-06 总部解散独立印本  
5. 1947-11-04 北平《新民报》原版  

→ 继续依赖 `cheer_only_queue_20260719.md` 港大/二史馆/NLC 视检等路径。

## 六、给 Grok 独立复核的提示

交叉搜索上述 3 条新候选与 NLC511 是否重复/越级；确认五项硬缺口仍分卡且无虚报。
