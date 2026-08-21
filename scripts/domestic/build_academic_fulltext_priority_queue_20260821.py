#!/usr/bin/env python3
"""Build a body-free queue for academic full-text verification.

The input is the tracked academic metadata index.  The output contains only
safe bibliographic fields and an explicit next action.  It never reads a body,
never includes a local path, and never changes the formal SQLite database.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from collections import Counter
from pathlib import Path
from typing import Any


STABLE_STATUSES = {"FULLTEXT_PDF", "FULLTEXT_HTML"}
CANDIDATE_STATUSES = {"FULLTEXT_PDF_CANDIDATE", "FULLTEXT_HTML_CANDIDATE"}
ALLOWED_STATUSES = STABLE_STATUSES | CANDIDATE_STATUSES
TIER_ORDER = {"S": 0, "A": 1, "B": 2, "C": 3, "": 4}


def priority_for(record: dict[str, Any]) -> tuple[int, str, str]:
    tier = str(record.get("quality_tier") or "").strip().upper()
    status = str(record.get("fulltext_status") or "")
    if tier in {"S", "A"} and status in STABLE_STATUSES:
        return 0, "P0_STABLE_FULLTEXT", "先核验正文版本、作者/机构和页码；已有电子文本时不重复 OCR。"
    if tier in {"S", "A"} and status in CANDIDATE_STATUSES:
        return 1, "P1_FULLTEXT_CANDIDATE", "先核验来源入口、全文权限和版本；只有扫描件才进入定向 OCR。"
    if status in STABLE_STATUSES:
        return 2, "P2_STABLE_CONTEXT", "作为解释层全文核验；完成来源和页码审计后再决定是否纳入专题。"
    return 3, "P3_CANDIDATE_CONTEXT", "保留为候选，先补作者/机构/来源和版本字段，不直接入正式引文。"


def safe_record(record: dict[str, Any]) -> dict[str, Any]:
    rank, queue_class, next_action = priority_for(record)
    return {
        "external_id": str(record.get("external_id") or ""),
        "title": str(record.get("title") or ""),
        "author": str(record.get("author") or ""),
        "institution": str(record.get("institution") or ""),
        "publication_date": str(record.get("publication_date") or ""),
        "research_type": str(record.get("research_type") or ""),
        "quality_tier": str(record.get("quality_tier") or ""),
        "fulltext_status": str(record.get("fulltext_status") or ""),
        "source_url": str(record.get("source_url") or ""),
        "layer": str(record.get("layer") or ""),
        "version_relation": str(record.get("version_relation") or ""),
        "citation_ready": int(record.get("citation_ready") or 0),
        "human_verified": int(record.get("human_verified") or 0),
        "queue_class": queue_class,
        "priority_rank": rank,
        "next_action": next_action,
    }


def build(input_path: Path, output_path: Path) -> dict[str, Any]:
    payload = json.loads(input_path.read_text(encoding="utf-8"))
    records = payload.get("records") if isinstance(payload, dict) else None
    if not isinstance(records, list):
        raise ValueError("academic metadata index has no records list")

    selected = []
    for record in records:
        if not isinstance(record, dict):
            continue
        if record.get("academic_crosswalk_eligible", True) is False:
            continue
        if str(record.get("fulltext_status") or "") not in ALLOWED_STATUSES:
            continue
        item = safe_record(record)
        if not item["source_url"].startswith(("http://", "https://")):
            item["source_url"] = ""
        selected.append(item)

    selected.sort(
        key=lambda item: (
            int(item["priority_rank"]),
            TIER_ORDER.get(str(item["quality_tier"]).upper(), 4),
            str(item["publication_date"]),
            str(item["external_id"]),
        )
    )
    output = {
        "schema_version": "domestic_academic_fulltext_priority_queue.v1",
        "generated_at": dt.date.today().isoformat(),
        "source_index": str(input_path),
        "source_scope": "tracked_metadata_only",
        "body_read": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "selection_rule": "FULLTEXT_PDF/FULLTEXT_HTML and *_CANDIDATE only; S/A first",
        "summary": {
            "total": len(selected),
            "queue_classes": dict(sorted(Counter(item["queue_class"] for item in selected).items())),
            "quality_tiers": dict(sorted(Counter(item["quality_tier"] for item in selected).items())),
            "fulltext_statuses": dict(sorted(Counter(item["fulltext_status"] for item in selected).items())),
        },
        "records": selected,
    }
    serialized = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    forbidden = ("/Users/", "/private/", '"local_path"', '"derived_text_path"')
    if any(marker in serialized for marker in forbidden):
        raise ValueError("queue contains a forbidden local/body marker")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(serialized, encoding="utf-8")
    return {
        "status": "PASS",
        "records": len(selected),
        "summary": output["summary"],
        "body_read": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "output": str(output_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.input, args.output), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
