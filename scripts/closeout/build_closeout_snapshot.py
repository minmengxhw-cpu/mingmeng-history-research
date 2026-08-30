#!/usr/bin/env python3
"""Build a compact, metadata-only snapshot of the domestic platform gates.

The snapshot is an operational handoff artifact.  It runs the existing
validators, keeps infrastructure status separate from research-content
closure, and records the P0 intake state without reading page bodies, writing
the formal SQLite database, downloading sources, or deleting local files.
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
DB_PATH = ROOT / "data" / "research_index.sqlite"
CANDIDATES_PATH = ROOT / "data" / "domestic" / "candidates.jsonl"
COVERAGE_PATH = ROOT / "data" / "domestic" / "event_coverage.json"
RESEARCH_TRACKS_PATH = ROOT / "data" / "domestic" / "research_tracks.json"
ACADEMIC_METADATA_PATH = ROOT / "data" / "domestic" / "academic_layer_metadata.json"
ACADEMIC_QUEUE_PATH = ROOT / "data" / "domestic" / "academic_fulltext_priority_queue.json"
SIBLING_QUEUE_PATH = ROOT / "data" / "domestic" / "sibling_collection_intake_queue.json"
PRIMARY_ACCESS_AUDIT_PATH = ROOT / "data" / "domestic" / "primary_evidence_access_audit.json"
CONTENT_TIER_REPORT_GLOB = ROOT / "work" / "domestic" / "content_tier_audit_*" / "REPORT.json"
P0_REPORT_PATH = ROOT / "work" / "domestic" / "authorized_original_intake_20260821" / "REPORT.json"
P0_MANIFEST_PATH = ROOT / "work" / "domestic" / "authorized_original_intake_20260821" / "INTAKE_MANIFEST.jsonl"


def load_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return default


def load_p0_target_statuses(path: Path = P0_MANIFEST_PATH) -> list[dict[str, Any]]:
    """Read only safe target-level intake metadata, never local paths or bodies."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []

    statuses: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(row, dict) or not row.get("target_id"):
            continue
        missing = row.get("missing_fields")
        safe_missing: list[str] = []
        if isinstance(missing, list):
            for field in missing:
                name = str(field)
                if "path" in name.lower() or name in {"source_file", "page_image_path"}:
                    safe_missing.append("file_mapping")
                else:
                    safe_missing.append(name)
        statuses.append(
            {
                "target_id": row.get("target_id"),
                "status": row.get("status", "UNKNOWN"),
                "missing_fields": sorted(set(safe_missing)),
            }
        )
    return statuses


def compact_result(result: dict[str, Any], fields: tuple[str, ...] = ()) -> dict[str, Any]:
    """Keep validator output useful without copying machine paths or bodies."""
    out: dict[str, Any] = {"status": result.get("status", "UNKNOWN")}
    for field in fields:
        if field in result:
            out[field] = result[field]
    errors = result.get("errors")
    if isinstance(errors, list):
        out["error_count"] = len(errors)
        if errors:
            out["errors"] = [str(item) for item in errors[:5]]
    return out


def p0_status(payload: dict[str, Any], target_count: int) -> str:
    explicit = str(payload.get("status") or "").strip()
    if explicit:
        return explicit
    counts = payload.get("status_counts")
    if isinstance(counts, dict) and target_count > 0:
        try:
            waiting = int(counts.get("WAITING_FOR_LOCAL_ORIGINAL") or 0)
        except (TypeError, ValueError):
            waiting = 0
        if waiting == target_count:
            return "WAITING_FOR_LOCAL_ORIGINAL"
    return "NOT_RUN"


def newest_content_tier_report() -> dict[str, Any]:
    candidates = [path for path in ROOT.glob("work/domestic/content_tier_audit_*/REPORT.json") if path.is_file()]
    valid: list[tuple[str, float, dict[str, Any]]] = []
    for path in candidates:
        payload = load_json(path, {})
        if not isinstance(payload, dict) or payload.get("schema_version") != "domestic_content_tier_audit.v1":
            continue
        try:
            mtime = path.stat().st_mtime
        except OSError:
            mtime = 0.0
        valid.append((str(payload.get("generated_at") or ""), mtime, payload))
    if not valid:
        return {}
    return max(valid, key=lambda item: (item[0], item[1]))[2]


