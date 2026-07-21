#!/usr/bin/env python3
"""Validate domestic candidate JSONL without touching SQLite or source files."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = {
    "candidate_id",
    "title",
    "repository_code",
    "repository_name",
    "access_mode",
    "rights_status",
    "authenticity_level_proposed",
    "relevance_grade_proposed",
    "evidence_note",
    "uncertainty_note",
    "checked_at",
    "checked_by",
    "review_status",
}

ENUMS = {
    "access_mode": {"open", "login", "reading_room", "offline", "unknown"},
    "rights_status": {"public", "internal", "restricted", "unknown"},
    "authenticity_level_proposed": {"L0", "L1", "L2", "L3", "L4", "LX"},
    "relevance_grade_proposed": {"core", "related", "person", "background", "exclude", "unknown"},
    "catalog_reference_status": {"verified", "unpublished", "not_found", "pending", "unknown"},
    "source_url_role": {"item_digital", "item_surrogate", "finding_aid", "bibliography", "institution_home", "none", "unknown"},
    "medium": {"physical", "digital", "hybrid", "unknown"},
    "online_availability": {"full_item_online", "surrogate_online", "catalogue_only_online", "not_online", "unknown"},
    "reuse_rights": {"public_domain", "open_license", "citation_only", "no_republication", "unknown"},
    "copy_allowed": {"yes", "no", "unknown"},
    "evidence_type": {"catalogue", "official_description", "digital_image", "printed_finding_aid", "secondary_lead", "unknown"},
    "checked_by": {"minimax", "grok", "codex", "human", "claude-code"},
    "review_status": {"candidate", "needs_human_review", "accepted", "rejected", "duplicate"},
    "reviewed_by": {"minimax", "grok", "codex", "human", "claude-code"},
    "check_outcome": {"pass", "fail", "needs_info", "deferred", "unknown"},
    # v2 新增字段
    "transcription_status": {"none", "partial", "full", "validated"},
    "transcription_confidence": {"high", "medium", "low"},
    "access_audit_status": {"ok", "redirect", "paywall", "archived", "failed", "unknown"},
}


def validate(row: dict[str, object]) -> list[str]:
    errors: list[str] = []
    for key in sorted(REQUIRED):
        if key not in row:
            errors.append(f"missing {key}")
    for key, allowed in ENUMS.items():
        if key in row and row[key] not in allowed:
            errors.append(f"{key}={row[key]!r} is not one of {sorted(allowed)}")
    if not isinstance(row.get("candidate_id"), str) or len(str(row.get("candidate_id", ""))) < 3:
        errors.append("candidate_id must be a string of length >= 3")
    if not isinstance(row.get("title"), str) or not str(row.get("title", "")).strip():
        errors.append("title must be non-empty")
    if "source_url" in row:
        value = row["source_url"]
        parsed = urlparse(str(value))
        if not isinstance(value, str) or parsed.scheme not in {"http", "https"} or not parsed.netloc:
            errors.append("source_url must be an http(s) URL")
    access_mode = row.get("access_mode")
    if access_mode in {"offline", "reading_room"}:
        for key in ("catalog_reference", "catalog_reference_status", "access_note"):
            if not str(row.get(key, "")).strip():
                errors.append(f"{key} is required for {access_mode} records")
    if row.get("online_availability") in {"full_item_online", "surrogate_online"}:
        if "source_url" not in row or "source_url_role" not in row:
            errors.append("online availability requires source_url and source_url_role")
    if row.get("authenticity_level_proposed") == "L0":
        for key in ("catalog_reference", "catalog_reference_status", "evidence_type", "evidence_locator"):
            if not str(row.get(key, "")).strip():
                errors.append(f"{key} is required for L0 records")
    if row.get("review_status") == "accepted":
        for key in ("check_outcome", "authenticity_level_accepted", "relevance_grade_accepted", "reviewed_at", "reviewed_by"):
            if key not in row or row[key] in (None, ""):
                errors.append(f"{key} is required for accepted records")
        if row.get("check_outcome") != "pass":
            errors.append("accepted records require check_outcome=pass")
    if row.get("review_status") in {"rejected", "duplicate"} and not str(row.get("review_note", "")).strip():
        errors.append("review_note is required for rejected or duplicate records")
    # v2 新增字段 conditional 校验
    transcription_status = row.get("transcription_status")
    if transcription_status in {"partial", "full", "validated"}:
        if not str(row.get("transcription_text_path", "")).strip():
            errors.append(f"transcription_text_path is required for transcription_status={transcription_status}")
    if transcription_status == "validated":
        if "access_audit_date" not in row or not str(row.get("access_audit_date", "")).strip():
            errors.append("access_audit_date is required for transcription_status=validated")
        if "access_audit_status" not in row or row.get("access_audit_status") is None:
            errors.append("access_audit_status is required for transcription_status=validated")
    # citation_key 格式校验 (如有, 必须符合 pattern)
    citation_key = row.get("citation_key")
    if citation_key is not None:
        import re
        if not re.match(r"^[a-z0-9_-]{4,80}$", str(citation_key)):
            errors.append(f"citation_key={citation_key!r} must match ^[a-z0-9_-]{{4,80}}$")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    args = parser.parse_args()
    total = 0
    failed = 0
    with args.jsonl.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            total += 1
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                print(f"line {line_no}: invalid JSON: {exc}", file=sys.stderr)
                failed += 1
                continue
            if not isinstance(row, dict):
                print(f"line {line_no}: record must be an object", file=sys.stderr)
                failed += 1
                continue
            errors = validate(row)
            if errors:
                failed += 1
                for error in errors:
                    print(f"line {line_no}: {error}", file=sys.stderr)
    print(json.dumps({"records": total, "failed": failed, "passed": total - failed}, ensure_ascii=False))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
