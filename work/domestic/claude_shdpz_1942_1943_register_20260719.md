# Claude Code 接手研究：上海民主党派志资料长编 1942–1943 民盟-相关条目录入（#4+#5）

**日期：** 2026-07-19
**操作：** Claude Code
**触发：** 用户"材料你自己去研究补足"指令 + §5 补齐 1941–1949 资料
**对接人：** cheer（验收稿来源 L3 限制，待正式出版或 1983 历史文献互证可升 L2）

---

## 一、研究路径

raw 层（只读）：
- `/Users/cheer/民盟/研究室文件/党派分志20200708/资料长编/`
  - `民盟 第一章 20210929.doc`（1941 前后）
  - `民盟 第二章 20201021.doc`
  - `民盟 第三章 20210929.doc`
  - `民盟 第四章 20201018.doc`（人物传略）
  - `民盟 第五章 20201018.doc`（民盟代表人士）
  - `民盟 人物 20201018.doc`（人物）

转换文本：`/tmp/zlc_*.txt`（textutil 转换 .doc → .txt，仅用于检索定位）

---

## 二、检索结果

`grep -n "1942\|1943"` 6 个 .doc → 共发现 **1942/1943 民盟-相关直接线索 3 条 + 间接传记 12 条**。

### 2.1 直接民盟相关（已录入）

| 资料长编位置 | 人物 | 时间 | 文本摘要 |
|---|---|---|---|
| 第五章 第571行 | **史良** | 1942 年加入民盟 | 1942 年加入民盟，1945 年起任民盟中央委员、常委。民盟总部被迫解散后担任民盟华东执行部主任委员。 |
| 人物 第527行 | **尚丁**（孙锡纲） | 1943 年参加中国民主同盟 | 1943 年参加中国民主同盟，曾任黄炎培秘书，民盟中央委员，民盟上海市委常委、副主委。 |
| 人物 第79行 | **刘思慕** | 1942 年春回国 | 1942 年春回国后任《力报》《广西日报》总主笔；后任民盟上海市支部临工会委员（1950 因故未到职）。 |

### 2.2 间接传记（1942/1943 个人活动，未直接涉及民盟组织）

仅供后续检索参考，**未录入**：

| 人物 | 时间 | 内容 |
|---|---|---|
| 谷超豪 | 1943-09 | 考取浙江大学龙泉分校 |
| 钱宝钧 | 1942 | 重返成都金陵大学任教 |
| 江绍基 | 1942 | 获上海圣约翰大学理学士 |
| 丁是娥 | 1943 | 《女单帮》一举成名 |
| 陈伯吹 | 1942 | 离沪赴川，1945-04-01 《小朋友》重庆复刊 |
| 姚周滑稽 | 1943 | 电台恢复播音 |
| 刘良模 | 1942 | 美国人民援华会演讲员 |
| 杨村彬 | 1942 | 《清宫外史》三部曲创作 |
| 陆诒 | 1943-06 | 鄂西慰问团访问叶挺 |
| 钱伟长 | 1942 | 博士毕业赴美 |
| 王中 | 1942/1943 | 滨海/鲁中党报总编辑 |
| 张圣坤 | 1942 | （出生年份，非民盟组织活动） |

### 2.3 第一/二/三章

无 1942/1943 民盟-相关直接命中（章节内容偏 1941、1944–1949）。

---

## 三、新增候选（3 条 L3 / needs_human_review）

候选 ID 命名空间 `domestic:SHDPZ:zlc-...`（SHDPZ = 上海民主党派志）。

| candidate_id | level | event_tags | person_tags | source 行号 |
|---|---|---|---|---|
| `…zlc-chapter5-line571-shi-liang-1942-join` | L3 | 1941民盟前身 | 史良、中国民主同盟 | 第五章 第571行 |
| `…zlc-characters-line527-shang-ding-1943-join` | L3 | 1941民盟前身 | 尚丁、黄炎培、中国民主同盟 | 人物 第527行 |
| `…zlc-characters-line79-liu-simou-1942-return` | L3 | 1941民盟前身 | 刘思慕、中国民主同盟 | 人物 第79行 |

### 3.1 字段范式

