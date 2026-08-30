#!/usr/bin/env python3
"""Reconcile a local discovery inventory with formal source paths by SHA256.

This is a hash-only utility. It reads inventory metadata, formal SQLite source
paths, and file bytes for hashing, but never parses document bodies, writes the
database, copies, moves, OCRs, or deletes files. Output reports contain safe
identifiers and aggregate counts only; local paths stay in the input inventory.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / "work/domestic/local_desktop_metadata_inventory_20260831/LOCAL_FILES_METADATA_ONLY.jsonl"
DEFAULT_DB = ROOT / "data/research_index.sqlite"
DEFAULT_OUTPUT = ROOT / "work/domestic/local_formal_hash_reconciliation_current"


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            rows.append(value)
    return rows


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_key(path: Path) -> tuple[str, int]:
    return path.name, path.stat().st_size


def formal_source_paths(db_path: Path) -> list[Path]:
    connection = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    try:
        rows = connection.execute(
            "SELECT local_path FROM sources WHERE local_path IS NOT NULL AND local_path != ?",
            ("",),
        ).fetchall()
    finally:
        connection.close()
    return [Path(str(row[0])).expanduser() for row in rows]


def reconcile(inventory_path: Path, db_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Return an aggregate report, safe per-file details, and unmatched queue."""

    local_rows = read_jsonl(inventory_path)
    raw_formal_paths = formal_source_paths(db_path)
    formal_files: list[Path] = []
    seen_formal: set[str] = set()
    for path in raw_formal_paths:
        try:
            resolved = path.resolve()
            if resolved.is_file() and str(resolved) not in seen_formal:
                seen_formal.add(str(resolved))
                formal_files.append(resolved)
        except OSError:
            continue

    hash_cache: dict[str, str] = {}
    formal_hash_to_paths: dict[str, list[Path]] = defaultdict(list)
    formal_hash_error_count = 0
    for path in formal_files:
        try:
            digest = sha256_file(path)
        except OSError:
            formal_hash_error_count += 1
            continue
        hash_cache[str(path)] = digest
        formal_hash_to_paths[digest].append(path)

    formal_by_key: dict[tuple[str, int], list[Path]] = defaultdict(list)
    for path in formal_files:
        try:
            formal_by_key[file_key(path)].append(path)
        except OSError:
            continue

    detail_rows: list[dict[str, Any]] = []
    unmatched_queue: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    local_hashed_file_count = 0
    local_hash_error_count = 0
    exact_path_count = 0
    exact_hash_count = 0
    candidate_pair_count = 0

    for row in local_rows:
        metadata_id = str(row.get("metadata_id") or row.get("local_path") or "")
        path = Path(str(row.get("local_path") or "")).expanduser()
        status = "LOCAL_FILE_UNAVAILABLE"
        digest: str | None = None
        formal_match_count = 0
        candidates: list[Path] = []
        try:
            resolved = path.resolve()
            if path.is_file():
                digest = hash_cache.get(str(resolved))
                if digest is None:
                    digest = sha256_file(resolved)
                    hash_cache[str(resolved)] = digest
                local_hashed_file_count += 1
                candidates = formal_by_key.get(file_key(resolved), [])
                candidate_pair_count += len(candidates)
                if str(resolved) in seen_formal:
                    status = "EXACT_FORMAL_SOURCE_PATH"
                    exact_path_count += 1
                    exact_hash_count += 1
                    formal_match_count = 1
                elif digest in formal_hash_to_paths:
                    status = "EXACT_FORMAL_SOURCE_HASH"
                    exact_hash_count += 1
                    formal_match_count = len(formal_hash_to_paths[digest])
                elif candidates:
                    status = "SAME_NAME_SIZE_DIFFERENT_HASH"
                else:
                    status = "NO_EXACT_FORMAL_SOURCE_MATCH"
            else:
                status = "LOCAL_FILE_UNAVAILABLE"
        except OSError:
            status = "LOCAL_HASH_UNAVAILABLE"
            local_hash_error_count += 1

        counts[status] += 1
        detail: dict[str, Any] = {"metadata_id": metadata_id, "status": status}
        if digest:
            detail["sha256"] = digest
        if formal_match_count:
            detail["formal_match_count"] = formal_match_count
        detail_rows.append(detail)

        if status not in {"EXACT_FORMAL_SOURCE_PATH", "EXACT_FORMAL_SOURCE_HASH"}:
            unmatched_queue.append(
                {
                    "metadata_id": row.get("metadata_id"),
                    "filename": row.get("filename"),
                    "bytes": row.get("bytes"),
                    "suffix": row.get("suffix"),
                    "filename_only_class": row.get("filename_only_class"),
                    "review_status": row.get("review_status"),
                    "status": status,
                    "body_read": False,
                }
            )

    unmatched_count = sum(
        counts[key]
        for key in ("NO_EXACT_FORMAL_SOURCE_MATCH", "SAME_NAME_SIZE_DIFFERENT_HASH", "LOCAL_FILE_UNAVAILABLE", "LOCAL_HASH_UNAVAILABLE")
    )
    report = {
        "schema": "local_formal_hash_reconciliation.v2",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "inventory_file_count": len(local_rows),
        "formal_source_path_count": len(raw_formal_paths),
        "formal_existing_file_count": len(formal_files),
        "formal_hashed_file_count": sum(len(paths) for paths in formal_hash_to_paths.values()),
        "formal_hash_error_count": formal_hash_error_count,
        "local_hashed_file_count": local_hashed_file_count,
        "local_hash_error_count": local_hash_error_count,
        "candidate_same_name_size_pair_count": candidate_pair_count,
        "exact_formal_source_path_count": exact_path_count,
        "exact_formal_source_hash_local_file_count": exact_hash_count,
        "same_name_size_different_hash_local_file_count": counts["SAME_NAME_SIZE_DIFFERENT_HASH"],
        "unmatched_local_file_count": unmatched_count,
        "unavailable_local_file_count": counts["LOCAL_FILE_UNAVAILABLE"],
        "status_counts": dict(sorted(counts.items())),
        "operation": "full_byte_hash_reconciliation_no_document_parsing",
        "body_read": False,
        "ocr_performed": False,
        "formal_db_written": False,
        "copied_or_moved": False,
        "deleted": False,
        "rule": "exact path or exact byte hash is file-identity evidence only; it does not establish provenance, rights, or historical value",
    }
    return report, detail_rows, unmatched_queue


