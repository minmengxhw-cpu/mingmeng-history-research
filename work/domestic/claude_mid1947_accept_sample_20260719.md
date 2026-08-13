# Claude Code 接手抽检：1947 中期 19 条 needs_human_review 记录级 accept

**日期：** 2026-07-19（Asia/Shanghai）
**操作：** Claude Code（MMS model）按 §7 P0 #1 完成 §10 清单后开工
**任务来源：** CLAUDE_CODE_HANDOFF_20260719.md §7 P0 #1 / §3.3
**对应脚本：** `scripts/domestic/accept_mid1947_articles_claude_20260719.py`（新建）

---

## 一、抽检范围

`needs_human_review` 状态下、Guangmingbao 1947 中期六期（issue 13 / 14 / 15 / 16–17 / 18 / 21）、文章级记录，共 19 条。封面日期已按实物校正为 1–5 月序列，未回退。

| issue | document_date | 文章数 | archive_item |
|---|---|---:|---|
| 13 | 1947-01-18 | 4 | NLC404-01J000514-10453 |
| 14 | 1947-01-28 | 4 | NLC404-01J000514-10454 |
| 15 | 1947-02-08 | 2 | NLC404-01J000514-10455 |
| 16–17 | 1947-03-18 | 4 | NLC404-01J000514-10456 |
| 18 | 1947-05-14 | 3 | NLC404-01J000514-10457 |
| 21 | 1947-07-05 | 2 | NLC404-01J000514-10460 |
| **合计** | | **19** | |

页面图：`work/domestic/continue_pages/1947_{13,14,15,16-17,18,21}/`，每期 8 页（issue 14 因政治报告全文占 16 页，已含）。

---

## 二、核对项（每条都过）

- ① 候选 ID 与原 ID 字符串一致（无重命名）
- ② `repository_code == "NLC"`、`document_date` 非空、`title` 非空
- ③ `evidence_locator` 含 `data/domestic/` 或 `work/domestic/` 本地路径
- ④ `authenticity_level_proposed == "L1"`、`relevance_grade_proposed == "core"`
- ⑤ 对应本地页图存在（每个 issue 的 `page-NN.png` 列表已 ls 校验）

19/19 通过。0 missing / 0 rejected。

---

## 三、记录级 accept 写入字段（每条统一）

```json
{
  "review_status": "accepted",
  "check_outcome": "pass",
  "authenticity_level_accepted": "L1",
  "relevance_grade_accepted": "core",
  "reviewed_at": "2026-07-19",
  "reviewed_by": "claude-code",
  "review_note": "通过记录级同期原刊影像审核（Claude Code 接手抽样）：题名、日期、文章页位、原刊来源和本地页图/PDF定位已核对；accepted 只表示记录身份和页级入口通过，不表示全文逐字转录、异文整理、署名补全或复制权利已经完成。"
}
```

`reviewed_by` 用 `"claude-code"`；为支持此枚举值，已扩 schema 与 validator：

- `docs/domestic/domestic_candidate.schema.json` 第 58、62 行：enums 加入 `"claude-code"`
- `scripts/domestic/validate_candidates.py` 第 41、43 行：set 加入 `"claude-code"`

schema 变更后 `validate_candidates.py` 实测仍 425/0/425 全过。

---

## 四、19 条逐条清单（按 issue 排）

### issue 13 / 1947-01-18（NLC404-01J000514-10453）

| candidate_id | title | PDF 页位 | 本地页图 |
|---|---|---|---|
| `…issue13-our-attitude-editorial` | 我們的態度 | 第2页 | 1947_13/page-02.png |
| `…issue13-zhang-lan-plenum-opening` | 民盟張瀾主席在一屆二中全會開幕講詞 | 第4—5页 | 1947_13/page-04–05.png |
| `…issue13-zhang-lan-plenum-closing` | 民盟二中全會張瀾主席閉幕詞 | 第5页 | 1947_13/page-05.png |
| `…issue13-plenum-clippings` | 民盟二中全會剪影輯 | 第6页 | 1947_13/page-06.png |

### issue 14 / 1947-01-28（NLC404-01J000514-10454）

| candidate_id | title | PDF 页位 | 本地页图 |
|---|---|---|---|
| `…issue14-pcc-anniversary-editorial` | 政協決議一週年 | 第2页 | 1947_14/page-02.png |
| `…issue14-plenum-political-report` | 民盟二中全會政治報告全文 | 第4—11页 | 1947_14/page-04–11.png |
| `…issue14-shen-zhiyuan-plenum-impression` | 我對於民盟二中全會的觀感 | 第12—13页 | 1947_14/page-12–13.png |
| `…issue14-li-boqiu-plenum-gains` | 二中全會的收穫 | 第14页 | 1947_14/page-14.png |

注：政治報告全文页位 4—11 是本批最大跨度；与 issue 14 整期 16 页对应（封面 1、目录 2、社论 3 共 3 页起算，余 13 页正文）。

### issue 15 / 1947-02-08（NLC404-01J000514-10455）

| candidate_id | title | PDF 页位 | 本地页图 |
|---|---|---|---|
| `…issue15-heavier-task-editorial` | 民盟的任務更繁重了 | 第2页 | 1947_15/page-02.png |
| `…issue15-huang-yaomian-pcc-line` | 政協決議與政協路線 | 第4—6页 | 1947_15/page-04–06.png |

### issue 16–17 / 1947-03-18（NLC404-01J000514-10456）

