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
uncertainty_note 保留旧值 + 追加新值 (避免 P0-3 覆写)。
状态机: source_url == NEW_URL → no_change (idempotent)
                source_url == OLD_URL → apply
                其他 → raise (unexpected state, 防止 P1-5 静默跳过)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _accept_lib import (
    dedupe_by_cid,
    read_jsonl,
    update_field,
    validate_after_write,
    write_jsonl_atomic,
)


TARGET_ID = "domestic:WS:wen-yiduo-last-testament-1946"
OLD_URL = "https://zh.wikisource.org/zh-hans/聞一多同志不朽的遺言"
NEW_URL = "https://baike.baidu.com/item/最后一次讲演/5722557"

FIELD_UPDATES = {
    "source_url": NEW_URL,
    "evidence_locator": (
        "页面题名《最后一次讲演》、作者闻一多、演讲日期 1946-07-15（李公朴追悼会）、"
        "原始记录 何丽芳 1946-07-15 速记；最早公开发表于《学生报》1946-07-21 第三版，"
        "后收入《闻一多全集·第二卷》（湖北人民出版社 1993 / 三联书店 1982）。"
        "URL 已从 wikisource 旧名《聞一多同志不朽的遺言》（404）改到 baidu baike 现行标题《最后一次讲演》。"
    ),
    "evidence_note": (
        "webfetch 2026-07-21 验证：baike.baidu.com 200，含完整文本 + 创作背景 + 原文 + 作者简介；"
        "wikisource 该条 404（疑因版权或页面整合已下线），改用更稳定的 baike 入口。"
    ),
    "catalog_reference": "闻一多全集·第二卷:湖北人民出版社:1993",
    "online_availability": "full_item_online",
    "reuse_rights": "citation_only",
}

# uncertainty_note 是 append 而非覆写 (P0-3 fix)
UNCERTAINTY_APPEND = (
    "原候选 evidence_note 提及「维基文库相关版本讨论进一步指出其与《民主周刊》"
    "第三卷第十九期有关」 — 改 URL 后该线索保留在 evidence_locator；"
    "如需引用《民主周刊》原刊，需走 NLC/特园 cheer-only 函调路径。"
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = read_jsonl(args.jsonl)
    rows = dedupe_by_cid(rows)

    # 状态机: 显式处理 3 档 (NEW / OLD / 其他)
    target = next((r for r in rows if r.get("candidate_id") == TARGET_ID), None)
    changed: list[str] = []
    no_change: list[str] = []
    missing: list[str] = []

    if target is None:
        missing.append(TARGET_ID)
    else:
        current = target.get("source_url")
        if current == NEW_URL:
            # 已修复, idempotent no-op
            no_change.append(TARGET_ID)
        elif current != OLD_URL:
            # 第三方状态, 失败 loud
            raise ValueError(
                f"unexpected state for {TARGET_ID}: source_url is neither OLD ({OLD_URL!r}) "
                f"nor NEW ({NEW_URL!r}), got {current!r}. Refusing to mutate."
            )
        else:
            # 主字段更新 (strict preconditions)
            rows, changed, _, _ = update_field(
                rows,
                TARGET_ID,
                field_updates=FIELD_UPDATES,
                preconditions={"source_url": OLD_URL},
            )
            # uncertainty_note 追加 (P0-3 fix: 不覆写)
            rows, _, _, _ = update_field(
                rows,
                TARGET_ID,
                field_updates={"uncertainty_note": UNCERTAINTY_APPEND},
                append_fields=["uncertainty_note"],
            )

    backup_path = None
    if args.apply:
        backup_path = write_jsonl_atomic(args.jsonl, rows)
        if not validate_after_write(args.jsonl):
            return 3

    summary = {
        "target": TARGET_ID,
        "old_url": OLD_URL,
        "new_url": NEW_URL,
        "changed": changed,
        "no_change": no_change,
        "missing": missing,
        "applied": args.apply,
        "backup": str(backup_path) if backup_path else None,
        "total_records": len(rows),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
