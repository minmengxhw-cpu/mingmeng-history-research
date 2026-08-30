#!/usr/bin/env python3
"""NewspaperSG 民盟相关中文报刊 OCR 入库。

该来源是新加坡国家图书馆 NewspaperSG，不属于现有 FRUS/CIA/Wilson/
Hoover/HathiTrust/DRNH 六个平台。页面公开提供期号、页码、文章题名和文章图像；
本脚本只下载含民盟关键词的文章图像，并用本地 Tesseract OCR 后入库。
"""

from __future__ import annotations

import csv
import html
import http.cookiejar
import re
import sqlite3
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
DATA_DIR = ROOT / "data" / "newspapersg"
DOC_DIR = DATA_DIR / "documents"
IMG_DIR = DATA_DIR / "images"
MANIFEST = DATA_DIR / "manifest.csv"

KEYWORDS = [
    "民盟",
    "民主同盟",
    "中國民主同盟",
    "中国民主同盟",
    "胡愈之",
    "張君勱",
    "张君劢",
    "李公樸",
    "聞一多",
]

EXCLUDE_TITLE_TERMS = [
    "馬民主同盟",
    "马民主同盟",
    "馬來亞民主同盟",
    "马来亚民主同盟",
]


def issue_url(issue_id: str) -> str:
    return f"https://eresources.nlb.gov.sg/newspapers/Digitised/Issue/{issue_id}"


SEED_ISSUES = [
    issue_url("nysp19460327-1"),
    issue_url("nysp19460501-1"),
    issue_url("nysp19460514-1"),
    issue_url("nysp19460601-1"),
    issue_url("nysp19460604-1"),
    issue_url("nysp19460705-1"),
    issue_url("nysp19460706-1"),
    issue_url("nysp19460709-1"),
    issue_url("nysp19460719-1"),
    issue_url("nysp19460722-1"),
    issue_url("nysp19460727-1"),
    issue_url("nysp19460808-1"),
    issue_url("nysp19460831-1"),
    issue_url("nysp19460907-1"),
    issue_url("nysp19460924-1"),
    issue_url("nysp19461001-1"),
    issue_url("nysp19470716-1"),
    issue_url("nysp19470916-1"),
    issue_url("nysp19471105-1"),
    issue_url("nysp19471107-1"),
    issue_url("nysp19471110-1"),
    issue_url("nysp19490316-1"),
    issue_url("nysp19490513-1"),
    issue_url("nysp19490518-1"),
]


@dataclass
class Article:
    issue_id: str
    date: str
    newspaper: str
    page_label: str
    title: str
    text: str
    url: str
    matched_terms: str
    image_urls: list[str] | None = None


def opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def fetch(url: str, client: urllib.request.OpenerDirector | None = None) -> str:
    if client is None:
        return curl_text(url)
    req = urllib.request.Request(url, headers={"User-Agent": "mingmeng-research/1.0"})
    with client.open(req, timeout=20) as resp:
        return resp.read().decode("utf-8", errors="replace")


def curl_text(url: str, data: dict[str, str] | None = None, referer: str | None = None) -> str:
    cmd = [
        "curl",
        "-L",
        "-sS",
        "--compressed",
        "-H",
        "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "-H",
        "Accept-Language: zh-CN,zh;q=0.9,en;q=0.8",
    ]
    if referer:
        cmd.extend(["-H", f"Referer: {referer}"])
    cookie_path = None
    if data:
        cookie_path = str(Path(tempfile.gettempdir()) / "newspapersg-cookies.txt")
        cmd.extend(["-c", cookie_path, "-b", cookie_path])
    if data:
        for key, value in data.items():
            cmd.extend(["--data-urlencode", f"{key}={value}"])
    cmd.append(url)
    result = subprocess.run(cmd, check=True, capture_output=True)
    return result.stdout.decode("utf-8", errors="replace")


def clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def issue_id_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def article_ref(article: Article) -> str:
    return article.url.rstrip("/").rsplit("/", 1)[-1]


def article_doc_id(article: Article) -> str:
    return f"{article.issue_id}-{article_ref(article)}"


