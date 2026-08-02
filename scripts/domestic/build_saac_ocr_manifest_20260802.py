#!/usr/bin/env python3
"""Build a full index of the SAAC '从五一口号到开国大典' album.

Fetch all six section pages (01..06), extract every detail-page link with its
title text, then map each candidate in the S3 queue to the matching detail page
by title-keyword similarity. Output work/domestic/SAAC_OCR_MANIFEST.json.
"""
from __future__ import annotations

import json
import re
import sqlite3
import subprocess
from html import unescape
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://www.saac.gov.cn/daj/gqzt/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
OUT = ROOT / "work/domestic/SAAC_OCR_MANIFEST.json"
QUEUE = ROOT / "work/domestic/S3_HTML_COLLECTION_QUEUE.json"
DB = ROOT / "data/research_index.sqlite"


def fetch(url: str) -> str:
    proc = subprocess.run(
        ["curl", "-sk", "-L", "-A", UA, "--connect-timeout", "15", "--max-time", "20", url],
        capture_output=True,
    )
    return proc.stdout.decode("utf-8", errors="replace")


def clean(t: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", t))).strip()


def extract_detail_pages(html: str) -> list[dict]:
    out = []
    # The album HTML is nonconformant: image anchors are unclosed (<a><img></td>).
    # Reliable title anchors are wrapped in <h3><a href="content/..">TITLE</a></h3>
    # (also tolerate missing </a> by ending at </h3>).
    for m in re.finditer(
            r'<h3[^>]*>\s*<a[^>]*?href="([^"]*?content/\d+/\d+_\d+\.html)"[^>]*>(.*?)(?:</a>\s*</h3>|</h3>)',
            html, re.S):
        href, body = m.group(1), m.group(2)
        txt = clean(body)
        if not txt or re.search(r"<img", body, re.I):
            continue
        out.append({"detail_url": urljoin(BASE, href), "title": txt})
    return out


def norm(s: str) -> set[str]:
    s = re.sub(r"[（(].*?[)）]|[年月日.,，。:：、/-]", " ", s)
    toks = set(re.findall(r"[\u3400-\u9fff]{2,}", s))
    return toks


def norm_date(s: str) -> set[str]:
    """Extract yyyy-mm-dd-ish dates as normalized tokens from either format."""
    s = s.replace("年月", "-").replace("月", "-").replace("日", "")
    dates = re.findall(r"(\d{4})-?(\d{1,2})-?(\d{1,2})", s)
    return {(y, m, d) for y, m, d in dates}


def title_sim(a: str, b: str) -> float:
    ta, tb = norm(a), norm(b)
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    sim = inter / max(len(ta), len(tb))
    # date agreement gives a strong signal for 1940s archive pieces
    if norm_date(a) & norm_date(b):
        sim += 0.35
    return sim


def main() -> int:
    detail_pages: list[dict] = []
    for sec in ("01", "02", "03", "04", "05", "05-1", "06"):
        html = fetch(BASE + f"{sec}.html")
        pages = extract_detail_pages(html)
        detail_pages.extend({"section": sec, **p} for p in pages)
        print(f"section {sec}: {len(pages)} detail pages")

    # dedupe by detail_url
    seen: dict[str, dict] = {}
    for p in detail_pages:
        seen.setdefault(p["detail_url"], p)
    detail_pages = list(seen.values())
    print(f"total detail pages: {len(detail_pages)}")

    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    saac = [x for x in queue if "saac.gov.cn" in x["source_url"]]

    manifest = []
    unmatched = []
    for cand in saac:
        title = cand["title"]
        # exact / high-sim match against detail titles
        best, best_score = None, 0.0
        for p in detail_pages:
            score = title_sim(title, p["title"])
            # boost if candidate_id section hint matches section
            m = re.search(r"-p(\d+)", cand["candidate_id"])
            hint = f"{int(m.group(1)):02d}" if m else None
            if hint and hint == p["section"]:
                score += 0.1
            if score > best_score:
                best, best_score = p, score
        entry = {"candidate_id": cand["candidate_id"], "candidate_title": title,
                 "source_url": cand["source_url"], "document_type": cand.get("document_type", "")}
        if best and best_score >= 0.25:
            entry.update({"detail_url": best["detail_url"], "section": best["section"],
                          "detail_title": best["title"], "match_score": round(best_score, 3)})
            manifest.append(entry)
        else:
            entry["detail_url"] = None
            entry["note"] = f"no title match (best_score={best_score:.3f})"
            unmatched.append(entry)

    OUT.write_text(json.dumps({"detail_pages_count": len(detail_pages), "candidates": manifest,
                               "unmatched": unmatched}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"matched: {len(manifest)} / unmatched: {len(unmatched)}")
    for u in unmatched:
        print(f"  UNMATCHED {u['candidate_id'][:40]} | {u['candidate_title'][:50]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
