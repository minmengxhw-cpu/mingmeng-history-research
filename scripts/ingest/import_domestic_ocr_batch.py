#!/usr/bin/env python3
"""Import a provenance-linked domestic OCR pilot batch.

This importer is deliberately separate from the authorized-MMDA importer.  It
accepts public-scan sourcebooks for search/indexing, but records every page as
an OCR pilot and never upgrades it to a clean scholarly transcription.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{line_no}: record is not an object")
        rows.append(row)
    return rows


def resolve(value: str, root: Path) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def markdown_text(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if "## 识别文本" in text:
        text = text.split("## 识别文本", 1)[1]
    if "## 明细" in text:
        text = text.split("## 明细", 1)[0]
    return text.strip()


def validate(rows: list[dict[str, Any]], root: Path) -> list[dict[str, Any]]:
    if not rows:
        raise ValueError("manifest is empty")
    seen = set()
    prepared = []
    for row in rows:
        record_id = str(row.get("record_id", "")).strip()
        if not record_id or record_id in seen:
            raise ValueError(f"missing or duplicate record_id: {record_id!r}")
        seen.add(record_id)
        if row.get("source_kind") not in {"public_scan", "authorized_mmda"}:
            raise ValueError(f"{record_id}: unsupported source_kind")
        source = resolve(str(row.get("source_path", "")), root)
        expected = str(row.get("source_sha256", "")).lower()
        if not source.is_file() or len(expected) != 64 or sha256(source) != expected:
            raise ValueError(f"{record_id}: source file or SHA256 gate failed: {source}")
        pages = row.get("pages")
        if not isinstance(pages, list) or not pages:
            raise ValueError(f"{record_id}: pages is empty")
        normalized_pages = []
        for page in pages:
            ocr = resolve(str(page.get("ocr_markdown", "")), root)
            text = markdown_text(ocr) if ocr.is_file() else ""
            if not text:
                raise ValueError(f"{record_id}: missing OCR text: {ocr}")
            normalized_pages.append({**page, "_ocr_path": ocr, "_text": text})
        prepared.append({**row, "_source_path": source, "_pages": normalized_pages})
    return prepared


def ensure_schema(conn: sqlite3.Connection) -> None:
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
    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='page_fts'").fetchone():
        conn.execute("CREATE VIRTUAL TABLE page_fts USING fts5(volume_id, doc_id, title, page_label, matched_terms, text)")


def apply(rows: list[dict[str, Any]], db_path: Path, batch_id: str) -> dict[str, Any]:
    backup = db_path.with_name(f"{db_path.name}.{batch_id}.pre.bak")
    if db_path.exists():
        shutil.copy2(db_path, backup)
    inserted_pages = 0
    with sqlite3.connect(db_path) as conn:
        ensure_schema(conn)
        has_platform = "source_platform" in {row[1] for row in conn.execute("PRAGMA table_info(documents)")}
        for row in rows:
            source_key = f"domestic-ocr:{row['record_id']}"
            source_row = conn.execute("SELECT id FROM sources WHERE source_id=?", (source_key,)).fetchone()
            if source_row:
                source_id = source_row[0]
                conn.execute("UPDATE sources SET title=?, origin_url=?, local_path=? WHERE id=?", (row["title"], row.get("source_url", ""), str(row["_source_path"]), source_id))
            else:
                source_id = conn.execute("INSERT INTO sources(source_type,source_id,title,origin_url,local_path) VALUES(?,?,?,?,?)", ("domestic_ocr_pilot", source_key, row["title"], row.get("source_url", ""), str(row["_source_path"]))).lastrowid
            doc_key = f"domestic-ocr/{row['record_id']}"
            old = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()
            if old:
                page_ids = [x[0] for x in conn.execute("SELECT id FROM pages WHERE document_id=?", (old[0],))]
                for page_id in page_ids:
                    conn.execute("DELETE FROM page_fts WHERE rowid=?", (page_id,))
                conn.execute("DELETE FROM pages WHERE document_id=?", (old[0],))
                conn.execute("DELETE FROM documents WHERE id=?", (old[0],))
            tags = ",".join(row.get("event_tags", [])) if isinstance(row.get("event_tags"), list) else str(row.get("event_tags", ""))
            tags = f"{tags},ocr_status=pilot,source_kind={row['source_kind']}".strip(",")
            columns = ["source_id", "doc_key", "volume_id", "volume_title", "doc_id", "title", "date_guess", "url", "local_txt", "hit_type", "matched_terms"]
            values: list[Any] = [source_id, doc_key, "MMHIST", row.get("collection", ""), row["record_id"], row["title"], row.get("document_date", ""), row.get("source_url", ""), str(row["_source_path"]), "domestic_ocr_pilot", tags]
            if has_platform:
                columns.append("source_platform")
                values.append("domestic")
            document_id = conn.execute(f"INSERT INTO documents({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", values).lastrowid
            for page in row["_pages"]:
                page_label = str(page.get("page_label", ""))
                page_url = f"{row.get('source_url', '')}#page={page_label}"
                pcur = conn.execute("INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)", (document_id, page_label, page_url, page["_text"]))
                page_tags = f"{tags},ocr_mean_confidence={page.get('mean_confidence','')},ocr_page_status={page.get('ocr_status','draft')}"
                conn.execute("INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)", (pcur.lastrowid, "MMHIST", row["record_id"], row["title"], page_label, page_tags, page["_text"]))
                inserted_pages += 1
        conn.commit()
    return {"batch_id": batch_id, "records": len(rows), "pages": inserted_pages, "rollback_path": str(backup), "applied_at": datetime.now().isoformat(timespec="seconds")}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    rows = validate(read_jsonl(args.manifest), ROOT)
    result: dict[str, Any] = {"batch_id": args.batch_id, "records": len(rows), "gate": "PASS", "mode": "apply" if args.apply else "dry_run"}
    if args.apply:
        result.update(apply(rows, args.db, args.batch_id))
    else:
        result["next_action"] = "rerun with --apply after reviewing pilot tags"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
