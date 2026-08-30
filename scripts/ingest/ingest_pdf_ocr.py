#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import sqlite3
import subprocess
import tempfile
from pathlib import Path


DEFAULT_DB_PATH = Path.cwd() / "data" / "research_index.sqlite"
PDF_STORE = Path.cwd() / "data" / "pdf_sources"


def run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def extract_with_pdftotext(pdf: Path) -> list[str]:
    if not shutil.which("pdftotext"):
        return []
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "pages.txt"
        run(["pdftotext", "-layout", "-enc", "UTF-8", str(pdf), str(out)])
        text = out.read_text(encoding="utf-8", errors="replace")
    # pdftotext separates pages with form feed.
    return [page.strip() for page in text.split("\f")]


def extract_with_tesseract(pdf: Path) -> list[str]:
    if not shutil.which("pdftoppm") or not shutil.which("tesseract"):
        raise RuntimeError("OCR requires pdftoppm and tesseract.")
    pages: list[str] = []
    with tempfile.TemporaryDirectory() as tmp:
        prefix = Path(tmp) / "page"
        run(["pdftoppm", "-r", "200", "-png", str(pdf), str(prefix)])
        images = sorted(Path(tmp).glob("page-*.png"))
        for image in images:
            result = run(["tesseract", str(image), "stdout", "-l", "eng"])
            pages.append(result.stdout.strip())
    return pages


def ensure_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY,
            source_type TEXT NOT NULL,
            source_id TEXT NOT NULL UNIQUE,
            title TEXT,
            origin_url TEXT,
            local_path TEXT
        );
        CREATE TABLE IF NOT EXISTS documents (
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
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY,
            document_id INTEGER NOT NULL REFERENCES documents(id),
            page_label TEXT,
            page_url TEXT,
            text TEXT NOT NULL
        );
        """
    )
    has_fts = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='page_fts'"
    ).fetchone()
    if not has_fts:
        conn.execute(
            """
            CREATE VIRTUAL TABLE page_fts USING fts5(
                volume_id, doc_id, title, page_label, matched_terms, text
            )
            """
        )


def ingest(pdf: Path, title: str, source_id: str, origin_url: str = "", db_path: Path = DEFAULT_DB_PATH) -> None:
    PDF_STORE.mkdir(parents=True, exist_ok=True)
    stored_pdf = PDF_STORE / pdf.name
    if pdf.resolve() != stored_pdf.resolve():
        shutil.copy2(pdf, stored_pdf)

    pages = extract_with_pdftotext(stored_pdf)
    if not any(page.strip() for page in pages):
        pages = extract_with_tesseract(stored_pdf)

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    ensure_tables(conn)
    cur = conn.execute(
        "INSERT OR REPLACE INTO sources(source_type, source_id, title, origin_url, local_path) VALUES (?, ?, ?, ?, ?)",
        ("pdf", source_id, title, origin_url, str(stored_pdf)),
    )
    source_row = cur.lastrowid or conn.execute("SELECT id FROM sources WHERE source_id=?", (source_id,)).fetchone()[0]
    doc_key = f"pdf/{source_id}"
    existing = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()
    if existing:
        old_document_id = existing[0]
        old_pages = [row[0] for row in conn.execute("SELECT id FROM pages WHERE document_id=?", (old_document_id,))]
        for page_id in old_pages:
            conn.execute("DELETE FROM page_fts WHERE rowid=?", (page_id,))
        conn.execute("DELETE FROM pages WHERE document_id=?", (old_document_id,))
        conn.execute("DELETE FROM documents WHERE id=?", (old_document_id,))
    cur = conn.execute(
        """
        INSERT INTO documents(
            source_id, doc_key, volume_id, volume_title, doc_id, doc_number,
            title, date_guess, url, local_html, local_txt, hit_type, matched_terms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (source_row, doc_key, source_id, title, source_id, "", title, "", origin_url, "", "", "pdf", ""),
    )
    document_id = cur.lastrowid
    inserted = 0
    for idx, text in enumerate(pages, 1):
        text = text.strip()
        if not text:
            continue
        page_url = f"{origin_url}#page={idx}" if origin_url else str(stored_pdf)
        pcur = conn.execute(
            "INSERT INTO pages(document_id, page_label, page_url, text) VALUES (?, ?, ?, ?)",
            (document_id, str(idx), page_url, text),
        )
        conn.execute(
            "INSERT INTO page_fts(rowid, volume_id, doc_id, title, page_label, matched_terms, text) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (pcur.lastrowid, source_id, source_id, title, str(idx), "", text),
        )
        inserted += 1
    conn.commit()
    conn.close()
    print(f"Ingested {inserted} OCR/text pages from {stored_pdf}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest a PDF into the research index with OCR fallback.")
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--title", default="")
    parser.add_argument("--source-id", default="")
    parser.add_argument("--origin-url", default="")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH)
    args = parser.parse_args()
    title = args.title or args.pdf.stem
    source_id = args.source_id or args.pdf.stem
    ingest(args.pdf, title, source_id, args.origin_url, args.db)


if __name__ == "__main__":
    main()
