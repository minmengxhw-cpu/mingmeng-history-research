#!/usr/bin/env python3
"""把 data/newspapersg/zh_translations.csv 注入本地 sqlite。

配套 translate_newspapersg_deepseek.py 使用：
- 那个脚本输出 CSV 进 git
- 这个脚本在本地把 CSV 注入 sqlite（依赖本地已 ingest 过 newspapersg documents/pages）

运行：
    python3 scripts/ingest/ingest_newspapersg_translations_from_csv.py
"""
from __future__ import annotations
import csv, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
CSV_PATH = ROOT / "data" / "newspapersg" / "zh_translations.csv"

STATUS = "machine-reviewed-newspapersg-deepseek-2026-06-02"
TRANSLATOR = "deepseek-v4-flash-newspapersg"

def main():
    if not DB.exists() or DB.stat().st_size == 0:
        raise SystemExit(f"sqlite 不存在或为空：{DB}。请先跑 build_research_index.py + ingest_newspapersg_meng.py")
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV 不存在：{CSV_PATH}。请先跑 translate_newspapersg_deepseek.py")

    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    print(f"待注入 {len(rows)} 篇翻译", file=sys.stderr)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    ok = miss = 0
    for r in rows:
        doc_key_full = f"newspapersg:{r['doc_key']}"
        # 找该文档的 pages（NewspaperSG 是单页结构，doc 与 page 1:1 或 1:N）
        d = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key_full,)).fetchone()
        if not d:
            miss += 1
            print(f"  ! 文档 {doc_key_full} 未入 sqlite（先跑 ingest_newspapersg_meng.py）", file=sys.stderr)
            continue
        doc_id = d["id"]
        pages = conn.execute("SELECT id FROM pages WHERE document_id=? ORDER BY id", (doc_id,)).fetchall()
        if not pages:
            miss += 1
            print(f"  ! 文档 {doc_key_full} 无 pages 行", file=sys.stderr)
            continue
        # 翻译挂第 1 页（doc-level 译文）
        page_id = pages[0]["id"]
        existing = conn.execute(
            "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
            (page_id,),
        ).fetchone()
        if existing:
            trans_id = existing["id"]
            conn.execute(
                "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
                (r["zh_text"], STATUS, TRANSLATOR, trans_id),
            )
            conn.execute("DELETE FROM translation_fts WHERE rowid=?", (trans_id,))
        else:
            cur = conn.execute(
                "INSERT INTO translations(page_id, language, translator, status, text) VALUES (?, 'zh-CN', ?, ?, ?)",
                (page_id, TRANSLATOR, STATUS, r["zh_text"]),
            )
            trans_id = cur.lastrowid
        conn.execute(
            "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
            (trans_id, r.get("title_zh", r["title"]), "doc-level", r["zh_text"]),
        )
        ok += 1

    # 同步更新 title_translations.csv（前端读这个做题名渲染）
    title_csv = ROOT / "data" / "newspapersg" / "title_translations.csv"
    existing_titles = {}
    if title_csv.exists():
        for row in csv.DictReader(title_csv.open(encoding="utf-8-sig")):
            existing_titles[row["title"]] = row["title_zh"]
    for r in rows:
        if r["title_zh"]:
            existing_titles[r["title"]] = r["title_zh"]
    with title_csv.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["title", "title_zh"])
        for t in sorted(existing_titles):
            w.writerow([t, existing_titles[t]])

    conn.commit(); conn.close()
    print(f"\n=== 完成 === 注入 {ok} 条 / 缺失 {miss} 条", file=sys.stderr)
    print(f"已同步 title_translations.csv", file=sys.stderr)


if __name__ == "__main__":
    main()
