#!/usr/bin/env python3
"""Audit Grok GAP_WAVE2 page chains without changing source data or SQLite."""

from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WAVE = ROOT / "work" / "domestic" / "grok_next_stage_20260730" / "10_gap_wave2_period_page_chain"
CHAIN_PATH = WAVE / "PAGE_EVIDENCE_CHAINS.jsonl"
DOC_INDEX_PATH = WAVE / "DOCUMENT_VERIFICATION_INDEX.jsonl"
REPORT_PATH = WAVE / "CODEX_AUDIT_REPORT.json"
CONFLICT_PATH = WAVE / "CODEX_PHASE_CONFLICTS.jsonl"

YEAR_RE = re.compile(r"(?<!\d)(19\d{2})(?!\d)")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def years_in(*values: str) -> set[str]:
    return {year for value in values if value for year in YEAR_RE.findall(value)}


def main() -> None:
    rows = [json.loads(line) for line in CHAIN_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    source_sha_cache: dict[Path, str] = {}
    image_sha_cache: dict[Path, str] = {}
    missing = Counter()
    mismatches = Counter()
    phase_rows = Counter()
    phase_sources: defaultdict[str, set[str]] = defaultdict(set)
    conflicts: list[dict] = []

    for row in rows:
        source = ROOT / row["source_file"]
        image = ROOT / row["page_image_path"]
        ocr = ROOT / row["ocr_md_path"]
        for kind, path in (("source", source), ("image", image), ("ocr", ocr)):
            if not path.exists():
                missing[kind] += 1
        if source.exists():
            if source not in source_sha_cache:
                source_sha_cache[source] = sha256(source)
            if source_sha_cache[source] != row.get("source_sha256"):
                mismatches["source_sha256"] += 1
        if image.exists():
            if image not in image_sha_cache:
                image_sha_cache[image] = sha256(image)
            if image_sha_cache[image] != row.get("page_image_sha256"):
                mismatches["page_image_sha256"] += 1

        phase = row.get("historical_phase") or "unknown"
        phase_rows[phase] += 1
        phase_sources[phase].add(row.get("source_id", ""))
        if phase == "1942-1943":
            source_years = years_in(row.get("source_title", ""), row.get("source_file", ""))
            # A row labelled 1942-1943 but explicitly naming 1941 cannot be
            # used to close the 1942-1943 original-source gap.
            if "1941" in source_years and not ({"1942", "1943"} & source_years):
                conflicts.append(
                    {
                        "source_id": row.get("source_id"),
                        "source_title": row.get("source_title"),
                        "source_file": row.get("source_file"),
                        "physical_page_no": row.get("physical_page_no"),
                        "declared_phase": phase,
                        "detected_years": sorted(source_years),
                        "status": "PHASE_LABEL_CONFLICT_REVIEW_REQUIRED",
                        "reason": "title_or_path_explicitly_identifies_1941",
                    }
                )

    doc_rows = [json.loads(line) for line in DOC_INDEX_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    page_ready = sum(1 for row in doc_rows if row.get("verification_status") == "PAGE_CHAIN_READY")
    report = {
        "report": "CODEX_GROK_GAP_WAVE2_PAGE_CHAIN_AUDIT_20260730",
        "input": str(CHAIN_PATH.relative_to(ROOT)),
        "page_chain_rows": len(rows),
        "unique_source_documents": len({row.get("source_id") for row in rows}),
        "machine_complete_declared": sum(1 for row in rows if row.get("chain_complete_machine") is True),
        "document_page_chain_ready": page_ready,
        "missing_asset_counts": dict(missing),
        "sha_mismatch_counts": dict(mismatches),
        "phase_row_counts": dict(phase_rows),
        "phase_source_counts": {phase: len(source_ids) for phase, source_ids in phase_sources.items()},
        "declared_1942_1943_rows": phase_rows.get("1942-1943", 0),
        "declared_1942_1943_sources": len(phase_sources.get("1942-1943", set())),
        "1942_1943_phase_conflict_rows": len(conflicts),
        "1942_1943_phase_conflict_sources": len({row["source_id"] for row in conflicts}),
        "clean_1942_1943_rows_for_core_gap": phase_rows.get("1942-1943", 0) - len(conflicts),
        "formal_db_written": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "rule": "page-chain completeness is separate from historical-phase correctness; conflicts remain review-only",
    }
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with CONFLICT_PATH.open("w", encoding="utf-8") as handle:
        for row in conflicts:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
