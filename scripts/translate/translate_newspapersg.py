#!/usr/bin/env python3
"""Translate and relevance-review NewspaperSG documents.

Writes:
- zh-CN translations into data/research_index.sqlite translations + translation_fts
- data/newspapersg/title_translations.csv for UI title rendering
- data/newspapersg/relevance_review.csv for audit trail

The SQLite database is intentionally not tracked by git; this script is the
reproducible way to rebuild the local translation layer.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sqlite3
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"
GLOSSARY_PATH = ROOT / "data" / "translation_glossary.csv"
TITLE_CSV = ROOT / "data" / "newspapersg" / "title_translations.csv"
REVIEW_CSV = ROOT / "data" / "newspapersg" / "relevance_review.csv"
API_URL = "https://api.openai.com/v1/responses"
MODEL = os.environ.get("NEWSPAPERSG_TRANSLATION_MODEL", "gpt-4.1-mini")
STATUS = "machine-reviewed-newspapersg-2026-06-02"
TRANSLATOR = "openai-gpt-4.1-mini-newspapersg"


SYSTEM = """你是中国民主同盟史、民国政治史和英属南洋报刊史研究助理。请把 NewspaperSG 报刊 OCR 文本处理成可入库的中文研究译文，并同时判断是否应保留在“中国民主同盟史料库”。

要求：
1. 忠实翻译或校订，不增加档案外事实；英文报道译成现代中文，中文繁体/旧字报道整理为现代简体中文。
2. 保留人名、机构、地名、日期、数量、引号内政治口号；明显 OCR 错字可按上下文校正。
3. Democratic League / Chinese Democratic League / China Democratic League 在中国语境下一律译为“中国民主同盟”；Federation of Chinese Democratic Parties 译为“中国民主政团同盟”。
4. 若文本实际说的是 Malayan Democratic Union、Malayan Democratic League、台湾民主同盟，或只是普通“民主同盟”而非中国民主同盟，应判为“剔除”。
5. 相关度只保留与中国民主同盟密切相关的材料：直接报道民盟组织、分部、领导人、非法化、政治主张、反内战活动、南洋华侨民盟活动，或与民盟核心人物/事件直接相关。
6. 输出必须是 JSON，不要 markdown，不要解释。"""


def glossary_text() -> str:
    if not GLOSSARY_PATH.exists():
        return ""
    rows = []
    with GLOSSARY_PATH.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            term = (row.get("term") or "").strip()
            trans = (row.get("translation") or "").strip()
            note = (row.get("note") or "").strip()
            if term and trans:
                rows.append(f"{term} = {trans}" + (f"（{note}）" if note else ""))
    return "\n".join(rows[:150])


def response_text(payload: dict) -> str:
    if payload.get("output_text"):
        return payload["output_text"].strip()
    parts: list[str] = []
    for item in payload.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"}:
                parts.append(content.get("text", ""))
    return "\n".join(parts).strip()


def parse_json_text(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", text, re.S)
        if not m:
            raise
        return json.loads(m.group(0))


def call_openai(api_key: str, title: str, date_guess: str, url: str, text: str, glossary: str) -> dict:
    prompt = f"""术语表：
{glossary}

报刊题名：{title}
日期：{date_guess}
原始链接：{url}

OCR 原文：
{text}

