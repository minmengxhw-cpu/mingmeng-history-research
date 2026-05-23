#!/usr/bin/env python3
"""國史館檔案史料文物查詢系統探勘脚本

API 路径：
  GET https://ahonline.drnh.gov.tw/index.php?act=Archive/search/<base64m_json>
其中 base64m 是把标准 base64 的 / 换成 *。

JSON 形如 {"accnum":"0","query":[{"field":"_all","value":"<關鍵詞>"}]}

提取字段：典藏號、題名、全宗系列、本件日期、密等、提供方式、數位化、應用限制、卷名/件號
"""
from __future__ import annotations

import base64
import csv
import html as html_lib
import http.cookiejar
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "drnh_probe"
OUT_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_FILE = OUT_DIR / "drnh_cookies.txt"

BASE = "https://ahonline.drnh.gov.tw"
SEARCH = BASE + "/index.php?act=Archive/search/{enc}"
SEARCH_PAGED = BASE + "/index.php?act=Archive/search/{enc}/{start}-{end}"
INIT = BASE + "/index.php?act=Archive"

PAGE_SIZE = 100  # 台北档案史料系统支持 20/50/100, 取最大减少请求数

# 6 个核心关键词（中國民主同盟系列 + 政協 + 非法團體 + 4 民盟主要人物）
# 跳过：國民大會 19673 + 國民參政會 3571（宽泛词，命中里大部分与民盟无关）
QUERIES = [
    "中國民主同盟",   # 113
    "民主同盟",       # 266
    "民盟",           # 174
    "張瀾",           # 148
    "沈鈞儒",         # 164
    "羅隆基",         # 99
    "章伯鈞",         # 119
    "政治協商會議",   # 372
    "非法團體",       # 10
]


def base64m_encode(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii").replace("/", "*")


def init_cookies(cj: http.cookiejar.MozillaCookieJar) -> None:
    """首次 GET 拿 session cookie"""
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.open(
        urllib.request.Request(
            INIT,
            headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/120"},
        ),
        timeout=30,
    ).read()


def search_one(cj, query: str, start: int = 1, end: int = PAGE_SIZE) -> tuple[int, str]:
    payload = {"accnum": "0", "query": [{"field": "_all", "value": query}]}
    encoded = urllib.parse.quote(base64m_encode(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))))
    url = SEARCH_PAGED.format(enc=encoded, start=start, end=end)
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Firefox/120",
            "Referer": INIT,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    html = opener.open(req, timeout=60).read().decode("utf-8", errors="replace")
    m = re.search(r"共\s*(\d+)\s*筆", html)
    count = int(m.group(1)) if m else 0
    return count, html


def parse_records(html: str) -> list[dict]:
    """从 result_block 抽每条记录的完整字段"""
    items = []
    blocks = re.split(r"<div class='data_record tr_like'>", html)
    for blk in blocks[1:]:
        # 不需要再 cut 尾部（split 已经按起点切分）
        rec = {}
        # 题名 - acc_link 区域里的 <a ...>题名</a>，标签内多空格也要兼容
        m = re.search(
            r"<span class='acc_link'>.*?<a\s[^>]*>(.*?)</a>",
            blk,
            flags=re.S,
        )
        if m:
            inner = m.group(1)
            inner = re.sub(r"</?search>", "", inner)  # 高亮标记
            inner = re.sub(r"<[^>]+>", "", inner)  # 其他可能标签
            rec["題名"] = re.sub(r"\s+", " ", html_lib.unescape(inner)).strip()
        # 各字段：&#187; 是 »
        for field_match in re.finditer(
            r"<span class='field_name'>[^<]*?&#187;\s*([^<]+?)</span>\s*<span class='field_value'>(.*?)</span>\s*</div>",
            blk,
            flags=re.S,
        ):
            label = field_match.group(1).strip()
            value_html = field_match.group(2)
            value = re.sub(r"</?search>", "", value_html)
            value = re.sub(r"<[^>]+>", " ", value)
            value = re.sub(r"\s+", " ", value).strip()
            if label and value:
                rec[label] = html_lib.unescape(value)
        m = re.search(r"collection='([^']+)'\s+identifier='([^']+)'", blk)
        if m:
            rec["_collection"] = m.group(1)
            rec["_identifier"] = m.group(2)
        if rec.get("題名"):
            items.append(rec)
    return items


