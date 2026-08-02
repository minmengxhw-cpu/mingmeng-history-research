#!/usr/bin/env python3
"""Apply a small, auditable lexicon to machine evidence candidates.

The output is annotation assistance, not historical interpretation.  Every
annotation remains review-required and cannot become citation-ready by itself.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DB = ROOT / "work/domestic/staging_20260730/domestic_staging.sqlite"
FORMAL_DB = ROOT / "data/research_index.sqlite"
EXPECTED_FORMAL_SHA = "738d81525c09bbff09266db00e54916bf1ec220ee169751bf1b64f3fb0626944"
TAXONOMY_VERSION = "domestic-lexicon-v1-20260730"

LEXICON = {
    "persons": [
        "黄炎培", "黃炎培", "张澜", "張瀾", "沈钧儒", "沈鈞儒", "梁漱溟", "罗隆基", "羅隆基",
        "李公朴", "李公樸", "闻一多", "聞一多", "章伯钧", "章伯鈞", "费孝通", "費孝通",
    ],
    "organizations": [
        "中国民主同盟", "中國民主同盟", "民主同盟", "民盟", "国民党", "國民黨", "共产党", "共產黨",
        "救国会", "救國會", "政治协商会议", "政治協商會議", "政协", "政協", "国民参政会", "國民參政會",
        "西南联大", "西南聯大",
    ],
    "events": [
        "成立", "代表大会", "代表大會", "政治协商", "政治協商", "解散", "非法", "五一口号", "五一口號",
        "一届三中全会", "一屆三中全會", "三中全会", "三中全會", "抗战", "抗戰", "反右", "参政议政", "參政議政",
        "宪政", "憲政",
    ],
    "places": ["上海", "重庆", "重慶", "昆明", "香港", "南京", "北平", "成都", "武汉", "武漢"],
    "publications": ["光明报", "光明報", "民宪", "民憲", "大公报", "大公報", "民主同盟文献", "民主同盟文獻", "观察", "觀察"],
}


def main() -> int:
    formal_before = hashlib.sha256(FORMAL_DB.read_bytes()).hexdigest()
    if formal_before != EXPECTED_FORMAL_SHA:
        raise SystemExit(f"formal DB baseline changed: {formal_before}")
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    rows = c.execute("SELECT * FROM evidence_claim_candidates ORDER BY candidate_id").fetchall()
    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS evidence_candidate_annotations (
            id INTEGER PRIMARY KEY,
            candidate_id TEXT NOT NULL UNIQUE,
            claim_family TEXT NOT NULL,
            person_tags_json TEXT NOT NULL,
            organization_tags_json TEXT NOT NULL,
            event_tags_json TEXT NOT NULL,
            place_tags_json TEXT NOT NULL,
            publication_tags_json TEXT NOT NULL,
            matched_terms_json TEXT NOT NULL,
            annotation_status TEXT NOT NULL,
            annotation_confidence TEXT NOT NULL,
            taxonomy_version TEXT NOT NULL,
            review_required INTEGER NOT NULL DEFAULT 1,
            citation_ready INTEGER NOT NULL DEFAULT 0,
            human_verified INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY(candidate_id) REFERENCES evidence_claim_candidates(candidate_id)
        );
        CREATE INDEX IF NOT EXISTS idx_candidate_annotations_family ON evidence_candidate_annotations(claim_family);
        CREATE INDEX IF NOT EXISTS idx_candidate_annotations_status ON evidence_candidate_annotations(annotation_status);
        """
    )
    counts = Counter()
    for row in rows:
        text = f"{row['source_title'] or ''}\n{row['period'] or ''}\n{row['candidate_text'] or ''}"
        found = {kind: sorted({term for term in terms if term in text}) for kind, terms in LEXICON.items()}
        matched = [term for values in found.values() for term in values]
        families = []
        if found["events"]:
            families.append("event")
        if found["persons"]:
            families.append("person")
        if found["organizations"]:
            families.append("organization")
        if found["places"]:
            families.append("place")
        if found["publications"]:
            families.append("publication")
        claim_family = "+".join(families) if families else "unclassified"
        confidence = "LOW" if not matched else ("MEDIUM" if len(matched) >= 3 else "LOW")
        c.execute(
            """INSERT INTO evidence_candidate_annotations
               (candidate_id,claim_family,person_tags_json,organization_tags_json,
                event_tags_json,place_tags_json,publication_tags_json,matched_terms_json,
                annotation_status,annotation_confidence,taxonomy_version,review_required,
                citation_ready,human_verified)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(candidate_id) DO UPDATE SET
                 claim_family=excluded.claim_family, person_tags_json=excluded.person_tags_json,
                 organization_tags_json=excluded.organization_tags_json, event_tags_json=excluded.event_tags_json,
                 place_tags_json=excluded.place_tags_json, publication_tags_json=excluded.publication_tags_json,
                 matched_terms_json=excluded.matched_terms_json, annotation_status=excluded.annotation_status,
                 annotation_confidence=excluded.annotation_confidence, taxonomy_version=excluded.taxonomy_version,
                 review_required=excluded.review_required, citation_ready=excluded.citation_ready,
                 human_verified=excluded.human_verified""",
            (
                row["candidate_id"], claim_family, json.dumps(found["persons"], ensure_ascii=False),
                json.dumps(found["organizations"], ensure_ascii=False), json.dumps(found["events"], ensure_ascii=False),
                json.dumps(found["places"], ensure_ascii=False), json.dumps(found["publications"], ensure_ascii=False),
                json.dumps(matched, ensure_ascii=False), "machine_rule_tagged_review", confidence,
                TAXONOMY_VERSION, 1, 0, 0,
            ),
        )
        counts["rows"] += 1
        counts[f"family:{claim_family}"] += 1
        counts["tagged"] += int(bool(matched))
        counts["unclassified"] += int(not matched)
    c.commit()
    integrity = c.execute("PRAGMA integrity_check").fetchone()[0]
    fk_count = len(c.execute("PRAGMA foreign_key_check").fetchall())
    counts["table_rows"] = c.execute("SELECT count(*) FROM evidence_candidate_annotations").fetchone()[0]
    formal_after = hashlib.sha256(FORMAL_DB.read_bytes()).hexdigest()
    report = {
        "report": "DOMESTIC_EVIDENCE_CANDIDATE_ANNOTATION_20260730",
        "taxonomy_version": TAXONOMY_VERSION,
        "lexicon_categories": {k: len(v) for k, v in LEXICON.items()},
        "counts": dict(counts),
        "integrity_check": integrity,
        "foreign_key_violation_count": fk_count,
        "formal_db_sha_before": formal_before,
        "formal_db_sha_after": formal_after,
        "formal_db_unchanged": formal_before == formal_after == EXPECTED_FORMAL_SHA,
        "semantic_validation_done": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = DB.parent / "EVIDENCE_CANDIDATE_ANNOTATION_REPORT.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    c.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
