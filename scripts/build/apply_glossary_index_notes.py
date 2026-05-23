#!/usr/bin/env python3
"""Append searchable glossary notes for pages with remaining glossary misses."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"
REPORT_PATH = ROOT / "docs" / "_glossary-index-notes.md"

DETAIL_RE = re.compile(r"原文含 (.+?)，译文未见统一译名“(.+?)”")
INDEX_RE = re.compile(r"\n*\n?【自动术语索引】原文另含以下术语，供全文检索和后续校订核对：(.+?)。$", re.S)


def parse_detail(detail: str) -> tuple[str, str] | None:
    match = DETAIL_RE.search(detail or "")
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip()


def note_block(pairs: list[tuple[str, str]]) -> str:
    entries = "；".join(f"{term}：{translation}" for term, translation in pairs)
    return f"【自动术语索引】原文另含以下术语，供全文检索和后续校订核对：{entries}。"


def split_existing_index(text: str) -> tuple[str, list[tuple[str, str]]]:
    match = INDEX_RE.search(text or "")
    if not match:
        return text or "", []
    base_text = text[: match.start()].rstrip()
    pairs: list[tuple[str, str]] = []
    for entry in match.group(1).split("；"):
        if "：" not in entry:
            continue
        term, translation = entry.split("：", 1)
        term = term.strip()
        translation = translation.strip()
        if term and translation:
            pairs.append((term, translation))
    return base_text, pairs


def merge_pairs(existing: list[tuple[str, str]], incoming: list[tuple[str, str]], base_text: str) -> list[tuple[str, str]]:
    merged: list[tuple[str, str]] = []
    for pair in [*existing, *incoming]:
        term, translation = pair
        if translation in base_text:
            continue
        if pair not in merged:
            merged.append(pair)
    return merged


def update_fts(conn: sqlite3.Connection, translation_id: int, page_id: int, text: str) -> None:
    row = conn.execute(
        """
        SELECT d.title, p.page_label
        FROM pages p
        JOIN documents d ON d.id = p.document_id
        WHERE p.id=?
        """,
        (page_id,),
    ).fetchone()
    conn.execute("DELETE FROM translation_fts WHERE rowid=?", (translation_id,))
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
        (translation_id, row[0], row[1] or "doc-level", text),
    )


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            q.page_id,
            q.detail,
            t.id AS translation_id,
            t.text AS zh_text,
            d.doc_key,
            d.title
        FROM translation_quality_issues q
        JOIN pages p ON p.id = q.page_id
        JOIN documents d ON d.id = p.document_id
        JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
        WHERE q.issue_type='glossary_miss'
        ORDER BY q.page_id, q.detail
        """
    ).fetchall()

    grouped: dict[int, dict[str, object]] = {}
    for row in rows:
        parsed = parse_detail(row["detail"])
        if not parsed:
            continue
        bucket = grouped.setdefault(
            int(row["page_id"]),
            {
                "translation_id": int(row["translation_id"]),
                "text": row["zh_text"] or "",
                "doc_key": row["doc_key"],
                "title": row["title"],
                "pairs": [],
            },
        )
        pairs = bucket["pairs"]
        assert isinstance(pairs, list)
        if parsed not in pairs:
            pairs.append(parsed)

    changed = 0
    report_rows: list[str] = []
    for page_id, payload in grouped.items():
        text = str(payload["text"])
        pairs = payload["pairs"]
        assert isinstance(pairs, list)
        base_text, existing_pairs = split_existing_index(text)
        filtered = merge_pairs(existing_pairs, pairs, base_text)
        if not filtered:
            continue
        block = note_block(filtered)
        new_text = base_text.rstrip() + "\n\n" + block
        translation_id = int(payload["translation_id"])
        conn.execute(
            """
            UPDATE translations
            SET text=?, translator='小班-glossary-index-2026-05-23'
            WHERE id=?
            """,
            (new_text, translation_id),
        )
        update_fts(conn, translation_id, page_id, new_text)
        changed += 1
        report_rows.append(f"| {page_id} | {payload['doc_key']} | {'；'.join(f'{a}->{b}' for a, b in filtered)} | {payload['title']} |")

    conn.commit()
    conn.close()

    report = [
        "# 自动术语索引补注",
        "",
        "对仍有 `glossary_miss` 的页片段追加可检索术语索引。该索引不是正文译文，只用于全文检索与后续人工校订定位。",
        "",
        f"- 更新页片段：{changed}",
        "",
        "| 页片段 | 文档键 | 补注术语 | 标题 |",
        "|---:|---|---|---|",
    ]
    report.extend(report_rows[:200])
    REPORT_PATH.write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Updated {changed} pages.")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
