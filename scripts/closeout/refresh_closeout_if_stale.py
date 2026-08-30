#!/usr/bin/env python3
"""Refresh the metadata-only closeout snapshot only when it is stale.

The command is intended for a low-cost local loop: a fresh snapshot is read
only, while a missing or stale snapshot invokes the existing closeout builder
and writes only the resulting report under ``work/``.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.closeout.read_closeout_status import (
    DEFAULT_MAX_AGE_SECONDS,
    DEFAULT_SNAPSHOT,
    build_status,
    load_json,
    snapshot_age_seconds,
)


def needs_refresh(
    snapshot: dict[str, Any] | None,
    *,
    now: dt.datetime | None = None,
    max_age_seconds: int = DEFAULT_MAX_AGE_SECONDS,
) -> bool:
    if snapshot is None or snapshot.get("schema_version") != "domestic_platform_closeout_snapshot.v1":
        return True
    age = snapshot_age_seconds(snapshot.get("generated_at"), now=now)
    return age is None or age > max(0, max_age_seconds)


def write_snapshot(path: Path, snapshot: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, default=DEFAULT_SNAPSHOT)
    parser.add_argument("--max-age-seconds", type=int, default=DEFAULT_MAX_AGE_SECONDS)
    parser.add_argument("--force", action="store_true", help="rebuild the snapshot even when it is fresh")
    args = parser.parse_args()

    snapshot_path = args.snapshot.expanduser().resolve()
    snapshot = load_json(snapshot_path)
    refreshed = bool(args.force or needs_refresh(snapshot, max_age_seconds=args.max_age_seconds))
    if refreshed:
        from scripts.closeout.build_closeout_snapshot import build_snapshot

        write_snapshot(snapshot_path, build_snapshot())

    latest = load_json(snapshot_path)
    if latest is None:
        print(json.dumps({"schema_version": "domestic_platform_quick_status.v1", "status": "MISSING_OR_INVALID_SNAPSHOT"}))
        return 1
    try:
        status = build_status(latest, max_age_seconds=args.max_age_seconds)
    except ValueError:
        print(json.dumps({"schema_version": "domestic_platform_quick_status.v1", "status": "MISSING_OR_INVALID_SNAPSHOT"}))
        return 1
    status["refresh_performed"] = refreshed
    print(json.dumps(status, ensure_ascii=False))
    return 0 if status["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
