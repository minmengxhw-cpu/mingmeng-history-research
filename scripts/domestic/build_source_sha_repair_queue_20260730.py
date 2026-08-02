#!/usr/bin/env python3
"""Build a source-level SHA repair queue from the read-only provenance ledger."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "work" / "domestic" / "minimax_two_month_20260730" / "w2" / "PROVENANCE_CANONICAL_LEDGER.csv"
OUT_DIR = LEDGER.parent
QUEUE = OUT_DIR / "SOURCE_SHA_REPAIR_QUEUE.jsonl"
REPORT = OUT_DIR / "SOURCE_SHA_REPAIR_REPORT.json"


def main() -> None:
    grouped: dict[tuple[str, str, str], dict] = {}
    with LEDGER.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("sha_status") != "manifest_sha_missing":
                continue
            key = (row.get("record_id", ""), row.get("source_path", ""), row.get("source_sha256", ""))
            item = grouped.setdefault(
                key,
                {
                    "record_id": row.get("record_id", ""),
                    "title": row.get("title", ""),
                    "source_path": row.get("source_path", ""),
                    "source_sha256": row.get("source_sha256", ""),
                    "source_url": row.get("source_url", ""),
                    "source_kind": row.get("source_kind", ""),
                    "page_count": 0,
                    "page_ids": [],
                    "review_priorities": set(),
                    "action": "ADD_SOURCE_SHA_TO_NEW_CANONICAL_MANIFEST_ONLY",
                    "formal_db_written": False,
                },
            )
            item["page_count"] += 1
            item["page_ids"].append(row.get("page_id"))
            item["review_priorities"].add(row.get("review_priority", ""))

    rows = []
    for item in sorted(grouped.values(), key=lambda x: (-x["page_count"], x["source_path"])):
        item["review_priorities"] = sorted(p for p in item["review_priorities"] if p)
        rows.append(item)
    with QUEUE.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "report": "SOURCE_SHA_REPAIR_QUEUE_20260730",
        "input": str(LEDGER.relative_to(ROOT)),
        "source_records": len(rows),
        "page_rows": sum(row["page_count"] for row in rows),
        "priority_source_counts": {
            priority: sum(1 for row in rows if priority in row["review_priorities"])
            for priority in ("P0", "P1", "P2")
        },
        "formal_db_written": False,
        "rule": "queue is source-level repair guidance; existing manifests and raw files remain unchanged",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
