#!/usr/bin/env python3
"""Validate one metadata-only domestic research packet.

The validator rebuilds the packet from the formal database and checks its
evidence boundaries.  It does not write to SQLite and does not export page
body text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.domestic.research_packet import build_research_packet  # noqa: E402


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_packet(packet: dict[str, object], event_id: str) -> dict[str, object]:
    errors: list[str] = []
    audit = packet.get("audit") or {}
    if audit.get("body_text_included") is not False:
        errors.append("body_text_included must be false")
    if audit.get("ocr_text_included") is not False:
        errors.append("ocr_text_included must be false")
    if audit.get("translation_text_included") is not False:
        errors.append("translation_text_included must be false")
    if audit.get("verbatim_quote_included") is not False:
        errors.append("verbatim_quote_included must be false")
    if audit.get("research_matrix_body_text_included") is not False:
        errors.append("research_matrix_body_text_included must be false")
    if audit.get("foreign_crosswalk_body_text_included") is not False:
        errors.append("foreign_crosswalk_body_text_included must be false")
    packet_counts = packet.get("counts") or {}
    research_tracks = packet.get("research_tracks") or []
    if not isinstance(research_tracks, list):
        errors.append("research_tracks must be a list")
        research_tracks = []
    if len(research_tracks) != packet_counts.get("research_track_count"):
        errors.append("research track count mismatch")
    if audit.get("research_track_count") != len(research_tracks):
        errors.append("research track audit count mismatch")
    if audit.get("research_tracks_body_text_included") is not False:
        errors.append("research tracks must not include body text")
    for track in research_tracks:
        if not isinstance(track, dict):
            errors.append("research track entry is not an object")
            continue
        if track.get("event_id") != event_id:
            errors.append(f"research track {track.get('track_id')} has wrong event_id")
        if track.get("primary_evidence_closed") is not False:
            errors.append(f"research track {track.get('track_id')} closes primary evidence")
        if track.get("body_text_included") is not False:
            errors.append(f"research track {track.get('track_id')} exports body text")
        if not track.get("track_id") or not track.get("title"):
            errors.append("research track missing track_id or title")
        if not isinstance(track.get("candidate_ids"), list):
            errors.append(f"research track {track.get('track_id')} candidate_ids must be a list")
        if not isinstance(track.get("lead_refs"), list):
            errors.append(f"research track {track.get('track_id')} lead_refs must be a list")
    matrix = packet.get("research_matrix") or {}
    matrix_questions = matrix.get("questions") if isinstance(matrix, dict) else []
    if not isinstance(matrix_questions, list):
        errors.append("research_matrix.questions must be a list")
        matrix_questions = []
    if len(matrix_questions) != audit.get("research_matrix_questions"):
        errors.append("research matrix question count mismatch")
    for question in matrix_questions:
        if question.get("body_text_included") is not False:
            errors.append(f"matrix question {question.get('id')} exports body text")
        if not question.get("id") or not question.get("question"):
            errors.append("matrix question missing id or question")
    crosswalk = packet.get("foreign_crosswalk") or {}
    crosswalk_questions = crosswalk.get("questions") if isinstance(crosswalk, dict) else {}
    if not isinstance(crosswalk_questions, dict):
        errors.append("foreign_crosswalk.questions must be a mapping")
        crosswalk_questions = {}
    if len(crosswalk_questions) != audit.get("foreign_crosswalk_questions"):
        errors.append("foreign crosswalk question count mismatch")
    if matrix_questions and set(item.get("id") for item in matrix_questions) != set(crosswalk_questions):
        errors.append("foreign crosswalk must cover exactly the matrix questions")
    for question_id, item in crosswalk_questions.items():
        if item.get("body_text_included") is not False:
            errors.append(f"foreign crosswalk {question_id} exports body text")
        if not item.get("relationship") or not item.get("relationship_label"):
            errors.append(f"foreign crosswalk {question_id} missing relationship")
    chain = packet.get("evidence_chain") or {}
    rows = [row for values in chain.values() for row in values]
    counts = packet.get("counts") or {}
    if len(rows) != counts.get("evidence_chain_page_items"):
        errors.append("page item count mismatch")
    if sum(bool(row.get("resolved")) for row in rows) != counts.get("evidence_chain_resolved_page_items"):
        errors.append("resolved page count mismatch")
    if not audit.get("page_rows_all_resolved"):
        errors.append("not all evidence page rows resolved")
    topic_rows = packet.get("topic_event_pages") or []
    counts = packet.get("counts") or {}
    if len(topic_rows) != counts.get("topic_event_sample_rows"):
        errors.append("topic event sample count mismatch")
    for row in topic_rows:
        if row.get("body_text_included") is not False:
            errors.append(f"topic event page {row.get('page_id')} exports body text")
        if not row.get("page_id") or not row.get("reader_url"):
            errors.append("topic event row missing page link")
    sourcebooks = packet.get("sourcebooks") or []
    if not isinstance(sourcebooks, list):
        errors.append("sourcebooks must be a list")
        sourcebooks = []
    if len(sourcebooks) != audit.get("sourcebook_count"):
        errors.append("sourcebook count mismatch")
    if sum(len(item.get("targets") or []) for item in sourcebooks if isinstance(item, dict)) != audit.get("sourcebook_target_count"):
        errors.append("sourcebook target count mismatch")
    for sourcebook in sourcebooks:
        if not isinstance(sourcebook, dict):
            errors.append("sourcebook entry is not an object")
            continue
        if sourcebook.get("body_text_included") is not False:
            errors.append(f"sourcebook {sourcebook.get('source_id')} exports body text")
        if sourcebook.get("raw_pdf_included") is not False:
            errors.append(f"sourcebook {sourcebook.get('source_id')} exports raw PDF")
        if len(str(sourcebook.get("source_sha256") or "")) != 64:
            errors.append(f"sourcebook {sourcebook.get('source_id')} missing source SHA256")
        if not sourcebook.get("target_map_url"):
            errors.append(f"sourcebook {sourcebook.get('source_id')} missing target map URL")
        for target in sourcebook.get("targets") or []:
            if not isinstance(target, dict) or target.get("body_text_included") is not False:
                errors.append(f"sourcebook {sourcebook.get('source_id')} target exports body text")
    fragments = packet.get("citation_fragments") or []
    if not isinstance(fragments, list):
        errors.append("citation_fragments must be a list")
        fragments = []
    if len(fragments) != counts.get("citation_fragment_count"):
        errors.append("citation fragment count mismatch")
    if audit.get("citation_fragment_count") != len(fragments):
        errors.append("citation fragment audit count mismatch")
    if audit.get("citation_fragment_text_included") is not False:
        errors.append("citation fragment text must not be included in packet")
    for fragment in fragments:
        if not isinstance(fragment, dict):
            errors.append("citation fragment entry is not an object")
            continue
        if fragment.get("body_text_included") is not False:
            errors.append(f"citation fragment {fragment.get('fragment_id')} exports body text")
        if fragment.get("fragment_text_included") is not False:
            errors.append(f"citation fragment {fragment.get('fragment_id')} exports fragment text")
        if fragment.get("fragment_citation_ready") is not True:
            errors.append(f"citation fragment {fragment.get('fragment_id')} is not fragment-ready")
        if fragment.get("page_citation_ready") is not False:
            errors.append(f"citation fragment {fragment.get('fragment_id')} promotes page citation")
        if len(str(fragment.get("source_sha256") or "")) != 64:
            errors.append(f"citation fragment {fragment.get('fragment_id')} missing source SHA256")
        if not fragment.get("citation_url") or not fragment.get("ledger_url"):
            errors.append(f"citation fragment {fragment.get('fragment_id')} missing navigation links")
    source_maps = packet.get("event_source_maps") or []
    if not isinstance(source_maps, list):
        errors.append("event_source_maps must be a list")
        source_maps = []
    if len(source_maps) != audit.get("event_source_map_count"):
        errors.append("event source map count mismatch")
    source_page_count = 0
    for source_map in source_maps:
        if not isinstance(source_map, dict):
            errors.append("event source map entry is not an object")
            continue
        if source_map.get("body_text_included") is not False:
            errors.append(f"event source map {source_map.get('event_id')} exports body text")
        if source_map.get("ocr_text_included") is not False:
            errors.append(f"event source map {source_map.get('event_id')} exports OCR text")
        if source_map.get("raw_files_included") is not False:
            errors.append(f"event source map {source_map.get('event_id')} exports raw files")
        if source_map.get("primary_evidence_closed") is not False:
            errors.append(f"event source map {source_map.get('event_id')} must keep primary gap open")
        sources = source_map.get("sources") or []
        if not isinstance(sources, list):
            errors.append(f"event source map {source_map.get('event_id')} sources must be a list")
            continue
        for source in sources:
            if not isinstance(source, dict):
                errors.append("event source map source is not an object")
                continue
            source_sha = str(source.get("source_sha256") or "")
            metadata_sha = str(source.get("metadata_snapshot_sha256") or "")
            pages = source.get("page_records") or []
            route_only_source = (
                str(source.get("source_role") or "") in {
                    "official_curated_reproduction",
                    "official_archive_image",
                    "public_facsimile_ocr_transcription",
                    "public_periodical_scan_route",
                }
                and not source.get("source_file")
                and not source.get("metadata_snapshot_file")
                and not pages
                and any(
                    str(source.get(key) or "").startswith(("http://", "https://"))
                    for key in ("source_url", "image_url")
                )
            )
            if len(source_sha) != 64 and not route_only_source:
                snapshot_file = str(source.get("metadata_snapshot_file") or "")
                if len(metadata_sha) != 64 or not snapshot_file:
                    errors.append(f"event source {source.get('source_id')} missing source or metadata snapshot SHA256")
                else:
                    snapshot_path = ROOT / snapshot_file
                    if not snapshot_path.is_file():
                        errors.append(f"event source {source.get('source_id')} metadata snapshot is missing")
                    else:
                        try:
                            if _sha256(snapshot_path) != metadata_sha:
                                errors.append(f"event source {source.get('source_id')} metadata snapshot SHA256 mismatch")
                        except OSError as exc:
                            errors.append(f"event source {source.get('source_id')} metadata snapshot unreadable: {exc}")
            if not isinstance(pages, list):
                errors.append(f"event source {source.get('source_id')} page_records must be a list")
                continue
            source_page_count += len(pages)
            for page in pages:
                if not isinstance(page, dict):
                    errors.append(f"event source {source.get('source_id')} page record is not an object")
                    continue
                if page.get("page_id") is not None and not str(page.get("page_id")).isdigit():
                    errors.append(f"event source {source.get('source_id')} page id is invalid")
                if page.get("status") == "strict_citation" and page.get("citation_ready") is not True:
                    errors.append(f"event source {source.get('source_id')} strict page is not citation ready")
                if page.get("status") == "negative_control" and page.get("citation_ready") is not False:
                    errors.append(f"event source {source.get('source_id')} negative page must not be citation ready")
    if source_page_count != audit.get("event_source_page_record_count"):
        errors.append("event source page record count mismatch")
    for row in rows:
        if not row.get("page_id"):
            errors.append("evidence row missing page_id")
        if row.get("resolved") and not row.get("source_sha256"):
            errors.append(f"page {row.get('page_id')} missing source SHA256")
        if row.get("status") == "strict_citation" and not row.get("citation_gate_passed"):
            errors.append(f"page {row.get('page_id')} strict row failed citation gate")
        if row.get("body_text_included") is not False:
            errors.append(f"page {row.get('page_id')} exports body text")
    return {
        "event_id": event_id,
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "counts": counts,
        "database_sha256": (packet.get("database") or {}).get("sha256", ""),
    }


def validate(event_id: str) -> dict[str, object]:
    packet = build_research_packet(event_id)
    if packet is None:
        return {"event_id": event_id, "status": "FAIL", "errors": ["packet not found"]}
    return validate_packet(packet, event_id)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("event_id")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.event_id)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
