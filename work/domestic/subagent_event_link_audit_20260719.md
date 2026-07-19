# 事件-候选链接审计与补强报告

- 日期：2026-07-19
- Agent：mingmeng-history-research / 事件-候选链接审计与补强
- 范围：`data/domestic/event_coverage.json` × `data/domestic/candidates.jsonl`（9 事件 / 352 候选）
- 原则：仅安全挂接（明确 `event_tags` 或题名/日期明显属于该事件，且 candidate_id 存在）
- 约束：不改 `review_status`；不改证据等级字段；L4 仅作事件索引线索，不升格为原件
- 校验：`python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json`
  - 结果：`{"candidate_ids": 382, "events": 9, "missing_candidate_references": [], "pair_status_counts": {"pair_available": 1, "pair_partial": 8}}`
  - exit code：0

## 一、每事件引用数前后

| event_id | 事件名 | 审计前 | 审计后 | 本 agent 新增 | 并发保留新增 | 净增 |
|---|---|---:|---:|---:|---:|---:|
| `domestic-1941-formation` | 1941年中国民主政团同盟成立 | 8 | 13 | +5 | +0 | +5 |
| `domestic-1944-reorganization` | 1944年改组并更名为中国民主同盟 | 11 | 16 | +5 | +0 | +5 |
| `domestic-1945-first-congress` | 1945年民盟第一次全国代表大会 | 19 | 23 | +4 | +0 | +4 |
| `domestic-1946-pcc` | 1946年政治协商会议（旧政协） | 24 | 25 | +1 | +0 | +1 |
| `domestic-1946-refuse-national-assembly` | 1946年民盟拒绝参加国民大会 | 19 | 21 | +1 | +1 | +2 |
| `domestic-1946-li-wen` | 1946年李公朴、闻一多遇害及各方反应 | 15 | 36 | +0 | +21 | +21 |
| `domestic-1947-illegal-dissolution` | 1947年民盟被宣布非法与组织解散 | 48 | 61 | +5 | +8 | +13 |
| `domestic-1948-third-plenum-may-day` | 1948年一届三中全会及响应“五一口号” | 11 | 19 | +8 | +0 | +8 |
| `domestic-1949-new-pcc` | 1949年新政协筹备、民主人士北上与第一届全体会议 | 10 | 173 | +163 | +0 | +163 |
| **合计** | | **165** | **387** | **+192** | **+30** | **+222** |

> 说明：审计过程中另一子任务并发写入了 1947《光明報》新十二号文章级拆分挂接；本报告将其记为「并发保留新增」，不回滚。

## 二、本 agent 新增挂接列表

### `domestic-1941-formation`（本 agent +5）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:HNMM:lead-民盟精神解析` | 1941—1948 | L4 | 民盟精神解析 | tags=`1941民盟前身；1946李闻血案；1947民盟被宣布非法` |
| `domestic:MMSH:lead-新中国成立前民盟对政治协商制度的贡献` | 1941—1949 | L4 | 新中国成立前民盟对政治协商制度的贡献 | tags=`1941民盟前身；1949政协一届全会` |
| `domestic:NLC:minmeng-wenxian-1946-whole` | 1946-12 | L2 | 《民主同盟文獻》 | tags=`1941成立；1944改组更名；1945第一次全国代表大会` |
| `domestic:NLC:minmeng-wenxian-1946-formation-declaration` | 1941-10-10 | L2 | 中国民主政团同盟成立宣言 | tags=`1941成立` |
| `domestic:NLC:minmeng-wenxian-1946-ten-program` | 1941-10-10 | L2 | 中国民主政团同盟对时局主张纲领 | tags=`1941成立` |

### `domestic-1944-reorganization`（本 agent +5）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:MMYunnan:democracy-weekly-run-1944-1946` | 1944-12-09/1946-08-02 | L4 | 昆明《民主周刊》出版沿革与馆藏追索线索 | tags=`1946李闻血案；1944改组更名` |
| `domestic:NLC:minxian-v1n1-1944-05-16` | 1944-05-16 | L1 | 《民憲》第一卷第一期 | tags=`1944改组更名` |
| `domestic:NLC:minxian-v1n6-1944-08-15` | 1944-08-15 | L1 | 《民憲》第一卷第六期 | tags=`1944改组更名` |
| `domestic:NLC:minxian-v1n9-1944-11-20` | 1944-11-20 | L1 | 《民憲》第一卷第九期 | tags=`1944改组更名` |
| `domestic:NLC:minxian-v1n9-democracy-vs-nondemocracy-1944-11-20` | 1944-11-20 | L1 | 民主政治與非民主政治 | tags=`1944改组更名；1944民主宪政论述` |

