#!/usr/bin/env python3
"""Register selected NLC 1949 conference-journal pages as metadata-only records.

This importer creates formal ``documents/pages/page_provenance`` rows and
searchable title/term cards, but deliberately writes an empty page body and
never runs OCR.  Every page stays ``review_only`` and ``citation_ready=0``.

The formal SQLite is the shared database pointed to by the checkout symlink.
Dry-run is read-only.  Apply mode requires the exact database SHA and a new
backup path; it only inserts additive records and navigation links.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_MANIFEST = ROOT / "data" / "domestic" / "nlc_1949_conference_journal_page_manifest_20260815.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_under_root(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    return path


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "domestic_nlc_conference_journal_page_manifest.v1":
        raise ValueError("unexpected manifest schema")
    pages = payload.get("pages")
    if not isinstance(pages, list) or not pages:
        raise ValueError("manifest pages must be non-empty")
    numbers = [int(page["pdf_page_no"]) for page in pages]
    if len(numbers) != len(set(numbers)) or any(number < 1 for number in numbers):
        raise ValueError("manifest page numbers must be unique positive integers")
    return payload


def root_for_db(db: Path) -> Path:
    resolved = db.resolve()
    if resolved.name != "research_index.sqlite" or resolved.parent.name != "data":
        raise ValueError(f"expected data/research_index.sqlite, got {resolved}")
    return resolved.parent.parent


def prepare(db: Path, manifest_path: Path) -> dict[str, Any]:
    root = root_for_db(db)
    manifest = load_manifest(manifest_path)
    source = resolve_under_root(root, manifest["source_file"])
    if not source.is_file():
        raise FileNotFoundError(f"source PDF missing from formal project root: {source}")
    actual_sha = sha256(source)
    if actual_sha != manifest["source_sha256"]:
        raise RuntimeError(f"source SHA mismatch: got {actual_sha}, expected {manifest['source_sha256']}")
    if source.stat().st_size != int(manifest["source_file_size"]):
        raise RuntimeError("source file size mismatch")
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        source_row = conn.execute(
            "SELECT id FROM sources WHERE source_id=?", (manifest["source_id"],)
        ).fetchone()
        document = conn.execute(
            "SELECT id, doc_key FROM documents WHERE doc_key=?", (manifest["doc_key"],)
        ).fetchone()
        if source_row or document:
            raise RuntimeError("source_id or doc_key already exists; refusing duplicate import")
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='research_events'"
        ).fetchone()
        if table is None:
            raise RuntimeError("research_events table is required")
    return {
        "status": "READY",
        "formal_db": str(db.resolve()),
        "formal_db_sha256": sha256(db.resolve()),
        "formal_project_root": str(root),
        "manifest": str(manifest_path.resolve()),
        "source_file": str(source),
        "source_sha256": actual_sha,
        "doc_key": manifest["doc_key"],
        "page_count": len(manifest["pages"]),
        "body_text_included": False,
        "ocr_included": False,
        "citation_ready_pages": 0,
        "review_only_pages": len(manifest["pages"]),
    }


def bigramize(text: str) -> str:
    output: list[str] = []
    for chunk in text.split():
        if all("\u3400" <= char <= "\u9fff" for char in chunk):
            output.extend(chunk[index : index + 2] for index in range(len(chunk) - 1))
        else:
            output.append(chunk)
    return " ".join(output)


def apply_import(db: Path, manifest_path: Path, backup: Path, expected_db_sha: str) -> dict[str, Any]:
    actual_db = db.resolve()
    before_sha = sha256(actual_db)
    if before_sha != expected_db_sha:
        raise RuntimeError(f"database SHA mismatch: got {before_sha}, expected {expected_db_sha}")
    if backup.exists():
        raise FileExistsError(f"refusing to overwrite backup: {backup}")
    prepared = prepare(db, manifest_path)
    root = root_for_db(db)
    manifest = load_manifest(manifest_path)
    source_path = resolve_under_root(root, manifest["source_file"])
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    if sha256(backup) != before_sha:
        raise RuntimeError("formal DB backup SHA mismatch")
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tags_base = [
        "source_kind=official_conference_journal_scan",
        "evidence_level=L1",
        "body_text=false",
        "ocr_status=not_performed",
        "citation_ready=false",
        "needs_human_review=true",
        "review_status=review_only",
        f"batch={manifest['batch_id']}",
        f"event={manifest['event_id']}",
    ]
    page_ids: list[int] = []
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.row_factory = sqlite3.Row
        conn.execute(
            "INSERT INTO sources(source_type,source_id,title,origin_url,local_path) VALUES(?,?,?,?,?)",
            (
                "domestic_conference_journal",
                manifest["source_id"],
                manifest["source_title"],
                manifest["source_url"],
                manifest["source_file"],
            ),
        )
        source_db_id = conn.execute(
            "SELECT id FROM sources WHERE source_id=?", (manifest["source_id"],)
        ).fetchone()[0]
        document_id = conn.execute(
            """INSERT INTO documents(
                 source_id,doc_key,volume_id,volume_title,doc_id,title,date_guess,url,
                 local_txt,hit_type,matched_terms,source_platform,ingested_candidate_id)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                source_db_id,
                manifest["doc_key"],
                manifest["volume_id"],
                manifest["source_title"],
                manifest["volume_id"],
                manifest["source_title"],
                manifest["document_date"],
                manifest["source_url"],
                None,
                "domestic_conference_journal_review",
                ";".join(tags_base),
                "domestic",
                None,
            ),
        ).lastrowid
        for page in manifest["pages"]:
            terms = list(page.get("search_terms") or [])
            tags = ";".join(tags_base + [f"term={term}" for term in terms])
            label = str(page["page_label"])
            page_url = f"{manifest['source_url']}#page={int(page['pdf_page_no'])}"
            page_id = conn.execute(
                "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                (document_id, label, page_url, ""),
            ).lastrowid
            page_ids.append(int(page_id))
            conn.execute(
                "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, manifest["volume_id"], manifest["volume_id"], manifest["source_title"], label, tags, ""),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, manifest["volume_id"], manifest["volume_id"], manifest["source_title"], label, tags, bigramize(" ".join(terms))),
            )
            conn.execute(
                """INSERT INTO page_provenance(
                    page_id,document_id,source_id,source_file,source_sha256,source_file_size,
                    pdf_page_no,physical_page_no,printed_page,page_image_path,page_image_sha256,
                    ocr_md_path,ocr_md_sha256,ocr_engine,ocr_model,ocr_mode,ocr_lines,
                    ocr_mean_confidence,text_chars,citation_ready,needs_human_review,review_status,
                    machine_review_note,human_review_note,period,year,event_tags,source_title,
                    batch_id,created_at,updated_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    page_id, document_id, manifest["source_id"], manifest["source_file"],
                    manifest["source_sha256"], int(manifest["source_file_size"]),
                    int(page["pdf_page_no"]), int(page["pdf_page_no"]), None, None, None,
                    None, None, None, None, "not_performed", None, None, 0,
                    0, 1, "review_only",
                    "仅登记正式会刊原件和选定页定位；未读取正文、未运行OCR、未完成逐字人工复核。",
                    None, "1941-1949", 1949, tags, manifest["source_title"],
                    manifest["batch_id"], now, now,
                ),
            )
            conn.execute(
                """INSERT OR IGNORE INTO research_events(
                    scope_type,scope_slug,scope_name,page_id,event_date,event_year,
                    event_title,event_summary,actors,tags,places,organizations,importance)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "topic", manifest["event_id"], "1949年新政协筹备、民主人士北上与第一届全体会议",
                    page_id, "1949", "1949", page["role"],
                    "专题导航关联（仅来源页级入口，非正文事实断言）：该页属于1949年正式会议会刊扫描，正文与人名仍待人工复核。",
                    "张澜；沈钧儒；章伯钧；张东荪；史良；沙千里" if int(page["pdf_page_no"]) == 30 else "",
                    ";".join(["nlc_conference_journal", "review_only"] + terms),
                    "北平", "", 10,
                ),
            )
        conn.commit()
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        fts_missing = conn.execute(
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE p.id IN (%s) AND f.rowid IS NULL" % ",".join("?" for _ in page_ids),
            page_ids,
        ).fetchone()[0]
        provenance_count = conn.execute(
            "SELECT COUNT(*) FROM page_provenance WHERE document_id=?", (document_id,)
        ).fetchone()[0]
        event_count = conn.execute(
            "SELECT COUNT(*) FROM research_events WHERE scope_slug=? AND page_id IN (%s)" % ",".join("?" for _ in page_ids),
            [manifest["event_id"], *page_ids],
        ).fetchone()[0]
    return {
        "status": "APPLIED",
        "batch_id": manifest["batch_id"],
        "document_id": int(document_id),
        "page_ids": page_ids,
        "before_db_sha256": before_sha,
        "after_db_sha256": sha256(actual_db),
        "backup": str(backup),
        "integrity_check": integrity,
        "foreign_key_violations": fk,
        "pages_without_fts": fts_missing,
        "page_provenance_count": provenance_count,
        "event_link_count": event_count,
        "citation_ready_pages": 0,
        "review_only_pages": len(page_ids),
        "body_text_included": False,
        "ocr_included": False,
        "source_file": str(source_path),
        "source_file_sha256": manifest["source_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()
    if args.apply == args.dry_run:
        parser.error("choose exactly one of --dry-run or --apply")
    db = args.db.expanduser().resolve()
    manifest = args.manifest.expanduser().resolve()
    prepared = prepare(db, manifest)
    if args.dry_run:
        print(json.dumps(prepared, ensure_ascii=False, indent=2))
        return 0
    if not args.expected_db_sha or not args.backup:
        parser.error("--apply requires --expected-db-sha and --backup")
    print(json.dumps(apply_import(db, manifest, args.backup.expanduser().resolve(), args.expected_db_sha), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
