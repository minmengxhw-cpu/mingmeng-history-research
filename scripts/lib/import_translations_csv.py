#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            language TEXT NOT NULL,
            translator TEXT,
            status TEXT,
            text TEXT NOT NULL,
            UNIQUE(page_id, language)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS translation_fts USING fts5(
            language,
            title,
            page_label,
            text
        );
        """
    )


def upsert(conn: sqlite3.Connection, page_id: int, title: str, page_label: str, text: str, translator: str, status: str) -> None:
    existing = conn.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (page_id,),
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (existing[0],))
        conn.execute("DELETE FROM translations WHERE id=?", (existing[0],))
    cur = conn.execute(
        """
        INSERT INTO translations(page_id, language, translator, status, text)
        VALUES (?, 'zh-CN', ?, ?, ?)
        """,
        (page_id, translator, status, text),
    )
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, ?, ?, ?, ?)",
        (cur.lastrowid, "zh-CN", title, page_label or "doc-level", text),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Import translated CSV batches into the research database.")
    parser.add_argument("csv_files", nargs="+", type=Path)
    parser.add_argument("--translator", default="external-batch")
    parser.add_argument("--status", default="machine-draft-review-needed")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    imported = 0
    skipped = 0
    for csv_file in args.csv_files:
        with csv_file.open(encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                text = (row.get("zh_translation") or "").strip()
                if not text:
                    skipped += 1
                    continue
                page_id = int(row["page_id"])
                page = conn.execute(
                    """
                    SELECT pages.page_label, documents.title
                    FROM pages
                    JOIN documents ON documents.id = pages.document_id
                    WHERE pages.id=?
                    """,
                    (page_id,),
                ).fetchone()
                if not page:
                    skipped += 1
                    continue
                upsert(conn, page_id, page["title"], page["page_label"] or "doc-level", text, args.translator, args.status)
                imported += 1
    conn.commit()
    conn.close()
    print(f"Imported {imported} translations; skipped {skipped} empty/missing rows.")


if __name__ == "__main__":
    main()
