#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score text overlap between primary OCR candidates and fulltext sources.

The output is a review queue, not a semantic conclusion. No body excerpts are
written; only counts, hashes, locators and review statuses are persisted.
"""

from __future__ import annotations

import html
import hashlib
import json
import re
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

try:
    import fitz  # type: ignore
except ImportError:
    fitz = None

ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
SIGNALS = ROOT / "work/domestic/staging_20260730/fulltext_semantic_signal_queue/SIGNALS.jsonl"
CROSSWALK = ROOT / "work/domestic/staging_20260730/claim_research_crosswalk/CROSSWALK.jsonl"
MATERIALS = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/MATERIALS.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/fulltext_text_overlap_queue"

STOP_TOKENS = {
    "民盟", "民主同盟", "中国民主同盟", "政治协商", "政治協商", "民主党派", "民主黨派",
    "历史文献", "歷史文獻", "1941", "1942", "1943", "1944", "1945", "1946", "1947", "1948", "1949",
}


def visible_html(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def norm(value: str) -> str:
    # Keep Chinese characters and digits; remove OCR whitespace/punctuation.
    return re.sub(r"[^\u3400-\u9fffA-Za-z0-9]", "", (value or "")).lower()


def path_from(row: dict) -> Path:
    path = Path(row["local_path"])
    return path if path.is_absolute() else ROOT / path


def terms_from(text: str) -> set[str]:
    terms: set[str] = set()
    for run in re.findall(r"[\u3400-\u9fff]{2,8}|[A-Za-z]{3,}|\d{4}", text or ""):
        run = norm(run)
        if len(run) >= 2 and run not in STOP_TOKENS:
            terms.add(run)
    return terms


def hash_terms(terms: set[str]) -> str:
    return hashlib.sha256("\n".join(sorted(terms)).encode("utf-8")).hexdigest()


def load_texts(materials: dict[str, dict]) -> dict[str, str]:
    result: dict[str, str] = {}
    for material_id, row in materials.items():
        path = path_from(row)
        if path.suffix.lower() == ".pdf" and fitz is not None and path.exists():
            doc = fitz.open(path)
            result[material_id] = "\n".join(page.get_text("text") for page in doc)
            doc.close()
        elif path.suffix.lower() in {".html", ".htm"} and path.exists():
            result[material_id] = visible_html(path.read_text(encoding="utf-8", errors="replace"))
        else:
            result[material_id] = ""
    return result


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    materials = {
        row["material_external_id"]: row
        for row in (json.loads(line) for line in MATERIALS.read_text(encoding="utf-8").splitlines() if line.strip())
        if row.get("fulltext_status", "").startswith("FULLTEXT")
    }
    accepted_units = {key: set(row.get("matched_units", [])) for key, row in materials.items()}
    signals = [json.loads(line) for line in SIGNALS.read_text(encoding="utf-8").splitlines() if line.strip()]
    crosswalk = {
        (row["unit_id"], row["material_external_id"]): row
        for row in (json.loads(line) for line in CROSSWALK.read_text(encoding="utf-8").splitlines() if line.strip())
        if row.get("material_external_id") in materials and row.get("unit_id") in accepted_units[row.get("material_external_id")]
    }
    texts = load_texts(materials)
    conn = sqlite3.connect(DB)
    candidate_rows = conn.execute(
        "SELECT candidate_id, candidate_text, candidate_text_sha256, physical_page_no, source_ocr_md_path "
        "FROM evidence_claim_candidates"
    ).fetchall()
    conn.close()
    candidates = {row[0]: row for row in candidate_rows}

    output = []
    counts = Counter()
    by_material = defaultdict(Counter)
    for signal in signals:
        key = (signal["unit_id"], signal["material_external_id"])
        source = crosswalk.get(key, {})
        candidate = candidates.get(signal["representative_candidate_id"])
        candidate_text = candidate[1] if candidate else ""
        fulltext = texts.get(signal["material_external_id"], "")
        candidate_norm = norm(candidate_text)
        fulltext_norm = norm(fulltext)
        candidate_terms = terms_from(candidate_text)
        overlapping_terms = {term for term in candidate_terms if term in fulltext_norm}
        specific_terms = [term for term in signal.get("specific_terms", []) if norm(term) in fulltext_norm]
        content_hold = signal.get("machine_relation_status") == "UNKNOWN_CONTENT_LAYER_HOLD"
        exact_match = bool(candidate_norm) and candidate_norm in fulltext_norm
        if content_hold:
            status = "UNKNOWN_CONTENT_LAYER_HOLD"
        elif exact_match or (len(overlapping_terms) >= 2 and specific_terms):
            status = "STRONG_TEXT_OVERLAP_REVIEW_REQUIRED"
        elif overlapping_terms or specific_terms:
            status = "WEAK_TEXT_OVERLAP_REVIEW_REQUIRED"
        else:
            status = "UNKNOWN_NO_TEXT_OVERLAP"
        counts[status] += 1
        by_material[signal["material_external_id"]][status] += 1
        output.append({
            "unit_id": signal["unit_id"],
            "representative_candidate_id": signal["representative_candidate_id"],
            "material_external_id": signal["material_external_id"],
            "material_title": signal["material_title"],
            "material_sha256": signal["material_sha256"],
            "candidate_text_sha256": candidate[2] if candidate else None,
            "candidate_physical_page_no": candidate[3] if candidate else None,
            "source_ocr_md_path": candidate[4] if candidate else None,
            "candidate_text_chars": len(candidate_text),
            "candidate_token_count": len(candidate_terms),
            "overlap_token_count": len(overlapping_terms),
            "overlap_token_set_sha256": hash_terms(overlapping_terms),
            "specific_term_hit_count": len(specific_terms),
            "exact_candidate_text_match": exact_match,
            "content_status": signal.get("content_status"),
            "locator_status": signal.get("locator_status"),
            "text_overlap_status": status,
            "machine_only": True,
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
            "body_excerpt_persisted": False,
        })
    report = {
        "run_id": "fulltext_text_overlap_queue_20260730",
        "fulltext_material_objects": len(materials),
        "rows_considered": len(output),
        "text_overlap_status_counts": dict(counts),
        "by_material": {key: dict(value) for key, value in sorted(by_material.items())},
        "method": "candidate OCR token overlap and specific-term presence; not semantic proof",
        "candidate_body_excerpts_persisted": False,
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "formal_db_written": False,
        "parser": "fitz" if fitz is not None else "unavailable",
    }
    (OUT / "OVERLAP_QUEUE.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in output) + "\n", encoding="utf-8"
    )
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
