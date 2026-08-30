#!/usr/bin/env python3
"""Compare SQLite recovery snapshots without reading document bodies.

The formal research database is large and contains page text, translations and
FTS indexes.  A file hash alone cannot tell whether two equal-sized snapshots
carry the same structured research state.  This tool compares a whitelist of
metadata tables and excludes body-like columns and full-text tables entirely.

It is a read-only audit: it never updates SQLite, creates a backup, deletes a
file, or emits row values.  The optional report is the only file it writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASE = ROOT / "data/research_index.sqlite"
DEFAULT_SNAPSHOTS = (
    ROOT / "work/domestic/backups/research_index.sqlite.before_mmhist_printed_subset_20260830.sqlite",
    ROOT / "work/domestic/backups/research_index_before_nlc_1949_journal_20260815.sqlite",
    ROOT / "work/domestic/backups/research_index_before_nlc_1949_page_identity_20260815.sqlite",
    ROOT / "work/domestic/backups/research_index_before_source_registry_nlc_1949_20260815.sqlite",
)

METADATA_TABLES = (
    "document_classifications",
    "documents",
    "domestic_candidates",
    "domestic_editorial_decisions",
    "domestic_sources",
    "drnh_images",
    "page_provenance",
    "pages",
    "research_events",
    "sources",
    "translations",
)

# These columns can contain document-like prose, notes or local body paths.
# Excluding them keeps this audit at the structural/metadata layer.
EXCLUDED_COLUMNS: dict[str, set[str]] = {
    "document_classifications": {"reason"},
    "documents": {"local_html", "local_txt"},
    "domestic_candidates": {"access_note", "evidence_note", "uncertainty_note", "review_note"},
    "domestic_editorial_decisions": {"rationale", "next_action"},
    "pages": {"text"},
    "page_provenance": {"machine_review_note", "human_review_note"},
    "research_events": {"event_summary", "actors", "tags", "places", "organizations"},
    "translations": {"text"},
}


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    return [str(row[1]) for row in connection.execute(f"PRAGMA table_info({quote_identifier(table)})")]


def jsonable(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"bytes_sha256": hashlib.sha256(value).hexdigest(), "bytes_length": len(value)}
    return value


def table_digest(connection: sqlite3.Connection, table: str) -> dict[str, Any]:
    columns = table_columns(connection, table)
    kept = [column for column in columns if column not in EXCLUDED_COLUMNS.get(table, set())]
    if not kept:
        return {"count": 0, "digest": None, "columns": []}
    projection = ", ".join(quote_identifier(column) for column in kept)
    rows = connection.execute(
        f"SELECT {projection} FROM {quote_identifier(table)}"
    ).fetchall()
    normalized = [json.dumps([jsonable(value) for value in row], ensure_ascii=False, separators=(",", ":")) for row in rows]
    normalized.sort()
    digest = hashlib.sha256("\n".join(normalized).encode("utf-8")).hexdigest()
    return {"count": len(rows), "digest": digest, "columns": kept}


def inspect_database(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(path)
    try:
        tables = {
            table: table_digest(connection, table)
            for table in METADATA_TABLES
            if connection.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)
            ).fetchone()
        }
        return {
            "path": str(path),
            "integrity_check": connection.execute("PRAGMA integrity_check").fetchone()[0],
            "user_version": connection.execute("PRAGMA user_version").fetchone()[0],
            "tables": tables,
        }
    finally:
        connection.close()


def compare(base: dict[str, Any], snapshot: dict[str, Any]) -> dict[str, Any]:
    base_tables = base["tables"]
    snapshot_tables = snapshot["tables"]
    all_tables = sorted(set(base_tables) | set(snapshot_tables))
    different = [
        table
        for table in all_tables
        if base_tables.get(table) != snapshot_tables.get(table)
    ]
    count_differences = {
        table: [
            (base_tables.get(table) or {}).get("count"),
            (snapshot_tables.get(table) or {}).get("count"),
        ]
        for table in all_tables
        if (base_tables.get(table) or {}).get("count")
        != (snapshot_tables.get(table) or {}).get("count")
    }
    return {
        "metadata_equal": not different,
        "different_tables": different,
        "count_differences": count_differences,
        "integrity_checks": {
            "base": base["integrity_check"],
            "snapshot": snapshot["integrity_check"],
        },
    }


def build_report(base_path: Path, snapshot_paths: list[Path]) -> dict[str, Any]:
    base = inspect_database(base_path)
    snapshots = [inspect_database(path) for path in snapshot_paths]
    return {
        "schema_version": "domestic_sqlite_snapshot_metadata_compare.v1",
        "scope": "whitelisted SQLite metadata tables; body-like columns and FTS tables excluded",
        "body_like_columns_excluded": {
            table: sorted(columns) for table, columns in EXCLUDED_COLUMNS.items()
        },
        "base": base,
        "snapshots": snapshots,
        "comparisons": {
            snapshot["path"]: compare(base, snapshot) for snapshot in snapshots
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--snapshot", type=Path, action="append", dest="snapshots")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true", help="only write --output; do not print the full report")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    snapshot_paths = args.snapshots or list(DEFAULT_SNAPSHOTS)
    paths = [args.base, *snapshot_paths]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit("missing SQLite file(s): " + ", ".join(missing))
    report = build_report(args.base, snapshot_paths)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    if not args.quiet:
        print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
