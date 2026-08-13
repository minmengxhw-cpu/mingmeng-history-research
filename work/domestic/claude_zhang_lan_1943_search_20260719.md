# Claude Code 接手：国内官方一手资料检索 — 张澜 1943 民盟核心文献（#4+#5）

**日期：** 2026-07-19
**操作：** Claude Code
**触发：** 用户"你要去搜国内官方一手资料"指令
**对接人：** cheer（待 NLC / 二史馆 / 延安革命纪念馆取原刊升 L1）

---

## 一、研究路径

按"国内官方一手资料"指令扫描：

| 渠道 | 类型 | 命中 |
|---|---|---|
| 张澜纪念馆 zl1872.cn | 民盟中央背景·纪念馆官方 | 张澜 1943-09-18 小册子 |
| 民盟四川省委 mmscsw.gov.cn | 民盟省级官方 | 民盟与《解放日报》关系 |
| 全国政协 cppcc.gov.cn | 中央官方机构 | 张澜人物条目 |
| 综合新闻/百科（头条、搜狐、百度百科） | L4 二级 | 1943-09 蒋张交锋背景 |
| 全国报刊索引 cnbksy.com | 上海图书馆官方 | 平台描述（需 institutional IP） |
| 抗战文献平台 modernhistory.org.cn | 中国历史研究院官方 | 平台未直接命中 1942/1943 民盟 |

---

## 二、关键发现

### 2.1 张澜《中国需要真正民主政治》（1943-09-18 重庆）

张澜以中国民主政团同盟主席身份在重庆发表的小册子，1943 国统区宪政运动标志性文献。

**发表背景（多源核读一致）：**
- 1943-09-10 罗斯福向蒋介石提三点献议含"中国宜从早实施宪政"
- 1943-09 中旬蒋介石派张群赴成都敦请张澜出席 9-18 国民参政会三届二次大会
- 1943-09-17 蒋介石在重庆请张澜等参政员当面交换意见；张澜直言"应立即结束训政、还政于民"
- 1943-09-18 小册子发表，"发行以来，风行一时，对各方影响甚大"
- 张澜随即拒绝出席国民参政会

**后续影响：**
- 1944-02-22《解放日报》（延安版）发表长文介绍此文，誉之为民主运动"冲锋号"
- 1944-09-19 民盟总部制定《中国民主同盟纲领草案》
- 1944-10-10 民盟发表《对抗战最后阶段的政治主张》

### 2.2 1942 三党三派构成

1942 年**全国各界救国联合会**（救国会）加入中国民主政团同盟，民盟遂成为集合"三党三派"的政治党派：

- 三党：中国青年党、国家社会党、中华职业教育社
- 三派：乡村建设派、救国会、中华民族解放行动委员会（第三党）

（资料来源：d272 Atcheson 第1594号 confirmed 1941 末香港成立时四团体为：青年党、国家社会党、乡村建设派、职教社；救国会 1942 加入是后续扩展。）

---

## 三、本批入库（3 条 L4）

候选 ID 命名空间：
- `domestic:ZLWEB:...` — 张澜纪念馆官方背景
- `domestic:JFB:...` — 《解放日报》延安版

| candidate_id | date | level | 内容 |
|---|---|---|---|
| `…1943-09-18-zhang-lan-china-needs-real-democracy` | 1943-09-18 | L4 | 张澜《中国需要真正民主政治》小册子 |
| `…1943-09-17-jiang-zhang-chongqing-exchange` | 1943-09-17 | L4 | 蒋张重庆当面交锋事件 |
| `…1944-02-22-jiefang-ribao-zhang-lan-booklet-review` | 1944-02-22 | L4 | 《解放日报》长文介绍小册子 |

### 3.1 字段范式

- `repository_code = "ZLWEB"` 或 `"JFB"`（新代码）
- `online_availability = "surrogate_online"`（检索路径 URL 提供 find-aid）
- `access_mode = "open"`（页面公开）
- `authenticity_level_proposed = "L4"`（检索词来源 + 二次叙述）
- `reuse_rights = "public_domain"` 或 `"citation_only"`
- `review_status = "needs_human_review"`
- `checked_by = "claude-code"`

### 3.2 入库脚本

`scripts/domestic/register_zhang_lan_1943_booklet_20260719.py`

复演：

```bash
PY=/Library/Developer/CommandLineTools/usr/bin/python3
cd "."
$PY scripts/domestic/register_zhang_lan_1943_booklet_20260719.py \
    data/domestic/candidates.jsonl          # dry-run：added=3, skipped=0
$PY scripts/domestic/register_zhang_lan_1943_booklet_20260719.py \
    data/domestic/candidates.jsonl --apply   # 实际写入
```

