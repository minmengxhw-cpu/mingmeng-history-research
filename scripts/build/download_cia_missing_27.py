#!/usr/bin/env python3
"""从 archive.org CIA Reading Room 镜像下载漏抓 27 篇的 OCR + metadata。
输出到 /tmp/cia-missing/cia-readingroom-document-<ident>/_djvu.txt + metadata.json
"""
import json, time, sys
from pathlib import Path
import urllib.request, ssl

SRC = Path("/tmp/missing_26.txt")
OUT = Path("/tmp/cia-missing")
OUT.mkdir(exist_ok=True)

IA_BASE = "https://archive.org"
ctx = ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
def get(url, max_retry=3):
    for i in range(max_retry):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            return urllib.request.urlopen(req, timeout=30, context=ctx).read()
        except Exception as e:
            if i == max_retry-1: return None
            time.sleep(3 * (2**i))

ids = []
for line in SRC.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#"): continue
    date, ident = line.split("|", 1)
    ids.append((date, ident.strip()))

print(f"待下载: {len(ids)} 篇", file=sys.stderr)
ok = err = 0
for i, (date, ident) in enumerate(ids, 1):
    # IA item 标识 = cia-readingroom-document-<ident>
    item = f"cia-readingroom-document-{ident}"
    dst = OUT / item
    dst.mkdir(exist_ok=True)
    djvu_url = f"{IA_BASE}/download/{item}/{item}_djvu.txt"
    meta_url = f"{IA_BASE}/metadata/{item}"
    djvu = get(djvu_url)
    meta = get(meta_url)
    if djvu and meta:
        (dst / f"{item}_djvu.txt").write_bytes(djvu)
        m = json.loads(meta)
        # 抽出关键 metadata
        md = {
            "identifier": item,
            "ia_identifier": ident,
            "date": date,
            "title": m.get("metadata", {}).get("title", ""),
            "description": m.get("metadata", {}).get("description", ""),
            "ia_date": m.get("metadata", {}).get("date", ""),
            "creator": m.get("metadata", {}).get("creator", ""),
            "subject": m.get("metadata", {}).get("subject", ""),
            "detail_url": f"{IA_BASE}/details/{item}",
            "pdf_url": f"{IA_BASE}/download/{item}/{item}.pdf",
            "djvu_size": len(djvu),
        }
        (dst / "metadata.json").write_text(json.dumps(md, ensure_ascii=False, indent=2))
        ok += 1
        print(f"  [{i}/{len(ids)}] ✓ {date} | {ident} | {md['title'][:50]} ({len(djvu)//1024} KB OCR)", file=sys.stderr)
    else:
        err += 1
        print(f"  [{i}/{len(ids)}] ✗ {date} | {ident} | djvu={bool(djvu)} meta={bool(meta)}", file=sys.stderr)
    time.sleep(1.0)
print(f"\n=== 完成 === 成功 {ok} / 失败 {err}", file=sys.stderr)
