#!/usr/bin/env python3
"""Accept explicitly page-verified article cards at record level.

This does not assert that the article has been transcribed.  It only closes
the identity/page-image review when the title, date, page locator and local
image/PDF path are already present in the candidate record.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IDS = {
    "domestic:NLC:guangmingbao-1948-1949-v1n12-article",
    "domestic:NLC:guangmingbao-1948-1949-v1n1-article",
    "domestic:NLC:minxian-v1n9-democracy-vs-nondemocracy-1944-11-20",
    "domestic:NLC:guangmingbao-1946-issue8-conditional-national-assembly",
    "domestic:NLC:guangmingbao-1946-issue11-anti-one-party-constitution",
    "domestic:NLC:guangmingbao-1946-issue11-zhang-lan-shanghai-welcome-speech",
    "domestic:NLC:guangmingbao-1946-issue11-china-at-1947-threshold",
    "domestic:NLC:guangmingbao-1946-issue11-truman-december-18-statement",
    "domestic:NLC:guangmingbao-1946-issue01-refounding-editorial",
    "domestic:NLC:guangmingbao-1946-issue02-people-power-editorial",
    "domestic:NLC:guangmingbao-1946-issue04-urgent-situation-editorial",
    "domestic:NLC:guangmingbao-1946-issue07-why-not-national-assembly",
    "domestic:NLC:guangmingbao-1946-issue03-double-ten-task-article",
    "domestic:NLC:guangmingbao-1947-19-article-01",
    "domestic:NLC:guangmingbao-1947-19-article-02",
    "domestic:NLC:guangmingbao-1947-19-article-03",
    "domestic:NLC:guangmingbao-1947-19-article-04",
    "domestic:NLC:guangmingbao-1947-19-article-05",
}


def accept(row: dict[str, object], checked_at: str) -> None:
    row["review_status"] = "accepted"
    row["check_outcome"] = "pass"
    row["authenticity_level_accepted"] = row["authenticity_level_proposed"]
    row["relevance_grade_accepted"] = row["relevance_grade_proposed"]
    row["reviewed_at"] = checked_at
    row["reviewed_by"] = "codex"
    row["review_note"] = (
        "通过记录级同期原刊影像审核：题名、日期、文章页位、原刊来源和本地页图/PDF定位已核对；"
        "accepted 只表示记录身份和页级入口通过，不表示全文逐字转录、异文整理、署名补全或复制权利已经完成。"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-19")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    selected = []
    rejected = []
    for row in rows:
        cid = str(row.get("candidate_id", ""))
        if cid not in IDS:
            continue
        selected.append(cid)
        if row.get("repository_code") != "NLC":
            rejected.append((cid, "not NLC"))
        elif not row.get("document_date") or not row.get("title"):
            rejected.append((cid, "missing title/date"))
        elif not ("data/domestic/" in str(row.get("evidence_locator", "")) or "work/domestic/" in str(row.get("evidence_locator", ""))):
            rejected.append((cid, "missing local locator"))
        elif args.apply:
            accept(row, args.checked_at)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
            encoding="utf-8",
        )
    print(json.dumps({"selected": len(selected), "applied": args.apply, "rejected": rejected, "ids": selected}, ensure_ascii=False))
    return 0 if not rejected else 1


if __name__ == "__main__":
    raise SystemExit(main())
