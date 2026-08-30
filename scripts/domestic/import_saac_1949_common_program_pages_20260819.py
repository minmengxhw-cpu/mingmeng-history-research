#!/usr/bin/env python3
"""Import the three local 1949 Common Program scan images as empty-body pages.

The official album publishes a title leaf plus printed pages 54 and 64, not
the complete statute.  This importer writes documents/pages/provenance and
search cards, but never copies body text or runs OCR.
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
DEFAULT_MANIFEST = ROOT / "data" / "domestic" / "saac_1949_common_program_page_manifest_20260819.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def root_for_db(db: Path) -> Path:
    resolved = db.resolve()
    if resolved.name != "research_index.sqlite" or resolved.parent.name != "data":
        raise ValueError(f"expected data/research_index.sqlite, got {resolved}")
    return resolved.parent.parent


def resolve_under_root(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    path.relative_to(root.resolve())
    return path


def bigramize(text: str) -> str:
    output: list[str] = []
    for chunk in text.split():
        if chunk and all("\u3400" <= char <= "\u9fff" for char in chunk):
            output.extend(chunk[index : index + 2] for index in range(len(chunk) - 1))
        else:
            output.append(chunk)
    return " ".join(output)


def load_manifest(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "domestic_saac_image_page_manifest.v1":
        raise ValueError("unexpected manifest schema")
    pages = payload.get("pages")
    if not isinstance(pages, list) or len(pages) != 3:
        raise ValueError("expected exactly three pages")
    return payload


def prepare(db: Path, manifest_path: Path) -> dict[str, Any]:
    root = root_for_db(db)
    manifest = load_manifest(manifest_path)
    files = []
    for page in manifest["pages"]:
        source = resolve_under_root(root, page["source_file"])
        if not source.is_file():
            raise FileNotFoundError(source)
        actual = sha256(source)
        if actual != page["source_sha256"]:
            raise RuntimeError(f"SHA mismatch {page['source_file']}: {actual}")
        if source.stat().st_size != int(page["source_file_size"]):
            raise RuntimeError(f"size mismatch {page['source_file']}")
        files.append(str(source))
    with sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        source_row = conn.execute(
            "SELECT id FROM sources WHERE source_id=?", (manifest["source_id"],)
        ).fetchone()
        if source_row is None:
            raise RuntimeError(f"missing source {manifest['source_id']}")
        document = conn.execute(
            "SELECT id FROM documents WHERE doc_key=?", (manifest["doc_key"],)
        ).fetchone()
        if document:
            raise RuntimeError("doc_key already exists")
        candidate = conn.execute(
            "SELECT candidate_id FROM domestic_candidates WHERE candidate_id=?",
            (manifest["candidate_id"],),
        ).fetchone()
        if candidate is None:
            raise RuntimeError("candidate missing")
    return {
        "status": "READY",
        "formal_db_sha256": sha256(db.resolve()),
        "doc_key": manifest["doc_key"],
        "page_count": 3,
        "files": files,
        "body_text_included": False,
        "ocr_included": False,
        "citation_ready_pages": 0,
    }


def apply_import(db: Path, manifest_path: Path, backup: Path, expected_db_sha: str) -> dict[str, Any]:
    actual_db = db.resolve()
    before_sha = sha256(actual_db)
    if before_sha != expected_db_sha:
        raise RuntimeError(f"database SHA mismatch: got {before_sha}")
    if backup.exists():
        raise FileExistsError(backup)
    prepared = prepare(db, manifest_path)
    root = root_for_db(db)
    manifest = load_manifest(manifest_path)
    backup.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(actual_db, backup)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    tags_base = [
        "source_kind=official_archive_digital_scan",
        "evidence_level=L1",
        "body_text=false",
        "ocr_status=not_performed",
        "citation_ready=false",
        "needs_human_review=true",
        "review_status=review_only",
        f"batch={manifest['batch_id']}",
        f"event={manifest['event_id']}",
        "excerpt_not_complete_text=true",
    ]
    page_ids: list[int] = []
    with sqlite3.connect(actual_db) as conn:
        conn.execute("PRAGMA foreign_keys=ON")
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
                "saac-05-68",
                manifest["source_title"],
                "1949-09-29-01",
                manifest["source_title"],
                manifest["document_date"],
                manifest["source_url"],
                None,
                "domestic_archive_scan_review",
                ";".join(tags_base),
                "domestic",
                manifest["candidate_id"],
            ),
        ).lastrowid
        for page in manifest["pages"]:
            terms = list(page.get("search_terms") or [])
            tags = ";".join(tags_base + [f"term={term}" for term in terms])
            label = str(page["page_label"])
            page_id = conn.execute(
                "INSERT INTO pages(document_id,page_label,page_url,text) VALUES(?,?,?,?)",
                (document_id, label, page["official_image_url"], ""),
            ).lastrowid
            page_ids.append(int(page_id))
            conn.execute(
                "INSERT INTO page_fts(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (page_id, "saac-05-68", "1949-09-29-01", manifest["source_title"], label, tags, ""),
            )
            conn.execute(
                "INSERT INTO page_fts_bigram(rowid,volume_id,doc_id,title,page_label,matched_terms,text) VALUES(?,?,?,?,?,?,?)",
                (
                    page_id,
                    "saac-05-68",
                    "1949-09-29-01",
                    manifest["source_title"],
                    label,
                    tags,
                    bigramize(" ".join(terms)),
                ),
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
                    page_id,
                    document_id,
                    manifest["source_id"],
                    page["source_file"],
                    page["source_sha256"],
                    int(page["source_file_size"]),
                    None,
                    int(page["physical_page_no"]),
                    page.get("printed_page"),
                    page["source_file"],
                    page["source_sha256"],
                    None,
                    None,
                    None,
                    None,
                    "not_performed",
                    None,
                    None,
                    0,
                    0,
                    1,
                    "review_only",
                    "空正文导入：只登记官方影像、页序和哈希；未读取正文、未运行OCR。三页不是共同纲领全件。",
                    None,
                    "1941-1949",
                    1949,
                    tags,
                    manifest["source_title"],
                    manifest["batch_id"],
                    now,
                    now,
                ),
            )
            conn.execute(
                """INSERT OR IGNORE INTO research_events(
                    scope_type,scope_slug,scope_name,page_id,event_date,event_year,
                    event_title,event_summary,actors,tags,places,organizations,importance)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    "topic",
                    manifest["event_id"],
                    "1949年新政协筹备、民主人士北上与第一届全体会议",
                    page_id,
                    "1949-09-29",
                    "1949",
                    page["role"],
                    "专题导航关联（仅页级入口，非正文事实断言）：该页属于国家档案局共同纲领官方影像选定页，不是全件，正文未核验。",
                    "",
                    "saac_scan;review_only;common_program_excerpt",
                    "北平",
                    "",
                    15,
                ),
            )
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = len(conn.execute("PRAGMA foreign_key_check").fetchall())
        if integrity != "ok" or fk:
            conn.rollback()
            raise RuntimeError(f"validation failed integrity={integrity} fk={fk}")
        conn.commit()
    return {
        "status": "APPLIED",
        "document_id": int(document_id),
        "page_ids": page_ids,
        "before_db_sha256": before_sha,
        "after_db_sha256": sha256(actual_db),
        "backup": str(backup),
        "prepared": prepared,
        "integrity_check": integrity,
        "foreign_key_violations": fk,
        "body_text_included": False,
        "ocr_included": False,
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
    if args.dry_run:
        print(json.dumps(prepare(db, manifest), ensure_ascii=False, indent=2))
        return 0
    if not args.expected_db_sha or not args.backup:
        parser.error("--apply requires --expected-db-sha and --backup")
    print(
        json.dumps(
            apply_import(db, manifest, args.backup.expanduser().resolve(), args.expected_db_sha),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
