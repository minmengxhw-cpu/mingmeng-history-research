#!/usr/bin/env python3
"""
T55 — 1977-2000 阶段官方记录扩展。

从 T03 审计池按 1977-2000 关键字筛选。
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

T03_PATH = RESEARCH_DIR / "T03_OFFICIAL_IDENTITY_AUDIT.jsonl"


def classify_1977_2000(text: str) -> bool:
    if not text:
        return False
    keywords = [
        "1977", "1978", "1979", "1980", "1981", "1982", "1983", "1984", "1985",
        "1986", "1987", "1988", "1989", "1990", "1991", "1992", "1993", "1994",
        "1995", "1996", "1997", "1998", "1999", "2000",
        "改革开放", "新时期", "恢复", "重建", "重返", "新时期统一战线",
    ]
    for kw in keywords:
        if kw in text:
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
    t55 = []
    seen = set()
    by_layer = Counter()
    by_inst = Counter()
    for r in rows:
        title = r.get("title", "")
        if classify_1977_2000(title):
            rec = {
                "candidate_id": r["candidate_id"],
                "title": title,
                "source_url": r.get("source_url", ""),
                "institution_type": r.get("institution_type"),
                "research_card_category": r.get("layer", "OFFICIAL_RETROSPECTIVE"),
                "research_theme_phase": "1977-2000",
                "local_path": r.get("local_path"),
                "local_file_status": r.get("local_file_status"),
                "local_sha256": r.get("local_sha256"),
                "citation_ready": False,
                "human_verified": False,
                "rights_status": "PUBLIC_LEGAL_SOURCE; rights_scope_not_human_verified",
            }
            if rec["candidate_id"] not in seen:
                t55.append(rec)
                seen.add(rec["candidate_id"])
                by_layer[rec["research_card_category"]] += 1
                by_inst[rec["institution_type"] or "null"] += 1
    out_t55 = RESEARCH_DIR / "T55_1977_2000_OFFICIAL.jsonl"
    with open(out_t55, "w") as f:
        for r in t55:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T55",
        "registrations": len(t55),
        "by_layer": dict(by_layer),
        "institution_type": dict(by_inst),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T55_1977_2000_ACCEPTANCE.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
