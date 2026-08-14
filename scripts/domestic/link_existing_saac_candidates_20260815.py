#!/usr/bin/env python3
"""Close explicit candidate -> formal-document links for existing SAAC scans.

This is a provenance repair, not a content import.  The selected SAAC image/OCR
records already exist in the formal SQLite index; this script only connects the
newer accepted candidate rows to those existing document IDs.  It deliberately
does not change page provenance, OCR review status, or citation readiness.

Default mode is read-only.  ``--apply`` requires an expected database SHA and a
non-existing backup path so that a stale checkout or an accidental overwrite
cannot silently change the formal index.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"

# These are intentionally explicit.  Each candidate is a newer SAAC catalogue
# row whose official page/image is already represented by the stated formal doc.
# Do not infer mappings from title similarity in the write path.
MAPPINGS = [
    {
        "candidate_id": "domestic:SAAC:1948-05-01-01",
        "document_id": 1510,
        "reason": "same SAAC 01_04 image/OCR record; candidate title/date are the expanded official title",
    },
    {
        "candidate_id": "domestic:SAAC:1948-08-01-01",
        "document_id": 1514,
        "reason": "same SAAC 01_06/01_15 image/OCR record; the formal record preserves the local scan path",
    },
    {
        "candidate_id": "domestic:SAAC:1948-10-01-01",
        "document_id": 1537,
        "reason": "same SAAC 01_07 image/OCR record; official candidate and formal scan share the date and actors",
    },
    {
        "candidate_id": "domestic:SAAC:1949-02-01-01",
        "document_id": 1513,
        "reason": "same SAAC 01_14 five-image record; candidate is the expanded official page title",
    },
    {
        "candidate_id": "domestic:SAAC:1949-09-21-01",
        "document_id": 1538,
        "reason": "same SAAC 05_02 representative-list scan",
    },
    {
        "candidate_id": "domestic:SAAC:1949-09-21-02",
        "document_id": 1539,
        "reason": "same SAAC 05_03 representative-signature scan",
    },
    {
        "candidate_id": "domestic:SAAC:1949-09-21-03",
        "document_id": 1542,
        "reason": "same SAAC 05_06 session-procedure scan",
    },
    {
        "candidate_id": "domestic:SAAC:1949-09-21-04",
        "document_id": 1543,
        "reason": "same SAAC 05_07 presidium-list scan",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def counts(conn: sqlite3.Connection) -> dict[str, int | str]:
    result: dict[str, int | str] = {}
    for key, query in {
        "candidate_links": "SELECT count(*) FROM domestic_candidates WHERE ingested_document_id IS NOT NULL",
        "reverse_links": "SELECT count(*) FROM documents WHERE ingested_candidate_id IS NOT NULL",
        "pages_without_fts": "SELECT count(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL",
        "fts_without_pages": "SELECT count(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL",
        "foreign_key_violations": "SELECT count(*) FROM pragma_foreign_key_check",
    }.items():
        result[key] = int(conn.execute(query).fetchone()[0])
    result["integrity_check"] = str(conn.execute("PRAGMA integrity_check").fetchone()[0])
    return result


def plan(conn: sqlite3.Connection) -> dict[str, object]:
    if "ingested_document_id" not in {
        row[1] for row in conn.execute("PRAGMA table_info(domestic_candidates)")
    }:
        raise RuntimeError("domestic_candidates.ingested_document_id is absent")
    if "ingested_candidate_id" not in {
        row[1] for row in conn.execute("PRAGMA table_info(documents)")
    }:
        raise RuntimeError("documents.ingested_candidate_id is absent")

    rows: list[dict[str, object]] = []
    errors: list[str] = []
    for item in MAPPINGS:
        candidate = conn.execute(
            """SELECT candidate_id, title, repository_code, source_url,
                      ingested_document_id
               FROM domestic_candidates WHERE candidate_id=?""",
            (item["candidate_id"],),
        ).fetchone()
        document = conn.execute(
            """SELECT d.id, d.doc_key, d.title, d.local_txt,
                      count(p.id) AS page_count,
                      count(pp.page_id) AS provenance_count
               FROM documents d
               LEFT JOIN pages p ON p.document_id=d.id
               LEFT JOIN page_provenance pp ON pp.page_id=p.id
               WHERE d.id=?
               GROUP BY d.id, d.doc_key, d.title, d.local_txt""",
            (item["document_id"],),
        ).fetchone()
        row: dict[str, object] = dict(item)
        row["candidate"] = dict(candidate) if candidate else None
        row["document"] = dict(document) if document else None
        if candidate is None:
            errors.append(f"candidate missing: {item['candidate_id']}")
        else:
            if candidate["repository_code"] != "SAAC":
                errors.append(f"candidate is not SAAC: {item['candidate_id']}")
            if candidate["source_url"] and "saac.gov.cn" not in str(candidate["source_url"]):
                errors.append(f"candidate source is not SAAC official URL: {item['candidate_id']}")
            existing = candidate["ingested_document_id"]
            if existing not in (None, item["document_id"]):
                errors.append(
                    f"candidate link conflict: {item['candidate_id']} already points to {existing}"
                )
        if document is None:
            errors.append(f"document missing: {item['document_id']}")
        else:
            if not str(document["doc_key"]).startswith("domestic-ocr/SAAC:"):
                errors.append(f"document is not SAAC OCR: {item['document_id']}")
            if "saac_scans" not in str(document["local_txt"] or ""):
                errors.append(f"document has no local SAAC scan path: {item['document_id']}")
            if int(document["page_count"] or 0) <= 0:
                errors.append(f"document has no pages: {item['document_id']}")
            if int(document["provenance_count"] or 0) != int(document["page_count"] or 0):
                errors.append(f"document provenance count mismatch: {item['document_id']}")
            reverse = conn.execute(
                "SELECT ingested_candidate_id FROM documents WHERE id=?",
                (item["document_id"],),
            ).fetchone()[0]
            if reverse not in (None, item["candidate_id"]):
                errors.append(
                    f"reverse link conflict: doc {item['document_id']} already points to {reverse}"
                )
            row["reverse_link"] = reverse
        rows.append(row)
    return {"mappings": rows, "errors": errors}


def write_report(path: Path | None, payload: dict[str, object]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-db-sha")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()

    db = args.db.resolve()
    before_sha = sha256_file(db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        before_counts = counts(conn)
        planned = plan(conn)
        payload: dict[str, object] = {
            "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
            "mode": "apply" if args.apply else "dry_run",
            "db": str(db),
            "before_sha256": before_sha,
            "mapping_count": len(MAPPINGS),
            "before_counts": before_counts,
            **planned,
        }
        if planned["errors"]:
            payload["status"] = "BLOCKED"
            write_report(args.report, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2
        if not args.apply:
            payload["status"] = "PASS"
            write_report(args.report, payload)
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0
        if not args.expected_db_sha or args.expected_db_sha != before_sha:
            raise RuntimeError("--expected-db-sha is required and must match the current database")
        if args.backup is None:
            raise RuntimeError("--backup is required for --apply")
        backup = args.backup.resolve()
        if backup.exists():
            raise RuntimeError(f"refusing to overwrite existing backup: {backup}")
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(db, backup)

        conn.execute("BEGIN")
        for item in MAPPINGS:
            conn.execute(
                "UPDATE domestic_candidates SET ingested_document_id=? WHERE candidate_id=?",
                (item["document_id"], item["candidate_id"]),
            )
            conn.execute(
                "UPDATE documents SET ingested_candidate_id=? WHERE id=?",
                (item["candidate_id"], item["document_id"]),
            )
        after_counts = counts(conn)
        if after_counts["integrity_check"] != "ok":
            conn.rollback()
            raise RuntimeError(f"integrity_check failed before commit: {after_counts}")
        if after_counts["foreign_key_violations"] != 0:
            conn.rollback()
            raise RuntimeError(f"foreign-key check failed before commit: {after_counts}")
        if after_counts["pages_without_fts"] != 0 or after_counts["fts_without_pages"] != 0:
            conn.rollback()
            raise RuntimeError(f"FTS alignment failed before commit: {after_counts}")
        conn.commit()
        after_sha = sha256_file(db)
        payload.update(
            {
                "status": "APPLIED",
                "after_sha256": after_sha,
                "after_counts": after_counts,
                "backup": str(backup),
                "updated_candidate_links": len(MAPPINGS),
                "updated_reverse_links": len(MAPPINGS),
                "citation_status_unchanged": True,
            }
        )
        write_report(args.report, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    raise SystemExit(main())
