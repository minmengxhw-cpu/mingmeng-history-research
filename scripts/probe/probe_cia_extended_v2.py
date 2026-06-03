#!/usr/bin/env python3
"""CIA Reading Room 扩展关键词扫描 v2
原有 62 篇 + 阶段 1 漏抓 27 篇 = 89 个 identifier 已知
本脚本用更宽关键词集（11 人物威氏拼音 + 8 概念）补扫漏抓
"""
from __future__ import annotations
import json, sys, time, urllib.request, urllib.parse, ssl
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "cia_extended_v2_candidates.csv"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 民盟核心人物威氏拼音
PEOPLE = [
    "Shih Liang",          # 史良
    "Tao Hsing-chih",      # 陶行知
    "Ma Yin-chu",          # 马寅初
    "Huang Yen-pei",       # 黄炎培
    "Hu Yu-chih",          # 胡愈之
    "Tu Pin-cheng",        # 杜斌丞
    "Li Kung-pu",          # 李公朴
    "Wen I-to",            # 闻一多
    "Chang Tung-sun",      # 张东荪
    "Chu Yun-shan",        # 储安平
    "Kao Ch'ung-min",      # 高崇民（民盟东北）
]

# 概念/事件关键词
CONCEPTS = [
    "Federation of Chinese Democratic Parties",
    '"third force" China',
    '"third party" Chiang Kai-shek',
    '"Political Consultative" 1946',
    '"minor parties" China',
    '"Democratic Parties" Peiping',
    "Coalition Government China 1946",
    "Chinese minor parties Communist",
]

def search(query, rows=50):
    url = ("https://archive.org/advancedsearch.php?"
           f"q={urllib.parse.quote(query)}"
           "&fl[]=identifier&fl[]=title&fl[]=date&fl[]=description"
           f"&rows={rows}&output=json")
    req = urllib.request.Request(url, headers={"Accept":"application/json","User-Agent":"Mozilla/5.0"})
    for attempt in range(2):
        try:
            r = urllib.request.urlopen(req, timeout=25, context=ctx).read()
            return json.loads(r)
        except Exception as e:
            if attempt == 1:
                return {"_error": str(e)[:120]}
            time.sleep(3)

def known():
    s = set()
    for m in json.load(open(ROOT/"data"/"cia_meng"/"manifest.json")):
        s.add(m["identifier"])
    miss = ROOT / "data" / "cia_missing_27_identifiers.txt"
    if miss.exists():
        for line in miss.read_text().splitlines():
            if "|" in line and not line.startswith("#"):
                ident = line.split("|",1)[1].strip()
                s.add(f"cia-readingroom-document-{ident}")
    return s

def main():
    have = known()
    print(f"已知 CIA identifier: {len(have)}", file=sys.stderr)

    all_keywords = [("person", p) for p in PEOPLE] + [("concept", c) for c in CONCEPTS]
    print(f"扫描 {len(all_keywords)} 个关键词", file=sys.stderr)

    new_finds = {}
    for kind, kw in all_keywords:
        # archive.org advancedsearch 用空格隐式 AND，collection 不加括号；人物名加引号精确匹配
        if kind == "person":
            q = f'collection:ciareadingroom "{kw}"'
        else:
            q = f'collection:ciareadingroom ({kw})'
        r = search(q, rows=80)
        if "_error" in r:
            print(f"  ✗ [{kind}] {kw}: {r['_error']}", file=sys.stderr); continue
        docs = r["response"]["docs"]
        new_in_this_kw = []
        for d in docs:
            ident = d["identifier"]
            if ident in have: continue
            if ident in new_finds:
                new_finds[ident]["matched"].append(kw); continue
            new_finds[ident] = {
                "identifier": ident,
                "title": d.get("title",""),
                "date": d.get("date","")[:10],
                "matched": [kw],
                "kind": kind,
            }
            new_in_this_kw.append(ident)
        print(f"  [{kind:7s}] {kw[:50]:50s} | 共 {len(docs):>3} 命中 | 新 {len(new_in_this_kw):>3}", file=sys.stderr)
        time.sleep(0.5)

    print(f"\n=== 新发现 (去除已知 {len(have)} 个) ===", file=sys.stderr)
    print(f"新候选: {len(new_finds)} 个 identifier", file=sys.stderr)

    # 按日期排序，过滤 1941-1957
    import csv, re
    out_rows = []
    for ident, d in new_finds.items():
        date = d["date"]
        year_match = re.match(r"(\d{4})", date)
        year = int(year_match.group(1)) if year_match else 0
        if year and not (1941 <= year <= 1957): continue
        out_rows.append({
            "identifier": ident,
            "title": d["title"][:200],
            "date": date,
            "year": year,
            "matched_keywords": "; ".join(sorted(set(d["matched"]))),
            "kind": d["kind"],
            "ia_detail_url": f"https://archive.org/details/{ident}",
        })
    out_rows.sort(key=lambda x:(x["year"], x["date"]))

    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["identifier","title","date","year","matched_keywords","kind","ia_detail_url"])
        w.writeheader()
        for r in out_rows: w.writerow(r)

    print(f"\n在 1941-1957 窗口内: {len(out_rows)} 个候选", file=sys.stderr)
    print(f"输出: {OUT}", file=sys.stderr)
    # 按年份分布
    from collections import Counter
    by_year = Counter(r["year"] for r in out_rows)
    for y in sorted(by_year):
        print(f"  {y}: {by_year[y]}", file=sys.stderr)

if __name__ == "__main__":
    main()
