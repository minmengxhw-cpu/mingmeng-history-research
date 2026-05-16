#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "research_index.sqlite"
MANIFEST = ROOT / "data" / "wilson_center" / "manifest.json"


def compact(text: str) -> str:
    text = text.replace("\x0c", "\n\n--- page break ---\n\n")
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    return text.strip()


def infer_doc_id(record: dict[str, str]) -> str:
    m = re.search(r"/document/([^/?#]+)", record.get("original_url", ""))
    if m:
        return m.group(1)
    return record["doc_key"].replace("wilson:", "")


def split_pages(text: str) -> list[tuple[str, str]]:
    parts = [p.strip() for p in re.split(r"\n\s*--- page break ---\s*\n", text) if p.strip()]
    if len(parts) <= 1:
        return [("1", text)]
    return [(str(i + 1), part) for i, part in enumerate(parts)]


def ensure_columns(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(documents)")}
    if "source_platform" not in cols:
        conn.execute("ALTER TABLE documents ADD COLUMN source_platform TEXT DEFAULT 'frus'")


def main() -> None:
    records = json.loads(MANIFEST.read_text(encoding="utf-8"))
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    ensure_columns(conn)
    cur = conn.cursor()

    row = cur.execute("SELECT id FROM sources WHERE source_type='wilson' AND source_id='wilson-digital-archive'").fetchone()
    if row:
        source_id = row["id"]
    else:
        cur.execute(
            """
            INSERT INTO sources(source_type, source_id, title, origin_url, local_path)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "wilson",
                "wilson-digital-archive",
                "Wilson Center Digital Archive",
                "https://www.wilsoncenter.org/digital-archive",
                "data/wilson_center",
            ),
        )
        source_id = cur.lastrowid

    inserted = 0
    replaced = 0
    skipped = 0
    for record in records:
        if record.get("status") != "ok":
            skipped += 1
            continue
        txt_path = ROOT / record["local_txt"]
        text = compact(txt_path.read_text(encoding="utf-8", errors="replace"))
        if len(text) < 500:
            skipped += 1
            continue

        old = cur.execute("SELECT id FROM documents WHERE doc_key=?", (record["doc_key"],)).fetchone()
        if old:
            document_id = old["id"]
            old_page_ids = [row["id"] for row in cur.execute("SELECT id FROM pages WHERE document_id=?", (document_id,))]
            for page_id in old_page_ids:
                translation_ids = [
                    row["id"]
                    for row in cur.execute("SELECT id FROM translations WHERE page_id=?", (page_id,))
                ]
                for translation_id in translation_ids:
                    cur.execute("DELETE FROM translation_fts WHERE rowid=?", (translation_id,))
                cur.execute("DELETE FROM translations WHERE page_id=?", (page_id,))
                cur.execute("DELETE FROM page_fts WHERE rowid=?", (page_id,))
            cur.execute("DELETE FROM pages WHERE document_id=?", (document_id,))
            cur.execute("DELETE FROM document_classifications WHERE document_id=?", (document_id,))
            cur.execute(
                """
                UPDATE documents
                SET source_id=?, volume_id=?, volume_title=?, doc_id=?, doc_number='',
                    title=?, date_guess=?, url=?, local_html=?, local_txt=?,
                    hit_type=?, matched_terms=?, source_platform='wilson'
                WHERE id=?
                """,
                (
                    source_id,
                    "WILSON",
                    "Wilson Center Digital Archive",
                    infer_doc_id(record),
                    record["title"],
                    record["date"],
                    record["original_url"],
                    record["local_raw"] if record["kind"] == "html" else "",
                    record["local_txt"],
                    "wilson",
                    "Wilson Center; 中国民主同盟; 民主党派; 新政协; 中苏关系",
                    document_id,
                ),
            )
            replaced += 1
        else:
            cur.execute(
                """
                INSERT INTO documents(
                    source_id, doc_key, volume_id, volume_title, doc_id, doc_number,
                    title, date_guess, url, local_html, local_txt, hit_type,
                    matched_terms, source_platform
                ) VALUES (?, ?, ?, ?, ?, '', ?, ?, ?, ?, ?, ?, ?, 'wilson')
                """,
                (
                    source_id,
                    record["doc_key"],
                    "WILSON",
                    "Wilson Center Digital Archive",
                    infer_doc_id(record),
                    record["title"],
                    record["date"],
                    record["original_url"],
                    record["local_raw"] if record["kind"] == "html" else "",
                    record["local_txt"],
                    "wilson",
                    "Wilson Center; 中国民主同盟; 民主党派; 新政协; 中苏关系",
                ),
            )
            document_id = cur.lastrowid
            inserted += 1

        for page_label, page_text in split_pages(text):
            page_url = f"{record['original_url']}#page={page_label}"
            cur.execute(
                "INSERT INTO pages(document_id, page_label, page_url, text) VALUES (?, ?, ?, ?)",
                (document_id, page_label, page_url, page_text),
            )
            page_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO page_fts(rowid, volume_id, doc_id, title, page_label, matched_terms, text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    page_id,
                    "WILSON",
                    infer_doc_id(record),
                    record["title"],
                    page_label,
                    "Wilson Center; 中国民主同盟; 民主党派; 新政协; 中苏关系",
                    page_text,
                ),
            )

        cur.execute(
            """
            INSERT OR REPLACE INTO document_classifications(document_id, grade, score, reason, needs_review)
            VALUES (?, ?, ?, ?, 0)
            """,
            (document_id, record["grade"], int(record["score"]), record["reason"]),
        )

    conn.commit()
    counts = cur.execute(
        "SELECT source_platform, COUNT(*) FROM documents GROUP BY source_platform ORDER BY COUNT(*) DESC"
    ).fetchall()
    print(f"inserted={inserted} replaced={replaced} skipped={skipped}")
    for platform, count in counts:
        print(f"{platform}: {count}")
    conn.close()


if __name__ == "__main__":
    main()
