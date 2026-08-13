#!/usr/bin/env python3
"""Apply a bounded PDF-provenance review for three Minxian contents pages.

The migration is metadata-only.  It binds existing OCR page rows to the real
issue PDF and PDF page number, then opens the strict citation gate only for
issue identity/date/contents-page claims.  It never edits page body text,
OCR files, source PDFs, or unrelated rows.  Dry-run is the default; --apply
requires an exact database SHA and a new backup path.
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
DEFAULT_BATCH = ROOT / "work/domestic/minxian_1944_contents_review_20260814/BATCH.json"
DEFAULT_DECISIONS = ROOT / "work/domestic/minxian_1944_contents_review_20260814/REVIEW_DECISIONS.json"
DEFAULT_REPORT = ROOT / "work/domestic/minxian_1944_contents_review_20260814/APPLY_REPORT.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_root_for(db_path: Path) -> Path:
    return db_path.resolve().parent.parent


def resolve_source(root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def strict_count(conn: sqlite3.Connection) -> int:
    return int(conn.execute(
        """SELECT count(*) FROM page_provenance
           WHERE citation_ready=1 AND needs_human_review=0
             AND review_status='human_verified'
             AND trim(COALESCE(human_review_note,''))<>''"""
    ).fetchone()[0])


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser()
    batch = load_json(args.batch.expanduser())
    decisions_payload = load_json(args.decisions.expanduser())
    expected_sha = str(batch.get("database", {}).get("sha256") or "").lower()
    actual_sha = sha256_file(db)
    if expected_sha != actual_sha:
        raise SystemExit(f"database SHA mismatch: expected {expected_sha}, got {actual_sha}")
    if batch.get("body_text_included") is not False or decisions_payload.get("body_text_included") is not False:
        raise SystemExit("body_text_included must be false")

    pages = {int(item["page_id"]): item for item in batch.get("pages", [])}
    decisions = decisions_payload.get("pages", [])
    if not pages or not isinstance(decisions, list) or len(decisions) != len(pages):
        raise SystemExit("batch and decisions must contain the same non-empty page set")

    forbidden = {"text", "page_text", "ocr_text", "body", "body_text", "original_text"}
    errors: list[str] = []
    accepted: list[tuple[dict, dict]] = []
    seen: set[int] = set()
    source_root = source_root_for(db)

    with sqlite3.connect(db) as conn:
        conn.row_factory = sqlite3.Row
        for decision in decisions:
            try:
                page_id = int(decision["page_id"])
            except (KeyError, TypeError, ValueError):
                errors.append("decision without integer page_id")
                continue
            if page_id in seen:
                errors.append(f"duplicate decision page_id={page_id}")
                continue
            seen.add(page_id)
            item = pages.get(page_id)
            if item is None:
                errors.append(f"page_id={page_id} is not in batch")
                continue
            if forbidden.intersection(decision):
                errors.append(f"page_id={page_id} decision contains body text")
            if str(decision.get("decision") or "") != "human_verified":
                errors.append(f"page_id={page_id} decision is not human_verified")
            reviewer = str(decision.get("reviewer") or "").strip()
            note = str(decision.get("note") or "").strip()
            if not reviewer or len(note) < 20:
                errors.append(f"page_id={page_id} requires reviewer and a 20+ character note")

            row = conn.execute(
                """SELECT p.id,p.document_id,p.page_label,p.page_url,p.text,
                          d.doc_key,d.title,d.date_guess,d.source_platform,
                          pp.source_file,pp.source_sha256,pp.review_status,
                          pp.citation_ready,pp.needs_human_review
                   FROM pages p JOIN documents d ON d.id=p.document_id
                   JOIN page_provenance pp ON pp.page_id=p.id
                   WHERE p.id=?""", (page_id,)
            ).fetchone()
            if row is None:
                errors.append(f"page_id={page_id} current provenance row missing")
                continue
            expected_current = item.get("current", {})
            checks = {
                "document_id": (int(row["document_id"]), int(item.get("document_id") or 0)),
                "doc_key": (str(row["doc_key"] or ""), str(item.get("doc_key") or "")),
                "page_label": (str(row["page_label"] or ""), str(item.get("page_label") or "")),
                "source_platform": (str(row["source_platform"] or ""), "domestic"),
                "current_page_url": (str(row["page_url"] or ""), str(expected_current.get("page_url") or "")),
                "current_source_file": (str(row["source_file"] or ""), str(expected_current.get("source_file") or "")),
                "current_source_sha256": (str(row["source_sha256"] or "").lower(), str(expected_current.get("source_sha256") or "").lower()),
                "current_review_status": (str(row["review_status"] or ""), str(expected_current.get("review_status") or "")),
                "current_citation_ready": (int(row["citation_ready"] or 0), int(expected_current.get("citation_ready") or 0)),
                "current_needs_human_review": (int(row["needs_human_review"] or 0), int(expected_current.get("needs_human_review") or 0)),
            }
            for name, (actual, expected) in checks.items():
                if actual != expected:
                    errors.append(f"page_id={page_id} {name} differs from batch")

            source_file = str(item.get("source_file") or "")
            source_path = resolve_source(source_root, source_file)
            expected_source_sha = str(item.get("source_sha256") or "").lower()
            actual_source_sha = sha256_file(source_path) if source_path.is_file() else ""
            if Path(source_file).is_absolute() or Path(source_file).suffix.lower() != ".pdf":
                errors.append(f"page_id={page_id} source must be a project-relative PDF")
            if not source_path.is_file() or actual_source_sha != expected_source_sha:
                errors.append(f"page_id={page_id} source PDF hash/file check failed")
            if source_path.is_file() and source_path.stat().st_size != int(item.get("source_file_size") or 0):
                errors.append(f"page_id={page_id} source PDF size differs from batch")
            if int(item.get("pdf_page_no") or 0) != 2 or int(item.get("physical_page_no") or 0) != 2:
                errors.append(f"page_id={page_id} expected PDF and physical page 2")
            if str(item.get("new_page_url") or "").find("#page=2") < 0:
                errors.append(f"page_id={page_id} new page URL lacks #page=2")
            accepted.append((item, decision))

        before_strict = strict_count(conn)
        if errors:
            report = {
                "mode": "apply" if args.apply else "dry_run",
                "database_sha_before": actual_sha,
                "database_sha_after": actual_sha,
                "decisions": len(decisions),
                "accepted_decisions": len(accepted),
                "validation_errors": errors,
                "strict_citation_count_before": before_strict,
                "strict_citation_count_after": before_strict,
                "body_text_included": False,
                "source_pdfs_modified": False,
            }
            args.report.expanduser().parent.mkdir(parents=True, exist_ok=True)
            args.report.expanduser().write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            raise SystemExit("validation failed:\n- " + "\n- ".join(errors))
        if args.apply and not args.backup:
            raise SystemExit("--backup is required with --apply")
        if args.apply and args.backup.exists():
            raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")
        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("BEGIN IMMEDIATE")
            try:
                for item, decision in accepted:
                    note = f"审核者：{decision['reviewer']}；{decision['note']}"
                    conn.execute(
                        """UPDATE pages SET page_url=? WHERE id=?""",
                        (item["new_page_url"], int(item["page_id"])),
                    )
                    conn.execute(
                        """UPDATE page_provenance
                           SET source_file=?, source_sha256=?, source_file_size=?,
                               pdf_page_no=?, physical_page_no=?, page_image_path=NULL,
                               page_image_sha256=NULL, citation_ready=1,
                               needs_human_review=0, review_status='human_verified',
                               human_review_note=?, period=?, year=?, event_tags=?,
                               source_title=?, updated_at=?
                         WHERE page_id=?""",
                        (
                            item["source_file"], item["source_sha256"], int(item["source_file_size"]),
                            int(item["pdf_page_no"]), int(item["physical_page_no"]), note,
                            item["period"], int(item["year"]), item["event_tags"], item["source_title"],
                            now, int(item["page_id"]),
                        ),
                    )
                integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
                if integrity != "ok" or foreign_keys:
                    raise RuntimeError(f"SQLite validation failed: {integrity}; foreign_keys={len(foreign_keys)}")
                conn.commit()
            except Exception:
                conn.rollback()
                raise
        after_strict = strict_count(conn)

    final_sha = sha256_file(db)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": actual_sha,
        "database_sha_after": final_sha,
        "batch_sha": expected_sha,
        "decisions": len(decisions),
        "accepted_decisions": len(accepted),
        "validation_errors": [],
        "strict_citation_count_before": before_strict,
        "strict_citation_count_after": after_strict,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "body_text_included": False,
        "source_pdfs_modified": False,
    }
    args.report.expanduser().parent.mkdir(parents=True, exist_ok=True)
    args.report.expanduser().write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