def parse_issue(raw_html: str, issue_url: str) -> list[Article]:
    issue_id = issue_id_from_url(issue_url)
    text = clean_text(raw_html)
    date = ""
    date_match = re.search(r"(\d{4})/(\d{2})/(\d{2})|(\d{4}-\d{2}-\d{2})", text)
    if date_match:
        if date_match.group(4):
            date = date_match.group(4)
        else:
            date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
    newspaper = "南洋商报" if "南洋商报" in text or "南洋商報" in text or "Nan Yang Shang Bao" in text else "NewspaperSG"

    articles: list[Article] = []
    article_re = re.compile(
        r'<a\b[^>]*href="(?P<href>/newspapers/digitised/article/[^"]+)"[^>]*title="(?P<title>[^"]+)"',
        re.S,
    )
    for match in article_re.finditer(raw_html):
        title = html.unescape(match.group("title")).strip()
        if not any(term in title for term in KEYWORDS):
            continue
        if any(term in title for term in EXCLUDE_TITLE_TERMS):
            continue
        block = raw_html[max(0, match.start() - 5000): match.start() + 1400]
        page_matches = re.findall(r"Page\s+(\d+)", clean_text(block))
        page_label = page_matches[-1] if page_matches else "1"
        matched = [term for term in KEYWORDS if term in title]
        url = "https://eresources.nlb.gov.sg" + html.unescape(match.group("href"))
        articles.append(
            Article(
                issue_id=issue_id,
                date=date,
                newspaper=newspaper,
                page_label=page_label or "1",
                title=title[:120],
                text="",
                url=url,
                matched_terms="; ".join(matched),
            )
        )
    return articles


def accept_terms_and_fetch_article(article_url: str) -> str:
    path = urllib.parse.urlparse(article_url).path
    return curl_text(
        "https://eresources.nlb.gov.sg/newspapers/Digitised/TermsAndConditionsCheck",
        data={"u": path},
        referer=article_url,
    )


def parse_article_page(raw_html: str, article: Article) -> Article:
    title_match = re.search(r"<h1[^>]*>(.*?)</h1>", raw_html, re.S)
    if title_match:
        article.title = clean_text(title_match.group(1))[:120]
    image_urls = []
    for src in re.findall(r'<img[^>]+class="image-content"[^>]+src="([^"]+)"', raw_html):
        image_urls.append(re.sub(r"width=\d+", "width=1600", html.unescape(src)))
    article.image_urls = image_urls
    return article


def download_binary(url: str, path: Path, referer: str) -> None:
    cookie_path = str(Path(tempfile.gettempdir()) / "newspapersg-cookies.txt")
    cmd = [
        "curl",
        "-L",
        "-sS",
        "-c",
        cookie_path,
        "-b",
        cookie_path,
        "-H",
        f"Referer: {referer}",
        url,
        "-o",
        str(path),
    ]
    subprocess.run(cmd, check=True)


