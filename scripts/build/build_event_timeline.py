#!/usr/bin/env python3
from __future__ import annotations

import re
import sqlite3
from pathlib import Path


DB_PATH = Path.cwd() / "data" / "research_index.sqlite"


TOPICS = [
    {
        "slug": "kunming-assassinations",
        "name": "昆明暗杀与民盟政治压力",
        "terms": ["Kunming", "assassin", "assassination", "李公朴", "闻一多", "暗杀", "昆明"],
    },
    {
        "slug": "pcc-1946",
        "name": "1946 年政治协商会议",
        "terms": ["Political Consultative", "PCC", "政治协商", "政协", "国民大会", "Steering Committee"],
    },
    {
        "slug": "marshall-mediation",
        "name": "马歇尔调处与民盟",
        "terms": ["Marshall", "马歇尔", "truce", "cease", "停战", "调处", "mediation"],
    },
    {
        "slug": "third-force",
        "name": "第三方面与中间路线",
        "terms": ["Third Party", "third party", "third force", "第三方面", "中间路线", "Youth Party", "Democratic Socialist"],
    },
    {
        "slug": "peiping-1949",
        "name": "1949 年北平接触",
        "terms": ["Peiping", "1949", "北平", "Clubb", "Lo Lung-chi", "Chang Lan", "Li Chi-shen"],
    },
]


PEOPLE = [
    {"slug": "lo-lung-chi", "name": "罗隆基", "terms": ["Lo Lung-chi", "Lo Lung Chi", "Lo Lung", "罗隆基"]},
    {"slug": "chang-lan", "name": "张澜", "terms": ["Chang Lan", "Chang Piao-fang", "张澜"]},
    {"slug": "liang-shu-ming", "name": "梁漱溟", "terms": ["Liang Shu-ming", "梁漱溟"]},
    {"slug": "shen-chun-ju", "name": "沈钧儒", "terms": ["Shen Chun-ju", "沈钧儒"]},
    {"slug": "huang-yen-pei", "name": "黄炎培", "terms": ["Huang Yen-pei", "黄炎培"]},
    {"slug": "chang-po-chun", "name": "章伯钧", "terms": ["Chang Po-chun", "章伯钧"]},
    {"slug": "shih-liang", "name": "史良", "terms": ["Shih Liang", "史良"]},
    {"slug": "carsun-chang", "name": "张君劢", "terms": ["Carsun Chang", "Chang Chun-mai", "张君劢"]},
    {"slug": "chang-tung-sun", "name": "张东荪", "terms": ["Chang Tung-sun", "Chang Tung Sun", "张东荪"]},
    {"slug": "chou-en-lai", "name": "周恩来", "terms": ["Chou En-lai", "Chou Enlai", "周恩来", "周将军"]},
]


ACTORS = [
    ("罗隆基", ["Lo Lung-chi", "Lo Lung Chi", "罗隆基"]),
    ("张澜", ["Chang Lan", "Chang Piao-fang", "张澜"]),
    ("梁漱溟", ["Liang Shu-ming", "梁漱溟"]),
    ("沈钧儒", ["Shen Chun-ju", "沈钧儒"]),
    ("黄炎培", ["Huang Yen-pei", "黄炎培"]),
    ("章伯钧", ["Chang Po-chun", "章伯钧"]),
    ("史良", ["Shih Liang", "史良"]),
    ("张君劢", ["Carsun Chang", "张君劢"]),
    ("张东荪", ["Chang Tung-sun", "张东荪"]),
    ("周恩来", ["Chou En-lai", "周恩来", "周将军"]),
    ("马歇尔", ["Marshall", "马歇尔"]),
    ("司徒雷登", ["Stuart", "司徒雷登"]),
    ("蒋介石", ["Generalissimo", "蒋介石", "委员长"]),
]


PLACES = [
    ("昆明", ["Kunming", "昆明"]),
    ("北平", ["Peiping", "Peking", "北平", "北京"]),
    ("南京", ["Nanking", "南京"]),
    ("重庆", ["Chungking", "Chungking", "重庆"]),
    ("上海", ["Shanghai", "上海"]),
    ("香港", ["Hong Kong", "香港"]),
    ("延安", ["Yenan", "Yen-an", "延安"]),
    ("沈阳", ["Mukden", "Shenyang", "沈阳"]),
    ("满洲", ["Manchuria", "满洲"]),
    ("成都", ["Chengtu", "Chengdu", "成都"]),
    ("桂林", ["Kweilin", "Kueilin", "桂林"]),
    ("天津", ["Tientsin", "天津"]),
    ("牯岭", ["Kuling", "牯岭"]),
    ("华盛顿", ["Washington", "华盛顿"]),
]


