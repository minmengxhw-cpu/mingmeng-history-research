#!/usr/bin/env python3
"""Repair the enum value on the idempotently appended newspaper candidate."""

import json
from pathlib import Path

path = Path(__file__).resolve().parents[2] / "data/domestic/candidates.jsonl"
target = "domestic:RMrb:1946-11-19-national-assembly-boycott"
rows = []
changed = 0
with path.open(encoding="utf-8") as fh:
    for line in fh:
        if not line.strip():
            continue
        item = json.loads(line)
        if item.get("candidate_id") == target:
            item["evidence_type"] = "secondary_lead"
            changed += 1
        rows.append(item)
with path.open("w", encoding="utf-8") as fh:
    for item in rows:
        fh.write(json.dumps(item, ensure_ascii=False, separators=(",", ":")) + "\n")
print(json.dumps({"target": target, "updated": changed}, ensure_ascii=False))
