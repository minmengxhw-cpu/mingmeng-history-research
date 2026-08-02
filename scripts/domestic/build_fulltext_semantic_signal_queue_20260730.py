#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create conservative support/conflict/unknown signals for fulltext crosswalks.

This is a machine triage layer only. It stores terms and statuses, never body
excerpts, and cannot promote a claim to citation-ready.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

try:
    import fitz  # type: ignore
except ImportError:
    fitz = None

ROOT = Path(__file__).resolve().parents[2]
CROSSWALK = ROOT / "work/domestic/staging_20260730/claim_research_crosswalk/CROSSWALK.jsonl"
MATERIALS = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/MATERIALS.jsonl"
LOCATORS = ROOT / "work/domestic/staging_20260730/fulltext_locator_candidates/LOCATOR_CANDIDATES.jsonl"
TRIAGE = ROOT / "work/domestic/staging_20260730/claim_semantic_triage/TRIAGE.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/fulltext_semantic_signal_queue"

CONFLICT_MARKERS = (
    "未", "并非", "並非", "否认", "否認", "反对", "反對", "拒绝", "拒絕", "没有", "沒有",
    "不支持", "不承认", "不承認", "未曾", "并不", "並不", "不存在", "不成立",
)


def visible_html(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def norm(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def local_path(row: dict) -> Path:
    path = Path(row["local_path"])
    return path if path.is_absolute() else ROOT / path


def load_material_texts(materials: dict[str, dict]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for material_id, row in materials.items():
        path = local_path(row)
        pages: list[str] = []
        if path.suffix.lower() == ".pdf" and fitz is not None and path.exists():
            doc = fitz.open(path)
            pages = [page.get_text("text") for page in doc]
            doc.close()
        elif path.suffix.lower() in {".html", ".htm"} and path.exists():
            pages = [visible_html(path.read_text(encoding="utf-8", errors="replace"))]
        out[material_id] = pages
    return out


def nearby_conflict_markers(text: str, term: str) -> set[str]:
    text_n = norm(text)
    term_n = norm(term)
    if not term_n:
        return set()
    markers: set[str] = set()
    start = 0
    while True:
        index = text_n.find(term_n, start)
        if index < 0:
            break
        window = text_n[max(0, index - 35): index + len(term_n) + 35]
        for marker in CONFLICT_MARKERS:
            if norm(marker) in window:
                markers.add(marker)
        start = index + max(1, len(term_n))
    return markers


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    material_rows = {
        row["material_external_id"]: row
        for row in (json.loads(line) for line in MATERIALS.read_text(encoding="utf-8").splitlines() if line.strip())
        if row.get("fulltext_status", "").startswith("FULLTEXT")
    }
    accepted_units = {
        material_id: set(row.get("matched_units", []))
        for material_id, row in material_rows.items()
    }
    locator_rows = {
        (row["unit_id"], row["material_external_id"]): row
        for row in (json.loads(line) for line in LOCATORS.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    triage_rows = {
        row["candidate_id"]: row
        for row in (json.loads(line) for line in TRIAGE.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    texts = load_material_texts(material_rows)
    results = []
    counts = Counter()
    by_material = defaultdict(Counter)
    considered = 0
    for line in CROSSWALK.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        source = json.loads(line)
        material_id = source.get("material_external_id")
        unit_id = source.get("unit_id")
        if material_id not in material_rows or unit_id not in accepted_units[material_id]:
            continue
        considered += 1
        locator = locator_rows.get((unit_id, material_id), {})
        content_status = locator.get("content_status", "HOLD_CONTENT_SIGNAL_MISSING")
        specific_terms = list(dict.fromkeys(source.get("specific_terms") or []))
        generic_terms = list(dict.fromkeys((source.get("matched_terms") or []) + (source.get("match_basis") or [])))
        page_text = "\n".join(texts.get(material_id, []))
        matched_specific = [term for term in specific_terms if norm(term) and norm(term) in norm(page_text)]
        conflict_markers = set()
        for term in matched_specific:
            # Two-character places/names (e.g. 上海/香港) occur frequently in
            # navigation, headers and unrelated sentences; never promote
            # those generic hits to a conflict signal.
            compact_term = norm(term)
            if len(compact_term) >= 4 and not compact_term.isdigit():
                conflict_markers.update(nearby_conflict_markers(page_text, term))
        if content_status.startswith("HOLD_"):
            status = "UNKNOWN_CONTENT_LAYER_HOLD"
            basis = ["全文内容层未通过"]
        elif locator.get("locator_status") != "TEXT_LOCATOR_FOUND":
            status = "UNKNOWN_NO_TEXT_LOCATOR"
            basis = ["没有形成文本位置定位"]
        elif conflict_markers and matched_specific:
            status = "POSSIBLE_CONFLICT_SIGNAL_REVIEW_REQUIRED"
            basis = ["具体词项附近出现否定/冲突词，仅作机器提示"]
        elif matched_specific:
            status = "POSSIBLE_SUPPORT_SIGNAL_REVIEW_REQUIRED"
            basis = ["具体词项在全文文本层出现，仅作机器提示"]
        else:
            status = "UNKNOWN_GENERIC_OR_METADATA_ONLY"
            basis = ["仅有泛词/标题/机构匹配，未形成具体词项正文支持"]
        triage = triage_rows.get(source.get("representative_candidate_id"), {})
        row = {
            "unit_id": unit_id,
            "representative_candidate_id": source.get("representative_candidate_id"),
            "material_external_id": material_id,
            "material_title": source.get("material_title"),
            "material_sha256": material_rows[material_id].get("sha256"),
            "priority": triage.get("priority"),
            "triage_class": triage.get("triage_class"),
            "content_status": content_status,
            "locator_status": locator.get("locator_status"),
            "specific_terms": specific_terms,
            "matched_specific_terms": matched_specific,
            "conflict_markers": sorted(conflict_markers),
            "machine_relation_status": status,
            "machine_basis": basis,
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
            "body_excerpt_persisted": False,
        }
        results.append(row)
        counts[status] += 1
        by_material[material_id][status] += 1
    report = {
        "run_id": "fulltext_semantic_signal_queue_20260730",
        "fulltext_material_objects": len(material_rows),
        "crosswalk_rows_considered": considered,
        "machine_relation_status_counts": dict(counts),
        "by_material": {key: dict(value) for key, value in sorted(by_material.items())},
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
        "method": "specific-term presence plus conservative nearby-negation signal; not semantic proof",
        "parser": "fitz" if fitz is not None else "unavailable",
    }
    (OUT / "SIGNALS.jsonl").write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in results) + "\n", encoding="utf-8"
    )
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
