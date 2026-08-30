#!/usr/bin/env python3
"""下载國史館已入库档案的访客水印图（仅作内部研究参考）

流程：
1. 取 documents 中 source_platform='drnh' 的 doc_id（典藏号）
2. 对每条：
   a. 用典藏号 search → 取 acckey
   b. Display/initial/<acckey> → 取 ObjectCode
   c. Display/built/<ObjectCode>/ → 取 page_list（各页 code）
   d. 下载每页 Display/loadimg/<page_code>/original → JPG（含水印）
3. 存到 data/drnh_images/<doc_key>/p1.jpg, p2.jpg, ...
4. 更新 documents.local_html 字段记录图像路径前缀

重要：图像有「请登入」绿色水印，仅作内部研究参考，不正式发布。
"""
from __future__ import annotations

import base64
import http.cookiejar
import json
import re
import sqlite3
import ssl
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

# 忽略 SSL 证书校验错误，以连通台北档案史料网站
try:
    ssl._create_default_https_context = ssl._create_unverified_context
except AttributeError:
    pass

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
IMG_DIR = ROOT / "data" / "drnh_images"
IMG_DIR.mkdir(parents=True, exist_ok=True)
COOKIE_FILE = ROOT / "data" / "drnh_probe" / "drnh_cookies.txt"

BASE = "https://ahonline.drnh.gov.tw"


def base64m(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii").replace("/", "*")


def make_opener():
    cj = http.cookiejar.MozillaCookieJar(str(COOKIE_FILE))
    try:
        cj.load(ignore_discard=True, ignore_expires=True)
    except Exception:
        pass
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) Firefox/120"),
        ("Referer", f"{BASE}/index.php?act=Archive"),
    ]
    # 初始化 session
    if not cj:
        opener.open(f"{BASE}/index.php?act=Archive", timeout=20).read()
        cj.save(ignore_discard=True, ignore_expires=True)
    return opener, cj


def search_by_storeno(opener, store_no: str) -> str | None:
    """用典藏号搜索 → 返回 acckey（单查询单结果，取第一个 acckey）"""
    payload = {"query": [{"field": "store_no", "value": store_no, "attr": "+"}]}
    enc = urllib.parse.quote(base64m(json.dumps(payload, ensure_ascii=False, separators=(",", ":"))))
    url = f"{BASE}/index.php?act=Archive/search/{enc}"
    html = opener.open(url, timeout=40).read().decode("utf-8", errors="replace")
    # 校验：典藏号必须在 HTML 里（避免误命中其他档案）
    if store_no not in html:
        return None
    m = re.search(r"acckey='([a-f0-9]{32})'", html)
    return m.group(1) if m else None


def initial(opener, acckey: str) -> dict | None:
    """Display/initial → 取 ObjectCode + display 类型"""
    url = f"{BASE}/index.php"
    data = urllib.parse.urlencode({"act": f"Display/initial/{acckey}"}).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    resp = opener.open(req, timeout=20).read().decode("utf-8")
    obj = json.loads(resp)
    return obj.get("data") if obj.get("action") else None


def built(opener, object_code: str) -> dict | None:
    """Display/built → 取 page_list 各页 code"""
    url = f"{BASE}/index.php"
    data = urllib.parse.urlencode({"act": f"Display/built/{object_code}/"}).encode()
    req = urllib.request.Request(
        url, data=data,
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )
    resp = opener.open(req, timeout=20).read().decode("utf-8")
    obj = json.loads(resp)
    return obj.get("data") if obj.get("action") else None


def download_image(opener, page_code: str, out_path: Path) -> bool:
    if out_path.exists() and out_path.stat().st_size > 1000:
        return True  # skip
    url = f"{BASE}/index.php?act=Display/loadimg/{page_code}/original"
    try:
        resp = opener.open(url, timeout=60)
        data = resp.read()
        if len(data) < 1000:
            return False
        out_path.write_bytes(data)
        return True
    except Exception as e:
        print(f"    [img err] {e}")
        return False


def process_one(opener, doc_key: str, store_no: str) -> tuple[int, int]:
    """处理一条档案，返回 (成功页数, 总页数)"""
    sub = IMG_DIR / doc_key.replace(":", "__").replace("/", "_")
    sub.mkdir(exist_ok=True)
    meta_path = sub / "_meta.json"

    if meta_path.exists() and (sub / "p1.jpg").exists():
        m = json.loads(meta_path.read_text())
        return m.get("downloaded", 0), m.get("page_count", 0)

    acckey = search_by_storeno(opener, store_no)
    if not acckey:
        print(f"  [skip] no acckey for {store_no}")
        return 0, 0
    init = initial(opener, acckey)
    if not init:
        print(f"  [skip] initial fail for {store_no}")
        return 0, 0
    if init.get("display") != "image":
        print(f"  [skip] non-image display={init.get('display')} for {store_no}")
        # 写元数据标记非图像
        meta_path.write_text(json.dumps({"store_no": store_no, "display": init.get("display"), "page_count": 0, "downloaded": 0}, ensure_ascii=False))
        return 0, 0
    obj_code = init.get("resouse")
    if not obj_code:
        return 0, 0
    bdata = built(opener, obj_code)
    if not bdata:
        return 0, 0
    page_list = bdata.get("page_list", {})
    page_count = bdata.get("page_count", 0)
    ok = 0
    for n, code in page_list.items():
        out = sub / f"p{n}.jpg"
        if download_image(opener, code, out):
            ok += 1
        time.sleep(0.3)
    meta_path.write_text(json.dumps({
        "store_no": store_no,
        "page_count": page_count,
        "downloaded": ok,
        "page_codes": page_list,
        "object_code": obj_code,
    }, ensure_ascii=False, indent=2))
    return ok, page_count


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0  # 0 = all
    only_a = "--only-a" in sys.argv

    conn = sqlite3.connect(DB); conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    q = (
        "SELECT documents.id, doc_key, doc_id, dc.grade FROM documents "
        "LEFT JOIN document_classifications dc ON dc.document_id=documents.id "
        "WHERE source_platform='drnh'"
    )
    if only_a:
        q += " AND dc.grade='A'"
    q += " ORDER BY dc.grade, doc_id"
    rows = list(cur.execute(q).fetchall())
    if limit > 0:
        rows = rows[:limit]
    print(f"待处理: {len(rows)}")

    opener, cj = make_opener()
    total_ok = total_pages = total_docs_ok = 0
    for i, r in enumerate(rows, 1):
        doc_key = r["doc_key"]
        store_no = r["doc_id"]
        try:
            ok, pc = process_one(opener, doc_key, store_no)
        except Exception as e:
            print(f"  [{i}/{len(rows)}] {store_no} ERR: {e}")
            time.sleep(2)
            continue
        if ok > 0:
            total_docs_ok += 1
            total_ok += ok
            total_pages += pc
        if i % 10 == 0:
            print(f"[{i}/{len(rows)}] 已成功 {total_docs_ok} 个 doc, {total_ok}/{total_pages} 页")
        # 限流
        time.sleep(0.5)
        # 每 50 条保 cookie 一次
        if i % 50 == 0:
            cj.save(ignore_discard=True, ignore_expires=True)

    cj.save(ignore_discard=True, ignore_expires=True)
    print(f"\n=== 完成 ===")
    print(f"成功 docs: {total_docs_ok}/{len(rows)}")
    print(f"成功 pages: {total_ok}/{total_pages}")


if __name__ == "__main__":
    main()
