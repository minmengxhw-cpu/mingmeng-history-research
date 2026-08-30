#!/usr/bin/env python3
"""
T47 — 1957-1976 web search candidates.

Search through accessible landing pages without bypass:
- marxists.org (CHINESE section, public)
- CASS (cssn.cn) public pages
- dswxyjy.org.cn (党史研究网) public pages
- mmzy.org.cn (民盟中央) public pages

Each candidate registered with stable id, source URL, retrieval date.
"""
from __future__ import annotations
import hashlib
import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime

ROOT = Path(".")
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"
ACQUISITION_DIR = ROOT / "data/domestic/1957_1976_search_20260730"
ACQUISITION_DIR.mkdir(parents=True, exist_ok=True)

# Public candidates (no login, no bypass)
CANDIDATES = [
    {
        "candidate_id": "KWR-1957-Marxists-fanyou",
        "title": "反右派斗争的相关历史文献（1957）",
        "source_url": "https://www.marxists.org/chinese/jerome/index.htm",
        "institution_type": "MARXISTS",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "反右派 民盟 1957",
        "rationale": "Marxists.org CHINESE archive; public and citable source URLs",
    },
    {
        "candidate_id": "KWR-CASS-1949-1957-overview",
        "title": "新中国初期多党合作（1949-1957）综述",
        "source_url": "https://www.cssn.cn/dukc/csddsj/",
        "institution_type": "CASS",
        "research_card_category": "SCHOLARLY_ARTICLE",
        "period": "1957-1976",
        "search_keywords": "多党合作 1957 反右 文革",
        "rationale": "CASS 当代史研究所 public landing page",
    },
    {
        "candidate_id": "KWR-MMSH-1949-1976",
        "title": "民盟中央 1949-1976 时期组织沿革",
        "source_url": "https://paper.minmengsh.gov.cn/",
        "institution_type": "MMSH",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "民盟中央 1949 反右",
        "rationale": "民盟中央 public 期刊页",
    },
    {
        "candidate_id": "KWR-CPPCC-WENSHI-1957-1976",
        "title": "政协文史资料 1957-1976 专题",
        "source_url": "https://www.cppcc.gov.cn/",
        "institution_type": "CPPCC",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "政协文史 1957 反右",
        "rationale": "全国政协 public 平台",
    },
    {
        "candidate_id": "KWR-DSWXYJY-1957",
        "title": "党史研究 1957 反右运动研究专题",
        "source_url": "https://www.dswxyjy.org.cn/",
        "institution_type": "DSWXYJY",
        "research_card_category": "SCHOLARLY_ARTICLE",
        "period": "1957-1976",
        "search_keywords": "反右 1957 民主党派",
        "rationale": "中央党史和文献研究院 public 平台",
    },
    {
        "candidate_id": "KWR-MMXY-1949-1957",
        "title": "民盟重要会议 1949 起 (第一届中央委员会)",
        "source_url": "https://www.minmengsh.org.cn/",
        "institution_type": "MMSH",
        "research_card_category": "OFFICIAL_HISTORICAL_STUDY",
        "period": "1949-1957",
        "search_keywords": "民盟 中央委员会 1949",
        "rationale": "民盟上海市委 公共平台",
    },
    {
        "candidate_id": "KWR-CASS-1957",
        "title": "1957 反右运动专题",
        "source_url": "https://www.cssn.cn/lsxzt/1957/",
        "institution_type": "CASS",
        "research_card_category": "SCHOLARLY_ARTICLE",
        "period": "1957-1976",
        "search_keywords": "1957 反右 历史",
        "rationale": "CASS 历史专题",
    },
    {
        "candidate_id": "KWR-DSWXYJY-MENG-1957",
        "title": "民盟在反右运动中的角色",
        "source_url": "https://www.dswxyjy.org.cn/n1/2019/0625/c189022-30560340.html",
        "institution_type": "DSWXYJY",
        "research_card_category": "SCHOLARLY_ARTICLE",
        "period": "1957-1976",
        "search_keywords": "民盟 反右 1957",
        "rationale": "公开学术文献中心",
    },
    {
        "candidate_id": "KWR-MARXISTS-1957",
        "title": "1957 反右派运动综合报告 (马列著作)",
        "source_url": "https://www.marxists.org/chinese/毛泽东选集/1957.htm",
        "institution_type": "MARXISTS",
        "research_card_category": "PRIMARY_SOURCE_EDITION",
        "period": "1957-1976",
        "search_keywords": "反右 1957 报告",
        "rationale": "Marxists.org 中文毛泽东选集 公开",
    },
    {
        "candidate_id": "KWR-HRMP-1957",
        "title": "中国国民党革命委员会 1957-1976 回忆录",
        "source_url": "https://www.minge.gov.cn/",
        "institution_type": "MINGE",
        "research_card_category": "OFFICIAL_RETROSPECTIVE",
        "period": "1957-1976",
        "search_keywords": "民革 1957 民主党派",
        "rationale": "民革中央 public 平台",
    },
]


def fetch_landing(url: str) -> tuple[bool, str, str]:
    """Fetch landing page (no bypass). Returns (ok, sha256, content_type)."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MiniMax-Research/2026"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content_type = resp.headers.get("Content-Type", "unknown")
            data = resp.read(1024 * 1024)  # max 1MB
            h = hashlib.sha256(data).hexdigest()
            return True, h, content_type
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, Exception) as e:
        return False, str(e)[:200], "error"


def main():
    rows = []
    accessed = 0
    for c in CANDIDATES:
        ok, h, ct = fetch_landing(c["source_url"])
        row = {
            **c,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "fetched_ok": ok,
            "fetched_sha256": h if ok else None,
            "content_type": ct,
            "local_path": None,
            "citation_ready": False,
            "human_verified": False,
            "rights_status": "PUBLIC_LEGAL_SOURCE; rights_scope_not_human_verified",
            "acquisition_status": "HOLD_ACCESS" if not ok else "PROVISIONAL_LANDING",
        }
        rows.append(row)
        if ok:
            accessed += 1
    out = ACQUISITION_DIR / "T47_1957_1976_CANDIDATES.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T47",
        "candidates": len(CANDIDATES),
        "accessed_ok": accessed,
        "fetch_failed": len(CANDIDATES) - accessed,
        "out_path": str(out),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
        "notes": "Public landing pages only; no login bypass, no paywall bypass; results are merely provisional links.",
    }
    out_json = RESEARCH_DIR / "T47_1957_1976_SEARCH.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
