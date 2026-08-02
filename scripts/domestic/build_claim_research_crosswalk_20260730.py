#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build metadata-only cross-source research candidates for claim review."""

from __future__ import annotations

import json
import re
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
OUT = ROOT / "work/domestic/staging_20260730/claim_research_crosswalk"
GENERIC_TERMS = {"民盟", "民主同盟", "中国民主同盟", "政治协商", "抗战", "成立", "会议", "代表大会"}


def clean(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def record_terms(tags_json: str | None, source_title: str | None, period: str | None) -> list[str]:
    try:
        tags = json.loads(tags_json or "{}")
    except (TypeError, json.JSONDecodeError):
        tags = {}
    terms = []
    for key in ("person", "organization", "event", "place", "publication", "matched"):
        values = tags.get(key, []) if isinstance(tags, dict) else []
        terms.extend(clean(value) for value in values if len(clean(value)) >= 2)
    for value in (source_title, period):
        value = clean(value)
        if value:
            for token in re.findall(r"[\u3400-\u9fff]{2,8}|(?:19|20)\d{2}", value):
                if token not in terms:
                    terms.append(token)
    return list(dict.fromkeys(terms))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    claims = conn.execute(
        """
        SELECT u.unit_id,u.representative_candidate_id,u.priority,u.triage_class,
               e.source_title,e.period,t.tags_json
        FROM evidence_claim_review_units u
        JOIN evidence_claim_candidates e ON e.candidate_id=u.representative_candidate_id
        JOIN evidence_claim_semantic_triage t ON t.candidate_id=u.representative_candidate_id
        ORDER BY u.unit_id
        """
    ).fetchall()
    materials = conn.execute(
        """
        SELECT external_id,layer,title,author,institution,publication_date,
               research_type,quality_tier,source_url,fulltext_status,metadata_json
        FROM domestic_research_materials ORDER BY external_id
        """
    ).fetchall()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS claim_research_crosswalk (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_id TEXT NOT NULL,
            representative_candidate_id TEXT NOT NULL,
            material_external_id TEXT NOT NULL,
            matched_terms_json TEXT NOT NULL,
            match_basis_json TEXT NOT NULL,
            crosswalk_status TEXT NOT NULL,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(unit_id,material_external_id)
        )
        """
    )
    output = []
    active_keys = set()
    claim_match_counts = Counter()
    material_match_counts = Counter()
    for claim in claims:
        terms = record_terms(claim["tags_json"], claim["source_title"], claim["period"])
        matches = []
        for material in materials:
            try:
                meta = json.loads(material["metadata_json"] or "{}")
            except (TypeError, json.JSONDecodeError):
                meta = {}
            haystack = " ".join(
                clean(value)
                for value in (
                    material["title"], material["author"], material["institution"],
                    material["publication_date"], material["research_type"],
                    meta.get("research_theme_phase"), meta.get("research_card_category"),
                )
                if value
            )
            matched = [term for term in terms if term and term in haystack]
            if not matched:
                continue
            basis = []
            if any(re.fullmatch(r"(?:19|20)\d{2}", term) for term in matched):
                basis.append("DATE_OR_PERIOD_OVERLAP")
            if any(term in clean(material["title"]) for term in matched):
                basis.append("TITLE_TERM_OVERLAP")
            if any(term in clean(material["institution"]) for term in matched):
                basis.append("INSTITUTION_TERM_OVERLAP")
            matches.append((len(matched), material, matched, basis))
        matches.sort(key=lambda row: (-row[0], row[1]["quality_tier"] or "Z", row[1]["external_id"]))
        for _, material, matched, basis in matches[:20]:
            specific_terms = [term for term in matched if term not in GENERIC_TERMS]
            crosswalk_status = "METADATA_CROSSWALK_REVIEW_REQUIRED" if specific_terms else "METADATA_CROSSWALK_GENERIC_ONLY_HOLD"
            item = {
                "unit_id": claim["unit_id"],
                "representative_candidate_id": claim["representative_candidate_id"],
                "priority": claim["priority"],
                "triage_class": claim["triage_class"],
                "material_external_id": material["external_id"],
                "material_title": material["title"],
                "material_layer": material["layer"],
                "material_quality_tier": material["quality_tier"],
                "material_fulltext_status": material["fulltext_status"],
                "source_url": material["source_url"],
                "matched_terms": matched,
                "specific_terms": specific_terms,
                "match_basis": basis,
                "crosswalk_status": crosswalk_status,
                "citation_ready": 0,
                "human_verified": 0,
            }
            conn.execute(
                """
                INSERT INTO claim_research_crosswalk
                (unit_id,representative_candidate_id,material_external_id,
                 matched_terms_json,match_basis_json,crosswalk_status,citation_ready,human_verified)
                VALUES (?,?,?,?,?,?,?,?)
                ON CONFLICT(unit_id,material_external_id) DO UPDATE SET
                  representative_candidate_id=excluded.representative_candidate_id,
                  matched_terms_json=excluded.matched_terms_json,
                  match_basis_json=excluded.match_basis_json,
                  crosswalk_status=excluded.crosswalk_status,
                  citation_ready=0,
                  human_verified=0
                """,
                (item["unit_id"], item["representative_candidate_id"], item["material_external_id"],
                 json.dumps(matched, ensure_ascii=False), json.dumps(basis, ensure_ascii=False),
                 item["crosswalk_status"], 0, 0),
            )
            output.append(item)
            active_keys.add((item["unit_id"], item["material_external_id"]))
            material_match_counts[material["external_id"]] += 1
        claim_match_counts[claim["unit_id"]] = min(len(matches), 20)
    stale_rows = 0
    for old in conn.execute("SELECT id,unit_id,material_external_id FROM claim_research_crosswalk").fetchall():
        if (old["unit_id"], old["material_external_id"]) not in active_keys:
            conn.execute(
                "UPDATE claim_research_crosswalk SET crosswalk_status='STALE_SUPERSEDED', citation_ready=0, human_verified=0 WHERE id=?",
                (old["id"],),
            )
            stale_rows += 1
    conn.commit()
    report = {
        "run_id": "claim_research_crosswalk_20260730",
        "review_units": len(claims),
        "crosswalk_rows": len(output),
        "stale_superseded_rows": stale_rows,
        "matched_units": sum(1 for value in claim_match_counts.values() if value),
        "unmatched_units": sum(1 for value in claim_match_counts.values() if not value),
        "distinct_materials_matched": len(material_match_counts),
        "crosswalk_status_counts": dict(Counter(item["crosswalk_status"] for item in output)),
        "generic_only_rows": sum(1 for item in output if item["crosswalk_status"] == "METADATA_CROSSWALK_GENERIC_ONLY_HOLD"),
        "top_material_match_counts": dict(material_match_counts.most_common(20)),
        "crosswalk_status": "METADATA_CROSSWALK_REVIEW_REQUIRED",
        "citation_ready": 0,
        "human_verified": 0,
        "formal_db_written": False,
        "staging_integrity": conn.execute("PRAGMA integrity_check").fetchone()[0],
    }
    (OUT / "CROSSWALK.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in output) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