### `domestic-1945-first-congress`（本 agent +4）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:NLC:minmeng-wenxian-1946-whole` | 1946-12 | L2 | 《民主同盟文獻》 | tags=`1941成立；1944改组更名；1945第一次全国代表大会` |
| `domestic:NLC:minmeng-wenxian-1946-situation-declaration-1945-01-15` | 1945-01-15 | L2 | 时局宣言 | tags=`1945第一次全国代表大会` |
| `domestic:NLC:minmeng-wenxian-1946-minmeng-platform-1945` | 1945-10 | L2 | 中国民主同盟纲领 | tags=`1945第一次全国代表大会` |
| `domestic:NLC:minmeng-wenxian-1946-congress-declaration-1945-10-16` | 1945-10-16 | L2 | 中国民主同盟临时全国代表大会宣言 | tags=`1945第一次全国代表大会` |

### `domestic-1946-pcc`（本 agent +1）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:WS:pcc-national-assembly-resolution-1946` | 1946 | LX | 政治协商会议国民大会问题决议案 | tags=`1946旧政协；1946拒绝国民大会` |

### `domestic-1946-refuse-national-assembly`（本 agent +1）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:RMrb:1946-11-19-national-assembly-boycott` | 1946-11-19 | L2 | 《人民日报》1946年11月19日第1版：国民大会开幕后中共和其他民主党派拒绝出席的报道 | tags=`1946拒绝国民大会` |

### `domestic-1946-li-wen`（本 agent +0）

无新增。李闻相关声明、DRNH 档案、《光明報》新八—十号及新二十二号「邹李闻陶」特辑等在审计前已挂接完毕。

### `domestic-1947-illegal-dissolution`（本 agent +5）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:HNMM:lead-民盟精神解析` | 1941—1948 | L4 | 民盟精神解析 | tags=`1941民盟前身；1946李闻血案；1947民盟被宣布非法` |
| `domestic:BJTZB:lead-人民民主统一战线的巩固和扩大` | 1947—1948 | L4 | 人民民主统一战线的巩固和扩大 | tags=`1947民盟被宣布非法；1948民盟一届三中全会` |
| `domestic:HBMJ:lead-民建简史第三章-迎接新中国的诞生` | 1947-11 | L4 | 民建简史第三章：迎接新中国的诞生 | tags=`1947民盟被宣布非法` |
| `domestic:ZJMG:lead-中国国民党革命委员会60年-一-` | 1947 | L4 | 中国国民党革命委员会60年（一） | tags=`1947民盟被宣布非法` |
| `domestic:FJMM:lead-少年记忆-初识民盟` | 1947 | L4 | 少年记忆·初识民盟 | tags=`1947民盟被宣布非法` |

