#!/usr/bin/env python3
"""把 data/excluded_master.csv 的误收清单注入本地 sqlite。

效果：
- 把对应文档在 document_classifications 表中 grade 置为'前台不展示'
- reason 字段写入剔除理由
- /excluded 前台页面会自动展示这批

用户本地运行：
    python3 scripts/ingest/ingest_excluded_master.py
"""
from __future__ import annotations
import csv, sqlite3, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
CSV_PATH = ROOT / "data" / "excluded_master.csv"


def main():
    if not DB.exists() or DB.stat().st_size == 0:
        raise SystemExit(f"sqlite 不存在或为空：{DB}")
    if not CSV_PATH.exists():
        raise SystemExit(f"CSV 不存在：{CSV_PATH}（请先跑 scripts/build/merge_excluded_master.py）")

    rows = list(csv.DictReader(CSV_PATH.open(encoding="utf-8-sig")))
    print(f"待注入 {len(rows)} 条误收", file=sys.stderr)

    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    # 确保 document_classifications 表存在
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS document_classifications (
            document_id INTEGER PRIMARY KEY,
            grade TEXT,
            reason TEXT,
            needs_review INTEGER DEFAULT 0
        )""")
    except: pass

    ok = miss = 0
    for r in rows:
        doc_key = r["doc_key"]
        d = conn.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone()
        if not d:
            miss += 1
            print(f"  ! 未找到 {doc_key}", file=sys.stderr)
            continue
        doc_id = d["id"]
        reason_text = (f"[{r['exclude_category']}] {r['specific_organization']}：{r['reason']}").strip()
        existing = conn.execute("SELECT grade FROM document_classifications WHERE document_id=?",
                                 (doc_id,)).fetchone()
        if existing:
            conn.execute(
                "UPDATE document_classifications SET grade=?, reason=?, needs_review=0 WHERE document_id=?",
                ("前台不展示", reason_text, doc_id),
            )
        else:
            conn.execute(
                "INSERT INTO document_classifications(document_id, grade, reason, needs_review) "
                "VALUES (?, '前台不展示', ?, 0)",
                (doc_id, reason_text),
            )
        ok += 1

    conn.commit(); conn.close()
    print(f"\n=== 完成 === 注入 {ok} 条 / 缺失 {miss} 条", file=sys.stderr)
    print(f"前台 /excluded 页面将自动展示新增的'前台不展示'文档", file=sys.stderr)


if __name__ == "__main__":
    main()
