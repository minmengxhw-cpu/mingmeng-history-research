#!/usr/bin/env python3
"""
T41 — Build dossiers D010-D015 from priority list.

D010 黄炎培与宪政运动
D011 梁漱溟与民盟创建
D012 张澜的政治思想与组织作用
D013 罗隆基与民主政治
D014 沈钧儒与救国会、民盟
D015 西南联大知识分子与民盟

For each: pull 8 official retrospective + 8 scholarly + 8 primary from existing T03/T18/T21/T25/T37 audits.
Add RESERVED-period scoping; relation subgraphs reused.
"""
from __future__ import annotations
import json
import re
from pathlib import Path
from collections import Counter

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
DOSSIERS = ROOT / "work/domestic/minimax_autonomous_research_20260730/dossiers"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"
SOURCE_AUDITS = [
    RESEARCH_DIR / "T03_OFFICIAL_IDENTITY_AUDIT.jsonl",
    RESEARCH_DIR / "T21_1948_1949_OFFICIAL.jsonl",
    RESEARCH_DIR / "T37_1949_1957_OFFICIAL.jsonl",
    RESEARCH_DIR / "T25_1950_1976_OFFICIAL.jsonl",
    RESEARCH_DIR / "T18_OFFICIAL_1977_2000.jsonl",
    RESEARCH_DIR / "T30_1941_1945_SCHOLARLY.jsonl",
    RESEARCH_DIR / "T22_1941_1943_ARCHIVE_CATALOG.jsonl",
    RESEARCH_DIR / "T17_HK_PRIMARY_LEDGER.jsonl",
]


THEMES = {
    "D010_黄炎培与宪政运动": {
        "period": "1937-1946",
        "person_keywords": ["黄炎培"],
        "primary_keywords": ["宪政", "参政", "中华职业教育社", "国讯", "黄炎培"],
    },
    "D011_梁漱溟与民盟创建": {
        "period": "1940-1941",
        "person_keywords": ["梁漱溟"],
        "primary_keywords": ["梁漱溟", "民盟", "政团", "统一建国同志会"],
    },
    "D012_张澜的政治思想与组织作用": {
        "period": "1941-1949",
        "person_keywords": ["张澜"],
        "primary_keywords": ["张澜", "民盟主席", "川北", "南充"],
    },
    "D013_罗隆基与民主政治": {
        "period": "1941-1949",
        "person_keywords": ["罗隆基"],
        "primary_keywords": ["罗隆基", "民主", "政协", "改组"],
    },
    "D014_沈钧儒与救国会、民盟": {
        "period": "1936-1949",
        "person_keywords": ["沈钧儒"],
        "primary_keywords": ["沈钧儒", "救国会", "七君子", "全民抗战"],
    },
    "D015_西南联大知识分子与民盟": {
        "period": "1938-1946",
        "person_keywords": ["闻一多", "李公朴", "吴晗", "潘光旦"],
        "primary_keywords": ["西南联大", "昆明", "一二·一", "李闻"],
    },
}


def load_audit_pool() -> list:
    rows = []
    seen = set()
    for p in SOURCE_AUDITS:
        if not p.exists():
            continue
        with open(p) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                cid = r.get("candidate_id") or r.get("record_id")
                if cid and cid not in seen:
                    seen.add(cid)
                    rows.append(r)
    return rows


def filter_by_keywords(rows: list, kw_list: list, max_n: int = 8) -> list:
    out = []
    for r in rows:
        title = r.get("title", "")
        text = json.dumps(r, ensure_ascii=False)
        if any(kw in title or kw in text for kw in kw_list):
            out.append(r)
    return out[:max_n]


