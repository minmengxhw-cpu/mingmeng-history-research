#!/usr/bin/env python3
"""
T57 — 1957-1976 第二轮 acquisition.

公开渠道：
- 中国政协文史资料 (cppcc.gov.cn)
- 中国国民党革命委员会 (minge.gov.cn)
- 农工党中央 (ngd.org.cn)
- 中国致公党 (zgzgd.org.cn)
- 九三学社中央 (93.gov.cn)
- 中国社会主义学院 (civ.ac.cn)
- 国家图书馆民国期刊 (nlc.gov.cn)
- 重庆图书馆民国期刊 (cqlib.org.cn)
- 上海图书馆近代文献 (library.sh.cn)
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
ACQUISITION_DIR = ROOT / "data/domestic/1957_1976_acquisition_v2_20260730"
ACQUISITION_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    ("AA2-1957-CPPCC", "全国政协文史资料 1957-1976", "http://www.cppcc.gov.cn", "CPPCC", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-DSWXYJY", "中央党史和文献研究院 1957-1976", "https://www.dswxyjy.org.cn", "DSWXYJY", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-LIB-NLC", "国家图书馆 民国期刊 1957-1976", "http://www.nlc.cn", "NLC", "ARCHIVAL_CATALOG", "1957-1976"),
    ("AA2-1957-LIB-CQ", "重庆图书馆 民国期刊", "http://www.cqlib.org.cn", "CQLIB", "ARCHIVAL_CATALOG", "1957-1976"),
    ("AA2-1957-LIB-SH", "上海图书馆 近代文献", "http://www.library.sh.cn", "SHLIB", "ARCHIVAL_CATALOG", "1957-1976"),
    ("AA2-1957-MINZHU", "民主党派历史资料", "http://www.minge.gov.cn", "MINGE", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-NONGONG", "农工党中央 1957-1976", "http://www.ngd.org.cn", "NGD", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-ZHIGONG", "中国致公党 1957-1976", "http://www.zgzgd.org.cn", "ZGZGD", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-JIUSAN", "九三学社中央 1957-1976", "http://www.93.gov.cn", "93GOV", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-CIV", "中国社会主义学院", "https://www.civ.ac.cn", "CIV", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-MARXISTS", "Marxists.org 1957-1976 中文", "https://www.marxists.org/chinese", "MARXISTS", "PRIMARY_SOURCE_EDITION", "1957-1976"),
    ("AA2-1957-WIKI", "Wikipedia 中文 1957-1976 民盟", "https://zh.wikipedia.org/wiki/中国民主同盟", "WIKI", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
    ("AA2-1957-DATA-SH", "上海档案馆 1957-1976 民主党派", "http://www.archives.sh.cn", "SHDA", "ARCHIVAL_CATALOG", "1957-1976"),
    ("AA2-1957-WX-WIKI", "维基文库 1957-1976 民盟", "https://zh.wikisource.org/wiki/Category:中国民主同盟", "WIKISRC", "ARCHIVAL_CATALOG", "1957-1976"),
    ("AA2-1957-MMSH-SH", "民盟上海市委 1957-1976", "https://www.minmengsh.org.cn", "MMSH", "OFFICIAL_RETROSPECTIVE", "1957-1976"),
]


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MiniMax-Research/2026"})
        with urllib.request.urlopen(req, timeout=10) as r:
            ct = r.headers.get("Content-Type", "unknown")
            data = r.read(1024 * 1024)
            return True, hashlib.sha256(data).hexdigest(), ct
    except Exception as e:
        return False, str(e)[:200], "error"


def main():
    rows = []
    ok = 0
    for cid, title, url, inst, layer, period in CANDIDATES:
        f_ok, f_sha, ct = fetch(url)
        rows.append({
            "candidate_id": cid,
            "title": title,
            "source_url": url,
            "institution_type": inst,
            "research_card_category": layer,
            "research_theme_phase": period,
            "fetched_at": datetime.utcnow().isoformat() + "Z",
            "fetched_ok": f_ok,
            "fetched_sha256": f_sha if f_ok else None,
            "content_type": ct,
            "local_path": None,
            "citation_ready": False,
            "human_verified": False,
            "rights_status": "PUBLIC_LEGAL_SOURCE; rights_scope_not_human_verified",
            "acquisition_status": "HOLD_ACCESS" if not f_ok else "PROVISIONAL_LANDING",
        })
        if f_ok:
            ok += 1
    out = ACQUISITION_DIR / "T57_1957_1976_V2_CANDIDATES.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T57",
        "candidates": len(CANDIDATES),
        "accessed_ok": ok,
        "fetch_failed": len(CANDIDATES) - ok,
        "out_path": str(out),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T57_1957_1976_V2_ACQUISITION.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
