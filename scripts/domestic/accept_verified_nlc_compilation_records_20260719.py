#!/usr/bin/env python3
"""Accept two explicitly page-bounded 1946 NLC compilation records.

This is record-level acceptance of the 1946 official compilation surrogate,
not acceptance of the 1941 original newspaper or an independent original.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


IDS = {
    "domestic:NLC:minmeng-wenxian-1946-formation-declaration",
    "domestic:NLC:minmeng-wenxian-1946-ten-program",
}


def accept(row: dict[str, object], checked_at: str) -> None:
    row["review_status"] = "accepted"
    row["check_outcome"] = "pass"
    row["authenticity_level_accepted"] = row["authenticity_level_proposed"]
    row["relevance_grade_accepted"] = row["relevance_grade_proposed"]
    row["reviewed_at"] = checked_at
    row["reviewed_by"] = "codex"
    row["review_note"] = (
        "通过记录级1946年民盟总部官方汇编扫描审核：题名、日期、连续正文页界、目录定位、"
        "本地页图和SHA256已核对；保留L2。accepted仅表示该汇编记录是稳定可复查入口，"
        "不表示1941年《光明報》原刊、独立原始印本、底本关系、全文逐字转录或复制权利已经闭环。"
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
        locator = str(row.get("evidence_locator", ""))
        if row.get("repository_code") != "NLC":
            rejected.append((cid, "not NLC"))
        elif row.get("authenticity_level_proposed") != "L2":
            rejected.append((cid, "unexpected evidence level"))
        elif not row.get("document_date") or not row.get("title"):
            rejected.append((cid, "missing title/date"))
        elif "work/domestic/minmeng_wenxian_1946/formation_9_13_images/" not in locator:
            rejected.append((cid, "missing local page-image locator"))
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
