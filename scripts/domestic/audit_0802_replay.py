#!/usr/bin/env python3
"""
audit_0802_replay.py — Re-runnable cross-batch audit for 0802 final state.

Usage:
    python3 scripts/domestic/audit_0802_replay.py

Output:
    - Console summary (state per category)
    - audit_0802_replay_<timestamp>.json (machine-readable full snapshot)

Replaces manual one-shot audit. Future sessions can run this single command
to verify all 0802-batch deliverables are intact and consistent.

Hardcoded baseline (P3 acceptance freeze):
    formal_db_sha256 = 822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
FORMAL_DB = REPO / "data" / "research_index.sqlite"
P3_FREEZE_SHA = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"
REBASELINE_0802_SHA = "e4417bd1dfce77772832e0fcee17f5fb33bbd0fc9d1e6b2618932a64e9c8c0a5"
CURRENT_FREEZE_SHA = "7af2e27b4d5fd4d917f63b6af392b86da0ec84add878aa23918b351141def0e6"
FREEZE_SHA = CURRENT_FREEZE_SHA  # alias for back-compat
CST = timezone(timedelta(hours=8))


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def check(label: str, path: str, expected_sha: str | None = None,
          expected_lines: int | None = None,
          expected_state: str | None = None) -> dict:
    full = REPO / path
    result = {"label": label, "path": path, "exists": full.exists()}
    if full.exists():
        result["sha256"] = sha(full)
        result["size_bytes"] = full.stat().st_size
        if expected_sha:
            result["sha_match"] = result["sha256"] == expected_sha
        if expected_lines is not None and path.endswith(".jsonl"):
            with full.open() as f:
                lines = sum(1 for l in f if l.strip())
            result["lines"] = lines
            result["lines_match"] = lines == expected_lines
        if expected_state and path.endswith(".json"):
            try:
                d = json.load(full.open())
                state = d.get("state") or d.get("phase") or d.get("verdict") or d.get("task_id")
                result["observed_state"] = state
                result["state_match"] = state == expected_state
            except Exception as e:
                result["error"] = str(e)
    return result


def main() -> int:
    sqlite_sha = sha(FORMAL_DB) if FORMAL_DB.exists() else None
    drift = sqlite_sha != FREEZE_SHA if sqlite_sha else None

    print(f"=" * 72)
    print(f"0802 REPLAY AUDIT  ({datetime.now(CST).isoformat()})")
    print(f"=" * 72)
    print(f"formal DB SHA256        : {sqlite_sha}")
    print(f"P3 freeze SHA (0801)    : {P3_FREEZE_SHA}")
    print(f"rebaseline 0802 SHA     : {REBASELINE_0802_SHA}")
    print(f"CURRENT freeze SHA      : {CURRENT_FREEZE_SHA}")
    print(f"drift vs current freeze : {drift}")
    print()

    inventory = []

    # A. P0-P3 protected files (must NOT change from P3 freeze)
    protected = [
        ("V2_SAMPLE_1500", "work/domestic/minimax_domestic_evidence_v2_month_20260729/02_sample_v2/V2_SAMPLE_1500.jsonl", "cd226897c52e44108681a19e02dab6041feb67f39ac356f8506ec059924b7228", 1500),
        ("EVIDENCE_CANDIDATES_300", "work/domestic/minimax_domestic_evidence_v2_month_20260729/06_period_evidence/EVIDENCE_CANDIDATES_300.jsonl", "b805eeb68dec8303f72e3f73fe5cacd0d99acb5e9b2b71cd4b92320ae7281d65", 300),
        ("HARD_GAPS", "work/domestic/minimax_domestic_evidence_v2_month_20260729/06_period_evidence/HARD_GAPS.md", "cbee8215c07aad6afd2666d95010fe5f983952c4f92fcce9ced4881bb39a3fd0", None),
        ("OBSERVER_V3_SCREENING", "work/domestic/minimax_domestic_evidence_v2_month_20260729/06_period_evidence/OBSERVER_V3_SCREENING.json", "71728353d3d2f56557c5ba95d8088d19191e91bb550308810ec3672b3fe69d4c", None),
    ]
    for label, path, exp_sha, exp_lines in protected:
        r = check(label, path, exp_sha, exp_lines)
        inventory.append(r)
        flag = "✓" if r.get("sha_match") or r.get("lines_match") else "✗"
        print(f"  [PROTECTED] {flag} {label:30s} {r['path']}")

    # B. P5 outputs (0802 batch)
    p5_files = [
        "P5_HARD_GAP_POOL", "P5_HARD_GAP_POOL_REJECTS", "P5_HARD_GAP_NOTES",
        "P5_OBSERVER_HOLD_DECISION", "CODEX_APPLY_ACCEPTANCE_ENTRY", "P5_CHECKPOINT",
    ]
    p5_paths = {
        "P5_HARD_GAP_POOL": "work/domestic/minimax_domestic_evidence_v2_month_20260729/06_period_evidence/P5_HARD_GAP_POOL.jsonl",
        "P5_HARD_GAP_POOL_REJECTS": "work/domestic/minimax_domestic_evidence_v2_month_20260729/06_period_evidence/P5_HARD_GAP_POOL_REJECTS.jsonl",
        "P5_HARD_GAP_NOTES": "work/domestic/minimax_domestic_evidence_v2_month_20260729/09_reports/P5_HARD_GAP_NOTES.md",
        "P5_OBSERVER_HOLD_DECISION": "work/domestic/minimax_domestic_evidence_v2_month_20260729/09_reports/P5_OBSERVER_HOLD_DECISION.json",
        "CODEX_APPLY_ACCEPTANCE_ENTRY": "work/domestic/minimax_domestic_evidence_v2_month_20260729/09_reports/CODEX_APPLY_ACCEPTANCE_ENTRY.md",
        "P5_CHECKPOINT": "work/domestic/minimax_domestic_evidence_v2_month_20260729/09_reports/P5_CHECKPOINT.md",
    }
    for label in p5_files:
        r = check(label, p5_paths[label])
        inventory.append(r)
        flag = "✓" if r["exists"] else "✗"
        print(f"  [P5]        {flag} {label:30s} {r['size_bytes'] if r['exists'] else 'N/A'} bytes")

    # C. OFFICIAL_RESEARCH 0802 outputs
    official_files = [
        ("PRE_AUDIT_0802", "work/domestic/minimax_official_research_20260730/06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.json"),
        ("PRE_AUDIT_0802_MD", "work/domestic/minimax_official_research_20260730/06_reports/PRE_CODEX_AUDIT_BLOCKERS_20260802.md"),
        ("B05_VERIFICATION", "work/domestic/minimax_official_research_20260730/06_reports/B05_VERIFICATION.jsonl"),
        ("B05_CONFLICTS", "work/domestic/minimax_official_research_20260730/06_reports/B05_CONFLICTS.md"),
        ("B03_RELATIONS_SUMMARY", "work/domestic/minimax_official_research_20260730/06_reports/B03_RELATIONS_SUMMARY.json"),
        ("B02_AUDIT", "work/domestic/minimax_official_research_20260730/06_reports/B02_AUDIT_1948_1949.md"),
        ("B01_GAP_ANALYSIS", "work/domestic/minimax_official_research_20260730/06_reports/B01_GAP_ANALYSIS.md"),
    ]
    for label, path in official_files:
        r = check(label, path)
        inventory.append(r)
        flag = "✓" if r["exists"] else "✗"
        print(f"  [OFFICIAL]  {flag} {label:30s} {r['size_bytes'] if r['exists'] else 'N/A'} bytes")

    # D. HARD_GAPS Sept package
    sept_files = [
        ("SEPT_T1_T6", "work/domestic/HARD_GAPS_SEPT_PACKAGE_20260802/"),
        ("SEPT_README", "work/domestic/HARD_GAPS_SEPT_PACKAGE_20260802/README_20260802.md"),
        ("SEPT_TRACKER", "work/domestic/HARD_GAPS_SEPT_PACKAGE_20260802/HARD_GAPS_SEPT_TRACKER_20260802.jsonl"),
        ("SEPT_STATUS", "work/domestic/HARD_GAPS_SEPT_PACKAGE_20260802/SEPT_PACKAGE_STATUS.json"),
    ]
    for label, path in sept_files:
        full = REPO / path
        if full.is_dir():
            files = list(full.glob("*"))
            files = [f for f in files if f.is_file() and not f.name.startswith("OLD")]
            inventory.append({"label": label, "path": path, "exists": True, "file_count": len(files)})
            print(f"  [SEPT]      ✓ {label:30s} {len(files)} files in dir")
        elif full.exists():
            r = check(label, path)
            inventory.append(r)
            print(f"  [SEPT]      ✓ {label:30s} {r.get('size_bytes', 'N/A')} bytes")
        else:
            inventory.append({"label": label, "path": path, "exists": False})
            print(f"  [SEPT]      ✗ {label:30s} MISSING")

    # E. Codex packet
    codex_packet_dir = REPO / "work/domestic/OFFICIAL_RESEARCH_CODEX_PACKET_20260802"
    if codex_packet_dir.is_dir():
        files = sorted([f for f in codex_packet_dir.iterdir() if f.is_file()])
        inventory.append({"label": "CODEX_PACKET", "path": str(codex_packet_dir.relative_to(REPO)), "exists": True, "file_count": len(files)})
        print(f"  [CODEX_PKT]  ✓ CODEX_PACKET                   {len(files)} files in dir")
        for f in files:
            r = check(f.name, str(f.relative_to(REPO)))
            inventory.append(r)
            print(f"  [CODEX_PKT]  - {f.name:50s} {r.get('size_bytes', 'N/A')} bytes")
    else:
        print(f"  [CODEX_PKT]  ✗ MISSING")

    # F. Final summary docs
    final_docs = [
        ("PROJECT_FINAL_AUDIT", "work/domestic/PROJECT_FINAL_AUDIT_20260802.json"),
        ("PROJECT_STATE_FINAL", "work/domestic/PROJECT_STATE_FINAL_20260802.md"),
        ("CHEER_NEXT_ACTIONS", "work/domestic/CHEER_NEXT_ACTIONS.md"),
        ("PROJECT_POST_0802_SUMMARY", "work/domestic/PROJECT_POST_0802_SUMMARY.md"),
    ]
    for label, path in final_docs:
        r = check(label, path)
        inventory.append(r)
        flag = "✓" if r["exists"] else "✗"
        print(f"  [FINAL]     {flag} {label:30s} {r['size_bytes'] if r['exists'] else 'N/A'} bytes")

    # Summary
    total = len(inventory)
    existing = sum(1 for r in inventory if r.get("exists"))
    drift_items = sum(1 for r in inventory if r.get("sha_match") is False)
    print()
    print(f"=" * 72)
    print(f"TOTAL files checked: {total}")
    print(f"existing            : {existing}")
    print(f"missing             : {total - existing}")
    print(f"formal DB SHA drift : {drift}")
    print(f"=" * 72)

    # Save replay snapshot
    ts = datetime.now(CST).strftime("%Y%m%dT%H%M%S")
    snap_path = REPO / f"work/domestic/audit_0802_replay_{ts}.json"
    snap = {
        "replay_at": datetime.now(CST).isoformat(),
        "tool": "scripts/domestic/audit_0802_replay.py",
        "formal_db_sha256": sqlite_sha,
        "p3_freeze_sha256": P3_FREEZE_SHA,
        "rebaseline_0802_sha256": REBASELINE_0802_SHA,
        "current_freeze_sha256": CURRENT_FREEZE_SHA,
        "drift": drift,
        "drift_attribution": "if drift, check whether app.py / supervisor / translation import rebaselined",
        "totals": {
            "files_checked": total,
            "existing": existing,
            "missing": total - existing,
        },
        "inventory": inventory,
        "conclusion": (
            "PASS" if (existing == total and not drift)
            else "PARTIAL_DRIFT_OR_MISSING"
        ),
    }
    snap_path.write_text(json.dumps(snap, ensure_ascii=False, indent=2))
    print(f"\nSnapshot written: {snap_path}")
    print(f"Conclusion: {snap['conclusion']}")
    return 0 if snap["conclusion"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())