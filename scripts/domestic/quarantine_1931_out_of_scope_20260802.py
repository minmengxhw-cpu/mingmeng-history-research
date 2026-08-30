#!/usr/bin/env python3
"""Quarantine the 1931 out-of-scope Dagongbao documents from front-facing views.

Marks document_classifications.grade = '前台不展示' for the four documents that
hold 1931 (pre-1941) content mislabeled as 1947. This follows the same
convention used by scripts/build/exclude_cia_off_topic.py; app.py filters every
front-facing route on grade != '前台不展示' and lists them on /excluded.

The rows themselves (pages, provenance, fts) are intentionally preserved so the
quarantine is reversible and the provenance audit trail stays intact.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path("data/research_index.sqlite")

QUARANTINE_IDS = [1243, 1245, 1112, 1113, 1171, 1172]

REASON = "[隔离:1931范围外] 大公报 1931 年 11/12 月卷（1947 误标），民盟史 1941—1949 范围外；移出前台检索"


def main() -> int:
    with sqlite3.connect(DB) as conn:
        cur = conn.cursor()
        updated = 0
        for did in QUARANTINE_IDS:
            exists = cur.execute(
                "SELECT document_id, grade FROM document_classifications WHERE document_id=?", (did,)
            ).fetchone()
            if exists is None:
                cur.execute(
                    "INSERT INTO document_classifications (document_id, grade, score, reason) VALUES (?, '前台不展示', 0, ?)",
                    (did, REASON),
                )
            elif exists[1] != "前台不展示":
                cur.execute(
                    "UPDATE document_classifications SET grade='前台不展示', reason=COALESCE(reason||'；','')||? WHERE document_id=?",
                    (REASON, did),
                )
            else:
                print(f"  ⊙ [{did}] 已是 前台不展示，跳过")
                continue
            updated += 1
            title = cur.execute("SELECT title FROM documents WHERE id=?", (did,)).fetchone()[0]
            print(f"  ✓ [{did}] 已隔离：{title[:55]}")
    print(f"\n共隔离 {updated} 个文档（489 页移出前台检索，物理数据保留可回滚）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
