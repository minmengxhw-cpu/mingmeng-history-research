# domestic-1949-new-pcc 激进瘦身报告

- 日期：2026-07-19
- 事件：`domestic-1949-new-pcc`（1949年新政协筹备、民主人士北上与第一届全体会议）
- 范围：仅改 `data/domestic/event_coverage.json` → `domestic_candidate_ids` + `review_note`
- **未删** `candidates.jsonl` 中的候选本身（仅从 event 列表移出）
- **未改** `event_tags` / `pair_status` / `domestic_status` / `foreign_event_slugs`

## 0. 备份思路

- 瘦身前完整 ID 列表见 **附录 A**（本报告内嵌，可对照 git / 本 md 回滚）。
- 若需机器回滚：以本报告附录 ID 列表写回 `domestic-1949-new-pcc.domestic_candidate_ids`，
  并将 `review_note` 恢复为瘦身前原文（见附录 B）。
- 候选库未动，移出项仍可通过 `candidate_id` 在 `candidates.jsonl` 检索。

## 一、数量

| 指标 | 数值 |
|---|---|
| 瘦身前引用数 | **171**（unique 171） |
| 瘦身后引用数 | **167**（unique 167） |
| 移出条数 | **4** |
| 保留条数 | **167** |

## 二、保留原则（激进·已批准）

默认**只保留**：

| 类 | 规则 |
|---|---|
| **A** | SAAC / 中央档案馆：`candidate_id` 含 `SAAC` 且 `authenticity_level_accepted=L1`（或题名明确 1949 一届全会/新政协/开国/筹备会） |
| **B** | NLC 光明报 1949：`guangmingbao-1948-1949-v2n1*`、`v2n12*` 整期与文章 |
| **C** | 题名或 `document_date` 明确 1949 且与新政协/政协/共同纲领/开国**直接相关**的少量 L2/L3/L4 线索（宁缺毋滥，总额外 ≤15） |

移出（仅 event 列表）：1948 五一/输送计划等应归 1948 的；1945–1947 材料；无直接字面关联的泛盟史 L4；重复 ID。

## 三、保留分类计数

| 保留类 | 条数 |
|---|---|
| A_SAAC_L1 | 161 |
| B_NLC_光明报1949_v2n1/v2n12 | 5 |
| C_L2L3L4_直接线索 | 1 |
| **合计** | **167** |

### A 类主题细分（信息性）

| 主题桶 | 条数 |
|---|---|
| A·一届全会 | 88 |
| A·新政协筹备会 | 43 |
| A·开国大典相关 | 20 |
| A·共同纲领/组织法 | 5 |
| A·其它SAAC_L1（专题目录条目） | 5 |

### C 类保留明细（1 条，远低于 ≤15 上限）

| candidate_id | auth | date | title | 理由 |
|---|---|---|---|---|
| `domestic:MMZY:lead-周恩来与第一届人民政协会议的召开` | None | 1945—1949 | 周恩来与第一届人民政协会议的召开 | 题名含「第一届人民政协会议」，作 L4 检索线索 |

### B 类保留明细（5）

| candidate_id | date | title |
|---|---|---|
| `domestic:NLC:guangmingbao-1948-1949-v2n1` | 1949-01-10 | 《光明報》1949年2卷1期（1949-01-10） |
| `domestic:NLC:guangmingbao-1948-1949-v2n1-article` | 1949-01-10 | 新政协问题笔谈 |
| `domestic:NLC:guangmingbao-1948-1949-v2n12` | 1949-02-12 | 《光明報》1949年2卷12期（1949-02-12） |
| `domestic:NLC:guangmingbao-1948-1949-v2n12-article` | 1949-02-12 | 我們對和平的態度 |
| `domestic:NLC:guangmingbao-1948-1949-v2n12-taiwan-liberation` | 1949-02-12 | 談台灣解放問題 |

## 四、移出分类计数

| 移出类 | 条数 |
|---|---|
| 1948应归1948（输送计划） | 1 |
| 1948应归1948（进入解放区动员） | 1 |
| 1948应归1948（纲领草案初稿） | 1 |
| 泛盟史L4无线面直接关联 | 1 |
| **合计** | **4** |

