#!/usr/bin/env python3
"""Extract auditable plain text from the 2026-07-27 public web intake.

Raw HTML stays immutable under data/domestic/raw/.  Extracted text and a
provenance manifest are written under work/domestic/ for review and indexing.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data/domestic/raw/public_sources"
OUT_DIR = ROOT / "work/domestic/public_web_extracted_20260728"
MANIFEST = ROOT / "work/domestic/PUBLIC_WEB_EXTRACT_MANIFEST_20260728.jsonl"

SOURCES = [
    {
        "download_id": "DL-20260727-001",
        "file": "DL-20260727-001_zh_wikipedia_cdl.html",
        "title": "中国民主同盟（维基百科导航条目）",
        "date": "",
        "evidence_level": "L4",
        "source_kind": "secondary_navigation",
        "selector": "#mw-content-text",
        "formal_import": False,
    },
    {
        "download_id": "DL-20260727-002",
        "file": "DL-20260727-002_en_wikipedia_cdl.html",
        "title": "China Democratic League（Wikipedia导航条目）",
        "date": "",
        "evidence_level": "L4",
        "source_kind": "secondary_navigation",
        "selector": "#mw-content-text",
        "formal_import": False,
    },
    {
        "download_id": "DL-20260727-003",
        "file": "DL-20260727-003_wikisource_commonprogram.html",
        "title": "中国人民政治协商会议共同纲领（维基文库公开转录）",
        "date": "1949-09-29",
        "evidence_level": "L2",
        "source_kind": "public_domain_transcription",
        "selector": "#mw-content-text",
        "formal_import": True,
    },
    {
        "download_id": "DL-20260727-004",
        "file": "DL-20260727-004_mmzy_jianjie.html",
        "title": "中国民主同盟简介（民盟中央官方史叙）",
        "date": "",
        "evidence_level": "L4",
        "source_kind": "official_history",
        "selector": ".news-demo-details",
        "formal_import": True,
    },
    {
        "download_id": "DL-20260727-005",
        "file": "DL-20260727-005_icppcc_1948_01_05.html",
        "title": "1948年1月5日，民盟恢复组织活动（人民政协网钩沉）",
        "date": "1948-01-05",
        "evidence_level": "L4",
        "source_kind": "official_retrospective",
        "selector": ".main-left2",
        "formal_import": True,
    },
    {
        "download_id": "DL-20260727-006",
        "file": "DL-20260727-006_cpc_people_1946.html",
        "title": "中国共产党大事记·1946年",
        "date": "1946",
        "evidence_level": "L4",
        "source_kind": "official_chronology",
        "selector": "#zoom",
        "formal_import": True,
        "encoding": "gb18030",
    },
    {
        "download_id": "DL-20260727-007",
        "file": "DL-20260727-007_zytzb_2024_11_08.html",
        "title": "沈钧儒保存的政协筹建会议提纲和记录（中央统战部）",
        "date": "1948",
        "evidence_level": "L4",
        "source_kind": "official_retrospective",
        "selector": ".detailMain",
        "formal_import": True,
    },
    {
        "download_id": "DL-20260727-008",
        "file": "DL-20260727-008_en_wikipedia_cdl_raw.txt",
        "title": "China Democratic League（Wikipedia原始wikitext）",
        "date": "",
        "evidence_level": "L4",
        "source_kind": "secondary_navigation",
        "selector": None,
        "formal_import": False,
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def clean_text(text: str) -> str:
    lines: list[str] = []
    previous = ""
    for raw_line in text.replace("\r", "\n").splitlines():
        line = re.sub(r"[ \t\u00a0]+", " ", raw_line).strip()
        if not line or line == previous:
            continue
        lines.append(line)
        previous = line
    return "\n".join(lines).strip() + "\n"


def extract(source: dict[str, object], path: Path) -> tuple[str, str]:
    encoding = str(source.get("encoding") or "utf-8")
    raw = path.read_bytes()
    try:
        decoded = raw.decode(encoding)
    except UnicodeDecodeError:
        decoded = raw.decode("gb18030", errors="replace")

    if path.suffix.lower() == ".txt":
        return clean_text(decoded), "plain_text"

    soup = BeautifulSoup(decoded, "lxml")
    for tag in soup(["script", "style", "noscript", "nav", "footer"]):
        tag.decompose()
    selector = str(source.get("selector") or "")
    node = soup.select_one(selector) if selector else None
    if node is None:
        candidates = soup.find_all(["article", "main", "div"])
        node = max(candidates, key=lambda item: len(item.get_text(" ", strip=True)))
        selector = "largest_text_container_fallback"
    return clean_text(node.get_text("\n", strip=True)), selector


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    for source in SOURCES:
        raw_path = RAW_DIR / str(source["file"])
        if not raw_path.is_file():
            raise SystemExit(f"missing raw source: {raw_path}")
        text, selector_used = extract(source, raw_path)
        if len(text) < 200:
            raise SystemExit(f"extracted text too short: {raw_path} ({len(text)})")
        out_path = OUT_DIR / f"{source['download_id']}.txt"
        out_path.write_text(text, encoding="utf-8")
        rows.append(
            {
                **source,
                "raw_path": str(raw_path.relative_to(ROOT)),
                "raw_sha256": sha256(raw_path),
                "extracted_text_path": str(out_path.relative_to(ROOT)),
                "extracted_text_sha256": sha256(out_path),
                "extracted_chars": len(text),
                "selector_used": selector_used,
                "citation_ready": False,
                "needs_human_review": True,
            }
        )
    MANIFEST.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "records": len(rows),
                "formal_import": sum(bool(row["formal_import"]) for row in rows),
                "navigation_only": sum(not bool(row["formal_import"]) for row in rows),
                "manifest": str(MANIFEST),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
