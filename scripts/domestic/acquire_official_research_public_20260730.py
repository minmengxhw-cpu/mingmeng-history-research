#!/usr/bin/env python3
"""公开网页/PDF 抓取 — 民盟官方研究层 (Phase 2)

不绕过登录；记录 URL、MIME、字节、SHA256、时间、版权说明。
"""
import json
import hashlib
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
BASE_OUT_HTML = ROOT / "data/domestic/official_research_public_20260730/html"
BASE_OUT_PDF = ROOT / "data/domestic/official_research_public_20260730/pdf"
MANIFEST = ROOT / "work/domestic/minimax_official_research_20260730/03_acquisition/ACQUISITION_MANIFEST.jsonl"
HOLD_FILE = ROOT / "work/domestic/minimax_official_research_20260730/03_acquisition/ACCESS_HOLD.jsonl"
RECS_FILE = ROOT / "work/domestic/minimax_official_research_20260730/02_records/OFFICIAL_RESEARCH_RECORDS.jsonl"

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
MAX_BYTES = 300 * 1024 * 1024  # 300 MB
TIMEOUT = 45  # seconds


def safe_filename(s: str) -> str:
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in s)[:80]


def fetch(url: str, out_path: Path) -> dict:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    # 用 curl 抓取
    try:
        result = subprocess.run(
            ["curl", "-sSL", "-A", UA, "--max-time", str(TIMEOUT),
             "-o", str(out_path), "-w", "%{http_code}|%{content_type}|%{size_download}",
             url],
            capture_output=True, text=True, timeout=TIMEOUT + 5
        )
        parts = (result.stdout or "").strip().split("|")
        http_code = parts[0] if len(parts) > 0 else "000"
        ctype = parts[1] if len(parts) > 1 else ""
        size = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
        err = result.stderr[:200] if result.stderr else ""
    except Exception as e:
        http_code, ctype, size = "000", "", 0
        err = str(e)
    if not out_path.exists() or out_path.stat().st_size == 0:
        sha = ""
        size = 0
    else:
        size = out_path.stat().st_size
        sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
    ended = datetime.now(timezone.utc).isoformat()
    ok = 200 <= int(http_code) < 400 and size > 0
    mime = ctype.split(";")[0].strip() if ctype else ""
    hold_reason = None
    if not ok:
        if "timeout" in (err or "").lower() or http_code == "000":
            hold_reason = "TIMEOUT_OR_UNREACHABLE"
        elif "404" in str(http_code) or "403" in str(http_code):
            hold_reason = "ACCESS_BLOCKED_OR_404"
        else:
            hold_reason = f"HTTP_{http_code}"
    elif size > MAX_BYTES:
        hold_reason = "OVERSIZE_300MB"
    return {
        "url": url, "out_path": str(out_path), "http_code": http_code,
        "mime": mime, "bytes": size, "sha256": sha,
        "started_at": started, "ended_at": ended,
        "ok": ok, "hold_reason": hold_reason, "curl_error": err[:200],
    }


