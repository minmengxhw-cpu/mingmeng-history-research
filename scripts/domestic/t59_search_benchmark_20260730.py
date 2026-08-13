#!/usr/bin/env python3
"""
T59 — Dry-run search benchmark.

Tests:
- trigram 3+ chars
- LIKE fallback for 2-char
- Chinese variants
- 3-char multi-char queries
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
DRYRUN_DB = ROOT / "work/domestic/minimax_autonomous_research_20260730/dryrun/minimax_autonomous_research_20260730_dryrun.sqlite"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

QUERIES = [
    ("3-char trigram", "民盟"),
    ("3-char trigram", "中华民国"),
    ("3-char trigram", "政协"),
    ("3-char trigram", "民主党"),
    ("3-char trigram", "黄炎培"),
    ("3-char trigram", "张澜"),
    ("3-char trigram", "沈钧儒"),
    ("3-char trigram", "罗隆基"),
    ("3-char trigram", "上海"),
    ("3-char trigram", "天津"),
    ("3-char trigram", "1947"),
    ("3-char trigram", "1949"),
    ("2-char LIKE", "盟史"),
    ("2-char LIKE", "民盟"),
    ("2-char LIKE", "政协"),
    ("2-char LIKE", "报刊"),
    ("name variant", "黄炎培"),
    ("name variant", "黄任之"),
    ("period", "1947"),
    ("period", "1949"),
    ("period", "1957"),
    ("place", "上海"),
    ("place", "重庆"),
    ("place", "昆明"),
    ("place", "南京"),
    ("event", "反右"),
    ("event", "政协"),
    ("event", "新政协"),
]


def main():
    conn = sqlite3.connect(DRYRUN_DB)
    cur = conn.cursor()
    results = []
    for label, q in QUERIES:
        if "3-char" in label:
            try:
                cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH ?", (q,))
                count = cur.fetchone()[0]
            except Exception as e:
                count = f"err: {str(e)[:50]}"
        elif "2-char" in label:
            cur.execute("SELECT COUNT(*) FROM research_materials WHERE title LIKE ?", (f"%{q}%",))
            count = cur.fetchone()[0]
        elif "name" in label:
            cur.execute("SELECT COUNT(*) FROM entities WHERE canonical_name LIKE ?", (f"%{q}%",))
            count = cur.fetchone()[0]
        elif "period" in label:
            cur.execute("SELECT COUNT(*) FROM research_materials WHERE research_theme_phase LIKE ?", (f"%{q}%",))
            count = cur.fetchone()[0]
        elif "place" in label:
            cur.execute("SELECT COUNT(*) FROM entities WHERE entity_type='PLACE' AND canonical_name LIKE ?", (f"%{q}%",))
            count = cur.fetchone()[0]
        elif "event" in label:
            cur.execute("SELECT COUNT(*) FROM research_materials WHERE title LIKE ? OR research_card_category LIKE ?", (f"%{q}%", f"%{q}%"))
            count = cur.fetchone()[0]
        results.append({"label": label, "query": q, "count": count})
    cur.execute("PRAGMA integrity_check")
    integrity = cur.fetchone()[0]
    summary = {
        "task_id": "T59",
        "search_queries": len(QUERIES),
        "results": results,
        "integrity_check": integrity,
        "dryrun_db_sha256": None,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T59_SEARCH_BENCHMARK.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