def build_snapshot() -> dict[str, Any]:
    # Imports stay inside the function so --help and syntax checks do not
    # initialize the application or touch the database.
    from scripts.domestic.validate_academic_layer import validate as validate_academic
    from scripts.domestic.validate_primary_evidence_access_audit import validate as validate_primary_access
    from scripts.domestic.validate_research_tracks import validate as validate_tracks
    from scripts.domestic.validate_sibling_collection_intake import validate as validate_sibling
    from scripts.domestic.validate_unified_research_platform import build_report as build_unified_report

    unified = build_unified_report()
    academic = validate_academic(ACADEMIC_METADATA_PATH, ACADEMIC_QUEUE_PATH)
    sibling = validate_sibling(SIBLING_QUEUE_PATH)
    tracks = validate_tracks(RESEARCH_TRACKS_PATH, COVERAGE_PATH, CANDIDATES_PATH)
    primary = validate_primary_access(PRIMARY_ACCESS_AUDIT_PATH, DB_PATH, COVERAGE_PATH)

    p0_targets = load_json(ROOT / "data/domestic/authorized_original_intake_targets_20260821.json", {})
    target_rows = p0_targets.get("targets", []) if isinstance(p0_targets, dict) else []
    p0_report = load_json(P0_REPORT_PATH, {})
    if not isinstance(p0_report, dict):
        p0_report = {}

    content = newest_content_tier_report()
    layers = []
    for row in content.get("layers", []) if isinstance(content, dict) else []:
        if isinstance(row, dict):
            layers.append(
                {
                    "code": row.get("code"),
                    "documents": row.get("documents", 0),
                    "pages": row.get("pages", 0),
                }
            )

    return {
        "schema_version": "domestic_platform_closeout_snapshot.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "scope": "domestic_research_platform_operational_handoff",
        "safety": {
            "body_read": False,
            "formal_db_written": False,
            "sources_downloaded": False,
            "files_deleted_or_moved": False,
            "auto_delete": False,
        },
        "platform": {
            "status": unified.get("status", "UNKNOWN"),
            "research_content_status": unified.get("research_content_status", "UNKNOWN"),
            "failed_checks": unified.get("failed_checks", []),
        },
        "checks": {
            "academic_layer": compact_result(academic, ("summary",)),
            "sibling_collection_intake": compact_result(
                sibling,
                ("queue_records", "unique_external_ids", "valid_sha256_count", "disposition_counts"),
            ),
            "research_tracks": compact_result(
                tracks,
                ("coverage_topics", "track_count", "candidate_reference_count", "lead_reference_count", "lead_catalog_count"),
            ),
            "primary_evidence_access": compact_result(
                primary,
                ("records", "body_read", "download_available", "local_original_present", "citation_ready"),
            ),
        },
        "content_tier": {
            "generated_at": content.get("generated_at") if isinstance(content, dict) else None,
            "status": content.get("status") if isinstance(content, dict) else "NOT_FOUND",
            "layers": layers,
        },
        "p0_intake": {
            "status": p0_status(p0_report, len(target_rows)),
            "target_count": len(target_rows),
            "incoming_file_count": p0_report.get("incoming_file_count", 0),
            "mapping_count": p0_report.get("mapping_count", 0),
            "status_counts": p0_report.get("status_counts", {}),
            "target_statuses": load_p0_target_statuses(),
        },
        "next_gate": {
            "condition": "authorized P0 originals with explicit mapping, SHA256, page identity, rights, and version relation",
            "targets_open": len(target_rows),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "work/domestic/closeout_snapshot_current/REPORT.json",
    )
    args = parser.parse_args()
    report = build_snapshot()
    output = args.output.expanduser().resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": report["platform"]["status"],
                "research_content_status": report["platform"]["research_content_status"],
                "p0_status": report["p0_intake"]["status"],
                "failed_checks": report["platform"]["failed_checks"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["platform"]["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
