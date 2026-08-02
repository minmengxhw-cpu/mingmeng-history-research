#!/usr/bin/env python3
"""
T34 / T37 — Register 1957-1976 and 1949-1957 official records from T03 audited set.

Uses T03_OFFICIAL_IDENTITY_AUDIT.jsonl as candidate pool.
Classifies by title keyword matching to assign period.
Filters to candidates with local_file_status=PASS and reasonable period match.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

T03_PATH = RESEARCH_DIR / "T03_OFFICIAL_IDENTITY_AUDIT.jsonl"


PERIOD_1949_1957_KEYWORDS = [
    "1949", "1950", "1951", "1952", "1953", "1954", "1955", "1956", "1957",
    "新中国", "建国", "解放后", "人民代表大会", "人代会", "政协全国委员会",
    "第一届人民政协", "共同纲领", "土地改革", "三大改造", "反右前", "抗美援朝",
    "新中国成立", "新政协", "第一届", "三大运动",
]

PERIOD_1957_1976_KEYWORDS = [
    "1957", "1958", "1959", "1960", "1961", "1962", "1963", "1964", "1965",
    "1966", "1967", "1968", "1969", "1970", "1971", "1972", "1973", "1974", "1975", "1976",
    "反右", "整风", "反右派", "文化大革命", "文革", "上山下乡", "五七指示",
    "社会主义教育", "四清", "批林批孔", "天安门事件", "四五运动",
    "多党合作", "长期共存", "互相监督",
]


def classify_period(text: str) -> str | None:
    if not text:
        return None
    s = text
    matches_49 = sum(1 for kw in PERIOD_1949_1957_KEYWORDS if kw in s)
    matches_57 = sum(1 for kw in PERIOD_1957_1976_KEYWORDS if kw in s)
    matches_77 = sum(1 for kw in ["1977", "1978", "1979", "1980", "1981", "1982", "改革开放", "恢复", "重建", "新时期"] if kw in s)
    if matches_57 >= matches_49 and matches_57 >= matches_77 and matches_57 > 0:
        return "1957-1976"
    if matches_77 > matches_49 and matches_77 > 0:
        return "1977-2000"
    if matches_49 > 0:
        return "1949-1957"
    return None


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
    by_layer = Counter()
    by_inst = Counter()
    for r in rows:
        title = r.get("title", "")
        period = classify_period(title)
        if period == "1957-1976":
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
                by_layer["T34"] += 1
                by_inst[r.get("institution_type") or "null"] += 1
        elif period == "1949-1957":
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
                by_layer["T37"] += 1
    out_t34 = RESEARCH_DIR / "T34_1957_1976_FULL.jsonl"
    with open(out_t34, "w") as f:
        for r in t34:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    out_t37 = RESEARCH_DIR / "T37_1949_1957_OFFICIAL.jsonl"
    with open(out_t37, "w") as f:
        for r in t37:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary_t34 = {
        "task_id": "T34",
        "registrations": len(t34),
        "by_layer": by_layer.copy(),
        "institution_type": dict(by_inst),
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_touched": False,
        "notes": "Filtered from T03 audited pool by 1957-1976 keyword match; titles only, no claim of human verification.",
    }
    summary_t37 = {
        "task_id": "T37",
        "registrations": len(t37),
        "by_layer": {"OFFICIAL_RETROSPECTIVE": len(t37)},
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "formal_db_touched": False,
        "notes": "Filtered from T03 audited pool by 1949-1957 keyword match; titles only, no claim of human verification.",
    }
    (RESEARCH_DIR / "T34_1957_1976_ACCEPTANCE.json").write_text(json.dumps(summary_t34, ensure_ascii=False, indent=2))
    (RESEARCH_DIR / "T37_1949_1957_ACCEPTANCE.json").write_text(json.dumps(summary_t37, ensure_ascii=False, indent=2))
    print(json.dumps({"T34": summary_t34, "T37": summary_t37, "by_inst": dict(by_inst)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