本轮**未命中**类别：1945–1947 材料（0）、重复 ID（0）、1948 五一原件（上轮已移，本轮列表已无）。

### 移出明细

| candidate_id | date | title | 分类 | 理由 |
|---|---|---|---|---|
| `domestic:SAAC:catalog-01-01_10` | 1948-10-31 | 钱之光关于报送在香港的民主人士输送内地计划给周恩来、任弼时等的电报 | 1948应归1948（输送计划） | document_date=1948-10-31；香港民主人士输送内地计划，主属1948北上筹备链，应归1948事件，激进策略不再双挂1949 |
| `domestic:SAAC:catalog-01-01_11` | 1948-11-20 | 周恩来拟写的中共中央关于港沪两地迅速动员一批民主人士等经天津进入解放区给上海局、香港分局的电报 | 1948应归1948（进入解放区动员） | document_date=1948-11-20；港沪民主人士经天津进入解放区动员电报，主属1948，激进策略移出 |
| `domestic:SAAC:catalog-03-03_03_01` | 1948 | 周恩来拟写的新民主主义纲领（草案初稿） | 1948应归1948（纲领草案初稿） | document_date=1948；《新民主主义纲领》草案初稿属共同纲领谱系前史，日期1948，激进策略不扩列进1949核心 |
| `domestic:MMSH:lead-新中国成立前民盟对政治协商制度的贡献` | 1941—1949 | 新中国成立前民盟对政治协商制度的贡献 | 泛盟史L4无线面直接关联 | L4；题名泛述民盟对政治协商制度贡献，日期跨1941—1949，无「一届全会/新政协/共同纲领/开国」直接字面，宁缺毋滥 |

## 五、边界案例

| candidate_id | 处置 | 说明 |
|---|---|---|
| `domestic:SAAC:catalog-01-01_10` / `_11` | **移出** | 上轮保守瘦身曾以「事件名含民主人士北上」双挂；激进策略明确 1948-10/11 输送/进入解放区归 1948 |
| `domestic:SAAC:catalog-03-03_03_01` | **移出** | 上轮作共同纲领起草谱系保留；日期 1948，激进策略不进 1949 核心列表 |
| `domestic:MMSH:lead-新中国成立前民盟对政治协商制度的贡献` | **移出** | 上轮因 tags 含 1949 政协保留；题名无直接字面，泛盟史 L4，宁缺毋滥 |
| `domestic:MMZY:lead-周恩来与第一届人民政协会议的召开` | **保留·C** | 题名明确「第一届人民政协」，唯一 L4 线索，计入 C 配额 |
| `domestic:NLC:…v2n12-taiwan-liberation` | **保留·B** | 属 v2n12* 文章级，规则要求整期与文章一并保留 |
| `domestic:SAAC:catalog-01-01_17`–`_22`（迁平/西苑/宋庆龄信/论人民民主专政等） | **保留·A** | 均为 SAAC L1，1949 年专题条目，服务北上进京与建国语境 |
| 全部 `1949-index-c*` / `1949-item-a*` / `catalog-02`–`06` 等 L1 | **保留·A** | SAAC L1 默认保留；主体为一届全会/筹备会/开国目录 |

## 六、review_note 更新

已写入一句（含日期与原则），并保留境外对应待建提示。

## 七、校验

```text
$ python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
{"candidate_ids": 405, "events": 9, "missing_candidate_references": [], "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}
```

- **结果：通过**（`missing_candidate_references` 为空，exit 0）
- 仅改 `domestic-1949-new-pcc.domestic_candidate_ids` 与 `review_note`；候选库与其它事件引用未动

## 八、返回摘要

| 项 | 值 |
|---|---|
| 前→后 | **171 → 167** |
| 移出 N | **4** |
| 保留 N | **167** |
| 校验 | **通过** |

---

## 附录 A：瘦身前完整 ID 列表（171）

