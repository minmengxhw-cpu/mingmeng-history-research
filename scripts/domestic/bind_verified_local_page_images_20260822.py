#!/usr/bin/env python3
"""Bind local page-image paths and hashes for already verified pages.

This is a provenance-only migration. It does not change page text, OCR fields,
source-file fields, citation flags, or evidence level. The formal database is
external to Git and must be backed up byte-for-byte before ``--apply``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data" / "research_index.sqlite"
MANIFEST_PATH = ROOT / "data" / "domestic" / "local_page_image_provenance_20260822.json"
DEFAULT_REPORT = ROOT / "work" / "domestic" / "local_page_image_provenance_20260822" / "APPLY_REPORT.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_manifest() -> dict[str, object]:
    payload = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if payload.get("schema") != "domestic_local_page_image_provenance.v1":
        raise SystemExit("unexpected provenance manifest schema")
    pages = payload.get("pages")
    if not isinstance(pages, list) or not pages:
        raise SystemExit("provenance manifest has no pages")
    ids = [int(item["page_id"]) for item in pages]
    if len(ids) != len(set(ids)):
        raise SystemExit("provenance manifest has duplicate page IDs")
    if payload.get("body_read") is not False or payload.get("ocr_performed") is not False:
        raise SystemExit("provenance manifest must remain body-free and OCR-free")
    if payload.get("citation_status_changed") is not False:
        raise SystemExit("provenance manifest must not change citation status")
    return payload


def validate_inputs(connection: sqlite3.Connection, db: Path, manifest: dict[str, object], *, applied: bool = False) -> list[dict[str, object]]:
    source_root = db.resolve().parent.parent
    rows: list[dict[str, object]] = []
    for item in manifest["pages"]:
        page_id = int(item["page_id"])
        source_file = str(item["source_file"])
        source_path = source_root / source_file
        image_path = source_root / str(item["page_image_path"])
        if not source_path.is_file() or sha256_file(source_path) != str(item["source_sha256"]).lower():
            raise SystemExit(f"page {page_id} source file/hash check failed: {source_file}")
        if not image_path.is_file() or sha256_file(image_path) != str(item["page_image_sha256"]).lower():
            raise SystemExit(f"page {page_id} page image/hash check failed: {image_path}")
        if Path(str(item["page_image_path"])).is_absolute():
            raise SystemExit(f"page {page_id} has an absolute page-image path")
        row = connection.execute(
            """
            SELECT pp.page_id, pp.source_file, pp.source_sha256, pp.pdf_page_no,
                   pp.physical_page_no, pp.page_image_path, pp.page_image_sha256,
                   pp.citation_ready, pp.needs_human_review, pp.review_status,
                   pp.human_review_note, d.source_platform
            FROM page_provenance pp
            JOIN documents d ON d.id=pp.document_id
            WHERE pp.page_id=?
            """,
            (page_id,),
        ).fetchone()
        if row is None:
            raise SystemExit(f"missing provenance row: page {page_id}")
        (
            _page_id, current_source, current_source_sha, pdf_page, physical_page,
            current_image, current_image_sha, citation_ready, needs_review,
            review_status, human_note, platform,
        ) = row
        if platform != "domestic":
            raise SystemExit(f"page {page_id} is not a domestic record")
        if current_source != source_file or str(current_source_sha).lower() != str(item["source_sha256"]).lower():
            raise SystemExit(f"page {page_id} source provenance differs from manifest")
        if int(pdf_page) != int(item["pdf_page_no"]) or int(physical_page) != int(item["physical_page_no"]):
            raise SystemExit(f"page {page_id} page-number provenance differs from manifest")
        if applied:
            if current_image != item["page_image_path"] or str(current_image_sha or "").lower() != str(item["page_image_sha256"]).lower():
                raise SystemExit(f"page {page_id} applied page-image provenance does not match manifest")
        else:
            if current_image != item["expected_current_page_image_path"]:
                raise SystemExit(f"page {page_id} current page-image path is not the expected pre-migration value")
            if current_image_sha not in (None, ""):
                raise SystemExit(f"page {page_id} already has a page-image SHA; refusing overwrite")
        if (int(citation_ready), int(needs_review), str(review_status), bool(str(human_note or "").strip())) != (1, 0, "human_verified", True):
            raise SystemExit(f"page {page_id} is not an already human-verified strict record")
        rows.append({"page_id": page_id, "old_image": current_image, "new_image": item["page_image_path"], "new_sha": item["page_image_sha256"]})
    return rows


def post_validate(connection: sqlite3.Connection, page_ids: list[int], strict_target_before: int, pages_before: int, fts_before: int) -> dict[str, object]:
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
    foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
    pages_after = int(connection.execute("SELECT count(*) FROM pages").fetchone()[0])
    fts_after = int(connection.execute("SELECT count(*) FROM page_fts").fetchone()[0])
    placeholders = ",".join("?" for _ in page_ids)
    strict_after = int(connection.execute(
        f"SELECT count(*) FROM page_provenance WHERE page_id IN ({placeholders}) AND citation_ready=1 AND needs_human_review=0 AND review_status='human_verified'",
        page_ids,
    ).fetchone()[0])
    image_sha_count = int(connection.execute(
        f"SELECT count(*) FROM page_provenance WHERE page_id IN ({placeholders}) AND page_image_sha256 IS NOT NULL",
        page_ids,
    ).fetchone()[0])
    if integrity != "ok" or foreign_keys or pages_after != pages_before or fts_after != fts_before or strict_target_before != strict_after or image_sha_count != len(page_ids):
        raise SystemExit(
            f"post-validation failed: integrity={integrity}, fk={len(foreign_keys)}, pages={pages_before}->{pages_after}, "
            f"fts={fts_before}->{fts_after}, strict_targets={strict_target_before}->{strict_after}, image_sha_count={image_sha_count}"
        )
    return {
        "integrity_check": integrity,
        "foreign_key_violations": len(foreign_keys),
        "pages_before": pages_before,
        "pages_after": pages_after,
        "page_fts_before": fts_before,
        "page_fts_after": fts_after,
        "strict_target_count": strict_after,
        "page_image_sha_count": image_sha_count,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--verify-applied", action="store_true")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    manifest = load_manifest()
    db = DB_PATH.resolve()
    expected_db_sha = str(manifest["formal_db_sha256_before"]).lower()
    current_db_sha = sha256_file(db)
    if not args.verify_applied and current_db_sha != expected_db_sha:
        raise SystemExit(f"database SHA mismatch: expected {expected_db_sha}, got {current_db_sha}")

    rows: list[dict[str, object]] = []
    strict_before = 0
    pages_before = 0
    fts_before = 0
    if not args.verify_applied:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            rows = validate_inputs(connection, db, manifest)
            strict_before = int(connection.execute("SELECT count(*) FROM page_provenance WHERE citation_ready=1 AND needs_human_review=0 AND review_status='human_verified'").fetchone()[0])
            pages_before = int(connection.execute("SELECT count(*) FROM pages").fetchone()[0])
            fts_before = int(connection.execute("SELECT count(*) FROM page_fts").fetchone()[0])

    if args.verify_applied:
        with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
            connection.row_factory = sqlite3.Row
            rows = validate_inputs(connection, db, manifest, applied=True)
            pages_before = int(connection.execute("SELECT count(*) FROM pages").fetchone()[0])
            fts_before = int(connection.execute("SELECT count(*) FROM page_fts").fetchone()[0])
            checks = post_validate(connection, [int(r["page_id"]) for r in rows], len(rows), pages_before, fts_before)
        report = {
            "schema": "domestic_local_page_image_provenance_apply.v1",
            "status": "VERIFIED_APPLIED",
            "database_sha256_before": expected_db_sha,
            "database_sha256_after": current_db_sha,
            "page_ids": [int(r["page_id"]) for r in rows],
            "page_image_bindings_added": len(rows),
            "body_text_changed": False,
            "ocr_performed": False,
            "citation_status_changed": False,
            **checks,
        }
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))
        return 0

    if not args.apply:
        print(json.dumps({"status": "READY", "database_sha256": current_db_sha, "page_ids": [r["page_id"] for r in rows], "body_text_changed": False, "ocr_performed": False, "citation_status_changed": False}, ensure_ascii=False))
        return 0

    if args.backup is None:
        raise SystemExit("--backup is required with --apply")
    backup = args.backup.expanduser().resolve()
    if not backup.is_file() or sha256_file(backup) != current_db_sha:
        raise SystemExit("backup is missing or is not byte-identical to the current database")

    with sqlite3.connect(db) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        validate_inputs(connection, db, manifest)
        connection.execute("BEGIN IMMEDIATE")
        now = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
        for row in rows:
            connection.execute(
                "UPDATE page_provenance SET page_image_path=?, page_image_sha256=?, updated_at=? WHERE page_id=?",
                (row["new_image"], row["new_sha"], now, row["page_id"]),
            )
        connection.commit()
        checks = post_validate(connection, [int(r["page_id"]) for r in rows], len(rows), pages_before, fts_before)

    after_db_sha = sha256_file(db)
    report = {
        "schema": "domestic_local_page_image_provenance_apply.v1",
        "status": "APPLIED",
        "database_sha256_before": current_db_sha,
        "database_sha256_after": after_db_sha,
        "backup": str(backup),
        "page_ids": [int(r["page_id"]) for r in rows],
        "page_image_bindings_added": len(rows),
        "body_text_changed": False,
        "ocr_performed": False,
        "citation_status_changed": False,
        **checks,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
