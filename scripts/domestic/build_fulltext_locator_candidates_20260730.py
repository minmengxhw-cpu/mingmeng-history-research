#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build locator-only candidates for the seven crosswalk fulltext objects."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

try:
    import fitz  # type: ignore
except ImportError:
    fitz = None

ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = ROOT / "work/domestic/staging_20260730/claim_research_crosswalk/CROSSWALK.jsonl"
MATERIALS = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/MATERIALS.jsonl"
CONTENT = ROOT / "work/domestic/staging_20260730/crosswalk_fulltext_content_audit/CONTENT_SIGNALS.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/fulltext_locator_candidates"


def visible_html(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def norm(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def path_from(row: dict) -> Path:
    path = Path(row["local_path"])
    return path if path.is_absolute() else ROOT / path


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    materials = {
        row["material_external_id"]: row
        for row in (json.loads(line) for line in MATERIALS.read_text(encoding="utf-8").splitlines() if line.strip())
        if row.get("fulltext_status", "").startswith("FULLTEXT")
    }
    accepted_units = {
        material_id: set(material.get("matched_units", []))
        for material_id, material in materials.items()
    }
    content = {
        row["material_external_id"]: row
        for row in (json.loads(line) for line in CONTENT.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    page_cache: dict[str, list[str]] = {}
    cache_meta: dict[str, dict] = {}
    for material_id, material in materials.items():
        path = path_from(material)
        pages: list[str] = []
        if path.suffix.lower() == ".pdf" and fitz is not None and path.exists():
            doc = fitz.open(path)
            pages = [page.get_text("text") for page in doc]
            doc.close()
        elif path.suffix.lower() in {".html", ".htm"} and path.exists():
            pages = [visible_html(path.read_text(encoding="utf-8", errors="replace"))]
        page_cache[material_id] = pages
        cache_meta[material_id] = content.get(material_id, {})

    rows = []
    status_counts = Counter()
    locator_counts = Counter()
    for line in CROSSWALK.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        source = json.loads(line)
        material_id = source.get("material_external_id")
        if material_id not in materials:
            continue
        if source.get("unit_id") not in accepted_units[material_id]:
            continue
        signal = cache_meta.get(material_id, {})
        content_status = signal.get("content_status", "HOLD_CONTENT_SIGNAL_MISSING")
        terms = list(dict.fromkeys((source.get("matched_terms") or []) + (source.get("specific_terms") or [])))
        terms = [term for term in terms if len(norm(term)) >= 2]
        pages = page_cache[material_id]
        locators = []
        if content_status.startswith("HOLD_"):
            locator_status = "HOLD_CONTENT_LAYER"
        else:
            for index, page_text in enumerate(pages, start=1):
                normalized = norm(page_text)
                found = [term for term in terms if norm(term) in normalized]
                if found:
                    is_pdf = path.suffix.lower() == ".pdf"
                    locators.append({
                        "locator_kind": "PDF_PAGE" if is_pdf else "HTML_DOCUMENT",
                        "page_number": index if is_pdf else None,
                        "html_char_count": len(page_text) if not is_pdf else None,
                        "matched_terms": found,
                    })
            locator_status = "TEXT_LOCATOR_FOUND" if locators else "TEXT_LOCATOR_NOT_FOUND"
        status_counts[content_status] += 1
        locator_counts[locator_status] += 1
        rows.append({
            "unit_id": source["unit_id"],
            "representative_candidate_id": source["representative_candidate_id"],
            "material_external_id": material_id,
            "material_title": source.get("material_title"),
            "material_sha256": materials[material_id].get("sha256"),
            "content_status": content_status,
            "locator_status": locator_status,
            "locators": locators,
            "match_basis": source.get("match_basis", []),
            "crosswalk_status": source.get("crosswalk_status"),
            "citation_ready": 0,
            "human_verified": 0,
            "body_excerpt_persisted": False,
        })
    report = {
        "run_id": "fulltext_locator_candidates_20260730",
        "fulltext_material_objects": len(materials),
        "crosswalk_rows_considered": len(rows),
        "content_status_counts": dict(status_counts),
        "locator_status_counts": dict(locator_counts),
        "body_excerpts_persisted": False,
        "citation_ready": 0,
        "human_verified": 0,
        "formal_db_written": False,
        "parser": "fitz" if fitz is not None else "unavailable",
    }
    (OUT / "LOCATOR_CANDIDATES.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8"
    )
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
