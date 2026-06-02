#!/usr/bin/env python3
"""从 data.gov.sg 的 NewspaperSG 开放表筛民盟候选文章。

data.gov.sg 的子数据集主要是英文报刊文章索引；南洋商报不在该开放表中，
但 Malaya Tribune / Morning Tribune / Sunday Tribune 等英文报刊可能有
China Democratic League 或 Democratic League 相关报道。脚本只做候选清单，
真正入库仍由 NewspaperSG 原始文章页和图像 OCR 完成。
"""

from __future__ import annotations

import csv
import json
import subprocess
import urllib.parse
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
OUT = ROOT / "data" / "newspapersg" / "datagov_candidates.csv"
API = "https://api-production.data.gov.sg/v2/public/api"

DATASETS = {
    "d_35edcd8fbe08f517e1c23470f996dadc": "Malaya Tribune 1945-1949",
    "d_b1233478b7e05f5fb6211edc9ab449e7": "Morning Tribune 1946-1949",
    "d_ffa948e85a23f815cf4355e47b387232": "Sunday Tribune 1945-1950",
    "d_434d294555cbb371da63e9770d5b4ca1": "Indian Daily Mail 1946-1947",
    "d_8da33537d8112093ea230332db01896b": "Indian Daily Mail 1949-1953",
}

TERMS = [
    "China Democratic League",
    "Chinese Democratic League",
    "Democratic League",
    "Chang Lan",
    "Lo Lung-chi",
    "Lo Lung Chi",
    "Chang Chun-mai",
    "Chang Chun Mai",
    "Li Kung-pu",
    "Wen I-to",
    "Hu Yu-chih",
]

EXCLUDE = [
    "Malayan Democratic Union",
    "Malayan Democratic League",
    "Korean Democratic League",
    "Taiwan Democratic League",
]


def curl_json(url: str) -> dict:
    raw = subprocess.check_output(["curl", "-sS", "--max-time", "25", url])
    return json.loads(raw)


def list_rows_url(dataset_id: str, offset: int, limit: int = 5000) -> str:
    return f"{API}/datasets/{dataset_id}/list-rows?offset={offset}&limit={limit}"


def matched_terms(text: str) -> list[str]:
    low = text.lower()
    if any(term.lower() in low for term in EXCLUDE):
        return []
    return [term for term in TERMS if term.lower() in low]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rows_out: list[dict[str, str]] = []
    seen: set[str] = set()
    for dataset_id, dataset_name in DATASETS.items():
        offset = 0
        limit = 5000
        scanned = 0
        hits = 0
        while True:
            try:
                payload = curl_json(list_rows_url(dataset_id, offset, limit))
            except Exception as exc:
                print(f"{dataset_name}: offset={offset} failed: {exc}")
                offset += limit
                continue
            data = payload.get("data", {})
            rows = data.get("rows", [])
            if not rows:
                break
            for row in rows:
                scanned += 1
                title = row.get("article_title", "")
                first = row.get("article_text_1st50words", "")
                terms = matched_terms(f"{title} {first}")
                if not terms:
                    continue
                article_id = row.get("article_id", "")
                if article_id in seen:
                    continue
                seen.add(article_id)
                hits += 1
                issue_id = row.get("issue_id", "")
                rows_out.append({
                    "dataset": dataset_name,
                    "newspaper_title": row.get("newspaper_title", ""),
                    "issue_id": issue_id,
                    "issue_date": row.get("issue_date", ""),
                    "page_number": row.get("page_number", ""),
                    "article_id": article_id,
                    "article_title": title,
                    "article_text_1st50words": first,
                    "matched_terms": "; ".join(terms),
                    "url": f"https://eresources.nlb.gov.sg/newspapers/digitised/article/{urllib.parse.quote(article_id)}",
                })
            offset += len(rows)
            if scanned and scanned % 50000 == 0:
                print(f"{dataset_name}: scanned={scanned} hits={hits}")
            if len(rows) < limit:
                break
        print(f"{dataset_name}: scanned={scanned} hits={hits}")

    rows_out.sort(key=lambda r: (r["issue_date"], r["newspaper_title"], r["article_id"]))
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "dataset",
            "newspaper_title",
            "issue_id",
            "issue_date",
            "page_number",
            "article_id",
            "article_title",
            "article_text_1st50words",
            "matched_terms",
            "url",
        ])
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"candidates={len(rows_out)}")
    print(f"out={OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
