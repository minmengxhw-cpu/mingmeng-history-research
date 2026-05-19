#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "research_index.sqlite"
sys.path.insert(0, str(ROOT))

from app import bibliography_entry, compact, short_citation, source_page_label, split_terms, translate_title


def slugify(value: str) -> str:
    value = re.sub(r"\s+", "-", value.strip())
    value = re.sub(r"[^\w\-\u4e00-\u9fff]+", "", value)
    return value or "events"


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def fetch_rows(scope_type: str, value: str) -> list[sqlite3.Row]:
    base_sql = """
        SELECT
            e.scope_type,
            e.scope_slug,
            e.scope_name,
            e.event_date,
            e.event_year,
            e.event_title,
            e.event_summary,
            e.actors,
            e.tags,
            e.places,
            e.organizations,
            e.importance,
            e.page_id,
            pages.page_label,
            pages.page_url,
            pages.text AS original_text,
            documents.volume_id,
            documents.doc_id,
            documents.doc_key,
            documents.volume_title,
            documents.title,
            documents.date_guess,
            documents.url AS doc_url,
            COALESCE(dc.grade, '') AS grade,
            translations.text AS zh_text,
            translations.status AS zh_status
        FROM research_events e
        JOIN pages ON pages.id = e.page_id
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
    """
    order_sql = """
        ORDER BY
            e.event_year,
            documents.date_guess,
            documents.volume_id,
            CAST(documents.doc_number AS INTEGER),
            pages.id,
            e.importance DESC
    """
    with conn() as c:
        if scope_type in {"person", "topic"}:
            return c.execute(
                base_sql + " WHERE e.scope_type=? AND e.scope_slug=? " + order_sql,
                (scope_type, value),
            ).fetchall()
        rows = c.execute(base_sql + " " + order_sql).fetchall()

    column = "places" if scope_type == "place" else "organizations"
    filtered = []
    seen: set[tuple[int, str]] = set()
    for row in rows:
        if value not in split_terms(row[column]):
            continue
        key = (row["page_id"], row["event_title"])
        if key in seen:
            continue
        seen.add(key)
        filtered.append(row)
    return filtered


def scope_title(scope_type: str, value: str, rows: list[sqlite3.Row]) -> str:
    if scope_type in {"person", "topic"} and rows:
        return str(rows[0]["scope_name"])
    labels = {"place": "地点", "organization": "机构"}
    return f"{value}{labels.get(scope_type, '')}线索"


def build_markdown(scope_type: str, value: str, rows: list[sqlite3.Row]) -> str:
    title = scope_title(scope_type, value, rows)
    lines = [
        f"# {title}事件研究卡片",
        "",
        f"- 事件节点：{len(rows)}",
        f"- 覆盖片段：{len({row['page_id'] for row in rows})}",
        f"- 覆盖文档：{len({row['doc_key'] for row in rows})}",
        "",
    ]
    current_year = ""
    for row in rows:
        year = str(row["event_year"] or "未注明")
        if year != current_year:
            current_year = year
            lines.extend([f"## {year}", ""])
        source_url = row["page_url"] or row["doc_url"] or ""
        page = source_page_label(row)
        lines.extend(
            [
                f"### {row['event_date'] or row['date_guess'] or year}｜{row['event_title']}",
                "",
                f"- 摘要：{compact(row['event_summary'], 520)}",
                f"- 人物：{row['actors'] or '未标注'}",
                f"- 标签：{row['tags'] or '未标注'}",
                f"- 地点：{row['places'] or '未标注'}",
                f"- 机构：{row['organizations'] or '未标注'}",
                f"- 短引文：{short_citation(row)}",
                f"- 参考文献：{bibliography_entry(row)}",
                f"- 题名：{translate_title(row['title'])}",
                f"- 英文题名：{row['title']}",
                f"- 卷册：{row['volume_id']} / {row['volume_title'] or ''}",
                f"- 引用位置：{page}",
                f"- FRUS 来源：{source_url}",
                f"- 本库入口：http://127.0.0.1:8765/cite/{row['page_id']}",
                "",
                "原文摘录：",
                "",
                f"> {compact(row['original_text'], 700)}",
                "",
                "中文译文摘录：",
                "",
                f"> {compact(row['zh_text'], 700)}",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="导出事件研究卡片 Markdown 文件。")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--person", help="人物 slug，例如 lo-lung-chi")
    group.add_argument("--topic", help="专题 slug，例如 kunming-assassinations")
    group.add_argument("--place", help="地点名，例如 南京")
    group.add_argument("--organization", help="机构名，例如 中国民主同盟")
    parser.add_argument("--out-dir", default=str(ROOT / "exports"), help="输出目录")
    parser.add_argument("--split-by-tag", action="store_true", help="按事件标签分册导出")
    parser.add_argument("--split-by-place", action="store_true", help="按地点分册导出")
    parser.add_argument("--split-by-organization", action="store_true", help="按机构分册导出")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scope_type = "person"
    value = args.person
    if args.topic:
        scope_type, value = "topic", args.topic
    elif args.place:
        scope_type, value = "place", args.place
    elif args.organization:
        scope_type, value = "organization", args.organization

    rows = fetch_rows(scope_type, value)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    base_name = f"event_cards_{scope_type}_{slugify(value)}"
    out_path = out_dir / f"{base_name}.md"
    out_path.write_text(build_markdown(scope_type, value, rows), encoding="utf-8")
    print(f"Wrote {out_path} ({len(rows)} events)")

    split_specs = []
    if args.split_by_tag:
        split_specs.append(("tag", "tags"))
    if args.split_by_place:
        split_specs.append(("place", "places"))
    if args.split_by_organization:
        split_specs.append(("organization", "organizations"))

    for suffix, column in split_specs:
        grouped: dict[str, list[sqlite3.Row]] = {}
        for row in rows:
            values = split_terms(row[column]) or ["未标注"]
            for value_item in values:
                grouped.setdefault(value_item, []).append(row)

        for group_value, group_rows in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
            group_path = out_dir / f"{base_name}_{suffix}_{slugify(group_value)}.md"
            group_path.write_text(build_markdown(scope_type, f"{value}｜{group_value}", group_rows), encoding="utf-8")
            print(f"Wrote {group_path} ({len(group_rows)} events)")


if __name__ == "__main__":
    main()