### `domestic-1948-third-plenum-may-day`（本 agent +8）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:SAAC:1948-08-01-01` | 1948-08-01 | L1 | 毛泽东关于召集新政协会议的时间、地点等问题给李济深、沈钧儒等的电报 | tags=`1948新政协；民主党派协商` |
| `domestic:SAAC:1948-10-01-01` | 1948-10-01 | L1 | 沈钧儒、谭平山等民主人士关于希望早日召集新政协会议给毛泽东的电报 | tags=`1948新政协；民主人士北上` |
| `domestic:SAAC:1948-10-08-01` | 1948-10-08 | L1 | 中共中央关于约集沈钧儒、谭平山等征求对召开新政协诸问题的意见给高岗、李富春的电报 | tags=`1948新政协；民主党派协商` |
| `domestic:SAAC:catalog-01-01_03` | 1948-05-01 | L1 | 中共中央关于邀请各民主党派及人民团体代表来解放区召开政治协商会议给上海局、香港分局的指示 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_05` | 1948-05-07 | L1 | 中共中央关于与各民主党派及人民团体交换召开政治协商会议的意见给上海局、香港分局等的指示 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_10` | 1948-10-31 | L1 | 钱之光关于报送在香港的民主人士输送内地计划给周恩来、任弼时等的电报 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_11` | 1948-11-20 | L1 | 周恩来拟写的中共中央关于港沪两地迅速动员一批民主人士等经天津进入解放区给上海局、香港分局的电报 | tags=`新政协筹备；1948五一口号` |
| `domestic:93JS:lead-历史的必然-郑重的选择-中共中央发布-五一口号-的历史由` | 1948-05 | L4 | 历史的必然 郑重的选择——中共中央发布“五一口号”的历史由来 | tags=`1948五一口号；1947民盟被宣布非法` |

### `domestic-1949-new-pcc`（本 agent +163）

| candidate_id | 日期 | 等级 | 题名 | 挂接依据 |
|---|---|---|---|---|
| `domestic:SAAC:1949-01-08-01` | 1949-01-08 | L1 | 中共中央政治局会议通过的《目前形势和党在一九四九年的任务》 | tags=`1949新政协筹备；解放战争` |
| `domestic:SAAC:1949-09-21-01` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议单位及代表名单 | tags=`1949第一届政协；民盟代表` |
| `domestic:SAAC:1949-09-21-02` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议代表签名册 | tags=`1949第一届政协；民盟代表` |
| `domestic:SAAC:1949-09-21-03` | 1949-09-21/1949-09-30 | L1 | 中国人民政治协商会议第一届全体会议程序 | tags=`1949第一届政协；会议制度` |
| `domestic:SAAC:1949-09-21-04` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议主席团名单 | tags=`1949第一届政协；组织构成` |
| `domestic:SAAC:1949-09-21-06` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议第一天会议记录 | tags=`1949第一届政协；民盟代表发言` |
| `domestic:SAAC:1949-09-21-07` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议主席团第一次会议纪要 | tags=`1949第一届政协；会议组织` |
| `domestic:SAAC:1949-09-22-01` | 1949-09-22 | L1 | 谭平山关于中国人民政治协商会议筹备会第二小组工作的报告 | tags=`1949第一届政协；政协筹备` |
| `domestic:SAAC:1949-09-22-02` | 1949-09-22 | L1 | 周恩来关于中国人民政治协商会议共同纲领草案的起草经过及其特点的报告 | tags=`1949第一届政协；共同纲领` |
| `domestic:SAAC:1949-09-23-01` | 1949-09-23 | L1 | 中国人民政治协商会议第一届全体会议第三天会议记录 | tags=`1949第一届政协；民主党派发言` |
| `domestic:SAAC:1949-09-25-01` | 1949-09-25 | L1 | 中国人民政治协商会议组织法草案整理委员会第一次会议记录 | tags=`1949第一届政协；政协组织法` |
| `domestic:SAAC:1949-09-26-01` | 1949-09-26 | L1 | 毛泽东给周恩来的信 | tags=`1949第一届政协；建国筹备` |
| `domestic:SAAC:1949-09-27-01` | 1949-09-27 | L1 | 中国人民政治协商会议第一届全体会议通过的《中国人民政治协商会议组织法》 | tags=`1949第一届政协；政协组织法` |
| `domestic:SAAC:1949-09-27-02` | 1949-09-27 | L1 | 中国人民政治协商会议第一届全体会议通过的《中华人民共和国中央人民政府组织法》 | tags=`1949第一届政协；中央人民政府组织法` |
| `domestic:SAAC:1949-09-28-01` | 1949-09-28 | L1 | 中国人民政治协商会议共同纲领草案整理委员会会议记录 | tags=`1949第一届政协；共同纲领` |
| `domestic:SAAC:1949-09-29-01` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议通过的《中国人民政治协商会议共同纲领》 | tags=`1949第一届政协；共同纲领` |
| `domestic:SAAC:1949-09-29-02` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议第七天会议记录 | tags=`1949第一届政协；共同纲领` |
| `domestic:SAAC:1949-09-30-01` | 1949-09-30 | L1 | 中国人民政治协商会议第一届全体会议宣言（草案） | tags=`1949第一届政协；建国宣言` |
| `domestic:SAAC:1949-09-30-02` | 1949-09-30 | L1 | 中国人民政治协商会议第一届全体会议全国委员会委员名单 | tags=`1949第一届政协；全国委员会` |
| `domestic:SAAC:1949-09-30-03` | 1949-09-30 | L1 | 朱德在中国人民政治协商会议第一届全体会议上致闭幕词 | tags=`1949第一届政协；会议闭幕` |
| `domestic:SAAC:1949-index-c01` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议会场 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c02` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议开幕式签到簿 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c04` | 1949-09-21 | L1 | 毛泽东在中国人民政治协商会议第一届全体会议上致开幕词 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c05` | 1949-09-21 | L1 | 中国共产党代表刘少奇在中国人民政治协商会议第一届全体会议上的讲话 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c06` | 1949-09-21 | L1 | 特邀代表宋庆龄在中国人民政治协商会议第一届全体会议上的讲话 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c07` | 1949-09-21 | L1 | 中华全国总工会副主席李立三在中国人民政治协商会议第一届全体会议上的讲话 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c08` | 1949-09-21 | L1 | 特邀代表张治中在中国人民政治协商会议第一届全体会议上的讲话 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c09` | 1949-09-21 | L1 | 特邀代表程潜在中国人民政治协商会议第一届全体会议上的讲话 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c10` | 1949-09-21 | L1 | 华侨代表司徒美堂在中国人民政治协商会议第一届全体会议上的讲话 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c11` | 1949-09-21 | L1 | 何香凝、陈毅、黄炎培在中国人民政治协商会议第一届全体会议上讲话照片 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c12` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议会议现场 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c13` | 1949-09-22 | L1 | 董必武关于草拟中华人民共和国中央人民政府组织法的经过及其基本内容的报告 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c14` | 1949-09-22 | L1 | 林伯渠、谭平山在中国人民政治协商会议第一届全体会议上作报告照片 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c15` | 1949-09-22 | L1 | 中国人民政治协商会议第一届全体会议主席团常委会第一次会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c16` | 1949-09-22 | L1 | 中国人民政治协商会议筹备会第六小组第五次全体会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c17` | 1949-09-22 | L1 | 中国人民政治协商会议第一届全体会议会刊第二期 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c18` | 1949-09-23 | L1 | 中国国民党革命委员会主席李济深在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c19` | 1949-09-23 | L1 | 人民解放军第二野战军首席代表刘伯承在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c20` | 1949-09-23 | L1 | 特邀代表傅作义在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c21` | 1949-09-23 | L1 | 人民解放军第三野战军首席代表粟裕在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c22` | 1949-09-23 | L1 | 中华全国民主青年联合总会首席代表廖承志在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c23` | 1949-09-23 | L1 | 中国人民政治协商会议第一届全体会议会刊第三期 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c24` | 1949-09-24 | L1 | 中华全国民主妇女联合会代表邓颖超在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c25` | 1949-09-24 | L1 | 九三学社首席代表许德珩在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c26` | 1949-09-24 | L1 | 马明方、高崇民、彭泽民、张云逸、乌兰夫、梅兰芳、谢邦定在中国人民政治协商会议第一届全体会议上发言照片 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c27` | 1949-09-24 | L1 | 中国人民政治协商会议秘书处关于召开主席团常委会第二次会议的通知 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c28` | 1949-09-24 | L1 | 召开政府组织法草案整理委员会第一次会议的通知 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c29` | 1949-09-24 | L1 | 中国人民政治协商会议第一届全体会议会刊第四期 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c30` | 1949-09-25 | L1 | 贺龙在中国人民政治协商会议第一届全体会议上发言照片 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c31` | 1949-09-25 | L1 | 中国人民政治协商会议代表提案审查委员会第一次会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-index-c32` | 1949-09-25 | L1 | 政府组织法草案整理委员会第一次全体会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a01` | 1949-09-25 | L1 | 国旗国徽国歌纪年国都协商会座谈会主要发言摘录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a02` | 1949-09-25 | L1 | 中国人民政治协商会议第一届全体会议会刊第五期 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a03` | 1949-09-26 | L1 | 中国人民政治协商会议第一届全体会议代表提案审查委员会审查报告 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a04` | 1949-09-26 | L1 | 国旗国徽国歌国都纪年审查委员会第一次会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a05` | 1949-09-26 | L1 | 中国人民政治协商会议第一届全体会议会刊第六期 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a06` | 1949-09-27 | L1 | 蓝公武、赵寿山、刘善本、刘清扬在中国人民政治协商会议第一届全体会议上发言照片 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a07` | 1949-09-27 | L1 | 中国人民政治协商会议第一届全体会议第六天会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a08` | 1949-09-27 | L1 | 中国人民政治协商会议第一届全体会议主席团常委会第三次会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a09` | 1949-09-27 | L1 | 中国人民政治协商会议第一届全体会议会刊第七期 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a10` | 1949-09-28 | L1 | 中国人民政治协商会议第一届全体会议会刊第八期 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a11` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议第七天会议议程 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a12` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议关于选举政协全国委员会和中央人民政府委员会的规定 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a13` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议第七天会议对代表提案的决议 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a14` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议主席团第二次会议纪要 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a15` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议主席团常委会第四次会议记录 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a16` | 1949-09-30 | L1 | 中华人民共和国中央人民政府委员会候选名单 | tags=`1949第一届政协` |
| `domestic:SAAC:1949-item-a17` | 1949-09-30 | L1 | 参加选举中华人民共和国中央人民政府主席、副主席及委员的代表人数统计 | tags=`1949第一届政协` |
| `domestic:SAAC:catalog-01-01_03` | 1948-05-01 | L1 | 中共中央关于邀请各民主党派及人民团体代表来解放区召开政治协商会议给上海局、香港分局的指示 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_05` | 1948-05-07 | L1 | 中共中央关于与各民主党派及人民团体交换召开政治协商会议的意见给上海局、香港分局等的指示 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_10` | 1948-10-31 | L1 | 钱之光关于报送在香港的民主人士输送内地计划给周恩来、任弼时等的电报 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_11` | 1948-11-20 | L1 | 周恩来拟写的中共中央关于港沪两地迅速动员一批民主人士等经天津进入解放区给上海局、香港分局的电报 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_13` | 1949-01-20 | L1 | 中共中央关于邀请张澜、黄炎培北上给方方、潘汉年等的电报 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_17` | 1949-03-21/1949-03-22 | L1 | 叶剑英、李克农关于迎接中央迁平工作布置给周恩来等的请示电报及周恩来的复电 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_18` | 1949-03-25 | L1 | 毛泽东在北平西苑机场与各界群众代表见面、检阅部队 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_19` | 1949-03-26 | L1 | 《人民日报》关于中共中央和人民解放军总部进驻北平的报道 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_20` | 1949-06-19 | L1 | 毛泽东给宋庆龄的信 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_21` | 1949-06-21 | L1 | 周恩来给宋庆龄的信 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-01-01_22` | 1949-06-30 | L1 | 毛泽东《论人民民主专政》手稿 | tags=`新政协筹备；1948五一口号` |
| `domestic:SAAC:catalog-02-02_01` | 1949-06-14 | L1 | 新政治协商会议筹备会关于召开成立会的通知 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_02` | 1949-06-15 | L1 | 毛泽东在新政治协商会议筹备会开幕典礼上的讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_03` | 1949-06-15 | L1 | 朱德在新政治协商会议筹备会开幕典礼上的讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_04` | 1949-06-15 | L1 | 李济深在新政治协商会议筹备会开幕典礼上的讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_05` | 1949-06-15 | L1 | 沈钧儒在新政治协商会议筹备会开幕典礼上的讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_06` | 1949-06-15 | L1 | 郭沫若在新政治协商会议筹备会开幕典礼上的讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_07` | 1949-06-15 | L1 | 陈叔通在新政治协商会议筹备会开幕典礼上的讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_08` | 1949-06-15 | L1 | 陈嘉庚在新政治协商会议筹备会开幕典礼上的讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_09` | 1949-06-16 | L1 | 新政治协商会议筹备会第一次全体会议议程 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_10` | 1949-06-16 | L1 | 新政治协商会议筹备会组织条例 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_11` | 1949-06-16 | L1 | 新政治协商会议筹备会常委会第一次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_12` | 1949-06-19 | L1 | 新政治协商会议筹备会关于参加新政治协商会议的单位及其代表名额的规定 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_13` | 1949-06-19 | L1 | 新政治协商会议筹备会第一次全体会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_14` | 1949-07-11 | L1 | 周恩来关于组织新政治协商会议筹备会党组干事会及常委名单的通知 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_15` | 1949-07-11 | L1 | 新政治协商会议筹备会秘书长会议第一次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_16` | 1949-07-13 | L1 | 新政治协商会议筹备会秘书长会议第二次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-02-02_17` | 1949-07-18 | L1 | 新政治协商会议筹备会秘书长会议第三次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_01_01` | 1949-06-17 | L1 | 新政治协商会议筹备会第一小组第一次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_01_02` | 1949-06-17 | L1 | 新政治协商会议筹备会第一小组关于召开小组会议讨论新政治协商会议参加单位及人数事项的通知 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_02_01` | 1949-06-18 | L1 | 新政治协商会议筹备会第二小组第一次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_02_02` | 1949-06-28 | L1 | 新政治协商会议筹备会第二小组第二次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_02_03` | 1949-08-18 | L1 | 新政治协商会议筹备会第二小组第三次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_02_04` | 1949-09-15 | L1 | 新政治协商会议筹备会第二小组第四次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_03_01` | 1948 | L1 | 周恩来拟写的新民主主义纲领（草案初稿） | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_03_02` | 1949-06-18 | L1 | 新政治协商会议筹备会第三小组成立会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_03_03` | 1949-06 | L1 | 新政治协商会议筹备会第三小组第一分组意见 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_03_04` | 1949-06-25 | L1 | 新政治协商会议筹备会第三小组第四分组意见 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_03_05` | 1949-06-30 | L1 | 新政治协商会议筹备会第三小组第二分组讨论总结 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_04_01` | 1949-06-18 | L1 | 新政治协商会议筹备会第四小组第一次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_04_02` | 1949-07-09 | L1 | 新政治协商会议筹备会第四小组起草委员会第一次会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_04_03` | 1949-07-20 | L1 | 董必武关于修改中华人民共和国中央人民政府组织大纲草案给赖亚力的信 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_04_04` | 1949-08 | L1 | 中华人民共和国中央人民政府组织表 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_04_05` | 1949-09-02 | L1 | 《中华人民共和国中央人民政府组织法（草案）》 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_05_01` | 1949-06-18 | L1 | 新政治协商会议筹备会第五小组第一次小组会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_05_02` | 1949-08-21 | L1 | 新政治协商会议筹备会第五小组第二次小组会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_01` | 1949-07-04 | L1 | 新政治协商会议筹备会第六小组第一次全体会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_02` | 1949-07-10 | L1 | 新政治协商会议筹备会征求国旗国徽图案及国歌辞谱启事（草案） | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_03` | 1949-08-05 | L1 | 新政治协商会议筹备会第六小组第二次全体会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_04` | 1949-08-24 | L1 | 新政治协商会议筹备会第六小组第三次全体会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_05` | 1949-08 | L1 | 曾联松设计的国旗图案 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_06` | 1949-09-14 | L1 | 新政治协商会议筹备会第六小组第四次全体会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_07` | 1949-09-22 | L1 | 新政治协商会议筹备会第六小组第五次全体会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_08` | 1949-09 | L1 | 新政治协商会议筹备会编印的国旗图案参考资料 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-03-03_06_09` | 1949-09 | L1 | 新政治协商会议筹备会国旗分解图 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-04-04_01` | 1949-09-17 | L1 | 周恩来、李维汉在中国人民政治协商会议筹备会第二次全体会议上讲话 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-04-04_02` | 1949-09-17 | L1 | 中国人民政治协商会议筹备会第二次全体会议决议案 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-04-04_03` | 1949-09-17 | L1 | 中国人民政治协商会议筹备会第二次全体会议记录 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-04-04_04` | 1949-09 | L1 | 中国人民政治协商会议第一届全体会议主席团及秘书长名单（草案） | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-04-04_05` | 1949-09-20 | L1 | 中国人民政治协商会议筹备会关于召开中国人民政治协商会议第一届全体会议的通知 | tags=`新政协筹备；1949政协筹备会` |
| `domestic:SAAC:catalog-05-05_01` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议会场 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_19` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议主席团第一次会议议程 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_21` | 1949-09-21 | L1 | 中国人民政治协商会议拟制国旗国徽国歌方案组报告 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_22` | 1949-09-21 | L1 | 中国人民政治协商会议第一届全体会议会刊第一期 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_35` | 1949-09-23 | L1 | 全国工商界首席代表陈叔通在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_36` | 1949-09-23 | L1 | 中华全国文学艺术界联合会首席代表沈雁冰（茅盾）在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_37` | 1949-09-23 | L1 | 台湾民主自治同盟首席代表谢雪红在中国人民政治协商会议第一届全体会议上的发言 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_38` | 1949-09-23 | L1 | 黄克诚、梁希、胡乔木在中国人民政治协商会议第一届全体会议上发言照片 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_40` | 1949-09-23 | L1 | 中国人民政治协商会议组织法草案座谈会记录 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_60` | 1949-09-26 | L1 | 中国人民政治协商会议第一届全体会议通过的关于国旗、国徽、国歌、国都、纪年的四个决议草案 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_74` | 1949-09-29 | L1 | 中国人民政治协商会议第一届全体会议主席团常委会关于代表提案的审查报告 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_77` | 1949-09-30 | L1 | 中华人民共和国中央人民政府委员会选举办法及监票人员名单（草案） | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_78` | 1949-09-30 | L1 | 中华人民共和国中央人民政府委员会选举票 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_79` | 1949-09-30 | L1 | 中国人民政治协商会议第一届全体会议选举现场 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_81` | 1949-09-30 | L1 | 中国人民政治协商会议第一届全体会议致中国人民解放军全体指挥员战斗员的慰问电 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_83` | 1949-09-30 | L1 | 中华人民共和国中央人民政府主席、副主席及全体委员名单 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_85` | 1949-09-30 | L1 | 中国人民政治协商会议秘书处给中国人民政治协商会议第一届全国委员会委员、秘书长的当选通知 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_86` | 1949-09-30 | L1 | 中国人民政治协商会议秘书处关于周恩来当选为中央人民政府委员的通知 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_87` | 1949-09-30 | L1 | 中国人民政治协商会议第一届全体会议第八天会议记录 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_88` | 1949-09-30 | L1 | 人民英雄纪念碑奠基典礼程序 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_89` | 1949-09-30 | L1 | 周恩来为人民英雄纪念碑书写的碑文 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-05-05_90` | 1949-09-30 | L1 | 毛泽东为人民英雄纪念碑奠基 | tags=`1949政协一届全会` |
| `domestic:SAAC:catalog-06-06_01` | 1949-09-30 | L1 | 中央人民政府委员会第一次会议通知 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_02` | 1949-10-01 | L1 | 中国人民政治协商会议第一届全体会议会刊第十一期 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_03` | 1949-10-01 | L1 | 中央人民政府委员会第一次会议签到簿 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_04` | 1949-10 | L1 | 中央人民政府委员会第一次会议议程 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_05` | 1949-10-01 | L1 | 中央人民政府委员会第一次会议记录 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_06` | 1949-10-01 | L1 | 中央人民政府委员会第一次会议任命周恩来为政务院总理兼外交部长的通知书 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_07` | 1949-10-01 | L1 | 毛泽东与中央人民政府委员会部分委员合影 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_08` | 1949-10-01 | L1 | 庆祝中华人民共和国中央人民政府成立典礼程序（附周恩来批示） | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_10` | 1949-10-01 | L1 | 周恩来关于将《中华人民共和国中央人民政府公告》通知各国政府给黄华的电报 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_11` | 1949-10-01 | L1 | 饶彰风致中央统战部的电报：香港《华商报》等同人举行升旗典礼 | tags=`1949开国大典` |
| `domestic:SAAC:catalog-06-06_12` | 1949-10-01 | L1 | 开国大典原始影像 | tags=`1949开国大典` |
| `domestic:MMZY:lead-周恩来与第一届人民政协会议的召开` | 1945—1949 | L4 | 周恩来与第一届人民政协会议的召开 | tags=`1946拒绝参加国民大会；1949政协一届全会` |
| `domestic:MMSH:lead-新中国成立前民盟对政治协商制度的贡献` | 1941—1949 | L4 | 新中国成立前民盟对政治协商制度的贡献 | tags=`1941民盟前身；1949政协一届全会` |

## 三、并发写入保留（非本 agent 主责，已核 ID 存在）

### `domestic-1946-refuse-national-assembly`

- `domestic:NLC:guangmingbao-1947-12-statement-one-sided-constitution` — 對於片面憲法民盟發表聲明（1947-08-08 / L1）

### `domestic-1946-li-wen`

- `domestic:NLC:guangmingbao-1947-issue22-middle-route-again-deng` — 再論中間路線問題（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-one-year-war-result-lu` — 打了一年多以後的結果（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-cry-recall-xingzhi-deng` — 哭憶行知（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-gongpu-still-beside-zhang` — 公樸，你還在我的身邊（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-learn-taofen-spirit-hu` — 習韜奮精神（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-patriotic-poet-wen-hong` — 愛國詩人聞一多（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-hengshe-tonghua-sa` — 由衡舍桐花談起（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-action-memorial-peng` — 用行動來紀念鄒李聞陶四先生（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-double-effort-people-shen` — 加倍為人民事業努力（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-wipe-out-killers-li` — 撲滅殺人的兇手（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-pass-the-test-hu-sheng` — 過關（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-liwen-anniversary-qian` — 李聞週年祭（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-painful-memorial-chen` — 沉痛紀念鄒李聞陶四先生（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-mourn-and-spur-song` — 悼念逝者，鞭策自己（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-dare-not-forget-chen` — 不敢忘（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-dictators-killed-them-ye` — 是獨裁者殺死了他們！（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-gongpu-rest-in-peace-simu` — 公樸，安眠吧！（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-one-falls-thousands-rise-lu` — 一個倒下去千百個起來（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-history-essays-shen-gong` — 讀史隨筆（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-shantou-black-terror` — 汕頭的黑色恐怖（1947-08-01 / L1）
- `domestic:NLC:guangmingbao-1947-issue22-meixian-recent-look` — 梅縣近貌（1947-08-01 / L1）

