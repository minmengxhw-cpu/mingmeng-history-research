#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
from pathlib import Path

from translate_missing_pages_argos import GLOSSARY_PATH, glossary_postedit, load_glossary


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"


def main() -> None:
    glossary = load_glossary()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            translations.id,
            translations.text,
            translations.language,
            pages.page_label,
            documents.title
        FROM translations
        JOIN pages ON pages.id = translations.page_id
        JOIN documents ON documents.id = pages.document_id
        WHERE translations.language = 'zh-CN'
          AND translations.translator = 'argos-en-zh-local'
        """
    ).fetchall()
    changed = 0
    for row in rows:
        updated = glossary_postedit(row["text"], glossary)
        if updated == row["text"]:
            continue
        conn.execute("UPDATE translations SET text=? WHERE id=?", (updated, row["id"]))
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (row["id"],))
        conn.execute(
            "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, ?, ?, ?, ?)",
            (row["id"], row["language"], row["title"], row["page_label"] or "doc-level", updated),
        )
        changed += 1
    conn.commit()
    conn.close()
    print(f"Post-edited {changed} translations using {GLOSSARY_PATH}.")


if __name__ == "__main__":
    main()
