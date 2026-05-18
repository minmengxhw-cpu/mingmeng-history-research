#!/usr/bin/env python3
"""中研院近代史研究所档案馆探勘脚本（v2 - 修正版）

提取每条命中的：题名、馆藏号、全宗、副全宗、系列、提供方式（数字化状态）、页数、旧档号
"""
from __future__ import annotations

import csv
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://archivesonline.mh.sinica.edu.tw"
SEARCH = BASE + "/search/?query_term={q}&query_field=text&query_op=and&match_type=phrase"
PAGE_FMT = BASE + "/refine-search/?page={p}&page_size=50"  # 翻页接口

OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "sinica_probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)

QUERIES = [
    "民主同盟", "中國民主同盟", "民盟",
    "張瀾", "沈鈞儒", "張君勱", "羅隆基", "章伯鈞",
    "黃炎培", "黃任之", "梁漱溟",
    "第三方面", "民主政團同盟", "政治協商會議",
]


def fetch(url: str, cookies: dict | None = None) -> tuple[str, dict]:
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; academic-research; mingmeng-history-research)",
        "Accept": "text/html",
        "Accept-Language": "zh-TW,zh;q=0.9",
    }
    if cookies:
        headers["Cookie"] = "; ".join(f"{k}={v}" for k, v in cookies.items())
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=30) as resp:
        # 拿 set-cookie
        new_cookies = {}
        for h, v in resp.getheaders():
            if h.lower() == "set-cookie":
                cm = re.match(r"([^=]+)=([^;]+)", v)
                if cm:
                    new_cookies[cm.group(1)] = cm.group(2)
        return resp.read().decode("utf-8", errors="replace"), new_cookies


def parse_count(html: str) -> int:
    m = re.search(r"總共找到[^0-9]*([0-9,]+)", html)
    return int(m.group(1).replace(",", "")) if m else 0


def parse_result_links(html: str) -> list[dict]:
    """解析结果页的命中条目（标题 + 详情链接）"""
    # 结果项格式：<a href="/detail/HASH/?seq=N">题名</a>
    items = []
    # 在结果块里抽
    for m in re.finditer(
        r'href="(/detail/([a-f0-9]+)/\?seq=\d+)"[^>]*>([^<]+)</a>',
        html,
    ):
        items.append({
            "detail_path": m.group(1),
            "detail_hash": m.group(2),
            "title": m.group(3).strip(),
        })
    # 去重保序
    seen = set()
    deduped = []
    for it in items:
        if it["detail_hash"] in seen:
            continue
        seen.add(it["detail_hash"])
        deduped.append(it)
    return deduped


def parse_detail(html: str) -> dict:
    """从详情页抽 dt/dd 字段"""
    res = {}
    for m in re.finditer(r"<dt[^>]*>([^<]{2,30})</dt>\s*<dd[^>]*>(.*?)</dd>", html, flags=re.S):
        label = m.group(1).strip()
        text = re.sub(r"<[^>]+>", " ", m.group(2))
        text = re.sub(r"\s+", " ", text).strip()[:400]
        res[label] = text
    # 题名通常在 <h1> 或 <h2>
    m = re.search(r"<h[12][^>]*>([^<]{2,200})</h[12]>", html)
    if m:
        res["_h1_title"] = m.group(1).strip()
    # 摘要 / 描述
    m = re.search(r"摘要[^<]*</[^>]+>\s*<[^>]+>([^<]{2,800})", html)
    if m:
        res["摘要"] = m.group(1).strip()
    return res


def main() -> None:
    # 先访问首页拿 csrftoken
    _, cookies = fetch(BASE + "/")
    summary = []
    all_hits = []

    for q in QUERIES:
        url = SEARCH.format(q=urllib.parse.quote(q))
        print(f"\n>>> {q}")
        try:
            html, _ = fetch(url, cookies)
        except Exception as e:
            print(f"  ERR: {e}")
            summary.append({"query": q, "count": "ERR", "first_page_records": 0, "note": str(e)[:120]})
            continue
        cnt = parse_count(html)
        items = parse_result_links(html)
        print(f"  總筆數: {cnt}, 首页解析记录: {len(items)}")
        summary.append({"query": q, "count": cnt, "first_page_records": len(items), "note": ""})
        for it in items:
            it["query"] = q
            all_hits.append(it)
        time.sleep(1.2)

    # 去重（同一条记录可能在多个关键词下都出现）
    print(f"\n--- 去重前 {len(all_hits)} 条 ---")
    unique = {}
    for h in all_hits:
        key = h["detail_hash"]
        if key not in unique:
            unique[key] = {**h, "matched_queries": h["query"]}
        else:
            unique[key]["matched_queries"] += f"; {h['query']}"
    print(f"--- 去重后 {len(unique)} 条 ---")

    # 拉每个详情页（限速）
    print(f"\n=== 开始拉详情 ===")
    enriched = []
    for i, (hash_, rec) in enumerate(unique.items(), 1):
        try:
            detail_html, _ = fetch(BASE + rec["detail_path"], cookies)
            fields = parse_detail(detail_html)
            rec.update(fields)
            print(f"  [{i}/{len(unique)}] {rec.get('館藏號','-')} · {rec.get('全宗','-')[:30]} · {rec['title'][:50]}")
        except Exception as e:
            print(f"  [{i}/{len(unique)}] ERR: {e}")
        enriched.append(rec)
        time.sleep(0.8)

    # 输出
    if enriched:
        cols = ["query", "matched_queries", "title", "館藏號", "全宗", "副全宗", "系列",
                "提供方式/地點", "頁數", "舊檔號", "detail_hash"]
        with (OUT_DIR / "sinica_hits.csv").open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
            w.writeheader()
            for row in enriched:
                w.writerow(row)

    with (OUT_DIR / "sinica_summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["query", "count", "first_page_records", "note"])
        w.writeheader()
        for row in summary:
            w.writerow(row)

    print(f"\n=== 完成 ===")
    print(f"命中（去重）: {len(enriched)} 条 -> {OUT_DIR / 'sinica_hits.csv'}")
    print(f"摘要: {len(summary)} 条 -> {OUT_DIR / 'sinica_summary.csv'}")


if __name__ == "__main__":
    main()