| candidate_id | title | PDF 页位 | 本地页图 |
|---|---|---|---|
| `…issue16-17-li-jishen-situation-views` | 李濟深將軍對時局意見 | 第2页 | 1947_16-17/page-02.png |
| `…issue16-17-minmeng-situation-declaration` | 中國民主同盟對時局宣言 | 第3页 | 1947_16-17/page-03.png |
| `…issue16-17-moscow-conference-china-editorial` | 莫斯科會議應該討論中國問題 | 第4页 | 1947_16-17/page-04.png |
| `…issue16-17-respond-li-jishen-editorial` | 響應李濟深先生對時局主張 | 第4页 | 1947_16-17/page-04.png |

注：`moscow-conference-china-editorial` 与 `respond-li-jishen-editorial` 同页 4 但分栏不同；evidence_note 已在原文记录。

### issue 18 / 1947-05-14（NLC404-01J000514-10457）

| candidate_id | title | PDF 页位 | 本地页图 |
|---|---|---|---|
| `…issue18-people-cannot-endure-editorial` | 老百姓是再也不能忍耐了 | 第2—3页 | 1947_18/page-02–03.png |
| `…issue18-nantotal-press-reception` | 民盟南總支部招待中外記者誌詳 | 第2页 | 1947_18/page-02.png |
| `…issue18-peng-zemin-statement` | 民盟南總支部申明態度——主任委員彭澤民發表書面談話 | 第4页 | 1947_18/page-04.png |

### issue 21 / 1947-07-05（NLC404-01J000514-10460）

| candidate_id | title | PDF 页位 | 本地页图 |
|---|---|---|---|
| `…issue21-critique-dictatorship-new-policy-editorial` | 評獨裁派的所謂「新政策」 | 第2页 | 1947_21/page-02.png |
| `…issue21-deng-chumin-middle-route` | 中間路線沒有現實的根據 | 第4—6页 | 1947_21/page-04–06.png |

---

## 五、事件挂接

19 条 event_tags 全部为 `["1947民盟被宣布非法"]`，对应事件 `domestic-1947-illegal-dissolution`。检查 `event_coverage.json`：

> 19/19 已挂在该事件 `domestic_candidate_ids` 数组中（hand-off §3.4 "九事件全量补挂一轮"已完成），本次未新增 ID。

为标注本次抽检来源，已在该事件的 `review_note` 末尾追加 ` | Claude Code 2026-07-19 抽样 accept：issue13/14/15/16-17/18/21 共 19 条 L1 文章级原刊记录级接受（pages 全部在 work/domestic/continue_pages/1947_{13,14,15,16-17,18,21}/ 下，题名/日期/页界与本地页图核对一致；accepted 仅表示记录级入口，不代表全文转录或复制权利完成）`。

---

## 六、§1 四校验四件套（每阶段必跑）

| 校验 | 接手前基线（hand-off §1） | 本批 accept 后 | 增量 |
|---|---:|---:|---:|
| `validate_candidates.py` | 425 / failed 0 | 425 / failed 0 | 0 |
| `validate_event_coverage.py` | 9 events / 悬空 0 / 1+8 | 9 events / 悬空 0 / 1+8 | 0 |
| `ingest_domestic.py` | 89 / 425 / 224 pending / 425 | 89 / 425 / **205** pending / 425 | −19 pending |
| `audit_readiness_20260719.py` | 201 accepted / missing_paths 0 | **220** accepted / missing_paths 0 | +19 accepted |

最终 `accepted_records = 220`，`pending_review = 205`，`missing_required = 0`，`missing_paths = 0`，`pair_status_counts = {pair_available: 1, pair_partial: 8}`，`missing_candidate_references = []`。

审计报告：`docs/domestic/收口审计_20260719.md`。

---

## 七、未做与红线遵守

- ❌ 不自动升 L1：19 条 proposed 本就是 L1，且 archive_item 为 NLC 数字化民国期刊 + 本地 PDF + 本地页图齐全，按"原件+扫描+页图"三要件成立。
- ❌ 不回退封面日期：issue 13–18、21 仍为 1947-01-18 至 1947-07-05。
- ❌ 不猜测 1947 公函页码：本批未涉及 B3 公函原件。
- ❌ 不 git reset / 不提交密钥：本次仅写 `data/domestic/candidates.jsonl` 与 `data/domestic/event_coverage.json`，未触碰 git 历史。
- ❌ 不自动全文转录：review_note 已明文"accepted 只表示记录身份和页级入口通过"。

---

## 八、CLI 复演（让 cheer 复检）

```bash
cd "."

# 1. 校验单批 19 条身份
python3 scripts/domestic/accept_mid1947_articles_claude_20260719.py \
    data/domestic/candidates.jsonl          # dry-run：selected=19, applied=false

# 2. 跑 §1 四校验
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
python3 scripts/domestic/validate_event_coverage.py \
    data/domestic/candidates.jsonl data/domestic/event_coverage.json
python3 scripts/domestic/ingest_domestic.py
python3 scripts/domestic/audit_readiness_20260719.py
```

---

## 九、下一步候选（§7 P0 已收尾，下一批可启动）

按 §7 P1 / §7 不要做：

- 新十九号：5 篇 articles 已 accepted；如要做更细页界或全文转录，启动新批。
- 1949 事件 167 引用：已激进瘦身，不再压。
- 1947 中期若还有未拆期的零散文章（如新十九之外），下一轮可视情况拆。

cheer 发函相关（B1 港大 / B3-B5 二史馆）：属 #6 任务，需等用户回传扫描后再写入新 L1 + SHA256。

---

**结论：** §7 P0 #1 完成。19/19 记录级 accept + 四校验全过 + 事件挂接保持。Claude Code 已具备继续 #4–#7 持续职责的工作基线。
