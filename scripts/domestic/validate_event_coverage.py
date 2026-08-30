#!/usr/bin/env python3
"""Validate domestic event coverage references against the candidate JSONL."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: validate_event_coverage.py CANDIDATES_JSONL EVENT_COVERAGE_JSON", file=sys.stderr)
        return 2

    candidates_path = Path(sys.argv[1])
    coverage_path = Path(sys.argv[2])
    candidate_ids = {
        json.loads(line)["candidate_id"]
        for line in candidates_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    missing: list[dict[str, str]] = []
    for event in coverage:
        for candidate_id in event.get("domestic_candidate_ids", []):
            if candidate_id not in candidate_ids:
                missing.append({"event_id": event["event_id"], "candidate_id": candidate_id})

    pair_counts = {}
    for event in coverage:
        status = event.get("pair_status", "unknown")
        pair_counts[status] = pair_counts.get(status, 0) + 1

    result = {
        "events": len(coverage),
        "candidate_ids": len(candidate_ids),
        "missing_candidate_references": missing,
        "pair_status_counts": pair_counts,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
