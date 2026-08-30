#!/usr/bin/env python3
"""
T39 — Reclassify relations missing machine-verifiable evidence.

Per dual acceptance:
- 447 relations; 84 missing source_url and missing real local_path.
- Downgrade those 84 to HOLD_UNSUPPORTED.
- Keep original RELATIONS.jsonl unchanged; write RELATIONS_RECLASSIFIED.jsonl.
"""
from __future__ import annotations
import json
import os
from pathlib import Path

ROOT = Path(".")
REL_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/relations"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

SRC = REL_DIR / "RELATIONS.jsonl"
DST = REL_DIR / "RELATIONS_RECLASSIFIED.jsonl"


def is_real_local_path(p: str | None) -> bool:
    if not p:
        return False
    # any existing local file path
    if p.startswith("/") or p.startswith("./") or p.startswith("work/") or p.startswith("data/"):
        full = ROOT / p if not p.startswith("/") else Path(p)
        return full.exists()
    return False


def main():
    rows = []
    with open(SRC) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    keep = []
    downgraded = []
    for r in rows:
        ev = r.get("evidence", {})
        url = ev.get("source_url")
        has_url = bool(url) and url != ""
        local = ev.get("local_path")
        loc = ev.get("evidence_location")
        has_local_path = is_real_local_path(local)
        has_real_location = is_real_local_path(loc)
        new = dict(r)
        new["evidence"] = dict(ev)
        new["evidence"]["has_source_url"] = has_url
        new["evidence"]["has_local_path"] = has_local_path
        new["evidence"]["has_real_evidence_location"] = has_real_location
        if not has_url and not has_local_path and not has_real_location:
            new["machine_status"] = "HOLD_UNSUPPORTED"
            new["downgrade_reason"] = "missing_url_or_local_path"
            downgraded.append(new)
        else:
            new["machine_status"] = "PROVISIONAL_EVIDENCE"
            keep.append(new)
    with open(DST, "w") as f:
        for r in keep + downgraded:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "total": len(rows),
        "kept_provisional": len(keep),
        "downgraded_to_hold_unsupported": len(downgraded),
        "out_path": str(DST),
        "decisions": {
            "rule": "downgrade if (!source_url && !local_path_exists && !evidence_location_is_real_path)",
        },
        "by_predicate": {},
    }
    from collections import Counter
    cnt = Counter()
    for r in downgraded:
        cnt[r.get("predicate", "UNKNOWN")] += 1
    summary["downgraded_by_predicate"] = dict(cnt)
    out = RESEARCH_DIR / "T39_RELATIONS_RECLASSIFICATION.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
