#!/usr/bin/env python3
"""Recover deterministic evidence links without upgrading citation status.

First-principles rule: a searchable text is not a formal source. This repair
only records facts that can be recomputed from local bytes, stable page
locators, explicit publication metadata, or another record bound to the exact
same single-issue asset. It never marks a page ``citation_ready``.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import shutil
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_REPORT_DIR = ROOT / "work" / "evidence-chain-20260813"
BATCH_ID = "codex-evidence-chain-20260813"
DATE_RE = re.compile(
    r"^(?:18|19|20)\d{2}(?:-(?:0[1-9]|1[0-2])(?:-(?:0[1-9]|[12]\d|3[01]))?)?$"
)
DAY_IN_NAME_RE = re.compile(
    r"(?<!\d)((?:18|19|20)\d{2})[-年](0?[1-9]|1[0-2])[-月]"
    r"(0?[1-9]|[12]\d|3[01])(?:日)?(?!\d)"
)
COMPOSITE_ASSET_RE = re.compile(
    r"(?:第?1[-–—]12期|第[一二三四五六七八九十百\d]+卷\.pdf$|全集|合集)", re.I
)
CATALOG_KEY_RE = re.compile(r"(NLC\d+-[0-9A-Za-z]+-[0-9A-Za-z]+)", re.I)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def scalar(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> int | str:
    return conn.execute(sql, params).fetchone()[0]


def valid_date(value: object) -> str | None:
    cleaned = str(value or "").strip()
    return cleaned if DATE_RE.fullmatch(cleaned) else None


def resolve_local_path(raw: object, project_root: Path) -> Path | None:
    value = str(raw or "").strip()
    if not value or value.startswith(("http://", "https://", "file://")):
        return None
    path = Path(value).expanduser()
    return (path if path.is_absolute() else project_root / path).resolve()


def project_relative(path: Path, project_root: Path) -> str | None:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return None


def page_number(page_url: object, page_label: object, source_path: Path) -> int | None:
    match = re.search(r"[#&?]page=0*(\d+)", str(page_url or ""), re.I)
    if match:
        return int(match.group(1))
    label = str(page_label or "").strip()
    if source_path.suffix.lower() == ".pdf" and re.fullmatch(r"0*\d+", label):
        return int(label)
    return None


def compatible_most_precise(values: list[str]) -> str | None:
    unique = sorted(set(values), key=len, reverse=True)
    if not unique:
        return None
    best = unique[0]
    return best if all(best.startswith(value) for value in unique) else None


def catalog_keys(*values: object) -> set[str]:
    return {
        match.upper()
        for value in values
        for match in CATALOG_KEY_RE.findall(str(value or ""))
    }


def explicit_web_date(document: sqlite3.Row, project_root: Path) -> tuple[str | None, str | None]:
    html_path = resolve_local_path(document["local_html"], project_root)
    html = html_path.read_text(errors="ignore") if html_path and html_path.is_file() else ""
    candidates: list[tuple[str, str]] = []
    for value in re.findall(
        r"(?:发布时间|发布日期|更新日期)\s*[:：]\s*"
        r"((?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))",
        html,
    ):
        candidates.append(("html_publication_label", value))

    url_match = re.search(
        r"/((?:19|20)\d{2})/(0[1-9]|1[0-2])/(0[1-9]|[12]\d|3[01])/",
        str(document["url"] or ""),
    )
    if url_match:
        candidates.append(("dated_article_url", "-".join(url_match.groups())))

    # Some official overview pages display one update date in the heading but
    # do not label it. Accept only when there is exactly one ISO day in a span.
    if not candidates:
        span_dates = {
            date
            for span in re.findall(r"<span[^>]*>(.*?)</span>", html, re.I | re.S)
            for date in re.findall(
                r"((?:19|20)\d{2}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01]))",
                span,
            )
        }
        if len(span_dates) == 1:
            candidates.append(("single_heading_date", next(iter(span_dates))))

    values = {value for _, value in candidates}
    if len(values) != 1:
        return None, None
    return next(iter(values)), "+".join(sorted({reason for reason, _ in candidates}))


def collect_metrics(conn: sqlite3.Connection) -> dict[str, int | str]:
    return {
        "integrity_check": scalar(conn, "PRAGMA integrity_check"),
        "foreign_key_violations": len(conn.execute("PRAGMA foreign_key_check").fetchall()),
        "pages": scalar(conn, "SELECT COUNT(*) FROM pages"),
        "page_fts": scalar(conn, "SELECT COUNT(*) FROM page_fts"),
        "pages_without_fts": scalar(
            conn,
            "SELECT COUNT(*) FROM pages p LEFT JOIN page_fts f ON f.rowid=p.id WHERE f.rowid IS NULL",
        ),
        "fts_without_pages": scalar(
            conn,
            "SELECT COUNT(*) FROM page_fts f LEFT JOIN pages p ON p.id=f.rowid WHERE p.id IS NULL",
        ),
        "domestic_pages_missing_provenance": scalar(
            conn,
            """SELECT COUNT(*) FROM pages p
               JOIN documents d ON d.id=p.document_id
               LEFT JOIN page_provenance pp ON pp.page_id=p.id
               WHERE d.source_platform='domestic' AND pp.page_id IS NULL""",
        ),
        "domestic_file_backed_provenance": scalar(
            conn,
            """SELECT COUNT(*) FROM page_provenance pp
               JOIN documents d ON d.id=pp.document_id
               WHERE d.source_platform='domestic'
                 AND trim(COALESCE(pp.source_file,''))<>''
                 AND length(trim(COALESCE(pp.source_sha256,'')))=64""",
        ),
        "domestic_documents_missing_date": scalar(
            conn,
            """SELECT COUNT(*) FROM documents
               WHERE source_platform='domestic'
                 AND trim(COALESCE(date_guess,''))=''""",
        ),
        "formal_citation_pages": scalar(
            conn,
            """SELECT COUNT(*) FROM page_provenance
               WHERE citation_ready=1
                 AND needs_human_review=0
                 AND review_status='human_verified'
                 AND trim(COALESCE(human_review_note,''))<>''""",
        ),
    }


def audit_source_files(
    conn: sqlite3.Connection,
    project_root: Path,
    hash_cache: dict[str, tuple[str, int]],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    rows = conn.execute(
        """SELECT pp.source_file,
                  group_concat(DISTINCT lower(pp.source_sha256)) AS expected_sha256,
                  count(*) AS pages
           FROM page_provenance pp
           JOIN documents d ON d.id=pp.document_id
           WHERE d.source_platform='domestic'
           GROUP BY pp.source_file
           ORDER BY pp.source_file"""
    ).fetchall()
    assets: list[dict[str, object]] = []
    project_root = project_root.resolve()
    missing = mismatched = absolute = outside = total_bytes = 0
    for row in rows:
        raw = str(row["source_file"] or "").strip()
        absolute += int(Path(raw).expanduser().is_absolute())
        path = resolve_local_path(raw, project_root)
        relative = project_relative(path, project_root) if path else None
        if path and not relative:
            outside += 1
            assets.append(
                {
                    "source_file": "<outside-project>",
                    "pages": row["pages"],
                    "status": "outside_project",
                }
            )
            continue
        if not path or not path.is_file():
            missing += 1
            assets.append(
                {
                    "source_file": relative or "<unresolved>",
                    "pages": row["pages"],
                    "status": "missing_or_outside_project",
                }
            )
            continue
        cache_key = str(path)
        if cache_key not in hash_cache:
            hash_cache[cache_key] = (sha256(path), path.stat().st_size)
        actual_hash, size = hash_cache[cache_key]
        expected = sorted(set(str(row["expected_sha256"] or "").split(",")))
        ok = actual_hash in expected
        mismatched += int(not ok)
        total_bytes += size
        assets.append(
            {
                "source_file": relative,
                "actual_sha256": actual_hash,
                "expected_sha256": expected,
                "size": size,
                "pages": row["pages"],
                "status": "matched" if ok else "hash_mismatch",
            }
        )
    return assets, {
        "source_files_checked": len(rows),
        "source_file_bytes": total_bytes,
        "source_files_missing": missing,
        "source_hash_mismatches": mismatched,
        "absolute_source_paths": absolute,
        "source_files_outside_project": outside,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--expected-sha")
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    args = parser.parse_args()

    db = args.db.expanduser().resolve()
    if not db.is_file():
        raise SystemExit(f"database not found: {db}")
    project_root = db.parent.parent
    before_sha = sha256(db)
    if args.expected_sha and before_sha != args.expected_sha:
        raise SystemExit(f"hash mismatch: expected {args.expected_sha}, got {before_sha}")

    backup: Path | None = None
    if args.apply:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = db.with_name(f"{db.name}.pre_evidence_chain_{stamp}.bak")
        shutil.copy2(db, backup)
        if sha256(backup) != before_sha:
            raise SystemExit("backup verification failed")

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    before = collect_metrics(conn)
    all_documents = conn.execute(
        "SELECT * FROM documents WHERE source_platform='domestic'"
    ).fetchall()

    documents_by_file: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for document in all_documents:
        preferred = (
            document["local_html"]
            if document["hit_type"] in ("domestic_web", "domestic_public_web", "saac_album_index")
            else document["local_txt"] or document["local_html"]
        )
        path = resolve_local_path(preferred, project_root)
        if path:
            documents_by_file[str(path)].append(document)

    dated_by_catalog_key: dict[str, set[str]] = defaultdict(set)
    dated_rows = conn.execute(
        """SELECT d.doc_key, d.title, d.local_txt, d.local_html, d.date_guess,
                  pp.source_file, pp.ocr_md_path
           FROM documents d
           LEFT JOIN page_provenance pp ON pp.document_id=d.id
           WHERE d.source_platform='domestic'
             AND trim(COALESCE(d.date_guess,''))<>''"""
    ).fetchall()
    for row in dated_rows:
        date = valid_date(row["date_guess"])
        if not date:
            continue
        for key in catalog_keys(
            row["doc_key"], row["title"], row["local_txt"], row["local_html"],
            row["source_file"], row["ocr_md_path"],
        ):
            dated_by_catalog_key[key].add(date)

    target_pages = conn.execute(
        """SELECT p.id AS page_id, p.page_label, p.page_url, p.text,
                  d.*,
                  pp.source_id AS existing_source_id
           FROM pages p
           JOIN documents d ON d.id=p.document_id
           LEFT JOIN page_provenance pp ON pp.page_id=p.id
           WHERE d.source_platform='domestic'
             AND (pp.page_id IS NULL OR pp.source_id='domestic-pilot-missing-prov')
           ORDER BY p.id"""
    ).fetchall()

    hash_cache: dict[str, tuple[str, int]] = {}
    provenance_rows: list[dict[str, object]] = []
    provenance_unresolved: list[dict[str, object]] = []
    for row in target_pages:
        preferred = (
            row["local_html"]
            if row["hit_type"] in ("domestic_web", "domestic_public_web", "saac_album_index")
            else row["local_txt"] or row["local_html"]
        )
        source_path = resolve_local_path(preferred, project_root)
        relative = project_relative(source_path, project_root) if source_path else None
        if not source_path or not source_path.is_file() or not relative:
            provenance_unresolved.append(
                {
                    "page_id": row["page_id"],
                    "doc_key": row["doc_key"],
                    "title": row["title"],
                    "reason": "no_project_local_source_snapshot",
                    "source_url": row["page_url"] or row["url"] or "",
                }
            )
            continue
        cache_key = str(source_path)
        if cache_key not in hash_cache:
            hash_cache[cache_key] = (sha256(source_path), source_path.stat().st_size)
        source_hash, source_size = hash_cache[cache_key]
        number = page_number(row["page_url"], row["page_label"], source_path)
        aggregate_match = re.search(
            r"(?:^|-)p0*(\d+)-p0*\d+$", str(row["page_label"] or ""), re.I
        )
        named_page_match = re.search(
            r"(?:front|page|p)[-_]?0*(\d+)$", str(row["page_label"] or ""), re.I
        )
        physical_number = (
            number
            if number is not None
            else int(aggregate_match.group(1))
            if aggregate_match
            else int(named_page_match.group(1))
            if named_page_match
            else 0
        )
        date = valid_date(row["date_guess"])
        provenance_rows.append(
            {
                "page_id": row["page_id"],
                "document_id": row["id"],
                "source_id": f"domestic-file:{source_hash[:16]}",
                "source_file": relative,
                "source_sha256": source_hash,
                "source_file_size": source_size,
                "pdf_page_no": number,
                # For aggregate OCR chunks, the range start is the locator.
                # Zero remains reserved for a non-page aggregate with no range.
                "physical_page_no": physical_number,
                "page_image_path": row["page_url"] if number else None,
                "ocr_engine": "legacy-unknown" if "ocr" in str(row["hit_type"] or "") else None,
                "ocr_mode": "legacy_import_file_backed" if "ocr" in str(row["hit_type"] or "") else None,
                "text_chars": len(row["text"] or ""),
                "year": int(date[:4]) if date else None,
                "source_title": row["volume_title"] or row["title"],
                "existing_source_id": row["existing_source_id"],
            }
        )

    date_proposals: list[dict[str, object]] = []
    date_unresolved: list[dict[str, object]] = []
    for document in all_documents:
        if str(document["date_guess"] or "").strip():
            continue
        preferred = (
            document["local_html"]
            if document["hit_type"] in ("domestic_web", "domestic_public_web", "saac_album_index")
            else document["local_txt"] or document["local_html"]
        )
        path = resolve_local_path(preferred, project_root)
        proposed: str | None = None
        reason: str | None = None
        evidence_values: list[str] = []

        if document["hit_type"] in ("domestic_web", "domestic_public_web"):
            proposed, reason = explicit_web_date(document, project_root)
            if proposed:
                evidence_values = [proposed]
            catalog_dates: list[str] = []
        else:
            path_text = path.as_posix() if path else ""
            safe_single_asset = (
                any(marker in path_text for marker in ("/press_scans/", "/gazette_scans/", "/observer_issue_ocr_"))
                and not COMPOSITE_ASSET_RE.search(path.name if path else "")
            )
            keys = catalog_keys(
                document["doc_key"], document["title"], document["local_txt"],
                document["local_html"],
            )
            catalog_dates = sorted(
                set().union(*(dated_by_catalog_key.get(key, set()) for key in keys))
                if keys else set()
            )
            if safe_single_asset and path:
                inherited = [
                    date
                    for other in documents_by_file.get(str(path), [])
                    if other["id"] != document["id"]
                    for date in [valid_date(other["date_guess"])]
                    if date
                ]
                filename_match = DAY_IN_NAME_RE.search(path.name)
                filename_date = (
                    f"{filename_match.group(1)}-{int(filename_match.group(2)):02d}-"
                    f"{int(filename_match.group(3)):02d}"
                    if filename_match
                    else None
                )
                evidence_values = catalog_dates or inherited
                if filename_date:
                    evidence_values.append(filename_date)
                proposed = compatible_most_precise(evidence_values)
                if proposed:
                    reason = "catalog_key_consensus" if catalog_dates else "same_single_asset_date"
                    if filename_date:
                        reason += "+filename_day"

        if proposed and reason:
            date_proposals.append(
                {
                    "document_id": document["id"],
                    "doc_key": document["doc_key"],
                    "title": document["title"],
                    "proposed_date": proposed,
                    "reason": reason,
                    "evidence_values": sorted(set(evidence_values)),
                    "source_file": project_relative(path, project_root) if path else None,
                }
            )
        else:
            date_unresolved.append(
                {
                    "document_id": document["id"],
                    "doc_key": document["doc_key"],
                    "title": document["title"],
                    "hit_type": document["hit_type"],
                    "reason": (
                        "conflicting_catalog_dates"
                        if len(catalog_dates) > 1 and not compatible_most_precise(catalog_dates)
                        else "no_unambiguous_document_or_publication_date"
                    ),
                    "evidence_values": " | ".join(catalog_dates),
                    "source_file": project_relative(path, project_root) if path else None,
                }
            )

    now = datetime.now().isoformat(timespec="seconds")
    conn.execute("BEGIN IMMEDIATE")
    inserted = updated = 0
    for row in provenance_rows:
        values = (
            row["document_id"], row["source_id"], row["source_file"], row["source_sha256"],
            row["source_file_size"], row["pdf_page_no"], row["physical_page_no"],
            row["page_image_path"], row["ocr_engine"], row["ocr_mode"], row["text_chars"],
            row["year"], row["source_title"], BATCH_ID, now, now,
        )
        if row["existing_source_id"]:
            conn.execute(
                """UPDATE page_provenance
                   SET document_id=?, source_id=?, source_file=?, source_sha256=?,
                       source_file_size=?, pdf_page_no=?, physical_page_no=?, page_image_path=?,
                       ocr_engine=?, ocr_mode=?, text_chars=?, citation_ready=0,
                       needs_human_review=1, review_status='review_only',
                       machine_review_note='Local source bytes and locator verified; OCR/transcription content not human-verified; formal citation blocked',
                       human_review_note=NULL, year=?, source_title=?, batch_id=?,
                       created_at=COALESCE(created_at, ?), updated_at=?
                   WHERE page_id=?""",
                values + (row["page_id"],),
            )
            updated += 1
        else:
            conn.execute(
                """INSERT INTO page_provenance (
                       page_id, document_id, source_id, source_file, source_sha256,
                       source_file_size, pdf_page_no, physical_page_no, page_image_path,
                       ocr_engine, ocr_mode, text_chars, citation_ready, needs_human_review,
                       review_status, machine_review_note, human_review_note, year,
                       source_title, batch_id, created_at, updated_at
                   ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 1, 'review_only',
                       'Local source bytes and locator verified; OCR/transcription content not human-verified; formal citation blocked',
                       NULL, ?, ?, ?, ?, ?)""",
                (row["page_id"],) + values,
            )
            inserted += 1

    for proposal in date_proposals:
        conn.execute(
            """UPDATE documents SET date_guess=?
               WHERE id=? AND trim(COALESCE(date_guess,''))=''""",
            (proposal["proposed_date"], proposal["document_id"]),
        )

    after = collect_metrics(conn)
    if after["integrity_check"] != "ok":
        conn.rollback()
        raise SystemExit(f"integrity check failed: {after['integrity_check']}")
    if after["foreign_key_violations"]:
        conn.rollback()
        raise SystemExit(f"foreign key violations: {after['foreign_key_violations']}")
    if after["pages_without_fts"] or after["fts_without_pages"]:
        conn.rollback()
        raise SystemExit("FTS alignment failed")
    if after["formal_citation_pages"] != before["formal_citation_pages"]:
        conn.rollback()
        raise SystemExit("formal citation count changed unexpectedly")

    source_assets, source_file_audit = audit_source_files(conn, project_root, hash_cache)
    if source_file_audit["source_files_missing"]:
        conn.rollback()
        raise SystemExit("domestic provenance points to missing or external source files")
    if source_file_audit["source_hash_mismatches"]:
        conn.rollback()
        raise SystemExit("domestic provenance source hash mismatch")
    if source_file_audit["absolute_source_paths"]:
        conn.rollback()
        raise SystemExit("domestic provenance contains absolute source paths")
    if source_file_audit["source_files_outside_project"]:
        conn.rollback()
        raise SystemExit("domestic provenance escapes the project directory")

    if args.apply:
        conn.commit()
    else:
        conn.rollback()
    conn.close()
    after_sha = sha256(db)
    if not args.apply and after_sha != before_sha:
        raise SystemExit("dry-run changed the database")

    args.report_dir.mkdir(parents=True, exist_ok=True)
    (args.report_dir / "source_assets.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in source_assets),
        encoding="utf-8",
    )
    for name, rows, fields in (
        (
            "provenance_unresolved.csv",
            provenance_unresolved,
            ["page_id", "doc_key", "title", "reason", "source_url"],
        ),
        (
            "date_unresolved.csv",
            date_unresolved,
            [
                "document_id", "doc_key", "title", "hit_type", "reason",
                "evidence_values", "source_file",
            ],
        ),
    ):
        with (args.report_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    result = {
        "mode": "apply" if args.apply else "dry-run",
        "database": f"data/{db.name}",
        "before_sha256": before_sha,
        "after_sha256": after_sha,
        "backup": backup.name if backup else None,
        "before": before,
        "changes": {
            "provenance_inserted": inserted,
            "legacy_stubs_upgraded": updated,
            "document_dates_backfilled": len(date_proposals),
        },
        "source_file_audit": source_file_audit,
        "after": after,
        "unresolved": {
            "provenance_pages": len(provenance_unresolved),
            "document_dates": len(date_unresolved),
        },
        "date_proposals": date_proposals,
        "completed_at": now,
    }
    output = args.report_dir / f"evidence_chain_{result['mode']}.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
