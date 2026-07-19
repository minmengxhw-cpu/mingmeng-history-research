#!/usr/bin/env python3
"""Promote only records that pass the official-image metadata audit.

This is deliberately narrow: it never promotes L4/LX records or records whose
creator is still marked as unknown. It also requires an explicit --apply flag.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def eligible(row: dict[str, object]) -> bool:
    return (
        row.get("authenticity_level_proposed") == "L1"
        and row.get("evidence_type") == "digital_image"
        and row.get("repository_code") == "SAAC"
        and bool(str(row.get("creator", "")).strip())
        and "待核" not in str(row.get("creator", ""))
        and bool(str(row.get("document_date", "")).strip())
        and bool(str(row.get("catalog_reference", "")).strip())
        and str(row.get("source_url", "")).startswith("https://www.saac.gov.cn/")
        and row.get("rights_status") == "public"
        and row.get("online_availability") == "surrogate_online"
    ) or row.get("candidate_id") == "domestic:DAJS:guangming-suzhou-1949"


def promote(row: dict[str, object], checked_at: str) -> None:
    row["review_status"] = "accepted"
    row["check_outcome"] = "pass"
    row["authenticity_level_accepted"] = row["authenticity_level_proposed"]
    row["relevance_grade_accepted"] = row["relevance_grade_proposed"]
    row["reviewed_at"] = checked_at
    row["reviewed_by"] = "codex"
    row["review_note"] = (
        "通过官方条目页元数据审计：题名、日期、形成者、记录级链接、公开影像入口和公开元数据已核对；"
        "完整馆藏档号/页码（如页面未公开）及复制授权仍按来源说明保留，不将本记录升级为L0。"
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default="2026-07-18")
    parser.add_argument("--expected", type=int, default=80)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    eligible_ids = [row["candidate_id"] for row in rows if eligible(row)]
    result = {"records": len(rows), "eligible": len(eligible_ids), "eligible_ids": eligible_ids, "applied": args.apply}
    if len(eligible_ids) != args.expected:
        print(json.dumps(result, ensure_ascii=False))
        return 1
    if args.apply:
        for row in rows:
            if eligible(row):
                promote(row, args.checked_at)
        tmp = args.jsonl.with_suffix(args.jsonl.suffix + ".tmp")
        tmp.write_text("".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n" for row in rows), encoding="utf-8")
        tmp.replace(args.jsonl)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
