#!/usr/bin/env python3
"""
T65 — Dry-run schema polish with unicode61 tokenizer.

Re-create FTS5 with unicode61 + trigram for better Chinese search.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from pathlib import Path

ROOT = Path(".")
DRYRUN_DB = ROOT / "work/domestic/minimax_autonomous_research_20260730/dryrun/minimax_autonomous_research_20260730_dryrun.sqlite"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"


def sha256_file(path):
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    conn = sqlite3.connect(DRYRUN_DB)
    cur = conn.cursor()
    # Re-create FTS5 with unicode61 + trigram
    cur.execute("DROP TABLE IF EXISTS research_material_fts_trigram")
    cur.execute("""
    CREATE VIRTUAL TABLE research_material_fts_trigram USING fts5(
        candidate_id UNINDEXED,
        title,
        source_title,
        period,
        year,
        institution_type,
        research_card_category,
        tokenize = 'unicode61 remove_diacritics 2'
    )
    """)
    # Re-populate from research_materials
    cur.execute("SELECT candidate_id, title, research_theme_phase, institution_type, research_card_category FROM research_materials")
    for r in cur.fetchall():
        cur.execute("""INSERT INTO research_material_fts_trigram (candidate_id, title, source_title, period, year, institution_type, research_card_category)
                       VALUES (?,?,?,?,?,?,?)""", (r[0], r[1], r[1], r[2] or "", 0, r[3] or "", r[4] or ""))
    conn.commit()
    # Test
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '民盟'")
    m = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '中华民国'")
    zhh = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '政协'")
    zx = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '黄炎培'")
    hyp = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '上海'")
    sh = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '1947'")
    y47 = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '1949'")
    y49 = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '1957'")
    y57 = cur.fetchone()[0]
    cur.execute("PRAGMA integrity_check")
    integrity = cur.fetchone()[0]
    summary = {
        "task_id": "T65",
        "tokenizer": "unicode61 remove_diacritics 2",
        "fts_probes": {
            "民盟": m,
            "中华民国": zhh,
            "政协": zx,
            "黄炎培": hyp,
            "上海": sh,
            "1947": y47,
            "1949": y49,
            "1957": y57,
        },
        "integrity_check": integrity,
        "dryrun_db_sha256": sha256_file(DRYRUN_DB),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T65_DRYRUN_POLISH.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
