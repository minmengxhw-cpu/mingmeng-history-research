#!/usr/bin/env python3
"""Accept three explicitly page-bounded MMHIST compilation records.

The records remain L2 compilation evidence.  Acceptance closes the identity,
title, date and page-boundary review only; it does not claim that the 1983
surrogate is the 1941/1945 original or that a diplomatic transcription is
complete.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IDS = {
    "domestic:MMHIST:formation-declaration-1941",
    "domestic:MMHIST:platform-1945",
    "domestic:MMHIST:congress-declaration-1945",
}


def accept(row: dict[str, object], checked_at: str) -> None:
    row["review_status"] = "accepted"
    row["check_outcome"] = "pass"
    row["authenticity_level_accepted"] = row["authenticity_level_proposed"]
    row["relevance_grade_accepted"] = row["relevance_grade_proposed"]
    row["reviewed_at"] = checked_at
    row["reviewed_by"] = "codex"
    row["review_note"] = (
        "通过记录级正式汇编扫描审核：题名、日期、正文页界、下一文边界和本地页图定位已核对；"
        "保留L2，accepted只表示该汇编记录可作为稳定研究入口，不表示1941/1945原件 provenance、"
        "同期原刊互校、全文逐字转录、异文整理或复制权利已经完成。"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-19")
    args = parser.parse_args()

    rows = [
        json.loads(line)
        for line in args.jsonl.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    selected: list[str] = []
    rejected: list[tuple[str, str]] = []
    for row in rows:
        cid = str(row.get("candidate_id", ""))
        if cid not in IDS:
            continue
        selected.append(cid)
        if row.get("repository_code") != "MMHIST":
            rejected.append((cid, "not MMHIST"))
        elif row.get("authenticity_level_proposed") != "L2":
            rejected.append((cid, "unexpected evidence level"))
        elif not row.get("document_date") or not row.get("title"):
            rejected.append((cid, "missing title/date"))
        elif not ("work/domestic/mmhist_" in str(row.get("evidence_locator", ""))):
            rejected.append((cid, "missing MMHIST local page locator"))
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