```
domestic:SAAC:1949-02-01-01
domestic:SAAC:1949-02-14-01
domestic:SAAC:1949-09-21-05
domestic:SAAC:1949-index-c03
domestic:SAAC:catalog-06-06_09
domestic:NLC:guangmingbao-1948-1949-v2n1
domestic:NLC:guangmingbao-1948-1949-v2n1-article
domestic:NLC:guangmingbao-1948-1949-v2n12
domestic:NLC:guangmingbao-1948-1949-v2n12-article
domestic:NLC:guangmingbao-1948-1949-v2n12-taiwan-liberation
domestic:SAAC:1949-01-08-01
domestic:SAAC:1949-09-21-01
domestic:SAAC:1949-09-21-02
domestic:SAAC:1949-09-21-03
domestic:SAAC:1949-09-21-04
domestic:SAAC:1949-09-21-06
domestic:SAAC:1949-09-21-07
domestic:SAAC:1949-09-22-01
domestic:SAAC:1949-09-22-02
domestic:SAAC:1949-09-23-01
domestic:SAAC:1949-09-25-01
domestic:SAAC:1949-09-26-01
domestic:SAAC:1949-09-27-01
domestic:SAAC:1949-09-27-02
domestic:SAAC:1949-09-28-01
domestic:SAAC:1949-09-29-01
domestic:SAAC:1949-09-29-02
domestic:SAAC:1949-09-30-01
domestic:SAAC:1949-09-30-02
domestic:SAAC:1949-09-30-03
domestic:SAAC:1949-index-c01
domestic:SAAC:1949-index-c02
domestic:SAAC:1949-index-c04
domestic:SAAC:1949-index-c05
domestic:SAAC:1949-index-c06
domestic:SAAC:1949-index-c07
domestic:SAAC:1949-index-c08
domestic:SAAC:1949-index-c09
domestic:SAAC:1949-index-c10
domestic:SAAC:1949-index-c11
domestic:SAAC:1949-index-c12
domestic:SAAC:1949-index-c13
domestic:SAAC:1949-index-c14
domestic:SAAC:1949-index-c15
domestic:SAAC:1949-index-c16
domestic:SAAC:1949-index-c17
domestic:SAAC:1949-index-c18
domestic:SAAC:1949-index-c19
domestic:SAAC:1949-index-c20
domestic:SAAC:1949-index-c21
domestic:SAAC:1949-index-c22
domestic:SAAC:1949-index-c23
domestic:SAAC:1949-index-c24
domestic:SAAC:1949-index-c25
domestic:SAAC:1949-index-c26
domestic:SAAC:1949-index-c27
domestic:SAAC:1949-index-c28
domestic:SAAC:1949-index-c29
domestic:SAAC:1949-index-c30
domestic:SAAC:1949-index-c31
domestic:SAAC:1949-index-c32
domestic:SAAC:1949-item-a01
domestic:SAAC:1949-item-a02
domestic:SAAC:1949-item-a03
domestic:SAAC:1949-item-a04
domestic:SAAC:1949-item-a05
domestic:SAAC:1949-item-a06
domestic:SAAC:1949-item-a07
domestic:SAAC:1949-item-a08
domestic:SAAC:1949-item-a09
domestic:SAAC:1949-item-a10
domestic:SAAC:1949-item-a11
domestic:SAAC:1949-item-a12
domestic:SAAC:1949-item-a13
domestic:SAAC:1949-item-a14
domestic:SAAC:1949-item-a15
domestic:SAAC:1949-item-a16
domestic:SAAC:1949-item-a17
domestic:SAAC:catalog-01-01_10
domestic:SAAC:catalog-01-01_11
domestic:SAAC:catalog-01-01_13
domestic:SAAC:catalog-01-01_17
domestic:SAAC:catalog-01-01_18
domestic:SAAC:catalog-01-01_19
domestic:SAAC:catalog-01-01_20
domestic:SAAC:catalog-01-01_21
domestic:SAAC:catalog-01-01_22
domestic:SAAC:catalog-02-02_01
domestic:SAAC:catalog-02-02_02
domestic:SAAC:catalog-02-02_03
domestic:SAAC:catalog-02-02_04
domestic:SAAC:catalog-02-02_05
domestic:SAAC:catalog-02-02_06
domestic:SAAC:catalog-02-02_07
domestic:SAAC:catalog-02-02_08
domestic:SAAC:catalog-02-02_09
domestic:SAAC:catalog-02-02_10
domestic:SAAC:catalog-02-02_11
domestic:SAAC:catalog-02-02_12
domestic:SAAC:catalog-02-02_13
domestic:SAAC:catalog-02-02_14
domestic:SAAC:catalog-02-02_15
domestic:SAAC:catalog-02-02_16
domestic:SAAC:catalog-02-02_17
domestic:SAAC:catalog-03-03_01_01
domestic:SAAC:catalog-03-03_01_02
domestic:SAAC:catalog-03-03_02_01
domestic:SAAC:catalog-03-03_02_02
domestic:SAAC:catalog-03-03_02_03
domestic:SAAC:catalog-03-03_02_04
domestic:SAAC:catalog-03-03_03_01
domestic:SAAC:catalog-03-03_03_02
domestic:SAAC:catalog-03-03_03_03
domestic:SAAC:catalog-03-03_03_04
domestic:SAAC:catalog-03-03_03_05
domestic:SAAC:catalog-03-03_04_01
domestic:SAAC:catalog-03-03_04_02
domestic:SAAC:catalog-03-03_04_03
domestic:SAAC:catalog-03-03_04_04
domestic:SAAC:catalog-03-03_04_05
domestic:SAAC:catalog-03-03_05_01
domestic:SAAC:catalog-03-03_05_02
domestic:SAAC:catalog-03-03_06_01
domestic:SAAC:catalog-03-03_06_02
domestic:SAAC:catalog-03-03_06_03
domestic:SAAC:catalog-03-03_06_04
domestic:SAAC:catalog-03-03_06_05
domestic:SAAC:catalog-03-03_06_06
domestic:SAAC:catalog-03-03_06_07
domestic:SAAC:catalog-03-03_06_08
domestic:SAAC:catalog-03-03_06_09
domestic:SAAC:catalog-04-04_01
domestic:SAAC:catalog-04-04_02
domestic:SAAC:catalog-04-04_03
domestic:SAAC:catalog-04-04_04
domestic:SAAC:catalog-04-04_05
domestic:SAAC:catalog-05-05_01
domestic:SAAC:catalog-05-05_19
domestic:SAAC:catalog-05-05_21
domestic:SAAC:catalog-05-05_22
domestic:SAAC:catalog-05-05_35
domestic:SAAC:catalog-05-05_36
domestic:SAAC:catalog-05-05_37
domestic:SAAC:catalog-05-05_38
domestic:SAAC:catalog-05-05_40
domestic:SAAC:catalog-05-05_60
domestic:SAAC:catalog-05-05_74
domestic:SAAC:catalog-05-05_77
domestic:SAAC:catalog-05-05_78
domestic:SAAC:catalog-05-05_79
domestic:SAAC:catalog-05-05_81
domestic:SAAC:catalog-05-05_83
domestic:SAAC:catalog-05-05_85
domestic:SAAC:catalog-05-05_86
domestic:SAAC:catalog-05-05_87
domestic:SAAC:catalog-05-05_88
domestic:SAAC:catalog-05-05_89
domestic:SAAC:catalog-05-05_90
domestic:SAAC:catalog-06-06_01
domestic:SAAC:catalog-06-06_02
domestic:SAAC:catalog-06-06_03
domestic:SAAC:catalog-06-06_04
domestic:SAAC:catalog-06-06_05
domestic:SAAC:catalog-06-06_06
domestic:SAAC:catalog-06-06_07
domestic:SAAC:catalog-06-06_08
domestic:SAAC:catalog-06-06_10
domestic:SAAC:catalog-06-06_11
domestic:SAAC:catalog-06-06_12
domestic:MMZY:lead-周恩来与第一届人民政协会议的召开
domestic:MMSH:lead-新中国成立前民盟对政治协商制度的贡献
```

