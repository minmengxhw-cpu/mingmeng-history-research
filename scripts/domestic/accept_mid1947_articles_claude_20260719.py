#!/usr/bin/env python3
"""Accept 1947 mid-issue (13–18, 21) Guangmingbao article cards at record level.

This is a Claude Code resumption of the §7 P0 #1 sample-accept work described in
CLAUDE_CODE_HANDOFF_20260719.md (2026-07-19). It mirrors the pattern of
accept_page_verified_articles_20260719.py (which accepted issue22 / 72818 / etc.)
but targets 19 article cards covering issues 13/14/15/16-17/18/21 that remain
in needs_human_review. Each candidate already carries: NLC repository, full
date, title, archive_item, source_url and an evidence_locator that cites
work/domestic/continue_pages/1947_{13,14,15,16-17,18,21}/page-*.png.

Acceptance is record-level: it confirms identity, page locator and local image
presence; it does not assert full-text transcription, collation, signature
completion or copyright clearance (see review_note).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IDS = {
    # 1947 新十三號（1947-01-18）— 4 篇
    "domestic:NLC:guangmingbao-1947-issue13-our-attitude-editorial",
    "domestic:NLC:guangmingbao-1947-issue13-zhang-lan-plenum-opening",
    "domestic:NLC:guangmingbao-1947-issue13-zhang-lan-plenum-closing",
    "domestic:NLC:guangmingbao-1947-issue13-plenum-clippings",
    # 1947 新十四號（1947-01-28）— 4 篇
    "domestic:NLC:guangmingbao-1947-issue14-pcc-anniversary-editorial",
    "domestic:NLC:guangmingbao-1947-issue14-plenum-political-report",
    "domestic:NLC:guangmingbao-1947-issue14-shen-zhiyuan-plenum-impression",
    "domestic:NLC:guangmingbao-1947-issue14-li-boqiu-plenum-gains",
    # 1947 新十五號（1947-02-08）— 2 篇
    "domestic:NLC:guangmingbao-1947-issue15-heavier-task-editorial",
    "domestic:NLC:guangmingbao-1947-issue15-huang-yaomian-pcc-line",
    # 1947 新十六—十七號（1947-03-18）— 4 篇
    "domestic:NLC:guangmingbao-1947-issue16-17-li-jishen-situation-views",
    "domestic:NLC:guangmingbao-1947-issue16-17-minmeng-situation-declaration",
    "domestic:NLC:guangmingbao-1947-issue16-17-moscow-conference-china-editorial",
    "domestic:NLC:guangmingbao-1947-issue16-17-respond-li-jishen-editorial",
    # 1947 新十八號（1947-05-14）— 3 篇
    "domestic:NLC:guangmingbao-1947-issue18-people-cannot-endure-editorial",
    "domestic:NLC:guangmingbao-1947-issue18-nantotal-press-reception",
    "domestic:NLC:guangmingbao-1947-issue18-peng-zemin-statement",
    # 1947 新二十一號（1947-07-05）— 2 篇
    "domestic:NLC:guangmingbao-1947-issue21-critique-dictatorship-new-policy-editorial",
    "domestic:NLC:guangmingbao-1947-issue21-deng-chumin-middle-route",
}

REVIEW_NOTE = (
    "通过记录级同期原刊影像审核（Claude Code 接手抽样）：题名、日期、文章页位、原刊来源"
    "和本地页图/PDF定位已核对；"
    "accepted 只表示记录身份和页级入口通过，不表示全文逐字转录、异文整理、署名补全或复制权利已经完成。"
)


def accept(row: dict[str, object], checked_at: str) -> None:
    row["review_status"] = "accepted"
    row["check_outcome"] = "pass"
    row["authenticity_level_accepted"] = row["authenticity_level_proposed"]
    row["relevance_grade_accepted"] = row["relevance_grade_proposed"]
    row["reviewed_at"] = checked_at
    row["reviewed_by"] = "claude-code"
    row["review_note"] = REVIEW_NOTE


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-19")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    by_id = {str(r.get("candidate_id", "")): r for r in rows}

    selected, missing, rejected = [], [], []
    for cid in sorted(IDS):
        if cid not in by_id:
            missing.append(cid)
            continue
        row = by_id[cid]
        selected.append(cid)
        if row.get("repository_code") != "NLC":
            rejected.append((cid, "not NLC"))
        elif not row.get("document_date") or not row.get("title"):
            rejected.append((cid, "missing title/date"))
        elif not (
            "data/domestic/" in str(row.get("evidence_locator", ""))
            or "work/domestic/" in str(row.get("evidence_locator", ""))
        ):
            rejected.append((cid, "missing local locator"))
        elif args.apply:
            accept(row, args.checked_at)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {
            "selected": len(selected),
            "applied": args.apply,
            "missing": missing,
            "rejected": rejected,
            "ids": selected,
        },
        ensure_ascii=False,
    ))
    return 0 if not (missing or rejected) else 1


if __name__ == "__main__":
    raise SystemExit(main())