def write_outputs(output: Path, report: dict[str, Any], details: list[dict[str, Any]], unmatched: list[dict[str, Any]]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "RECONCILIATION_METADATA_ONLY.jsonl").open("w", encoding="utf-8") as handle:
        for row in details:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    with (output / "UNMATCHED_LOCAL_QUEUE_METADATA_ONLY.jsonl").open("w", encoding="utf-8") as handle:
        for row in unmatched:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    report, details, unmatched = reconcile(
        args.inventory.expanduser().resolve(),
        args.db.expanduser().resolve(),
    )
    write_outputs(args.output.expanduser().resolve(), report, details, unmatched)
    print(json.dumps({
        "status": "PASS",
        "report": str(args.output.expanduser().resolve() / "REPORT.json"),
        "inventory_file_count": report["inventory_file_count"],
        "formal_existing_file_count": report["formal_existing_file_count"],
        "formal_hashed_file_count": report["formal_hashed_file_count"],
        "local_hashed_file_count": report["local_hashed_file_count"],
        "exact_formal_source_path_count": report["exact_formal_source_path_count"],
        "exact_formal_source_hash_local_file_count": report["exact_formal_source_hash_local_file_count"],
        "unmatched_local_file_count": report["unmatched_local_file_count"],
        "status_counts": report["status_counts"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
