#!/usr/bin/env python3
"""
T66 — Comprehensive search benchmark v2.

Tests:
- trigram 3+ chars
- LIKE fallback for 2-char
- Chinese variants
- multi-char queries
- name lookups
- period lookups
- place lookups
- event lookups
- entity lookups
- relation lookups
"""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path

ROOT = Path(".")
DRYRUN_DB = ROOT / "work/domestic/minimax_autonomous_research_20260730/dryrun/minimax_autonomous_research_20260730_dryrun.sqlite"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

QUERIES = [
    # 3-char trigram
    ("3-char trigram", "民盟"),
    ("3-char trigram", "中华民国"),
    ("3-char trigram", "中国民主同盟"),
    ("3-char trigram", "政治协商"),
    ("3-char trigram", "民主党派"),
    ("3-char trigram", "新政协"),
    ("3-char trigram", "反右运动"),
    ("3-char trigram", "黄炎培"),
    ("3-char trigram", "张澜"),
    ("3-char trigram", "沈钧儒"),
    ("3-char trigram", "罗隆基"),
    ("3-char trigram", "梁漱溟"),
    ("3-char trigram", "闻一多"),
    ("3-char trigram", "李公朴"),
    ("3-char trigram", "上海"),
    ("3-char trigram", "重庆"),
    ("3-char trigram", "昆明"),
    ("3-char trigram", "南京"),
    ("3-char trigram", "1947"),
    ("3-char trigram", "1948"),
    ("3-char trigram", "1949"),
    ("3-char trigram", "1957"),
    ("3-char trigram", "1977"),
    ("3-char trigram", "光明報"),
    ("3-char trigram", "大公報"),
    ("3-char trigram", "民盟中央"),
    ("3-char trigram", "上海民盟"),
    # 2-char LIKE
    ("2-char LIKE", "民盟"),
    ("2-char LIKE", "政协"),
    ("2-char LIKE", "报刊"),
    ("2-char LIKE", "盟史"),
    ("2-char LIKE", "统战"),
    ("2-char LIKE", "宣言"),
    ("2-char LIKE", "纲领"),
    ("2-char LIKE", "中央"),
    ("2-char LIKE", "上海"),
    ("2-char LIKE", "同志"),
    ("2-char LIKE", "参政"),
    # name variants
    ("name variant", "黄炎培"),
    ("name variant", "张澜"),
    ("name variant", "沈钧儒"),
    ("name variant", "罗隆基"),
    ("name variant", "梁漱溟"),
    ("name variant", "闻一多"),
    ("name variant", "李公朴"),
    ("name variant", "陶行知"),
    ("name variant", "邓初民"),
    ("name variant", "章伯钧"),
    ("name variant", "马叙伦"),
    # period
    ("period", "1947"),
    ("period", "1949"),
    ("period", "1957"),
    ("period", "1977"),
    # place
    ("place", "上海"),
    ("place", "重庆"),
    ("place", "昆明"),
    ("place", "南京"),
    ("place", "北京"),
    ("place", "广州"),
    ("place", "武汉"),
    ("place", "西安"),
    ("place", "天津"),
    ("place", "杭州"),
    # event
    ("event", "反右"),
    ("event", "政协"),
    ("event", "新政协"),
    ("event", "三中全会"),
    ("event", "二中全会"),
    ("event", "一届二中全会"),
    ("event", "一届三中全会"),
    # relation
    ("relation", "MENTIONED_IN_SOURCE"),
    ("relation", "MEMBER_OF"),
    ("relation", "ORG_HOSTED_SOURCE"),
    ("relation", "CROSS_REFERENCED"),
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
        elif "relation" in label:
            cur.execute("SELECT COUNT(*) FROM relations WHERE predicate = ?", (q,))
            count = cur.fetchone()[0]
        results.append({"label": label, "query": q, "count": count})
    cur.execute("PRAGMA integrity_check")
    integrity = cur.fetchone()[0]
    summary = {
        "task_id": "T66",
        "search_queries": len(QUERIES),
        "results": results,
        "integrity_check": integrity,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T66_SEARCH_BENCHMARK_V2.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    # Print summary by category
    by_cat = {}
    for r in results:
        cat = r["label"]
        by_cat.setdefault(cat, []).append((r["query"], r["count"]))
    for cat, items in by_cat.items():
        print(f"\n{cat}:")
        for q, c in items:
            print(f"  {q}: {c}")
    conn.close()


if __name__ == "__main__":
    main()
