# sprint 38+ Worker 公共规范

3 个 minimax worker 公共规范。每个 worker 自己的范围见各自 prompt。

## 项目基线（0718-0719 freeze）

```text
候选: 345 (L1 247 / L2 47 / L3 8 / L4 39 / LX 4)
状态: accepted 160 / needs_human_review 185
事件: 9 (1 pair_available + 8 pair_partial)
来源: 87
SQLite: 87 sources / 345 candidates / 185 pending / 345 decisions
```

## sprint 38+ spec 落档

`work/domestic/SPRINT_38_PLUS_SPEC_20260719.md` — 5 阶段规划, 包含每阶段任务清单。

## cheer 5 阶段指令（原文）

- 阶段 1：补齐 1941—1945 年民盟成立及早期活动的一手资料
- 阶段 2：整理 1946 年报刊文章，按标题、作者、日期、版面边界拆分
- 阶段 3：分别追查 1947 年五个硬缺口（B1+B4+B5+B6+B7）
- 阶段 4：补齐 1948—1949 年民盟活动资料
- 阶段 5：最后才运行入库、校验和审计

## 角色分工

- **MiniMax**（你）：主执行
- **Grok**：独立复核（不派 — sprint 38+ 仅在 codex 审核时跑）
- **mavis (Mavis)**：中介，接收回报、跑校验、写收口
- **Codex**：每阶段末独立审核
- **cheer**：每阶段启动 / 收口 拍板

## 每阶段必输出 5 件（cheer 红线）

1. `work/domestic/sprint_38_phase{N}_report_2026MMDD.md` 阶段报告
2. 新增或修改的候选记录（追加到 `data/domestic/candidates.jsonl`，不覆盖）
3. 已检索但未找到的来源及检索范围（阶段报告 §3）
4. 来源 URL、访问日期、本地路径、SHA256、页码、证据等级（阶段报告 §4）
5. 校验命令及完整结果（阶段报告 §5）

## 6 件禁止（cheer 红线 — 守死）

- ❌ 把 OCR、目录、后人叙述当作原始一手证据
- ❌ 凭推测补日期、作者、页码
- ❌ 删除既有资料
- ❌ 覆盖用户数据
- ❌ 提交密钥、Token 或隐私
- ❌ 未经核验把 `needs_human_review` 改成 `accepted`

## close 边界

- 阶段完成后 commit + close，**不**续接
- 续接工作等下次 spawn

## report-back 格式

完成后：

1. commit 你的变更
2. 写 `work/domestic/sprint_38_phase{N}_report_2026MMDD.md`
3. 给 parent session 发回报

回报内容：

```text
# sprint 38+ 阶段 N minimax 主执行 回报

- 新增候选 X 条: [list of candidate_id]
- 修改候选 Y 条: [list of candidate_id]
- 负向结论 Z 条: [list of source 跟 检索范围]
- 阶段报告: work/domestic/sprint_38_phaseN_report_2026MMDD.md
- 校验结果: validate_candidates / event_coverage / ingest / audit / git diff --check
- 阻塞 / 风险: [如有]
- Git commit hash: [hash]
```

## 校验命令（阶段 5 收口时跑，minimax worker 不跑）

```bash
cd "."
python3 -B scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
python3 -B scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
python3 -B scripts/domestic/ingest_domestic.py --db data/research_index.sqlite --sources data/domestic/source_registry.json --candidates data/domestic/candidates.jsonl
git diff --check
```

## 文件命名约定

```
阶段报告:  work/domestic/sprint_38_phase{N}_report_2026MMDD.md
候选文件:  data/domestic/candidates.jsonl  (追加, 不覆盖)
来源文件:  data/domestic/source_registry.json  (追加, 不覆盖)
事件文件:  data/domestic/event_coverage.json  (追加, 不覆盖)
```

## parent session

- session_id: `mvs_99f6df4cf4454cf3b4bb0cc1d54d087a`
- agent: Mavis / mavis
- root session — 接收你的回报
