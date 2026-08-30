#!/usr/bin/env python3
"""Export the domestic academic layer as a body-free, path-free metadata index.

The source is a private staging SQLite database.  The output is deliberately
limited to bibliographic and structured topic metadata so a clean checkout can
search the full research layer without carrying the staging database or any
source body/local path.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_RECONCILIATION = ROOT / "data" / "domestic" / "academic_acquisition_reconciliation.json"


ALLOWED_METADATA_KEYS = {
    "events",
    "historical_periods",
    "people",
    "places",
    "research_type",
    "research_theme_phase",
    "research_card_category",
    "source_type",
    "date_or_period_original",
    "normalized_date",
    "institution_type",
    "classification_reason",
}


def safe_url(value: object) -> str:
    raw = str(value or "").strip()
    return raw if raw.startswith(("http://", "https://")) else ""


def clean_value(value: object) -> object:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def clean_metadata(raw: object) -> dict[str, object]:
    try:
        payload = json.loads(str(raw or "{}"))
    except (TypeError, json.JSONDecodeError):
        return {}
    if not isinstance(payload, dict):
        return {}
    result: dict[str, object] = {}
    for key in sorted(ALLOWED_METADATA_KEYS):
        if key not in payload:
            continue
        value = clean_value(payload[key])
        if value not in (None, "", []):
            result[key] = value
    return result


def record_role(row: sqlite3.Row, metadata: dict[str, object]) -> str:
    """Separate research-gap notes from actual explanation-layer materials."""
    author = str(row["author"] or "").strip()
    institution = str(row["institution"] or "").strip()
    if author == "本层著录" and institution == "任务记录":
        return "RESEARCH_GAP_NOTE"
    if str(row["layer"] or "") == "SCHOLARLY_RESEARCH":
        return "SCHOLARLY_RESEARCH"
    if str(row["layer"] or "") == "OFFICIAL_RETROSPECTIVE":
        return "OFFICIAL_RETROSPECTIVE"
    return "OTHER_RESEARCH_RECORD"


def normalize_title(value: object) -> str:
    return re.sub(r"[\s\W_]+", "", str(value or ""), flags=re.UNICODE).casefold()


def load_reconciliation(path: Path) -> dict[str, dict[str, object]]:
    """Load body-free identity holds and fail closed if the ledger is malformed."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"academic reconciliation unreadable: {exc}") from exc
    if not isinstance(payload, dict) or payload.get("schema_version") != "domestic_academic_acquisition_reconciliation.v1":
        raise ValueError("academic reconciliation schema is missing or unsupported")
    for field in ("body_text_included", "formal_db_written", "local_paths_included", "auto_delete"):
        if payload.get(field) is not False:
            raise ValueError(f"academic reconciliation {field} must be false")
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("academic reconciliation records must be a list")
    result: dict[str, dict[str, object]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("academic reconciliation record must be an object")
        external_id = str(record.get("external_id") or "").strip()
        if not external_id or external_id in result:
            raise ValueError(f"academic reconciliation has duplicate or empty external_id: {external_id}")
        status = str(record.get("status") or "")
        if status != "WRONG_PAGE_ALIAS_HOLD":
            raise ValueError(f"unsupported academic reconciliation status: {external_id}")
        if record.get("target_fulltext_present") is not False or record.get("formal_import_allowed") is not False:
            raise ValueError(f"academic reconciliation hold is not closed for import: {external_id}")
        result[external_id] = record
    return result


def apply_reconciliation_override(
    record: dict[str, object] | None,
    role: str,
) -> dict[str, object]:
    """Return safe exported flags after applying a source-identity hold."""
    if record is None:
        return {
            "fulltext_status": None,
            "review_status": None,
            "academic_crosswalk_eligible": role != "RESEARCH_GAP_NOTE",
            "version_relation": "",
            "reconciliation_status": "",
            "matched_record_id": "",
            "source_quality_audit": "",
            "observed_page_title": "",
            "target_fulltext_present": None,
        }
    matched_id = str(record.get("matched_record_id") or "").strip()
    return {
        "fulltext_status": "METADATA_OR_WRONG_PAGE",
        "review_status": "wrong_page_alias_hold",
        "academic_crosswalk_eligible": False,
        "version_relation": f"wrong_page_alias_to_{matched_id}" if matched_id else "wrong_page_alias_hold",
        "reconciliation_status": str(record.get("status") or ""),
        "matched_record_id": matched_id,
        "source_quality_audit": str(record.get("status") or ""),
        "observed_page_title": str(record.get("observed_page_title") or ""),
        "target_fulltext_present": False,
    }


def export(
    db_path: Path,
    output_path: Path,
    reconciliation_path: Path = DEFAULT_RECONCILIATION,
) -> dict[str, Any]:
    reconciliation = load_reconciliation(reconciliation_path)
    connection = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(
        """SELECT external_id, layer, title, author, institution,
                  publication_date, research_type, quality_tier, source_url,
                  fulltext_status, review_status, citation_ready,
                  human_verified, metadata_json
           FROM domestic_research_materials
           ORDER BY external_id"""
    ).fetchall()
    connection.close()

    title_groups: dict[str, list[str]] = {}
    for row in rows:
        key = normalize_title(row["title"])
        if key:
            title_groups.setdefault(key, []).append(str(row["external_id"] or ""))
    duplicate_group_by_id: dict[str, str] = {}
    duplicate_groups: list[dict[str, object]] = []
    for key, record_ids in sorted(title_groups.items()):
        if len(record_ids) < 2:
            continue
        group_id = "TITLE-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12].upper()
        for record_id in record_ids:
            duplicate_group_by_id[record_id] = group_id
        duplicate_groups.append(
            {
                "group_id": group_id,
                "record_ids": sorted(record_ids),
                "relation": "same_normalized_title_review_required",
            }
        )

    records: list[dict[str, object]] = []
    for row in rows:
        external_id = str(row["external_id"] or "")
        metadata = clean_metadata(row["metadata_json"])
        row_url = safe_url(row["source_url"])
        metadata_url = safe_url(metadata.get("source_url"))
        role = record_role(row, metadata)
        override = apply_reconciliation_override(reconciliation.get(external_id), role)
        records.append(
            {
                "external_id": external_id,
                "layer": str(row["layer"] or ""),
                "title": str(row["title"] or ""),
                "author": str(row["author"] or ""),
                "institution": str(row["institution"] or ""),
                "publication_date": str(row["publication_date"] or ""),
                "research_type": str(row["research_type"] or ""),
                "quality_tier": str(row["quality_tier"] or ""),
                "source_url": row_url or metadata_url,
                "fulltext_status": override["fulltext_status"] or str(row["fulltext_status"] or ""),
                "review_status": override["review_status"] or str(row["review_status"] or ""),
                "citation_ready": int(row["citation_ready"] or 0),
                "human_verified": int(row["human_verified"] or 0),
                "record_role": role,
                "academic_crosswalk_eligible": override["academic_crosswalk_eligible"],
                "metadata": metadata,
                "duplicate_group_id": duplicate_group_by_id.get(external_id, ""),
                "version_relation": override["version_relation"] or (
                    "same_normalized_title_review_required"
                    if external_id in duplicate_group_by_id
                    else "no_exact_title_duplicate_detected"
                ),
                **(
                    {
                        "reconciliation_status": override["reconciliation_status"],
                        "matched_record_id": override["matched_record_id"],
                        "source_quality_audit": override["source_quality_audit"],
                        "observed_page_title": override["observed_page_title"],
                        "target_fulltext_present": override["target_fulltext_present"],
                    }
                    if override["reconciliation_status"]
                    else {}
                ),
            }
        )

    payload = {
        "schema_version": "domestic_academic_layer_metadata.v1",
        "generated_at": dt.date.today().isoformat(),
        "source_scope": "staging_metadata_only",
        "reconciliation_ledger": "data/domestic/academic_acquisition_reconciliation.json",
        "reconciled_record_count": len(reconciliation),
        "body_read": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_record_count": sum(len(group["record_ids"]) for group in duplicate_groups),
        "duplicate_groups": duplicate_groups,
        "records": records,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "status": "PASS",
        "records": len(records),
        "body_read": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "output": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reconciliation", type=Path, default=DEFAULT_RECONCILIATION)
    args = parser.parse_args()
    report = export(args.db, args.output, args.reconciliation)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
