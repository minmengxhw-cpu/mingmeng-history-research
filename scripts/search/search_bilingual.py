#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path


DEFAULT_DB_PATH = Path.cwd() / "data" / "research_index.sqlite"


def compact(text: str, limit: int = 520) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 3] + "..."


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def main() -> None:
    parser = argparse.ArgumentParser(description="Search original text and Chinese translations side by side.")
    parser.add_argument("query", help="Search query. Use English or Chinese.")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    original_sql = """
        SELECT
            pages.id AS page_id,
            documents.volume_id,
            documents.doc_id,
            documents.date_guess,
            documents.title,
            documents.matched_terms,
            pages.page_label,
            pages.page_url,
            pages.text AS original_text,
            translations.text AS zh_text,
            translations.status AS zh_status
        FROM page_fts
        JOIN pages ON pages.id = page_fts.rowid
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        WHERE page_fts MATCH ?
    """
    translation_sql = """
        SELECT
            pages.id AS page_id,
            documents.volume_id,
            documents.doc_id,
            documents.date_guess,
            documents.title,
            documents.matched_terms,
            pages.page_label,
            pages.page_url,
            pages.text AS original_text,
            translations.text AS zh_text,
            translations.status AS zh_status
        FROM translation_fts
        JOIN translations ON translations.id = translation_fts.rowid
        JOIN pages ON pages.id = translations.page_id
        JOIN documents ON documents.id = pages.document_id
        WHERE translation_fts MATCH ?
    """
    translation_like_sql = """
        SELECT
            pages.id AS page_id,
            documents.volume_id,
            documents.doc_id,
            documents.date_guess,
            documents.title,
            documents.matched_terms,
            pages.page_label,
            pages.page_url,
            pages.text AS original_text,
            translations.text AS zh_text,
            translations.status AS zh_status
        FROM translations
        JOIN pages ON pages.id = translations.page_id
        JOIN documents ON documents.id = pages.document_id
        WHERE translations.language='zh-CN' AND translations.text LIKE ?
    """

    seen: set[int] = set()
    rows = []
    for row in conn.execute(original_sql, (args.query,)):
        if row["page_id"] not in seen:
            rows.append(row)
            seen.add(row["page_id"])
    try:
        zh_rows = conn.execute(translation_sql, (args.query,)).fetchall()
    except sqlite3.OperationalError:
        zh_rows = []
    for row in zh_rows:
        if row["page_id"] not in seen:
            rows.append(row)
            seen.add(row["page_id"])
    if has_cjk(args.query):
        for row in conn.execute(translation_like_sql, (f"%{args.query}%",)):
            if row["page_id"] not in seen:
                rows.insert(0, row)
                seen.add(row["page_id"])

    for i, row in enumerate(rows[: args.limit], 1):
        page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
        print(f"{i}. {row['volume_id']}/{row['doc_id']} | {row['date_guess']} | {page}")
        print(f"   {row['title']}")
        print(f"   citation: {row['page_url']}")
        print(f"   terms: {row['matched_terms']}")
        print(f"   原文: {compact(row['original_text'])}")
        if row["zh_text"]:
            print(f"   中文({row['zh_status']}): {compact(row['zh_text'])}")
        else:
            print("   中文: [尚未翻译]")
        print()
    conn.close()


if __name__ == "__main__":
    main()
