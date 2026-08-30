#!/usr/bin/env python3
"""Audit domestic research storage without changing or reading source bodies.

The audit is intentionally conservative.  It records file counts, byte sizes,
top-level work-artifact classes, and (when requested) SHA256/integrity metadata
for SQLite checkpoints.  It does not delete, move, rename, OCR, parse source
body text, or update the formal research database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[2]
CANONICAL_MOUNTED_FILES = (Path("research_index.sqlite"),)


def iter_files(root: Path) -> Iterable[tuple[Path, int]]:
    """Yield regular files without following symlinked files."""
    if not root.exists():
        return
    for path in root.rglob("*"):
        if path.is_symlink() or not path.is_file():
            continue
        try:
            yield path, path.stat().st_size
        except OSError:
            continue


def classify_work_file(relative: Path) -> str:
    text = str(relative).lower()
    if relative.parts and relative.parts[0] == "backups":
        return "recoverable_backup"
    if any(
        marker in text
        for marker in ("ocr", "render", "visual_review", "fragment", "smoke")
    ):
        return "derived_ocr_or_render"
    if any(
        marker in text
        for marker in (
            "gate",
            "validation",
            "audit",
            "parity",
            "reconciliation",
            "manifest",
            "report",
            "status",
        )
    ):
        return "audit_or_manifest"
    return "other_work_artifact"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sqlite_snapshot(path: Path, include_hash: bool) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path),
        "size_bytes": path.stat().st_size,
        "sha256": sha256(path) if include_hash else None,
    }
    try:
        with sqlite3.connect(path) as connection:
            record["integrity_check"] = connection.execute(
                "PRAGMA integrity_check"
            ).fetchone()[0]
            tables = {
                row[0]
                for row in connection.execute(
                    "SELECT name FROM sqlite_master "
                    "WHERE type='table' AND name NOT LIKE 'sqlite_%'"
                )
            }
            record["table_count"] = len(tables)
            selected = {}
            for table in (
                "documents",
                "pages",
                "page_fts",
                "research_events",
                "domestic_candidates",
            ):
                if table in tables:
                    selected[table] = connection.execute(
                        f'SELECT count(*) FROM "{table}"'
                    ).fetchone()[0]
            record["selected_row_counts"] = selected
    except (OSError, sqlite3.Error) as exc:
        record["integrity_check"] = f"ERROR: {exc}"
        record["table_count"] = None
        record["selected_row_counts"] = {}
    return record


def mounted_symlink_file(root: Path, relative: Path) -> dict[str, Any] | None:
    """Describe one known mounted file without following arbitrary symlinks."""
    path = root / relative
    if not path.is_symlink():
        return None
    try:
        target = path.resolve(strict=True)
        if not target.is_file():
            return None
        return {
            "path": str(path),
            "target": str(target),
            "size_bytes": target.stat().st_size,
        }
    except OSError:
        return None


def audit(repo: Path, include_hash: bool) -> dict[str, Any]:
    data_root = repo / "data"
    work_root = repo / "work" / "domestic"
    roots = {"data": data_root, "work_domestic": work_root}
    root_summary: dict[str, dict[str, Any]] = {}
    work_categories: Counter[str] = Counter()
    work_top_dirs: defaultdict[str, list[int]] = defaultdict(lambda: [0, 0])
    extension_bytes: Counter[str] = Counter()
    extension_counts: Counter[str] = Counter()
    mounted_symlink_files: list[dict[str, Any]] = []

    for name, root in roots.items():
        count = 0
        total = 0
        for path, size in iter_files(root):
            count += 1
            total += size
            suffix = path.suffix.lower() or "[no_ext]"
            extension_bytes[suffix] += size
            extension_counts[suffix] += 1
            if name == "work_domestic":
                relative = path.relative_to(root)
                work_categories[classify_work_file(relative)] += size
                first = relative.parts[0] if relative.parts else "."
                work_top_dirs[first][0] += 1
                work_top_dirs[first][1] += size
        if name == "data":
            for relative in CANONICAL_MOUNTED_FILES:
                mounted = mounted_symlink_file(root, relative)
                if not mounted:
                    continue
                target = Path(mounted["target"])
                try:
                    target.relative_to(root.resolve())
                except ValueError:
                    # The mounted target lives outside this checkout, so the
                    # regular-file walk above cannot have counted it.
                    count += 1
                    total += mounted["size_bytes"]
                    suffix = relative.suffix.lower() or "[no_ext]"
                    extension_bytes[suffix] += mounted["size_bytes"]
                    extension_counts[suffix] += 1
                    mounted_symlink_files.append(mounted)
        root_summary[name] = {"file_count": count, "bytes": total}

    sqlite_files: list[dict[str, Any]] = []
    for root in (data_root, work_root):
        # File-size totals intentionally skip symlinks, but the formal database
        # is commonly mounted as a symlink from the data checkout. Keep that
        # user-facing entry in the SQLite integrity/hash inventory so the
        # report cannot hide the active database behind its resolved target.
        for path in root.rglob("*.sqlite"):
            if path.is_symlink() or path.is_file():
                sqlite_files.append(sqlite_snapshot(path, include_hash))

    return {
        "schema": "domestic_storage_layers_audit.v2",
        "repo": str(repo),
        "body_text_read": False,
        "formal_db_written": False,
        "auto_delete": False,
        "roots": root_summary,
        "mounted_symlink_files": mounted_symlink_files,
        "work_domestic_categories_bytes": dict(work_categories.most_common()),
        "work_domestic_top_directories": [
            {"directory": key, "file_count": value[0], "bytes": value[1]}
            for key, value in sorted(
                work_top_dirs.items(), key=lambda item: item[1][1], reverse=True
            )[:30]
        ],
        "extension_summary": [
            {
                "extension": key,
                "file_count": extension_counts[key],
                "bytes": extension_bytes[key],
            }
            for key in sorted(extension_bytes, key=extension_bytes.get, reverse=True)
        ],
        "sqlite_files": sorted(sqlite_files, key=lambda item: item["path"]),
        "disposition_policy": {
            "canonical_data": "KEEP",
            "derived_layers": "KEEP_UNTIL_REBUILD_AND_MANIFEST_CHECK",
            "recoverable_backups": "REVIEW_ONLY_NO_AUTO_DELETE",
            "unknown_work_artifacts": "REVIEW_ONLY_NO_AUTO_DELETE",
        },
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Domestic storage layers audit",
        "",
        "Metadata-only audit; no source body was read and no file was changed.",
        "The canonical database symlink is counted in the data root when its target is outside this checkout.",
        "",
        "## Roots",
        "",
        "| Root | Files | Bytes |",
        "|---|---:|---:|",
    ]
    for name, summary in report["roots"].items():
        lines.append(f"| {name} | {summary['file_count']} | {summary['bytes']} |")
    lines.extend(["", "## Work-artifact classes", "", "| Class | Bytes |", "|---|---:|"])
    for name, size in report["work_domestic_categories_bytes"].items():
        lines.append(f"| {name} | {size} |")
    lines.extend(["", "## SQLite checkpoints", "", "| Path | Bytes | SHA256 | Integrity |", "|---|---:|---|---|"])
    for item in report["sqlite_files"]:
        lines.append(
            f"| `{item['path']}` | {item['size_bytes']} | "
            f"{item.get('sha256') or 'not_requested'} | {item.get('integrity_check')} |"
        )
    lines.extend(
        [
            "",
            "## Disposition",
            "",
            "- `KEEP`: canonical data and formal indexes.",
            "- `KEEP_UNTIL_REBUILD_AND_MANIFEST_CHECK`: OCR, render and derived layers.",
            "- `REVIEW_ONLY_NO_AUTO_DELETE`: backups and unknown work artifacts.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--hash-sqlite", action="store_true")
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    args = parser.parse_args()
    report = audit(args.repo.resolve(), args.hash_sqlite)
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output_json:
        args.output_json.parent.mkdir(parents=True, exist_ok=True)
        args.output_json.write_text(payload, encoding="utf-8")
    if args.output_md:
        args.output_md.parent.mkdir(parents=True, exist_ok=True)
        args.output_md.write_text(markdown(report), encoding="utf-8")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