## 附录 B：瘦身前 review_note

> 现有境外事件页更集中于北平和平接触，政协一届全体会议的境外对应仍需另建证据卡。

## 附录 C：瘦身后完整 ID 列表（167）

```
domestic:SAAC:1949-02-01-01
domestic:SAAC:1949-02-14-01
domestic:SAAC:1949-09-21-05
domestic:SAAC:1949-index-c03
domestic:SAAC:catalog-06-06_09
domestic:NLC:guangmingbao-1948-1949-v2n1
domestic:NLC:guangmingbao-1948-1949-v2n1-article
domestic:NLC:guangmingbao-1948-1949-v2n12
domestic:NLC:guangmingbao-1948-1949-v2n12-article
domestic:NLC:guangmingbao-1948-1949-v2n12-taiwan-liberation
domestic:SAAC:1949-01-08-01
domestic:SAAC:1949-09-21-01
domestic:SAAC:1949-09-21-02
domestic:SAAC:1949-09-21-03
domestic:SAAC:1949-09-21-04
domestic:SAAC:1949-09-21-06
domestic:SAAC:1949-09-21-07
domestic:SAAC:1949-09-22-01
domestic:SAAC:1949-09-22-02
domestic:SAAC:1949-09-23-01
domestic:SAAC:1949-09-25-01
domestic:SAAC:1949-09-26-01
domestic:SAAC:1949-09-27-01
domestic:SAAC:1949-09-27-02
domestic:SAAC:1949-09-28-01
domestic:SAAC:1949-09-29-01
domestic:SAAC:1949-09-29-02
domestic:SAAC:1949-09-30-01
domestic:SAAC:1949-09-30-02
domestic:SAAC:1949-09-30-03
domestic:SAAC:1949-index-c01
domestic:SAAC:1949-index-c02
domestic:SAAC:1949-index-c04
domestic:SAAC:1949-index-c05
domestic:SAAC:1949-index-c06
domestic:SAAC:1949-index-c07
domestic:SAAC:1949-index-c08
domestic:SAAC:1949-index-c09
domestic:SAAC:1949-index-c10
domestic:SAAC:1949-index-c11
domestic:SAAC:1949-index-c12
domestic:SAAC:1949-index-c13
domestic:SAAC:1949-index-c14
domestic:SAAC:1949-index-c15
domestic:SAAC:1949-index-c16
domestic:SAAC:1949-index-c17
domestic:SAAC:1949-index-c18
domestic:SAAC:1949-index-c19
domestic:SAAC:1949-index-c20
domestic:SAAC:1949-index-c21
domestic:SAAC:1949-index-c22
domestic:SAAC:1949-index-c23
domestic:SAAC:1949-index-c24
domestic:SAAC:1949-index-c25
domestic:SAAC:1949-index-c26
domestic:SAAC:1949-index-c27
domestic:SAAC:1949-index-c28
domestic:SAAC:1949-index-c29
domestic:SAAC:1949-index-c30
domestic:SAAC:1949-index-c31
domestic:SAAC:1949-index-c32
domestic:SAAC:1949-item-a01
domestic:SAAC:1949-item-a02
domestic:SAAC:1949-item-a03
domestic:SAAC:1949-item-a04
domestic:SAAC:1949-item-a05
domestic:SAAC:1949-item-a06
domestic:SAAC:1949-item-a07
domestic:SAAC:1949-item-a08
domestic:SAAC:1949-item-a09
domestic:SAAC:1949-item-a10
domestic:SAAC:1949-item-a11
domestic:SAAC:1949-item-a12
domestic:SAAC:1949-item-a13
domestic:SAAC:1949-item-a14
domestic:SAAC:1949-item-a15
domestic:SAAC:1949-item-a16
domestic:SAAC:1949-item-a17
domestic:SAAC:catalog-01-01_13
domestic:SAAC:catalog-01-01_17
domestic:SAAC:catalog-01-01_18
domestic:SAAC:catalog-01-01_19
domestic:SAAC:catalog-01-01_20
domestic:SAAC:catalog-01-01_21
domestic:SAAC:catalog-01-01_22
domestic:SAAC:catalog-02-02_01
domestic:SAAC:catalog-02-02_02
domestic:SAAC:catalog-02-02_03
domestic:SAAC:catalog-02-02_04
domestic:SAAC:catalog-02-02_05
domestic:SAAC:catalog-02-02_06
domestic:SAAC:catalog-02-02_07
domestic:SAAC:catalog-02-02_08
domestic:SAAC:catalog-02-02_09
domestic:SAAC:catalog-02-02_10
domestic:SAAC:catalog-02-02_11
domestic:SAAC:catalog-02-02_12
domestic:SAAC:catalog-02-02_13
domestic:SAAC:catalog-02-02_14
domestic:SAAC:catalog-02-02_15
domestic:SAAC:catalog-02-02_16
domestic:SAAC:catalog-02-02_17
domestic:SAAC:catalog-03-03_01_01
domestic:SAAC:catalog-03-03_01_02
domestic:SAAC:catalog-03-03_02_01
domestic:SAAC:catalog-03-03_02_02
domestic:SAAC:catalog-03-03_02_03
domestic:SAAC:catalog-03-03_02_04
domestic:SAAC:catalog-03-03_03_02
domestic:SAAC:catalog-03-03_03_03
domestic:SAAC:catalog-03-03_03_04
domestic:SAAC:catalog-03-03_03_05
domestic:SAAC:catalog-03-03_04_01
domestic:SAAC:catalog-03-03_04_02
domestic:SAAC:catalog-03-03_04_03
domestic:SAAC:catalog-03-03_04_04
domestic:SAAC:catalog-03-03_04_05
domestic:SAAC:catalog-03-03_05_01
domestic:SAAC:catalog-03-03_05_02
domestic:SAAC:catalog-03-03_06_01
domestic:SAAC:catalog-03-03_06_02
domestic:SAAC:catalog-03-03_06_03
domestic:SAAC:catalog-03-03_06_04
domestic:SAAC:catalog-03-03_06_05
domestic:SAAC:catalog-03-03_06_06
domestic:SAAC:catalog-03-03_06_07
domestic:SAAC:catalog-03-03_06_08
domestic:SAAC:catalog-03-03_06_09
domestic:SAAC:catalog-04-04_01
domestic:SAAC:catalog-04-04_02
domestic:SAAC:catalog-04-04_03
domestic:SAAC:catalog-04-04_04
domestic:SAAC:catalog-04-04_05
domestic:SAAC:catalog-05-05_01
domestic:SAAC:catalog-05-05_19
domestic:SAAC:catalog-05-05_21
domestic:SAAC:catalog-05-05_22
domestic:SAAC:catalog-05-05_35
domestic:SAAC:catalog-05-05_36
domestic:SAAC:catalog-05-05_37
domestic:SAAC:catalog-05-05_38
domestic:SAAC:catalog-05-05_40
domestic:SAAC:catalog-05-05_60
domestic:SAAC:catalog-05-05_74
domestic:SAAC:catalog-05-05_77
domestic:SAAC:catalog-05-05_78
domestic:SAAC:catalog-05-05_79
domestic:SAAC:catalog-05-05_81
domestic:SAAC:catalog-05-05_83
domestic:SAAC:catalog-05-05_85
domestic:SAAC:catalog-05-05_86
domestic:SAAC:catalog-05-05_87
domestic:SAAC:catalog-05-05_88
domestic:SAAC:catalog-05-05_89
domestic:SAAC:catalog-05-05_90
domestic:SAAC:catalog-06-06_01
domestic:SAAC:catalog-06-06_02
domestic:SAAC:catalog-06-06_03
domestic:SAAC:catalog-06-06_04
domestic:SAAC:catalog-06-06_05
domestic:SAAC:catalog-06-06_06
domestic:SAAC:catalog-06-06_07
domestic:SAAC:catalog-06-06_08
domestic:SAAC:catalog-06-06_10
domestic:SAAC:catalog-06-06_11
domestic:SAAC:catalog-06-06_12
domestic:MMZY:lead-周恩来与第一届人民政协会议的召开
```
