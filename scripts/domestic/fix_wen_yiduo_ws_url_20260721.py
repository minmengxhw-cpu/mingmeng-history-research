#!/usr/bin/env python3
"""修复闻一多《最后一次讲演》wikisource URL 404 问题（cheer 2026-07-21 拍板）。

原候选：domestic:WS:wen-yiduo-last-testament-1946
  - title: 闻一多同志不朽的遗言（旧名）
  - source_url: https://zh.wikisource.org/zh-hans/聞一多同志不朽的遺言 (404)
  - event_tags: 1946李闻血案

修复方案：source_url 改到 baike.baidu.com/item/最后一次讲演/5722557
  - 完整文本（闻一多全集·第二卷收录版）
  - 元数据齐（创作背景/主旨/作者简介/原文/后世影响）
  - webfetch 2026-07-21 验证 200
  - 等级 L3 保持不变（公开转录的 primary text）

不动 review_status / authenticity_level / 任何其他字段。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TARGET_ID = "domestic:WS:wen-yiduo-last-testament-1946"

OLD_URL = "https://zh.wikisource.org/zh-hans/聞一多同志不朽的遺言"
NEW_URL = "https://baike.baidu.com/item/最后一次讲演/5722557"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]

    changed, missing, no_change = [], [], []
    for r in rows:
        cid = r["candidate_id"]
        if cid != TARGET_ID:
            continue
        if r.get("source_url") == NEW_URL:
            no_change.append(cid)
            continue
        if r.get("source_url") != OLD_URL:
            # unexpected current state; skip
            no_change.append(cid)
            continue
        r["source_url"] = NEW_URL
        r["evidence_locator"] = (
            "页面题名《最后一次讲演》、作者闻一多、演讲日期 1946-07-15（李公朴追悼会）、"
            "原始记录 何丽芳 1946-07-15 速记；最早公开发表于《学生报》1946-07-21 第三版，"
            "后收入《闻一多全集·第二卷》（湖北人民出版社 1993 / 三联书店 1982）。"
            "URL 已从 wikisource 旧名《聞一多同志不朽的遺言》（404）改到 baidu baike 现行标题《最后一次讲演》。"
        )
        r["evidence_note"] = (
            "webfetch 2026-07-21 验证：baike.baidu.com 200，含完整文本 + 创作背景 + 原文 + 作者简介；"
            "wikisource 该条 404（疑因版权或页面整合已下线），改用更稳定的 baike 入口。"
        )
        r["catalog_reference"] = "闻一多全集·第二卷:湖北人民出版社:1993"
        r["online_availability"] = "full_item_online"
        r["reuse_rights"] = "citation_only"
        r["uncertainty_note"] = (
            "原候选 evidence_note 提及「维基文库相关版本讨论进一步指出其与《民主周刊》"
            "第三卷第十九期有关」 — 改 URL 后该线索保留在 evidence_locator；"
            "如需引用《民主周刊》原刊，需走 NLC/特园 cheer-only 函调路径。"
        )
        changed.append(cid)

    for cid in [TARGET_ID]:
        if cid not in changed and cid not in no_change:
            missing.append(cid)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )

    print(json.dumps(
        {
            "target": TARGET_ID,
            "old_url": OLD_URL,
            "new_url": NEW_URL,
            "changed": changed,
            "no_change": no_change,
            "missing": missing,
            "applied": args.apply,
            "total_records": len(rows),
        },
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
