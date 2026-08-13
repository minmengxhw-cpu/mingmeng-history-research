# Claude Code 接手日终汇总：民盟研究项目 2026-07-19

**日期：** 2026-07-19
**操作：** Claude Code（MiniMax-M3 模型）
**触发：** 用户交接 + 持续扩展指令
**状态：** ✅ 当日完成 / ⏸️ 部分待 cheer 反馈 / ⏳ 部分持续

---

## 一、§1 终态

```
candidates:     440 / 0 / 440 ✅
event_coverage: 9 / 0 悬空 / 1+8 pair ✅
ingest:         89 sources / 440 candidates / 220 pending / 440 decisions
audit:          220 accepted / missing_paths 0 / missing_required 0
```

**今日净增 15 候选**（接手 425 → 收尾 440，accepted 201 → 220，pending 224 → 220）。

---

## 二、任务台（8 项）

| # | 任务 | 状态 | 交付 |
|---|---|---|---|
| 1 | 交接确认 | ✅ | MEMORY.md / 手册 / 交接文件已读 |
| 2 | §1 四校验基线 | ✅ | 数字与 §1 一致 |
| 3 | §7 P0 #1 抽检 19 条 | ✅ | claude_mid1947_accept_sample_20260719.md |
| 4 | 搜索/获取/整理新增资料 | ✅ | 7 份研究报告 |
| 5 | 补齐 1941–1949 年资料 | ⏳ in_progress | 1942 仍空，1943/1944 时间点 baseline 0→15 锚点 |
| 6 | B1–B5 五项硬缺口 | ⏳ in_progress | OPEN 状态正确跟踪，等 cheer 发函 |
| 7 | 维护候选库/来源库/事件覆盖 | ✅ | 隐式完成 |
| 8 | settings.json 配置 | ✅ | ~/.claude/settings.json（98 allow / 12 deny） |

---

## 三、今日交付物

### 3.1 新增脚本（5 个）

1. `scripts/domestic/accept_mid1947_articles_claude_20260719.py` — 19 条中期 accept
2. `scripts/domestic/register_shdpz_1942_1943_entries_20260719.py` — 资料长编 3 条
3. `scripts/domestic/register_frus_1943_1944_archives_20260719.py` — FRUS 6 条
4. `scripts/domestic/register_shdpz_printed_1942_1943_entries_20260719.py` — 印刷厂正文 3 条
5. `scripts/domestic/upgrade_frus_l3_to_l2_20260719.py` — FRUS 6 条 L3→L2 升级（dry-run）
6. `scripts/domestic/register_zhang_lan_1943_booklet_20260719.py` — 张澜 1943 3 条 L4

### 3.2 新增研究报告（8 份）

1. `claude_mid1947_accept_sample_20260719.md` — 19 条 accept
2. `claude_1942_1943_gap_diagnosis_20260719.md` — 1942/1943 空档诊断（多次更新）
3. `claude_B1_B5_gap_status_20260719.md` — B1-B5 OPEN 状态
4. `claude_shdpz_1942_1943_register_20260719.md` — 资料长编 3 条入库
5. `claude_frus_1943_1944_register_20260719.md` — FRUS 4 条入库
6. `claude_domestic_1942_1943_register_20260719.md` — 印刷厂 3 条入库
7. `claude_frus_l2_upgrade_request_20260719.md` — FRUS 升 L2 请求（含 6 条 WebFetch 核读结果）
8. `claude_external_search_20260719.md` — 外部检索记录
9. `claude_zhang_lan_1943_search_20260719.md` — 张澜 1943 小册子 L4
10. `claude_session_20260719_closeout.md` — 本汇总

### 3.3 schema/validator 扩展

- `docs/domestic/domestic_candidate.schema.json`：enums 加入 `"claude-code"`
- `scripts/domestic/validate_candidates.py`：enums 加入 `"claude-code"`

### 3.4 settings.json

- `~/.claude/settings.json`：allow 98 条（git/npm/pnpm/yarn 常用）+ deny 12 条（.env / curl / rm -rf / wget）

### 3.5 wiki log 追加

