#!/usr/bin/env python3
"""Build the metadata-only ledger for manually verified domestic fragments.

The ledger is deliberately narrower than the formal page citation layer.  A
row may expose a short, visually verified fragment while still declaring
``page_citation_ready=false`` and ``body_read=false``.  The script reads only
review artifacts and never reads or writes the formal SQLite database.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
FRAGMENT_REFS = [
    "work/domestic/pcc_1946_page23_manual_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/pcc_1946_page52_manual_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/pcc_1946_page62_manual_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/pcc_1946_page101_manual_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/pcc_1946_page125_manual_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/pcc_1946_page206_manual_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/nlc_1949_page220_manual_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/saac_1949_common_program_fragment_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/minmeng_wenxian_1945_fragment_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/guangmingbao_1946_issue8_fragment_review_20260821/FRAGMENT_SECOND_PASS.json",
    "work/domestic/guangmingbao_1946_issue8_refuse_fragment_review_20260821/FRAGMENT_SECOND_PASS.json",
]
DEFAULT_LEDGER = ROOT / "data" / "domestic" / "citation_fragments.jsonl"
DEFAULT_MANIFEST = ROOT / "data" / "domestic" / "citation_fragments_manifest.json"
DEFAULT_REPORT = ROOT / "work" / "domestic" / "citation_fragment_ledger_20260821" / "REPORT.json"


def read_json(relative: str) -> dict[str, Any]:
    path = ROOT / relative
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_relative(value: object, label: str) -> None:
    if value is None or value == "":
        return
    text = str(value)
    if text.startswith(("/", "file://")):
        raise ValueError(f"{label} must remain repository-relative: {text}")


def build_row(relative_ref: str) -> dict[str, Any]:
    artifact = read_json(relative_ref)
    page_ref = str(artifact["source_page_review_ref"])
    page_review = read_json(page_ref)
    source = artifact["source"]
    page_source = page_review["source"]
    fragment = artifact["fragment"]
    boundary = artifact["evidence_boundary"]

    required_true = {
        "quote_safe": fragment.get("quote_safe"),
        "search_safe": fragment.get("search_safe"),
        "fragment_citation_ready": fragment.get("fragment_citation_ready"),
        "page_identity_ready": boundary.get("page_identity_ready"),
        "fragment_identity_ready": boundary.get("fragment_identity_ready"),
    }
    failed_true = [name for name, value in required_true.items() if value is not True]
    if failed_true:
        raise ValueError(f"{relative_ref}: required positive gate(s) missing: {failed_true}")
    required_false = {
        "page_citation_ready": boundary.get("page_citation_ready"),
        "formal_db_written": boundary.get("formal_db_written"),
        "body_read": boundary.get("body_read"),
    }
    failed_false = [name for name, value in required_false.items() if value is not False]
    if failed_false:
        raise ValueError(f"{relative_ref}: promotion boundary changed unexpectedly: {failed_false}")

    for label, value in {
        "fragment_ref": relative_ref,
        "page_review_ref": page_ref,
        "boundary_review_ref": artifact.get("source_boundary_review_ref"),
        "source_file": page_source.get("source_file"),
        "page_url": page_source.get("page_url"),
        "ocr_crosscheck": fragment.get("ocr_crosscheck"),
    }.items():
        ensure_relative(value, label)

    target_id = str(fragment["target_id"])
    source_id = str(source["source_id"])
    raw_source_page_no = source.get("source_page_no", source.get("pdf_page"))
    if raw_source_page_no in (None, ""):
        raise ValueError(f"{relative_ref}: source_page_no/pdf_page is required")
    source_page_no = int(raw_source_page_no)
    raw_pdf_page = source.get("pdf_page")
    pdf_page = int(raw_pdf_page) if raw_pdf_page not in (None, "") else None
    source_page_type = str(source.get("page_type") or ("pdf" if pdf_page is not None else "official_image"))
    raw_year = source.get("source_year", source.get("publication_year"))
    if raw_year in (None, ""):
        raw_year = next((year for year in (1941, 1944, 1945, 1946, 1947, 1948, 1949) if str(year) in source_id), None)
    source_year = int(raw_year) if raw_year not in (None, "") else None
    raw_event_year = source.get("event_year")
    event_year = int(raw_event_year) if raw_event_year not in (None, "") else None
    year_anchor_label = str(source.get("year_anchor_label") or "")
    if not year_anchor_label and source_year:
        year_anchor_label = (
            f"{source_year}（出版年锚点）"
            if source_year == 1946
            else f"{source_year}（来源年锚点）"
        )
    page_locator = str(source.get("page_locator") or "")
    if not page_locator:
        page_locator = (
            f"PDF 第 {pdf_page} 页"
            if pdf_page is not None
            else f"官方影像第 {source_page_no} 图"
        )
    if source_id == "nlc-pcc-1946-NLC416-01jh004019-12949":
        fragment_prefix = "pcc-1946"
    else:
        fragment_prefix = source_id
    row = {
        "schema": "domestic_citation_fragment.v1",
        "fragment_id": f"{fragment_prefix}-p{source_page_no:03d}-{target_id}",
        "target_id": target_id,
        "title": str(fragment["title"]),
        "text": str(fragment["text"]),
        "display_suffix": str(fragment.get("display_suffix") or ""),
        "fragment_ends_mid_sentence": bool(fragment.get("fragment_ends_mid_sentence", False)),
        "scope": str(fragment.get("scope") or ""),
        "quote_safe": True,
        "search_safe": True,
        "fragment_citation_ready": True,
        "page_citation_ready": False,
        "body_read": False,
        "formal_db_written": False,
        "main_db_page_id": int(page_source["main_db_page_id"]),
        "source_id": source_id,
        "source_file": str(page_source["source_file"]),
        "source_sha256": str(source["source_sha256"]),
        "pdf_page": pdf_page,
        "source_page_no": source_page_no,
        "source_page_type": source_page_type,
        "page_locator": page_locator,
        "printed_page": (
            int(source["printed_page"])
            if source.get("printed_page") not in (None, "")
            else None
        ),
        "source_year": source_year,
        "event_year": event_year,
        "year_anchor_label": year_anchor_label,
        "page_url": str(page_source.get("page_url") or ""),
        "page_review_ref": page_ref,
        "fragment_review_ref": relative_ref,
        "boundary_review_ref": artifact.get("source_boundary_review_ref"),
        "ocr_crosscheck": fragment.get("ocr_crosscheck"),
        "page_image_300dpi": source.get("page_image_300dpi"),
        "page_image_300dpi_sha256": source.get("page_image_300dpi_sha256"),
        "page_image_600dpi_probe": source.get("page_image_600dpi_probe"),
        "page_image_600dpi_probe_sha256": source.get("page_image_600dpi_probe_sha256"),
        "boundary_status": boundary.get("continuation_boundary_status")
        or boundary.get("continuation_boundary")
        or boundary.get("continuation_status"),
        "promotion_scope": str(boundary.get("promotion_scope") or ""),
        "transcription_mode": str(fragment.get("transcription_mode") or ""),
        "character_check": str(fragment.get("character_check") or ""),
        "punctuation_check": str(fragment.get("punctuation_check") or ""),
    }
    for key in (
        "source_file",
        "page_url",
        "page_review_ref",
        "fragment_review_ref",
        "boundary_review_ref",
        "ocr_crosscheck",
        "page_image_300dpi",
        "page_image_600dpi_probe",
    ):
        ensure_relative(row.get(key), key)
    return row


def build(ledger_path: Path, manifest_path: Path, report_path: Path) -> dict[str, Any]:
    rows = [build_row(relative) for relative in FRAGMENT_REFS]
    rows.sort(key=lambda row: (int(row.get("source_page_no") or row.get("pdf_page") or 0), str(row["fragment_id"])))
    seen_ids: set[str] = set()
    for row in rows:
        if row["fragment_id"] in seen_ids:
            raise ValueError(f"duplicate fragment_id: {row['fragment_id']}")
        seen_ids.add(row["fragment_id"])

    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows),
        encoding="utf-8",
    )
    ledger_hash = sha256(ledger_path)
    manifest = {
        "schema": "domestic_citation_fragment_ledger_manifest.v1",
        "generated_at": date.today().isoformat(),
        "ledger": "data/domestic/citation_fragments.jsonl",
        "ledger_sha256": ledger_hash,
        "fragment_review_refs": FRAGMENT_REFS,
        "fragment_count": len(rows),
        "fragment_citation_ready_count": sum(bool(row["fragment_citation_ready"]) for row in rows),
        "page_citation_ready_count": sum(bool(row["page_citation_ready"]) for row in rows),
        "formal_db_written_count": sum(bool(row["formal_db_written"]) for row in rows),
        "body_read_count": sum(bool(row["body_read"]) for row in rows),
        "scope": "eleven manually verified short fragments from 1945, 1946 and 1949 PDF/official-image sources; not full-page body promotion",
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report = {
        "schema": "domestic_citation_fragment_ledger_report.v1",
        "generated_at": manifest["generated_at"],
        "status": "PASS",
        "ledger": "data/domestic/citation_fragments.jsonl",
        "manifest": "data/domestic/citation_fragments_manifest.json",
        "fragment_count": len(rows),
        "checks": {
            "all_review_artifacts_present": True,
            "all_fragment_gates_valid": True,
            "all_paths_repository_relative": True,
            "formal_db_written": False,
            "page_citation_ready": False,
        },
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    report = build(args.ledger, args.manifest, args.report)
    print(json.dumps({"status": report["status"], "fragment_count": report["fragment_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
