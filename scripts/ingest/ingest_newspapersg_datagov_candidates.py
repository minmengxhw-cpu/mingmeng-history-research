#!/usr/bin/env python3
"""将 data.gov.sg 筛出的 NewspaperSG 英文报刊民盟候选 OCR 入库。"""

from __future__ import annotations

import csv
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from ingest_newspapersg_meng import (
    DB,
    MANIFEST,
    ROOT,
    Article,
    article_doc_id,
    enrich_with_article_ocr,
    insert_db,
    save_articles,
)


CANDIDATES = ROOT / "data" / "newspapersg" / "datagov_candidates.csv"

EXCLUDE = [
    "malayan democratic union",
    "malayan democratic league",
    "korean democratic league",
    "taiwan democratic league",
]


def normalize_date(value: str) -> str:
    for fmt in ("%d %B %Y", "%d-%b-%y"):
        try:
            dt = datetime.strptime(value, fmt)
            if dt.year > 2000:
                dt = dt.replace(year=dt.year - 100)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass
    return value


def keep_candidate(row: dict[str, str]) -> bool:
    blob = " ".join([
        row.get("matched_terms", ""),
        row.get("article_title", ""),
        row.get("article_text_1st50words", ""),
    ]).lower()
    if any(term in blob for term in EXCLUDE):
        return False
    if "china democratic league" in blob or "chinese democratic league" in blob:
        return True
    if any(term in blob for term in ["lo lung-chi", "li kung-pu", "wen i-to", "chang lan", "hu yu-chih"]):
        return True
    if "democratic league" in blob and any(term in blob for term in [
        "china", "chinese", "nanking", "shanghai", "s'hai", "chungking",
        "kuomintang", "communist", "c. d. l.", "c.d.l.", "anti-chiang", "chiang",
    ]):
        return True
    return False


def existing_doc_keys() -> set[str]:
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT doc_key FROM documents WHERE source_platform='newspapersg'").fetchall()
    conn.close()
    return {r[0] for r in rows}


def load_candidates(limit: int | None = None) -> list[Article]:
    existing = existing_doc_keys()
    articles: list[Article] = []
    with CANDIDATES.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            if not keep_candidate(row):
                continue
            article_id = row["article_id"].strip()
            issue_id = row["issue_id"].strip()
            pseudo = Article(
                issue_id=issue_id,
                date=normalize_date(row["issue_date"].strip()),
                newspaper=row["newspaper_title"].strip() or "NewspaperSG",
                page_label=row["page_number"].strip() or "1",
                title=re.sub(r"\s+", " ", row["article_title"].strip())[:120],
                text="",
                url=row["url"].strip(),
                matched_terms=row["matched_terms"].strip(),
            )
            if f"newspapersg:{article_doc_id(pseudo)}" in existing:
                continue
            if article_id not in pseudo.url:
                continue
            articles.append(pseudo)
            if limit and len(articles) >= limit:
                break
    return articles


def append_manifest(articles: list[Article]) -> None:
    if not articles:
        return
    fields = ["issue_id", "date", "newspaper", "page_label", "title", "url", "matched_terms", "images", "chars"]
    exists = MANIFEST.exists()
    with MANIFEST.open("a", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if not exists:
            writer.writeheader()
        for a in articles:
            writer.writerow({
                "issue_id": a.issue_id,
                "date": a.date,
                "newspaper": a.newspaper,
                "page_label": a.page_label,
                "title": a.title,
                "url": a.url,
                "matched_terms": a.matched_terms,
                "images": len(a.image_urls or []),
                "chars": len(a.text),
            })


def main() -> int:
    limit_env = os.environ.get("NEWSPAPERSG_LIMIT", "40").strip()
    limit = int(limit_env) if limit_env else None
    candidates = load_candidates(limit=limit)
    print(f"data.gov candidates selected: {len(candidates)}")
    enriched = enrich_with_article_ocr(candidates)
    save_articles(enriched)
    append_manifest(enriched)
    inserted = insert_db(enriched)
    print(f"NewspaperSG data.gov OCR articles: {len(enriched)}")
    print(f"NewspaperSG data.gov inserted: {inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
