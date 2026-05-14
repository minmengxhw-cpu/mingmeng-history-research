#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import re
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse


ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "data" / "research_index.sqlite"
HOME_FOCUS_PATH = ROOT / "data" / "home_focus.json"


def h(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def compact(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


PERSON_ZH = {
    "Atcheson": "艾奇逊",
    "Cabot": "卡伯特",
    "Clubb": "柯乐博",
    "Caughey": "考吉",
    "Clark": "克拉克",
    "Dams": "达姆斯",
    "Gauss": "高斯",
    "Hopper": "霍珀",
    "Hurley": "赫尔利",
    "Langdon": "兰登",
    "Marshall": "马歇尔",
    "McConaughy": "麦康纳",
    "McKenna": "麦肯纳",
    "Myers": "迈尔斯",
    "Penfield": "彭菲尔德",
    "Rice": "赖斯",
    "Ringwalt": "林沃尔特",
    "Service": "谢伟思",
    "Smyth": "史密斯",
    "Sprouse": "斯普劳斯",
    "Stuart": "司徒雷登",
}


ROLE_ZH = {
    "The Ambassador in China": "驻华大使",
    "The Appointed Ambassador in China": "被任命的驻华大使",
    "The Ambassador Designate in China": "候任驻华大使",
    "The Chargé in China": "驻华代办",
    "The Counselor of Embassy in China": "驻华使馆参赞",
    "The Minister-Counselor of Embassy in China": "驻华使馆公使衔参赞",
    "The Consul at Kweilin": "驻桂林领事",
    "The Consul General at Kunming": "驻昆明总领事",
    "The Consul General at Shanghai": "驻上海总领事",
    "The Consul General at Hong Kong": "驻香港总领事",
    "The Consul General at Peiping": "驻北平总领事",
    "The Consul General at Tientsin": "驻天津总领事",
    "The Vice Consul at Chengtu": "驻成都副领事",
    "The Second Secretary of Embassy in China": "驻华使馆第二书记",
    "The Acting Secretary of State": "代理国务卿",
    "The Secretary of State": "国务卿",
}


EXACT_TITLE_ZH = {
    "Memorandum by the Second Secretary of Embassy in China (Sprouse)": "驻华使馆第二书记斯普劳斯备忘录",
    "Memorandum by the Second Secretary of Embassy in China (Sprouse) to General Marshall": "驻华使馆第二书记斯普劳斯致马歇尔将军备忘录",
    "Minutes of Conference Between General Marshall and Dr. Lo Lung-chi at General Marshall’s House, June 1, 1946, 10 a.m.": "马歇尔将军与罗隆基博士会谈纪要，1946年6月1日上午10时",
    "Counterproposals by the Chinese Communist Party": "中国共产党方面的反建议",
    "Chinese National Government’s Reply to Communist Party’s Counterproposals": "中国国民政府对共产党反建议的答复",
    "General Marshall’s Notes on a Conference With Dr. Wang Shihchieh, at Nanking, January 7, 1947, 5 p.m.": "马歇尔将军关于1947年1月7日下午5时在南京同王世杰博士会谈的记录",
    "Memorandum Concerning United States Post-War Military Policies With Respect to China": "关于美国战后对华军事政策的备忘录",
}


def person_zh(name: str) -> str:
    return PERSON_ZH.get(name, name)


def role_zh(role: str) -> str:
    role = role.strip()
    candidates = [role]
    if role.startswith("the "):
        candidates.append("The " + role[4:])
    if role.startswith("The "):
        candidates.append("the " + role[4:])
    for candidate in candidates:
        if candidate in ROLE_ZH:
            return ROLE_ZH[candidate]
    return role


def role_with_person(role: str, person: str) -> str:
    return f"{role_zh(role)}（{person_zh(person)}）"


def translate_title(title: str) -> str:
    title = title or ""
    if title in EXACT_TITLE_ZH:
        return EXACT_TITLE_ZH[title]

    m = re.match(r"(.+?) \(([^)]+)\) to (.+?) \(([^)]+)\)$", title)
    if m:
        src_role, src_person, dst_role, dst_person = m.groups()
        return f"{role_with_person(src_role, src_person)}致{role_with_person(dst_role, dst_person)}"

    m = re.match(r"(.+?) \(([^)]+)\) to (.+)$", title)
    if m:
        src_role, src_person, dst_role = m.groups()
        return f"{role_with_person(src_role, src_person)}致{role_zh(dst_role)}"

    m = re.match(r"Memorandum by (.+?) \(([^)]+)\)$", title)
    if m:
        role, person = m.groups()
        return f"{role_with_person(role, person)}备忘录"

    m = re.match(r"(.+?) \(([^)]+)\)$", title)
    if m:
        role, person = m.groups()
        return role_with_person(role, person)

    return title


def title_block(title: str, href: str | None = None, level: str = "h2") -> str:
    zh = translate_title(title)
    main = f'<a href="{h(href)}">{h(zh)}</a>' if href else h(zh)
    english = "" if zh == title else f'<div class="title-en">{h(title)}</div>'
    return f"<{level}>{main}</{level}>{english}"


def source_page_label(row: sqlite3.Row) -> str:
    return f"p. {row['page_label']}" if row["page_label"] else "doc-level"


def short_citation(row: sqlite3.Row) -> str:
    page = source_page_label(row)
    date = row["date_guess"] or row["event_date"] if "event_date" in row.keys() else row["date_guess"]
    return f"{translate_title(row['title'])}，{date or '日期未注明'}，{page}。"


def bibliography_entry(row: sqlite3.Row) -> str:
    page = source_page_label(row)
    source_url = ""
    if "page_url" in row.keys():
        source_url = row["page_url"] or ""
    if not source_url and "doc_url" in row.keys():
        source_url = row["doc_url"] or ""
    volume = row["volume_title"] if "volume_title" in row.keys() else ""
    return (
        f"Foreign Relations of the United States, {row['volume_id']}"
        f"{', ' + volume if volume else ''}, {translate_title(row['title'])}, "
        f"{row['date_guess'] or ''}, {page}, {source_url}"
    ).strip()


def grade_badge(row: sqlite3.Row) -> str:
    grade = row["grade"] if "grade" in row.keys() else ""
    if not grade:
        return ""
    class_name = "grade context" if grade in {"人物关联", "背景材料"} else "grade"
    return f'<span class="{class_name}">{h(grade)}</span>'


ISSUE_LABELS = {
    "known_bad_term": "已知误译",
    "glossary_miss": "术语待查",
    "english_residue": "英文残留",
    "length_short": "译文偏短",
    "length_too_short": "译文过短",
    "length_long": "译文偏长",
    "core_machine_draft": "核心初稿",
    "missing_translation": "缺少译文",
}


PEOPLE = [
    {"slug": "lo-lung-chi", "name": "罗隆基", "aliases": ["Lo Lung-chi", "Lo Lung Chi", "Lo Lung", "罗隆基", "罗龙基", "罗龙志", "洛龙芝"]},
    {"slug": "chang-lan", "name": "张澜", "aliases": ["Chang Lan", "Chang Piao-fang", "张澜"]},
    {"slug": "liang-shu-ming", "name": "梁漱溟", "aliases": ["Liang Shu-ming", "梁漱溟"]},
    {"slug": "shen-chun-ju", "name": "沈钧儒", "aliases": ["Shen Chun-ju", "沈钧儒"]},
    {"slug": "huang-yen-pei", "name": "黄炎培", "aliases": ["Huang Yen-pei", "黄炎培", "黄延培"]},
    {"slug": "chang-po-chun", "name": "章伯钧", "aliases": ["Chang Po-chun", "章伯钧"]},
    {"slug": "shih-liang", "name": "史良", "aliases": ["Shih Liang", "史良"]},
    {"slug": "carsun-chang", "name": "张君劢", "aliases": ["Carsun Chang", "Chang Chun-mai", "张君劢", "嘉善昌"]},
    {"slug": "chang-tung-sun", "name": "张东荪", "aliases": ["Chang Tung-sun", "Chang Tung Sun", "张东荪", "张敦善"]},
    {"slug": "chou-en-lai", "name": "周恩来", "aliases": ["Chou En-lai", "Chou Enlai", "周恩来", "周将军"]},
]


TOPICS = [
    {
        "slug": "kunming-assassinations",
        "name": "昆明暗杀与民盟政治压力",
        "brief": "围绕李公朴、闻一多遇害及美国领事保护、马歇尔调处中的政治影响。",
        "terms": ["Kunming", "assassin", "assassination", "李公朴", "闻一多", "暗杀", "昆明"],
    },
    {
        "slug": "pcc-1946",
        "name": "1946 年政治协商会议",
        "brief": "政协、政协指导委员会、国民大会、联合政府与第三方面斡旋。",
        "terms": ["Political Consultative", "PCC", "政治协商", "政协", "国民大会", "Steering Committee"],
    },
    {
        "slug": "marshall-mediation",
        "name": "马歇尔调处与民盟",
        "brief": "马歇尔与民盟、第三方面、国共双方围绕停战和改组政府的会谈。",
        "terms": ["Marshall", "马歇尔", "truce", "cease", "停战", "调处", "mediation"],
    },
    {
        "slug": "third-force",
        "name": "第三方面与中间路线",
        "brief": "民盟、青年党、民主社会党及无党派人士在国共之间的政治空间。",
        "terms": ["Third Party", "third party", "third force", "第三方面", "中间路线", "Youth Party", "Democratic Socialist"],
    },
    {
        "slug": "peiping-1949",
        "name": "1949 年北平接触",
        "brief": "北平、上海、香港之间关于民盟人士、美国使馆和中共当局的接触材料。",
        "terms": ["Peiping", "1949", "北平", "Clubb", "Lo Lung-chi", "Chang Lan", "Li Chi-shen"],
    },
]


def issue_label(value: str) -> str:
    return ISSUE_LABELS.get(value, value)


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def layout(title: str, body: str, query: str = "") -> bytes:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{h(title)}</title>
  <style>
    :root {{
      --bg: #f7f8fa;
      --panel: #ffffff;
      --line: #d9dee7;
      --text: #1f2933;
      --muted: #627083;
      --accent: #0f6b5b;
      --accent-ink: #ffffff;
      --warn: #8a5a00;
      --mark: #fff0a6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--bg);
      color: var(--text);
      font: 15px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Arial, sans-serif;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .topbar {{
      position: sticky;
      top: 0;
      z-index: 10;
      display: grid;
      grid-template-columns: minmax(170px, 260px) minmax(280px, 1fr) auto;
      gap: 12px;
      align-items: center;
      padding: 12px 18px;
      border-bottom: 1px solid var(--line);
      background: rgba(255,255,255,.96);
    }}
    .brand {{ font-weight: 700; letter-spacing: 0; white-space: nowrap; }}
    .search {{ display: flex; min-width: 0; }}
    .search input {{
      width: 100%;
      min-width: 0;
      border: 1px solid var(--line);
      border-right: 0;
      border-radius: 6px 0 0 6px;
      padding: 9px 11px;
      font: inherit;
      background: #fff;
    }}
    .search button {{
      min-width: 72px;
      flex: 0 0 72px;
      border: 1px solid var(--accent);
      border-radius: 0 6px 6px 0;
      padding: 0 14px;
      background: var(--accent);
      color: var(--accent-ink);
      font: inherit;
      white-space: nowrap;
      word-break: keep-all;
      overflow-wrap: normal;
      text-wrap: nowrap;
      line-height: 1;
      cursor: pointer;
    }}
    .navlink {{ color: var(--muted); font-size: 14px; }}
    main {{ padding: 18px; }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(130px, 1fr));
      gap: 1px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--line);
      margin-bottom: 18px;
    }}
    .stat {{ background: var(--panel); padding: 13px 15px; }}
    .stat strong {{ display: block; font-size: 22px; line-height: 1.2; }}
    .stat span {{ color: var(--muted); font-size: 13px; }}
    .result-list {{
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: var(--panel);
    }}
    .result {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 150px;
      gap: 16px;
      padding: 14px 16px;
      border-top: 1px solid var(--line);
    }}
    .result:first-child {{ border-top: 0; }}
    .result h2 {{ margin: 0 0 6px; font-size: 16px; line-height: 1.35; }}
    .title-en {{
      margin: -2px 0 7px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.35;
    }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .snippet {{ margin-top: 8px; color: #34404f; }}
    .zh {{ margin-top: 8px; color: #243b35; }}
    .tagline {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 9px; }}
    .tag {{ border: 1px solid var(--line); border-radius: 999px; padding: 2px 8px; font-size: 12px; color: var(--muted); }}
    .grade {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      background: #eef7f4;
      color: var(--accent);
      border: 1px solid #c9e4dc;
    }}
    .grade.context {{ background: #f4f6f8; color: var(--muted); border-color: var(--line); }}
    .issue {{
      display: inline-flex;
      align-items: center;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 12px;
      border: 1px solid #ead4a2;
      color: #7a5200;
      background: #fff8e8;
    }}
    .issue.high {{
      border-color: #e4b5aa;
      color: #8a2d1f;
      background: #fff1ee;
    }}
    .cite {{ text-align: right; font-size: 13px; color: var(--muted); }}
    .doc-head {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 16px;
      align-items: start;
      padding: 16px 18px;
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      margin-bottom: 16px;
      scroll-margin-top: 82px;
    }}
    .doc-head h1 {{ margin: 0 0 5px; font-size: 21px; line-height: 1.3; }}
    .doc-tools {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    .button {{
      display: inline-flex;
      align-items: center;
      min-height: 32px;
      padding: 5px 10px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      color: var(--text);
      font-size: 13px;
    }}
    .button.active {{
      border-color: var(--accent);
      color: var(--accent);
      background: #eef7f4;
    }}
    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0 0 14px;
    }}
    .reader {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 14px;
    }}
    .segment {{
      display: contents;
    }}
    .pane {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      min-width: 0;
      scroll-margin-top: 76px;
    }}
    .pane-head {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      padding: 9px 12px;
      border-bottom: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
      background: #fbfcfd;
      border-radius: 8px 8px 0 0;
    }}
    .pane-body {{
      padding: 13px 14px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }}
    textarea.review-text {{
      width: 100%;
      min-height: 460px;
      resize: vertical;
      border: 0;
      padding: 13px 14px;
      font: inherit;
      line-height: 1.65;
      color: var(--text);
      background: #fff;
      outline: none;
    }}
    .formbar {{
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      align-items: center;
      padding: 10px 12px;
      border-top: 1px solid var(--line);
      background: #fbfcfd;
      border-radius: 0 0 8px 8px;
    }}
    .formbar select {{
      min-height: 32px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: #fff;
      padding: 4px 8px;
      font: inherit;
    }}
    .formbar button {{
      min-height: 32px;
      border: 1px solid var(--accent);
      border-radius: 6px;
      background: var(--accent);
      color: #fff;
      padding: 4px 12px;
      font: inherit;
      cursor: pointer;
    }}
    .copybox {{
      width: 100%;
      min-height: 260px;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      font: 14px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      color: var(--text);
      background: #fff;
      resize: vertical;
    }}
    .empty {{ color: var(--muted); font-style: italic; }}
    mark {{ background: var(--mark); padding: 0 2px; border-radius: 2px; }}
    .notice {{
      border: 1px solid var(--line);
      border-radius: 8px;
      background: var(--panel);
      padding: 16px;
      color: var(--muted);
    }}
    @media (max-width: 820px) {{
      .topbar {{ grid-template-columns: 1fr; }}
      main {{ padding: 12px; }}
      .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .result {{ grid-template-columns: 1fr; }}
      .cite {{ text-align: left; }}
      .doc-head {{ grid-template-columns: 1fr; }}
      .doc-tools {{ justify-content: flex-start; }}
      .reader {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header class="topbar">
    <a class="brand" href="/">民盟历史文献研究库</a>
    <form class="search" method="get" action="/search">
      <input name="q" value="{h(query)}" placeholder="搜索原文或中文译文">
      <button type="submit">搜索</button>
    </form>
    <div style="display:flex;gap:12px;justify-content:flex-end;white-space:nowrap;">
      <a class="navlink" href="/docs">全部文档</a>
      <a class="navlink" href="/tasks">校订任务</a>
      <a class="navlink" href="/people">人物索引</a>
      <a class="navlink" href="/topics">专题</a>
      <a class="navlink" href="/timeline">年表</a>
      <a class="navlink" href="/events">事件</a>
      <a class="navlink" href="/dashboard">进度</a>
      <a class="navlink" href="/quality">质量检查</a>
    </div>
  </header>
  <main>{body}</main>
</body>
</html>""".encode("utf-8")


def stats_html(c: sqlite3.Connection) -> str:
    docs = c.execute("SELECT count(*) FROM documents").fetchone()[0]
    grades = {row[0]: row[1] for row in c.execute("SELECT grade, count(*) FROM document_classifications GROUP BY grade")}
    zh = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN'").fetchone()[0]
    try:
        quality = c.execute("SELECT count(DISTINCT page_id) FROM translation_quality_issues WHERE severity >= 2").fetchone()[0]
    except sqlite3.OperationalError:
        quality = 0
    return f"""
<section class="stats">
  <div class="stat"><strong>{docs}</strong><span>文档总数</span></div>
  <div class="stat"><strong>{grades.get("核心文献", 0)}</strong><span>核心文献</span></div>
  <div class="stat"><strong>{grades.get("相关文献", 0)}</strong><span>相关文献</span></div>
  <div class="stat"><strong>{grades.get("人物关联", 0)}</strong><span>人物关联</span></div>
  <div class="stat"><strong>{grades.get("背景材料", 0)}</strong><span>背景材料</span></div>
  <div class="stat"><strong>{zh}</strong><span>中文译文片段</span></div>
  <div class="stat"><strong>{quality}</strong><span>高优先级质量提示</span></div>
</section>"""


def docs_url(grade: str = "", translation: str = "") -> str:
    params = []
    if grade:
        params.append(f"grade={quote(grade)}")
    if translation:
        params.append(f"translation={quote(translation)}")
    return "/docs" + (("?" + "&".join(params)) if params else "")


def quality_url(severity: str = "", issue: str = "") -> str:
    params = []
    if severity:
        params.append(f"severity={quote(severity)}")
    if issue:
        params.append(f"issue={quote(issue)}")
    return "/quality" + (("?" + "&".join(params)) if params else "")


def tasks_url(queue: str = "") -> str:
    return "/tasks" + (f"?queue={quote(queue)}" if queue else "")


def grade_filters(active_grade: str = "", active_translation: str = "") -> str:
    grades = ["", "核心文献", "相关文献", "人物关联", "背景材料"]
    labels = {"": "全部"}
    chips = []
    for grade in grades:
        label = labels.get(grade, grade)
        href = docs_url(grade, active_translation)
        cls = "button active" if grade == active_grade else "button"
        chips.append(f'<a class="{cls}" href="{href}">{h(label)}</a>')
    translation_filters = [
        ("", "全部译文状态"),
        ("translated", "有译文"),
        ("missing", "未翻译"),
    ]
    translation_chips = []
    for value, label in translation_filters:
        cls = "button active" if value == active_translation else "button"
        translation_chips.append(f'<a class="{cls}" href="{docs_url(active_grade, value)}">{h(label)}</a>')
    return '<div class="filters">' + "".join(chips) + '</div><div class="filters">' + "".join(translation_chips) + "</div>"


def quality_filters(active_severity: str = "", active_issue: str = "") -> str:
    severities = [
        ("", "全部严重度"),
        ("3", "严重"),
        ("2", "需要检查"),
        ("1", "低优先级"),
    ]
    issues = [
        ("", "全部问题"),
        ("known_bad_term", "已知误译"),
        ("glossary_miss", "术语待查"),
        ("english_residue", "英文残留"),
        ("length_short", "译文偏短"),
        ("core_machine_draft", "核心初稿"),
    ]
    sev_chips = []
    for value, label in severities:
        cls = "button active" if value == active_severity else "button"
        sev_chips.append(f'<a class="{cls}" href="{quality_url(value, active_issue)}">{h(label)}</a>')
    issue_chips = []
    for value, label in issues:
        cls = "button active" if value == active_issue else "button"
        issue_chips.append(f'<a class="{cls}" href="{quality_url(active_severity, value)}">{h(label)}</a>')
    return '<div class="filters">' + "".join(sev_chips) + '</div><div class="filters">' + "".join(issue_chips) + "</div>"


def task_filters(active_queue: str = "") -> str:
    queues = [
        ("", "全部任务"),
        ("core", "核心优先"),
        ("people", "人物线索"),
        ("topics", "专题线索"),
        ("terms", "术语待查"),
        ("english", "英文残留"),
    ]
    chips = []
    for value, label in queues:
        cls = "button active" if value == active_queue else "button"
        chips.append(f'<a class="{cls}" href="{tasks_url(value)}">{h(label)}</a>')
    return '<div class="filters">' + "".join(chips) + "</div>"


def topic_tags(row: sqlite3.Row) -> list[str]:
    text = " ".join(str(row[key] or "") for key in row.keys() if key in {"title", "matched_terms", "original_text", "zh_text"})
    tags: list[str] = []
    checks = [
        ("罗隆基", ["Lo Lung-chi", "Lo Lung Chi", "罗隆基"]),
        ("昆明暗杀", ["Kunming", "assassination", "暗杀", "李公朴", "闻一多"]),
        ("政协", ["Political Consultative", "PCC", "政治协商", "政协"]),
        ("马歇尔调处", ["Marshall", "马歇尔"]),
        ("北平接触", ["Peiping", "北平", "Clubb", "柯乐博"]),
        ("1949", ["1949"]),
    ]
    for label, needles in checks:
        if any(needle.lower() in text.lower() for needle in needles):
            tags.append(label)
    return tags[:5]


def alias_where(columns: list[str], aliases: list[str]) -> tuple[str, list[str]]:
    parts = []
    params: list[str] = []
    for alias in aliases:
        like = f"%{alias}%"
        for column in columns:
            parts.append(f"{column} LIKE ?")
            params.append(like)
    return "(" + " OR ".join(parts) + ")", params


def person_by_slug(slug: str) -> dict[str, object] | None:
    for person in PEOPLE:
        if person["slug"] == slug:
            return person
    return None


def topic_by_slug(slug: str) -> dict[str, object] | None:
    for topic in TOPICS:
        if topic["slug"] == slug:
            return topic
    return None


def year_from_row(row: sqlite3.Row) -> str:
    text = f"{row['date_guess'] or ''} {row['volume_id'] or ''} {row['doc_key'] or ''}"
    m = re.search(r"\b(19[4-5][0-9])\b", text)
    return m.group(1) if m else "未注明"


def rows_for_search(c: sqlite3.Connection, query: str, limit: int = 50) -> list[sqlite3.Row]:
    if not query.strip():
        return []
    base = """
        SELECT
            pages.id AS page_id,
            documents.volume_id,
            documents.doc_id,
            documents.doc_key,
            documents.date_guess,
            documents.title,
            documents.matched_terms,
            dc.grade,
            dc.score,
            pages.page_label,
            pages.page_url,
            pages.text AS original_text,
            translations.text AS zh_text,
            translations.status AS zh_status
        FROM page_fts
        JOIN pages ON pages.id = page_fts.rowid
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        WHERE page_fts MATCH ?
        LIMIT ?
    """
    seen: set[int] = set()
    out: list[sqlite3.Row] = []
    try:
        for row in c.execute(base, (query, limit)):
            out.append(row)
            seen.add(row["page_id"])
    except sqlite3.OperationalError:
        like = f"%{query}%"
        fallback = """
            SELECT
                pages.id AS page_id,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.date_guess,
                documents.title,
                documents.matched_terms,
                dc.grade,
                dc.score,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                translations.text AS zh_text,
                translations.status AS zh_status
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            WHERE pages.text LIKE ? OR documents.title LIKE ? OR documents.matched_terms LIKE ?
            LIMIT ?
        """
        for row in c.execute(fallback, (like, like, like, limit)):
            out.append(row)
            seen.add(row["page_id"])

    if has_cjk(query):
        zh_sql = """
            SELECT
                pages.id AS page_id,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.date_guess,
                documents.title,
                documents.matched_terms,
                dc.grade,
                dc.score,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                translations.text AS zh_text,
                translations.status AS zh_status
            FROM translations
            JOIN pages ON pages.id = translations.page_id
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            WHERE translations.language='zh-CN' AND translations.text LIKE ?
            LIMIT ?
        """
        for row in c.execute(zh_sql, (f"%{query}%", limit)):
            if row["page_id"] not in seen:
                out.insert(0, row)
                seen.add(row["page_id"])
    return out[:limit]


def result_html(row: sqlite3.Row) -> str:
    page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
    href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
    terms = [t.strip() for t in (row["matched_terms"] or "").split(";") if t.strip()]
    tags = "".join(f'<span class="tag">{h(t)}</span>' for t in terms[:6])
    grade = grade_badge(row)
    zh = (
        f'<div class="zh">中文({h(row["zh_status"])}): {h(compact(row["zh_text"], 300))}</div>'
        if row["zh_text"]
        else '<div class="zh empty">中文: 尚未翻译</div>'
    )
    return f"""
<article class="result">
  <div>
    {title_block(row["title"], href)}
    <div class="meta">{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 330))}</div>
    {zh}
    <div class="tagline">{tags}</div>
  </div>
  <div class="cite"><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">原始来源</a><br>{h(page)}</div>
</article>"""


def default_home_focus() -> dict[str, object]:
    return {
        "title": "今日继续研究",
        "description": "优先从罗隆基、昆明暗杀、政协、马歇尔调处和核心文献入口继续推进。",
        "event_scope_slugs": ["lo-lung-chi", "kunming-assassinations", "pcc-1946", "marshall-mediation"],
        "event_grade": "核心文献",
        "event_limit": 8,
        "links": [
            {"label": "罗隆基 · 民盟", "href": "/events?person=lo-lung-chi&tag=民盟"},
            {"label": "南京核心", "href": "/places/南京?grade=core"},
            {"label": "民盟核心", "href": "/organizations/中国民主同盟?grade=core"},
            {"label": "罗隆基卡片", "href": "/events/cards?person=lo-lung-chi"},
            {"label": "核心校订", "href": "/tasks?queue=core"},
        ],
    }


def load_home_focus() -> dict[str, object]:
    config = default_home_focus()
    if HOME_FOCUS_PATH.exists():
        try:
            loaded = json.loads(HOME_FOCUS_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update(loaded)
        except (OSError, json.JSONDecodeError):
            pass
    links = config.get("links", [])
    if not isinstance(links, list):
        config["links"] = []
    scopes = config.get("event_scope_slugs", [])
    if not isinstance(scopes, list):
        config["event_scope_slugs"] = []
    return config


def home_focus_rows(c: sqlite3.Connection, config: dict[str, object]) -> list[sqlite3.Row]:
    scopes = [str(value) for value in config.get("event_scope_slugs", []) if str(value).strip()]
    if not scopes:
        return []
    grade = str(config.get("event_grade", "") or "")
    try:
        limit = int(config.get("event_limit", 8) or 8)
    except (TypeError, ValueError):
        limit = 8
    limit = max(1, min(limit, 30))

    params: list[object] = scopes[:]
    placeholders = ",".join("?" for _ in scopes)
    grade_clause = ""
    if grade:
        grade_clause = "AND COALESCE(dc.grade, '') = ?"
        params.append(grade)
    params.append(limit)
    return c.execute(
        f"""
        SELECT
            e.scope_name,
            e.event_date,
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
            documents.volume_id,
            documents.doc_id,
            documents.doc_key,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade
        FROM research_events e
        JOIN pages ON pages.id = e.page_id
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        WHERE e.scope_slug IN ({placeholders})
          {grade_clause}
        GROUP BY e.page_id
        ORDER BY e.importance DESC, documents.date_guess, pages.id
        LIMIT ?
        """,
        tuple(params),
    ).fetchall()


def focus_page(saved: bool = False, error: str = "") -> bytes:
    config = load_home_focus()
    config_text = json.dumps(config, ensure_ascii=False, indent=2)
    links = config.get("links", [])
    scopes = config.get("event_scope_slugs", [])
    saved_html = '<div class="notice" style="margin-bottom:14px;">首页继续研究清单已保存。</div>' if saved else ""
    error_html = f'<div class="notice" style="margin-bottom:14px;color:#8a2d1f;">{h(error)}</div>' if error else ""
    body = f"""
{saved_html}
{error_html}
<section class="doc-head">
  <div>
    <h1>首页继续研究清单</h1>
    <div class="meta">首页“今日继续研究”的入口和高价值事件范围来自 data/home_focus.json。保存后首页立即生效。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/">返回首页</a>
    <a class="button" href="/events">事件总览</a>
  </div>
</section>
<section class="result-list">
  <article class="result">
    <div>
      <h2>{h(config.get("title", "今日继续研究"))}</h2>
      <div class="meta">{h(config.get("description", ""))}</div>
      <div class="tagline">{''.join(f'<span class="tag">{h(scope)}</span>' for scope in scopes if isinstance(scope, str))}</div>
    </div>
    <div class="cite">事件上限 {h(config.get("event_limit", 8))}<br>{h(config.get("event_grade", ""))}</div>
  </article>
"""
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            label = str(link.get("label", "未命名入口"))
            href = str(link.get("href", "#"))
            body += f"""
  <article class="result">
    <div>
      <h2><a href="{h(href)}">{h(label)}</a></h2>
      <div class="meta">{h(href)}</div>
    </div>
    <div class="cite"><a href="{h(href)}">打开</a></div>
  </article>"""
    body += "</section>"
    body += f"""
<section style="margin-top:14px;">
  <form method="post" action="/focus">
    <article class="pane">
      <div class="pane-head"><span>配置清单 JSON</span><span>data/home_focus.json</span></div>
      <textarea class="review-text" name="config_text" style="min-height:520px;">{h(config_text)}</textarea>
      <div class="formbar">
        <button type="submit">保存清单</button>
      </div>
    </article>
  </form>
</section>
"""
    return layout("首页继续研究清单", body)


def dashboard() -> bytes:
    with conn() as c:
        docs_count = c.execute("SELECT count(*) FROM documents").fetchone()[0]
        pages_count = c.execute("SELECT count(*) FROM pages").fetchone()[0]
        translations_count = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN'").fetchone()[0]
        events_count = c.execute("SELECT count(*) FROM research_events").fetchone()[0]
        place_events = c.execute("SELECT count(*) FROM research_events WHERE COALESCE(places, '')<>''").fetchone()[0]
        org_events = c.execute("SELECT count(*) FROM research_events WHERE COALESCE(organizations, '')<>''").fetchone()[0]
        grades = {row[0]: row[1] for row in c.execute("SELECT grade, count(*) FROM document_classifications GROUP BY grade")}
        try:
            quality_rows = c.execute(
                """
                SELECT
                    count(*) AS issue_count,
                    count(DISTINCT page_id) AS issue_pages,
                    sum(CASE WHEN severity >= 2 THEN 1 ELSE 0 END) AS high_issues,
                    count(DISTINCT CASE WHEN severity >= 2 THEN page_id END) AS high_pages,
                    sum(CASE WHEN severity >= 3 THEN 1 ELSE 0 END) AS severe_issues
                FROM translation_quality_issues
                """
            ).fetchone()
        except sqlite3.OperationalError:
            quality_rows = {"issue_count": 0, "issue_pages": 0, "high_issues": 0, "high_pages": 0, "severe_issues": 0}
        top_events = c.execute(
            """
            SELECT scope_type, scope_slug, scope_name, count(*) AS n, count(DISTINCT page_id) AS pages
            FROM research_events
            GROUP BY scope_type, scope_slug, scope_name
            ORDER BY n DESC
            LIMIT 8
            """
        ).fetchall()
        try:
            suggested_tasks = c.execute(
                """
                WITH issue_stats AS (
                    SELECT
                        page_id,
                        count(*) AS issue_count,
                        max(severity) AS max_severity,
                        group_concat(DISTINCT issue_type) AS issue_types,
                        group_concat(detail, '; ') AS details
                    FROM translation_quality_issues
                    GROUP BY page_id
                )
                SELECT
                    pages.id AS page_id,
                    pages.page_label,
                    pages.page_url,
                    pages.text AS original_text,
                    documents.volume_id,
                    documents.doc_id,
                    documents.doc_key,
                    documents.title,
                    documents.date_guess,
                    COALESCE(dc.grade, '') AS grade,
                    translations.text AS zh_text,
                    issue_stats.issue_count,
                    issue_stats.max_severity,
                    issue_stats.issue_types,
                    issue_stats.details,
                    (
                        issue_stats.max_severity * 100
                        + issue_stats.issue_count * 10
                        + CASE COALESCE(dc.grade, '')
                            WHEN '核心文献' THEN 80
                            WHEN '相关文献' THEN 45
                            WHEN '人物关联' THEN 25
                            ELSE 0
                          END
                        + CASE WHEN documents.matched_terms LIKE '%Lo Lung-chi%' OR translations.text LIKE '%罗隆基%' THEN 30 ELSE 0 END
                        + CASE WHEN documents.matched_terms LIKE '%Democratic League%' OR translations.text LIKE '%民盟%' THEN 20 ELSE 0 END
                    ) AS priority_score
                FROM issue_stats
                JOIN pages ON pages.id = issue_stats.page_id
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                ORDER BY priority_score DESC, documents.date_guess, pages.id
                LIMIT 10
                """
            ).fetchall()
        except sqlite3.OperationalError:
            suggested_tasks = []
    export_files = sorted((ROOT / "exports").glob("*.md")) if (ROOT / "exports").exists() else []
    recent_exports = sorted(export_files, key=lambda path: path.stat().st_mtime, reverse=True)[:8]

    body = f"""
<section class="doc-head">
  <div>
    <h1>研究进度仪表盘</h1>
    <div class="meta">汇总资料库规模、译文覆盖、事件索引、质量提示和最近导出卡片。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/tasks?queue=core">核心校订</a>
    <a class="button" href="/quality?severity=2">质量检查</a>
    <a class="button" href="/events">事件线索</a>
    <a class="button" href="/focus">首页清单</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{docs_count}</strong><span>文档</span></div>
  <div class="stat"><strong>{pages_count}</strong><span>页/片段</span></div>
  <div class="stat"><strong>{translations_count}</strong><span>中文译文</span></div>
  <div class="stat"><strong>{events_count}</strong><span>事件节点</span></div>
  <div class="stat"><strong>{place_events}</strong><span>带地点事件</span></div>
  <div class="stat"><strong>{org_events}</strong><span>带机构事件</span></div>
  <div class="stat"><strong>{quality_rows["high_pages"] or 0}</strong><span>高优先级质量页</span></div>
  <div class="stat"><strong>{len(export_files)}</strong><span>Markdown 导出</span></div>
</section>
<section class="result-list">
  <article class="result">
    <div>
      <h2>文档等级</h2>
      <div class="tagline">
        <span class="tag">核心文献 {h(grades.get("核心文献", 0))}</span>
        <span class="tag">相关文献 {h(grades.get("相关文献", 0))}</span>
        <span class="tag">人物关联 {h(grades.get("人物关联", 0))}</span>
        <span class="tag">背景材料 {h(grades.get("背景材料", 0))}</span>
      </div>
    </div>
    <div class="cite"><a href="/docs?grade=核心文献">核心文献</a><br><a href="/docs">全部文档</a></div>
  </article>
  <article class="result">
    <div>
      <h2>译文质量</h2>
      <div class="meta">{h(quality_rows["issue_count"] or 0)} 个提示 · {h(quality_rows["issue_pages"] or 0)} 个片段 · 高优先级 {h(quality_rows["high_pages"] or 0)} 页 · 严重 {h(quality_rows["severe_issues"] or 0)}</div>
    </div>
    <div class="cite"><a href="/quality">质量检查</a><br><a href="/tasks">校订任务</a></div>
  </article>
</section>
<h2 style="font-size:18px;margin:18px 0 8px;">今日建议校订</h2>
<section class="result-list">
"""
    if suggested_tasks:
        for index, row in enumerate(suggested_tasks, start=1):
            page = source_page_label(row)
            doc_href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
            issue_tags = "".join(
                f'<span class="issue{" high" if (row["max_severity"] or 0) >= 3 else ""}">{h(issue_label(issue))}</span>'
                for issue in (row["issue_types"] or "").split(",")
                if issue
            )
            body += f"""
  <article class="result">
    <div>
      {title_block(row["title"], f"/review/{row['page_id']}")}
      <div class="meta">#{index} · 优先级 {h(row["priority_score"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
      <div class="zh">{h(compact(row["zh_text"], 260))}</div>
      <div class="tagline">{issue_tags}<span class="tag">{h(row["issue_count"])} 个提示</span></div>
    </div>
    <div class="cite"><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="/cite/{h(row["page_id"])}">摘录卡片</a></div>
  </article>"""
    else:
        body += '<div class="notice">当前没有建议校订任务。</div>'
    body += """
</section>
<h2 style="font-size:18px;margin:18px 0 8px;">事件范围</h2>
<section class="result-list">
"""
    for row in top_events:
        key = "topic" if row["scope_type"] == "topic" else "person"
        href = f"/events?{key}={quote(row['scope_slug'])}"
        body += f"""
  <article class="result">
    <div>
      <h2><a href="{h(href)}">{h(row["scope_name"])}</a></h2>
      <div class="meta">{row["n"]} 个事件节点 · {row["pages"]} 个资料片段</div>
    </div>
    <div class="cite"><a href="{h(href)}">查看事件</a></div>
  </article>"""
    body += "</section>"

    body += '<h2 style="font-size:18px;margin:18px 0 8px;">最近导出</h2><section class="result-list">'
    if recent_exports:
        for path in recent_exports:
            body += f"""
  <article class="result">
    <div>
      <h2>{h(path.name)}</h2>
      <div class="meta">{h(str(path.relative_to(ROOT)))} · {path.stat().st_size // 1024} KB</div>
    </div>
    <div class="cite">Markdown</div>
  </article>"""
    else:
        body += '<div class="notice">暂无导出文件。</div>'
    body += "</section>"
    return layout("研究进度仪表盘", body)


def save_home_focus(form: dict[str, list[str]]) -> tuple[bool, str]:
    raw = form.get("config_text", [""])[0]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        return False, f"JSON 格式有误：第 {exc.lineno} 行第 {exc.colno} 列。"
    if not isinstance(parsed, dict):
        return False, "配置必须是一个 JSON 对象。"
    if "links" in parsed and not isinstance(parsed["links"], list):
        return False, "links 必须是数组。"
    for index, link in enumerate(parsed.get("links", []), start=1):
        if not isinstance(link, dict):
            return False, f"第 {index} 个入口必须是对象。"
        if not str(link.get("label", "")).strip():
            return False, f"第 {index} 个入口缺少 label。"
        if not str(link.get("href", "")).strip():
            return False, f"第 {index} 个入口缺少 href。"
    if "event_scope_slugs" in parsed and not isinstance(parsed["event_scope_slugs"], list):
        return False, "event_scope_slugs 必须是数组。"
    for index, scope in enumerate(parsed.get("event_scope_slugs", []), start=1):
        if not isinstance(scope, str) or not scope.strip():
            return False, f"第 {index} 个事件范围必须是非空文字。"
    if "event_limit" in parsed:
        try:
            limit = int(parsed["event_limit"])
        except (TypeError, ValueError):
            return False, "event_limit 必须是数字。"
        if limit < 1 or limit > 30:
            return False, "event_limit 必须在 1 到 30 之间。"
    HOME_FOCUS_PATH.write_text(json.dumps(parsed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True, ""


def home() -> bytes:
    focus_config = load_home_focus()
    with conn() as c:
        try:
            focus_rows = home_focus_rows(c, focus_config)
        except sqlite3.OperationalError:
            focus_rows = []
        latest = c.execute(
            """
            SELECT
                pages.id AS page_id,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.date_guess,
                documents.title,
                documents.matched_terms,
                dc.grade,
                dc.score,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                translations.text AS zh_text,
                translations.status AS zh_status
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            ORDER BY documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
            LIMIT 12
            """
        ).fetchall()
        body = stats_html(c)
        focus_links = focus_config.get("links", [])
        focus_buttons = ""
        if isinstance(focus_links, list):
            for link in focus_links:
                if isinstance(link, dict):
                    focus_buttons += f'<a class="button" href="{h(link.get("href", "#"))}">{h(link.get("label", "入口"))}</a>'
        body += f"""
<section class="doc-head">
  <div>
    <h1>{h(focus_config.get("title", "今日继续研究"))}</h1>
    <div class="meta">{h(focus_config.get("description", ""))}</div>
  </div>
  <div class="doc-tools">
    {focus_buttons}
    <a class="button" href="/focus">管理清单</a>
  </div>
</section>
"""
        if focus_rows:
            body += '<h2 style="font-size:18px;margin:18px 0 8px;">高价值事件</h2><section class="result-list">'
            for row in focus_rows:
                page = source_page_label(row)
                doc_href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
                chips = "".join(
                    f'<span class="tag">{h(term)}</span>'
                    for term in split_terms(row["actors"]) + split_terms(row["tags"]) + split_terms(row["places"]) + split_terms(row["organizations"])
                )
                body += f"""
<article class="result">
  <div>
    <h2><a href="{h(doc_href)}">{h(row["event_title"])}</a></h2>
    <div class="meta">{h(row["event_date"] or row["date_guess"])} · {h(row["scope_name"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(page)} {grade_badge(row)}</div>
    <div class="zh">{h(compact(row["event_summary"], 300))}</div>
    <div class="tagline">{chips}<span class="tag">重要度 {h(row["importance"])}</span></div>
  </div>
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">FRUS</a></div>
</article>"""
            body += "</section>"
        body += '<h2 style="font-size:18px;margin:18px 0 8px;">资料入口</h2>'
        body += '<section class="result-list">'
        body += "".join(result_html(row) for row in latest)
        body += "</section>"
    return layout("民盟历史文献研究库", body)


def search(query: str) -> bytes:
    with conn() as c:
        rows = rows_for_search(c, query)
        body = stats_html(c)
        body += f'<h1 style="font-size:20px;margin:0 0 12px;">搜索：{h(query)}</h1>'
        if rows:
            body += '<section class="result-list">' + "".join(result_html(row) for row in rows) + "</section>"
        else:
            body += '<div class="notice">没有找到结果。</div>'
    return layout(f"搜索 {query}", body, query)


def doc_page(doc_key: str, page_id: str | None = None) -> bytes:
    with conn() as c:
        doc = c.execute(
            """
            SELECT documents.*, dc.grade, dc.score, dc.reason, dc.needs_review
            FROM documents
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            WHERE documents.doc_key=?
            """,
            (doc_key,),
        ).fetchone()
        if not doc:
            return layout("未找到文档", '<div class="notice">未找到文档。</div>')
        rows = c.execute(
            """
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                translations.text AS zh_text,
                translations.status AS zh_status
            FROM pages
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            WHERE pages.document_id=?
            ORDER BY pages.id
            """,
            (doc["id"],),
        ).fetchall()

    source_link = h(doc["url"] or "")
    body = f"""
<section class="doc-head">
  <div>
    {title_block(doc["title"], None, "h1")}
    <div class="meta">{h(doc["volume_id"])}/{h(doc["doc_id"])} · {h(doc["date_guess"])} · {h(doc["matched_terms"])} {grade_badge(doc)}</div>
    <div class="meta">{h(doc["reason"] or "")}</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="{source_link}" target="_blank" rel="noreferrer">原始来源</a>
    <a class="button" href="/search?q={quote(doc["matched_terms"] or doc["title"])}">相关搜索</a>
  </div>
</section>
<section class="reader">"""
    for row in rows:
        page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
        selected = " id=\"selected\"" if page_id and str(row["page_id"]) == str(page_id) else ""
        zh = row["zh_text"] or "尚未翻译"
        zh_class = "" if row["zh_text"] else " empty"
        status = row["zh_status"] or "needs-translation"
        body += f"""
  <div class="segment">
    <article class="pane"{selected}>
      <div class="pane-head"><span>原文 · {h(page)}</span><span><a href="/cite/{h(row["page_id"])}">摘录卡片</a> · <a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">引用</a></span></div>
      <div class="pane-body">{h(row["original_text"])}</div>
    </article>
    <article class="pane">
      <div class="pane-head"><span>中文 · {h(status)}</span><a href="/review/{h(row["page_id"])}">校订</a></div>
      <div class="pane-body{zh_class}">{h(zh)}</div>
    </article>
  </div>"""
    body += "</section>"
    if page_id:
        body += "<script>document.getElementById('selected')?.scrollIntoView({block:'center'});</script>"
    else:
        body += "<script>window.scrollTo({top: 0});</script>"
    return layout(doc["title"], body)


def docs(active_grade: str = "", active_translation: str = "") -> bytes:
    with conn() as c:
        where_parts = []
        params: list[str] = []
        if active_grade:
            where_parts.append("dc.grade = ?")
            params.append(active_grade)
        if active_translation == "translated":
            where_parts.append("translation_stats.translated_pages > 0")
        elif active_translation == "missing":
            where_parts.append("(translation_stats.translated_pages IS NULL OR translation_stats.translated_pages < translation_stats.total_pages)")
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        rows = c.execute(
            f"""
            SELECT
                documents.*,
                dc.grade,
                dc.score,
                dc.reason,
                translation_stats.total_pages AS page_count,
                COALESCE(translation_stats.translated_pages, 0) AS translated_pages
            FROM documents
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            JOIN (
                SELECT
                    pages.document_id,
                    count(pages.id) AS total_pages,
                    sum(CASE WHEN translations.id IS NULL THEN 0 ELSE 1 END) AS translated_pages
                FROM pages
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                GROUP BY pages.document_id
            ) translation_stats ON translation_stats.document_id = documents.id
            {where}
            ORDER BY documents.volume_id, CAST(documents.doc_number AS INTEGER)
            """,
            tuple(params),
        ).fetchall()
    body = grade_filters(active_grade, active_translation)
    body += '<section class="result-list">'
    for row in rows:
        page = f"{row['translated_pages']}/{row['page_count']} 已译"
        body += f"""
<article class="result">
  <div>
    {title_block(row["title"], f"/doc/{quote(row['doc_key'])}")}
    <div class="meta">{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(row["hit_type"])} {grade_badge(row)}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(t.strip())}</span>' for t in (row["matched_terms"] or "").split(";") if t.strip())}</div>
  </div>
  <div class="cite">{h(page)}</div>
</article>"""
    body += "</section>"
    return layout("全部文档", body)


def quality(active_severity: str = "", active_issue: str = "") -> bytes:
    with conn() as c:
        where_parts = []
        params: list[str] = []
        if active_severity:
            where_parts.append("q.severity = ?")
            params.append(active_severity)
        if active_issue:
            where_parts.append("q.issue_type = ?")
            params.append(active_issue)
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        rows = c.execute(
            f"""
            SELECT
                q.id AS issue_id,
                q.page_id,
                q.issue_type,
                q.severity,
                q.detail,
                q.snippet,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.date_guess,
                documents.title,
                pages.page_label,
                pages.page_url,
                COALESCE(dc.grade, '') AS grade
            FROM translation_quality_issues q
            JOIN pages ON pages.id = q.page_id
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            {where}
            ORDER BY q.severity DESC,
                CASE COALESCE(dc.grade, '')
                    WHEN '核心文献' THEN 1
                    WHEN '相关文献' THEN 2
                    WHEN '人物关联' THEN 3
                    WHEN '背景材料' THEN 4
                    ELSE 5
                END,
                documents.date_guess,
                q.page_id,
                q.issue_type
            LIMIT 250
            """,
            tuple(params),
        ).fetchall()
        totals = c.execute(
            """
            SELECT issue_type, severity, count(*) AS n
            FROM translation_quality_issues
            GROUP BY issue_type, severity
            ORDER BY severity DESC, n DESC
            """
        ).fetchall()
        distinct_pages = c.execute("SELECT count(DISTINCT page_id) FROM translation_quality_issues").fetchone()[0]
        high_pages = c.execute("SELECT count(DISTINCT page_id) FROM translation_quality_issues WHERE severity >= 2").fetchone()[0]

    body = f"""
<section class="doc-head">
  <div>
    <h1>译文质量检查</h1>
    <div class="meta">有提示的片段 {distinct_pages} 个；高优先级片段 {high_pages} 个。列表只显示前 250 条，优先处理严重度高、核心文献和术语问题。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/docs">返回文档</a>
  </div>
</section>
"""
    body += quality_filters(active_severity, active_issue)
    if totals:
        body += '<section class="stats">'
        for row in totals[:6]:
            body += f'<div class="stat"><strong>{row["n"]}</strong><span>{h(issue_label(row["issue_type"]))} · 严重度 {h(row["severity"])}</span></div>'
        body += "</section>"
    if not rows:
        body += '<div class="notice">没有符合筛选条件的质量提示。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows:
            page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
            doc_href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
            review_href = f"/review/{row['page_id']}"
            issue_class = "issue high" if row["severity"] >= 3 else "issue"
            body += f"""
<article class="result">
  <div>
    {title_block(row["title"], review_href)}
    <div class="meta">{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
    <div class="tagline">
      <span class="{issue_class}">{h(issue_label(row["issue_type"]))}</span>
      <span class="tag">严重度 {h(row["severity"])}</span>
    </div>
    <div class="snippet">{h(row["detail"])}</div>
    <div class="zh">{h(row["snippet"])}</div>
  </div>
  <div class="cite"><a href="{h(review_href)}">打开校订</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
        body += "</section>"
    return layout("译文质量检查", body)


def tasks(active_queue: str = "") -> bytes:
    queue_where = ""
    params: list[str] = []
    if active_queue == "core":
        queue_where = "WHERE COALESCE(dc.grade, '') = '核心文献'"
    elif active_queue == "people":
        queue_where = """
            WHERE documents.matched_terms LIKE '%Lo Lung%'
               OR documents.matched_terms LIKE '%Chang Lan%'
               OR documents.matched_terms LIKE '%Liang Shu%'
               OR documents.matched_terms LIKE '%Huang Yen%'
               OR documents.matched_terms LIKE '%Chang Po%'
               OR documents.matched_terms LIKE '%Shih Liang%'
        """
    elif active_queue == "topics":
        queue_where = """
            WHERE pages.text LIKE '%Kunming%'
               OR pages.text LIKE '%assassin%'
               OR pages.text LIKE '%Political Consultative%'
               OR pages.text LIKE '%PCC%'
               OR pages.text LIKE '%Marshall%'
               OR pages.text LIKE '%Peiping%'
               OR translations.text LIKE '%昆明%'
               OR translations.text LIKE '%暗杀%'
               OR translations.text LIKE '%政治协商%'
               OR translations.text LIKE '%马歇尔%'
               OR translations.text LIKE '%北平%'
        """
    elif active_queue == "terms":
        queue_where = "WHERE issue_stats.issue_types LIKE '%glossary_miss%'"
    elif active_queue == "english":
        queue_where = "WHERE issue_stats.issue_types LIKE '%english_residue%'"

    with conn() as c:
        rows = c.execute(
            f"""
            WITH issue_stats AS (
                SELECT
                    page_id,
                    max(severity) AS max_severity,
                    count(*) AS issue_count,
                    group_concat(DISTINCT issue_type) AS issue_types,
                    group_concat(detail, '；') AS details
                FROM translation_quality_issues
                GROUP BY page_id
            )
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.title,
                documents.date_guess,
                documents.matched_terms,
                COALESCE(dc.grade, '') AS grade,
                translations.text AS zh_text,
                translations.status AS zh_status,
                issue_stats.max_severity,
                issue_stats.issue_count,
                issue_stats.issue_types,
                issue_stats.details,
                (
                    issue_stats.max_severity * 100
                    + CASE COALESCE(dc.grade, '')
                        WHEN '核心文献' THEN 40
                        WHEN '相关文献' THEN 20
                        WHEN '人物关联' THEN 15
                        ELSE 0
                      END
                    + CASE WHEN documents.matched_terms LIKE '%Lo Lung%' THEN 20 ELSE 0 END
                    + CASE WHEN pages.text LIKE '%assassin%' OR translations.text LIKE '%暗杀%' THEN 20 ELSE 0 END
                    + CASE WHEN pages.text LIKE '%Political Consultative%' OR translations.text LIKE '%政治协商%' THEN 14 ELSE 0 END
                    + CASE WHEN pages.text LIKE '%Peiping%' OR translations.text LIKE '%北平%' THEN 10 ELSE 0 END
                    + issue_stats.issue_count
                ) AS priority_score
            FROM issue_stats
            JOIN pages ON pages.id = issue_stats.page_id
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            {queue_where}
            ORDER BY priority_score DESC, documents.date_guess, pages.id
            LIMIT 200
            """,
            tuple(params),
        ).fetchall()
        counts = c.execute(
            """
            SELECT
                count(DISTINCT q.page_id) AS all_tasks,
                count(DISTINCT CASE WHEN COALESCE(dc.grade, '') = '核心文献' THEN q.page_id END) AS core_tasks,
                count(DISTINCT CASE WHEN q.severity >= 2 THEN q.page_id END) AS high_tasks,
                count(DISTINCT CASE WHEN t.status = 'human-reviewed' THEN q.page_id END) AS reviewed_tasks
            FROM translation_quality_issues q
            JOIN pages p ON p.id = q.page_id
            JOIN documents d ON d.id = p.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = d.id
            LEFT JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
            """
        ).fetchone()

    body = f"""
<section class="doc-head">
  <div>
    <h1>校订任务队列</h1>
    <div class="meta">把质量提示合并为页片段任务，按核心文献、严重度、人物与专题线索自动排序。建议从前 20 条开始处理。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/quality">质量检查</a>
    <a class="button" href="/docs?grade={quote('核心文献')}">核心文献</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{counts["all_tasks"]}</strong><span>待处理任务片段</span></div>
  <div class="stat"><strong>{counts["high_tasks"]}</strong><span>高优先级任务</span></div>
  <div class="stat"><strong>{counts["core_tasks"]}</strong><span>核心文献任务</span></div>
  <div class="stat"><strong>{counts["reviewed_tasks"]}</strong><span>已校订但仍有提示</span></div>
</section>
"""
    body += task_filters(active_queue)
    if not rows:
        body += '<div class="notice">当前队列没有任务。</div>'
    else:
        body += '<section class="result-list">'
        for index, row in enumerate(rows, start=1):
            page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
            review_href = f"/review/{row['page_id']}"
            doc_href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
            issue_tags = "".join(
                f'<span class="issue{" high" if row["max_severity"] >= 3 else ""}">{h(issue_label(issue))}</span>'
                for issue in (row["issue_types"] or "").split(",")
                if issue
            )
            topics = "".join(f'<span class="tag">{h(tag)}</span>' for tag in topic_tags(row))
            body += f"""
<article class="result">
  <div>
    {title_block(row["title"], review_href)}
    <div class="meta">#{index} · 优先级 {h(row["priority_score"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
    <div class="tagline">{issue_tags}<span class="tag">{h(row["issue_count"])} 个提示</span>{topics}</div>
    <div class="snippet">{h(compact(row["details"], 260))}</div>
    <div class="zh">{h(compact(row["zh_text"], 260))}</div>
  </div>
  <div class="cite"><a href="{h(review_href)}">校订</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
        body += "</section>"
    return layout("校订任务队列", body)


def people() -> bytes:
    cards = []
    with conn() as c:
        for person in PEOPLE:
            where, params = alias_where(
                ["documents.matched_terms", "documents.title", "pages.text", "translations.text"],
                person["aliases"],
            )
            row = c.execute(
                f"""
                SELECT
                    count(DISTINCT documents.id) AS doc_count,
                    count(DISTINCT pages.id) AS page_count,
                    min(documents.date_guess) AS first_date,
                    max(documents.date_guess) AS last_date,
                    sum(CASE WHEN dc.grade = '核心文献' THEN 1 ELSE 0 END) AS core_hits
                FROM pages
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                WHERE {where}
                """,
                tuple(params),
            ).fetchone()
            cards.append((person, row))

    body = """
<section class="doc-head">
  <div>
    <h1>人物索引</h1>
    <div class="meta">按民盟人物、第三方面人物和关键谈判人物汇总 FRUS 命中文档。每个人物页都保留原文、译文、页码和来源链接。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/tasks?queue=people">人物校订任务</a>
  </div>
</section>
<section class="result-list">
"""
    for person, row in sorted(cards, key=lambda item: (item[1]["doc_count"] or 0, item[1]["page_count"] or 0), reverse=True):
        body += f"""
<article class="result">
  <div>
    <h2><a href="/people/{h(person["slug"])}">{h(person["name"])}</a></h2>
    <div class="title-en">{h(' / '.join(person["aliases"][:4]))}</div>
    <div class="meta">{row["doc_count"] or 0} 篇文档 · {row["page_count"] or 0} 个片段 · 核心命中 {row["core_hits"] or 0}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(alias)}</span>' for alias in person["aliases"][:5])}</div>
  </div>
  <div class="cite"><a href="/people/{h(person["slug"])}">查看人物页</a><br><a href="/search?q={quote(person["name"])}">中文搜索</a></div>
</article>"""
    body += "</section>"
    return layout("人物索引", body)


def person_page(slug: str) -> bytes:
    person = person_by_slug(slug)
    if not person:
        return layout("未找到人物", '<div class="notice">未找到人物。</div>')
    aliases = person["aliases"]
    with conn() as c:
        where, params = alias_where(
            ["documents.matched_terms", "documents.title", "pages.text", "translations.text"],
            aliases,
        )
        rows = c.execute(
            f"""
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.title,
                documents.date_guess,
                documents.matched_terms,
                COALESCE(dc.grade, '') AS grade,
                translations.text AS zh_text,
                translations.status AS zh_status,
                count(q.id) AS issue_count,
                max(q.severity) AS max_severity
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translation_quality_issues q ON q.page_id = pages.id
            WHERE {where}
            GROUP BY pages.id
            ORDER BY documents.date_guess, documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
            LIMIT 300
            """,
            tuple(params),
        ).fetchall()
        doc_count = len({row["doc_key"] for row in rows})
        core_count = sum(1 for row in rows if row["grade"] == "核心文献")
        issue_count = sum(1 for row in rows if row["issue_count"])

    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(person["name"])}</h1>
    <div class="meta">{doc_count} 篇文档 · {len(rows)} 个片段 · 核心片段 {core_count} · 有质量提示片段 {issue_count}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(alias)}</span>' for alias in aliases)}</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/people">人物索引</a>
    <a class="button" href="/search?q={quote(person["name"])}">搜索此人</a>
    <a class="button" href="/timeline?person={h(person["slug"])}">人物年表</a>
    <a class="button" href="/events?person={h(person["slug"])}">事件线索</a>
  </div>
</section>
"""
    if not rows:
        body += '<div class="notice">暂无匹配材料。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows:
            page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
            href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
            tags = "".join(f'<span class="tag">{h(tag)}</span>' for tag in topic_tags(row))
            issue = ""
            if row["issue_count"]:
                issue = f'<span class="issue{" high" if (row["max_severity"] or 0) >= 3 else ""}">{row["issue_count"]} 个校订提示</span>'
            body += f"""
<article class="result">
  <div>
    {title_block(row["title"], href)}
    <div class="meta">{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 260))}</div>
    <div class="zh">中文: {h(compact(row["zh_text"], 260))}</div>
    <div class="tagline">{tags}{issue}</div>
  </div>
  <div class="cite"><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
        body += "</section>"
    return layout(str(person["name"]), body)


def topics() -> bytes:
    cards = []
    with conn() as c:
        for topic in TOPICS:
            where, params = alias_where(
                ["documents.title", "documents.matched_terms", "pages.text", "translations.text"],
                topic["terms"],
            )
            row = c.execute(
                f"""
                SELECT
                    count(DISTINCT documents.id) AS doc_count,
                    count(DISTINCT pages.id) AS page_count,
                    sum(CASE WHEN dc.grade = '核心文献' THEN 1 ELSE 0 END) AS core_hits,
                    count(DISTINCT q.page_id) AS issue_pages
                FROM pages
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                LEFT JOIN translation_quality_issues q ON q.page_id = pages.id
                WHERE {where}
                """,
                tuple(params),
            ).fetchone()
            cards.append((topic, row))
    body = """
<section class="doc-head">
  <div>
    <h1>核心主题专题</h1>
    <div class="meta">把 FRUS 民盟材料按研究问题聚合，便于从事件和政治过程进入原文。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/tasks?queue=topics">专题校订任务</a>
  </div>
</section>
<section class="result-list">
"""
    for topic, row in sorted(cards, key=lambda item: (item[1]["core_hits"] or 0, item[1]["doc_count"] or 0), reverse=True):
        body += f"""
<article class="result">
  <div>
    <h2><a href="/topics/{h(topic["slug"])}">{h(topic["name"])}</a></h2>
    <div class="meta">{h(topic["brief"])}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(term)}</span>' for term in topic["terms"][:6])}</div>
  </div>
  <div class="cite">{row["doc_count"] or 0} 篇文档<br>{row["page_count"] or 0} 个片段<br>{row["issue_pages"] or 0} 个待校订</div>
</article>"""
    body += "</section>"
    return layout("核心主题专题", body)


def topic_page(slug: str) -> bytes:
    topic = topic_by_slug(slug)
    if not topic:
        return layout("未找到专题", '<div class="notice">未找到专题。</div>')
    with conn() as c:
        where, params = alias_where(
            ["documents.title", "documents.matched_terms", "pages.text", "translations.text"],
            topic["terms"],
        )
        rows = c.execute(
            f"""
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.title,
                documents.date_guess,
                documents.matched_terms,
                COALESCE(dc.grade, '') AS grade,
                translations.text AS zh_text,
                translations.status AS zh_status,
                count(q.id) AS issue_count,
                max(q.severity) AS max_severity
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translation_quality_issues q ON q.page_id = pages.id
            WHERE {where}
            GROUP BY pages.id
            ORDER BY
                CASE COALESCE(dc.grade, '')
                    WHEN '核心文献' THEN 1
                    WHEN '相关文献' THEN 2
                    WHEN '人物关联' THEN 3
                    ELSE 4
                END,
                documents.date_guess,
                documents.volume_id,
                CAST(documents.doc_number AS INTEGER),
                pages.id
            LIMIT 300
            """,
            tuple(params),
        ).fetchall()
    doc_count = len({row["doc_key"] for row in rows})
    core_count = sum(1 for row in rows if row["grade"] == "核心文献")
    issue_count = sum(1 for row in rows if row["issue_count"])
    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(topic["name"])}</h1>
    <div class="meta">{h(topic["brief"])}</div>
    <div class="meta">{doc_count} 篇文档 · {len(rows)} 个片段 · 核心片段 {core_count} · 待校订片段 {issue_count}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(term)}</span>' for term in topic["terms"])}</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/topics">专题列表</a>
    <a class="button" href="/tasks?queue=topics">专题校订任务</a>
    <a class="button" href="/timeline?topic={h(topic["slug"])}">专题年表</a>
    <a class="button" href="/events?topic={h(topic["slug"])}">事件线索</a>
  </div>
</section>
"""
    if not rows:
        body += '<div class="notice">暂无匹配材料。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows:
            page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
            href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
            issue = ""
            if row["issue_count"]:
                issue = f'<span class="issue{" high" if (row["max_severity"] or 0) >= 3 else ""}">{row["issue_count"]} 个校订提示</span>'
            body += f"""
<article class="result">
  <div>
    {title_block(row["title"], href)}
    <div class="meta">{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 280))}</div>
    <div class="zh">中文: {h(compact(row["zh_text"], 280))}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(tag)}</span>' for tag in topic_tags(row))}{issue}</div>
  </div>
  <div class="cite"><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
        body += "</section>"
    return layout(str(topic["name"]), body)


def upsert_translation(c: sqlite3.Connection, page_id: int, text: str, status: str, translator: str = "human-review") -> None:
    existing = c.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (page_id,),
    ).fetchone()
    if existing:
        translation_id = existing["id"]
        c.execute(
            """
            UPDATE translations
            SET text=?, status=?, translator=?
            WHERE id=?
            """,
            (text, status, translator, translation_id),
        )
        c.execute("DELETE FROM translation_fts WHERE rowid=?", (translation_id,))
    else:
        cur = c.execute(
            """
            INSERT INTO translations(page_id, language, translator, status, text)
            VALUES (?, 'zh-CN', ?, ?, ?)
            """,
            (page_id, translator, status, text),
        )
        translation_id = cur.lastrowid

    page = c.execute(
        """
        SELECT pages.page_label, documents.title
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        WHERE pages.id=?
        """,
        (page_id,),
    ).fetchone()
    c.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, ?, ?, ?, ?)",
        (translation_id, "zh-CN", page["title"], page["page_label"] or "doc-level", text),
    )


def save_review(page_id: int, form: dict[str, list[str]]) -> None:
    text = (form.get("zh_text", [""])[0] or "").strip()
    status = (form.get("status", ["human-reviewed"])[0] or "human-reviewed").strip()
    allowed = {
        "machine-draft-local-review-needed",
        "machine-draft-review-needed",
        "batch-qc-passed",
        "human-reviewed",
        "needs-revision",
    }
    if status not in allowed:
        status = "human-reviewed"
    with conn() as c:
        upsert_translation(c, page_id, text, status)
        c.execute("DELETE FROM translation_quality_issues WHERE page_id=?", (page_id,))
        c.commit()


def suggested_review_tasks(c: sqlite3.Connection, limit: int = 10, exclude_page_id: int = 0) -> list[sqlite3.Row]:
    exclude_clause = "WHERE issue_stats.page_id <> ?" if exclude_page_id else ""
    params: list[object] = [exclude_page_id] if exclude_page_id else []
    params.append(limit)
    return c.execute(
        f"""
        WITH issue_stats AS (
            SELECT
                page_id,
                count(*) AS issue_count,
                max(severity) AS max_severity,
                group_concat(DISTINCT issue_type) AS issue_types,
                group_concat(detail, '; ') AS details
            FROM translation_quality_issues
            GROUP BY page_id
        )
        SELECT
            pages.id AS page_id,
            pages.page_label,
            pages.page_url,
            pages.text AS original_text,
            documents.volume_id,
            documents.doc_id,
            documents.doc_key,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade,
            translations.text AS zh_text,
            issue_stats.issue_count,
            issue_stats.max_severity,
            issue_stats.issue_types,
            issue_stats.details,
            (
                issue_stats.max_severity * 100
                + issue_stats.issue_count * 10
                + CASE COALESCE(dc.grade, '')
                    WHEN '核心文献' THEN 80
                    WHEN '相关文献' THEN 45
                    WHEN '人物关联' THEN 25
                    ELSE 0
                  END
                + CASE WHEN documents.matched_terms LIKE '%Lo Lung-chi%' OR translations.text LIKE '%罗隆基%' THEN 30 ELSE 0 END
                + CASE WHEN documents.matched_terms LIKE '%Democratic League%' OR translations.text LIKE '%民盟%' THEN 20 ELSE 0 END
            ) AS priority_score
        FROM issue_stats
        JOIN pages ON pages.id = issue_stats.page_id
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        {exclude_clause}
        ORDER BY priority_score DESC, documents.date_guess, pages.id
        LIMIT ?
        """,
        tuple(params),
    ).fetchall()


def next_review_page_id(current_page_id: int) -> int:
    try:
        with conn() as c:
            rows = suggested_review_tasks(c, 1, current_page_id)
    except sqlite3.OperationalError:
        return 0
    return int(rows[0]["page_id"]) if rows else 0


def review_page(page_id: int, saved: bool = False) -> bytes:
    with conn() as c:
        row = c.execute(
            """
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                documents.doc_key,
                documents.volume_id,
                documents.doc_id,
                documents.title,
                documents.date_guess,
                COALESCE(dc.grade, '') AS grade,
                translations.text AS zh_text,
                translations.status AS zh_status
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            WHERE pages.id=?
            """,
            (page_id,),
        ).fetchone()
        issues = c.execute(
            """
            SELECT issue_type, severity, detail, snippet
            FROM translation_quality_issues
            WHERE page_id=?
            ORDER BY severity DESC, issue_type
            """,
            (page_id,),
        ).fetchall()
        try:
            next_task = suggested_review_tasks(c, 1, page_id)
        except sqlite3.OperationalError:
            next_task = []
    if not row:
        return layout("未找到片段", '<div class="notice">未找到片段。</div>')

    next_id = int(next_task[0]["page_id"]) if next_task else 0
    page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
    status = row["zh_status"] or "human-reviewed"
    issue_html = ""
    if issues:
        issue_html = '<div class="tagline">' + "".join(
            f'<span class="issue{" high" if issue["severity"] >= 3 else ""}">{h(issue_label(issue["issue_type"]))} · {h(issue["detail"])}</span>'
            for issue in issues
        ) + "</div>"
    saved_html = '<div class="notice" style="margin-bottom:14px;">已保存校订，并已更新中文全文检索。</div>' if saved else ""
    next_button = '<button type="submit" name="after_save" value="next">保存并进入下一条</button>' if next_id else ""
    next_link = f'<a class="button" href="/review/{h(next_id)}">下一条校订</a>' if next_id else ""
    status_options = [
        ("human-reviewed", "已校订"),
        ("batch-qc-passed", "批量质检通过"),
        ("needs-revision", "需再修订"),
        ("machine-draft-local-review-needed", "本地机器初稿"),
        ("machine-draft-review-needed", "机器初稿"),
    ]
    options = "".join(
        f'<option value="{h(value)}"{" selected" if value == status else ""}>{h(label)}</option>'
        for value, label in status_options
    )
    body = f"""
{saved_html}
<section class="doc-head">
  <div>
    {title_block(row["title"], None, "h1")}
    <div class="meta">{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
    {issue_html}
  </div>
  <div class="doc-tools">
    <a class="button" href="/doc/{quote(row["doc_key"])}?page_id={h(row["page_id"])}">并排阅读</a>
    <a class="button" href="/cite/{h(row["page_id"])}">摘录卡片</a>
    {next_link}
    <a class="button" href="{h(row["page_url"])}" target="_blank" rel="noreferrer">原始来源</a>
    <a class="button" href="/quality">质量检查</a>
  </div>
</section>
<section class="reader">
  <article class="pane">
    <div class="pane-head"><span>原文 · {h(page)}</span><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">引用</a></div>
    <div class="pane-body">{h(row["original_text"])}</div>
  </article>
  <article class="pane">
    <form method="post" action="/review/{h(row["page_id"])}">
      <div class="pane-head"><span>中文校订</span><span>{h(status)}</span></div>
      <textarea class="review-text" name="zh_text">{h(row["zh_text"] or "")}</textarea>
      <div class="formbar">
        <label>状态 <select name="status">{options}</select></label>
        <button type="submit" name="after_save" value="stay">保存校订</button>
        {next_button}
      </div>
    </form>
  </article>
</section>
"""
    return layout("校订译文", body)


def citation_page(page_id: int) -> bytes:
    with conn() as c:
        row = c.execute(
            """
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                documents.doc_key,
                documents.volume_id,
                documents.doc_id,
                documents.volume_title,
                documents.title,
                documents.date_guess,
                documents.url AS doc_url,
                COALESCE(dc.grade, '') AS grade,
                translations.text AS zh_text,
                translations.status AS zh_status
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            WHERE pages.id=?
            """,
            (page_id,),
        ).fetchone()
    if not row:
        return layout("未找到摘录", '<div class="notice">未找到摘录。</div>')
    page = source_page_label(row)
    source_url = row["page_url"] or row["doc_url"] or ""
    citation = (
        f"短引文：{short_citation(row)}\n"
        f"参考文献：{bibliography_entry(row)}\n\n"
        f"题名：{translate_title(row['title'])}\n"
        f"英文题名：{row['title']}\n"
        f"卷册：{row['volume_id']} / {row['volume_title'] or ''}\n"
        f"日期：{row['date_guess'] or ''}\n"
        f"引用位置：{page}\n"
        f"FRUS 来源：{source_url}\n\n"
        f"原文摘录：\n{row['original_text']}\n\n"
        f"中文译文（{row['zh_status'] or '未标注'}）：\n{row['zh_text'] or ''}"
    )
    body = f"""
<section class="doc-head">
  <div>
    {title_block(row["title"], None, "h1")}
    <div class="meta">{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/doc/{quote(row["doc_key"])}?page_id={h(row["page_id"])}">并排阅读</a>
    <a class="button" href="/review/{h(row["page_id"])}">校订译文</a>
    <a class="button" href="{h(source_url)}" target="_blank" rel="noreferrer">FRUS 来源</a>
  </div>
</section>
<section class="reader">
  <article class="pane">
    <div class="pane-head"><span>原文摘录</span><span>{h(page)}</span></div>
    <div class="pane-body">{h(row["original_text"])}</div>
  </article>
  <article class="pane">
    <div class="pane-head"><span>中文译文 · {h(row["zh_status"] or "未标注")}</span><span>{h(page)}</span></div>
    <div class="pane-body">{h(row["zh_text"] or "")}</div>
  </article>
</section>
<section style="margin-top:14px;">
  <textarea class="copybox" readonly>{h(citation)}</textarea>
</section>
"""
    return layout("引用摘录卡片", body)


def timeline(topic_slug: str = "", person_slug: str = "") -> bytes:
    title = "FRUS 民盟材料年表"
    subtitle = "按年份排列文档片段，保留校订、摘录和 FRUS 来源入口。"
    where = ""
    params: list[str] = []
    filter_links = []
    if topic_slug:
        topic = topic_by_slug(topic_slug)
        if topic:
            title = f"{topic['name']}年表"
            subtitle = str(topic["brief"])
            where, params = alias_where(
                ["documents.title", "documents.matched_terms", "pages.text", "translations.text"],
                topic["terms"],
            )
            where = "WHERE " + where
    elif person_slug:
        person = person_by_slug(person_slug)
        if person:
            title = f"{person['name']}年表"
            subtitle = "按时间排列该人物在 FRUS 民盟材料中的出现。"
            where, params = alias_where(
                ["documents.matched_terms", "documents.title", "pages.text", "translations.text"],
                person["aliases"],
            )
            where = "WHERE " + where

    with conn() as c:
        rows = c.execute(
            f"""
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                documents.volume_id,
                documents.doc_id,
                documents.doc_key,
                documents.title,
                documents.date_guess,
                documents.matched_terms,
                COALESCE(dc.grade, '') AS grade,
                translations.text AS zh_text,
                translations.status AS zh_status,
                count(q.id) AS issue_count,
                max(q.severity) AS max_severity
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translation_quality_issues q ON q.page_id = pages.id
            {where}
            GROUP BY pages.id
            ORDER BY documents.date_guess, documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
            LIMIT 500
            """,
            tuple(params),
        ).fetchall()
    years: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        years.setdefault(year_from_row(row), []).append(row)

    filter_links.append('<a class="button" href="/timeline">全部年表</a>')
    filter_links.extend(f'<a class="button" href="/timeline?topic={h(topic["slug"])}">{h(topic["name"])}</a>' for topic in TOPICS[:5])
    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(title)}</h1>
    <div class="meta">{h(subtitle)}</div>
    <div class="meta">{len({row["doc_key"] for row in rows})} 篇文档 · {len(rows)} 个片段</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/topics">专题</a>
    <a class="button" href="/people">人物</a>
    <a class="button" href="/events">事件线索</a>
  </div>
</section>
<div class="filters">{''.join(filter_links)}</div>
"""
    if not rows:
        body += '<div class="notice">暂无匹配年表材料。</div>'
    else:
        for year in sorted(years.keys(), key=lambda y: (y == "未注明", y)):
            body += f'<h2 style="font-size:18px;margin:18px 0 8px;">{h(year)}</h2><section class="result-list">'
            for row in years[year]:
                page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
                href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
                issue = ""
                if row["issue_count"]:
                    issue = f'<span class="issue{" high" if (row["max_severity"] or 0) >= 3 else ""}">{row["issue_count"]} 个校订提示</span>'
                body += f"""
<article class="result">
  <div>
    {title_block(row["title"], href)}
    <div class="meta">{h(row["date_guess"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(page)} {grade_badge(row)}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 230))}</div>
    <div class="zh">中文: {h(compact(row["zh_text"], 230))}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(tag)}</span>' for tag in topic_tags(row))}{issue}</div>
  </div>
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">FRUS</a></div>
</article>"""
            body += "</section>"
    return layout(title, body)


def event_overview() -> bytes:
    try:
        with conn() as c:
            rows = c.execute(
                """
                SELECT scope_type, scope_slug, scope_name, count(*) AS event_count, count(DISTINCT page_id) AS page_count
                FROM research_events
                GROUP BY scope_type, scope_slug, scope_name
                ORDER BY scope_type DESC, event_count DESC, scope_name
                """
            ).fetchall()
    except sqlite3.OperationalError:
        return layout(
            "事件线索",
            '<div class="notice">事件线索数据还没有生成。请先运行事件年表生成脚本。</div>',
        )

    body = """
<section class="doc-head">
  <div>
    <h1>事件线索</h1>
    <div class="meta">把专题和人物命中的材料压缩成可浏览事件节点。每个节点都能回到原文、译文、摘录卡片和 FRUS 来源。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/timeline">文档年表</a>
    <a class="button" href="/topics">专题</a>
    <a class="button" href="/people">人物</a>
    <a class="button" href="/places">地点</a>
    <a class="button" href="/organizations">机构</a>
  </div>
</section>
"""
    if not rows:
        body += '<div class="notice">暂无事件线索。</div>'
        return layout("事件线索", body)

    labels = {"topic": "专题事件", "person": "人物事件"}
    for scope_type in ["topic", "person"]:
        group = [row for row in rows if row["scope_type"] == scope_type]
        if not group:
            continue
        body += f'<h2 style="font-size:18px;margin:18px 0 8px;">{h(labels[scope_type])}</h2><section class="result-list">'
        for row in group:
            query_key = "topic" if scope_type == "topic" else "person"
            href = f"/events?{query_key}={quote(row['scope_slug'])}"
            related_href = f"/timeline?{query_key}={quote(row['scope_slug'])}"
            body += f"""
<article class="result">
  <div>
    <h2><a href="{h(href)}">{h(row["scope_name"])}</a></h2>
    <div class="meta">{row["event_count"]} 个事件节点 · {row["page_count"]} 个资料片段</div>
  </div>
  <div class="cite"><a href="{h(href)}">查看事件</a><br><a href="{h(related_href)}">文档年表</a></div>
</article>"""
        body += "</section>"
    return layout("事件线索", body)


def fetch_event_rows(scope_type: str, scope_slug: str) -> list[sqlite3.Row]:
    with conn() as c:
        return c.execute(
            """
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
            WHERE e.scope_type=? AND e.scope_slug=?
            ORDER BY
                e.event_year,
                documents.date_guess,
                documents.volume_id,
                CAST(documents.doc_number AS INTEGER),
                pages.id,
                e.importance DESC
            """,
            (scope_type, scope_slug),
        ).fetchall()


def fetch_all_event_rows() -> list[sqlite3.Row]:
    with conn() as c:
        return c.execute(
            """
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
            ORDER BY
                e.event_year,
                documents.date_guess,
                documents.volume_id,
                CAST(documents.doc_number AS INTEGER),
                pages.id,
                e.importance DESC
            """
        ).fetchall()


def split_terms(value: str) -> list[str]:
    return [item.strip() for item in (value or "").split(";") if item.strip()]


def event_filter_href(scope_type: str, scope_slug: str, tag: str = "", actor: str = "", place: str = "", org: str = "") -> str:
    params = [f"{scope_type}={quote(scope_slug)}"]
    if tag:
        params.append(f"tag={quote(tag)}")
    if actor:
        params.append(f"actor={quote(actor)}")
    if place:
        params.append(f"place={quote(place)}")
    if org:
        params.append(f"org={quote(org)}")
    return "/events?" + "&".join(params)


def event_filter_bar(
    rows: list[sqlite3.Row],
    scope_type: str,
    scope_slug: str,
    active_tag: str = "",
    active_actor: str = "",
    active_place: str = "",
    active_org: str = "",
) -> str:
    tag_counts: dict[str, int] = {}
    actor_counts: dict[str, int] = {}
    place_counts: dict[str, int] = {}
    org_counts: dict[str, int] = {}
    for row in rows:
        for tag in split_terms(row["tags"]):
            tag_counts[tag] = tag_counts.get(tag, 0) + 1
        for actor in split_terms(row["actors"]):
            actor_counts[actor] = actor_counts.get(actor, 0) + 1
        for place in split_terms(row["places"]):
            place_counts[place] = place_counts.get(place, 0) + 1
        for org in split_terms(row["organizations"]):
            org_counts[org] = org_counts.get(org, 0) + 1

    parts = [f'<a class="button{" active" if not active_tag and not active_actor and not active_place and not active_org else ""}" href="{h(event_filter_href(scope_type, scope_slug))}">全部事件</a>']
    for tag, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:10]:
        cls = "button active" if tag == active_tag else "button"
        parts.append(f'<a class="{cls}" href="{h(event_filter_href(scope_type, scope_slug, tag=tag, actor=active_actor, place=active_place, org=active_org))}">{h(tag)} {count}</a>')

    actor_parts = []
    for actor, count in sorted(actor_counts.items(), key=lambda item: (-item[1], item[0]))[:10]:
        cls = "button active" if actor == active_actor else "button"
        actor_parts.append(f'<a class="{cls}" href="{h(event_filter_href(scope_type, scope_slug, tag=active_tag, actor=actor, place=active_place, org=active_org))}">{h(actor)} {count}</a>')

    place_parts = []
    for place, count in sorted(place_counts.items(), key=lambda item: (-item[1], item[0]))[:10]:
        cls = "button active" if place == active_place else "button"
        place_parts.append(f'<a class="{cls}" href="{h(event_filter_href(scope_type, scope_slug, tag=active_tag, actor=active_actor, place=place, org=active_org))}">{h(place)} {count}</a>')

    org_parts = []
    for org, count in sorted(org_counts.items(), key=lambda item: (-item[1], item[0]))[:10]:
        cls = "button active" if org == active_org else "button"
        org_parts.append(f'<a class="{cls}" href="{h(event_filter_href(scope_type, scope_slug, tag=active_tag, actor=active_actor, place=active_place, org=org))}">{h(org)} {count}</a>')

    return (
        '<div class="filters">' + "".join(parts) + "</div>"
        + '<div class="filters">' + "".join(actor_parts) + "</div>"
        + '<div class="filters">' + "".join(place_parts) + "</div>"
        + '<div class="filters">' + "".join(org_parts) + "</div>"
    )


def events(
    topic_slug: str = "",
    person_slug: str = "",
    active_tag: str = "",
    active_actor: str = "",
    active_place: str = "",
    active_org: str = "",
) -> bytes:
    if not topic_slug and not person_slug:
        return event_overview()

    scope_type = "topic" if topic_slug else "person"
    scope_slug = topic_slug or person_slug
    known = topic_by_slug(scope_slug) if scope_type == "topic" else person_by_slug(scope_slug)
    if not known:
        return layout("未找到事件线索", '<div class="notice">未找到对应的事件线索。</div>')

    try:
        rows = fetch_event_rows(scope_type, scope_slug)
    except sqlite3.OperationalError:
        return layout(
            "事件线索",
            '<div class="notice">事件线索数据还没有生成。请先运行事件年表生成脚本。</div>',
        )

    scope_name = str(known["name"])
    all_rows = rows
    if active_tag:
        rows = [row for row in rows if active_tag in split_terms(row["tags"])]
    if active_actor:
        rows = [row for row in rows if active_actor in split_terms(row["actors"])]
    if active_place:
        rows = [row for row in rows if active_place in split_terms(row["places"])]
    if active_org:
        rows = [row for row in rows if active_org in split_terms(row["organizations"])]
    back_href = "/topics" if scope_type == "topic" else "/people"
    timeline_href = f"/timeline?{scope_type}={quote(scope_slug)}"
    source_href = f"/{scope_type}s/{quote(scope_slug)}" if scope_type == "topic" else f"/people/{quote(scope_slug)}"
    title = f"{scope_name}事件线索"
    years: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        years.setdefault(str(row["event_year"] or "未注明"), []).append(row)

    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(title)}</h1>
    <div class="meta">按事件节点组织资料。事件摘要来自中文译文和术语规则，适合快速定位线索；正式引用仍以原文、页码和 FRUS 来源为准。</div>
    <div class="meta">{len(rows)} 个事件节点 · {len({row["page_id"] for row in rows})} 个资料片段 · {len({row["doc_key"] for row in rows})} 篇文档</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/events">事件总览</a>
    <a class="button" href="{h(back_href)}">返回索引</a>
    <a class="button" href="{h(source_href)}">资料列表</a>
    <a class="button" href="{h(timeline_href)}">文档年表</a>
    <a class="button" href="/events/cards?{h(scope_type)}={h(scope_slug)}">研究卡片</a>
  </div>
</section>
{event_filter_bar(all_rows, scope_type, scope_slug, active_tag, active_actor, active_place, active_org)}
"""
    if not rows:
        body += '<div class="notice">暂无事件线索。</div>'
    else:
        for year in sorted(years.keys(), key=lambda y: (y == "未注明", y)):
            body += f'<h2 style="font-size:18px;margin:18px 0 8px;">{h(year)}</h2><section class="result-list">'
            for row in years[year]:
                page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
                doc_href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
                actor_tags = "".join(f'<span class="tag">{h(value)}</span>' for value in split_terms(row["actors"]))
                topic_tags_html = "".join(f'<span class="tag">{h(value)}</span>' for value in split_terms(row["tags"]))
                place_tags_html = "".join(f'<span class="tag">{h(value)}</span>' for value in split_terms(row["places"]))
                org_tags_html = "".join(f'<span class="tag">{h(value)}</span>' for value in split_terms(row["organizations"]))
                body += f"""
<article class="result">
  <div>
    <h2><a href="{h(doc_href)}">{h(row["event_title"])}</a></h2>
    <div class="meta">{h(row["event_date"] or row["date_guess"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(page)} {grade_badge(row)}</div>
    <div class="zh">{h(compact(row["event_summary"], 360))}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 220))}</div>
    <div class="tagline">{actor_tags}{topic_tags_html}{place_tags_html}{org_tags_html}<span class="tag">重要度 {h(row["importance"])}</span></div>
  </div>
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">FRUS</a></div>
</article>"""
            body += "</section>"
    return layout(title, body)


def facet_column(kind: str) -> tuple[str, str, str]:
    if kind == "place":
        return "places", "地点索引", "地点"
    return "organizations", "机构索引", "机构"


def event_facet_index(kind: str) -> bytes:
    column, title, label = facet_column(kind)
    try:
        rows = fetch_all_event_rows()
    except sqlite3.OperationalError:
        return layout(title, '<div class="notice">事件线索数据还没有生成。</div>')

    counts: dict[str, set[int]] = {}
    event_counts: dict[str, int] = {}
    for row in rows:
        for value in split_terms(row[column]):
            counts.setdefault(value, set()).add(row["page_id"])
            event_counts[value] = event_counts.get(value, 0) + 1

    path = "/places" if kind == "place" else "/organizations"
    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(title)}</h1>
    <div class="meta">按{h(label)}聚合事件线索，并保留原文、译文、摘录卡片和 FRUS 来源入口。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/events">事件总览</a>
    <a class="button" href="/topics">专题</a>
    <a class="button" href="/people">人物</a>
  </div>
</section>
"""
    if not counts:
        body += f'<div class="notice">暂无{h(label)}线索。</div>'
        return layout(title, body)

    body += '<section class="result-list">'
    for value in sorted(counts.keys(), key=lambda item: (-len(counts[item]), -event_counts[item], item)):
        href = f"{path}/{quote(value)}"
        body += f"""
<article class="result">
  <div>
    <h2><a href="{h(href)}">{h(value)}</a></h2>
    <div class="meta">{event_counts[value]} 个事件节点 · {len(counts[value])} 个资料片段</div>
  </div>
  <div class="cite"><a href="{h(href)}">查看线索</a></div>
</article>"""
    body += "</section>"
    return layout(title, body)


def event_facet_page(kind: str, value: str, core_only: bool = False) -> bytes:
    column, title, label = facet_column(kind)
    try:
        all_rows = fetch_all_event_rows()
    except sqlite3.OperationalError:
        return layout(title, '<div class="notice">事件线索数据还没有生成。</div>')

    seen: set[tuple[int, str]] = set()
    rows = []
    for row in all_rows:
        if value not in split_terms(row[column]):
            continue
        if core_only and row["grade"] != "核心文献":
            continue
        key = (row["page_id"], row["event_title"])
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)

    list_href = "/places" if kind == "place" else "/organizations"
    core_href = f"{list_href}/{quote(value)}?grade=core"
    all_href = f"{list_href}/{quote(value)}"
    page_title = f"{value}{label}线索"
    years: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        years.setdefault(str(row["event_year"] or "未注明"), []).append(row)

    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(page_title)}</h1>
    <div class="meta">{len(rows)} 个事件节点 · {len({row["page_id"] for row in rows})} 个资料片段 · {len({row["doc_key"] for row in rows})} 篇文档</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="{h(list_href)}">返回{h(label)}索引</a>
    <a class="button" href="/events">事件总览</a>
    <a class="button{' active' if not core_only else ''}" href="{h(all_href)}">全部</a>
    <a class="button{' active' if core_only else ''}" href="{h(core_href)}">核心文献</a>
  </div>