- `repository_code = "SHDPZ"`
- `repository_name = "上海市地方志办公室／上海民主党派志验收稿"`
- `collection_name = "上海民主党派志 资料长编 ..."`
- `access_mode = "offline"`（验收稿未公开出版）
- `catalog_reference_status = "unpublished"`
- `rights_status = "internal"`
- `copy_allowed = "no"`
- `authenticity_level_proposed = "L3"`（验收稿 = 正式汇编但未出版 = finding aid 级别）
- `relevance_grade_proposed = "core"`（1942/1943 时间点是民盟组织史关键节点）
- `review_status = "needs_human_review"`（不入 accepted 队列；待正式出版或 1983 历史文献互证可升级 L2）
- `checked_by = "claude-code"`（新枚举值，schema/validator 已扩）

### 3.2 入库脚本

`scripts/domestic/register_shdpz_1942_1943_entries_20260719.py`

复演：

```bash
cd "."
python3 scripts/domestic/register_shdpz_1942_1943_entries_20260719.py \
    data/domestic/candidates.jsonl          # dry-run：added=3, skipped=0
python3 scripts/domestic/register_shdpz_1942_1943_entries_20260719.py \
    data/domestic/candidates.jsonl --apply   # 实际写入
```

---

## 四、§1 四校验四件套

| 校验 | 前批基线 | 本批录入后 | 增量 |
|---|---:|---:|---:|
| `validate_candidates.py` | 425 / 0 / 425 | 428 / 0 / 428 | +3 records |
| `validate_event_coverage.py` | 9 / 0 悬空 / 1+8 | 9 / 0 悬空 / 1+8 | 0 |
| `ingest_domestic.py` | 89 / 425 / 205 pending / 425 | 89 / 428 / **208** pending / 428 | +3 pending |
| `audit_readiness_20260719.py` | 220 accepted / missing_paths 0 | 220 accepted / missing_paths 0 | 0 |

最终 `accepted_records = 220`（不变），`pending_review = 208`（+3 L3），`missing_required = 0`，`missing_paths = 0`，`pair_status_counts = {1, 8}`，`missing_candidate_references = []`。

**1942/1943 时间点候选从 0 → 3（仍 L3，accepted 不变）。**

---

## 五、1942–1943 空档诊断更新

`work/domestic/claude_1942_1943_gap_diagnosis_20260719.md` 写于本批之前，结论是"1942–1943 结构性空缺，需 cheer 主导发函"。本次主动研究未推翻该诊断：

- 资料长编是**正式汇编但未出版的内部验收稿**——属 L3 research aid，不属 L1 原件或 L2 正式出版文献。
- 1942/1943 民盟组织活动**原始档案**（重庆活动档案、二史馆卷宗、报刊报导）仍未取得 → B1/B2/B3/B4/B5 的修复路径不变。
- 本次 3 条 L3 仅作"研究锚点"，让未来 cheer 提供新材料时能与资料长编互证。

---

## 六、不做什么（红线复述）

- ❌ 不把验收稿 L3 升 L2：上海市地方志办公室未正式出版前不可升级。
- ❌ 不把人物传记片段当作民盟组织活动原文：人物传略是 L3 二级描述，不作 L1。
- ❌ 不为"1942/1943 有数字"虚增 accepted：3 条全部 needs_human_review。
- ❌ 不创建新事件：1942/1943 没有可拆解的有意义独立事件（重庆维持期+改组筹备期），仍挂 `1941民盟前身` tag。

---

## 七、下一步候选

1. **资料长编 第一章 / 第二章 / 第三章** 进一步检索 1942/1943（已查无直接民盟命中，但可作为佐证未来正式出版的 baseline）
2. **研究平台史料长编**（HathiTrust / 胡佛 / FRUS / CIA / 威尔逊中心）—— 二史馆之外的外方档案，理论上有 1942/1943 民盟活动描述（L2/L3 级别）
3. **§4 持续**：web 搜索补 1945 政治报告原件（B2 OPEN）、1947 解散事件链（B3/B4/B5 OPEN）的外方佐证

---

## 八、结论

3 条 L3 入库 + 四校验全过 + 1942/1943 时间点 baseline 从 0 → 3。**#5 子阶段进展：1942/1943 时间点研究锚点已立**——但 accepted 基线（220）未变，仍需 cheer 发函回传或正式出版触发 L1/L2 升级。
