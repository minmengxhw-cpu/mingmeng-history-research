#!/usr/bin/env python3
"""Register article-level leads that are visually located in Guangming Bao issue 19.

The scan proves the title and page boundary only.  These records deliberately
remain needs_human_review until a transcription and a second page-level read
are completed.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_PATH = ROOT / "data" / "domestic" / "candidates.jsonl"
COVERAGE_PATH = ROOT / "data" / "domestic" / "event_coverage.json"

IDENT = "NLC404-01J000514-10458"
VOLUME = "1947年19期"
DATE = "1947-10-28"
PDF = "data/domestic/press_scans/NLC404-01J000514-10458_光明報_1947年19期.pdf"
URL = "https://commons.wikimedia.org/wiki/File:NLC404-01J000514-10458_光明報_1947年19期.pdf"
SOURCE_ID = "domestic:source:nlc_guangmingbao_1947_1947_19"

ARTICLES = [
    ("01", "《我们对于和平的态度》", "2", "2", "", "目录第1页列出；PDF第2页目视核定题名，PDF第3页已转入另一篇文章。"),
    ("02", "《民盟中央对于五参政员出席参政会之决定》", "6", "6", "", "目录第1页列出；PDF第6页目视核定题名，PDF第7页已转入另一篇文章。"),
    ("03", "《迎接学生运动新的高潮》", "7", "9", "高天", "目录第1页列出；PDF第7页题名起页，第7—9页为连续正文，PDF第10页已转入另一篇文章；PDF第7页可见署名“高天”。"),
    ("04", "《独裁政府是怎样摧残新闻自由的？》", "10", "10", "", "目录第1页列出；PDF第10页目视核定题名，PDF第11页已转入另一篇文章。"),
    ("05", "《两种制度和两种问题》", "11", "12", "", "目录第1页列出；PDF第11页题名起页，第11—12页为连续正文，PDF第13页已转入另一篇文章。"),
]


def main() -> None:
    rows = [
        json.loads(line)
        for line in CANDIDATE_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    by_id = {row["candidate_id"]: row for row in rows}
    added: list[str] = []
    for ordinal, title, page, end_page, creator, note in ARTICLES:
        candidate_id = f"domestic:NLC:guangmingbao-1947-19-article-{ordinal}"
        by_id[candidate_id] = {
            "candidate_id": candidate_id,
            "title": title,
            "creator": creator,
            "document_date": DATE,
            "document_date_precision": "day",
            "document_type": "同期政论报刊文章（整期原刊内文章）",
            "repository_code": "NLC",
            "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
            "collection_name": "民国期刊／光明報／1947年19期",
            "archive_fonds": "",
            "archive_series": "民国期刊／光明報",
            "archive_item": IDENT,
            "catalog_reference": f"{IDENT}；{VOLUME}；目录与正文页{page}—{end_page}",
            "catalog_reference_status": "verified",
            "source_url": URL,
            "source_url_role": "item_digital",
            "access_mode": "open",
            "access_note": f"公开整期PDF；文章定位于PDF第{page}—{end_page}页；本地副本：{PDF}",
            "medium": "hybrid",
            "online_availability": "full_item_online",
            "rights_status": "unknown",
            "reuse_rights": "citation_only",
            "rights_basis": "",
            "copy_allowed": "unknown",
            "authenticity_level_proposed": "L1",
            "relevance_grade_proposed": "core",
            "event_tags": ["1947民盟被宣布非法"],
            "person_tags": ["中国民主同盟", "张澜", "沈钧儒", "罗隆基"],
            "place_tags": ["北平", "上海"],
            "evidence_note": note,
            "evidence_type": "digital_image",
            "evidence_locator": f"{IDENT}；本地PDF第{page}—{end_page}页；work/domestic/guangmingbao_1947_19_pages/page-{page.zfill(2)}.png至page-{end_page.zfill(2)}.png；work/domestic/guangmingbao_1947_19_ocr/page-{page.zfill(2)}.ocr.md至page-{end_page.zfill(2)}.ocr.md；{PDF}",
            "uncertainty_note": "已核对目录题名、正文题名和文章页界；尚未完成逐字转录、署名确认、异体字校对、复制权利确认和独立全文复审。OCR只作导航。",
            "checked_at": "2026-07-19",
            "checked_by": "codex",
            "review_status": "needs_human_review",
            "review_note": "文章级页码定位已完成；保持needs_human_review，不等同于全文转录或政府公文原件闭环。",
        }
        added.append(candidate_id)

    CANDIDATE_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in by_id.values()) + "\n",
        encoding="utf-8",
    )

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    event = next(row for row in coverage if "1947民盟被宣布非法" in row.get("event_tags", []))
    for candidate_id in added:
        if candidate_id not in event["domestic_candidate_ids"]:
            event["domestic_candidate_ids"].append(candidate_id)
    event["domestic_status"] = "已补入1947年8—10月《光明報》连续原刊；新十九号已增加5条文章级页码定位；10月27日公函、11月解散公告和全文转录仍待完成"
    COVERAGE_PATH.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added_articles": added, "candidates": len(by_id)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
