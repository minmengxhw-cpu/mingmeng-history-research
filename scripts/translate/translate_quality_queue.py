#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"
GLOSSARY_PATH = Path.cwd() / "data" / "translation_glossary.csv"
API_URL = "https://api.openai.com/v1/responses"
DEFAULT_MODEL = os.environ.get("FRUS_TRANSLATION_MODEL", "gpt-4.1-mini")
STATUS = "machine-draft-review-needed"
TRANSLATOR = "openai-quality-batch-v1"


def glossary_text() -> str:
    if not GLOSSARY_PATH.exists():
        return ""
    rows = list(csv.DictReader(GLOSSARY_PATH.open(encoding="utf-8")))
    return "\n".join(f"- {row['term']} => {row['translation']} ({row['note']})" for row in rows)


def response_text(payload: dict) -> str:
    if "output_text" in payload:
        return payload["output_text"].strip()
    parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(content.get("text", ""))
    return "\n".join(parts).strip()


def translate(api_key: str, model: str, title: str, source_ref: str, text: str) -> str:
    instructions = f"""你是中国近现代政治史与 FRUS 档案研究助理。请把英文档案逐段译为中文研究稿。

硬性要求：
- 忠实翻译英文原文，不增删事实，不写摘要，不写说明。
- 保留档号、文件号、日期、页码、脚注编号、括号信息。
- 专名按术语表统一；术语表没有的，采用中国近现代史通行译名。确无把握的人名可保留英文并加括号说明“原文转写”。
- Democratic League / Chinese Democratic League / China Democratic League 译为“中国民主同盟”或“民盟”。
- Federation of Chinese Democratic Parties 在 1941-1944 年语境译为“中国民主政团同盟”。
- Political Consultative Council / Conference 译为“政治协商会议”或“政协”。
- Generalissimo 通常译为“委员长”，不要误译为普通“将军”。
- 输出只包含中文译文。

术语表：
{glossary_text()}"""
    body = {
        "model": model,
        "instructions": instructions,
        "input": f"标题：{title}\n来源：{source_ref}\n\n英文原文：\n{text}",
        "temperature": 0.1,
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=240) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:800]}") from exc
    translated = response_text(payload)
    if not translated:
        raise RuntimeError("empty translation response")
    return translated


def fetch_queue(conn: sqlite3.Connection, limit: int, max_chars: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        WITH issue_stats AS (
            SELECT
                page_id,
                count(*) AS issue_count,
                max(severity) AS max_severity,
                group_concat(DISTINCT issue_type) AS issue_types
            FROM translation_quality_issues
            GROUP BY page_id
        )
        SELECT
            pages.id AS page_id,
            pages.page_label,
            pages.page_url,
            pages.text,
            documents.doc_key,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade,
            translations.id AS translation_id,
            issue_stats.issue_count,
            issue_stats.max_severity,
            issue_stats.issue_types,
            (
                issue_stats.max_severity * 100
                + issue_stats.issue_count * 10
                + CASE COALESCE(dc.grade, '')
                    WHEN '核心文献' THEN 80
                    WHEN '相关文献' THEN 45
                    WHEN '人物关联' THEN 25
                    ELSE 0
                  END
                + CASE WHEN documents.matched_terms LIKE '%Lo Lung-chi%' THEN 30 ELSE 0 END
                + CASE WHEN documents.matched_terms LIKE '%Democratic League%' THEN 20 ELSE 0 END
            ) AS priority_score
        FROM issue_stats
        JOIN pages ON pages.id = issue_stats.page_id
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        WHERE length(pages.text) <= ?
        ORDER BY priority_score DESC, documents.date_guess, pages.id
        LIMIT ?
        """,
        (max_chars, limit),
    ).fetchall()
    return rows


def upsert_translation(conn: sqlite3.Connection, row: sqlite3.Row, text: str) -> None:
    existing = conn.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (row["page_id"],),
    ).fetchone()
    if existing:
        translation_id = existing["id"]
        conn.execute(
            """
            UPDATE translations
            SET text=?, translator=?, status=?
            WHERE id=?
            """,
            (text, TRANSLATOR, STATUS, translation_id),
        )
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (translation_id,))
    else:
        cur = conn.execute(
            """
            INSERT INTO translations(page_id, language, translator, status, text)
            VALUES (?, 'zh-CN', ?, ?, ?)
            """,
            (row["page_id"], TRANSLATOR, STATUS, text),
        )
        translation_id = cur.lastrowid
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
        (translation_id, row["title"], row["page_label"] or "doc-level", text),
    )
    conn.execute("DELETE FROM translation_quality_issues WHERE page_id=?", (row["page_id"],))


def main() -> None:
    parser = argparse.ArgumentParser(description="Retranslate pages that are currently in the quality issue queue.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--max-chars", type=int, default=6500)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--sleep", type=float, default=0.4)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = fetch_queue(conn, args.limit, args.max_chars)
    print(f"Retranslating {len(rows)} queued pages with {args.model}.")
    done = 0
    for row in rows:
        source_ref = f"{row['doc_key']} {row['date_guess']} {row['page_url']}"
        for attempt in range(1, 4):
            try:
                zh = translate(api_key, args.model, row["title"], source_ref, row["text"])
                upsert_translation(conn, row, zh)
                conn.commit()
                done += 1
                print(
                    f"{done}/{len(rows)} translated page_id={row['page_id']} {row['doc_key']} issues={row['issue_types']}",
                    flush=True,
                )
                time.sleep(args.sleep)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                print(f"attempt {attempt}/3 failed page_id={row['page_id']}: {exc}", flush=True)
                if attempt == 3:
                    raise
                time.sleep(3 * attempt)
    conn.close()
    print(f"Done. Translated {done} queued pages.")


if __name__ == "__main__":
    main()
