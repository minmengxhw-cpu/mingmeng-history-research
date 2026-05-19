#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import sqlite3
import time
import urllib.request
import zipfile
from dataclasses import dataclass
from html import unescape
from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup


BASE_URL = "https://history.state.gov"
STATIC_URL = "https://static.history.state.gov/frus"

VOLUMES = [
    ("frus1941v04", "Foreign Relations of the United States, Diplomatic Papers, 1941, The Far East, Volume IV"),
    ("frus1941v05", "Foreign Relations of the United States, Diplomatic Papers, 1941, The Far East, Volume V"),
    ("frus1942China", "Foreign Relations of the United States, Diplomatic Papers, 1942, China"),
    ("frus1943China", "Foreign Relations of the United States, Diplomatic Papers, 1943, China"),
    ("frus1944v06", "Foreign Relations of the United States, Diplomatic Papers, 1944, China, Volume VI"),
    ("frus1945v07", "Foreign Relations of the United States, Diplomatic Papers, 1945, The Far East, China, Volume VII"),
    ("frus1946v09", "Foreign Relations of the United States, 1946, The Far East: China, Volume IX"),
    ("frus1946v10", "Foreign Relations of the United States, 1946, The Far East: China, Volume X"),
    ("frus1947v07", "Foreign Relations of the United States, 1947, The Far East: China, Volume VII"),
    ("frus1948v07", "Foreign Relations of the United States, 1948, The Far East: China, Volume VII"),
    ("frus1948v08", "Foreign Relations of the United States, 1948, The Far East: China, Volume VIII"),
    ("frus1949v08", "Foreign Relations of the United States, 1949, The Far East: China, Volume VIII"),
    ("frus1949v09", "Foreign Relations of the United States, 1949, The Far East: China, Volume IX"),
    ("frus1950v06", "Foreign Relations of the United States, 1950, East Asia and the Pacific, Volume VI"),
]

DIRECT_TERMS = [
    "China Democratic League",
    "Chinese Democratic League",
    "Democratic League",
    "Democratic Political League",
    "Federation of Chinese Democratic Parties",
]

# These are useful second-pass handles. They are kept separate from organization
# hits because a person can appear in FRUS outside a Democratic League context.
PERSON_TERMS = [
    "Lo Lung-chi",
    "Lo Lung Chi",
    "Lo Lungchi",
    "Luo Lung-chi",
    "Chang Lan",
    "Chang Po-chun",
    "Chang Po-chün",
    "Chang Po Chun",
    "Shen Chun-ju",
    "Shen Chun Ju",
    "Liang Shu-ming",
    "Liang Shuming",
    "Huang Yen-pei",
    "Huang Yen Pei",
    "Fei Hsiao-tung",
    "Fei Hsiao Tung",
    "Ch'u T'u-nan",
    "Chu T'u-nan",
    "Ch’u T’u-nan",
    "Ch’u Tu-nan",
    "Shih Liang",
    "Shih Liang",
]

TERM_RE = re.compile(
    "|".join(re.escape(term) for term in sorted(DIRECT_TERMS + PERSON_TERMS, key=len, reverse=True)),
    re.IGNORECASE,
)
DIRECT_RE = re.compile("|".join(re.escape(term) for term in sorted(DIRECT_TERMS, key=len, reverse=True)), re.IGNORECASE)
PERSON_RE = re.compile("|".join(re.escape(term) for term in sorted(PERSON_TERMS, key=len, reverse=True)), re.IGNORECASE)


@dataclass
class Hit:
    volume_id: str
    volume_title: str
    doc_id: str
    doc_number: str
    title: str
    opener: str
    date_guess: str
    url: str
    local_html: str
    local_txt: str
    hit_type: str
    matched_terms: list[str]
    excerpt: str


def fetch(url: str, dest: Path) -> None:
    if dest.exists() and dest.stat().st_size > 0:
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "personal-research-frus-crawler/0.1"})
    last_error: Exception | None = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                data = response.read()
            dest.write_bytes(data)
            time.sleep(0.2)
            return
        except Exception as exc:
            last_error = exc
            if dest.exists():
                dest.unlink()
            print(f"  retry {attempt}/3 after download error: {exc}", flush=True)
            time.sleep(2 * attempt)
    raise RuntimeError(f"failed to download {url}") from last_error


