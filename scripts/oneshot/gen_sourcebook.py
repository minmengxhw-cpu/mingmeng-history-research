#!/usr/bin/env python3
"""史料长编生成器——按平台输出「按时间线编排、英文原文+中文译文对照」的研究文献。

输出为出版级排版的 PDF（HTML + WeasyPrint）。
用法:
    python3 gen_sourcebook.py wilson      # 单个平台
    python3 gen_sourcebook.py all         # 全部 5 个平台
台北档案（drnh）目前仅有案由、无全文，不在范围内。
"""
import html
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path

from weasyprint import HTML

ROOT = Path(__file__).resolve().parent.parent.parent
DB = ROOT / "data" / "research_index.sqlite"
OUT = Path("/home/zq/work/mm/mm-bot/workspace")

PLATFORMS = {
    "frus": ("美国对外关系文件集", "Foreign Relations of the United States (FRUS)",
             "美国国务院官方编纂的外交文件集，收录国务院、驻华使领馆与白宫间"
             "的往来电报、备忘录与会谈记录。"),
    "cia": ("美国中央情报局解密档案", "CIA FOIA Electronic Reading Room",
            "美国中央情报局依《信息自由法》解密公开的情报评估、报告与电文。"),
    "wilson": ("威尔逊中心数字档案", "Wilson Center Digital Archive",
               "美国威尔逊国际学者中心「冷战国际史项目」整理公开的多国解密档案，"
               "含苏联、美国等方面的外交文电。"),
    "hoover": ("胡佛研究所档案", "Hoover Institution Archives",
               "斯坦福大学胡佛研究所典藏的近代中国政治人物与机构档案。"),
    "hathitrust": ("HathiTrust 数字典藏", "HathiTrust Digital Library",
                   "由 HathiTrust 数字图书馆与 Internet Archive 数字化的"
                   "同时期图书、报刊与文献。"),
}

CSS = """
@page {
  size: A4;
  margin: 25mm 22mm 22mm 22mm;
  @top-center { content: string(runhead); font-family: "Noto Serif CJK SC";
                font-size: 8pt; color: #9a9384; letter-spacing: .05em; }
  @bottom-center { content: counter(page); font-family: "Noto Serif CJK SC";
                   font-size: 9pt; color: #6b6352; }
}
@page cover { margin: 0; @top-center { content: ""; } @bottom-center { content: ""; } }
@page front { @top-center { content: ""; } }

body { font-family: "Noto Serif CJK SC", "Noto Serif", serif;
       font-size: 10.5pt; line-height: 1.75; color: #221f18;
       text-align: justify; }

/* ——— 封面 ——— */
.cover { page: cover; height: 100vh; box-sizing: border-box;
         padding: 70mm 26mm 30mm; text-align: center;
         border-top: 12mm solid #5a3a26; }
.cover .lib { font-size: 11pt; color: #8a8273; letter-spacing: .3em; }
.cover .kind { margin-top: 4mm; font-size: 13pt; color: #5a3a26;
               letter-spacing: .5em; }
.cover h1 { font-size: 34pt; margin: 14mm 0 4mm; color: #221f18;
            letter-spacing: .08em; font-weight: 700; }
.cover .vol { font-size: 17pt; color: #0f6b5b; margin-bottom: 3mm;
              letter-spacing: .12em; }
.cover .en { font-size: 10.5pt; color: #8a8273; font-style: italic; }
.cover .rule { width: 40mm; border-bottom: .6pt solid #b9a98c;
               margin: 12mm auto; }
.cover .desc { font-size: 11pt; color: #443f33; line-height: 2; }
.cover .foot { position: absolute; bottom: 32mm; left: 0; right: 0;
               font-size: 10pt; color: #8a8273; }

/* ——— 前置页 ——— */
.front { page: front; }
.front h2 { font-size: 16pt; color: #5a3a26; text-align: center;
            letter-spacing: .3em; margin: 4mm 0 8mm;
            padding-bottom: 3mm; border-bottom: .6pt solid #d8ccb4; }
.front p { text-indent: 2em; margin: 0 0 3mm; }
.front .sign { text-align: right; text-indent: 0; color: #6b6352;
               font-size: 10pt; margin-top: 6mm; }

/* ——— 目录 ——— */
.toc { page: front; }
.toc h2 { font-size: 16pt; color: #5a3a26; text-align: center;
          letter-spacing: .3em; margin: 4mm 0 8mm;
          padding-bottom: 3mm; border-bottom: .6pt solid #d8ccb4; }
.toc .year { font-weight: 700; color: #5a3a26; margin: 5mm 0 2mm;
             font-size: 11pt; }
.toc .item { display: flex; font-size: 10pt; margin: 1.4mm 0;
             color: #332f26; }
.toc .item .t { flex: 1; padding-right: 3mm; }
.toc .item .d { color: #8a8273; white-space: nowrap; }

/* ——— 正文 ——— */
.body { string-set: runhead "中国民主同盟史料长编"; }
.year-head { font-size: 15pt; font-weight: 700; color: #5a3a26;
             text-align: center; margin: 10mm 0 6mm; letter-spacing: .2em;
             page-break-before: auto; }
.year-head .yr-rule { display: block; width: 30mm; margin: 2mm auto 0;
                      border-bottom: .8pt solid #b9a98c; }

.entry { margin: 0 0 9mm; page-break-inside: auto; }
.entry .no-title { font-size: 12pt; font-weight: 700; color: #221f18;
                   line-height: 1.5; margin-bottom: 2mm;
                   page-break-after: avoid; }
.entry .no-title .no { color: #0f6b5b; margin-right: 2mm; }
.entry .meta { font-size: 8.6pt; color: #6b6352; background: #f6f1e6;
               border-left: 2.4pt solid #b9a98c; padding: 2mm 3mm;
               margin-bottom: 3mm; line-height: 1.6; word-break: break-all; }
.entry .seclabel { font-size: 9.4pt; font-weight: 700; color: #5a3a26;
                   letter-spacing: .15em; margin: 3mm 0 1.5mm;
                   page-break-after: avoid; }
.entry .en-text { font-family: "Noto Serif", "Noto Serif CJK SC", serif;
                  font-size: 9.8pt; line-height: 1.62; color: #2d2a22; }
.entry .en-text p { margin: 0 0 1.8mm; text-align: justify; }
.entry .zh-text { font-size: 10.6pt; line-height: 1.85; color: #221f18; }
.entry .zh-text p { margin: 0 0 2mm; text-indent: 2em; text-align: justify; }
.entry .pagemark { font-size: 8pt; color: #9a9384; font-style: italic;
                   margin: 1.5mm 0 .8mm; }
.entry .none { color: #9a9384; font-size: 9.5pt; }
.entry-rule { border: 0; border-bottom: .5pt dotted #c9bda2;
              margin: 0 0 9mm; }
"""


