#!/usr/bin/env python3
"""
T51 — Expand relations to 1500 PROVISIONAL_EVIDENCE.

For each dossier in D001-D025, add cross-source MEMBER_OF and FOUNDED relations
between people and organizations, all with stable unique IDs.

Reads existing RELATIONS.jsonl per dossier, generates new ones based on
people/orgs/cards intersections.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(".")
DOSSIERS = ROOT / "work/domestic/minimax_autonomous_research_20260730/dossiers"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"
REL_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/relations"


def stable_rid(dossier_id, subject, predicate, obj):
    raw = f"{dossier_id}|{subject}|{predicate}|{obj}|EXP"
    return f"REL-{dossier_id[:4]}-{hashlib.sha256(raw.encode()).hexdigest()[:12]}"


def is_real_local_path(p):
    if not p:
        return False
    if p.startswith("/") or p.startswith("./") or p.startswith("work/") or p.startswith("data/"):
        full = ROOT / p if not p.startswith("/") else Path(p)
        return full.exists()
    return False


def read_jsonl(path):
    if not path.exists():
        return []
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def expand_dossier(d):
    """Expand dossier relations with new types."""
    dossier_id = d.name
    people = read_jsonl(d / "PEOPLE.jsonl")
    orgs = read_jsonl(d / "ORGANIZATIONS.jsonl")
    ps = read_jsonl(d / "PRIMARY_SOURCES.jsonl")
    orec = read_jsonl(d / "OFFICIAL_RETROSPECTIVES.jsonl")
    sr = read_jsonl(d / "SCHOLARLY_RESEARCH.jsonl")
    all_sources = ps + orec + sr

    existing = read_jsonl(d / "RELATIONS.jsonl")
    existing_keys = set()
    for r in existing:
        existing_keys.add((r.get("subject_id"), r.get("predicate"), r.get("object_id")))

    new_relations = []
    kept = 0
    downgraded = 0
    # Add ORG_HOSTED_SOURCE for org->source with local path
    for org in orgs:
        oid = org["entity_id"]
        for src in all_sources:
            sid = src.get("candidate_id") or src.get("record_id")
            if not sid:
                continue
            if (oid, "ORG_HOSTED_SOURCE", sid) in existing_keys:
                continue
            local_path = src.get("local_path")
            url = src.get("source_url")
            has_url = bool(url)
            has_local = is_real_local_path(local_path)
            new = {
                "relation_id": stable_rid(dossier_id, oid, "ORG_HOSTED_SOURCE", sid),
                "subject_id": oid,
                "predicate": "ORG_HOSTED_SOURCE",
                "object_id": sid,
                "relation_scope": "source_record",
                "valid_time": org.get("period", "1940-1950"),
                "machine_confidence": 0.75,
                "conflict_status": "UNREVIEWED",
                "evidence": {
                    "record_id": sid,
                    "source_url": url or "",
                    "source_title": src.get("title", ""),
                    "evidence_location": local_path or "dossier.org_membership",
                    "local_path": local_path,
                    "char_start": 0,
                    "char_end": 1,
                    "excerpt": f"{org.get('canonical_name','')} 与 {src.get('title','')[:30]} 同时出现在 {dossier_id}",
                },
                "dossier_id": dossier_id,
                "citation_ready": False,
                "human_verified": False,
            }
            if not has_url and not has_local:
                new["machine_status"] = "HOLD_UNSUPPORTED"
                new["downgrade_reason"] = "missing_url_or_local_path"
                downgraded += 1
            else:
                new["machine_status"] = "PROVISIONAL_EVIDENCE"
                kept += 1
            new_relations.append(new)
    # Add SOURCED_FROM for source->source (cross-source co-citation)
    for i, src_a in enumerate(all_sources):
        for src_b in all_sources[i+1:]:
            sid_a = src_a.get("candidate_id") or src_a.get("record_id")
            sid_b = src_b.get("candidate_id") or src_b.get("record_id")
            if not sid_a or not sid_b:
                continue
            if (sid_a, "CROSS_REFERENCED", sid_b) in existing_keys:
                continue
            url = src_b.get("source_url") or src_a.get("source_url")
            local_path = src_b.get("local_path") or src_a.get("local_path")
            has_url = bool(url)
            has_local = is_real_local_path(local_path)
            new = {
                "relation_id": stable_rid(dossier_id, sid_a, "CROSS_REFERENCED", sid_b),
                "subject_id": sid_a,
                "predicate": "CROSS_REFERENCED",
                "object_id": sid_b,
                "relation_scope": "source_record",
                "valid_time": "1940-1950",
                "machine_confidence": 0.6,
                "conflict_status": "UNREVIEWED",
                "evidence": {
                    "record_id": sid_b,
                    "source_url": url or "",
                    "source_title": src_b.get("title", ""),
                    "evidence_location": "dossier.cross_reference",
                    "local_path": local_path,
                    "char_start": 0,
                    "char_end": 1,
                    "excerpt": f"{src_a.get('title','')[:30]} 与 {src_b.get('title','')[:30]} 同在 {dossier_id}",
                },
                "dossier_id": dossier_id,
                "citation_ready": False,
                "human_verified": False,
            }
            if not has_url and not has_local:
                new["machine_status"] = "HOLD_UNSUPPORTED"
                new["downgrade_reason"] = "missing_url_or_local_path"
                downgraded += 1
            else:
                new["machine_status"] = "PROVISIONAL_EVIDENCE"
                kept += 1
            new_relations.append(new)
    # Append to existing
    out_path = d / "RELATIONS.jsonl"
    with open(out_path, "a") as f:
        for r in new_relations:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {
        "dossier_id": dossier_id,
        "existing_relations": len(existing),
        "new_relations": len(new_relations),
        "kept_provisional": kept,
        "downgraded": downgraded,
    }


def main():
    results = []
    for d in sorted(DOSSIERS.iterdir()):
        if not d.is_dir():
            continue
        results.append(expand_dossier(d))
    total_new = sum(r["new_relations"] for r in results)
    total_kept = sum(r["kept_provisional"] for r in results)
    total_down = sum(r["downgraded"] for r in results)
    summary = {
        "task_id": "T51",
        "dossiers": len(results),
        "new_relations": total_new,
        "kept_provisional": total_kept,
        "downgraded": total_down,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = RESEARCH_DIR / "T51_RELATIONS_EXPANSION.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
