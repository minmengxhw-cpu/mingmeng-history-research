#!/usr/bin/env python3
"""英国国家档案馆 Kew Discovery 目录探勘脚本

对一组民盟相关关键词，跑 1941-1950 命中目录，输出命中条目（参考号、卷宗名、
形成日期、馆藏处、批次摘要）的 CSV 量表。
"""
from __future__ import annotations

import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://discovery.nationalarchives.gov.uk/API/search/v1/records"
OUT_DIR = Path(__file__).resolve().parent.parent / "data" / "kew_probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# 关键词：组织名 + 人物（中英对照）+ 主题
QUERIES = [
    # 组织名
    '"Chinese Democratic League"',
    '"China Democratic League"',
    '"Democratic League"',
    "Min Meng",
    # 1947 民盟非法事件相关
    '"Democratic League" outlawed',
    '"Democratic League" suppressed',
    # 香港时期
    '"Democratic League" Hong Kong',
    # 主要领袖
    "Chang Lan",
    "Carsun Chang",
    "Lo Lung-chi",
    '"Lo Lung-ki"',
    "Shen Chun-ju",
    '"Chang Po-chun"',
    "Tan Ping-shan",
    # 第三方面 / 第三党
    '"third party" China',
    "Kuomintang opposition parties",
]

DATE_FROM = "1941-01-01"
DATE_TO = "1950-12-31"
PAGE_SIZE = 50  # API 单页上限不明，先取 50


def search(query: str, page: int = 0) -> dict:
    params = {
        "sps.searchQuery": query,
        "sps.dateFrom": DATE_FROM,
        "sps.dateTo": DATE_TO,
        "sps.resultsPageSize": str(PAGE_SIZE),
        "sps.page": str(page),
    }
    qs = urllib.parse.urlencode(params)
    url = f"{API}?{qs}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "Mozilla/5.0 (academic-research; mingmeng-history-research)",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def flatten_record(r: dict, query: str) -> dict:
    return {
        "query": query,
        "iaid": r.get("id"),
        "ref": r.get("reference"),
        "title": (r.get("title") or "").replace("\n", " ").strip()[:300],
        "date": r.get("coveringDates"),
        "held_by": r.get("heldBy", {}).get("description")
        if isinstance(r.get("heldBy"), dict)
        else (r.get("heldBy") if isinstance(r.get("heldBy"), str) else ""),
        "catalogue_level": r.get("catalogueLevelCode"),
        "department": r.get("department"),
        "url": f"https://discovery.nationalarchives.gov.uk/details/r/{r.get('id')}"
        if r.get("id")
        else "",
    }


def main() -> None:
    all_hits = []
    summary = []
    for q in QUERIES:
        print(f"\n>>> 查询: {q}")
        try:
            data = search(q)
        except Exception as e:
            print(f"  ERROR: {e}")
            summary.append({"query": q, "count": "ERR", "note": str(e)[:120]})
            continue
        count = data.get("count", 0)
        records = data.get("records", [])
        print(f"  命中总数: {count}, 本页返回: {len(records)}")
        summary.append({"query": q, "count": count, "note": f"first_page={len(records)}"})

        for r in records:
            all_hits.append(flatten_record(r, q))

        # 友好限流
        time.sleep(1.2)

    # 输出
    hits_path = OUT_DIR / "kew_hits.csv"
    summary_path = OUT_DIR / "kew_summary.csv"

    if all_hits:
        with hits_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(all_hits[0].keys()))
            w.writeheader()
            for row in all_hits:
                w.writerow(row)
    with summary_path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["query", "count", "note"])
        w.writeheader()
        for row in summary:
            w.writerow(row)

    print(f"\n=== 完成 ===")
    print(f"命中条目: {len(all_hits)} -> {hits_path}")
    print(f"查询摘要: {len(summary)} -> {summary_path}")


if __name__ == "__main__":
    main()
