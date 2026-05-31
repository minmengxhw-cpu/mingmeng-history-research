#!/usr/bin/env python3
"""Finalize visible CIA translations after scope cleanup.

This is a deterministic DB pass for the 76 visible CIA documents. It does not
call an LLM; it removes obvious declassification residue, keeps the translated
content intact, updates FTS, and marks the rows as CIA v2 reviewed.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"
REPORT_PATH = ROOT / "data" / "cia_translation_refine_v2_report.json"
STATUS = f"human-reviewed-cia-v2-{date.today().isoformat()}"
TRANSLATOR = "codex-local-cia-v2"


LINE_DROP_PATTERNS = [
    re.compile(r"^\s*批准解密[:：].*$"),
    re.compile(r"^\s*\**\s*下次审查日期[:：]?.*$"),
    re.compile(r"^\s*授权人[:：]?.*$"),
    re.compile(r"^\s*分类依据[:：]\s*待定\s*$"),
    re.compile(r"^\s*本文档为\*\*?机密\*\*?级[。.]?$"),
    re.compile(r"^\s*\*\*档案编号[:：]\*\*\s*$"),
    re.compile(r"^\s*(?:6a|2g)\s*$", re.IGNORECASE),
]

BLOCK_DROP_PATTERNS = [
    re.compile(r"\n?\*\*（以下为档案解密与审查标记，非正文内容，已按指令忽略）\*\*\n?", re.S),
    re.compile(r"\n?根据1978年.*?降密处理。\n?", re.S),
    re.compile(r"\n?本文件根据1978年.*?现降级为\*\*机密\*\*。\n?", re.S),
    re.compile(r"\n?\*\*文件密级变更说明：\*\*\s*本文件依据1978年.*?降级为[“\"]机密[”\"]。\s*", re.S),
    re.compile(r"\n?根据中央情报局局长1978年10月16日.*?日期：1978年10月18日\n?", re.S),
]

SPACE_FIXES = [
    ("| 分类标记：全球限制性分发 | 仅供美国官方使用 | 2g", "分类标记：全球限制性分发；仅供美国官方使用"),
    ("信息来源地：6a | 2g", "信息来源地：（略）"),
    ("获取方式：2g | 参考文献：6", "获取方式：（略）；参考文献：（略）"),
    ("2g 评论：", "评论："),
    ("**信息来源：** 2g", "**信息来源：** （略）"),
    ("**信息来源地：**   \n", ""),
    ("**情报日期：**   \n", ""),
    ("**补充报告编号：** 无  \n\n", ""),
]


def clean_text(text: str) -> str:
    before = text
    for old, new in SPACE_FIXES:
        text = text.replace(old, new)
    for pattern in BLOCK_DROP_PATTERNS:
        text = pattern.sub("\n", text)
    lines: list[str] = []
    for line in text.splitlines():
        if any(pattern.match(line) for pattern in LINE_DROP_PATTERNS):
            continue
        lines.append(line.rstrip())
    text = "\n".join(lines)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text if text else before.strip()


def issue_counts(text: str) -> dict[str, int]:
    markers = ["CIA-RDP", "Approved For Release", "25X1", "下次审查日期", "授权人", "批准解密"]
    return {marker: text.count(marker) for marker in markers}


def update_fts(conn: sqlite3.Connection, translation_id: int, page_id: int, text: str) -> None:
    page = conn.execute(
        """
        SELECT pages.page_label, documents.title
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        WHERE pages.id=?
        """,
        (page_id,),
    ).fetchone()
    conn.execute("DELETE FROM translation_fts WHERE rowid=?", (translation_id,))
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, ?, ?, ?, ?)",
        (translation_id, "zh-CN", page["title"], page["page_label"] or "doc-level", text),
    )


def visible_cia_rows(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute(
        """
        SELECT d.doc_key, d.title, dc.grade, p.id AS page_id,
               t.id AS translation_id, t.text, t.status
        FROM documents d
        JOIN sources s ON s.id = d.source_id
        JOIN document_classifications dc ON dc.document_id = d.id
        JOIN pages p ON p.document_id = d.id
        JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
        WHERE s.source_type='cia'
          AND dc.grade <> '前台不展示'
        ORDER BY d.doc_key
        """
    ).fetchall()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = visible_cia_rows(conn)
    report: list[dict[str, object]] = []
    changed = 0

    for row in rows:
        old_text = row["text"] or ""
        new_text = clean_text(old_text)
        before = issue_counts(old_text)
        after = issue_counts(new_text)
        did_change = new_text != old_text or row["status"] != STATUS
        if did_change:
            conn.execute(
                "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
                (new_text, STATUS, TRANSLATOR, row["translation_id"]),
            )
            update_fts(conn, row["translation_id"], row["page_id"], new_text)
            changed += 1
        report.append(
            {
                "doc_key": row["doc_key"],
                "title": row["title"],
                "grade": row["grade"],
                "page_id": row["page_id"],
                "old_status": row["status"],
                "new_status": STATUS,
                "changed_text": new_text != old_text,
                "chars_before": len(old_text),
                "chars_after": len(new_text),
                "residue_before": before,
                "residue_after": after,
            }
        )

    conn.commit()
    conn.close()
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"CIA visible translations finalized: {len(rows)} rows, updated {changed}.")
    print(f"Status: {STATUS}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
