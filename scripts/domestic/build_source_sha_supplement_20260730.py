#!/usr/bin/env python3
"""Verify and materialize a non-destructive source SHA supplement."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "work" / "domestic" / "minimax_two_month_20260730" / "w2" / "SOURCE_SHA_REPAIR_QUEUE.jsonl"
OUT_DIR = QUEUE.parent
SUPPLEMENT = OUT_DIR / "SOURCE_SHA_SUPPLEMENT.jsonl"
REPORT = OUT_DIR / "SOURCE_SHA_SUPPLEMENT_REPORT.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    rows = [json.loads(line) for line in QUEUE.read_text(encoding="utf-8").splitlines() if line.strip()]
    supplement_rows = []
    failures = []
    for row in rows:
        path = ROOT / row["source_path"]
        if not path.is_file():
            failures.append({"source_path": row["source_path"], "status": "SOURCE_MISSING"})
            continue
        actual = sha256(path)
        if actual != row["source_sha256"]:
            failures.append({"source_path": row["source_path"], "expected": row["source_sha256"], "actual": actual, "status": "SHA_MISMATCH"})
            continue
        supplement_rows.append(
            {
                "supplement_id": f"SHA-SUP-20260730-{len(supplement_rows)+1:04d}",
                "record_id": row.get("record_id", ""),
                "source_path": row["source_path"],
                "source_sha256": actual,
                "source_title": row.get("title", ""),
                "page_count": row.get("page_count", 0),
                "derived_from": "SOURCE_SHA_REPAIR_QUEUE.jsonl + local file rehash",
                "computed_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "status": "VERIFIED_STAGING_SUPPLEMENT",
                "formal_db_written": False,
            }
        )
    with SUPPLEMENT.open("w", encoding="utf-8") as handle:
        for row in supplement_rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    report = {
        "report": "SOURCE_SHA_SUPPLEMENT_20260730",
        "input_sources": len(rows),
        "verified_supplement_sources": len(supplement_rows),
        "failure_sources": len(failures),
        "verified_supplement_pages": sum(row["page_count"] for row in supplement_rows),
        "formal_db_written": False,
        "raw_manifests_modified": False,
        "failures": failures,
        "rule": "supplement verifies local source bytes and is valid only for staging; it does not rewrite historical manifests",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