ORGANIZATIONS = [
    ("中国民主同盟", ["Democratic League", "民主同盟", "民盟", "Federation of Chinese Democratic Parties", "民主政团同盟"]),
    ("国民政府", ["National Government", "Kuomintang Government", "国民政府"]),
    ("国民党", ["Kuomintang", "KMT", "国民党"]),
    ("中国共产党", ["Chinese Communist Party", "Communist Party", "CCP", "共产党", "中共"]),
    ("青年党", ["Youth Party", "青年党"]),
    ("民主社会党", ["Democratic Socialist", "民主社会党"]),
    ("政治协商会议", ["Political Consultative", "PCC", "政治协商", "政协"]),
    ("美国国务院", ["Department of State", "State Department", "国务卿", "国务院"]),
    ("美国驻华使馆", ["Embassy in China", "American Embassy", "美国使馆", "驻华使馆"]),
    ("美国驻昆明领事馆", ["Consul General at Kunming", "Consulate General at Kunming", "驻昆明总领事"]),
    ("美国驻北平总领事馆", ["Consul General at Peiping", "驻北平总领事"]),
    ("美国驻上海总领事馆", ["Consul General at Shanghai", "驻上海总领事"]),
    ("行政院", ["Executive Yuan", "行政院"]),
    ("国民大会", ["National Assembly", "国民大会"]),
]


