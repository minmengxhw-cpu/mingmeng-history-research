#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build conservative entity/event relation signals for 38 review cards."""

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
REVIEW_CARDS = ROOT / "work/domestic/staging_20260730/fulltext_semantic_review_cards/REVIEW_CARDS.jsonl"
EVIDENCE_CARDS = ROOT / "work/domestic/staging_20260730/evidence_claim_cards/CARDS.jsonl"
MATERIALS = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/MATERIALS.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/structured_relation_signals"

STOP = {"民盟", "民主同盟", "中国民主同盟", "政治协商", "政治協商", "民盟文献", "民主同盟文献", "民主同盟文獻"}


def visible_html(raw: str) -> str:
    raw = re.sub(r"<script\b[^>]*>.*?</script>", " ", raw, flags=re.I | re.S)
    raw = re.sub(r"<style\b[^>]*>.*?</style>", " ", raw, flags=re.I | re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def norm(value: str) -> str:
    return re.sub(r"\s+", "", value or "").lower()


def load_fulltexts(materials: dict[str, dict]) -> dict[str, str]:
    out = {}
    for material_id, row in materials.items():
        path = Path(row["local_path"])
        if not path.is_absolute():
            path = ROOT / path
        text = ""
        if path.suffix.lower() == ".pdf" and fitz is not None and path.exists():
            doc = fitz.open(path)
            text = "\n".join(page.get_text("text") for page in doc)
            doc.close()
        elif path.suffix.lower() in {".html", ".htm"} and path.exists():
            text = visible_html(path.read_text(encoding="utf-8", errors="replace"))
        out[material_id] = norm(text)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    materials = {
        row["material_external_id"]: row
        for row in (json.loads(line) for line in MATERIALS.read_text(encoding="utf-8").splitlines() if line.strip())
        if row.get("local_path") and row.get("fulltext_status", "").startswith("FULLTEXT")
    }
    cards = {}
    for line in EVIDENCE_CARDS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            cards[row["candidate_id"]] = row
    texts = load_fulltexts(materials)
    rows = []
    counts = Counter()
    for review in (json.loads(line) for line in REVIEW_CARDS.read_text(encoding="utf-8").splitlines() if line.strip()):
        card = cards.get(review["representative_candidate_id"], {})
        tags = card.get("machine_tags") or {}
        category_hits = {}
        for category in ("person", "organization", "event", "place", "publication"):
            terms = [term for term in tags.get(category, []) if norm(term) not in STOP and len(norm(term)) >= 2]
            category_hits[category] = [term for term in dict.fromkeys(terms) if norm(term) in texts.get(review["fulltext_material_external_id"], "")]
        subject_hit_count = sum(len(value) for value in category_hits.values())
        event_entity_hits = len(category_hits["person"] + category_hits["organization"] + category_hits["event"])
        if event_entity_hits >= 2:
            signal = "POTENTIAL_SAME_CONTEXT_REVIEW_REQUIRED"
        elif subject_hit_count >= 1:
            signal = "POTENTIAL_CONTEXT_ONLY_REVIEW_REQUIRED"
        else:
            signal = "UNKNOWN_NO_SUBJECT_HIT"
        counts[signal] += 1
        rows.append({
            "review_card_id": review["review_card_id"],
            "unit_id": review["unit_id"],
            "representative_candidate_id": review["representative_candidate_id"],
            "fulltext_material_external_id": review["fulltext_material_external_id"],
            "primary_physical_page_no": review["primary_physical_page_no"],
            "fulltext_locators": review.get("fulltext_locators", []),
            "category_hit_counts": {key: len(value) for key, value in category_hits.items()},
            "subject_hit_count": subject_hit_count,
            "event_entity_hit_count": event_entity_hits,
            "relation_signal": signal,
            "relation_status": "UNVERIFIED",
            "semantic_validation_done": 0,
            "citation_ready": 0,
            "human_verified": 0,
            "body_excerpt_persisted": False,
        })
    report = {
        "run_id": "structured_relation_signals_20260730",
        "input_review_cards": len(rows),
        "relation_signal_counts": dict(counts),
        "relation_status": "UNVERIFIED_ALL",
        "semantic_validation_done": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
        "method": "machine tag category overlap; not semantic proof",
    }
    (OUT / "SIGNALS.jsonl").write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
