#!/usr/bin/env python3
"""把 NewspaperSG v2 相关度复核结果写回本地 sqlite。"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
CSV_PATH = ROOT / "data" / "newspapersg" / "relevance_review_v2.csv"


def main() -> None:
    if not DB.exists():
        raise SystemExit(f"sqlite 不存在：{DB}")
    if not CSV_PATH.exists():
        raise SystemExit(f"v2 复核表不存在：{CSV_PATH}")

    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    updated = missing = 0
    for row in rows:
        doc_key = row["doc_key"]
        doc = conn.execute(
            "SELECT id FROM documents WHERE doc_key=? AND source_platform='newspapersg'",
            (doc_key,),
        ).fetchone()
        if not doc:
            missing += 1
            continue
        conn.execute(
            """
            INSERT INTO document_classifications(document_id, grade, score, reason, needs_review)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(document_id) DO UPDATE SET
                grade=excluded.grade,
                score=excluded.score,
                reason=excluded.reason,
                needs_review=excluded.needs_review
            """,
            (
                doc["id"],
                row["grade"],
                int(row["score"] or 0),
                row["reason"],
                int(row["needs_review"] or 0),
            ),
        )
        updated += 1

    conn.commit()
    conn.close()
    print(f"NewspaperSG v2 classifications imported: {updated}; missing: {missing}")


if __name__ == "__main__":
    main()