### `domestic-1947-illegal-dissolution`

- `domestic:NLC:guangmingbao-1947-12-si-tan-guo-shi` — 肆談國事（1947-08-08 / L1）
- `domestic:NLC:guangmingbao-1947-12-respond-anti-us-military` — 響應反對美軍暴行運動（1947-08-08 / L1）
- `domestic:NLC:guangmingbao-1947-12-second-plenum-domestic-situation` — 民盟二中全會與國內局勢（1947-08-08 / L1）
- `domestic:NLC:guangmingbao-1947-12-interview-shen-junru` — 訪問沈鈞儒先生（1947-08-08 / L1）
- `domestic:NLC:guangmingbao-1947-12-qingmo-democracy-two-paths` — 清末民主運動的兩條路線（1947-08-08 / L1）
- `domestic:NLC:guangmingbao-1947-12-oppose-us-atrocities-shanghai` — 反對美軍暴行（1947-08-08 / L1）
- `domestic:NLC:guangmingbao-1947-12-shanghai-democrats-on-us-atrocities` — 滬民主人士對美軍暴行意見（1947-08-08 / L1）
- `domestic:NLC:guangmingbao-1947-12-students-letter-to-truman` — 學生致杜魯門總統書（1947-08-08 / L1）

## 四、故意不挂 / 回撤原因

