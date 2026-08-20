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


def normalize_title(value: object) -> str:
    return re.sub(r"[\s\W_]+", "", str(value or ""), flags=re.UNICODE).casefold()


def export(db_path: Path, output_path: Path) -> dict[str, Any]:
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
                "fulltext_status": str(row["fulltext_status"] or ""),
                "review_status": str(row["review_status"] or ""),
                "citation_ready": int(row["citation_ready"] or 0),
                "human_verified": int(row["human_verified"] or 0),
                "metadata": metadata,
                "duplicate_group_id": duplicate_group_by_id.get(external_id, ""),
                "version_relation": (
                    "same_normalized_title_review_required"
                    if external_id in duplicate_group_by_id
                    else "no_exact_title_duplicate_detected"
                ),
            }
        )

    payload = {
        "schema_version": "domestic_academic_layer_metadata.v1",
        "generated_at": dt.date.today().isoformat(),
        "source_scope": "staging_metadata_only",
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
    args = parser.parse_args()
    report = export(args.db, args.output)
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
