#!/usr/bin/env python3
"""NewspaperSG 史料长编独立生成器（不依赖 sqlite，纯 CSV + txt + weasyprint）。

输入：
- data/newspapersg/manifest.csv（93 行）
- data/newspapersg/documents/<doc_key>.txt（OCR 原文）
- data/newspapersg/zh_translations.csv（DeepSeek 翻译）
- data/newspapersg/relevance_review.csv（grade/score）

输出：
- output/sourcebooks/NewspaperSG_史料长编_v1.pdf

按日期排序，每条目：英文原文（OCR 清洗后） + 中文译文对照，含报刊名、日期、原文链接。
"""
from __future__ import annotations
import csv, html, re, sys
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data" / "newspapersg"
MANIFEST = DATA / "manifest.csv"
DOC_DIR = DATA / "documents"
TRANS_CSV = DATA / "zh_translations.csv"
REVIEW_CSV = DATA / "relevance_review.csv"
OUT_DIR = ROOT / "output" / "sourcebooks"
OUT_DIR.mkdir(parents=True, exist_ok=True)
OUT_PDF = OUT_DIR / "NewspaperSG_史料长编_v1.pdf"

CSS = """
@page {
  size: A4;
  margin: 25mm 22mm 22mm;
  @top-center { content: string(runhead); font-family: "Noto Serif CJK SC";
                font-size: 8.5pt; color: #9a9384; letter-spacing: .04em; }
  @bottom-center { content: counter(page); font-family: "Noto Serif CJK SC";
                   font-size: 9pt; color: #7b725f; }
}
body {
  font-family: "Noto Serif CJK SC", "Songti SC", serif;
  font-size: 11pt; line-height: 1.85; color: #211f18;
}
h1.cover {
  font-size: 30pt; text-align: center; margin: 60mm 0 8mm;
  color: #4d3022; letter-spacing: .1em; font-weight: bold;
  string-set: runhead "NewspaperSG · 中国民主同盟史料长编";
}
.cover-sub {
  text-align: center; font-size: 13pt; color: #5a5547;
  margin-bottom: 6mm; letter-spacing: .05em;
}
.cover-meta {
  text-align: center; font-size: 10.5pt; color: #7b725f;
  margin-top: 70mm; letter-spacing: .03em;
}
.cover-meta p { margin: 0 0 2mm; }
.cover { page-break-after: always; }

h2.year {
  font-size: 18pt; color: #4d3022; margin: 14mm 0 4mm;
  border-bottom: 1.2pt solid #b9a98c; padding-bottom: 3mm;
  page-break-after: avoid;
  string-set: runhead "NewspaperSG · " content(text);
}
.entry {
  margin: 0 0 9mm; page-break-inside: avoid;
}
.entry-head {
  font-size: 11pt; color: #4d3022; font-weight: bold;
  margin: 0 0 1mm; line-height: 1.4;
}
.entry-meta {
  font-size: 9.5pt; color: #7b725f; margin: 0 0 3mm;
  font-style: italic;
}
.entry-meta .link { color: #0f6b5b; }
.grade-core { color: #b8552d; font-weight: bold; }
.grade-related { color: #c08a40; }
.grade-person { color: #6b7c8f; }
.lang-block { margin: 2.5mm 0; }
.lang-label {
  font-size: 8.5pt; color: #9a8a6c; letter-spacing: .08em;
  text-transform: uppercase; margin: 0 0 1mm;
}
.en-text {
  font-family: "EB Garamond", Georgia, serif;
  font-size: 10pt; color: #2c2820; line-height: 1.7;
}
.en-text p { margin: 0 0 1.8mm; text-align: justify; }
.zh-text {
  font-size: 10.6pt; line-height: 1.85; color: #221f18;
}
.zh-text p { margin: 0 0 2mm; text-indent: 2em; text-align: justify; }
.translator-note {
  font-size: 9pt; color: #7b725f; background: #f6f1e6;
  padding: 2mm 3mm; margin-top: 2mm; border-left: 2pt solid #b9a98c;
  font-style: italic;
}
.entry-rule {
  border: 0; border-bottom: .5pt dotted #c9bda2; margin: 0 0 9mm;
}
.toc { page-break-after: always; }
.toc h2 { margin-top: 0; }
.toc ul { list-style: none; padding-left: 0; }
.toc li {
  padding: 1.5mm 0; border-bottom: .3pt dotted #d4cab2;
  font-size: 10pt;
}
.toc .toc-date { color: #7b725f; margin-right: 3mm; }
.toc .toc-news { color: #4d3022; margin-right: 3mm; font-weight: bold; }
.intro {
  page-break-after: always; padding: 8mm 0;
}
.intro h2 { font-size: 16pt; color: #4d3022; margin: 4mm 0 4mm; }
.intro p { text-indent: 2em; text-align: justify; }
"""