def text_from_soup(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = unescape(text)
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def matched_terms(text: str, regex: re.Pattern[str]) -> list[str]:
    seen: dict[str, str] = {}
    for match in regex.finditer(text):
        key = match.group(0).lower()
        seen.setdefault(key, match.group(0))
    return sorted(seen.values(), key=str.lower)


def excerpts(text: str, window: int = 280) -> list[str]:
    out = []
    for match in TERM_RE.finditer(text):
        start = max(0, match.start() - window)
        end = min(len(text), match.end() + window)
        out.append(compact(text[start:end]))
        if len(out) >= 5:
            break
    return out


def parse_date_guess(opener: str, text: str) -> str:
    sample = " ".join([opener, text[:700]])
    patterns = [
        r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}",
        r"\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}",
        r"\d{4}",
    ]
    for pattern in patterns:
        match = re.search(pattern, sample)
        if match:
            return match.group(0)
    return ""


def iter_docs(epub_path: Path) -> Iterable[tuple[str, str]]:
    with zipfile.ZipFile(epub_path) as archive:
        for name in archive.namelist():
            if re.search(r"/d\d+\.html$", name):
                yield name, archive.read(name).decode("utf-8", errors="replace")


def build_hit(volume_id: str, volume_title: str, name: str, html: str, out_dir: Path) -> Hit | None:
    soup = BeautifulSoup(html, "html.parser")
    text = text_from_soup(soup)
    if not TERM_RE.search(text):
        return None

    direct = matched_terms(text, DIRECT_RE)
    person = matched_terms(text, PERSON_RE)
    hit_type = "direct_org" if direct else "person_candidate"

    doc_id = Path(name).stem
    title = compact(soup.title.get_text(" ")) if soup.title else ""
    doc_number = ""
    doc_marker = soup.find(string=re.compile(r"\[Document\s+\d+\]"))
    if doc_marker:
        m = re.search(r"\d+", str(doc_marker))
        doc_number = m.group(0) if m else ""
    opener_node = soup.find(class_="opener")
    opener = compact(opener_node.get_text(" ")) if opener_node else ""
    url = f"{BASE_URL}/historicaldocuments/{volume_id}/{doc_id}"

    local_base = out_dir / "documents" / volume_id / doc_id
    local_base.parent.mkdir(parents=True, exist_ok=True)
    html_path = local_base.with_suffix(".html")
    txt_path = local_base.with_suffix(".txt")
    html_path.write_text(html, encoding="utf-8")
    txt_path.write_text(text, encoding="utf-8")

    return Hit(
        volume_id=volume_id,
        volume_title=volume_title,
        doc_id=doc_id,
        doc_number=doc_number,
        title=title,
        opener=opener,
        date_guess=parse_date_guess(opener, text),
        url=url,
        local_html=str(html_path),
        local_txt=str(txt_path),
        hit_type=hit_type,
        matched_terms=direct + [term for term in person if term not in direct],
        excerpt="\n---\n".join(excerpts(text)),
    )