def esc(s: str) -> str:
    return html.escape(s or "")


def clean_md(s: str) -> str:
    """清除文本中残留的 markdown 标记（译文中偶有 **加粗**、# 标题、- 列表等）。"""
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)          # 粗体
    s = re.sub(r"(?<!\*)\*(?!\*)([^*\n]+?)\*(?!\*)", r"\1", s)  # 斜体
    s = re.sub(r"^\s{0,3}#{1,6}\s*", "", s, flags=re.M)  # 标题井号
    s = re.sub(r"^\s*[-*+]\s+", "", s, flags=re.M)       # 列表符号
    return s.replace("**", "").replace("__", "")


# 应整行删除的元信息行（保留正文流畅，删掉档案样板/占位垃圾）
_META_LINE = re.compile(
    r"^\s*(摘要|致谢|鸣谢|原文语种|原文语言|语种|目录|内容|引文|出处来源|档案来源"
    r"|档案标题|档案编号|档案原文|来源|Summary|Credits|Citation|Original Language"
    r"|Contents)\s*[：:]",
    re.I,
)
_BARE_NOISE = {"档案原文", "国际史解密档案", "英文译文", "English Translation",
               "Digital Archive", "分页符"}


def clean_archive_text(text: str, lang: str) -> str:
    """清洗档案原始文本：去样板头、分页符、页码标记、占位垃圾，保持正文流畅。"""
    text = (text or "").strip()
    if not text:
        return ""
    if lang == "en":
        # 维尔逊数字档案样板头：截到 "Contents: English Translation" 之后即正文
        m = re.search(r"Contents:\s*English Translation\s*", text[:1400], re.I)
        if m:
            text = text[m.end():]
    else:
        text = clean_md(text)
        # 移除大模型应答垃圾段落（"抱歉，您似乎/请提供/无法处理…"），可能出现在任意页
        blocks = re.split(r"\n\s*\n", text)
        kept = [b for b in blocks if not (
            b.lstrip().startswith("抱歉") and re.search(
                r"您似乎|您提供|请提供|无法处理|按照您的要求|没有提供|需要翻译", b))]
        text = "\n\n".join(kept)
        # 译文前置元信息块：截到 "目录/内容：英文译文" 之后即正文
        m = re.search(r"(目录|内容)\s*[：:]\s*英文译文\s*", text[:1400])
        if m:
            text = text[m.end():]
    # 占位垃圾（此处为…待翻译…）整体抹去
    text = re.sub(r"[（(]\s*此处[^）)]*[）)]", "", text)
    text = re.sub(r"[（(]\s*待翻译[^）)]*[）)]", "", text)
    # 逐行去噪
    keep = []
    for ln in text.split("\n"):
        s = ln.strip()
        if not s:
            keep.append("")
            continue
        # markdown 表格行：分隔行直接弃，数据行去竖线
        if "|" in s and (s.startswith("|") or s.count("|") >= 2):
            if re.fullmatch(r"[\s:|+\-]{3,}", s):
                continue
            s = re.sub(r"\s*\|\s*", " ", s).strip()
            if not s:
                continue
        if re.fullmatch(r"[-—–_=*·.\s]{3,}", s) or "分页符" in s:   # 分隔线/分页符
            continue
        if re.search(r"page\s*break", s, re.I) and len(s) < 32:     # --- page break ---
            continue
        if re.fullmatch(r"\[?\s*(p\.?\s*\d+|page\s*\d+|page|第\s*\d+\s*页"
                        r"|第[一二三四五六七八九十百]+页)\s*\]?", s, re.I):  # 页码标记
            continue
        if len(s) < 32 and re.search(r"[A-Za-z](\s*-\s*[A-Za-z0-9]){3,}", s):  # 拼写式密级章
            continue
        if re.fullmatch(r":?\s*CIA-[A-Z0-9][A-Z0-9-]+", s, re.I):   # 档案控制号
            continue
        if (re.search(r"Declassif|Decisesiied|Sanitiz|anitiz\w* Cop", s)   # 解密处理章
                or re.search(r"ppp?roved\W{0,4}([Ff]o|Rele|Wease)", s)     # (A)pproved For…
                or re.search(r"[Cc]opy\s+[Aa]?ppp?rov", s)                 # …Copy Approved
                or re.search(r"[lt]ease\s+:?\s*(?:19|20)\s?\d", s)          # …Release 19/20XX(含空格残形)
                or re.search(r"CIA[\s.\-]{0,2}R[DM]P?\s?\d", s)             # …控制号
                or re.match(r"\W{0,4}Approved\b", s)):                       # 行首"Approved"=解密章
            continue
        if len(s) > 8:                                                      # OCR 乱码行
            _weird = len(re.findall(
                r"[^\w\s一-鿿，。；：、！？“”‘’（）()\[\]/.,;:!?'\"&%—–-]", s))
            if _weird / len(s) > 0.12:
                continue
        if s in _BARE_NOISE:
            continue
        if _META_LINE.match(s):
            continue
        keep.append(s)
    text = "\n".join(keep)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def to_paras(text: str, en: bool) -> str:
    """把已清洗的文本切成段落 HTML。空行分段，段内换行并为空格。"""
    text = (text or "").strip()
    if not text:
        return ""
    blocks = re.split(r"\n\s*\n", text)
    out = []
    for b in blocks:
        b = re.sub(r"\s*\n\s*", " ", b).strip()
        b = re.sub(r"[ \t]{2,}", " ", b)
        if b:
            out.append(f"<p>{esc(b)}</p>")
    return "\n".join(out)