def ocr_image(image_path: Path) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        png = Path(tmp) / "image.png"
        subprocess.run(["sips", "-s", "format", "png", str(image_path), "--out", str(png)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        out_base = Path(tmp) / "ocr"
        subprocess.run(["tesseract", str(png), str(out_base), "-l", "chi_tra+eng", "--psm", "6"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return (out_base.with_suffix(".txt")).read_text(encoding="utf-8", errors="replace")


def enrich_with_article_ocr(articles: list[Article]) -> list[Article]:
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    enriched = []
    for a in articles:
        try:
            raw = accept_terms_and_fetch_article(a.url)
            a = parse_article_page(raw, a)
        except Exception as exc:
            print(f"  article fetch failed {a.url}: {exc}", file=sys.stderr)
            continue
        texts = []
        for idx, image_url in enumerate(a.image_urls or [], start=1):
            image_path = IMG_DIR / f"{a.issue_id}-{a.url.rsplit('/', 1)[-1]}-{idx:02d}.webp"
            try:
                download_binary(image_url, image_path, a.url)
                texts.append(ocr_image(image_path))
            except Exception as exc:
                print(f"  OCR failed {image_url}: {exc}", file=sys.stderr)
        a.text = "\n".join(t.strip() for t in texts if t.strip())
        if not a.text:
            a.text = a.title
        enriched.append(a)
        print(f"  {a.title} | images={len(a.image_urls or [])} | ocr={len(a.text)} chars")
    return enriched


def write_manifest(articles: list[Article]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    fields = ["issue_id", "date", "newspaper", "page_label", "title", "url", "matched_terms", "images", "chars"]
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
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


def save_articles(articles: list[Article]) -> None:
    DOC_DIR.mkdir(parents=True, exist_ok=True)
    for idx, a in enumerate(articles, start=1):
        out = DOC_DIR / f"{article_doc_id(a)}.txt"
        out.write_text(a.text, encoding="utf-8")


def insert_db(articles: list[Article]) -> int:
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    src = cur.execute("SELECT id FROM sources WHERE source_type='newspapersg' LIMIT 1").fetchone()
    if src:
        source_id = src["id"]
    else:
        cur.execute(
            """INSERT INTO sources (source_type, source_id, title, origin_url, local_path)
               VALUES (?, ?, ?, ?, ?)""",
            (
                "newspapersg",
                "nlb-newspapersg",
                "NewspaperSG 新加坡中文报刊 OCR",
                "https://eresources.nlb.gov.sg/newspapers/",
                str(DATA_DIR.relative_to(ROOT)),
            ),
        )
        source_id = cur.lastrowid

    inserted = 0
    for a in articles:
        doc_id = article_doc_id(a)
        doc_key = f"newspapersg:{doc_id}"
        txt_path = DOC_DIR / f"{doc_id}.txt"
        if cur.execute("SELECT id FROM documents WHERE doc_key=?", (doc_key,)).fetchone():
            continue
        cur.execute(
            """INSERT INTO documents (source_id, doc_key, volume_id, volume_title, doc_id,
                                      doc_number, title, date_guess, url, local_html, local_txt,
                                      hit_type, matched_terms, source_platform)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                source_id,
                doc_key,
                "newspapersg-1946-1949",
                "NewspaperSG Chinese Press Meng-related OCR",
                doc_id,
                "",
                a.title,
                a.date,
                a.url,
                "",
                str(txt_path.relative_to(ROOT)),
                "core" if ("民盟" in a.matched_terms or "中國民主同盟" in a.matched_terms or "中国民主同盟" in a.matched_terms) else "related",
                a.matched_terms,
                "newspapersg",
            ),
        )
        document_id = cur.lastrowid
        cur.execute(
            "INSERT INTO pages (document_id, page_label, page_url, text) VALUES (?, ?, ?, ?)",
            (document_id, a.page_label, a.url, a.text),
        )
        try:
            cur.execute(
                "INSERT INTO page_fts (volume_id, doc_id, title, page_label, matched_terms, text) VALUES (?, ?, ?, ?, ?, ?)",
                ("newspapersg-1946-1949", doc_id, a.title, a.page_label, a.matched_terms, a.text),
            )
        except sqlite3.OperationalError:
            pass
        cur.execute(
            """INSERT OR REPLACE INTO document_classifications
               (document_id, grade, score, reason, needs_review)
               VALUES (?, ?, ?, ?, ?)""",
            (
                document_id,
                "核心文献",
                82,
                f"NewspaperSG {a.newspaper} {a.date} OCR 直接含民盟关键词：{a.matched_terms}",
                0,
            ),
        )
        inserted += 1
    conn.commit()
    conn.close()
    return inserted


def main() -> int:
    all_articles: list[Article] = []
    for url in SEED_ISSUES:
        try:
            raw = fetch(url)
        except Exception as exc:
            print(f"ERR {url}: {exc}", file=sys.stderr)
            continue
        articles = parse_issue(raw, url)
        print(f"{issue_id_from_url(url)}: {len(articles)} matched articles")
        all_articles.extend(articles)

    # 去重：同一期同页同标题只保留一次。
    unique: dict[tuple[str, str, str], Article] = {}
    for a in all_articles:
        unique[(a.issue_id, a.page_label, a.title)] = a
    articles = enrich_with_article_ocr(list(unique.values()))
    write_manifest(articles)
    save_articles(articles)
    inserted = insert_db(articles)
    print(f"NewspaperSG matched articles: {len(articles)}")
    print(f"NewspaperSG inserted: {inserted}")
    print(f"manifest: {MANIFEST.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
