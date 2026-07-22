# 国内史料研究平台验收收口报告

验收日期：2026-07-22（Asia/Shanghai）  
项目：`mingmeng-history-research`  
验收范围：MiniMax、Grok 及后续 Claude Code 处理的国内资料、数据入库、平台入口和研究边界。

## 结论

国内资料已经成为平台的正式组成部分，不再只是海外研究的附录：候选库、来源库、事件覆盖、SQLite 和网页入口均已接通。

但当前成果应称为“国内史料研究骨架 + 一手影像层”，不能称为“国内原件全部闭环”。`accepted` 只表示记录级审核通过，不表示原件 provenance、全文转录、异文校勘或复制权利已经完成。

## 当前实测基线

```text
candidates.jsonl       689 条，validate 689/689 通过
review_status           647 accepted / 42 needs_human_review
source_registry         89 个来源
event_coverage          9 个事件，0 个悬空候选引用
pair_status             1 pair_available / 8 pair_partial
SQLite                  89 sources / 689 candidates / 647 accepted / 42 pending / 689 decisions
audit                   missing_required=0 / missing_paths=0
```

证据等级分布：

```text
L1 325（其中 304 accepted）
L2 228（其中 226 accepted）
L3  88（其中  70 accepted）
L4  44（其中  43 accepted）
LX   4（其中   4 accepted）
```

## 国内一手资料层

按当前项目口径，最稳妥的一手影像层是 **304 条 accepted L1**，构成为：

| 来源 | accepted L1 | 说明 |
|---|---:|---|
| SAAC | 174 | 国家档案局公开档案影像/档案条目 |
| NLC | 127 | 国家图书馆民国报刊等同期原刊影像 |
| WM | 2 | 公有领域民国时期原始影像镜像 |
| DAJS | 1 | 地方档案馆公开报刊号外影像 |

这 304 条可以作为平台的“国内一手影像”入口，但仍需在页面上显式标注“记录级通过”，不能让用户误解为每条都完成了馆藏实物核验或全文转录。

另外 226 条 accepted L2 主要是正式文献汇编、官方出版物或影印汇编，研究价值高，但不应改称为对应历史事件的原始印本。

## 平台验收

临时启动本地服务后，以下入口均返回 HTTP 200：

```text
/domestic
/domestic/sources
/domestic/events
/domestic/acquisition
/domestic/review
```

国内页面已经提供：候选目录、来源地图、九事件覆盖、人物/地点索引、调档清单和复核看板。当前服务验收后已停止；需要访问时在项目根目录运行 `python3 app.py`。

SQLite 已完成国内候选入库，但当前没有 `domestic_fts` 全文检索表；现阶段主要是候选元数据检索。OCR 到全文、国内全文 FTS 和逐页引用仍属于下一阶段。

## 仍未闭环的核心缺口

以下五项仍为 OPEN，接受相关汇编、报刊报道或线索记录不能替代原件：

1. 1941 年香港《光明报》成立相关原刊影像；
2. 1946 年《民主同盟文献》目录所列“代表大会政治报告”正文；
3. 1947-10-27 内政部宣布民盟非法的公函/公报原页；
4. 1947-11-06 民盟总部解散公告独立印本；
5. 1947-11-04 北平《新民报》教授联署声明原版。

因此，当前 `B_LAYER_OPEN=true`、`pair_available=1/9` 是正确状态，不能宣称国内史料全链路闭环。

## 下一阶段交给 Claude Code

1. 保留并维护 304 条 L1 一手影像层，逐条补馆藏标识、页界、SHA256、访问日期和权利字段。
2. 对 42 条 pending 做逐条复核，不按总数批量升格；尤其先处理 L1 和 5 个原件缺口。
3. 启动 OCR 流水线：优先 1941《光明报》、1946《民主同盟文献》、1947《光明报》及 1948—1949 代表期。
4. 建立国内全文索引和逐页引用定位，区分 OCR 定位文本与人工校对文本。
5. 处理 cheer-only 馆藏任务：港大缩微、二史馆 1354 全宗、NLC 视检、校史馆、民盟中央和《新民报》原版追索。
6. 每一阶段结束后重跑：

```bash
python3 scripts/domestic/validate_candidates.py data/domestic/candidates.jsonl
python3 scripts/domestic/validate_event_coverage.py data/domestic/candidates.jsonl data/domestic/event_coverage.json
python3 scripts/domestic/ingest_domestic.py
python3 scripts/domestic/audit_readiness_20260719.py
```

## 口径提醒

`work/domestic/snapshot_20260721.md` 是历史快照，仍保留 406 accepted / 283 pending 的旧数字；本报告和 `work/domestic/monitor_status_latest.json` 以 2026-07-22 实测的 647/42 为准。