def fetch(platform):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    docs = c.execute(
        """SELECT id, doc_key, title, date_guess, url
           FROM documents WHERE COALESCE(source_platform,'frus')=?
           ORDER BY date_guess, id""",
        (platform,),
    ).fetchall()
    items = []
    for d in docs:
        pages = c.execute(
            "SELECT page_label, text FROM pages WHERE document_id=? ORDER BY id",
            (d["id"],),
        ).fetchall()
        trans = c.execute(
            """SELECT p.page_label pl, t.text tx FROM pages p
               JOIN translations t ON t.page_id=p.id AND t.language='zh-CN'
               WHERE p.document_id=? ORDER BY p.id""",
            (d["id"],),
        ).fetchall()
        items.append((d, pages, trans))
    c.close()
    return items


def build(platform):
    zh_name, en_name, intro = PLATFORMS[platform]
    items = fetch(platform)
    if not items:
        print(f"[跳过] {platform}：无文档")
        return
    dates = [d["date_guess"] for d, _, _ in items if d["date_guess"]]
    span = f"{dates[0]} — {dates[-1]}" if dates else "时间不详"
    today = f"{date.today():%Y 年 %m 月}"

    # 封面
    parts = [f"""<div class="cover">
  <div class="lib">民盟历史文献研究库</div>
  <div class="kind">史 料 长 编</div>
  <h1>{esc(zh_name)}</h1>
  <div class="vol">中国民主同盟史料长编 · 分卷</div>
  <div class="en">{esc(en_name)}</div>
  <div class="rule"></div>
  <div class="desc">1941—1950 年中国民主同盟<br>中国大陆境外一手档案<br>
    英文原文与中文译文对照 · 按时间线编排</div>
  <div class="foot">收录档案 {len(items)} 篇　·　{esc(span)}<br>
    民盟历史文献研究项目组（编）　·　{today}</div>
</div>"""]

    # 编者说明
    parts.append(f"""<div class="front">
  <h2>编 者 说 明</h2>
  <p>本编为「民盟历史文献研究库」史料长编系列之一，汇辑 {esc(en_name)}
    （{esc(zh_name)}）中与中国民主同盟相关的一手史料，共 {len(items)} 篇，
    时间跨度 {esc(span)}。</p>
  <p>{esc(intro)}</p>
  <p>全编按档案日期先后编排，每篇先列档案信息（日期、标题、出处与原档链接），
    继列英文原文，再列中文译文。英文原文照录自原始档案数字化文本，可能含
    扫描识别（OCR）噪声，未作改动；中文译文供研究参考。正式学术引用请以
    原始档案为准，并按各档案出处依 GB/T 7714 著录。</p>
  <p>本编为研究编排与翻译整理之成果，原始档案版权归各档案馆所属机构所有。</p>
  <p class="sign">民盟历史文献研究项目组</p>
</div>""")

    # 目录
    toc = ['<div class="toc"><h2>目 　 录</h2>']
    cur = None
    for i, (d, _, _) in enumerate(items, 1):
        yr = (d["date_guess"] or "0000")[:4]
        if yr != cur:
            cur = yr
            label = f"{yr} 年" if yr != "0000" else "日期不详"
            toc.append(f'<div class="year">{label}</div>')
        title = esc((d["title"] or "（无标题）"))
        toc.append(
            f'<div class="item"><span class="t">{i}. {title}</span>'
            f'<span class="d">{esc(d["date_guess"] or "—")}</span></div>'
        )
    toc.append("</div>")
    parts.append("\n".join(toc))

    # 正文
    body = ['<div class="body">']
    cur = None
    for i, (d, pages, trans) in enumerate(items, 1):
        yr = (d["date_guess"] or "0000")[:4]
        if yr != cur:
            cur = yr
            label = f"{yr} 年" if yr != "0000" else "日期不详"
            body.append(f'<div class="year-head">{label}'
                         f'<span class="yr-rule"></span></div>')
        en_raw = clean_archive_text(
            "\n\n".join(p["text"] or "" for p in pages), "en")
        zh_raw = clean_archive_text(
            "\n\n".join(t["tx"] or "" for t in trans), "zh")
        en_html = to_paras(en_raw, True) or '<div class="none">（无原文文本）</div>'
        zh_html = to_paras(zh_raw, False) or '<div class="none">（暂无中文译文）</div>'
        url = (f'　|　原档链接：{esc(d["url"])}' if d["url"] else "")
        body.append(f"""<div class="entry">
  <div class="no-title"><span class="no">{i}.</span>{esc(d["title"] or "（无标题）")}</div>
  <div class="meta">日期：{esc(d["date_guess"] or "不详")}　|　出处：{esc(en_name)}　|　本库 ID：doc/{esc(d["doc_key"])}{url}</div>
  <div class="seclabel">英 文 原 文</div>
  <div class="en-text">{en_html}</div>
  <div class="seclabel">中 文 译 文</div>
  <div class="zh-text">{zh_html}</div>
</div>
<hr class="entry-rule">""")
    body.append("</div>")
    parts.append("\n".join(body))

    doc_html = f"""<!DOCTYPE html><html lang="zh-CN"><head>
<meta charset="utf-8"><style>{CSS}</style></head>
<body>{''.join(parts)}</body></html>"""

    out = OUT / f"民盟史料长编_{zh_name}_{platform}.pdf"
    HTML(string=doc_html).write_pdf(str(out))
    print(f"[完成] {platform}：{len(items)} 篇 -> {out.name}")


def main():
    arg = sys.argv[1] if len(sys.argv) > 1 else "wilson"
    keys = list(PLATFORMS) if arg == "all" else [arg]
    for k in keys:
        if k not in PLATFORMS:
            print(f"[错误] 未知平台 {k}；可选 {', '.join(PLATFORMS)} / all")
            continue
        build(k)


if __name__ == "__main__":
    main()
