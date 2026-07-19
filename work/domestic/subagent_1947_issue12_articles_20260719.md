# 《光明報》新十二號文章级拆分报告

- 执行：mingmeng-history-research 国内资料库执行 agent（grok）
- 日期：2026-07-19
- 原刊：`NLC404-01J000514-72818`，《光明報》新十二號，1947-08-08，16 页
- 页图：`work/domestic/continue_pages/1947_12/page-01.png` … `page-16.png`
- 已有社论：`domestic:NLC:guangmingbao-1947-12-congratulate-second-plenum-editorial`《祝民盟二中全會》（PDF 第 2 页）
- 约束：只新建题名+页界充分的 L1 / `needs_human_review`；不自动 `accepted`；不把目录当正文；不删文件；不 git commit

## 封面目录（page-01，仅导航）

| 目录题名 | 署名 | 本轮处置 |
|---|---|---|
| 肆談國事 | 陳此生 | 新建 p4—6 |
| 響應反對美軍暴行運動 | 黃藥眠 | 新建 p6—7 |
| 民盟二中全會與國內局勢 | 胡愈之 | 新建 p8—9 |
| 民主運動在南洋 | （目录无署名） | **未拆**（见下） |
| 清末民主運動的兩條路線 | 晨曦 | 新建 p12—13 |
| 訪問沈鈞儒先生 | 王健 | 新建 p10—11 |
| 反對美軍暴行（上海通訊） | 黎洪 | 新建 p14—15 |
| 滬民主人士對美軍暴行意見 | （辑录） | 新建 p14—15 |
| 文件：對片面憲法民盟發表聲明 | 民盟 | 新建 p11 |
| 上海學生致杜魯門總統書 | 上海學生抗聯 | 新建 p16 |
| （目录未单列）社論《祝民盟二中全會》 | 《光明報》社 | 已有 p2 |

另：PDF 第 3 页为《短評》多则，目录未单列长文题名，本轮不拆。

## 正文页界（page-02 起目视）

| PDF 页 | 所见正文/栏 |
|---:|---|
| 2 | 社論《祝民盟二中全會》（已登记） |
| 3 | 《短評》多则（訪越南的人民、美國也是受人煽動？等） |
| 4—6 | 陳此生《肆談國事》（一…四节；第 6 页与黄药眠文共用） |
| 6—7 | 黃藥眠《響應反對美軍暴行運動》 |
| 8—9 | 胡愈之《民盟二中全會與國內局勢》（轉載）；同页另栏「民主運動在南洋」短讯 |
| 10—11 | 王健《訪問沈鈞儒先生》；第 11 页左栏转入声明 |
| 11 | 《對於片面憲法民盟發表聲明》（民主文獻） |
| 12—13 | 晨曦《清末民主運動的兩條路線》（民主運動史話之二） |
| 14—15 | 黎洪《反對美軍暴行！》（上海通訊）；下栏「滬民主人士…意見」 |
| 16 | 《學生致杜魯門總統書》；左栏或仍为反美暴行通讯续文 |

## 新增 candidate_id（9）

全部 `authenticity_level_proposed=L1`，`review_status=needs_human_review`，`checked_by=grok`，`checked_at=2026-07-19`。

1. `domestic:NLC:guangmingbao-1947-12-si-tan-guo-shi`  
   《肆談國事》／陳此生／PDF 第 4—6 页／`1947民盟被宣布非法`／core

2. `domestic:NLC:guangmingbao-1947-12-respond-anti-us-military`  
   《響應反對美軍暴行運動》／黃藥眠／PDF 第 6—7 页／`1947民盟被宣布非法`／core

3. `domestic:NLC:guangmingbao-1947-12-second-plenum-domestic-situation`  
   《民盟二中全會與國內局勢》／胡愈之／PDF 第 8—9 页／`1947民盟被宣布非法`／core  
   （优先目标；转载；不作 1947-01 会期臆测）

4. `domestic:NLC:guangmingbao-1947-12-interview-shen-junru`  
   《訪問沈鈞儒先生》／王健／PDF 第 10—11 页／`1947民盟被宣布非法`／core

5. `domestic:NLC:guangmingbao-1947-12-statement-one-sided-constitution`  
   《對於片面憲法民盟發表聲明》／中国民主同盟／PDF 第 11 页／`1946拒绝国民大会`／core

6. `domestic:NLC:guangmingbao-1947-12-qingmo-democracy-two-paths`  
   《清末民主運動的兩條路線》／晨曦／PDF 第 12—13 页／`1947民盟被宣布非法`／related

7. `domestic:NLC:guangmingbao-1947-12-oppose-us-atrocities-shanghai`  
   《反對美軍暴行》／黎洪／PDF 第 14—15 页／`1947民盟被宣布非法`／related

8. `domestic:NLC:guangmingbao-1947-12-shanghai-democrats-on-us-atrocities`  
   《滬民主人士對美軍暴行意見》／《光明報》辑／PDF 第 14—15 页／`1947民盟被宣布非法`／related

9. `domestic:NLC:guangmingbao-1947-12-students-letter-to-truman`  
   《學生致杜魯門總統書》／上海學生抗議美軍暴行聯合會／PDF 第 16 页／`1947民盟被宣布非法`／related

## 未拆目录项及原因

| 目录项 | 原因 |
|---|---|
| 民主運動在南洋 | 第 8 页左栏可见栏目题；内含居鑾分部成立、峇眼筹组等短讯，并与第 8—9 页「要求美軍離華…」类标题及胡愈之正文栏交错。题名可辨，但**单一长文起止页界不充分**，不猜栏界，留待复审。 |
| 短評（第 3 页，非目录长文） | 多则短评并列，无单一可挂长文题名+稳定页界；不拆。 |
| 黎洪文是否延至第 16 页左栏 | 第 16 页左栏叙事口吻相近，但同页右栏已是《學生致杜魯門總統書》。为避免混页，黎洪条**止于第 15 页**；左栏归属待栏界复审。 |

## event_coverage 挂接

- `domestic-1947-illegal-dissolution`（`1947民盟被宣布非法`）：挂入新增 8 条（声明除外）+ 既有社论；更新 `domestic_status` 说明新十二号已有文章级页码定位。
- `domestic-1946-refuse-national-assembly`（`1946拒绝国民大会`）：挂入 `…-statement-one-sided-constitution`（片面宪法声明，主题更贴 1946 拒国大/宪法线）。
- 未乱挂 1948/1949 或其他事件。

## 校验结果

```text
validate_candidates.py
{"records": 361, "failed": 0, "passed": 361}

validate_event_coverage.py
{"candidate_ids": 361, "events": 9, "missing_candidate_references": [],
 "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}
```

- 新增 9 条均为 `needs_human_review`，无自动 `accepted`。
- 既有整期 `domestic:NLC:guangmingbao-1947-1947-12`（accepted 整期身份）与社论条未改写删除。

## 边界说明

- OCR 未作为引文；页界仅据 `continue_pages/1947_12` 页图目视。
- 第 6、11、14—16 页存在多文共页；证据注已标明共用页，复审时应按栏切分。
- 本批不替代 1947-10-27 内政部公函、1947-11-06 解散公告或民盟正式文件原件。
