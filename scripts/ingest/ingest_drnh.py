#!/usr/bin/env python3
"""國史館档案 ingest 脚本 — 把分级后 A+B 档元数据入本平台 documents 表

入库范围：docs/drnh/drnh_classified.csv 中 _priority='A' 或 'B' 共 475 条
入库后：
- source_platform='drnh'
- pages 表每条 doc 1 个 page（合并题名 + 内容描述作为原文）
- translations 表注入繁→简体作为 zh-CN（标 translator='zhconv-auto'）
- document_classifications 标 A 或 B
- url 指向台北档案史料按典藏号搜索结果（用户点链接可直达档案 detail）
"""
from __future__ import annotations

import base64
import csv
import json
import sqlite3
import sys
import urllib.parse
from pathlib import Path

import zhconv

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "research_index.sqlite"
HITS = ROOT / "docs" / "drnh" / "drnh_classified.csv"

BASE = "https://ahonline.drnh.gov.tw"


def base64m_encode(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii").replace("/", "*")


def make_drnh_url(store_no: str) -> str:
    """构造台北档案史料按典藏号搜索的 URL（用户点开后能直达档案 detail）"""
    if not store_no:
        return ""
    payload = {"query": [{"field": "store_no", "value": store_no, "attr": "+"}]}
    enc = urllib.parse.quote(
        base64m_encode(json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
    )
    return f"{BASE}/index.php?act=Archive/search/{enc}"


def t2s(text: str) -> str:
    if not text:
        return ""
    return zhconv.convert(text, "zh-cn")


def ingest(dry_run: bool = False):
    rows = list(csv.DictReader(open(HITS, encoding="utf-8")))
    target = [r for r in rows if r.get("_priority") in ("A", "B")]
    print(f"加载 {len(rows)} 条，待入库 A+B {len(target)} 条")

    conn = sqlite3.connect(DB)
    cur = conn.cursor()

    # 1. sources 表加 drnh
    cur.execute(
        "INSERT OR IGNORE INTO sources(source_type, source_id, title, origin_url, local_path) "
        "VALUES(?, ?, ?, ?, ?)",
        ("drnh", "DRNH", "國史館檔案史料文物查詢系統", "https://ahonline.drnh.gov.tw", ""),
    )
    source_id = cur.execute(
        "SELECT id FROM sources WHERE source_type='drnh' AND source_id='DRNH'"
    ).fetchone()[0]
    print(f"source_id = {source_id}")

    # 2. 清旧 drnh 数据（保证幂等）
    if not dry_run:
        # 删 pages / translations / classifications 联级
        cur.execute(
            "DELETE FROM translations WHERE page_id IN ("
            "SELECT pages.id FROM pages JOIN documents ON pages.document_id=documents.id "
            "WHERE documents.source_platform='drnh')"
        )
        cur.execute(
            "DELETE FROM pages WHERE document_id IN ("
            "SELECT id FROM documents WHERE source_platform='drnh')"
        )
        cur.execute(
            "DELETE FROM document_classifications WHERE document_id IN ("
            "SELECT id FROM documents WHERE source_platform='drnh')"
        )
        n_del = cur.execute(
            "DELETE FROM documents WHERE source_platform='drnh'"
        ).rowcount
        print(f"清理旧 drnh 记录: {n_del} 条")

    # 二次去重（A+B 内同一 store_no 多次命中）
    seen_keys = set()
    unique_target = []
    for r in target:
        sn = (r.get("典藏號") or "").strip()
        if not sn or sn in seen_keys:
            continue
        seen_keys.add(sn)
        unique_target.append(r)
    print(f"A+B 二次去重: {len(target)} → {len(unique_target)}")

    inserted = 0
    for r in unique_target:
        store_no = (r.get("典藏號") or "").strip()
        if not store_no:
            continue

        title_zh_hant = (r.get("題名") or "").strip()
        if not title_zh_hant:
            continue
        title_zh_hans = t2s(title_zh_hant)

        fonds_name = (r.get("全宗名稱") or "").strip()
        fonds_id = (r.get("_collection") or "").split(store_no.split("-")[0])[0] if False else ""
        # 简化：volume_id 用全宗号（典藏号前缀 3 位），volume_title 用全宗名称
        fonds_no = store_no.split("-")[0] if "-" in store_no else (r.get("_collection") or "")[:3]

        doc_key = f"drnh:{store_no}"
        url = make_drnh_url(store_no)
        date_str = (r.get("本件日期") or r.get("_year") or "").strip()
        priority = r.get("_priority")
        reason = r.get("_reason") or ""
        matched = r.get("_matched_queries") or ""

        if dry_run:
            print(f"\n--- DRY RUN sample ---")
            print(f"  doc_key: {doc_key}")
            print(f"  volume_id: {fonds_no}  volume_title: {fonds_name}")
            print(f"  doc_id: {store_no}")
            print(f"  title (繁): {title_zh_hant[:60]}")
            print(f"  title→简体: {title_zh_hans[:60]}")
            print(f"  date_guess: {date_str}")
            print(f"  url: {url[:100]}")
            print(f"  priority: {priority}, reason: {reason[:80]}")
            if inserted >= 2:
                break
            inserted += 1
            continue

        # 插 documents
        cur.execute(
            """INSERT INTO documents(
                source_id, doc_key, volume_id, volume_title,
                doc_id, doc_number, title, date_guess, url,
                local_html, local_txt, hit_type, matched_terms, source_platform
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                source_id, doc_key, fonds_no, fonds_name,
                store_no, "", title_zh_hant, date_str, url,
                "", "", priority.lower() + "_drnh", matched, "drnh",
            ),
        )
        doc_id_db = cur.lastrowid

        # 插 pages：1 条 doc 1 个 page；原文 = 繁体题名（台北档案史料未提供全文 OCR）
        page_text = title_zh_hant
        # 如果有内容描述附加
        desc = (r.get("內容描述") or "").strip()
        if desc and desc != title_zh_hant:
            page_text = title_zh_hant + "\n\n" + desc

        cur.execute(
            "INSERT INTO pages(document_id, page_label, page_url, text) VALUES (?,?,?,?)",
            (doc_id_db, "doc-level", url, page_text),
        )
        page_id_db = cur.lastrowid

        # 插 translations：简体作为「翻译」（实际是繁→简）
        trans_text = t2s(page_text)
        cur.execute(
            "INSERT INTO translations(page_id, language, translator, status, text) "
            "VALUES (?,?,?,?,?)",
            (page_id_db, "zh-CN", "zhconv-auto", "auto-converted", trans_text),
        )

        # 插 document_classifications
        score_map = {"A": 90, "B": 60}
        cur.execute(
            """INSERT INTO document_classifications(
                document_id, grade, score, reason, needs_review
            ) VALUES (?,?,?,?,?)""",
            (doc_id_db, priority, score_map.get(priority, 50), reason, 1 if priority == "B" else 0),
        )

        inserted += 1
        if inserted % 50 == 0:
            print(f"  已入库 {inserted}/{len(target)}")

    if not dry_run:
        conn.commit()
    conn.close()
    print(f"\n=== 完成 ===")
    print(f"入库 documents: {inserted}")


if __name__ == "__main__":
    dry = "--dry" in sys.argv
    ingest(dry_run=dry)
