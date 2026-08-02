#!/usr/bin/env python3
"""
T62 — 1957-1976 第三轮 acquisition.

更多地方民盟:
- 北京市
- 上海市
- 重庆市
- 四川省
- 云南省
- 江苏省
- 浙江省
- 安徽省
- 湖北省
- 湖南省
- 广东省
- 山东省
- 福建省
- 广西
- 贵州省
- 甘肃省
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
ACQUISITION_DIR = ROOT / "data/domestic/1957_1976_acquisition_v3_20260730"
ACQUISITION_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATES = [
    ("AA3-1957-MM-BJ", "北京市民盟 1957-1976", "https://www.bjmm.org.cn", "BJMM"),
    ("AA3-1957-MM-SH", "上海民盟 1957-1976", "https://www.minmengsh.org.cn", "SHMM"),
    ("AA3-1957-MM-CQ", "重庆民盟 1957-1976", "http://www.minmengsh.org.cn", "CQMM"),
    ("AA3-1957-MM-SC", "四川省民盟 1957-1976", "https://www.scmm.org.cn", "SCMM"),
    ("AA3-1957-MM-YN", "云南省民盟 1957-1976", "https://www.ynmm.org.cn", "YNMM"),
    ("AA3-1957-MM-JS", "江苏省民盟 1957-1976", "https://www.jsmm.org.cn", "JSMM"),
    ("AA3-1957-MM-ZJ", "浙江省民盟 1957-1976", "https://www.zjmm.org.cn", "ZJMM"),
    ("AA3-1957-MM-AH", "安徽省民盟 1957-1976", "https://www.ahmm.org.cn", "AHMM"),
    ("AA3-1957-MM-HB", "湖北省民盟 1957-1976", "https://www.hbmm.org.cn", "HBMM"),
    ("AA3-1957-MM-HN", "湖南省民盟 1957-1976", "https://www.hnmm.org.cn", "HNMM"),
    ("AA3-1957-MM-GD", "广东省民盟 1957-1976", "https://www.gdmm.org.cn", "GDMM"),
    ("AA3-1957-MM-SD", "山东省民盟 1957-1976", "https://www.sdmm.org.cn", "SDMM"),
    ("AA3-1957-MM-FJ", "福建省民盟 1957-1976", "https://www.fjmm.org.cn", "FJMM"),
    ("AA3-1957-MM-GX", "广西民盟 1957-1976", "https://www.gxmm.org.cn", "GXMM"),
    ("AA3-1957-MM-GZ", "贵州省民盟 1957-1976", "https://www.gzmm.org.cn", "GZMM"),
    ("AA3-1957-MM-GS", "甘肃省民盟 1957-1976", "https://www.gsmm.org.cn", "GSMM"),
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
    out = ACQUISITION_DIR / "T62_1957_1976_V3_CANDIDATES.jsonl"
    with open(out, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    summary = {
        "task_id": "T62",
        "candidates": len(CANDIDATES),
        "accessed_ok": ok,
        "fetch_failed": len(CANDIDATES) - ok,
        "out_path": str(out),
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T62_1957_1976_V3_ACQUISITION.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
