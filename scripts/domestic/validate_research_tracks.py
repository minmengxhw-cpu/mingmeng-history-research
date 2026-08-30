#!/usr/bin/env python3
"""Validate declaration-only research tracks attached to fixed topics.

Research tracks are presentation and retrieval metadata.  They do not create
new formal events, copy page bodies, promote primary evidence, or authorize
OCR/deletion.  The validator keeps the pre-dissolution history layer attached
to an existing nine-topic event until an independently sourced event mapping
is ready.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TRACKS = ROOT / "data" / "domestic" / "research_tracks.json"
DEFAULT_COVERAGE = ROOT / "data" / "domestic" / "event_coverage.json"
DEFAULT_CANDIDATES = ROOT / "data" / "domestic" / "candidates.jsonl"
DEFAULT_LEADS_DIR = ROOT / "data" / "domestic"

REQUIRED_TRACK_FIELDS = {
    "track_id",
    "event_id",
    "track_role",
    "title",
    "period",
    "status",
    "primary_evidence_closed",
    "research_question",
    "candidate_ids",
    "lead_refs",
    "evidence_boundary",
    "processing_policy",
    "next_action",
}
REQUIRED_LEAD_FIELDS = {"lead_id", "title", "evidence_level", "role", "url"}
LOCAL_MARKERS = (
    "/Users/",
    "/private/",
    "/tmp/",
    "file://",
    "data/",
    "work/",
    "local_path",
    "source_file",
    "page_image_path",
)


def read_jsonl_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if isinstance(item, dict) and item.get("candidate_id"):
                ids.add(str(item["candidate_id"]))
    return ids


def read_lead_records(directory: Path) -> tuple[dict[str, dict[str, Any]], list[str]]:
    records: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    paths = sorted(directory.glob("collection_leads_*.jsonl"))
    if not paths:
        errors.append("lead catalog has no collection_leads_*.jsonl files")
    for path in paths:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:
            errors.append(f"lead catalog unreadable: {path.name}: {exc}")
            continue
        for line_number, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"lead catalog invalid JSON: {path.name}:{line_number}: {exc}")
                continue
            if not isinstance(item, dict) or not item.get("lead_id"):
                continue
            lead_id = str(item["lead_id"])
            if lead_id in records:
                errors.append(f"duplicate lead catalog id: {lead_id}")
                continue
            records[lead_id] = item
    return records, errors


def validate(
    tracks_path: Path,
    coverage_path: Path,
    candidates_path: Path,
    leads_dir: Path = DEFAULT_LEADS_DIR,
) -> dict[str, Any]:
    errors: list[str] = []
    try:
        payload = json.loads(tracks_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"tracks unreadable: {exc}"]}
    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
        coverage_ids = {
            str(item.get("event_id"))
            for item in coverage
            if isinstance(item, dict) and item.get("event_id")
        }
    except (OSError, json.JSONDecodeError) as exc:
        return {"status": "FAIL", "errors": [f"coverage unreadable: {exc}"]}
    try:
        candidate_ids = read_jsonl_ids(candidates_path)
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        return {"status": "FAIL", "errors": [f"candidates unreadable: {exc}"]}
    lead_catalog, lead_catalog_errors = read_lead_records(leads_dir)
    errors.extend(lead_catalog_errors)

    if payload.get("schema") != "domestic_research_tracks.v1":
        errors.append("unsupported research track schema")
    for field in ("body_read", "formal_db_written", "auto_delete"):
        if payload.get(field) is not False:
            errors.append(f"tracks {field} must be false")
    tracks = payload.get("tracks")
    if not isinstance(tracks, list) or not tracks:
        errors.append("tracks must be a non-empty list")
        tracks = []

    track_ids: set[str] = set()
    lead_ids: set[str] = set()
    candidate_ref_count = 0
    for index, track in enumerate(tracks):
        if not isinstance(track, dict):
            errors.append(f"track[{index}] is not an object")
            continue
        missing = sorted(REQUIRED_TRACK_FIELDS - set(track))
        errors.extend(f"track[{index}] missing {field}" for field in missing)
        track_id = str(track.get("track_id") or "")
        if not track_id:
            errors.append(f"track[{index}] empty track_id")
        elif track_id in track_ids:
            errors.append(f"duplicate track_id: {track_id}")
        track_ids.add(track_id)
        event_id = str(track.get("event_id") or "")
        if event_id not in coverage_ids:
            errors.append(f"track[{index}] attaches to unknown event_id: {event_id}")
        if track.get("primary_evidence_closed") is not False:
            errors.append(f"track[{index}] primary_evidence_closed must be false")
        for field in REQUIRED_TRACK_FIELDS - {"candidate_ids", "lead_refs", "primary_evidence_closed"}:
            if field in track and not str(track.get(field) or "").strip():
                errors.append(f"track[{index}] empty {field}")
        refs = track.get("candidate_ids")
        if not isinstance(refs, list) or not refs:
            errors.append(f"track[{index}] candidate_ids must be a non-empty list")
        else:
            for candidate_id in refs:
                candidate_ref_count += 1
                if str(candidate_id) not in candidate_ids:
                    errors.append(f"track[{index}] unknown candidate_id: {candidate_id}")
        leads = track.get("lead_refs")
        if not isinstance(leads, list) or not leads:
            errors.append(f"track[{index}] lead_refs must be a non-empty list")
        else:
            for lead_index, lead in enumerate(leads):
                if not isinstance(lead, dict):
                    errors.append(f"track[{index}] lead[{lead_index}] is not an object")
                    continue
                errors.extend(
                    f"track[{index}] lead[{lead_index}] missing {field}"
                    for field in sorted(REQUIRED_LEAD_FIELDS - set(lead))
                )
                lead_id = str(lead.get("lead_id") or "")
                if lead_id in lead_ids:
                    errors.append(f"duplicate lead_id: {lead_id}")
                lead_ids.add(lead_id)
                url = str(lead.get("url") or "")
                if not url.startswith(("https://", "http://")):
                    errors.append(f"track[{index}] lead[{lead_index}] url must be http(s)")
                catalog_record = lead_catalog.get(lead_id)
                if catalog_record is None:
                    errors.append(f"track[{index}] lead_id is absent from local lead catalog: {lead_id}")
                else:
                    catalog_urls = {
                        str(catalog_record.get(key) or "").strip()
                        for key in ("origin_url", "landing_url", "download_url")
                    }
                    if url and url not in catalog_urls:
                        errors.append(f"track[{index}] lead URL does not match local lead catalog: {lead_id}")

    serialized = json.dumps(payload, ensure_ascii=False)
    for marker in LOCAL_MARKERS:
        if marker in serialized:
            errors.append(f"tracks contain forbidden local marker: {marker}")
    return {
        "status": "PASS" if not errors else "FAIL",
        "tracks_path": str(tracks_path),
        "coverage_topics": len(coverage_ids),
        "track_count": len(tracks),
        "candidate_reference_count": candidate_ref_count,
        "lead_reference_count": len(lead_ids),
        "lead_catalog_count": len(lead_catalog),
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tracks", type=Path, default=DEFAULT_TRACKS)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--candidates", type=Path, default=DEFAULT_CANDIDATES)
    parser.add_argument("--leads-dir", type=Path, default=DEFAULT_LEADS_DIR)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.tracks, args.coverage, args.candidates, args.leads_dir)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
