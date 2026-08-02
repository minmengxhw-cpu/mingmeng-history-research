#!/usr/bin/env python3
"""Import reviewed domestic public-web text with provenance and rollback.

The importer accepts only records marked formal_import=true in the extraction
manifest.  All records remain non-citation-ready reference/search material.
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


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def resolve(path: str) -> Path:
    candidate = Path(path).expanduser()
    return candidate if candidate.is_absolute() else ROOT / candidate


def prepare(
    extract_manifest: Path, download_manifest: Path
) -> list[dict[str, Any]]:
    downloads = {
        row["download_id"]: row
        for row in read_jsonl(download_manifest)
        if row.get("download_id")
    }
    prepared: list[dict[str, Any]] = []
    for row in read_jsonl(extract_manifest):
        if not row.get("formal_import"):
            continue
        download_id = row["download_id"]
        download = downloads.get(download_id)
        if not download:
            raise ValueError(f"{download_id}: missing download provenance")
        raw_path = resolve(row["raw_path"])
        text_path = resolve(row["extracted_text_path"])
        if not raw_path.is_file() or sha256(raw_path) != row["raw_sha256"]:
            raise ValueError(f"{download_id}: raw SHA256 gate failed")
        if (
            not text_path.is_file()
            or sha256(text_path) != row["extracted_text_sha256"]
        ):
            raise ValueError(f"{download_id}: extracted text SHA256 gate failed")
        text = text_path.read_text(encoding="utf-8").strip()
        if len(text) < 200:
            raise ValueError(f"{download_id}: extracted text too short")
        prepared.append(
            {
                **row,
                "_raw_path": raw_path,
                "_text_path": text_path,
                "_text": text,
                "_source_url": download.get("source_url") or "",
            }
        )
    if not prepared:
        raise ValueError("no formal_import records")
    return prepared


def counts(connection: sqlite3.Connection) -> dict[str, int]:
    return {
        table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        for table in ("sources", "documents", "pages", "page_fts")
    }


def apply(rows: list[dict[str, Any]], db: Path, batch_id: str) -> dict[str, Any]:
    backup = db.with_name(f"{db.name}.{batch_id}.pre.bak")
    if backup.exists():
        raise ValueError(f"backup already exists: {backup}")
    shutil.copy2(db, backup)

    with sqlite3.connect(db) as connection:
        connection.execute("PRAGMA foreign_keys=ON")
        before = counts(connection)
        inserted = 0
        updated = 0
        for row in rows:
            source_key = f"domestic-web:{row['download_id']}"
            source = connection.execute(
                "SELECT id FROM sources WHERE source_id=?", (source_key,)
            ).fetchone()
            if source:
                source_id = source[0]
                connection.execute(
                    "UPDATE sources SET title=?,origin_url=?,local_path=? WHERE id=?",
                    (
                        row["title"],
                        row["_source_url"],
                        str(row["_raw_path"]),
                        source_id,
                    ),
                )
            else:
                source_id = connection.execute(
                    """
                    INSERT INTO sources(
                        source_type,source_id,title,origin_url,local_path
                    ) VALUES(?,?,?,?,?)
                    """,
                    (
                        "domestic_public_web",
                        source_key,
                        row["title"],
                        row["_source_url"],
                        str(row["_raw_path"]),
                    ),
                ).lastrowid

            doc_key = f"domestic-web/{row['download_id']}"
            document = connection.execute(
                "SELECT id FROM documents WHERE doc_key=?", (doc_key,)
            ).fetchone()
            tags = ",".join(
                [
                    "国内盟史",
                    "公开网页",
                    f"evidence_level={row['evidence_level']}",
                    f"source_kind={row['source_kind']}",
                    "citation_ready=false",
                    "needs_human_review=true",
                ]
            )
            if document:
                document_id = document[0]
                page = connection.execute(
                    "SELECT id FROM pages WHERE document_id=? AND page_label='full-text'",
                    (document_id,),
                ).fetchone()
                connection.execute(
                    """
                    UPDATE documents
                    SET title=?,date_guess=?,url=?,local_html=?,local_txt=?,
                        hit_type=?,matched_terms=?,source_platform='domestic'
                    WHERE id=?
                    """,
                    (
                        row["title"],
                        row["date"],
                        row["_source_url"],
                        str(row["_raw_path"]),
                        str(row["_text_path"]),
                        "domestic_public_web",
                        tags,
                        document_id,
                    ),
                )
                if page:
                    page_id = page[0]
                    connection.execute(
                        "UPDATE pages SET page_url=?,text=? WHERE id=?",
                        (row["_source_url"], row["_text"], page_id),
                    )
                    connection.execute(
                        "DELETE FROM page_fts WHERE rowid=?", (page_id,)
                    )
                else:
                    page_id = connection.execute(
                        """
                        INSERT INTO pages(document_id,page_label,page_url,text)
                        VALUES(?,?,?,?)
                        """,
                        (
                            document_id,
                            "full-text",
                            row["_source_url"],
                            row["_text"],
                        ),
                    ).lastrowid
                updated += 1
            else:
                document_id = connection.execute(
                    """
                    INSERT INTO documents(
                        source_id,doc_key,volume_id,volume_title,doc_id,title,
                        date_guess,url,local_html,local_txt,hit_type,
                        matched_terms,source_platform
                    ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
                    """,
                    (
                        source_id,
                        doc_key,
                        "MMHIST-WEB",
                        "国内公开网页资料",
                        row["download_id"],
                        row["title"],
                        row["date"],
                        row["_source_url"],
                        str(row["_raw_path"]),
                        str(row["_text_path"]),
                        "domestic_public_web",
                        tags,
                        "domestic",
                    ),
                ).lastrowid
                page_id = connection.execute(
                    """
                    INSERT INTO pages(document_id,page_label,page_url,text)
                    VALUES(?,?,?,?)
                    """,
                    (
                        document_id,
                        "full-text",
                        row["_source_url"],
                        row["_text"],
                    ),
                ).lastrowid
                inserted += 1
            connection.execute(
                """
                INSERT INTO page_fts(
                    rowid,volume_id,doc_id,title,page_label,matched_terms,text
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    page_id,
                    "MMHIST-WEB",
                    row["download_id"],
                    row["title"],
                    "full-text",
                    tags,
                    row["_text"],
                ),
            )
        connection.commit()
        after = counts(connection)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
        fts_orphans = connection.execute(
            """
            SELECT COUNT(*) FROM page_fts
            WHERE rowid NOT IN (SELECT id FROM pages)
            """
        ).fetchone()[0]
        pages_missing_fts = connection.execute(
            """
            SELECT COUNT(*) FROM pages
            WHERE id NOT IN (SELECT rowid FROM page_fts)
            """
        ).fetchone()[0]
    return {
        "backup": str(backup),
        "before": before,
        "after": after,
        "inserted_documents": inserted,
        "updated_documents": updated,
        "integrity_check": integrity,
        "fts_orphans": fts_orphans,
        "pages_missing_fts": pages_missing_fts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract-manifest", type=Path, required=True)
    parser.add_argument("--download-manifest", type=Path, required=True)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = prepare(args.extract_manifest, args.download_manifest)
    result: dict[str, Any] = {
        "batch_id": args.batch_id,
        "mode": "apply" if args.apply else "dry_run",
        "gate": "PASS",
        "records": len(rows),
        "record_ids": [row["download_id"] for row in rows],
        "citation_ready": 0,
    }
    if args.apply:
        result.update(apply(rows, args.db, args.batch_id))
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
