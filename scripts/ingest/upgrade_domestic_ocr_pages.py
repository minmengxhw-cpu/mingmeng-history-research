#!/usr/bin/env python3
"""Upgrade existing domestic OCR pages in-place, preserving document groups."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


CONF_RE = re.compile(r"平均置信度：`?([0-9.]+)")
ROOT = Path(__file__).resolve().parents[2]


def markdown_confidence(text: str) -> float | None:
    match = CONF_RE.search(text)
    return float(match.group(1)) if match else None


def resolve(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_provenance(row: dict) -> str | None:
    checks = [
        ("original_source", "original_source_sha256"),
        ("derived_image", "derived_image_sha256"),
        ("ocr_markdown", "ocr_markdown_sha256"),
    ]
    for path_field, sha_field in checks:
        if not row.get(path_field) and not row.get(sha_field):
            continue
        path = resolve(str(row.get(path_field, "")))
        expected = str(row.get(sha_field, "")).lower()
        if not path.is_file():
            return f"missing_{path_field}"
        if len(expected) != 64 or sha256(path) != expected:
            return f"sha256_mismatch_{path_field}"
    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    db = Path(args.db)
    rows = [json.loads(line) for line in Path(args.manifest).read_text(encoding="utf-8").splitlines() if line.strip()]
    approved = [row for row in rows if row.get("approved_for_upgrade")]
    report = {"db": str(db), "manifest": str(args.manifest), "dry_run": not args.apply, "rows": len(rows), "approved": len(approved), "applied": 0, "skipped": [], "backup": None}
    backup = None
    if args.apply:
        backup = db.with_name(db.name + "." + datetime.now().strftime("%Y%m%d_%H%M%S") + ".pre_ocr_upgrade.bak")
        shutil.copy2(db, backup)
        report["backup"] = str(backup)
    connection = sqlite3.connect(db)
    connection.row_factory = sqlite3.Row
    try:
        for row in approved:
            provenance_error = validate_provenance(row)
            if provenance_error:
                report["skipped"].append({"row": row, "reason": provenance_error})
                continue
            text_path = resolve(row["ocr_markdown"])
            if not text_path.is_file():
                report["skipped"].append({"row": row, "reason": "missing_markdown"})
                continue
            document = connection.execute(
                "select id, title, volume_id, doc_id, matched_terms from documents where doc_key=?",
                (row.get("doc_key") or f"domestic-ocr/{row['record_id']}",),
            ).fetchone()
            if document is None:
                report["skipped"].append({"row": row, "reason": "missing_document"})
                continue
            text = text_path.read_text(encoding="utf-8")
            page = connection.execute(
                "select id, page_url, text from pages where document_id=? and page_label=?",
                (document["id"], row["page_label"]),
            ).fetchone()
            if page is None:
                report["skipped"].append({"row": row, "reason": "missing_page"})
                continue
            if not args.apply:
                report["applied"] += 1
                continue
            connection.execute("update pages set text=? where id=?", (text, page["id"]))
            connection.execute("delete from page_fts where rowid=?", (page["id"],))
            tags = [document["matched_terms"] or "", f"ocr_variant={row.get('variant') or 'rotated_enhanced'}"]
            if row.get("new_mean_confidence") not in (None, ""):
                tags.append(f"ocr_mean_confidence={row['new_mean_confidence']}")
            tags.extend(["ocr_page_status=needs_human_review", "ocr_status=pilot", "source_kind=public_scan"])
            connection.execute(
                "insert into page_fts(rowid, volume_id, doc_id, title, page_label, matched_terms, text) values(?,?,?,?,?,?,?)",
                (page["id"], document["volume_id"], document["doc_id"], document["title"], row["page_label"],
                 ",".join(tags), text),
            )
            report["applied"] += 1
        if args.apply:
            connection.commit()
    finally:
        connection.close()
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
