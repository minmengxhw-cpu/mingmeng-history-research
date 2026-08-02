#!/usr/bin/env python3
"""
T53 — 1957-1976 dedicated acquisition.

Public candidates:
- 周恩来与第二届人大 民盟
- 政协二届/三届 民盟 委员
- 民盟二届/三届 报告
- 反右运动 民盟 史料
- 文革 民盟 牺牲
- 1957-1976 民主党派 历史
"""
from __future__ import annotations
import hashlib
import json
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"
ACQUISITION_DIR = ROOT / "data/domestic/1957_1976_acquisition_20260730"
ACQUISITION_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    {
        "candidate_id": "AA-1957-MMSH-mmzy",
        "title": "民盟中央 反右运动 史料",
        "source_url": "http://www.minmeng1941.cn",
        "institution_type": "MMSH",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "反右 民盟 1957",
    },
    {
        "candidate_id": "AA-1957-CSSN-history",
        "title": "1957 反右运动专题",
        "source_url": "http://www.cssn.cn/lsxzt/1957/",
        "institution_type": "CASS",
        "research_card_category": "SCHOLARLY_ARTICLE",
        "period": "1957-1976",
        "search_keywords": "1957 反右 历史",
    },
    {
        "candidate_id": "AA-1957-marxists-cpc",
        "title": "1957 反右运动 综合材料",
        "source_url": "https://www.marxists.org/chinese/CCP/1957.htm",
        "institution_type": "MARXISTS",
        "research_card_category": "PRIMARY_SOURCE_EDITION",
        "period": "1957-1976",
        "search_keywords": "反右 1957",
    },
    {
        "candidate_id": "AA-1966-marxists-cpc",
        "title": "文革 史料",
        "source_url": "https://www.marxists.org/chinese/CCP/cultural-revolution/",
        "institution_type": "MARXISTS",
        "research_card_category": "PRIMARY_SOURCE_EDITION",
        "period": "1957-1976",
        "search_keywords": "文革 1966 民盟",
    },
    {
        "candidate_id": "AA-1957-CASS-history",
        "title": "中国当代史 1957-1976 民盟",
        "source_url": "http://www.iccs.cn/",
        "institution_type": "CASS",
        "research_card_category": "SCHOLARLY_ARTICLE",
        "period": "1957-1976",
        "search_keywords": "民盟 当代史 1957",
    },
    {
        "candidate_id": "AA-1957-mmzy-www",
        "title": "民盟中央 1957-1976 历史",
        "source_url": "https://www.mmzy.org.cn/mobile/ArticleList.aspx",
        "institution_type": "MMZY",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "民盟中央 历史",
    },
    {
        "candidate_id": "AA-1957-cppcc-wenshi",
        "title": "政协文史资料 1957-1976 民盟",
        "source_url": "http://www.cppcc.gov.cn",
        "institution_type": "CPPCC",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "政协文史 1957 民盟",
    },
    {
        "candidate_id": "AA-1957-difang-meng",
        "title": "省市民盟 1957-1976 资料",
        "source_url": "http://www.mm1941.org",
        "institution_type": "MM1941",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "省民盟 市委",
    },
]


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MiniMax-Research/2026"})
        with urllib.request.urlopen(req, timeout=10) as r:
            ct = r.headers.get("Content-Type", "unknown")
            data = r.read(1024 * 1024)
            return True, hashlib.sha256(data).hexdigest(), ct
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        return False, str(e)[:200], "error"


def main():
    rows = []
    ok = 0
    for c in CANDIDATES:
        f_ok, f_sha, ct = fetch(c["source_url"])
        row = {
            **c,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "fetched_ok": f_ok,
            "fetched_sha256": f_sha if f_ok else None,
            "content_type": ct,
            "local_path": None,
            "citation_ready": False,
            "human_verified": False,
            "rights_status": "PUBLIC_LEGAL_SOURCE; rights_scope_not_human_verified",
            "acquisition_status": "HOLD_ACCESS" if not f_ok else "PROVISIONAL_LANDING",
        }
        rows.append(row)
        if f_ok:
            ok += 1
    out = ACQUISITION_DIR / "T53_1957_1976_ACQUISITION.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T53",
        "candidates": len(CANDIDATES),
        "accessed_ok": ok,
        "fetch_failed": len(CANDIDATES) - ok,
        "out_path": str(out),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T53_1957_1976_ACQUISITION.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
