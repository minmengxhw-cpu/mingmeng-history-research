#!/usr/bin/env python3
"""把三源（NewspaperSG / CIA / HathiTrust）的 exclude 决定合并为统一黑名单。

输入：
- data/newspapersg/exclusions.csv（NewspaperSG 复核结果，1 篇剔除）
- data/excluded_org_final.csv（CIA + HathiTrust 复核结果，6 篇剔除）

输出：
- data/excluded_master.csv（统一误收清单，含 platform / doc_key / 剔除类别 / 理由）

用户本地用此 CSV 配合 ingest_excluded_master.py 把 grade 置为'前台不展示'。
"""
from __future__ import annotations
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "excluded_master.csv"


def load_newspapersg():
    p = ROOT / "data" / "newspapersg" / "exclusions.csv"
    if not p.exists(): return []
    out = []
    for r in csv.DictReader(p.open(encoding="utf-8-sig")):
        if r.get("decision") == "exclude":
            out.append({
                "platform": "newspapersg",
                "doc_key": f"newspapersg:{r['doc_key']}",
                "title": r.get("title", ""),
                "date": r.get("date", ""),
                "specific_organization": r.get("specific_org", ""),
                "exclude_category": r.get("exclude_category", ""),
                "reason": r.get("reason", "")[:500],
                "source_script": "review_newspapersg_exclusions.py",
            })
    return out


def load_cia_ht():
    p = ROOT / "data" / "excluded_org_final.csv"
    if not p.exists(): return []
    out = []
    for r in csv.DictReader(p.open(encoding="utf-8-sig")):
        if r.get("decision") == "exclude":
            out.append({
                "platform": r["platform"],
                "doc_key": r["doc_key"],
                "title": r.get("title", ""),
                "date": r.get("date", ""),
                "specific_organization": r.get("specific_organization", ""),
                "exclude_category": r.get("exclude_category", ""),
                "reason": r.get("reason", "")[:500],
                "source_script": "scan_excluded_organizations.py",
            })
    return out


def main():
    rows = load_newspapersg() + load_cia_ht()
    print(f"汇总 {len(rows)} 条误收清单", file=sys.stderr)

    fields = ["platform", "doc_key", "title", "date",
              "specific_organization", "exclude_category", "reason", "source_script"]
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in sorted(rows, key=lambda x: (x["platform"], x["date"])):
            w.writerow(r)

    from collections import Counter
    by_plat = Counter(r["platform"] for r in rows)
    by_cat = Counter(r["exclude_category"] for r in rows)
    print(f"\n按平台分布:", file=sys.stderr)
    for k, v in by_plat.items(): print(f"  {k}: {v}", file=sys.stderr)
    print(f"\n按类别分布:", file=sys.stderr)
    for k, v in by_cat.items(): print(f"  {k}: {v}", file=sys.stderr)
    print(f"\n输出: {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