def build_dossier(dossier_id: str, theme: dict, pool: list) -> dict:
    period = theme["period"]
    person_keywords = theme["person_keywords"]
    primary_keywords = theme["primary_keywords"]
    # pick 8 official, 8 scholarly, 8 primary
    # discriminate by research_card_category or layer:
    off = [r for r in pool if r.get("institution_type") or r.get("research_card_category") in ("OFFICIAL_HISTORICAL_STUDY", "OFFICIAL_SOURCE_EDITION", "LOCAL_LEAGUE_HISTORY", "BIOGRAPHICAL_STUDY", "OFFICIAL_RETROSPECTIVE")]
    scholar = [r for r in pool if r.get("research_card_category") in ("SCHOLARLY_ARTICLE", "ACADEMIC_MONOGRAPH", "ARCHIVAL_GUIDE", "PRIMARY_SOURCE_EDITION", "SCHOLARLY_RESEARCH") or r.get("layer") == "SCHOLARLY_RESEARCH"]
    prim = [r for r in pool if r.get("classification") in ("CONTEMPORARY_ORIGINAL", "CONTEMPORARY_REPRINT", "ARCHIVAL_CATALOG", "LATER_TRANSCRIPTION") or r.get("local_path")]
    off_picked = filter_by_keywords(off, primary_keywords + person_keywords, 8)
    scholar_picked = filter_by_keywords(scholar, primary_keywords + person_keywords, 8)
    primary_picked = filter_by_keywords(prim, primary_keywords + person_keywords, 8)
    # build PEOPLE / ORG / timeline cards
    people = []
    for p in person_keywords:
        people.append({
            "entity_id": f"person:{p}",
            "entity_type": "PERSON",
            "canonical_name": p,
            "aliases": [],
            "evidence_count": len(off_picked) + len(scholar_picked),
            "confidence": "MACHINE_EXPLICIT_MENTION",
            "citation_ready": False,
            "human_verified": False,
        })
    orgs = [
        {"entity_id": "organization:中国民主同盟", "entity_type": "ORGANIZATION", "canonical_name": "中国民主同盟", "aliases": [], "evidence_count": len(off_picked) + len(scholar_picked), "confidence": "MACHINE_EXPLICIT_MENTION", "citation_ready": False, "human_verified": False},
        {"entity_id": "organization:中国民主政团同盟", "entity_type": "ORGANIZATION", "canonical_name": "中国民主政团同盟", "aliases": [], "evidence_count": len(off_picked), "confidence": "MACHINE_EXPLICIT_MENTION", "citation_ready": False, "human_verified": False},
    ]
    timeline = []
    for r in (off_picked + scholar_picked)[:8]:
        timeline.append({
            "date_or_period": period,
            "event_label": r.get("title", "")[:60],
            "source_record_id": r.get("candidate_id") or r.get("record_id"),
            "evidence_level": "OFFICIAL" if r in off_picked else "SCHOLARLY",
            "confidence": "MACHINE_PROVISIONAL",
            "citation_ready": False,
            "human_verified": False,
        })
    # write
    d = DOSSIERS / dossier_id
    d.mkdir(parents=True, exist_ok=True)
    def write_jsonl(name, rows):
        with open(d / name, "w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    write_jsonl("PRIMARY_SOURCES.jsonl", primary_picked)
    write_jsonl("OFFICIAL_RETROSPECTIVES.jsonl", off_picked)
    write_jsonl("SCHOLARLY_RESEARCH.jsonl", scholar_picked)
    write_jsonl("PEOPLE.jsonl", people)
    write_jsonl("ORGANIZATIONS.jsonl", orgs)
    write_jsonl("TIMELINE.jsonl", timeline)
    # EVIDENCE_GAPS.md
    gaps = ["本批次仅基于公开 metadata 标题筛选；尚未补实 OCR、逐页图和下载本地全文。",
            "研究主题人物【众源/aggregation】证据待 T03 链路补齐；本 dossier 不声明引用完整。"]
    (d / "EVIDENCE_GAPS.md").write_text("# EVIDENCE_GAPS\n\n" + "\n".join(f"- {g}" for g in gaps))
    # SEARCH_LOG.md
    log = [f"# Search log for {dossier_id}", "",
           "## Public official retrospectives",
           *[f"- {r.get('title','')[:60]} ({r.get('institution_type') or '?'})" for r in off_picked],
           "## Scholarly research", *[f"- {r.get('title','')[:60]}" for r in scholar_picked],
           "## Primary sources", *[f"- {r.get('title','')[:60]}" for r in primary_picked]]
    (d / "SEARCH_LOG.md").write_text("\n".join(log))
    # DOSSIER.md
    md = [
        f"# 专题：{dossier_id}",
        "",
        f"- dossier_id: {dossier_id}",
        f"- 周期: {period}",
        "- 状态：MACHINE_PROVISIONAL；未设置 citation_ready 或 human_verified。",
        "",
        "## 当前证据规模",
        f"- 一手候选：{len(primary_picked)} 条（最低门槛5）",
        f"- 官方整理：{len(off_picked)} 条（最低门槛3）",
        f"- 学术研究：{len(scholar_picked)} 条（最低门槛3）",
        f"- 时间线候选：{len(timeline)} 条",
    ]
    (d / "DOSSIER.md").write_text("\n".join(md))
    # Now build relations (deferred to T36 logic)
    return {
        "dossier_id": dossier_id,
        "primary_sources": len(primary_picked),
        "official_retrospectives": len(off_picked),
        "scholarly_research": len(scholar_picked),
        "people": len(people),
        "organizations": len(orgs),
        "timeline": len(timeline),
    }


def main():
    pool = load_audit_pool()
    results = []
    for name, theme in THEMES.items():
        results.append(build_dossier(name, theme, pool))
    summary = {
        "task_id": "T41",
        "dossiers": results,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "audit_pool_size": len(pool),
    }
    out = RESEARCH_DIR / "T41_DOSSIER_GENERATION.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