</section>
"""
    if not rows:
        body += f'<div class="notice">暂无{h(value)}相关事件线索。</div>'
        return layout(page_title, body)

    for year in sorted(years.keys(), key=lambda y: (y == "未注明", y)):
        body += f'<h2 style="font-size:18px;margin:18px 0 8px;">{h(year)}</h2><section class="result-list">'
        for row in years[year]:
            page = source_page_label(row)
            doc_href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
            chips = "".join(f'<span class="tag">{h(term)}</span>' for term in split_terms(row["actors"]) + split_terms(row["tags"]) + split_terms(row["places"]) + split_terms(row["organizations"]))
            body += f"""
<article class="result">
  <div>
    <h2><a href="{h(doc_href)}">{h(row["event_title"])}</a></h2>
    <div class="meta">{h(row["event_date"] or row["date_guess"])} · {h(row["scope_name"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(page)} {grade_badge(row)}</div>
    <div class="zh">{h(compact(row["event_summary"], 360))}</div>
    <div class="tagline">{chips}</div>
  </div>
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">FRUS</a></div>
</article>"""
        body += "</section>"
    return layout(page_title, body)


def event_cards(topic_slug: str = "", person_slug: str = "") -> bytes:
    if not topic_slug and not person_slug:
        return layout("研究卡片", '<div class="notice">请先选择一个人物或专题事件线索。</div>')

    scope_type = "topic" if topic_slug else "person"
    scope_slug = topic_slug or person_slug
    known = topic_by_slug(scope_slug) if scope_type == "topic" else person_by_slug(scope_slug)
    if not known:
        return layout("研究卡片", '<div class="notice">未找到对应的事件线索。</div>')

    try:
        rows = fetch_event_rows(scope_type, scope_slug)
    except sqlite3.OperationalError:
        return layout("研究卡片", '<div class="notice">事件线索数据还没有生成。</div>')

    scope_name = str(known["name"])
    lines = [
        f"# {scope_name}事件研究卡片",
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
        page = source_page_label(row)
        source_url = row["page_url"] or row["doc_url"] or ""
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
    markdown = "\n".join(lines).strip() + "\n"
    back_href = f"/events?{scope_type}={quote(scope_slug)}"
    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(scope_name)}研究卡片</h1>
    <div class="meta">按年份导出事件节点、摘要、人物标签、原文摘录、中文译文和 FRUS 来源。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="{h(back_href)}">返回事件线索</a>
    <a class="button" href="/events">事件总览</a>
  </div>
</section>
<textarea class="copybox" readonly style="min-height:640px;">{h(markdown)}</textarea>
"""
    return layout(f"{scope_name}研究卡片", body)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        if parsed.path == "/":
            payload = home()
        elif parsed.path == "/focus":
            payload = focus_page(qs.get("saved", [""])[0] == "1")
        elif parsed.path == "/dashboard":
            payload = dashboard()
        elif parsed.path == "/search":
            payload = search(qs.get("q", [""])[0])
        elif parsed.path == "/docs":
            payload = docs(qs.get("grade", [""])[0], qs.get("translation", [""])[0])
        elif parsed.path == "/quality":
            payload = quality(qs.get("severity", [""])[0], qs.get("issue", [""])[0])
        elif parsed.path == "/tasks":
            payload = tasks(qs.get("queue", [""])[0])
        elif parsed.path == "/people":
            payload = people()
        elif parsed.path.startswith("/people/"):
            payload = person_page(unquote(parsed.path.removeprefix("/people/")))
        elif parsed.path == "/places":
            payload = event_facet_index("place")
        elif parsed.path.startswith("/places/"):
            payload = event_facet_page("place", unquote(parsed.path.removeprefix("/places/")), qs.get("grade", [""])[0] == "core")
        elif parsed.path == "/organizations":
            payload = event_facet_index("organization")
        elif parsed.path.startswith("/organizations/"):
            payload = event_facet_page("organization", unquote(parsed.path.removeprefix("/organizations/")), qs.get("grade", [""])[0] == "core")
        elif parsed.path == "/topics":
            payload = topics()
        elif parsed.path.startswith("/topics/"):
            payload = topic_page(unquote(parsed.path.removeprefix("/topics/")))
        elif parsed.path == "/timeline":
            payload = timeline(qs.get("topic", [""])[0], qs.get("person", [""])[0])
        elif parsed.path == "/events":
            payload = events(
                qs.get("topic", [""])[0],
                qs.get("person", [""])[0],
                qs.get("tag", [""])[0],
                qs.get("actor", [""])[0],
                qs.get("place", [""])[0],
                qs.get("org", [""])[0],
            )
        elif parsed.path == "/events/cards":
            payload = event_cards(qs.get("topic", [""])[0], qs.get("person", [""])[0])
        elif parsed.path.startswith("/review/"):
            try:
                page_id_int = int(parsed.path.removeprefix("/review/"))
            except ValueError:
                page_id_int = 0
            payload = review_page(page_id_int, qs.get("saved", [""])[0] == "1")
        elif parsed.path.startswith("/cite/"):
            try:
                page_id_int = int(parsed.path.removeprefix("/cite/"))
            except ValueError:
                page_id_int = 0
            payload = citation_page(page_id_int)
        elif parsed.path.startswith("/doc/"):
            doc_key = unquote(parsed.path.removeprefix("/doc/"))
            payload = doc_page(doc_key, qs.get("page_id", [None])[0])
        else:
            self.send_response(404)
            payload = layout("未找到", '<div class="notice">未找到页面。</div>')
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/focus":
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            ok, error = save_home_focus(parse_qs(body))
            if ok:
                self.send_response(303)
                self.send_header("Location", "/focus?saved=1")
                self.end_headers()
                return
            payload = focus_page(error=error)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return
        if parsed.path.startswith("/review/"):
            try:
                page_id_int = int(parsed.path.removeprefix("/review/"))
            except ValueError:
                page_id_int = 0
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            form = parse_qs(body)
            after_save = (form.get("after_save", ["stay"])[0] or "stay").strip()
            save_review(page_id_int, form)
            next_id = next_review_page_id(page_id_int) if after_save == "next" else 0
            location = f"/review/{next_id}?saved=1" if next_id else f"/review/{page_id_int}?saved=1"
            self.send_response(303)
            self.send_header("Location", location)
            self.end_headers()
            return
        self.send_response(404)
        payload = layout("未找到", '<div class="notice">未找到页面。</div>')
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt: str, *args: object) -> None:
        print(fmt % args)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Serving http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
