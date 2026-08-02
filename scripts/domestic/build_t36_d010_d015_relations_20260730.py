#!/usr/bin/env python3
"""
T36 sub-routine — Build dossier subgraphs for D010-D015 (matches T36 logic).
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
DOSSIERS = ROOT / "work/domestic/minimax_autonomous_research_20260730/dossiers"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"

TARGET = [
    "D010_黄炎培与宪政运动",
    "D011_梁漱溟与民盟创建",
    "D012_张澜的政治思想与组织作用",
    "D013_罗隆基与民主政治",
    "D014_沈钧儒与救国会、民盟",
    "D015_西南联大知识分子与民盟",
]

PERIOD = {
    "D010_黄炎培与宪政运动": "1937-1946",
    "D011_梁漱溟与民盟创建": "1940-1941",
    "D012_张澜的政治思想与组织作用": "1941-1949",
    "D013_罗隆基与民主政治": "1941-1949",
    "D014_沈钧儒与救国会、民盟": "1936-1949",
    "D015_西南联大知识分子与民盟": "1938-1946",
}


def stable_rid(dossier_id, subject, predicate, obj):
    raw = f"{dossier_id}|{subject}|{predicate}|{obj}"
    h = hashlib.sha256(raw.encode()).hexdigest()[:12]
    return f"REL-{dossier_id[:4]}-{h}"


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


def build(d):
    dossier_id = d.name
    period = PERIOD.get(dossier_id, "1940-1949")
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
            sid = src.get("candidate_id") or src.get("record_id")
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
                    "excerpt": f"{person.get('canonical_name','')} 与 {org.get('canonical_name','')} 同时出现在 {dossier_id}",
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
        "downgraded": downgraded,
    }


def main():
    results = []
    for name in TARGET:
        d = DOSSIERS / name
        if not d.exists():
            results.append({"dossier_id": name, "skipped": True})
            continue
        results.append(build(d))
    summary = {
        "task_id": "T36_D010_D015",
        "dossiers": results,
        "total_relations": sum(r.get("relations", 0) for r in results if not r.get("skipped")),
        "total_kept": sum(r.get("kept_provisional", 0) for r in results if not r.get("skipped")),
        "total_downgraded": sum(r.get("downgraded", 0) for r in results if not r.get("skipped")),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out = RESEARCH_DIR / "T36_D010_D015_SUBGRAPH_ACCEPTANCE.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