INTRO = """\
本史料长编汇集新加坡国家图书馆 NewspaperSG 数字报刊平台所收 1945-1949 年间
关于中国民主同盟的报道共 93 篇，涵盖《南洋商报》、Malaya Tribune、Morning
Tribune、Indian Daily Mail、Sunday Tribune 等中英文报刊。所有条目按发表日期
排序，分年成章，呈现英文/旧字中文原文（OCR 清洗版）与现代汉语译文对照。

本批材料是民盟历史文献研究库继 FRUS、CIA、Wilson Center、Hoover、HathiTrust、
DRNH 之后的第七个数据源，填补了既有六源之外的「南洋华侨与英殖民地公共
舆论」视角。每篇 OCR 来自 NewspaperSG 原始报纸图像，使用本地 Tesseract OCR
生成；中文译文由 DeepSeek-v4-flash 在术语表约束下机器精译，保留人名、机构、
地名、日期、引号内政治口号一字不改，明显 OCR 错字按上下文校正。

读者可循"原始链接"按钮回到 NewspaperSG 平台核对扫描原图。每条左侧标注
研究等级：核心文献（直接报道民盟）、相关文献（与民盟政治脉络相关）、
人物关联（与民盟核心人物相关）。

—— 民盟历史文献研究库项目组
"""


def esc(s: str) -> str:
    return html.escape(s or "")


def clean_ocr(text: str) -> str:
    """轻清洗 OCR 原文：去页眉/页脚噪声行 + 合并断行。"""
    text = (text or "").strip()
    if not text: return ""
    keep = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            keep.append("")
            continue
        # 去 page break / 续页标记
        if re.fullmatch(r"[-—–_=*·.\s]{3,}", s): continue
        if re.search(r"(?i)continued\s+on\s+page", s) and len(s) < 50: continue
        if re.fullmatch(r"\[?\s*(p\.?\s*\d+|page\s*\d+)\s*\]?", s, re.I): continue
        # OCR 极脏行
        if len(s) > 8:
            weird = len(re.findall(r"[^\w\s一-鿿，。；：、！？“”‘’（）()\[\]/.,;:!?'\"&%—–-]", s))
            if weird / len(s) > 0.15: continue
        keep.append(s)
    return "\n".join(keep).strip()


def paragraphs(text: str) -> list[str]:
    """切分为段落（双换行 + 单换行启发式）"""
    text = text or ""
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for b in blocks:
        b = b.strip()
        if not b: continue
        # 同段单换行合并为空格（不破坏中文）
        b = re.sub(r"(?<=[a-zA-Z,;-])\n(?=[a-zA-Z])", " ", b)
        out.append(b)
    return out


def render_paragraphs(text: str, css_class: str = "") -> str:
    parts = paragraphs(text)
    if not parts: return '<p class="none">（无）</p>'
    return "\n".join(f'<p>{esc(p).replace(chr(10), "<br>")}</p>' for p in parts)


def load_manifest() -> list[dict]:
    rows = list(csv.DictReader(MANIFEST.open(encoding="utf-8-sig")))
    for r in rows:
        art = re.search(r"/article/(.+)$", r["url"])
        r["article_id"] = art.group(1) if art else ""
        r["doc_key"] = f"{r['issue_id']}-{r['article_id']}"
    return rows


def load_translations() -> dict[str, dict]:
    if not TRANS_CSV.exists(): return {}
    out = {}
    for r in csv.DictReader(TRANS_CSV.open(encoding="utf-8-sig")):
        out[r["doc_key"]] = r
    return out


def load_reviews() -> dict[str, dict]:
    if not REVIEW_CSV.exists(): return {}
    out = {}
    for r in csv.DictReader(REVIEW_CSV.open(encoding="utf-8-sig")):
        dk = r["doc_key"].replace("newspapersg:", "")
        out[dk] = r
    return out


