#!/usr/bin/env python3
"""Verify an external research_index.sqlite against its committed manifest."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = ROOT / "data" / "research_index.manifest.json"
STRICT_CITATION_SQL = """
    citation_ready = 1
    AND needs_human_review = 0
    AND review_status = 'human_verified'
    AND trim(COALESCE(human_review_note, '')) <> ''
"""


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar(conn: sqlite3.Connection, sql: str) -> int | str:
    return conn.execute(sql).fetchone()[0]


def audit_source_files(conn: sqlite3.Connection, project_root: Path) -> dict[str, int]:
    rows = conn.execute(
        """SELECT pp.source_file,
                  group_concat(DISTINCT lower(pp.source_sha256)) AS expected_sha256
           FROM page_provenance pp
           JOIN documents d ON d.id=pp.document_id
           WHERE d.source_platform='domestic'
           GROUP BY pp.source_file"""
    ).fetchall()
    project_root = project_root.resolve()
    missing = mismatched = absolute = outside = total_bytes = 0
    for row in rows:
        raw = str(row["source_file"] or "").strip()
        path = Path(raw).expanduser()
        if path.is_absolute():
            absolute += 1
        else:
            path = project_root / path
        path = path.resolve()
        try:
            path.relative_to(project_root)
        except ValueError:
            outside += 1
            continue
        if not path.is_file():
            missing += 1
            continue
        actual_hash = sha256(path)
        expected = set(str(row["expected_sha256"] or "").split(","))
        mismatched += int(actual_hash not in expected)
        total_bytes += path.stat().st_size
    return {
        "source_files_checked": len(rows),
        "source_file_bytes": total_bytes,
        "source_files_missing": missing,
        "source_hash_mismatches": mismatched,
        "absolute_source_paths": absolute,
        "source_files_outside_project": outside,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--db", type=Path)
    args = parser.parse_args()

    manifest_path = args.manifest.expanduser().resolve()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    configured_db = args.db or Path(
        os.environ.get(
            "MINGMENG_RESEARCH_DB",
            str(ROOT / "data" / manifest["database_filename"]),
        )
    )
    db = configured_db.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")

    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    actual = {
        "database_size_bytes": db.stat().st_size,
        "sha256": sha256(db),
        "documents": scalar(conn, "SELECT COUNT(*) FROM documents"),
        "domestic_documents": scalar(
            conn, "SELECT COUNT(*) FROM documents WHERE source_platform='domestic'"
        ),
        "pages": scalar(conn, "SELECT COUNT(*) FROM pages"),
        "page_fts": scalar(conn, "SELECT COUNT(*) FROM page_fts"),
        "domestic_candidates": scalar(conn, "SELECT COUNT(*) FROM domestic_candidates"),
        "domestic_file_backed_provenance": scalar(
            conn,
            """SELECT COUNT(*) FROM page_provenance pp
               JOIN documents d ON d.id=pp.document_id
               WHERE d.source_platform='domestic'
                 AND trim(COALESCE(pp.source_file,''))<>''
                 AND length(trim(COALESCE(pp.source_sha256,'')))=64""",
        ),
        "strict_human_citation_pages": scalar(
            conn, f"SELECT COUNT(*) FROM page_provenance WHERE {STRICT_CITATION_SQL}"
        ),
        "domestic_pages_missing_provenance": scalar(
            conn,
            """SELECT COUNT(*) FROM pages p
               JOIN documents d ON d.id=p.document_id
               LEFT JOIN page_provenance pp ON pp.page_id=p.id
               WHERE d.source_platform='domestic' AND pp.page_id IS NULL""",
        ),
        "domestic_documents_missing_date": scalar(
            conn,
            """SELECT COUNT(*) FROM documents
               WHERE source_platform='domestic'
                 AND (date_guess IS NULL OR trim(date_guess)='')""",
        ),
        "integrity_check": scalar(conn, "PRAGMA integrity_check"),
        "foreign_key_violations": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
        "pages_without_fts": scalar(
            conn,
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL",
        ),
        "fts_without_pages": scalar(
            conn,
            "SELECT COUNT(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL",
        ),
    }
    actual.update(audit_source_files(conn, db.parent.parent))
    conn.close()

    expected = {
        "database_size_bytes": manifest["database_size_bytes"],
        "sha256": manifest["sha256"],
        **manifest["counts"],
        **manifest["checks"],
    }
    mismatches = {
        key: {"expected": expected[key], "actual": actual.get(key)}
        for key in expected
        if actual.get(key) != expected[key]
    }
    result = {"ok": not mismatches, "mismatches": mismatches, "actual": actual}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if mismatches:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
