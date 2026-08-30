#!/usr/bin/env python3
"""Apply an explicit, audited page-review decision file to domestic provenance.

Default mode is dry-run.  ``--apply`` requires a new backup path and an exact
database SHA match with the batch manifest.  Only pages with a local PDF whose
SHA256 matches and whose source URL has an exact ``#page=N`` locator can be
promoted.  The decision file is deliberately separate from the batch so a
reviewer can inspect and edit it before any SQLite write.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import re


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_BATCH = ROOT / "work" / "domestic" / "core_citation_batch_20260813" / "BATCH.json"
DEFAULT_DECISIONS = ROOT / "work" / "domestic" / "core_citation_batch_20260813" / "REVIEW_DECISIONS.json"
DEFAULT_REPORT = ROOT / "work" / "domestic" / "core_citation_batch_20260813" / "APPLY_REPORT.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_root_for(db_path: Path) -> Path:
    return db_path.resolve().parent.parent


def resolve_source(root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def exact_page_locator(page_url: str, expected: int) -> bool:
    fragment = urlsplit(page_url or "").fragment
    match = re.fullmatch(r"page=0*(\d+)", fragment)
    return bool(match and int(match.group(1)) == expected)


def load_decisions(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("pages"), list):
        return payload["pages"]
    raise ValueError("decision file must be a list or an object with pages")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--decisions", type=Path, default=DEFAULT_DECISIONS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    expected_db_sha = str(batch.get("database", {}).get("sha256") or "").lower()
    actual_db_sha = sha256_file(args.db)
    if expected_db_sha and actual_db_sha != expected_db_sha:
        raise SystemExit(f"database SHA mismatch: expected {expected_db_sha}, got {actual_db_sha}")

    batch_pages = {int(item["page_id"]): item for item in batch.get("pages", [])}
    decisions = load_decisions(args.decisions)
    errors: list[str] = []
    accepted: list[dict] = []
    seen: set[int] = set()
    source_root = source_root_for(args.db)
    for decision in decisions:
        page_errors: list[str] = []
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
        if str(decision.get("decision") or "") != "human_verified":
            continue
        note = str(decision.get("note") or "").strip()
        reviewer = str(decision.get("reviewer") or "").strip()
        if not reviewer or len(note) < 20:
            page_errors.append(f"page_id={page_id} requires reviewer and a 20+ character note")
            continue
        source_file = str(batch_page.get("source_file") or "")
        source_path = resolve_source(source_root, source_file)
        expected_sha = str(batch_page.get("source_sha256") or "").lower()
        expected_page = int(batch_page.get("pdf_page_no") or 0)
        actual_sha = sha256_file(source_path) if source_path.is_file() else ""
        if not source_file.lower().endswith(".pdf"):
            page_errors.append(f"page_id={page_id} source is not PDF")
        if not source_path.is_file() or actual_sha != expected_sha:
            page_errors.append(f"page_id={page_id} source hash/file check failed")
        if not exact_page_locator(str(batch_page.get("page_url") or ""), expected_page):
            page_errors.append(f"page_id={page_id} does not have exact page locator")
        if str(batch_page.get("source_audit_status") or "") not in {"hash_match", ""}:
            page_errors.append(f"page_id={page_id} batch source audit is not hash_match")
        errors.extend(page_errors)
        if page_errors:
            continue
        accepted.append(
            {
                "page_id": page_id,
                "reviewer": reviewer,
                "note": note,
                "source_file": source_file,
                "source_sha256": expected_sha,
                "pdf_page_no": expected_page,
            }
        )

    with sqlite3.connect(args.db) as connection:
        connection.row_factory = sqlite3.Row
        missing_rows: list[int] = []
        for item in accepted:
            row_errors: list[str] = []
            row = connection.execute(
                "SELECT page_id, source_file, source_sha256, pdf_page_no, page_url FROM page_provenance pp JOIN pages p ON p.id=pp.page_id WHERE pp.page_id=?",
                (item["page_id"],),
            ).fetchone()
            if not row:
                row_errors.append(f"page_id={item['page_id']} provenance row missing")
                errors.extend(row_errors)
                continue
            if str(row["source_file"] or "") != item["source_file"] or str(row["source_sha256"] or "").lower() != item["source_sha256"]:
                row_errors.append(f"page_id={item['page_id']} current provenance differs from batch")
            if int(row["pdf_page_no"] or 0) != item["pdf_page_no"] or not exact_page_locator(str(row["page_url"] or ""), item["pdf_page_no"]):
                row_errors.append(f"page_id={item['page_id']} current page locator differs from batch")
            errors.extend(row_errors)

        before = connection.execute(
            "SELECT count(*) FROM page_provenance WHERE citation_ready=1 AND needs_human_review=0 AND review_status='human_verified' AND trim(COALESCE(human_review_note,''))<>''"
        ).fetchone()[0]
        if args.apply and errors:
            raise SystemExit("validation failed:\n- " + "\n- ".join(errors))
        if args.apply and not args.backup:
            raise SystemExit("--backup is required with --apply")
        if args.apply and args.backup.exists():
            raise SystemExit(f"backup already exists; refusing to overwrite: {args.backup}")
        if args.apply:
            args.backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(args.db, args.backup)
            now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            connection.execute("BEGIN IMMEDIATE")
            try:
                for item in accepted:
                    stored_note = f"审核者：{item['reviewer']}；{item['note']}"
                    connection.execute(
                        """UPDATE page_provenance
                           SET citation_ready=1, needs_human_review=0,
                               review_status='human_verified', human_review_note=?, updated_at=?
                         WHERE page_id=?""",
                        (stored_note, now, item["page_id"]),
                    )
                connection.execute("PRAGMA foreign_keys=ON")
                integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]
                foreign_keys = connection.execute("PRAGMA foreign_key_check").fetchall()
                if integrity != "ok" or foreign_keys:
                    raise RuntimeError(f"SQLite validation failed: {integrity}; foreign_keys={len(foreign_keys)}")
                connection.commit()
            except Exception:
                connection.rollback()
                raise
        after = connection.execute(
            "SELECT count(*) FROM page_provenance WHERE citation_ready=1 AND needs_human_review=0 AND review_status='human_verified' AND trim(COALESCE(human_review_note,''))<>''"
        ).fetchone()[0]

    final_db_sha = sha256_file(args.db)
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
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
