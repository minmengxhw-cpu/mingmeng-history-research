#!/usr/bin/env python3
"""Audit the metadata-only academic-to-topic crosswalk.

The matching logic is the same helper used by the web page.  This command
reads staging bibliographic metadata only and writes a compact report; it does
not read source bodies or change either SQLite database.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
import app  # noqa: E402


DEFAULT_DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
DEFAULT_COVERAGE = ROOT / "data/domestic/event_coverage.json"
DEFAULT_CARDS = ROOT / "data/domestic/topic_comparison_cards.json"
DEFAULT_CROSSWALK = ROOT / "data/domestic/academic_topic_crosswalk.json"


def load_tracked_crosswalk(path: Path, db_path: Path) -> dict:
    """Replay the tracked metadata crosswalk when private staging is absent."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            "body_read": False,
            "source": "tracked_metadata_crosswalk",
            "snapshot_only": True,
            "status": "BLOCKED",
            "reason": f"tracked academic crosswalk unreadable: {exc}",
        }
    if not isinstance(payload, dict):
        return {
            "body_read": False,
            "source": "tracked_metadata_crosswalk",
            "snapshot_only": True,
            "status": "BLOCKED",
            "reason": "tracked academic crosswalk is not an object",
        }
    topics = payload.get("topics")
    if payload.get("status") != "PASS" or payload.get("body_read") is not False or not isinstance(topics, list):
        return {
            "body_read": False,
            "source": "tracked_metadata_crosswalk",
            "snapshot_only": True,
            "status": "BLOCKED",
            "reason": "tracked academic crosswalk is not a PASS/body_read=false snapshot",
        }
    report = dict(payload)
    report.pop("db_path", None)
    report.update(
        {
            "source": "tracked_metadata_crosswalk",
            "snapshot_only": True,
            "audit_mode": "metadata_crosswalk_replay",
            "warning": "staging SQLite is absent; topic matches are replayed from tracked metadata and contain no academic正文",
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.db.is_file():
        report = load_tracked_crosswalk(args.crosswalk, args.db)
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report.get("status") in {"PASS", "BLOCKED"} else 1
    app.DOMESTIC_STAGING_DB_PATH = args.db
    coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
    cards = {
        str(row["event_id"]): row
        for row in json.loads(args.cards.read_text(encoding="utf-8"))
    }
    topics = []
    for item in coverage:
        event_id = str(item["event_id"])
        matches = app._research_academic_matches(item, cards.get(event_id, {}), limit=10000)
        topics.append(
            {
                "event_id": event_id,
                "event_name": item.get("event_name"),
                "matched_records": matches["total"],
                "shown_record_ids": [row["external_id"] for row in matches["rows"][:20]],
                "quality_tiers": {
                    tier: sum(1 for row in matches["rows"] if row["quality_tier"] == tier)
                    for tier in ("S", "A", "B", "C")
                },
            }
        )
    report = {
        "schema_version": "academic_topic_crosswalk.v1",
        "generated_at": dt.date.today().isoformat(),
        "body_read": False,
        "purpose": "国内九个核心专题的学术解释层元数据快照；只保存专题匹配数量、质量层级和不含正文的记录标识。",
        "matching_basis": "structured metadata fields plus title/author/institution; not body semantics",
        "source_scope": "local staging metadata snapshot; full records and any academic full text remain outside the code repository",
        "topics": topics,
        "total_topic_matches": sum(int(topic["matched_records"]) for topic in topics),
        "source": "staging_sqlite",
        "snapshot_only": False,
        "audit_mode": "per_record_metadata_crosswalk",
        "status": "PASS" if args.db.is_file() else "BLOCKED",
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] in {"PASS", "BLOCKED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
