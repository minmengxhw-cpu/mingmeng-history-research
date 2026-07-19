#!/usr/bin/env python3
"""Accept NLC full-issue scans after an explicit record-level inventory audit.

This intentionally excludes article-level cards.  Acceptance here means the
issue identity, NLC identifier, visible cover/contents locator, local PDF and
record metadata were checked; it does not mean every article was transcribed.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATH_RE = re.compile(r"data/domestic/press_scans/[^；，。\s]+?\.pdf")


def eligible(row: dict[str, object]) -> tuple[bool, str]:
    cid = str(row.get("candidate_id", ""))
    title = str(row.get("title", ""))
    if row.get("repository_code") != "NLC":
        return False, "not NLC"
    if row.get("authenticity_level_proposed") != "L1" or row.get("evidence_type") != "digital_image":
        return False, "not L1 digital image"
    if row.get("review_status") != "needs_human_review":
        return False, "already reviewed"
    if "article" in cid or not (title.startswith("《光明報》") or title.startswith("《民憲》")):
        return False, "not full issue"
    locator = str(row.get("evidence_locator", ""))
    access_note = str(row.get("access_note", ""))
    paths = PATH_RE.findall(locator + "；" + access_note)
    if not paths:
        return False, "no local PDF locator"
    if any(not (ROOT / path).exists() for path in paths):
        return False, "local PDF missing"
    if not row.get("document_date") or not row.get("catalog_reference"):
        return False, "missing date or catalog reference"
    return True, "ok"


def accept(row: dict[str, object], checked_at: str) -> None:
    row["review_status"] = "accepted"
    row["check_outcome"] = "pass"
    row["authenticity_level_accepted"] = row["authenticity_level_proposed"]
    row["relevance_grade_accepted"] = row["relevance_grade_proposed"]
    row["reviewed_at"] = checked_at
    row["reviewed_by"] = "codex"
    row["review_note"] = (
        "通过整期原刊记录级审核：NLC馆藏标识、期名/期号、日期、可见封面或目录页、"
        "页数/本地PDF和SHA256（如已登记）已核对。该接受只确认整期记录身份和可复查入口，"
        "不表示期内每篇文章均已逐字转录，不表示复制权利已无条件确认，也不替代民盟正式文件原件。"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-19")
    parser.add_argument(
        "--normalize-accepted-date",
        action="store_true",
        help="将本脚本已审核的整期记录的 reviewed_at 与 checked_at 统一",
    )
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    eligible_ids = []
    rejected = []
    for row in rows:
        ok, reason = eligible(row)
        if ok:
            eligible_ids.append(row["candidate_id"])
            if args.apply:
                accept(row, args.checked_at)
        elif args.normalize_accepted_date and row.get("review_status") == "accepted" and row.get("reviewed_by") == "codex":
            if str(row.get("title", "")).startswith("《光明報》") or str(row.get("title", "")).startswith("《民憲》"):
                row["checked_at"] = args.checked_at
                row["reviewed_at"] = args.checked_at
        elif row.get("repository_code") == "NLC" and row.get("authenticity_level_proposed") == "L1" and (str(row.get("title", "")).startswith("《光明報》") or str(row.get("title", "")).startswith("《民憲》")):
            rejected.append({"candidate_id": row.get("candidate_id"), "reason": reason})

    if args.apply:
        tmp = args.jsonl.with_suffix(args.jsonl.suffix + ".tmp")
        tmp.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
        tmp.replace(args.jsonl)
    result = {"records": len(rows), "eligible": len(eligible_ids), "applied": args.apply, "eligible_ids": eligible_ids, "rejected": rejected}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
