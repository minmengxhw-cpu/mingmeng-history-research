#!/usr/bin/env python3
"""Read the latest closeout snapshot without rerunning any expensive checks.

This is the low-cost monitor entry point.  It reads one metadata-only JSON
snapshot, emits a small safe status object, and never opens the SQLite
database, page bodies, source files, or images.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SNAPSHOT = ROOT / "work" / "domestic" / "closeout_snapshot_current" / "REPORT.json"
DEFAULT_MAX_AGE_SECONDS = 3600


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def safe_missing_fields(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for field in value:
        name = str(field)
        if "path" in name.lower() or name in {"source_file", "page_image_path"}:
            result.append("file_mapping")
        else:
            result.append(name)
    return sorted(set(result))


def safe_target_statuses(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    result: list[dict[str, Any]] = []
    for row in value:
        if not isinstance(row, dict) or not row.get("target_id"):
            continue
        result.append(
            {
                "target_id": row.get("target_id"),
                "status": row.get("status", "UNKNOWN"),
                "missing_fields": safe_missing_fields(row.get("missing_fields")),
            }
        )
    return result


def snapshot_age_seconds(value: Any, *, now: dt.datetime | None = None) -> int | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        generated = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if generated.tzinfo is None:
        generated = generated.replace(tzinfo=dt.timezone.utc)
    current = now or dt.datetime.now(dt.timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=dt.timezone.utc)
    return max(0, int((current - generated).total_seconds()))


def build_status(
    snapshot: dict[str, Any],
    *,
    now: dt.datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> dict[str, Any]:
    if snapshot.get("schema_version") != "domestic_platform_closeout_snapshot.v1":
        raise ValueError("unsupported snapshot schema")
    platform = snapshot.get("platform")
    intake = snapshot.get("p0_intake")
    safety = snapshot.get("safety")
    if not isinstance(platform, dict) or not isinstance(intake, dict) or not isinstance(safety, dict):
        raise ValueError("incomplete snapshot")
    age = snapshot_age_seconds(snapshot.get("generated_at"), now=now)
    freshness = "UNKNOWN" if age is None else ("FRESH" if age <= max(0, max_age_seconds) else "STALE")
    overall_status = {
        "FRESH": "OK",
        "STALE": "STALE_SNAPSHOT",
        "UNKNOWN": "SNAPSHOT_TIMESTAMP_UNKNOWN",
    }[freshness]
    return {
        "schema_version": "domestic_platform_quick_status.v1",
        "status": overall_status,
        "observed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "snapshot_generated_at": snapshot.get("generated_at"),
        "snapshot_age_seconds": age,
        "snapshot_freshness": freshness,
        "platform": {
            "status": platform.get("status", "UNKNOWN"),
            "research_content_status": platform.get("research_content_status", "UNKNOWN"),
            "failed_check_count": len(platform.get("failed_checks", []))
            if isinstance(platform.get("failed_checks", []), list)
            else 0,
        },
        "p0_intake": {
            "status": intake.get("status", "UNKNOWN"),
            "target_count": intake.get("target_count", 0),
            "incoming_file_count": intake.get("incoming_file_count", 0),
            "mapping_count": intake.get("mapping_count", 0),
            "target_statuses": safe_target_statuses(intake.get("target_statuses")),
        },
        "safety": {
            "body_read": safety.get("body_read") is True,
            "formal_db_written": safety.get("formal_db_written") is True,
            "sources_downloaded": safety.get("sources_downloaded") is True,
            "files_deleted_or_moved": safety.get("files_deleted_or_moved") is True,
            "auto_delete": safety.get("auto_delete") is True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--max-age-seconds", type=int, default=DEFAULT_MAX_AGE_SECONDS)
    args = parser.parse_args()
    snapshot = load_json(args.snapshot.expanduser().resolve())
    if snapshot is None:
        print(json.dumps({"schema_version": "domestic_platform_quick_status.v1", "status": "MISSING_OR_INVALID_SNAPSHOT"}))
        return 1
    try:
        status = build_status(snapshot, max_age_seconds=args.max_age_seconds)
    except ValueError:
        print(json.dumps({"schema_version": "domestic_platform_quick_status.v1", "status": "MISSING_OR_INVALID_SNAPSHOT"}))
        return 1
    print(json.dumps(status, ensure_ascii=False))
    return 0 if status["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