请返回 JSON，字段：
- title_zh: 题名中文译名，简洁准确
- relevance: "keep" 或 "drop"
- grade: "核心文献"、"相关文献"、"人物关联"、"背景材料"、"前台不展示" 之一
- score: 0-100 的相关度分
- reason: 一句话说明为什么保留或剔除
- zh_text: 完整中文译文或中文校订稿
"""
    body = {
        "model": MODEL,
        "instructions": SYSTEM,
        "input": prompt,
        "temperature": 0.1,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "newspapersg_translation_review",
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["title_zh", "relevance", "grade", "score", "reason", "zh_text"],
                    "properties": {
                        "title_zh": {"type": "string"},
                        "relevance": {"type": "string", "enum": ["keep", "drop"]},
                        "grade": {
                            "type": "string",
                            "enum": ["核心文献", "相关文献", "人物关联", "背景材料", "前台不展示"],
                        },
                        "score": {"type": "integer", "minimum": 0, "maximum": 100},
                        "reason": {"type": "string"},
                        "zh_text": {"type": "string"},
                    },
                },
            }
        },
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=240) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return parse_json_text(response_text(payload))


def upsert_translation(conn: sqlite3.Connection, page_id: int, title: str, page_label: str, text: str) -> None:
    existing = conn.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (page_id,),
    ).fetchone()
    if existing:
        trans_id = existing["id"]
        conn.execute(
            "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
            (text, STATUS, TRANSLATOR, trans_id),
        )
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (trans_id,))
    else:
        cur = conn.execute(
            "INSERT INTO translations(page_id, language, translator, status, text) VALUES (?, 'zh-CN', ?, ?, ?)",
            (page_id, TRANSLATOR, STATUS, text),
        )
        trans_id = cur.lastrowid
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
        (trans_id, title, page_label or "doc-level", text),
    )


def title_map_from_csv() -> dict[str, str]:
    if not TITLE_CSV.exists():
        return {}
    out: dict[str, str] = {}
    with TITLE_CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            title = (row.get("title") or "").strip()
            title_zh = (row.get("title_zh") or "").strip()
            if title and title_zh:
                out[title] = title_zh
    return out


def write_title_csv(mapping: dict[str, str]) -> None:
    TITLE_CSV.parent.mkdir(parents=True, exist_ok=True)
    with TITLE_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["title", "title_zh"])
        for title in sorted(mapping):
            writer.writerow([title, mapping[title]])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--force", action="store_true", help="Retranslate rows even if status already matches.")
    parser.add_argument("--sleep", type=float, default=0.2)
    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set.")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            d.id AS document_id, d.doc_key, d.title, d.date_guess, d.url,
            p.id AS page_id, p.page_label, p.text,
            t.status AS zh_status
        FROM documents d
        JOIN pages p ON p.document_id=d.id
        LEFT JOIN translations t ON t.page_id=p.id AND t.language='zh-CN'
        WHERE d.source_platform='newspapersg'
        ORDER BY d.date_guess, d.doc_key, p.id
        """
    ).fetchall()
    if not args.force:
        rows = [r for r in rows if r["zh_status"] != STATUS]
    if args.limit:
        rows = rows[: args.limit]

    titles = title_map_from_csv()
    glossary = glossary_text()
    review_rows: list[dict[str, object]] = []
    print(f"NewspaperSG rows to process: {len(rows)}")
    for idx, row in enumerate(rows, 1):
        for attempt in range(1, 4):
            try:
                res = call_openai(
                    api_key,
                    row["title"] or "",
                    row["date_guess"] or "",
                    row["url"] or "",
                    row["text"] or "",
                    glossary,
                )
                title_zh = (res.get("title_zh") or row["title"] or "").strip()
                zh_text = (res.get("zh_text") or "").strip()
                grade = str(res.get("grade") or "前台不展示")
                relevance = str(res.get("relevance") or "drop")
                score = int(res.get("score") or 0)
                reason = str(res.get("reason") or "").strip()
                if relevance == "drop":
                    grade = "前台不展示"
                    score = min(score, 30)
                if not zh_text:
                    raise RuntimeError("empty zh_text")

                titles[row["title"]] = title_zh
                upsert_translation(conn, row["page_id"], title_zh, row["page_label"] or "1", zh_text)
                conn.execute(
                    """
                    INSERT INTO document_classifications(document_id, grade, score, reason, needs_review)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(document_id) DO UPDATE SET
                        grade=excluded.grade,
                        score=excluded.score,
                        reason=excluded.reason,
                        needs_review=excluded.needs_review
                    """,
                    (row["document_id"], grade, score, reason, 0 if relevance == "keep" else 1),
                )
                conn.commit()
                review_rows.append(
                    {
                        "doc_key": row["doc_key"],
                        "date": row["date_guess"] or "",
                        "title": row["title"] or "",
                        "title_zh": title_zh,
                        "relevance": relevance,
                        "grade": grade,
                        "score": score,
                        "reason": reason,
                    }
                )
                print(f"{idx}/{len(rows)} {grade} {score} {row['doc_key']} -> {title_zh}", flush=True)
                time.sleep(args.sleep)
                break
            except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, RuntimeError, json.JSONDecodeError) as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:700] if isinstance(exc, urllib.error.HTTPError) else str(exc)
                print(f"attempt {attempt}/3 failed {row['doc_key']}: {detail}", flush=True)
                if attempt == 3:
                    raise
                time.sleep(2 * attempt)

    write_title_csv(titles)
    if review_rows:
        with REVIEW_CSV.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["doc_key", "date", "title", "title_zh", "relevance", "grade", "score", "reason"],
            )
            writer.writeheader()
            writer.writerows(review_rows)
    conn.close()
    print(f"title translations: {TITLE_CSV}")
    print(f"review report: {REVIEW_CSV}")


if __name__ == "__main__":
    main()
