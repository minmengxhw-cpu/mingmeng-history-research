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
TRANSLATOR = "openai-batch-v1"


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS translations (
            id INTEGER PRIMARY KEY,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            language TEXT NOT NULL,
            translator TEXT,
            status TEXT,
            text TEXT NOT NULL,
            UNIQUE(page_id, language)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS translation_fts USING fts5(
            language,
            title,
            page_label,
            text
        );
        """
    )


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
    instructions = f"""你是中国近现代史研究助理，任务是把 FRUS 英文档案译成中文研究稿。

要求：
- 忠实翻译，不增删事实，不做总结。
- 保留档号、文件号、日期、页码、注释编号。
- 人名地名按术语表处理；术语表没有的，采用常见中文译名，并保留必要的上下文。
- Federation of Chinese Democratic Parties 在 1941-1944 语境中译为“中国民主政团同盟”。
- Democratic League / Chinese Democratic League / China Democratic League 译为“中国民主同盟”。
- 输出只包含中文译文，不要解释。

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
        with urllib.request.urlopen(req, timeout=180) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {detail[:800]}") from exc
    translated = response_text(data)
    if not translated:
        raise RuntimeError("empty translation response")
    return translated


def upsert_translation(conn: sqlite3.Connection, page_id: int, title: str, page_label: str, text: str) -> None:
    existing = conn.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (page_id,),
    ).fetchone()
    if existing:
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (existing[0],))
        conn.execute("DELETE FROM translations WHERE id=?", (existing[0],))
    cur = conn.execute(
        """
        INSERT INTO translations(page_id, language, translator, status, text)
        VALUES (?, 'zh-CN', ?, ?, ?)
        """,
        (page_id, TRANSLATOR, STATUS, text),
    )
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, ?, ?, ?, ?)",
        (cur.lastrowid, "zh-CN", title, page_label or "doc-level", text),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate untranslated research-index page segments into zh-CN.")
    parser.add_argument("--limit", type=int, default=0, help="Maximum segments to translate; 0 means all.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--sleep", type=float, default=0.4)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    rows = conn.execute(
        """
        SELECT
            pages.id AS page_id,
            pages.page_label,
            pages.page_url,
            pages.text,
            documents.doc_key,
            documents.title,
            documents.date_guess
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        WHERE translations.id IS NULL
        ORDER BY documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
        """
    ).fetchall()
    if args.limit:
        rows = rows[: args.limit]

    print(f"Translating {len(rows)} segments with {args.model}.")
    done = 0
    for row in rows:
        source_ref = f"{row['doc_key']} {row['date_guess']} {row['page_url']}"
        for attempt in range(1, 4):
            try:
                zh = translate(api_key, args.model, row["title"], source_ref, row["text"])
                upsert_translation(conn, row["page_id"], row["title"], row["page_label"] or "doc-level", zh)
                conn.commit()
                done += 1
                print(f"{done}/{len(rows)} translated page_id={row['page_id']} {row['doc_key']} page={row['page_label'] or 'doc'}", flush=True)
                time.sleep(args.sleep)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError) as exc:
                print(f"attempt {attempt}/3 failed page_id={row['page_id']}: {exc}", flush=True)
                if attempt == 3:
                    raise
                time.sleep(3 * attempt)
    conn.close()
    print(f"Done. Translated {done} segments.")


if __name__ == "__main__":
    main()
