#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sqlite3
from pathlib import Path


ROOT = Path.cwd()
DB_PATH = ROOT / "data" / "research_index.sqlite"
OUT_DIR = ROOT / "exports"


TOPICS = {
    "kunming-assassinations": {
        "title": "昆明暗杀与民盟政治压力",
        "terms": ["Kunming", "assassin", "assassination", "李公朴", "闻一多", "暗杀", "昆明"],
    },
    "pcc-1946": {
        "title": "1946 年政治协商会议",
        "terms": ["Political Consultative", "PCC", "政治协商", "政协", "国民大会", "Steering Committee"],
    },
    "marshall-mediation": {
        "title": "马歇尔调处与民盟",
        "terms": ["Marshall", "马歇尔", "truce", "cease", "停战", "调处", "mediation"],
    },
    "third-force": {
        "title": "第三方面与中间路线",
        "terms": ["Third Party", "third party", "third force", "第三方面", "中间路线", "Youth Party", "Democratic Socialist"],
    },
    "peiping-1949": {
        "title": "1949 年北平接触",
        "terms": ["Peiping", "1949", "北平", "Clubb", "Lo Lung-chi", "Chang Lan", "Li Chi-shen"],
    },
}


PEOPLE = {
    "lo-lung-chi": {"title": "罗隆基", "terms": ["Lo Lung-chi", "Lo Lung Chi", "Lo Lung", "罗隆基", "罗龙基", "罗龙志", "洛龙芝"]},
    "chang-lan": {"title": "张澜", "terms": ["Chang Lan", "Chang Piao-fang", "张澜"]},
    "liang-shu-ming": {"title": "梁漱溟", "terms": ["Liang Shu-ming", "梁漱溟"]},
    "shen-chun-ju": {"title": "沈钧儒", "terms": ["Shen Chun-ju", "沈钧儒"]},
    "huang-yen-pei": {"title": "黄炎培", "terms": ["Huang Yen-pei", "黄炎培", "黄延培"]},
    "chang-po-chun": {"title": "章伯钧", "terms": ["Chang Po-chun", "章伯钧"]},
    "shih-liang": {"title": "史良", "terms": ["Shih Liang", "史良"]},
    "carsun-chang": {"title": "张君劢", "terms": ["Carsun Chang", "Chang Chun-mai", "张君劢", "嘉善昌"]},
    "chang-tung-sun": {"title": "张东荪", "terms": ["Chang Tung-sun", "Chang Tung Sun", "张东荪", "张敦善"]},
    "chou-en-lai": {"title": "周恩来", "terms": ["Chou En-lai", "Chou Enlai", "周恩来", "周将军"]},
}


def compact(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def alias_where(columns: list[str], aliases: list[str]) -> tuple[str, list[str]]:
    parts = []
    params: list[str] = []
    for alias in aliases:
        like = f"%{alias}%"
        for column in columns:
            parts.append(f"{column} LIKE ?")
            params.append(like)
    return "(" + " OR ".join(parts) + ")", params


def year_from(row: sqlite3.Row) -> str:
    text = f"{row['date_guess'] or ''} {row['volume_id'] or ''} {row['doc_key'] or ''}"
    match = re.search(r"\b(19[4-5][0-9])\b", text)
    return match.group(1) if match else "未注明"


def fetch_rows(kind: str, slug: str, limit: int) -> tuple[str, list[sqlite3.Row]]:
    if kind == "topic":
        item = TOPICS[slug]
    elif kind == "person":
        item = PEOPLE[slug]
    else:
        raise ValueError("kind must be topic or person")

    where, params = alias_where(
        ["documents.title", "documents.matched_terms", "pages.text", "translations.text"],
        item["terms"],
    )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"""
        SELECT
            pages.id AS page_id,
            pages.page_label,
            pages.page_url,
            pages.text AS original_text,
            documents.volume_id,
            documents.doc_id,
            documents.doc_key,
            documents.volume_title,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade,
            translations.text AS zh_text,
            translations.status AS zh_status
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        WHERE {where}
        GROUP BY pages.id
        ORDER BY documents.date_guess, documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
        LIMIT ?
        """,
        tuple(params + [limit]),
    ).fetchall()
    conn.close()
    return item["title"], rows


def render_markdown(title: str, rows: list[sqlite3.Row], excerpt_chars: int) -> str:
    out = [
        f"# {title}",
        "",
        f"- 文档数：{len({row['doc_key'] for row in rows})}",
        f"- 片段数：{len(rows)}",
        "",
    ]
    current_year = None
    for row in rows:
        year = year_from(row)
        if year != current_year:
            out.extend([f"## {year}", ""])
            current_year = year
        page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
        out.extend(
            [
                f"### {row['date_guess'] or '未注明日期'} · {row['title']}",
                "",
                f"- 文档：`{row['volume_id']}/{row['doc_id']}`",
                f"- 等级：{row['grade'] or '未分级'}",
                f"- 引用位置：{page}",
                f"- FRUS：{row['page_url']}",
                f"- 片段：`page_id={row['page_id']}`",
                "",
                "**原文摘录**",
                "",
                f"> {compact(row['original_text'], excerpt_chars)}",
                "",
                f"**中文译文（{row['zh_status'] or '未标注'}）**",
                "",
                f"> {compact(row['zh_text'], excerpt_chars)}",
                "",
            ]
        )
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description="Export topic or person research notes as Markdown.")
    parser.add_argument("--topic", choices=sorted(TOPICS))
    parser.add_argument("--person", choices=sorted(PEOPLE))
    parser.add_argument("--limit", type=int, default=300)
    parser.add_argument("--excerpt-chars", type=int, default=900)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    if bool(args.topic) == bool(args.person):
        raise SystemExit("Choose exactly one of --topic or --person.")

    kind = "topic" if args.topic else "person"
    slug = args.topic or args.person
    title, rows = fetch_rows(kind, slug, args.limit)
    OUT_DIR.mkdir(exist_ok=True)
    out_path = args.out or OUT_DIR / f"{kind}_{slug}_notes.md"
    out_path.write_text(render_markdown(title, rows, args.excerpt_chars), encoding="utf-8")
    print(f"Wrote {out_path}")
    print(f"Exported {len(rows)} snippets from {len({row['doc_key'] for row in rows})} documents.")


if __name__ == "__main__":
    main()
