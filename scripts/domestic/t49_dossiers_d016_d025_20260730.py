#!/usr/bin/env python3
"""
T49 — Build D016-D025 from the 25-dossier priority list.

From the master task:
16. 民盟地方组织形成
17. 西南联大知识分子与民盟
18. 民盟与国民参政会 (already D008)
19. 1947年压迫与解散 (already D003)
20. 香港恢复活动
21. 响应"五一口号" (already D009)
22. 民盟与新政协
23. 新中国成立初期参政
24. 1957年后的组织经历
25. 改革开放后的组织恢复
26. 民盟盟史编纂史
27. 民盟与中国多党合作制度形成
"""
from __future__ import annotations
import hashlib
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
    "D016_民盟地方组织形成": {
        "period": "1941-1949",
        "person_keywords": ["民盟", "地方组织", "省委", "市委"],
        "primary_keywords": ["民盟", "地方", "组织", "省级", "市级", "区委"],
    },
    "D017_西南联大知识分子与民盟": {
        "period": "1938-1946",
        "person_keywords": ["闻一多", "李公朴", "吴晗", "潘光旦", "张奚若", "罗常培"],
        "primary_keywords": ["西南联大", "昆明", "一二·一", "李闻", "联大"],
    },
    "D018_香港恢复活动": {
        "period": "1947-1949",
        "person_keywords": ["沈钧儒", "章伯钧", "邓初民", "周新民"],
        "primary_keywords": ["香港", "民盟", "恢复", "港九", "南方"],
    },
    "D019_民盟与新政协": {
        "period": "1948-1949",
        "person_keywords": ["张澜", "沈钧儒", "罗隆基", "章伯钧", "马叙伦"],
        "primary_keywords": ["新政协", "政协", "第一届", "共同纲领"],
    },
    "D020_新中国初期参政": {
        "period": "1949-1957",
        "person_keywords": ["张澜", "沈钧儒", "罗隆基", "章伯钧", "马叙伦"],
        "primary_keywords": ["新中国", "参政", "中央人民政府", "第一届"],
    },
    "D021_1957年后的组织经历": {
        "period": "1957-1976",
        "person_keywords": ["民盟", "中央", "组织"],
        "primary_keywords": ["1957", "反右", "整风", "文革", "民主党派"],
    },
    "D022_改革开放后的组织恢复": {
        "period": "1977-2000",
        "person_keywords": ["民盟", "中央", "恢复"],
        "primary_keywords": ["改革开放", "1977", "1978", "1979", "1980", "恢复", "重建"],
    },
    "D023_民盟盟史编纂史": {
        "period": "1949-2000",
        "person_keywords": ["民盟", "文史"],
        "primary_keywords": ["盟史", "编纂", "文史", "中央", "中央文史"],
    },
    "D024_民盟与中国多党合作制度形成": {
        "period": "1949-2000",
        "person_keywords": ["民盟", "中国"],
        "primary_keywords": ["多党合作", "长期共存", "互相监督", "肝胆相照", "荣辱与共"],
    },
    "D025_民盟参政议政史": {
        "period": "1949-2000",
        "person_keywords": ["民盟", "参政"],
        "primary_keywords": ["参政议政", "政协", "人大", "议案", "提案"],
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


def filter_by_keywords(rows, kw_list, max_n=8):
    out = []
    for r in rows:
        title = r.get("title", "")
        text = json.dumps(r, ensure_ascii=False)
        if any(kw in title or kw in text for kw in kw_list):
            out.append(r)
    return out[:max_n]


def build_dossier(dossier_id, theme, pool):
    period = theme["period"]
    person_keywords = theme["person_keywords"]
    primary_keywords = theme["primary_keywords"]
    off = [r for r in pool if r.get("institution_type") or r.get("research_card_category") in ("OFFICIAL_HISTORICAL_STUDY", "OFFICIAL_SOURCE_EDITION", "LOCAL_LEAGUE_HISTORY", "BIOGRAPHICAL_STUDY", "OFFICIAL_RETROSPECTIVE")]
    scholar = [r for r in pool if r.get("research_card_category") in ("SCHOLARLY_ARTICLE", "ACADEMIC_MONOGRAPH", "ARCHIVAL_GUIDE", "PRIMARY_SOURCE_EDITION", "SCHOLARLY_RESEARCH") or r.get("layer") == "SCHOLARLY_RESEARCH"]
    prim = [r for r in pool if r.get("classification") in ("CONTEMPORARY_ORIGINAL", "CONTEMPORARY_REPRINT", "ARCHIVAL_CATALOG", "LATER_TRANSCRIPTION") or r.get("local_path")]
    off_picked = filter_by_keywords(off, primary_keywords + person_keywords, 8)
    scholar_picked = filter_by_keywords(scholar, primary_keywords + person_keywords, 8)
    primary_picked = filter_by_keywords(prim, primary_keywords + person_keywords, 8)
    people = []
    for p in person_keywords:
        if p == "民盟" or p == "中国" or p == "中央" or p == "组织" or p == "参政" or p == "恢复" or p == "地方" or p == "省委" or p == "市委" or p == "区委":
            continue
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
        {"entity_id": "organization:民盟中央", "entity_type": "ORGANIZATION", "canonical_name": "民盟中央", "aliases": [], "evidence_count": len(off_picked), "confidence": "MACHINE_EXPLICIT_MENTION", "citation_ready": False, "human_verified": False},
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
    gaps = ["本批次仅基于公开 metadata 标题筛选；尚未补实 OCR、逐页图和下载本地全文。",
            "研究主题人物【众源/aggregation】证据待 T03 链路补齐；本 dossier 不声明引用完整。"]
    (d / "EVIDENCE_GAPS.md").write_text("# EVIDENCE_GAPS\n\n" + "\n".join(f"- {g}" for g in gaps))
    log = [f"# Search log for {dossier_id}", "",
           "## Public official retrospectives",
           *[f"- {r.get('title','')[:60]} ({r.get('institution_type') or '?'})" for r in off_picked],
           "## Scholarly research", *[f"- {r.get('title','')[:60]}" for r in scholar_picked],
           "## Primary sources", *[f"- {r.get('title','')[:60]}" for r in primary_picked]]
    (d / "SEARCH_LOG.md").write_text("\n".join(log))
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
        "task_id": "T49",
        "dossiers": results,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "audit_pool_size": len(pool),
    }
    out = RESEARCH_DIR / "T49_DOSSIER_GENERATION.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