| 事件 | 对象 | 原因 |
|---|---|---|
| `domestic-1945-first-congress` | `domestic:DRNH:002-090300-00017-115` | 标签含1945民盟一大，但题名/日期为1945-09昆明监视情报，属李闻前史背景，已挂 li-wen，不作一大核心 |
| `domestic-1945-first-congress` | `domestic:MMZY:lead-楚图南-民盟文章` | L4 多主题复合标签，题名非一大核心文件；已回撤 |
| `domestic-1947-illegal-dissolution` | `domestic:93JS:…五一口号…` | 主体论述五一口号，虽复合标签含1947；已回撤，改挂1948 |
| `domestic-1947-illegal-dissolution` | `domestic:MMZY:lead-楚图南-民盟文章` | L4 多主题概览；已回撤 |
| `domestic-1948-third-plenum-may-day` | `SAAC catalog-01-01_09` | 济南/锦州战役贺电，与三中全会/五一仅弱相关 |
| `domestic-1948-third-plenum-may-day` | `SAAC catalog-01-01_13/17/18/19/20/21/22` | document_date 已在1949，属北上/迁平/开国准备；虽误标1948五一口号，改由1949事件覆盖（13/17–22 已挂1949） |
| `domestic-1949-new-pcc` | `SAAC:1948-04-30-01 / 1948-05-01-01 / HNMM:response-may-day-1948` | 五一口号原件与响应书已挂1948主事件，避免把五一原件二次扩列为1949核心 |
| `domestic-1949-new-pcc` | `SAAC:catalog-01-01_09` | 战役贺电与新政协筹备弱相关 |
| `domestic-1946-li-wen` | `（无漏挂）` | 特辑与核心声明审计前已齐 |
| `全局` | `L4 后期叙述` | 可挂为线索（与既有 CPPCC/地方盟史体例一致），绝不改 authenticity / review_status，不在 domestic_status 中表述为原件 |