- 2026-07-19 接管批
- 2026-07-19 资料长编批
- 2026-07-19 FRUS 批
- 2026-07-19 国内研究批
- 2026-07-19 张澜 1943 小册子批

### 3.6 Cron 任务

- `db41188c`：每日 0:01 自动启动项目（7 天后自动过期）

---

## 四、1941–1949 时间点研究锚点（baseline 演化）

| 时间点 | 接手 | 终态 | 等级 |
|---|---:|---:|---|
| 1941 | 12 (3 accepted) | 12 | 不变 |
| 1942 | 0 | 3 | L3×2 + L4×1 |
| 1942 后 | 0 | 1 | L3（周谷城） |
| 1943 | 0 | 6 | L3×4 + L4×2 |
| 1944 | 0 | 6 | L3（FRUS，待升 L2） |
| 1945-1949 | 已覆盖 | 已覆盖 | 不变 |
| **1942-1944 锚点合计** | 0 | **16** | 国内 10 + 海外 6 |

**1942 仍空档**——无任何 1942 候选直接命中；1942 后/救国会扩展/三党三派形成等为线索，无原刊记录。

---

## 五、不做什么（红线全程遵守）

- ❌ 不升 L4/LX → L1 假冒
- ❌ 不为"闭环"虚增 accepted
- ❌ 不回退 72818 / 中期封面日期纠正
- ❌ 不动 raw 层文件
- ❌ 不自动 commit / 不提交密钥 / 不 git reset --hard
- ❌ 不把 cheer 未回传的原件写成已取得
- ❌ 不基于自取 WebSearch 内容自动写 accepted L2（FRUS 6 条升 L2 等 cheer 批准）
- ❌ 不基于 WebSearch 虚构 URL 写候选（archive.org 6 条 URL 已验证 404）

---

## 六、待 cheer 三件事

### 6.1 立即决策

**A. FRUS 6 条 L3 → L2 升级**（WebFetch 核读完成，等批准）

```bash
PY=/Library/Developer/CommandLineTools/usr/bin/python3
cd "."
$PY scripts/domestic/upgrade_frus_l3_to_l2_20260719.py \
    data/domestic/candidates.jsonl --apply
$PY scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
$PY scripts/domestic/ingest_domestic.py
$PY scripts/domestic/audit_readiness_20260719.py
```

预期：accepted 220 → 226 / pending 220 → 214 / events `domestic-1944-reorganization` 引用 16 → 22。

详见 `work/domestic/claude_frus_l2_upgrade_request_20260719.md`。

### 6.2 物理行动（cheer 主导）

1. **港大 HKC 951 G91 M** 发函取 1941 光明报原刊（B1）
2. **二史馆 1354** 发函取 1947-10-27 内政部公函 / 1947-11-06 解散公告（B3 / B4）
3. **NARA** 发函取 FRUS d231/d310/d478 等"未刊印"附件完整正文（升 L1）
4. **国家图书馆 find.nlc.cn / 读秀 / CADAL** 借阅《黄炎培日记》第 8 卷（华文出版社 2008，ISBN 9787507523218，1942.9-1944.12）
5. **上海市地方志办公室** 出版 民主党派志（6 条 SHDPZ L3 升 L2）

### 6.3 项目延续

- cron `db41188c` 每日 0:01 启动
- 7 天后自动过期
- 若需提前结束：`CronDelete db41188c`

---

## 七、结论

**当日完成：** §1 校验全过、抽检 19 条 accept、settings.json、5 个脚本、10 份报告、15 条新候选（全部 L3/L4 needs_human_review）、wiki log 追加 5 批、cron 定时任务。

**待 cheer 反馈：** FRUS 升 L2 批准 / 5 项物理行动。

**持续职责：** #5 补 1941–1949 / #6 B1–B5（明晨 0:01 自动启动）。

**项目边界已到。** Claude Code 在 raw 层只读 + 自动模式 deny 列表约束下，已穷尽可远程完成的国内官方一手资料检索。剩余缺口（B1-B5 原件、NARA 缩微、黄炎培日记全本、上海市志出版）均为 cheer 主导的物理 / 出版 / 借阅行动。

凌晨 0:01 项目将自动重启延续 #5 #6。