def main():
    records = [json.loads(l) for l in RECS_FILE.read_text().splitlines() if l.strip()]
    candidates = [r for r in records if r.get("source_url")]
    print(f"待处理: {len(candidates)} 条记录")
    # 去重 URL
    seen_urls = set()
    unique = []
    for r in candidates:
        u = r["source_url"]
        if u in seen_urls:
            continue
        seen_urls.add(u)
        unique.append(r)
    print(f"去重 URL: {len(unique)} 个")

    manifest = []
    hold = []
    fetched_count = 0
    hold_count = 0
    for i, r in enumerate(unique, 1):
        url = r["source_url"]
        title = r.get("title", "")[:40]
        cat = r.get("research_card_category", "")
        inst = r.get("institution_type", "")
        # 跳过明确需要登录的：minmeng1941.cn 详细页、孔夫子商家、孔网私人
        if "minmeng1941.cn" in url:
            hold.append({
                "candidate_id": r.get("candidate_id"), "url": url, "title": title,
                "institution_type": inst, "research_card_category": cat,
                "hold_reason": "MINMENG1941_LOGIN_REQUIRED",
                "note": "民盟历史文献全媒体数据库：需登录，按任务禁止访问 MMDA 登录正文",
            })
            hold_count += 1
            continue
        if "kongfz.com" in url or "jd.com" in url or "taobao.com" in url:
            # 这些是商业列表，仅作目录核验
            hold.append({
                "candidate_id": r.get("candidate_id"), "url": url, "title": title,
                "institution_type": inst, "research_card_category": cat,
                "hold_reason": "COMMERCIAL_BOOK_LISTING",
                "note": "孔夫子/京东/淘宝商家销售页：仅作书目核验，不作为正式全文来源",
            })
            hold_count += 1
            continue

        # 跳过 MMSH 已经在 P3 ACQUIRED_SNAPSHOT 的（避免重复下载）
        # 但对未获取的 URL，正常下载
        ext = "html"
        if ".pdf" in url.lower():
            ext = "pdf"
        elif ".htm" in url.lower() or ".aspx" in url.lower():
            ext = "html"
        # 文件名
        fname = f"{r.get('candidate_id') or 'unk'}_{safe_filename(title)}_{i:03d}.{ext}"
        out_path = (BASE_OUT_PDF if ext == "pdf" else BASE_OUT_HTML) / fname
        if out_path.exists() and out_path.stat().st_size > 0:
            # 已存在
            sha = hashlib.sha256(out_path.read_bytes()).hexdigest()
            res = {
                "url": url, "out_path": str(out_path), "http_code": "200",
                "mime": "application/pdf" if ext == "pdf" else "text/html",
                "bytes": out_path.stat().st_size, "sha256": sha,
                "started_at": "", "ended_at": datetime.now(timezone.utc).isoformat(),
                "ok": True, "hold_reason": None, "curl_error": "",
                "cached": True,
            }
        else:
            res = fetch(url, out_path)
            if res["ok"]:
                fetched_count += 1
            else:
                hold.append({
                    "candidate_id": r.get("candidate_id"), "url": url, "title": title,
                    "institution_type": inst, "research_card_category": cat,
                    "hold_reason": res["hold_reason"] or "UNKNOWN",
                    "note": res.get("curl_error", "")[:200],
                })
                hold_count += 1
        # 版权说明
        copyright_note = {
            "MMZY": "民盟中央官网：站点版权声明以 mmzy.org.cn 站规为准；用于官方研究/学术研究，引用需注明来源",
            "MMSH": "民盟上海市委：站点版权声明以 minmengsh.gov.cn 站规为准；引用需注明来源",
            "MMHIST": "正式汇编收录内容：汇编版权所有方为出版方；引用需注明汇编名+页码",
            "MM1941": "民盟历史文献全媒体数据库：登录后公开；本任务不获取登录内容",
            "QY": "群言出版社/民盟中央直属出版社：出版物版权属群言出版社；学术引用须注明出版社与 ISBN/页码",
            "MMC": "民盟中央官方：站点版权以 mmzy.org.cn 为准",
            "MX": "民盟内部资料汇编：上海民盟；引用须标注出处",
            "RCL": "上海民主党派志验收稿：上海市地方志办公室；引用须标注验收稿出处",
            "SHDPZ": "上海民主党派志：上海市地方志办公室；引用须标注章节",
            "BJDCMM": "民盟北京市东城区委：站点版权按该站声明；引用须注明来源",
            "SCU": "高校学术机构收录：版权依原汇编方；引用须注明汇编与收录机构",
            "default": "公开页面/汇编/出版物：按来源版权声明与学术引用规范",
        }.get(inst, "公开页面/汇编/出版物：按来源版权声明与学术引用规范")
        rec = {
            **res,
            "candidate_id": r.get("candidate_id"),
            "title": title,
            "institution_type": inst,
            "research_card_category": cat,
            "research_theme_phase": r.get("research_theme_phase"),
            "copyright_note": copyright_note,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "acquisition_method": "curl_public_get_no_auth",
            "batch_id": "minimax_official_research_20260730",
        }
        manifest.append(rec)
        if i % 10 == 0:
            print(f"  [{i}/{len(unique)}] ok={fetched_count} hold={hold_count}")
        # 速率限制
        time.sleep(0.5)

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST.open("w") as f:
        for m in manifest:
            f.write(json.dumps(m, ensure_ascii=False) + "\n")
    with HOLD_FILE.open("w") as f:
        for h in hold:
            f.write(json.dumps(h, ensure_ascii=False) + "\n")
    print(f"\n完成: 抓取 {fetched_count} 个，HOLD {hold_count} 个")
    print(f"  Manifest: {MANIFEST}")
    print(f"  Hold: {HOLD_FILE}")


if __name__ == "__main__":
    main()