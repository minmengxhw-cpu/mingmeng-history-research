#!/usr/bin/env python3
"""Apply provenance-gated document metadata corrections with a DB backup."""

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


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def read_rows(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--batch-id", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    rows = [row for row in read_rows(args.manifest) if row.get("approved")]
    result: dict[str, Any] = {
        "batch_id": args.batch_id,
        "mode": "apply" if args.apply else "dry_run",
        "rows": len(rows),
        "validated": 0,
        "applied": 0,
        "skipped": [],
        "backup": None,
    }
    with sqlite3.connect(args.db) as connection:
        validated: list[tuple[dict[str, Any], int]] = []
        for row in rows:
            source = resolve(row["source_path"])
            if not source.is_file() or sha256(source) != row["source_sha256"]:
                result["skipped"].append(
                    {"doc_key": row["doc_key"], "reason": "source_sha256_gate"}
                )
                continue
            document = connection.execute(
                "SELECT id,title FROM documents WHERE doc_key=?",
                (row["doc_key"],),
            ).fetchone()
            if document is None:
                result["skipped"].append(
                    {"doc_key": row["doc_key"], "reason": "document_missing"}
                )
                continue
            if document[1] != row["expected_old_title"]:
                result["skipped"].append(
                    {
                        "doc_key": row["doc_key"],
                        "reason": "unexpected_current_title",
                        "current": document[1],
                    }
                )
                continue
            validated.append((row, document[0]))
        result["validated"] = len(validated)

        if args.apply and validated:
            backup = args.db.with_name(
                f"{args.db.name}.{args.batch_id}."
                f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.pre.bak"
            )
            shutil.copy2(args.db, backup)
            result["backup"] = str(backup)
            for row, document_id in validated:
                connection.execute(
                    """
                    UPDATE documents
                    SET title=?,date_guess=?,volume_title=?,matched_terms=?
                    WHERE id=?
                    """,
                    (
                        row["new_title"],
                        row["new_date_guess"],
                        row["new_volume_title"],
                        row["new_matched_terms"],
                        document_id,
                    ),
                )
                connection.execute(
                    """
                    UPDATE page_fts
                    SET title=?,matched_terms=?
                    WHERE rowid IN (
                        SELECT id FROM pages WHERE document_id=?
                    )
                    """,
                    (
                        row["new_title"],
                        row["new_matched_terms"],
                        document_id,
                    ),
                )
                result["applied"] += 1
            connection.commit()

        result["integrity_check"] = connection.execute(
            "PRAGMA integrity_check"
        ).fetchone()[0]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not result["skipped"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
