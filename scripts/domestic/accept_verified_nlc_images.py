#!/usr/bin/env python3
"""Accept explicitly audited NLC image records at the record level.

This does not certify a full transcription or prove that the scan is an
original government document.  It only records that the catalog identifier,
date, title/author, page locator, local scan and visible page evidence were
checked by Codex.  The candidate's uncertainty note remains in force.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


AUDITED_IDS = {
    "domestic:NLC:observer-1947-v3n11",
    "domestic:NLC:observer-1947-v3n11-dong-shijin",
    "domestic:NLC:observer-1947-v3n11-han-depei",
    "domestic:NLC:dagongbao-hankow-1947-11-04-zhang-qun-notice",
    "domestic:NLC:dagongbao-hankow-1947-11-04-league-dissolution-meeting",
    "domestic:NLC:dagongbao-hankow-1947-11-06-league-dissolution",
    "domestic:NLC:dagongbao-shanghai-1947-11-06-page2-full",
    "domestic:NLC:dagongbao-tianjin-1947-11-06-page2-full",
}


def accept(row: dict[str, object], checked_at: str) -> None:
    row["review_status"] = "accepted"
    row["check_outcome"] = "pass"
    row["authenticity_level_accepted"] = row["authenticity_level_proposed"]
    row["relevance_grade_accepted"] = row["relevance_grade_proposed"]
    row["reviewed_at"] = checked_at
    row["reviewed_by"] = "codex"
    row["review_note"] = (
        "通过记录级原刊影像审计：国家图书馆馆藏标识、题名/署名、日期、"
        "页级定位、本地影像和可视证据已核对；全文逐字转录、异文整理及复制权利仍待完成。"
        "accepted 只表示记录级影像身份通过，不表示已取得政府公函原件或无条件再利用授权。"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-19")
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    found = {row["candidate_id"] for row in rows}
    missing = sorted(AUDITED_IDS - found)
    applied = []
    for row in rows:
        if row["candidate_id"] in AUDITED_IDS:
            if row.get("authenticity_level_proposed") != "L1" or row.get("evidence_type") != "digital_image":
                raise SystemExit(f"not an L1 digital image: {row['candidate_id']}")
            if args.apply and row.get("review_status") != "accepted":
                accept(row, args.checked_at)
                applied.append(row["candidate_id"])
    result = {
        "records": len(rows),
        "audited_ids": len(AUDITED_IDS),
        "missing_ids": missing,
        "applied": applied,
        "apply": args.apply,
    }
    if args.apply:
        tmp = args.jsonl.with_suffix(args.jsonl.suffix + ".tmp")
        tmp.write_text(
            "".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows),
            encoding="utf-8",
        )
        tmp.replace(args.jsonl)
    print(json.dumps(result, ensure_ascii=False))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
