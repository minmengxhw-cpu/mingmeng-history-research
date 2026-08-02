#!/usr/bin/env python3
"""
T67 — 1957-1976 v4 民主党派文献资源.
"""
from __future__ import annotations
import hashlib
import json
import urllib.request
from pathlib import Path
from datetime import datetime

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"
ACQUISITION_DIR = ROOT / "data/domestic/1957_1976_v4_20260730"
ACQUISITION_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    ("AA4-1957-MINGE", "民革中央 1957-1976", "https://www.minge.gov.cn", "MINGE"),
    ("AA4-1957-NONGONG", "农工党中央 1957-1976", "https://www.ngd.org.cn", "NGD"),
    ("AA4-1957-ZHIGONG", "致公党中央 1957-1976", "https://www.zgzgd.org.cn", "ZGZGD"),
    ("AA4-1957-JIUSAN", "九三学社中央 1957-1976", "https://www.93.gov.cn", "93GOV"),
    ("AA4-1957-TAIWAN", "台盟中央 1957-1976", "https://www.taimeng.org.cn", "TAIMENG"),
    ("AA4-1957-MINJIAN", "民建中央 1957-1976", "https://www.cndca.org.cn", "MINJIAN"),
    ("AA4-1957-MINJIN", "民进中央 1957-1976", "https://www.mj.org.cn", "MINJIN"),
    ("AA4-1957-NONGPING", "民进中央 1957-1976", "https://www.mj.org.cn", "MINJIN"),
    ("AA4-1957-MENG-MINGZHU", "民盟中央 1957-1976", "https://www.minmengsh.org.cn", "MMSH"),
    ("AA4-1957-MENG-WENSHI", "民盟中央文史 1957-1976", "https://www.minmengsh.org.cn", "MMSH"),
    ("AA4-1957-MENG-PUB", "民盟中央出版 1957-1976", "https://www.minmengsh.org.cn", "MMSH"),
    ("AA4-1957-SHANGHAI-MENG", "上海民盟 1957-1976", "https://www.minmengsh.org.cn", "SHMM"),
    ("AA4-1957-BEIJING-MENG", "北京民盟 1957-1976", "https://www.bjmm.org.cn", "BJMM"),
    ("AA4-1957-WUHAN-MENG", "武汉民盟 1957-1976", "https://www.whmm.org.cn", "WHMM"),
    ("AA4-1957-NANJING-MENG", "南京民盟 1957-1976", "https://www.njmm.org.cn", "NJMM"),
    ("AA4-1957-CHONGQING-MENG", "重庆民盟 1957-1976", "https://www.cqmm.org.cn", "CQMM"),
]


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MiniMax-Research/2026"})
        with urllib.request.urlopen(req, timeout=8) as r:
            ct = r.headers.get("Content-Type", "unknown")
            data = r.read(1 << 20)
            return True, hashlib.sha256(data).hexdigest(), ct
    except Exception as e:
        return False, str(e)[:200], "error"


def main():
    rows = []
    ok = 0
    for cid, title, url, inst in CANDIDATES:
        f_ok, f_sha, ct = fetch(url)
        rows.append({
            "candidate_id": cid,
            "title": title,
            "source_url": url,
            "institution_type": inst,
            "research_card_category": "OFFICIAL_RETROSPECTIVE",
            "research_theme_phase": "1957-1976",
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
    out = ACQUISITION_DIR / "T67_1957_1976_V4_CANDIDATES.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T67",
        "candidates": len(CANDIDATES),
        "accessed_ok": ok,
        "fetch_failed": len(CANDIDATES) - ok,
        "out_path": str(out),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T67_1957_1976_V4_ACQUISITION.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