### 安全规则

1. 与 `event_coverage.event_tags` 精确匹配（复合标签按 `；`/`;` 拆分）→ 可挂。
2. 同义标签需题名/日期支撑：`1941成立`→formation；`1945第一次全国代表大会`→一大；`1948三中全会`/`1948新政协`→1948；`1949政协一届全会`/`新政协筹备`→1949。
3. 跨年误标拒绝：仅有 `1948五一口号` 但日期≥1949 且题名属北上/开国/理论著作 → 不挂 1948。
4. 双挂允许：相邻事件共享前置文件（如政协国大决议案、1946 汇编整书）。

## 五、任务例举核对

| 例举 | 结果 |
|---|---|
| 1948 新文章未挂 1948 | 审计前 v1n1/v1n12 文章级已挂；本轮补 SAAC 1948-08/10 新政协商电与 5 月邀请/输送指示等 **+8** |
| 李闻特辑未挂 1946李闻 | issue22 特辑与声明/DRNH **审计前已挂**；本轮 **+0** |
| 1941 线索未挂 formation | 补 NLC 成立宣言/十纲领/汇编整书 + 地方盟史 L4 线索 **+5** |
| 1949 SAAC 有标签未挂 | 补一届全会/开国/筹备会 L1 目录条目 **+163**（已回撤纯五一原件双挂） |