def main() -> None:
    # 初始化 cookie
    cj = http.cookiejar.MozillaCookieJar(str(COOKIE_FILE))
    init_cookies(cj)
    cj.save(ignore_discard=True, ignore_expires=True)

    summary = []
    all_hits = []
    for q in QUERIES:
        print(f"\n>>> 查詢: {q}")
        # 首页
        try:
            count, html = search_one(cj, q, 1, PAGE_SIZE)
        except Exception as e:
            print(f"  ERROR: {e}")
            summary.append({"query": q, "count": "ERR", "fetched": 0, "note": str(e)[:120]})
            continue
        records = parse_records(html)
        for r in records:
            r["_query"] = q
            all_hits.append(r)
        fetched = len(records)
        print(f"  總筆數: {count}, 首页({PAGE_SIZE} 笔上限) 抓取: {len(records)}")

        # 翻页
        if count > PAGE_SIZE:
            pages = (count + PAGE_SIZE - 1) // PAGE_SIZE
            for p in range(2, pages + 1):
                start = (p - 1) * PAGE_SIZE + 1
                end = min(p * PAGE_SIZE, count)
                try:
                    time.sleep(1.0)
                    _, html_p = search_one(cj, q, start, end)
                    page_recs = parse_records(html_p)
                    for r in page_recs:
                        r["_query"] = q
                        all_hits.append(r)
                    fetched += len(page_recs)
                    print(f"  第 {p}/{pages} 页 ({start}-{end}): {len(page_recs)} 笔")
                except Exception as e:
                    print(f"  第 {p}/{pages} 页 ERR: {e}")
                    continue
        summary.append({"query": q, "count": count, "fetched": fetched, "note": ""})
        time.sleep(1.0)

    # 去重（按 collection + identifier）
    dedup = {}
    for r in all_hits:
        key = (r.get("_collection", ""), r.get("_identifier", ""), r.get("題名", ""))
        if key not in dedup:
            dedup[key] = {**r, "_matched_queries": r["_query"]}
        else:
            dedup[key]["_matched_queries"] += f"; {r['_query']}"
    print(f"\n=== 去重前 {len(all_hits)} 条, 去重后 {len(dedup)} 条 ===")

    # 输出 CSV
    all_cols = set()
    for r in dedup.values():
        all_cols.update(r.keys())
    # 排序：优先核心字段
    preferred = [
        "_matched_queries", "題名",
        "典藏號", "全宗號", "全宗名稱", "全宗系列", "隸屬卷名/件號",
        "本件日期", "卷件開始日期", "卷件結束日期",
        "密等", "密等/解密紀錄", "隱私問題",
        "提供方式/地點", "閱覽方式", "數位化", "應用限制",
        "_collection", "_identifier",
    ]
    cols = preferred + sorted(c for c in all_cols if c not in preferred and c != "_query")

    with (OUT_DIR / "drnh_hits.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in dedup.values():
            w.writerow(r)

    with (OUT_DIR / "drnh_summary.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["query", "count", "fetched", "note"])
        w.writeheader()
        for row in summary:
            w.writerow(row)

    print(f"\n=== 完成 ===")
    print(f"命中: {len(dedup)} 条 -> {OUT_DIR / 'drnh_hits.csv'}")
    print(f"摘要: {len(summary)} 条 -> {OUT_DIR / 'drnh_summary.csv'}")


if __name__ == "__main__":
    main()