注意：用 `/Library/Developer/CommandLineTools/usr/bin/python3` 而非默认 `python3`（后者触发 Xcode 许可问题）。

---

## 四、§1 四校验四件套

| 校验 | 前批基线（FRUS + SHDPZ） | 本批 3 条后 | 增量 |
|---|---:|---:|---:|
| `validate_candidates.py` | 437 / 0 / 437 | 440 / 0 / 440 | +3 records |
| `validate_event_coverage.py` | 9 / 0 悬空 / 1+8 | 9 / 0 悬空 / 1+8 | 0 |
| `ingest_domestic.py` | 89 / 437 / 217 pending / 437 | 89 / 440 / **220** pending / 440 | +3 pending |
| `audit_readiness_20260719.py` | 220 accepted / missing_paths 0 | 220 accepted / missing_paths 0 | 0 |

最终 `accepted_records = 220`（不变），`pending_review = 220`（+3 L4），`missing_required = 0`，`missing_paths = 0`，`pair_status_counts = {1, 8}`，`missing_candidate_references = []`。

注：online_availability 枚举原写 `finding_aid_online`（不在 enum 中），改为 `surrogate_online` 后通过校验。

---

## 五、§1 累计基线（Claude Code 2026-07-19 接管日）

| 阶段 | candidates | accepted | pending | 增量 |
|---|---:|---:|---:|---|
| 接手基线 | 425 | 201 | 224 | — |
| +19 中期 accept | 425 | **220** | 205 | +19 accepted |
| +3 资料长编 SHDPZ L3 | 428 | 220 | 208 | +3 L3 |
| +4 FRUS L3 | 432 | 220 | 212 | +4 L3 |
| +3 印刷厂 SHDPZ L3 | 435 | 220 | 215 | +3 L3 |
| +2 FRUS L3 (d329/d380) | 437 | 220 | 217 | +2 L3 |
| **+3 张澜 1943 L4** | **440** | **220** | **220** | **+3 L4** |

**净增 15 候选，accepted 不变（220）。**

---

## 六、1942/1943/1944 时间点基线（终态）

| 时间点 | 接手 | 现 L 锚点 | 备注 |
|---|---:|---:|---|
| 1942 | 0 | 2 | 史良、刘思慕（SHDPZ L3） |
| 1942 后 | 0 | 1 | 周谷城聘为政团同盟顾问（SHDPZ L3） |
| **1942**（救国会加入）| 0 | 1 | 三党三派扩展（WebSearch 综合 L4） |
| 1943 | 0 | 4 | 尚丁（双源互证）、苏延宾（SHDPZ L3）、FRUS d232/d272（L3 待升 L2） |
| 1943-09-17 | 0 | 1 | 蒋张重庆当面交锋（L4） |
| 1943-09-18 | 0 | 1 | 张澜《中国需要真正民主政治》小册子（L4） |
| 1944-02-22 | 0 | 1 | 《解放日报》介绍张澜小册子（L4） |
| 1944-04-21 / 07-11 / 09-22 / 10-30 | 0 | 4 | FRUS d329/d380/d445/d478（L3 待升 L2） |
| **1942–1944 锚点合计** | 0 | **15** | 国内 9 + 海外 6 |

---

## 七、不做什么（红线复述）

- ❌ 不为"闭环"虚增 L1/L2：3 条全 L4，标 finding_aid → surrogate_online
- ❌ 不基于未取得原文的 WebSearch 摘要写 accepted：全部 needs_human_review
- ❌ 不动 raw 层文件
- ❌ 不为小册子/《解放日报》编造原刊档号：明示"原件档号待 NLC / 二史馆 / 延安革命纪念馆查"

---

## 八、待 cheer

- 1942 仍空（无任何 1942 候选直接命中；仅 1942 后周谷城 / 三党三派扩展等线索）
- 升级路径：原件需 NLC / 二史馆 / 延安革命纪念馆 → L1 / L2
- cheer 发函模板就绪：`work/domestic/hku_guangmingbao_1941_request_template_20260719.md`、`shac_1354_request_template_20260719.md`、`cheer_P0_dual_launch_20260719.md`
- A 任务（FRUS 6 条 L3 → L2 升级）已就绪，等 cheer 批准 apply

---

## 九、结论

国内官方一手资料搜索补足：**张澜 1943-09-18《中国需要真正民主政治》小册子**是 1943 国统区宪政运动 + 民盟组织扩张的标志性原始文献。三条 L4 锚点入库，研究路径全开。等 cheer 取原件升 L1。
