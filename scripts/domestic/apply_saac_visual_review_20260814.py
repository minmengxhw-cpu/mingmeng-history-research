#!/usr/bin/env python3
"""Apply a bounded visual-review decision batch for SAAC image pages.

The batch is metadata-only: it contains no OCR or page body.  Dry-run is the
default.  ``--apply`` requires an exact database SHA and a new backup path,
checks the source-image SHA and page provenance for every decision, then only
changes the formal citation gate and the explicitly corrected date/topic
metadata.  It never deletes or rewrites source images.
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
DEFAULT_BATCH = ROOT / "work" / "domestic" / "saac_1949_pcc_review_20260814" / "BATCH.json"
DEFAULT_DECISIONS = ROOT / "work" / "domestic" / "saac_1949_pcc_review_20260814" / "REVIEW_DECISIONS.json"
DEFAULT_REPORT = ROOT / "work" / "domestic" / "saac_1949_pcc_review_20260814" / "APPLY_REPORT.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_root_for(db_path: Path) -> Path:
    # The formal checkout intentionally uses a symlink to the user's original
    # data tree.  Resolve it before resolving relative provenance paths.
    return db_path.resolve().parent.parent


def resolve_source(root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def load_decisions(path: Path) -> list[dict[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("pages"), list):
        return payload["pages"]
    raise ValueError("decision file must be a list or an object with pages")


def strict_count(connection: sqlite3.Connection) -> int:
    return int(
        connection.execute(
            """
            SELECT count(*) FROM page_provenance
            WHERE citation_ready=1 AND needs_human_review=0
              AND review_status='human_verified'
              AND trim(COALESCE(human_review_note,''))<>''
            """
        ).fetchone()[0]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    db = args.db.expanduser()
    batch_path = args.batch.expanduser()
    decisions_path = args.decisions.expanduser()
    report_path = args.report.expanduser()
    batch = json.loads(batch_path.read_text(encoding="utf-8"))
    expected_db_sha = str(batch.get("database", {}).get("sha256") or "").lower()
    actual_db_sha = sha256_file(db)
    if expected_db_sha != actual_db_sha:
        raise SystemExit(f"database SHA mismatch: expected {expected_db_sha}, got {actual_db_sha}")

    batch_pages = {int(item["page_id"]): item for item in batch.get("pages", [])}
    decisions = load_decisions(decisions_path)
    errors: list[str] = []
    accepted: list[dict[str, object]] = []
    seen: set[int] = set()
    source_root = source_root_for(db)
    forbidden_body_keys = {"text", "page_text", "ocr_text", "body", "body_text"}

    with sqlite3.connect(db) as connection:
        connection.row_factory = sqlite3.Row
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
            batch_page = batch_pages.get(page_id)
            if not batch_page:
                errors.append(f"page_id={page_id} is not in the batch")
                continue
            if forbidden_body_keys.intersection(decision):
                errors.append(f"page_id={page_id} decision contains forbidden body text")
            if str(decision.get("decision") or "") != "human_verified":
                continue
            reviewer = str(decision.get("reviewer") or "").strip()
            note = str(decision.get("note") or "").strip()
            if not reviewer or len(note) < 20:
                errors.append(f"page_id={page_id} requires reviewer and a 20+ character note")
                continue
            source_file = str(batch_page.get("source_file") or "")
            source_path = resolve_source(source_root, source_file)
            expected_sha = str(batch_page.get("source_sha256") or "").lower()
            expected_image_sha = str(batch_page.get("page_image_sha256") or expected_sha).lower()
            actual_sha = sha256_file(source_path) if source_path.is_file() else ""
            if Path(source_file).suffix.lower() not in {".jpg", ".jpeg", ".png", ".tif", ".tiff"}:
                errors.append(f"page_id={page_id} source is not an image")
            if not source_path.is_file() or actual_sha != expected_sha or actual_sha != expected_image_sha:
                errors.append(f"page_id={page_id} source image hash/file check failed")
            if str(batch_page.get("source_audit_status") or "") != "hash_match":
                errors.append(f"page_id={page_id} batch source audit is not hash_match")

            row = connection.execute(
                """
                SELECT p.id, p.page_label, p.page_url, d.doc_key, d.source_platform,
                       pp.source_id, pp.source_file, pp.source_sha256,
                       pp.page_image_path, pp.page_image_sha256, pp.physical_page_no,
                       pp.citation_ready, pp.needs_human_review, pp.review_status
                FROM pages p
                JOIN documents d ON d.id=p.document_id
                JOIN page_provenance pp ON pp.page_id=p.id
                WHERE p.id=?
                """,
                (page_id,),
            ).fetchone()
            if row is None:
                errors.append(f"page_id={page_id} provenance row missing")
                continue
            checks = {
                "source_platform": (str(row["source_platform"] or ""), "domestic"),
                "doc_key": (str(row["doc_key"] or ""), str(batch_page.get("doc_key") or "")),
                "page_label": (str(row["page_label"] or ""), str(batch_page.get("page_label") or "")),
                "page_url": (str(row["page_url"] or ""), str(batch_page.get("page_url") or "")),
                "source_id": (str(row["source_id"] or ""), str(batch_page.get("source_id") or "")),
                "source_file": (str(row["source_file"] or ""), source_file),
                "source_sha256": (str(row["source_sha256"] or "").lower(), expected_sha),
                "page_image_path": (str(row["page_image_path"] or ""), source_file),
                "page_image_sha256": (str(row["page_image_sha256"] or "").lower(), expected_image_sha),
                "physical_page_no": (int(row["physical_page_no"] or 0), int(batch_page.get("physical_page_no") or 0)),
            }
            for name, (actual, expected) in checks.items():
                if actual != expected:
                    errors.append(f"page_id={page_id} {name} differs from batch")
            accepted.append(
                {
                    "page_id": page_id,
                    "reviewer": reviewer,
                    "note": note,
                    "year": int(batch_page.get("year") or 1949),
                    "period": str(batch_page.get("period") or "1949"),
                    "event_tags": str(batch_page.get("event_tags") or ""),
                }
            )

        before = strict_count(connection)
        if args.apply and errors:
            raise SystemExit("validation failed:\n- " + "\n- ".join(errors))
        if args.apply and not args.backup:
            raise SystemExit("--backup is required with --apply")
        if args.apply and args.backup.exists():
            raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")
        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db, args.backup)
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("BEGIN IMMEDIATE")
            try:
                for item in accepted:
                    stored_note = f"审核者：{item['reviewer']}；{item['note']}"
                    connection.execute(
                        """
                        UPDATE page_provenance
                           SET citation_ready=1, needs_human_review=0,
                               review_status='human_verified', human_review_note=?,
                               period=?, year=?, event_tags=?, updated_at=?
                         WHERE page_id=?
                        """,
                        (
                            stored_note,
                            item["period"],
                            item["year"],
                            item["event_tags"],
                            now,
                            item["page_id"],
                        ),
                    )
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
                if integrity != "ok" or foreign_keys:
                    raise RuntimeError(f"SQLite validation failed: {integrity}; foreign_keys={len(foreign_keys)}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        after = strict_count(connection)

    final_db_sha = sha256_file(db)
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "mode": "apply" if args.apply else "dry_run",
        "database_sha_before": actual_db_sha,
        "database_sha_after": final_db_sha,
        "batch_sha": expected_db_sha,
        "decisions": len(decisions),
        "accepted_decisions": len(accepted),
        "validation_errors": errors,
        "strict_citation_count_before": before,
        "strict_citation_count_after": after,
        "backup": str(args.backup) if args.apply and args.backup else "",
        "body_text_included": False,
        "source_images_modified": False,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
