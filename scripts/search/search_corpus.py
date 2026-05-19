#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path.cwd() / "data" / "research_index.sqlite"


def main() -> None:
    parser = argparse.ArgumentParser(description="Search the local research corpus and print citable results.")
    parser.add_argument("query", help="SQLite FTS5 query, e.g. 'Kunming assassinations' or 'Democratic League'")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    sql = """
        SELECT
            documents.volume_id,
            documents.doc_id,
            documents.date_guess,
            documents.title,
            documents.matched_terms,
            pages.page_label,
            pages.page_url,
            snippet(page_fts, 5, '[', ']', ' ... ', 30) AS snippet
        FROM page_fts
        JOIN pages ON pages.id = page_fts.rowid
        JOIN documents ON documents.id = pages.document_id
        WHERE page_fts MATCH ?
        ORDER BY bm25(page_fts)
        LIMIT ?
    """
    rows = conn.execute(sql, (args.query, args.limit)).fetchall()
    for i, row in enumerate(rows, 1):
        page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
        print(f"{i}. {row['volume_id']}/{row['doc_id']} | {row['date_guess']} | {page}")
        print(f"   {row['title']}")
        print(f"   terms: {row['matched_terms']}")
        print(f"   {row['page_url']}")
        print(f"   {row['snippet']}")
        print()
    conn.close()


if __name__ == "__main__":
    main()