def ensure_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        DROP TABLE IF EXISTS research_events;
        CREATE TABLE research_events (
            id INTEGER PRIMARY KEY,
            scope_type TEXT NOT NULL,
            scope_slug TEXT NOT NULL,
            scope_name TEXT NOT NULL,
            page_id INTEGER NOT NULL REFERENCES pages(id),
            event_date TEXT,
            event_year TEXT,
            event_title TEXT NOT NULL,
            event_summary TEXT NOT NULL,
            actors TEXT,
            tags TEXT,
            places TEXT,
            organizations TEXT,
            importance INTEGER NOT NULL DEFAULT 0,
            UNIQUE(scope_type, scope_slug, page_id)
        );
        CREATE INDEX IF NOT EXISTS idx_research_events_scope ON research_events(scope_type, scope_slug);
        CREATE INDEX IF NOT EXISTS idx_research_events_page ON research_events(page_id);
        CREATE INDEX IF NOT EXISTS idx_research_events_year ON research_events(event_year);
        """
    )


def compact(text: str, limit: int = 220) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def year_from(text: str) -> str:
    match = re.search(r"\b(19[4-5][0-9])\b", text or "")
    return match.group(1) if match else "未注明"


def contains_any(text: str, needles: list[str]) -> bool:
    lower = (text or "").lower()
    return any(needle.lower() in lower for needle in needles)


def alias_where(columns: list[str], aliases: list[str]) -> tuple[str, list[str]]:
    parts = []
    params: list[str] = []
    for alias in aliases:
        like = f"%{alias}%"
        for column in columns:
            parts.append(f"{column} LIKE ?")
            params.append(like)
    return "(" + " OR ".join(parts) + ")", params


def actors_for(text: str) -> str:
    names = [name for name, aliases in ACTORS if contains_any(text, aliases)]
    return "; ".join(names[:8])


def places_for(text: str) -> str:
    names = [name for name, aliases in PLACES if contains_any(text, aliases)]
    return "; ".join(names[:8])


def organizations_for(text: str) -> str:
    names = [name for name, aliases in ORGANIZATIONS if contains_any(text, aliases)]
    return "; ".join(names[:10])


def tags_for(text: str) -> str:
    checks = [
        ("昆明暗杀", ["Kunming", "assassin", "暗杀", "李公朴", "闻一多"]),
        ("政协", ["Political Consultative", "PCC", "政治协商", "政协"]),
        ("马歇尔调处", ["Marshall", "马歇尔", "truce", "cease", "停战"]),
        ("第三方面", ["Third Party", "third force", "第三方面", "中间路线"]),
        ("北平接触", ["Peiping", "北平", "Clubb", "柯乐博"]),
        ("联合政府", ["coalition government", "联合政府"]),
        ("民盟", ["Democratic League", "民主同盟", "民盟"]),
    ]
    return "; ".join(label for label, aliases in checks if contains_any(text, aliases))


def event_title(scope_type: str, scope_name: str, row: sqlite3.Row, tags: str, actors: str) -> str:
    text = f"{row['title']} {row['source_text']} {row['zh_text']}"
    if "昆明暗杀" in tags:
        return "昆明暗杀事件引发的政治压力与外交关注"
    if "政协" in tags and "马歇尔" in actors:
        return "围绕政协决议和政府改组的调处"
    if "北平接触" in tags:
        return "北平接触与民盟人士沟通"
    if "第三方面" in tags:
        return "第三方面在国共之间寻求政治空间"
    if scope_type == "person":
        return f"{scope_name}相关材料：{row['title']}"
    return row["title"]


def event_summary(row: sqlite3.Row, tags: str, actors: str) -> str:
    zh = row["zh_text"] or ""
    source = row["source_text"] or ""
    text = zh if len(zh) > 80 else source
    sentences = re.split(r"(?<=[。.!?])\s*", text)
    useful = []
    for sentence in sentences:
        if not sentence.strip():
            continue
        if any(token in sentence for token in ["民主同盟", "民盟", "罗隆基", "张澜", "政协", "暗杀", "马歇尔", "北平", "联合政府", "第三方面"]):
            useful.append(sentence.strip())
        if len(useful) >= 2:
            break
    if useful:
        return compact(" ".join(useful), 260)
    return compact(text, 260)


def importance(row: sqlite3.Row, tags: str, actors: str) -> int:
    score = 0
    if row["grade"] == "核心文献":
        score += 40
    elif row["grade"] == "相关文献":
        score += 20
    if "民盟" in tags:
        score += 15
    if "昆明暗杀" in tags or "政协" in tags or "北平接触" in tags:
        score += 15
    if "罗隆基" in actors or "张澜" in actors:
        score += 10
    if row["page_label"]:
        score += 5
    return score


def fetch_matching_rows(conn: sqlite3.Connection, terms: list[str]) -> list[sqlite3.Row]:
    where, params = alias_where(
        ["documents.title", "documents.matched_terms", "pages.text", "translations.text"],
        terms,
    )
    return conn.execute(
        f"""
        SELECT
            pages.id AS page_id,
            pages.page_label,
            pages.page_url,
            pages.text AS source_text,
            documents.doc_key,
            documents.volume_id,
            documents.doc_id,
            documents.title,
            documents.date_guess,
            COALESCE(dc.grade, '') AS grade,
            translations.text AS zh_text
        FROM pages
        JOIN documents ON documents.id = pages.document_id
        LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        WHERE {where}
        GROUP BY pages.id
        ORDER BY documents.date_guess, documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
        """,
        tuple(params),
    ).fetchall()


def insert_events(conn: sqlite3.Connection, scope_type: str, scope_slug: str, scope_name: str, terms: list[str]) -> int:
    rows = fetch_matching_rows(conn, terms)
    inserted = 0
    for row in rows:
        combined = f"{row['title']} {row['source_text']} {row['zh_text']}"
        actors = actors_for(combined)
        tags = tags_for(combined)
        places = places_for(combined)
        organizations = organizations_for(combined)
        title = event_title(scope_type, scope_name, row, tags, actors)
        summary = event_summary(row, tags, actors)
        conn.execute(
            """
            INSERT OR REPLACE INTO research_events(
                scope_type, scope_slug, scope_name, page_id, event_date, event_year,
                event_title, event_summary, actors, tags, places, organizations, importance
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                scope_type,
                scope_slug,
                scope_name,
                row["page_id"],
                row["date_guess"] or "",
                year_from(f"{row['date_guess']} {row['volume_id']} {row['doc_key']}"),
                title,
                summary,
                actors,
                tags,
                places,
                organizations,
                importance(row, tags, actors),
            ),
        )
        inserted += 1
    return inserted


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    total = 0
    for topic in TOPICS:
        total += insert_events(conn, "topic", topic["slug"], topic["name"], topic["terms"])
    for person in PEOPLE:
        total += insert_events(conn, "person", person["slug"], person["name"], person["terms"])
    conn.commit()
    scopes = conn.execute("SELECT scope_type, scope_slug, count(*) FROM research_events GROUP BY scope_type, scope_slug").fetchall()
    conn.close()
    print(f"Built {total} scoped events.")
    for scope_type, scope_slug, count in scopes:
        print(f"{scope_type}:{scope_slug} {count}")


if __name__ == "__main__":
    main()
