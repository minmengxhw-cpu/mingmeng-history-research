#!/usr/bin/env python3
from __future__ import annotations

import csv
import re
import sqlite3
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag


ROOT = Path.cwd()
FRUS_DIR = ROOT / "data" / "frus_meng"
HITS_CSV = FRUS_DIR / "frus_meng_hits.csv"
DB_PATH = ROOT / "data" / "research_index.sqlite"


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def direct_text(tag: Tag) -> str:
    return compact(tag.get_text(" ", strip=True))


def iter_page_segments(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    doc = soup.select_one(".document") or soup.body or soup
    segments: list[dict[str, str]] = []
    current_page = ""
    buffer: list[str] = []

    def flush() -> None:
        nonlocal buffer
        text = compact(" ".join(buffer))
        if text:
            segments.append({"page": current_page, "text": text})
        buffer = []

    for child in doc.children:
        if isinstance(child, NavigableString):
            txt = compact(str(child))
            if txt:
                buffer.append(txt)
            continue
        if not isinstance(child, Tag):
            continue
        if child.name == "span" and "tei-pb" in (child.get("class") or []):
            flush()
            anchor = child.find("a", id=re.compile(r"pg_\d+"))
            current_page = anchor["id"].replace("pg_", "") if anchor and anchor.get("id") else ""
            continue
        if child.name in {"p", "h1", "h2", "h3", "h4", "li", "div"}:
            txt = direct_text(child)
            if txt:
                buffer.append(txt)
    flush()
    if not segments:
        text = compact(doc.get_text(" ", strip=True))
        if text:
            segments.append({"page": "", "text": text})
    return segments


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE sources (
            id INTEGER PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL UNIQUE,
            title TEXT,
            origin_url TEXT,
            local_path TEXT
        );

        CREATE TABLE documents (
            id INTEGER PRIMARY KEY,
            source_id INTEGER NOT NULL REFERENCES sources(id),
            doc_key TEXT NOT NULL UNIQUE,
            volume_id TEXT,
            volume_title TEXT,
            doc_id TEXT,
            doc_number TEXT,
            title TEXT,
            date_guess TEXT,
            url TEXT,
            local_html TEXT,
            local_txt TEXT,
            hit_type TEXT,
            matched_terms TEXT
        );

        CREATE TABLE pages (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL REFERENCES documents(id),
            page_label TEXT,
            page_url TEXT,
            text TEXT NOT NULL
        );

        CREATE VIRTUAL TABLE page_fts USING fts5(
            volume_id,
            doc_id,
            title,
            page_label,
            matched_terms,
            text
        );
        """
    )


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    create_schema(conn)

    rows = list(csv.DictReader(HITS_CSV.open(encoding="utf-8")))
    source_ids: dict[str, int] = {}
    doc_count = 0
    page_count = 0
    exact_page_count = 0

    for row in rows:
        volume_id = row["volume_id"]
        if volume_id not in source_ids:
            cur = conn.execute(
                "INSERT INTO sources(source_type, source_id, title, origin_url, local_path) VALUES (?, ?, ?, ?, ?)",
                (
                    "frus_epub",
                    volume_id,
                    row["volume_title"],
                    f"https://history.state.gov/historicaldocuments/{volume_id}",
                    str(FRUS_DIR / "epubs" / f"{volume_id}.epub"),
                ),
            )
            source_ids[volume_id] = cur.lastrowid

        doc_key = f"{volume_id}/{row['doc_id']}"
        cur = conn.execute(
            """
            INSERT INTO documents(
                source_id, doc_key, volume_id, volume_title, doc_id, doc_number,
                title, date_guess, url, local_html, local_txt, hit_type, matched_terms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_ids[volume_id],
                doc_key,
                volume_id,
                row["volume_title"],
                row["doc_id"],
                row["doc_number"],
                row["title"],
                row["date_guess"],
                row["url"],
                row["local_html"],
                row["local_txt"],
                row["hit_type"],
                row["matched_terms"],
            ),
        )
        document_id = cur.lastrowid
        doc_count += 1

        html = Path(row["local_html"]).read_text(encoding="utf-8", errors="replace")
        for segment in iter_page_segments(html):
            page = segment["page"]
            page_url = f"{row['url']}#pg_{page}" if page else row["url"]
            pcur = conn.execute(
                "INSERT INTO pages(document_id, page_label, page_url, text) VALUES (?, ?, ?, ?)",
                (document_id, page, page_url, segment["text"]),
            )
            conn.execute(
                """
                INSERT INTO page_fts(rowid, volume_id, doc_id, title, page_label, matched_terms, text)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (pcur.lastrowid, volume_id, row["doc_id"], row["title"], page, row["matched_terms"], segment["text"]),
            )
            page_count += 1
            if page:
                exact_page_count += 1

    conn.commit()
    conn.close()
    print(f"Wrote {DB_PATH}")
    print(f"Documents: {doc_count}")
    print(f"Page segments: {page_count}")
    print(f"Exact page-labelled segments: {exact_page_count}")


if __name__ == "__main__":
    main()
