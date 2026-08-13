# 国内专题共享事件索引

日期：2026-08-13

## 目的

让国内资料进入与境外资料相同的“专题事件 → 页级材料 → 原文/复核”路径。这里的事件索引是导航和编排层，不是事实判定层。

## 输入边界

- 只读取 `data/domestic/event_coverage.json` 中已经明确登记的 `event_id` 与 `domestic_candidate_ids`。
- 候选必须已经通过 `ingested_document_id` 回接到正式 `documents` 行。
- 只有 `documents.source_platform='domestic'` 的页面才会进入国内专题事件行；覆盖表中用于境外对照的 FRUS 等记录不会被重新标成国内资料。
- 页面正文、`page_provenance`、来源 SHA256、OCR 状态、人工复核和 `citation_ready` 均不被修改。

## 当前结果

- 9 个国内专题。
- 500 条页级导航关联。
- 486 个不同国内物理页被关联；同一页可属于多个明确专题。
- 共享 `research_events` 总节点 2,409 个。
- 所有国内专题关联页都能回到 `/doc/<doc_key>?page_id=<id>`，并提供国内证据复核入口。

## 可重复执行

默认是事务 dry-run，不改变数据库：

```bash
python3 scripts/domestic/link_domestic_event_pages_20260813.py \
  --db data/research_index.sqlite \
  --coverage data/domestic/event_coverage.json
```

应用时应先备份数据库，并用当前 manifest 的 SHA 做门控：

```bash
python3 scripts/domestic/link_domestic_event_pages_20260813.py \
  --db data/research_index.sqlite \
  --coverage data/domestic/event_coverage.json \
  --expected-sha <当前数据库SHA256> \
  --apply
```

事件总表重建脚本 `scripts/build/build_event_timeline.py` 也会在境外专题/人物事件生成后重新加入这条国内关联链。重复执行使用唯一键和 `INSERT OR IGNORE`，不会复制事件行。

## 阅读纪律

统一事件页上的“国内关联”只表示可追踪的候选—文档—页面关系。它不意味着该事件已被国内原件证明，也不提高机器 OCR 或候选接受状态的证据等级。正式引文仍须经过原件定位、来源哈希、页码和人工复核门禁。
