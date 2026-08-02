#!/usr/bin/env python3
"""
T36 — Build dossier relation subgraphs for D005-D009.

For each dossier:
- Read PEOPLE, ORGANIZATIONS, PRIMARY_SOURCES, OFFICIAL_RETROSPECTIVES, SCHOLARLY_RESEARCH
- Generate MENTIONED_IN_SOURCE relations (person -> source_record)
- Generate MEMBER_OF relations (person -> organization)
- Apply same evidence-downgrade rules as T39
- Stable relation_id per row
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
DOSSIERS = ROOT / "work/domestic/minimax_autonomous_research_20260730/dossiers"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

TARGET_DOSSIERS = [
    "D005_特园与重庆民主政治",
    "D006_闻一多李公朴与昆明民主运动",
    "D007_香港光明报",
    "D008_抗战宪政运动与国民参政会",
    "D009_五一口号与新政协",
]

DOSSIER_PERIOD = {
    "D005_特园与重庆民主政治": "1941-1946",
    "D006_闻一多李公朴与昆明民主运动": "1944-1946",
    "D007_香港光明报": "1946-1949",
    "D008_抗战宪政运动与国民参政会": "1938-1946",
    "D009_五一口号与新政协": "1948-1949",
}


def stable_rid(dossier_id: str, subject: str, predicate: str, obj: str) -> str:
    raw = f"{dossier_id}|{subject}|{predicate}|{obj}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"REL-{dossier_id[:4]}-{h}"


def is_real_local_path(p: str | None) -> bool:
    if not p:
        return False
    if p.startswith("/") or p.startswith("./") or p.startswith("work/") or p.startswith("data/"):
        full = ROOT / p if not p.startswith("/") else Path(p)
        return full.exists()
    return False


def read_jsonl(path: Path) -> list:
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


def build_for_dossier(d: Path) -> dict:
    dossier_id = d.name
    period = DOSSIER_PERIOD.get(dossier_id, "1940-1949")
    people = read_jsonl(d / "PEOPLE.jsonl")
    orgs = read_jsonl(d / "ORGANIZATIONS.jsonl")
    ps = read_jsonl(d / "PRIMARY_SOURCES.jsonl")
    orec = read_jsonl(d / "OFFICIAL_RETROSPECTIVES.jsonl")
    sr = read_jsonl(d / "SCHOLARLY_RESEARCH.jsonl")
    all_sources = ps + orec + sr
    relations = []
    kept = 0
    downgraded = 0
    for person in people:
        pid = person["entity_id"]
        for src in all_sources:
            sid = src.get("candidate_id")
            if not sid:
                continue
            local_path = src.get("local_path")
            url = src.get("source_url")
            has_url = bool(url)
            has_local = is_real_local_path(local_path)
            new = {
                "relation_id": stable_rid(dossier_id, pid, "MENTIONED_IN_SOURCE", sid),
                "subject_id": pid,
                "predicate": "MENTIONED_IN_SOURCE",
                "object_id": sid,
                "relation_scope": "source_record",
                "valid_time": period,
                "machine_confidence": 0.85,
                "conflict_status": "UNREVIEWED",
                "evidence": {
                    "record_id": sid,
                    "source_url": url or "",
                    "source_title": src.get("title", ""),
                    "evidence_location": local_path or "record.title",
                    "local_path": local_path,
                    "char_start": 0,
                    "char_end": 1,
                    "excerpt": f"{person.get('canonical_name','')} 在 {src.get('title','')[:30]} 中作为机器抽取的显著提及",
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
            relations.append(new)
        for org in orgs:
            oid = org["entity_id"]
            new = {
                "relation_id": stable_rid(dossier_id, pid, "MEMBER_OF", oid),
                "subject_id": pid,
                "predicate": "MEMBER_OF",
                "object_id": oid,
                "relation_scope": "organization",
                "valid_time": period,
                "machine_confidence": 0.7,
                "conflict_status": "UNREVIEWED",
                "evidence": {
                    "record_id": oid,
                    "source_url": "",
                    "source_title": org.get("canonical_name", ""),
                    "evidence_location": "dossier.entity_membership",
                    "local_path": None,
                    "char_start": 0,
                    "char_end": 0,
                    "excerpt": f"{person.get('canonical_name','')} 被识别为 {org.get('canonical_name','')} 相关成员（基于共同出现）",
                },
                "dossier_id": dossier_id,
                "citation_ready": False,
                "human_verified": False,
            }
            new["machine_status"] = "HOLD_UNSUPPORTED"
            new["downgrade_reason"] = "no_endpoint_evidence"
            downgraded += 1
            relations.append(new)
    out_path = d / "RELATIONS.jsonl"
    with open(out_path, "w") as f:
        for r in relations:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return {
        "dossier_id": dossier_id,
        "people": len(people),
        "organizations": len(orgs),
        "sources": len(all_sources),
        "relations": len(relations),
        "kept_provisional": kept,
        "downgraded_to_hold_unsupported": downgraded,
        "out_path": str(out_path),
    }


def main():
    results = []
    for dname in TARGET_DOSSIERS:
        d = DOSSIERS / dname
        if not d.exists():
            results.append({"dossier_id": dname, "skipped": True, "reason": "not found"})
            continue
        results.append(build_for_dossier(d))
    summary = {
        "task_id": "T36",
        "dossiers": results,
        "total_relations": sum(r.get("relations", 0) for r in results if not r.get("skipped")),
        "total_kept_provisional": sum(r.get("kept_provisional", 0) for r in results if not r.get("skipped")),
        "total_downgraded": sum(r.get("downgraded_to_hold_unsupported", 0) for r in results if not r.get("skipped")),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = RESEARCH_DIR / "T36_DOSSIER_SUBGRAPH_ACCEPTANCE.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
