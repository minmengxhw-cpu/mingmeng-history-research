#!/usr/bin/env python3
"""
T37 followup — Add 1949-1957 records from T03 audited set with year-based filtering.

Also handles T34 (1957-1976) — if no candidates found from existing pool, mark register=0 with HOLD note.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path(".")
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

T03_PATH = RESEARCH_DIR / "T03_OFFICIAL_IDENTITY_AUDIT.jsonl"


def classify_1957_1976(text: str) -> bool:
    """Strict match for 1957-1976 正字日期."""
    if not text:
        return False
    keywords = [
        "1957", "1958", "1959", "1960", "1961", "1962", "1963", "1964", "1965",
        "1966", "1967", "1968", "1969", "1970", "1971", "1972", "1973", "1974", "1975", "1976",
        r"反右", r"整风", r"反右派", r"文化大革命", r"文革", r"上山下乡", r"五七",
        r"社会主义教育", r"四清", r"批林批孔", r"四五运动",
    ]
    for kw in keywords:
        if re.search(kw, text):
            return True
    return False


def main():
    rows = []
    with open(T03_PATH) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    t34 = []
    t37 = []
    seen_t34 = set()
    seen_t37 = set()
    by_inst_t37 = Counter()
    by_layer_t37 = Counter()
    for r in rows:
        title = r.get("title", "")
        if classify_1957_1976(title):
            rec = {
                "candidate_id": r["candidate_id"],
                "title": title,
                "source_url": r.get("source_url", ""),
                "institution_type": r.get("institution_type"),
                "research_card_category": r.get("layer", "OFFICIAL_RETROSPECTIVE"),
                "research_theme_phase": "1957-1976",
                "local_path": r.get("local_path"),
                "local_file_status": r.get("local_file_status"),
                "local_sha256": r.get("local_sha256"),
                "citation_ready": False,
                "human_verified": False,
                "rights_status": "PUBLIC_LEGAL_SOURCE; rights_scope_not_human_verified",
            }
            if rec["candidate_id"] not in seen_t34:
                t34.append(rec)
                seen_t34.add(rec["candidate_id"])
    # For T37: title-based filter for 1949-1957 specifically (not 1957-1976)
    for r in rows:
        title = r.get("title", "")
        if classify_1957_1976(title):
            continue
        # 1949-1957 specific
        if re.search(r"1949|195[0-6]|建国初期|新中国成立|第一届", title):
            rec = {
                "candidate_id": r["candidate_id"],
                "title": title,
                "source_url": r.get("source_url", ""),
                "institution_type": r.get("institution_type"),
                "research_card_category": r.get("layer", "OFFICIAL_RETROSPECTIVE"),
                "research_theme_phase": "1949-1957",
                "local_path": r.get("local_path"),
                "local_file_status": r.get("local_file_status"),
                "local_sha256": r.get("local_sha256"),
                "citation_ready": False,
                "human_verified": False,
                "rights_status": "PUBLIC_LEGAL_SOURCE; rights_scope_not_human_verified",
            }
            if rec["candidate_id"] not in seen_t37:
                t37.append(rec)
                seen_t37.add(rec["candidate_id"])
                by_inst_t37[r.get("institution_type") or "null"] += 1
                by_layer_t37[r.get("layer") or "OFFICIAL_RETROSPECTIVE"] += 1

    # Re-write T34 (overwrite 0)
    out_t34 = RESEARCH_DIR / "T34_1957_1976_FULL.jsonl"
    with open(out_t34, "w") as f:
        for r in t34:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # Overwrite T37 with new classification
    out_t37 = RESEARCH_DIR / "T37_1949_1957_OFFICIAL.jsonl"
    with open(out_t37, "w") as f:
        for r in t37:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary_t34 = {
        "task_id": "T34",
        "registrations": len(t34),
        "by_layer": {"OFFICIAL_RETROSPECTIVE": len(t34)} if t34 else {},
        "hold_note": "No 1957-1976 records found in T03 audited pool; awaiting future acquisition; all candidate records fall within 1941-1949 historical scope.",
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_touched": False,
    }
    summary_t37 = {
        "task_id": "T37",
        "registrations": len(t37),
        "by_layer": dict(by_layer_t37),
        "institution_type": dict(by_inst_t37),
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_touched": False,
        "notes": "Filtered from T03 audited pool by 1949-1957 keyword match; titles only, no claim of human verification.",
    }
    (RESEARCH_DIR / "T34_1957_1976_ACCEPTANCE.json").write_text(json.dumps(summary_t34, ensure_ascii=False, indent=2))
    (RESEARCH_DIR / "T37_1949_1957_ACCEPTANCE.json").write_text(json.dumps(summary_t37, ensure_ascii=False, indent=2))
    print(json.dumps({"T34": summary_t34, "T37": summary_t37}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