def write_outputs(hits: list[Hit], volume_counts: dict[str, dict[str, int]], out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = [
        "volume_id",
        "volume_title",
        "doc_id",
        "doc_number",
        "title",
        "opener",
        "date_guess",
        "url",
        "local_html",
        "local_txt",
        "hit_type",
        "matched_terms",
        "excerpt",
    ]
    with (out_dir / "frus_meng_hits.csv").open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for hit in hits:
            row = hit.__dict__.copy()
            row["matched_terms"] = "; ".join(hit.matched_terms)
            writer.writerow(row)

    for hit_type, filename in [
        ("direct_org", "frus_meng_direct_hits.csv"),
        ("person_candidate", "frus_meng_person_candidates.csv"),
    ]:
        with (out_dir / filename).open("w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            for hit in [h for h in hits if h.hit_type == hit_type]:
                row = hit.__dict__.copy()
                row["matched_terms"] = "; ".join(hit.matched_terms)
                row["excerpt"] = compact(hit.excerpt)
                writer.writerow(row)

    with (out_dir / "frus_meng_hits.jsonl").open("w", encoding="utf-8") as f:
        for hit in hits:
            f.write(json.dumps(hit.__dict__, ensure_ascii=False) + "\n")

    db_path = out_dir / "frus_meng.sqlite"
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE hits (
            id INTEGER PRIMARY KEY,
            volume_id TEXT,
            volume_title TEXT,
            doc_id TEXT,
            doc_number TEXT,
            title TEXT,
            opener TEXT,
            date_guess TEXT,
            url TEXT,
            local_html TEXT,
            local_txt TEXT,
            hit_type TEXT,
            matched_terms TEXT,
            excerpt TEXT,
            full_text TEXT
        )
        """
    )
    conn.execute("CREATE VIRTUAL TABLE hit_fts USING fts5(title, opener, matched_terms, excerpt, full_text, content='hits', content_rowid='id')")
    for hit in hits:
        full_text = Path(hit.local_txt).read_text(encoding="utf-8")
        cur = conn.execute(
            """
            INSERT INTO hits (
                volume_id, volume_title, doc_id, doc_number, title, opener,
                date_guess, url, local_html, local_txt, hit_type, matched_terms,
                excerpt, full_text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                hit.volume_id,
                hit.volume_title,
                hit.doc_id,
                hit.doc_number,
                hit.title,
                hit.opener,
                hit.date_guess,
                hit.url,
                hit.local_html,
                hit.local_txt,
                hit.hit_type,
                "; ".join(hit.matched_terms),
                hit.excerpt,
                full_text,
            ),
        )
        conn.execute(
            "INSERT INTO hit_fts(rowid, title, opener, matched_terms, excerpt, full_text) VALUES (?, ?, ?, ?, ?, ?)",
            (cur.lastrowid, hit.title, hit.opener, "; ".join(hit.matched_terms), hit.excerpt, full_text),
        )
    conn.commit()
    conn.close()

    lines = [
        "# FRUS 民盟资料抓取结果",
        "",
        "来源：Office of the Historian 官方 FRUS EPUB 与对应网页。",
        "",
        "## 覆盖卷册",
        "",
        "| 卷册 | 文档数 | 直接组织命中 | 人物候选命中 |",
        "|---|---:|---:|---:|",
    ]
    for volume_id, title in VOLUMES:
        counts = volume_counts.get(volume_id, {"docs": 0, "direct_org": 0, "person_candidate": 0})
        lines.append(
            f"| {volume_id} - {title} | {counts['docs']} | {counts['direct_org']} | {counts['person_candidate']} |"
        )
    lines.extend(["", "## 直接组织命中", ""])
    for hit in [h for h in hits if h.hit_type == "direct_org"]:
        lines.append(f"### {hit.volume_id}/{hit.doc_id} - {hit.date_guess or hit.title}")
        lines.append(f"- 标题：{hit.title}")
        lines.append(f"- 链接：{hit.url}")
        lines.append(f"- 命中词：{', '.join(hit.matched_terms)}")
        lines.append(f"- 本地文本：`{hit.local_txt}`")
        lines.append("")
        lines.append(hit.excerpt[:1200])
        lines.append("")
    lines.extend(["## 人物候选命中", ""])
    for hit in [h for h in hits if h.hit_type == "person_candidate"]:
        lines.append(f"- {hit.volume_id}/{hit.doc_id} | {hit.date_guess or hit.title} | {', '.join(hit.matched_terms)} | {hit.url}")
    (out_dir / "frus_meng_report.md").write_text("\n".join(lines).strip() + "\n", encoding="utf-8")


def main() -> None:
    root = Path.cwd()
    out_dir = root / "data" / "frus_meng"
    epub_dir = out_dir / "epubs"
    hits: list[Hit] = []
    volume_counts: dict[str, dict[str, int]] = {}

    for volume_id, volume_title in VOLUMES:
        epub_url = f"{STATIC_URL}/{volume_id}/ebook/{volume_id}.epub"
        epub_path = epub_dir / f"{volume_id}.epub"
        print(f"Fetching {volume_id}", flush=True)
        fetch(epub_url, epub_path)
        counts = {"docs": 0, "direct_org": 0, "person_candidate": 0}
        for name, html in iter_docs(epub_path):
            counts["docs"] += 1
            hit = build_hit(volume_id, volume_title, name, html, out_dir)
            if hit:
                hits.append(hit)
                counts[hit.hit_type] += 1
        volume_counts[volume_id] = counts

    hits.sort(key=lambda h: (h.volume_id, int(h.doc_number or 0), h.doc_id))
    write_outputs(hits, volume_counts, out_dir)
    print(f"Wrote {len(hits)} hits to {out_dir}")


if __name__ == "__main__":
    main()