def grade_html(grade: str) -> str:
    g = (grade or "").strip()
    cls = "grade-core" if g == "核心文献" else "grade-related" if g == "相关文献" else "grade-person" if g == "人物关联" else ""
    return f'<span class="{cls}">{esc(g or "—")}</span>'


def main():
    manifest = load_manifest()
    trans = load_translations()
    reviews = load_reviews()

    # 按日期排序
    manifest.sort(key=lambda x: (x["date"], x["issue_id"]))

    # 按年分组
    from collections import OrderedDict
    by_year = OrderedDict()
    for m in manifest:
        y = m["date"][:4]
        by_year.setdefault(y, []).append(m)

    today = date.today().isoformat()
    parts = [
        f"<style>{CSS}</style>",
        '<div class="cover">',
        '<h1 class="cover">NewspaperSG 史料长编</h1>',
        '<p class="cover-sub">中国民主同盟与南洋报刊（1945-1949）</p>',
        '<div class="cover-meta">',
        '<p>民盟历史文献研究库 · 第 7 卷</p>',
        f'<p>共收录 NewspaperSG 报刊报道 {len(manifest)} 篇</p>',
        '<p>含《南洋商报》、Malaya Tribune、Morning Tribune、Indian Daily Mail、Sunday Tribune</p>',
        f'<p>编纂日期：{today}</p>',
        '</div></div>',
        '<div class="intro"><h2>编辑说明</h2>',
        f"<p>{esc(INTRO).replace(chr(10), '</p><p>')}</p>",
        '</div>',
    ]

    # 目录
    parts.append('<div class="toc"><h2>目录</h2><ul>')
    for m in manifest:
        parts.append(
            f'<li><span class="toc-date">{esc(m["date"])}</span>'
            f'<span class="toc-news">{esc(m["newspaper"])}</span>'
            f'{esc(m["title"][:80])}</li>'
        )
    parts.append('</ul></div>')

    # 正文按年
    for year, items in by_year.items():
        parts.append(f'<h2 class="year">{year} 年</h2>')
        for m in items:
            t = trans.get(m["doc_key"], {})
            rv = reviews.get(m["doc_key"], {})
            ocr_path = DOC_DIR / f"{m['doc_key']}.txt"
            en_text = clean_ocr(ocr_path.read_text(encoding="utf-8", errors="replace")) if ocr_path.exists() else ""
            zh_text = (t.get("zh_text") or "").strip()
            title_zh = (t.get("title_zh") or "").strip()
            note = (t.get("translator_note") or "").strip()
            grade = rv.get("grade", "") or t.get("grade", "")
            score = rv.get("score", "") or t.get("score", "")

            parts.append('<div class="entry">')
            parts.append(f'<div class="entry-head">{esc(m["title"])}'
                         f'{" · " + esc(title_zh) if title_zh else ""}</div>')
            parts.append(
                f'<div class="entry-meta">'
                f'{esc(m["date"])} ｜ {esc(m["newspaper"])} ｜ '
                f'{grade_html(grade)} ｜ 评分 {esc(score)} ｜ '
                f'<a class="link" href="{esc(m["url"])}">NewspaperSG 原文</a>'
                f'</div>'
            )
            parts.append('<div class="lang-block"><div class="lang-label">英文／旧字原文（OCR）</div>')
            parts.append(f'<div class="en-text">{render_paragraphs(en_text)}</div></div>')
            parts.append('<div class="lang-block"><div class="lang-label">中文译文</div>')
            parts.append(f'<div class="zh-text">{render_paragraphs(zh_text)}</div></div>')
            if note:
                parts.append(f'<div class="translator-note">译者注：{esc(note)}</div>')
            parts.append('</div><hr class="entry-rule">')

    html_str = "<html><head><meta charset='utf-8'></head><body>" + "\n".join(parts) + "</body></html>"

    # 写中间 HTML（便于调试）
    debug_html = OUT_DIR / "NewspaperSG_史料长编_v1.html"
    debug_html.write_text(html_str, encoding="utf-8")
    print(f"中间 HTML 已写：{debug_html}", file=sys.stderr)

    # 渲染 PDF
    from weasyprint import HTML
    HTML(string=html_str, base_url=str(ROOT)).write_pdf(OUT_PDF)
    print(f"\n=== 完成 ===", file=sys.stderr)
    print(f"长编 PDF: {OUT_PDF}", file=sys.stderr)
    print(f"  大小: {OUT_PDF.stat().st_size//1024} KB", file=sys.stderr)


if __name__ == "__main__":
    main()
