#!/usr/bin/env python3
"""Import a metadata-only academic patch into the private staging database.

The patch is deliberately separate from the formal SQLite database and never
copies source bodies.  Dry-run is the default; applying requires --apply and
an explicit --backup path.  Existing external IDs are rejected so this tool
cannot silently overwrite a prior bibliographic decision.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATCH = ROOT / "data/domestic/academic_metadata_additions_20260813.json"
DEFAULT_DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"


def load_patch(path: Path) -> tuple[dict, list[dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("body_read") is not False:
        raise ValueError("metadata patch must declare body_read=false")
    records = payload.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("metadata patch has no records")
    ids = [str(row.get("external_id") or "") for row in records]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError("patch external_id values must be non-empty and unique")
    for row in records:
        required = {"external_id", "layer", "title", "author", "publication_date",
                    "research_type", "quality_tier", "source_url", "fulltext_status",
                    "review_status", "metadata"}
        missing = sorted(required - set(row))
        if missing:
            raise ValueError(f"{row.get('external_id')}: missing {missing}")
        if row["layer"] != "SCHOLARLY_RESEARCH":
            raise ValueError(f"{row['external_id']}: patch is not scholarly research")
        if row["fulltext_status"] != "METADATA_ONLY":
            raise ValueError(f"{row['external_id']}: metadata patch cannot claim full text")
        if int(row.get("citation_ready", 0)) or int(row.get("human_verified", 0)):
            raise ValueError(f"{row['external_id']}: metadata patch cannot set citation gates")
    return payload, records


def open_db(path: Path, readonly: bool) -> sqlite3.Connection:
    if readonly:
        return sqlite3.connect(f"file:{path.resolve()}?mode=ro", uri=True)
    return sqlite3.connect(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--patch", type=Path, default=DEFAULT_PATCH)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    args = parser.parse_args()

    payload, records = load_patch(args.patch)
    if not args.db.is_file():
        result = {"status": "BLOCKED", "reason": "staging database missing", "db_path": str(args.db)}
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    with open_db(args.db, readonly=True) as conn:
        table = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domestic_research_materials'"
        ).fetchone()
        if not table:
            raise RuntimeError("domestic_research_materials table missing")
        ids = [row[0] for row in conn.execute(
            "SELECT external_id FROM domestic_research_materials WHERE external_id IN (%s)"
            % ",".join("?" for _ in records),
            [row["external_id"] for row in records],
        )]
        before = conn.execute("SELECT count(*) FROM domestic_research_materials").fetchone()[0]
        integrity_before = conn.execute("PRAGMA integrity_check").fetchone()[0]

    if ids:
        raise RuntimeError(f"refusing to overwrite existing external IDs: {ids}")
    if args.apply and not args.backup:
        raise RuntimeError("--apply requires an explicit --backup path")

    if args.apply:
        args.backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(args.db, args.backup)
        conn = open_db(args.db, readonly=False)
        try:
            conn.execute("BEGIN IMMEDIATE")
            for row in records:
                conn.execute(
                    """INSERT INTO domestic_research_materials
                    (external_id,layer,title,author,institution,publication_date,
                     research_type,quality_tier,source_url,local_path,sha256,
                     fulltext_status,review_status,citation_ready,human_verified,
                     metadata_json,acceptance_summary_json)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        row["external_id"], row["layer"], row["title"], row.get("author"),
                        row.get("institution"), row.get("publication_date"), row.get("research_type"),
                        row.get("quality_tier"), row.get("source_url"), row.get("local_path"),
                        row.get("sha256"), row["fulltext_status"], row["review_status"],
                        0, 0, json.dumps(row["metadata"], ensure_ascii=False),
                        json.dumps({"manifest": payload.get("manifest"), "body_read": False}, ensure_ascii=False),
                    ),
                )
            conn.execute("INSERT INTO domestic_research_materials_fts(domestic_research_materials_fts) VALUES('rebuild')")
            conn.execute("INSERT INTO domestic_research_materials_fts_trigram(domestic_research_materials_fts_trigram) VALUES('rebuild')")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    with open_db(args.db, readonly=True) as conn:
        after = conn.execute("SELECT count(*) FROM domestic_research_materials").fetchone()[0]
        inserted = conn.execute(
            "SELECT count(*) FROM domestic_research_materials WHERE external_id IN (%s)"
            % ",".join("?" for _ in records),
            [row["external_id"] for row in records],
        ).fetchone()[0]
        integrity_after = conn.execute("PRAGMA integrity_check").fetchone()[0]

    result = {
        "manifest": payload.get("manifest"),
        "status": "APPLIED" if args.apply else "DRY_RUN",
        "body_read": False,
        "formal_db_written": False,
        "source_bodies_copied": False,
        "db_path": str(args.db),
        "backup_path": str(args.backup) if args.apply and args.backup else None,
        "input_records": len(records),
        "inserted_records": inserted if args.apply else 0,
        "would_insert_records": len(records),
        "records_before": before,
        "records_after": after,
        "integrity_before": integrity_before,
        "integrity_after": integrity_after,
        "external_ids": [row["external_id"] for row in records],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