## 六、未改动字段确认

- 仅扩展 `event_coverage.json` → `domestic_candidate_ids`
- **未**修改 `candidates.jsonl` 的 `review_status` / `authenticity_level_*` / `event_tags`
- **未**修改各事件的 `pair_status` / `domestic_status` / `review_note`

## 七、返回摘要

- `domestic-1941-formation`: 8 → 13（本 agent 新增 5，净增 5）
- `domestic-1944-reorganization`: 11 → 16（本 agent 新增 5，净增 5）
- `domestic-1945-first-congress`: 19 → 23（本 agent 新增 4，净增 4）
- `domestic-1946-pcc`: 24 → 25（本 agent 新增 1，净增 1）
- `domestic-1946-refuse-national-assembly`: 19 → 21（本 agent 新增 1，净增 2）
- `domestic-1946-li-wen`: 15 → 36（本 agent 新增 0，净增 21）
- `domestic-1947-illegal-dissolution`: 48 → 61（本 agent 新增 5，净增 13）
- `domestic-1948-third-plenum-may-day`: 11 → 19（本 agent 新增 8，净增 8）
- `domestic-1949-new-pcc`: 10 → 173（本 agent 新增 163，净增 163）
- **本 agent 新增挂接条数合计**：192
- **全库净增引用**（含并发）：222
