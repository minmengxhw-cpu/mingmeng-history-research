#!/usr/bin/env python3
from __future__ import annotations

import html
import sys
import json
import re
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

# 当前请求路径的 thread-local 容器，layout() 用来自动 highlight 当前导航
_request = threading.local()


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
    "Burke": "伯克",
    "Cabot": "卡伯特",
    "Caughey": "考吉",
    "Charlton Ogburn": "查尔顿·奥格本",
    "Chiang Kai-shek": "蒋介石",
    "Chou En-lai": "周恩来",
    "Chang Chun": "张群",
    "Chang Lan": "张澜",
    "Carsun Chang": "张君劢",
    "Clark": "克拉克",
    "Clubb": "柯乐博",
    "Dams": "达姆斯",
    "Freeman": "弗里曼",
    "Fulton Freeman": "弗里曼",
    "Gauss": "高斯",
    "Generalissimo Chiang Kai-shek": "蒋介石委员长",
    "Hopper": "霍珀",
    "Hsu Yung-chang": "徐永昌",
    "Hurley": "赫尔利",
    "James R. Shepley": "詹姆斯·R·谢普利",
    "John Service": "约翰·谢伟思",
    "John S. Service": "约翰·S·谢伟思",
    "Langdon": "兰登",
    "Lo Lung-chi": "罗隆基",
    "Ludden": "卢登",
    "Marshall": "马歇尔",
    "McConaughy": "麦康纳",
    "McKenna": "麦肯纳",
    "Mo Teh-hui": "莫德惠",
    "Myers": "迈尔斯",
    "Penfield": "彭菲尔德",
    "Rice": "赖斯",
    "Ringwalt": "林沃尔特",
    "Service": "谢伟思",
    "Shepley": "谢普利",
    "Smyth": "史密斯",
    "Sprouse": "斯普劳斯",
    "Stuart": "司徒雷登",
    "T. V. Soong": "宋子文",
    "Truman": "杜鲁门",
    "Wang Shihchieh": "王世杰",
    "Wang Shih-chieh": "王世杰",
    "Wedemeyer": "魏德迈",
    "Yu Ta-wei": "俞大维",
}


ROLE_ZH = {
    "The Ambassador in China": "驻华大使",
    "The Appointed Ambassador in China": "被任命的驻华大使",
    "The Ambassador Designate in China": "候任驻华大使",
    "The Chargé in China": "驻华代办",
    "The Counselor of Embassy in China": "驻华使馆参赞",
    "The Minister-Counselor of Embassy in China": "驻华使馆公使衔参赞",
    "The First Secretary of Embassy in China": "驻华使馆一等秘书",
    "The Second Secretary of Embassy in China": "驻华使馆第二书记",
    "The Consul at Canton": "驻广州领事",
    "The Consul at Kweilin": "驻桂林领事",
    "The Consul at Peiping": "驻北平领事",
    "The Consul at Shanghai": "驻沪领事",
    "The Consul at Tientsin": "驻天津领事",
    "The Consul General at Kunming": "驻昆明总领事",
    "The Consul General at Shanghai": "驻上海总领事",
    "The Consul General at Hong Kong": "驻香港总领事",
    "The Consul General at Peiping": "驻北平总领事",
    "The Consul General at Tientsin": "驻天津总领事",
    "The Vice Consul at Chengtu": "驻成都副领事",
    "The Acting Secretary of State": "代理国务卿",
    "The Secretary of State": "国务卿",
    "The President": "总统",
    "President Truman": "杜鲁门总统",
    "the Bureau of Far Eastern Affairs": "远东事务司",
    "Bureau of Far Eastern Affairs": "远东事务司",
    "the State-War-Navy Coordinating Committee": "国务院-陆军部-海军部协调委员会",
    "State-War-Navy Coordinating Committee": "国务院-陆军部-海军部协调委员会",
    "the Department of State": "国务院",
    "Department of State": "国务院",
    "the Chinese Ministry of Information": "中国新闻局",
    "Chinese Ministry of Information": "中国新闻局",
    "the Embassy in China": "驻华使馆",
    "Embassy in China": "驻华使馆",
    "The British Embassy": "英国大使馆",
    "British Embassy": "英国大使馆",
    "the Department of State": "国务院",
    "Chinese Communist Party": "中国共产党",
    "the Chinese Communist Party": "中国共产党",
    "the Democratic League": "中国民主同盟",
    "Democratic League": "中国民主同盟",
}


EXACT_TITLE_ZH = {
    # --- FRUS 专用 ---
    "Memorandum by the Second Secretary of Embassy in China (Sprouse)": "驻华使馆第二书记斯普劳斯备忘录",
    "Memorandum by the Second Secretary of Embassy in China (Sprouse) to General Marshall": "驻华使馆第二书记斯普劳斯致马歇尔将军备忘录",
    "Minutes of Conference Between General Marshall and Dr. Lo Lung-chi at General Marshall’s House, June 1, 1946, 10 a.m.": "马歇尔将军与罗隆基博士会谈纪要，1946年6月1日上午10时",
    "Counterproposals by the Chinese Communist Party": "中国共产党方面的反建议",
    "Chinese National Government’s Reply to Communist Party’s Counterproposals": "中国国民政府对共产党反建议的答复",
    "General Marshall’s Notes on a Conference With Dr. Wang Shihchieh, at Nanking, January 7, 1947, 5 p.m.": "马歇尔将军关于1947年1月7日下午5时在南京同王世杰博士会谈的记录",
    "Memorandum Concerning United States Post-War Military Policies With Respect to China": "关于美国战后对华军事政策的备忘录",
    "Charter for the Interim Government of the Republic of China": "中华民国临时政府宪章",
    "General Marshall to President Truman": "马歇尔将军致杜鲁门总统",
    "Memorandum by General Chou En-lai to General Marshall": "周恩来将军致马歇尔将军备忘录",
    "Memorandum by General Marshall to Generalissimo Chiang Kai-shek": "马歇尔将军致蒋介石委员长备忘录",
    "Lieutenant General Albert C. Wedemeyer to General Marshall": "魏德迈中将致马歇尔将军",
    "Policy Statement Prepared in the Department of State": "国务院起草的政策声明",
    "Draft of New China News Agency": "新华社草案",
    "Memorandum by the State–War–Navy Coordinating Committee to the Secretary of State": "国务院-陆军部-海军部协调委员会致国务卿备忘录",
    "Report by the State-War-Navy Coordinating Committee": "国务院-陆军部-海军部协调委员会报告",
    "Memorandum by Mr. Charlton Ogburn of the Bureau of Far Eastern Affairs": "远东事务司查尔顿·奥格本备忘录",
    "Memorandum by Mr. James R. Shepley to General Marshall": "詹姆斯·R·谢普利致马歇尔将军备忘录",
    "Memorandum Prepared in the Chinese Ministry of Information Concerning the Chinese Communist Party": "中国新闻局起草的关于中国共产党的备忘录",
    "Notes on General Marshall’s First Conference With the Democratic League, 1600, 26 December 1945": "马歇尔将军与中国民主同盟首次会谈记录，1945年12月26日下午4时",
    "Notes on General Marshall's First Conference With the Democratic League, 1600, 26 December 1945": "马歇尔将军与中国民主同盟首次会谈记录，1945年12月26日下午4时",
    "Public Statement by General Marshall and Ambassador Stuart": "马歇尔将军与司徒雷登大使联合公开声明",
    # --- CIA 全部 61 篇 ---
    "POLITICAL INFORMATION: WENG SHIH-LIANG, SOUTH CHINA DEMOCRATIC LEAGUE CHAIRMAN, HONGKONG": "政治情报：华南民盟主席翁世亮，香港",
    "POLITICAL INFORMATION: SOUTH CHINA DEMOCRATIC LEAGUE ANTI-AMERICAN ACTIVITY . HONGKONG": "政治情报：华南民盟反美活动，香港",
    "PREPARATIONS FOR THE ALL-CHINA DEMOCRATIC WOMEN S CONGRESS": "全国民主妇女大会筹备",
    "POLITICAL INFORMATION:  PSEUDONYMS USED BY CHINESE COMMUNISTS IN REFERRING TO VARIOUS PUBLIC FIGURES": "政治情报：中共指称各公众人物所使用的化名",
    "CHINA DEMOCRATIC LEAGUE": "中国民主同盟",
    "POLITICAL INFORMATION: CHINA DEMOCRATIC LEAGUE MEMBERS' ESCAPE FROM SHANGHAI TO HONG KONG": "政治情报：民盟成员从上海出逃至香港",
    "PLAN FOR CHANGE IN POLICY FOR MEMBERSHIP IN DEMOCRATIC LEAGUE - LO LUNG-CHI AND CHANG LAN": "民盟成员政策变更方案——罗隆基与张澜",
    "WHO'S WHO - - CHINESE LEFTIST PERSONALITIES": "人物志——中国左翼人物",
    "MEMBERS OF THE CULTURAL AND EDUCATIONAL COMMISSION OF THE CENTRAL PEOPLE'S GOVERNMENT": "中央人民政府文化教育委员会委员名单",
    "LO LUNG-CHI": "罗隆基",
    "CHANG LAN": "张澜",
    "1.  POSITION OF SHEN CHUN-JU 1.  CRITICISM OF MAO TSE-TUNG": "一、沈钧儒的立场　二、对毛泽东的批评",
    "ARRIVAL OF CHINESE PEOPLE&#039;S POLITICAL CONSULTATIVE CONFERENCE DELEGATES IN CANTON": "中国人民政治协商会议代表抵达广州",
    "LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE": "中国民主同盟主要领导成员",
    "ROLE OF NON-COMMUNIST POLITICAL PARTIES IN PEIPING": "非共产党政党在北平的作用",
    "PLAN FOR MEETINGS OF NON-COMMUNIST PARTIES OF COMMUNIST CHINA": "共产党中国非共产党政党会议方案",
    "SUMMER TEACHERS' CLASSES SPONSORED BY CHINA DEMOCRATIC LEAGUE": "民盟主办的暑期教师讲习班",
    "MEMBERS OF THE EXECUTIVE COMMITTEE OF THE CHINESE CHAMBER OF COMMERCE": "中华商会执行委员会委员名单",
    "LIST OF IMPORTANT COMMITTEE OFFICIALS": "重要委员会官员名单",
    "ROSTER OF PRESIDIUM OF FIRST CONGRESS": "第一届全国人大主席团名册",
    "POLITICAL INFORMATION: SENIOR MEMBERS OF EXECUTIVE HEADQUARTERS FIELD TEAMS": "政治情报：军事调处执行部驻地小组高级成员",
    "CHINESE VIEWS ON AMERICAN ASSISTANCE TO CHINA": "中国各方对美国援华的看法",
    "SELANGOR CHINESE IN SUPPORT OF TAN KAH KEE": "雪兰莪华人声援陈嘉庚",
    "POLITICAL INFORMATION; PROVINCIAL GOVERNMENT PERSONNEL, KWANGSI": "政治情报：广西省政府人员",
    "CHINESE COMMUNIST ACTIVITIES IN INDONESIA": "中共在印度尼西亚的活动",
    "POLITICAL INFORMATION: CHINESE COMMUNIST PERSONALITIES IN SOUTH CHINA": "政治情报：华南中共人物",
    "CHINESE COMMUNIST VIEW CONCERNING THIRD WORLD WAR": "中共关于第三次世界大战的看法",
    "CHINESE COMMUNIST WOMEN CONNECTED WITH THE WORLD FEDERATION OF DEMOCRATIC WOMEN": "与世界民主妇女联合会有关联的中共女性",
    "POLITICAL INFORMATION: CHINESE COMMUNIST PLANS FOR COALITION GOVERNMENT": "政治情报：中共的联合政府方案",
    "DEVELOPMENTS IN CHINESE COMMUNITY IN THAILAND FOLLOWING COMMUNIST VICTORY IN CHINA": "中共胜利后泰国华人社会的新动态",
    "COMMUNIST IMFLUENCE IN BURMA": "共产势力在缅甸的影响",
    "ADMINISTRATIVE DIVISIONS OF CHINA": "中国行政区划",
    "CURRENT SITUATION IN MALAYA": "马来亚现状",
    "MINISTERS AND DEPUTY MINISTERS OF THE CENTRAL PEOPLE'S GOVERNMENT": "中央人民政府部长与副部长名单",
    "COMMUNIST INFLUENCE IN BURMA": "共产势力在缅甸的影响",
    "OFFICIALS OF THE EAST CHINA MILITARY AND POLITICAL COUNCIL": "华东军政委员会官员名单",
    "DIRECTORY OF CCP GOVERNMENT PERSONNEL": "中共政府人员名录",
    "PRO-COMMUNIST CHINESE ORGANIZATIONS IN RANGOON": "仰光亲共华人组织",
    "RECEPTION FOR THE NEW CHINESE COMMUNIST AMBASSADOR TO BURMA": "欢迎新任中共驻缅甸大使",
    "1. NUMBER OF BCSEA MEMBERS   2. DECLINE OF BCSEA IN MANDALAY": "一、缅甸华侨教育会会员人数　二、曼德勒缅华教育会的衰落",
    "RECENT DEVELOPEMENTS WITHIN THE BURMA WORKERS AND PEASANTS PARTY": "缅甸工农党近况",
    "ARRESTS, EXECUTIONS, AND OTHER CHINESE COMMUNIST ACTIVITIES": "逮捕、处决及其他中共活动",
    "CHINESE COMMUNIST ACTIVITIES IN EAST CHINA": "中共在华东的活动",
    "COMMUNISTS PUSH CONSTRUCTION OF T'ANG-KU HARBOR, STOP WORK ON HUANG-P'U HARBOR": "共产党推进塘沽港建设、停建黄浦港",
    "CHINESE COMMUNIST ACTIVITIES IN THE HONG KONG AREA": "中共在香港地区的活动",
    "DEVELOPMENTS IN THE CHINESE SCHOOL CONTROVERSY IN RANGOON": "仰光华校争议的新进展",
    "ORGANIZATION AND PERSONNEL OF UNITED FRONT DEPARTMENT OF SOUTH CHINA BUREAU": "中共华南局统战部组织与人员",
    "CHINESE COMMUNIST POLITICAL ACTIVITIES IN HANOI": "中共在河内的政治活动",
    "GOVERNMENT ADMINISTRATION COUNCIL APPROVES PERSONNEL CHANGES": "政务院批准人事变动",
    "CONFERENCE OF THE CHINA FARMERS&#039; AND WORKERS&#039; DEMOCRATIC PARTY": "中国农工民主党会议",
    "TREATMENT OF REPUDIATION OF COMPROMISE WITH WEST IN CHINESE COMMUNIST PRESS, PERIODICALS, FIRST QUARTER 1952": "1952年第一季度中共报刊中对拒绝与西方妥协的处理",
    "ECONOMIC ORGANIZATION OF COMMUNIST CHINA": "共产党中国的经济组织",
    "SMUGGLING OF RUBBER": "橡胶走私",
    "OUTLINE OF NEW ECONOMICS (REVISED LIBERATION EDITION)": "新经济学大纲（修订解放版）",
    "OUTLINE OF PUBLIC FINANCE": "公共财政概论",
    "SURVEY OF CHINA'S FOOD INDUSTRY, 1950": "1950年中国食品工业概况",
    "THE OVERSEAS CHINESE IN SOURTHEAST ASIA Section OC-3: THE OVERSEAS CHINESE IN BURMA": "东南亚华侨 第OC-3节：缅甸华侨",
    "COMMUNIST CHINA'S POWER POTENTIAL THROUGH 1957": "至1957年共产党中国的力量潜力",
    "COMMUNIST FIRMS, AND PARTY AND MILITARY ORGANIZATIONS IN FOOCHOW": "福州的共产党企业与党军组织",
    # --- Wilson Center ---
    "On the People's Democratic Dictatorship: In Commemoration of the Twenty-eighth Anniversary of the Communist Party of China, June 30, 1949": "论人民民主专政——纪念中国共产党二十八周年，1949年6月30日",
    "Report, Peng Dehuai to Mao Zedong and the CCP Central Committee (Excerpt)": "彭德怀致毛泽东及中共中央报告（节选）",
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


RANK_TITLES = {
    "General": "将军",
    "Lieutenant General": "中将",
    "Major General": "少将",
    "Colonel": "上校",
    "Admiral": "海军上将",
    "President": "总统",
    "Premier": "总理",
    "Generalissimo": "委员长",
    "Mr.": "先生",
    "Mrs.": "夫人",
    "Madame": "夫人",
    "Dr.": "博士",
    "Professor": "教授",
}

_RANK_RE = r"(General|Lieutenant General|Major General|Colonel|Admiral|President|Premier|Generalissimo|Mr\.|Mrs\.|Madame|Dr\.|Professor)"


def _rank_with_name(rank: str, name: str) -> str:
    """把 'General Chou En-lai' 转成 '周恩来将军'；'President Truman' → '杜鲁门总统'。"""
    name = name.strip()
    rank_zh = RANK_TITLES.get(rank, rank)
    name_zh = PERSON_ZH.get(name, name)
    # Mr./Mrs./Dr. 这种放后面（如 Mr. 谢普利）；其他放后面（如 周恩来将军）
    return f"{name_zh}{rank_zh}"


def translate_title(title: str) -> str:
    title = title or ""
    if title in EXACT_TITLE_ZH:
        return EXACT_TITLE_ZH[title]

    # 1. "X (P) to Y (Q)" → "X(P)致Y(Q)"
    m = re.match(r"(.+?) \(([^)]+)\) to (.+?) \(([^)]+)\)$", title)
    if m:
        src_role, src_person, dst_role, dst_person = m.groups()
        return f"{role_with_person(src_role, src_person)}致{role_with_person(dst_role, dst_person)}"

    # 2. "X (P) to Y" → "X(P)致Y"
    m = re.match(r"(.+?) \(([^)]+)\) to (.+)$", title)
    if m:
        src_role, src_person, dst_role = m.groups()
        return f"{role_with_person(src_role, src_person)}致{role_zh(dst_role)}"

    # 3. "Memorandum by X (P) to Y" → "X(P)致Y 备忘录"
    m = re.match(r"Memorandum by (.+?) \(([^)]+)\) to (.+)$", title)
    if m:
        role, person, dst = m.groups()
        return f"{role_with_person(role, person)}致{role_zh(dst)}备忘录"

    # 4. "Memorandum by X (P)" → "X(P)备忘录"
    m = re.match(r"Memorandum by (.+?) \(([^)]+)\)$", title)
    if m:
        role, person = m.groups()
        return f"{role_with_person(role, person)}备忘录"

    # 5. "Memorandum by RANK Name to RANK Name" → "X 致 Y 备忘录"
    m = re.match(rf"Memorandum by {_RANK_RE} (.+?) to {_RANK_RE} (.+?)$", title)
    if m:
        return f"{_rank_with_name(m.group(1), m.group(2))}致{_rank_with_name(m.group(3), m.group(4))}备忘录"

    # 6. "Memorandum by RANK Name of/in <body>" → "<body>之 RANK Name 备忘录"
    m = re.match(rf"Memorandum by {_RANK_RE} (.+?) (?:of|in) (?:the )?(.+?)$", title)
    if m:
        return f"{role_zh(m.group(3))}{_rank_with_name(m.group(1), m.group(2))}备忘录"

    # 7. "Memorandum by RANK Name" → "RANK Name 备忘录"
    m = re.match(rf"Memorandum by {_RANK_RE} (.+?)$", title)
    if m:
        return f"{_rank_with_name(m.group(1), m.group(2))}备忘录"

    # 8. "RANK Name to RANK Name" → "X 致 Y"
    m = re.match(rf"^{_RANK_RE} (.+?) to {_RANK_RE} (.+?)$", title)
    if m:
        return f"{_rank_with_name(m.group(1), m.group(2))}致{_rank_with_name(m.group(3), m.group(4))}"

    # 9. "RANK Name to <role>" → "X 致 <role>"
    m = re.match(rf"^{_RANK_RE} (.+?) to (.+?)$", title)
    if m:
        return f"{_rank_with_name(m.group(1), m.group(2))}致{role_zh(m.group(3))}"

    # 10. "Minutes/Notes of/on Meeting/Conference Between A and B[, at C][, date]"
    m = re.match(r"(?:Minutes|Notes) (?:of|on) (?:Meeting|Conference) Between (.+?) and (.+?)(?:, at (.+?))?(?:, .+)?$", title)
    if m:
        a, b, place = m.groups()
        a_zh = _translate_party(a)
        b_zh = _translate_party(b)
        place_zh = f"在{m.group(3)}" if place else ""
        return f"{a_zh}与{b_zh}{place_zh}会谈纪要"

    # 11. "Notes/Minutes of Conference Between A and B and C, ..."
    m = re.match(r"(?:Minutes|Notes) (?:of|on) (?:Meeting|Conference) Between (.+?), (.+?),? and (.+?)(?:, at (.+?))?(?:, .+)?$", title)
    if m:
        return f"{_translate_party(m.group(1))}、{_translate_party(m.group(2))}、{_translate_party(m.group(3))}会谈纪要"

    # 12. "Charter for X" → "X 宪章"
    m = re.match(r"Charter for (?:the )?(.+?)$", title)
    if m:
        return f"{role_zh(m.group(1))}宪章"

    # 13. "Report by X" → "X 报告"
    m = re.match(r"Report by (?:the )?(.+?)$", title)
    if m:
        return f"{role_zh(m.group(1))}报告"

    # 14. "Draft Prepared by X for Y" → "X 起草的 Y 草案"
    m = re.match(r"Draft Prepared by (?:the )?(.+?) for (?:the )?(.+?)$", title)
    if m:
        return f"{role_zh(m.group(1))}起草的{role_zh(m.group(2))}草案"

    # 15. "Statement by X" → "X 声明"
    m = re.match(r"Statement by (?:the )?(.+?)$", title)
    if m:
        return f"{role_zh(m.group(1))}声明"

    # 15a. "Public Statement by RANK Name and RANK Name" → "X 与 Y 公开声明"
    m = re.match(rf"Public Statement by {_RANK_RE} (.+?) and {_RANK_RE} (.+?)$", title)
    if m:
        return f"{_rank_with_name(m.group(1), m.group(2))}与{_rank_with_name(m.group(3), m.group(4))}公开声明"

    # 15b. "Memorandum Prepared in/by (the) X[ Concerning Y]" → "X 起草的备忘录[关于 Y]"
    m = re.match(r"Memorandum Prepared (?:in|by) (?:the )?(.+?)(?: Concerning (?:the )?(.+?))?$", title)
    if m:
        body = role_zh(m.group(1))
        topic = m.group(2)
        if topic:
            return f"{body}起草的关于{role_zh(topic)}的备忘录"
        return f"{body}起草的备忘录"

    # 15c. "Notes/Minutes of Interview Between A and B[ at C][, date]"
    m = re.match(r"(?:Notes|Minutes) (?:of|on) Interview Between (.+?) and (.+?)(?: at (.+?))?(?:, .+)?$", title)
    if m:
        a, b, place = m.groups()
        place_zh = f"在{place}" if place else ""
        return f"{_translate_party(a)}与{_translate_party(b)}{place_zh}访谈纪要"

    # 15d. "Notes of Meeting of A With B[ at C][, date]"
    m = re.match(r"Notes of Meeting of (.+?) With (.+?)(?: at (.+?))?(?:, .+)?$", title)
    if m:
        a, b, place = m.groups()
        place_zh = f"在{place}" if place else ""
        return f"{_translate_party(a)}与{_translate_party(b)}{place_zh}会议记录"

    # 15e. "Extracts of Minutes of Meeting Between A and B[ at C]"
    m = re.match(r"Extracts of Minutes of (?:Meeting|Conference) Between (.+?) and (.+?)(?: at (.+?))?(?:, .+)?$", title)
    if m:
        a, b, place = m.groups()
        place_zh = f"在{place}" if place else ""
        return f"{_translate_party(a)}与{_translate_party(b)}{place_zh}会谈纪要摘录"

    # 15f. "X's Notes on a Conference With Y[, at Z][, date]"
    m = re.match(r"(.+?)['’]s Notes on (?:a |an |the )?(?:Conference|Meeting) With (.+?)(?:, at (.+?))?(?:, .+)?$", title)
    if m:
        a, b, place = m.groups()
        place_zh = f"在{place}" if place else ""
        return f"{_translate_party(a)}与{_translate_party(b)}{place_zh}会谈记录"

    # 15g. "X's Notes on a Series of Meetings With Y[, date]"
    m = re.match(r"(.+?)['’]s Notes on a Series of Meetings With (.+?)(?:, .+)?$", title)
    if m:
        a, b = m.group(1), m.group(2)
        return f"{_translate_party(a)}与{_translate_party(b)}系列会议记录"

    # 15h. "Second/First/Third Draft Statement for X Prepared by RANK Name and ..."
    m = re.match(r"(First|Second|Third|Fourth) Draft Statement for (.+?) Prepared by (.+?)(?: and .+?)?$", title)
    if m:
        nth = {"First": "第一稿", "Second": "第二稿", "Third": "第三稿", "Fourth": "第四稿"}[m.group(1)]
        return f"由{_translate_party(m.group(3))}等起草的{_translate_party(m.group(2))}声明{nth}"

    # 15i. "The X to the Y" → 机构对机构（如 "The British Embassy to the Department of State"）
    m = re.match(r"The (.+?) to the (.+?)$", title)
    if m:
        return f"{role_zh('The ' + m.group(1))}致{role_zh('the ' + m.group(2))}"

    # 16. "X (P)" → "X(P)"（旧规则保留）
    m = re.match(r"(.+?) \(([^)]+)\)$", title)
    if m:
        role, person = m.groups()
        return role_with_person(role, person)

    return title


def _translate_party(party: str) -> str:
    """会谈纪要中的'某将军'/'某博士'/'某主席'类参与方翻译"""
    party = party.strip()
    # Dr./General/Mr. + name
    m = re.match(rf"^{_RANK_RE} (.+?)$", party)
    if m:
        return _rank_with_name(m.group(1), m.group(2))
    return PERSON_ZH.get(party, party)


def title_block(title: str, href: str | None = None, level: str = "h2") -> str:
    zh = translate_title(title)
    main = f'<a href="{h(href)}">{h(zh)}</a>' if href else h(zh)
    english = "" if zh == title else f'<div class="title-en">{h(title)}</div>'
    return f"<{level}>{main}</{level}>{english}"


def breadcrumb_html(crumbs: list[tuple[str | None, str]]) -> str:
    """生成面包屑导航。crumbs = [(href|None, label), ...]，None 表示当前页（不渲染链接）"""
    if not crumbs:
        return ""
    parts = []
    for i, (href, label) in enumerate(crumbs):
        if href:
            parts.append(f'<a href="{h(href)}">{h(label)}</a>')
        else:
            parts.append(f'<span class="current">{h(label)}</span>')
        if i < len(crumbs) - 1:
            parts.append('<span class="sep">›</span>')
    return f'<nav class="breadcrumb">{"".join(parts)}</nav>'


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


# 人物档案数据从 person_archive.py 独立模块加载（AI 内部研究参考）
# 本研究平台只收录国外一手原始档案；人物档案仅用于档案翻译人名标准化和上下文理解
from person_archive import PEOPLE, PERSON_GROUPS  # noqa: E402

# 关键历史事件骨架（AI 内部研究参考）
# 用于把档案碎片化命中聚合到学术意义上的历史事件节点
from key_events import KEY_EVENTS, EVENT_PHASES, event_by_slug  # noqa: E402


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


ICONS_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">
  <symbol id="i-search" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></symbol>
  <symbol id="i-archive" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="5" rx="1"/><path d="M5 8v11a1 1 0 001 1h12a1 1 0 001-1V8M10 12h4"/></symbol>
  <symbol id="i-people" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="9" cy="8" r="3.5"/><path d="M3.5 20a5.5 5.5 0 0111 0M16 11a3 3 0 100-6M21 20a4.5 4.5 0 00-7.5-3.4"/></symbol>
  <symbol id="i-tag" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 12.5L12.5 20a2 2 0 01-2.8 0L3 13.3V4h9.3L20 11.7a.6.6 0 010 .8z"/><circle cx="8" cy="9" r="1.4"/></symbol>
  <symbol id="i-clock" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol>
  <symbol id="i-calendar" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 9h18M8 3v4M16 3v4"/></symbol>
  <symbol id="i-check" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></symbol>
  <symbol id="i-checks" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="2 13 7 18 13 8"/><polyline points="11 13 16 18 22 8"/></symbol>
  <symbol id="i-edit" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9M16.5 3.5a2.1 2.1 0 113 3L7 19l-4 1 1-4z"/></symbol>
  <symbol id="i-chart" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3v18h18"/><path d="M7 16l4-4 3 3 5-7"/></symbol>
  <symbol id="i-book" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4.5A2.5 2.5 0 016.5 2H20v17H6.5A2.5 2.5 0 014 21.5v-17z"/><path d="M4 19.5h16"/></symbol>
  <symbol id="i-lock" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V8a4 4 0 018 0v3"/></symbol>
  <symbol id="i-globe" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 010 18M12 3a14 14 0 000 18"/></symbol>
  <symbol id="i-building" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21V8l9-5 9 5v13"/><path d="M3 21h18M9 12h6M9 16h6M9 21v-5h6v5"/></symbol>
  <symbol id="i-flag" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 21V4M5 4h13l-3 4 3 4H5"/></symbol>
  <symbol id="i-library" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 21V5l4-2 4 2 4-2 4 2v16M4 21h16M9 7v14M15 7v14"/></symbol>
  <symbol id="i-quote" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 7h4v4a4 4 0 01-4 4M14 7h4v4a4 4 0 01-4 4"/></symbol>
  <symbol id="i-arrow-right" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
</svg>
""".strip()


NAV_GROUPS = [
    ("library", "i-library", "资料库", [("/", "首页"), ("/docs", "全部文档"), ("/timeline", "年表"), ("/glossary", "术语表")]),
    ("workbench", "i-edit", "研究工作台", [("/tasks", "校订任务"), ("/quality", "质量检查"), ("/dashboard", "进度仪表盘")]),
    ("topics", "i-tag", "专题与人物", [("/topics", "专题"), ("/people", "人物"), ("/events/key", "关键事件"), ("/places", "地点"), ("/organizations", "机构"), ("/events", "事件线索")]),
]


def nav_active(path: str) -> str:
    """根据当前 path 推断激活的主导航分组。"""
    if path in ("/", "/focus"):
        return "library"
    for group_key, _, _, items in NAV_GROUPS:
        for href, _ in items:
            if path == href or (href != "/" and path.startswith(href + "/")):
                return group_key
    if path.startswith("/doc/") or path.startswith("/cite/"):
        return "library"
    if path.startswith("/review/"):
        return "workbench"
    if path.startswith(("/people/", "/places/", "/organizations/", "/topics/")):
        return "topics"
    return ""


def layout(title: str, body: str, query: str = "", active_path: str = "") -> bytes:
    # 优先使用调用方明确传的 active_path；否则从 thread-local 取（do_GET 设置）
    if not active_path:
        active_path = getattr(_request, "path", "/") or "/"
    active_group = nav_active(active_path)
    nav_html = ""
    for group_key, icon_id, group_label, items in NAV_GROUPS:
        is_active = group_key == active_group
        cls = "nav-group active" if is_active else "nav-group"
        sub = "".join(
            f'<a class="nav-sub{" current" if href == active_path else ""}" href="{href}">{h(label)}</a>'
            for href, label in items
        )
        nav_html += f'''
        <div class="{cls}">
          <button class="nav-main"><svg class="ico"><use href="#{icon_id}"/></svg>{h(group_label)}</button>
          <div class="nav-flyout">{sub}</div>
        </div>'''
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{h(title)} · 民盟历史文献研究库</title>
  <style>
    :root {{
      --bg: #f3eee2;
      --bg-paper: #fdfbf6;
      --panel: #ffffff;
      --panel-warm: #fbf7ee;
      --line: #d9d2bf;
      --line-soft: #ece6d6;
      --text: #2a2820;
      --muted: #6b6356;
      --muted-soft: #918979;
      --accent: #0f6b5b;
      --accent-deep: #0a4a3f;
      --accent-soft: #d8ebe4;
      --accent-ink: #ffffff;
      --archival: #8b5e34;
      --archival-soft: #f0e3d4;
      --warn: #a86b1a;
      --warn-soft: #fbecd0;
      --mark: #ffeea0;
      --shadow-sm: 0 1px 2px rgba(60, 50, 30, 0.05);
      --shadow-md: 0 4px 12px rgba(60, 50, 30, 0.07);
      --shadow-lg: 0 8px 24px rgba(60, 50, 30, 0.10);
      --serif: "Source Han Serif SC", "Noto Serif CJK SC", "STSongti SC", "Songti SC", "STSong", SimSun, "Source Serif Pro", "EB Garamond", Cambria, Georgia, serif;
      --sans: "Source Han Sans SC", "Noto Sans CJK SC", "PingFang SC", -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", "Hiragino Sans GB", sans-serif;
      --mono: ui-monospace, SFMono-Regular, "JetBrains Mono", "Cascadia Code", Menlo, Consolas, monospace;
    }}
    * {{ box-sizing: border-box; }}
    html {{ height: 100%; scroll-behavior: smooth; }}
    body {{
      margin: 0;
      min-height: 100vh;
      display: flex; flex-direction: column;
      background: var(--bg);
      color: var(--text);
      font: 15.5px/1.7 var(--sans);
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }}
    main {{ flex: 1; }}
    a {{ color: var(--accent); text-decoration: none; transition: color 0.15s; }}
    a:hover {{ text-decoration: underline; text-underline-offset: 3px; }}
    h1, h2, h3, h4 {{ font-family: var(--serif); font-weight: 600; letter-spacing: 0.01em; }}
    h1 {{ font-size: 28px; line-height: 1.3; margin: 0 0 14px; }}
    h2 {{ font-size: 20px; line-height: 1.35; margin: 0 0 12px; }}
    h3 {{ font-size: 17px; line-height: 1.4; margin: 0 0 8px; }}
    .ico {{ width: 16px; height: 16px; flex: 0 0 16px; vertical-align: -3px; stroke: currentColor; }}
    .ico-lg {{ width: 22px; height: 22px; flex: 0 0 22px; }}
    /* 聚焦可见性 */
    :focus-visible {{ outline: 2px solid var(--accent); outline-offset: 2px; border-radius: 4px; }}
    /* 入场动画 */
    @keyframes fadeInUp {{
      from {{ opacity: 0; transform: translateY(12px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    .fade-in {{ animation: fadeInUp 0.4s ease-out both; }}

    /* === Topbar === */
    .topbar {{
      position: sticky; top: 0; z-index: 50;
      display: grid;
      grid-template-columns: minmax(220px, auto) minmax(260px, 1fr) auto;
      gap: 22px; align-items: center;
      padding: 14px 28px;
      background: rgba(253, 251, 246, 0.94);
      backdrop-filter: saturate(140%) blur(8px);
      border-bottom: 1px solid var(--line);
    }}
    .brand {{
      display: flex; align-items: baseline; gap: 10px;
      font-family: var(--serif); font-weight: 600; font-size: 18px; color: var(--text);
      white-space: nowrap;
    }}
    .brand .brand-mark {{ color: var(--accent); font-size: 22px; line-height: 1; }}
    .brand .brand-sub {{ font-size: 12px; color: var(--muted); font-family: var(--sans); font-weight: 400; letter-spacing: 0.05em; }}
    .brand:hover {{ text-decoration: none; }}
    .brand:hover span:first-child {{ color: var(--accent-deep); }}
    .search {{ display: flex; min-width: 0; max-width: 540px; }}
    .search input {{
      width: 100%; min-width: 0;
      border: 1px solid var(--line); border-right: 0;
      border-radius: 6px 0 0 6px;
      padding: 9px 14px;
      font: 14px var(--sans);
      background: var(--bg-paper);
      color: var(--text);
      transition: border-color 0.2s, box-shadow 0.2s;
    }}
    .search input::placeholder {{ color: var(--muted-soft); }}
    .search input:focus {{ outline: none; border-color: var(--accent); box-shadow: 0 0 0 3px rgba(15, 107, 91, 0.08); }}
    .search button {{
      min-width: 76px;
      border: 1px solid var(--accent);
      border-radius: 0 6px 6px 0;
      padding: 0 16px;
      background: var(--accent); color: var(--accent-ink);
      font: 14px var(--sans);
      cursor: pointer;
      display: inline-flex; align-items: center; gap: 6px;
      transition: background 0.2s, transform 0.1s;
    }}
    .search button:hover {{ background: var(--accent-deep); }}
    .search button:active {{ transform: scale(0.97); }}

    /* === Nav === */
    nav.mainnav {{ display: flex; gap: 4px; align-items: center; }}
    .nav-group {{ position: relative; }}
    .nav-main {{
      display: inline-flex; align-items: center; gap: 6px;
      padding: 8px 14px; border-radius: 6px;
      background: transparent; border: 1px solid transparent;
      color: var(--muted); font: 14px var(--sans);
      cursor: pointer;
    }}
    .nav-main:hover {{ background: var(--panel-warm); color: var(--text); }}
    .nav-group.active .nav-main {{ background: var(--accent-soft); color: var(--accent-deep); border-color: rgba(15, 107, 91, 0.25); }}
    .nav-flyout {{
      position: absolute; top: 100%; right: 0;
      min-width: 160px; padding: 6px;
      padding-top: 12px;   /* 6px 视觉间距 + 6px 内容间距 */
      background: transparent;
      display: none; flex-direction: column;
      z-index: 100;
    }}
    .nav-flyout::before {{
      /* 透明桥：覆盖按钮与菜单之间的间隙，防止 hover 中断 */
      content: ""; position: absolute; top: 0; left: 0; right: 0; height: 6px;
    }}
    .nav-flyout::after {{
      /* 实际可见的菜单背景 */
      content: ""; position: absolute; top: 6px; left: 0; right: 0; bottom: 0;
      background: var(--panel); border: 1px solid var(--line);
      border-radius: 8px; box-shadow: var(--shadow-md);
      z-index: -1;
    }}
    .nav-group:hover .nav-flyout {{ display: flex; }}
    .nav-sub {{
      padding: 7px 12px; border-radius: 5px;
      color: var(--text); font: 14px var(--sans);
    }}
    .nav-sub:hover {{ background: var(--panel-warm); text-decoration: none; }}
    .nav-sub.current {{ background: var(--accent-soft); color: var(--accent-deep); font-weight: 500; }}

    main {{ padding: 28px 32px; max-width: 1320px; margin: 0 auto; }}
    /* === 封面区（首页） === */
    .hero {{
      background: linear-gradient(180deg, var(--bg-paper) 0%, var(--panel-warm) 100%);
      border: 1px solid var(--line);
      border-radius: 12px;
      padding: 36px 40px 32px;
      margin-bottom: 28px;
      box-shadow: var(--shadow-sm);
      position: relative;
      overflow: hidden;
    }}
    .hero::before {{
      content: "";
      position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, var(--accent) 0%, var(--archival) 50%, var(--accent-deep) 100%);
    }}
    .hero h1 {{
      font-size: 32px; line-height: 1.25;
      margin: 0 0 10px;
      color: var(--text);
    }}
    .hero .hero-sub {{
      font-family: var(--serif);
      color: var(--muted);
      font-size: 16px;
      margin: 0 0 22px;
      line-height: 1.7;
      max-width: 720px;
    }}
    .hero .hero-meta {{
      display: flex; flex-wrap: wrap; gap: 18px;
      font-size: 13px; color: var(--muted);
      padding-top: 18px;
      border-top: 1px dashed var(--line);
    }}
    .hero .hero-meta b {{ color: var(--accent-deep); font-weight: 600; }}
    .hero .hero-meta span {{
      transition: transform 0.2s;
    }}
    .hero .hero-meta span:hover {{
      transform: translateY(-1px);
    }}

    /* === Section 标题 === */
    .section-head {{
      display: flex; align-items: baseline; justify-content: space-between;
      margin: 32px 0 14px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--line-soft);
    }}
    .section-head h2 {{
      margin: 0;
      display: inline-flex; align-items: center; gap: 8px;
    }}
    .section-head .ico {{ color: var(--accent); }}
    .section-head .more {{ font-size: 13px; color: var(--muted); }}
    .section-head .more:hover {{ color: var(--accent); }}

    /* === Stats === */
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 1px;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--line);
      margin-bottom: 22px;
    }}
    .stat {{
      background: var(--panel);
      padding: 16px 18px;
      transition: background 0.2s, transform 0.2s;
    }}
    .stat:hover {{ background: var(--bg-paper); transform: scale(1.02); }}
    .stat strong {{
      display: block;
      font-family: var(--serif);
      font-size: 26px; font-weight: 600; line-height: 1.1;
      color: var(--accent-deep);
      margin-bottom: 4px;
      transition: color 0.2s;
    }}
    .stat:hover strong {{ color: var(--accent); }}
    .stat span {{ color: var(--muted); font-size: 12.5px; letter-spacing: 0.02em; }}

    /* === 平台卡片 === */
    .platforms {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
      gap: 14px;
      margin-bottom: 8px;
    }}
    .platform-card {{
      position: relative;
      display: block;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px 18px 16px;
      color: var(--text);
      transition: transform 0.25s ease, border-color 0.2s, box-shadow 0.25s ease;
      overflow: hidden;
    }}
    .platform-card::before {{
      content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px;
      background: var(--line);
      transition: background 0.2s, width 0.25s ease;
    }}
    .platform-card:hover {{
      border-color: var(--accent);
      box-shadow: var(--shadow-lg);
      transform: translateY(-3px);
      text-decoration: none;
    }}
    .platform-card:hover::before {{ background: var(--accent); width: 5px; }}
    .platform-card.active::before {{ background: var(--accent); }}
    .platform-card.upcoming {{ opacity: 0.7; background: var(--panel-warm); }}
    .platform-card.upcoming::before {{ background: var(--archival); }}
    .platform-card .phead {{ display: flex; align-items: center; gap: 10px; margin-bottom: 4px; }}
    .platform-card .phead svg {{ width: 22px; height: 22px; color: var(--accent); flex-shrink: 0; }}
    .platform-card.upcoming .phead svg {{ color: var(--archival); }}
    .platform-card h3 {{ margin: 0; font-size: 16.5px; font-family: var(--serif); }}
    .platform-card .pmeta {{ color: var(--muted); font-size: 12.5px; margin: 0 0 8px 32px; font-family: var(--serif); font-style: italic; }}
    .platform-card .pdesc {{ font-size: 13.5px; line-height: 1.65; color: var(--text); margin-top: 6px; }}
    .platform-card .pstatus {{
      display: inline-flex; align-items: center; gap: 4px;
      padding: 3px 9px; border-radius: 4px;
      font-size: 11.5px; font-weight: 500; margin-top: 12px;
      letter-spacing: 0.02em;
    }}
    .platform-card .pstatus.ok {{
      background: var(--accent-soft);
      color: var(--accent-deep);
      border: 1px solid rgba(15, 107, 91, 0.25);
    }}
    .platform-card .pstatus.todo {{ background: var(--archival-soft); color: var(--archival); }}
    /* === 文献条目列表 === */
    .result-list {{
      border: 1px solid var(--line);
      border-radius: 10px;
      overflow: hidden;
      background: var(--panel);
      box-shadow: var(--shadow-sm);
    }}
    .result {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 160px;
      gap: 18px;
      padding: 18px 22px;
      border-top: 1px solid var(--line-soft);
      transition: background 0.15s, padding-left 0.2s;
    }}
    .result:first-child {{ border-top: 0; }}
    .result:hover {{ background: var(--bg-paper); padding-left: 26px; }}
    .result h2 {{
      margin: 0 0 6px;
      font-size: 16.5px; line-height: 1.4;
      font-family: var(--serif); font-weight: 600;
    }}
    .title-en {{
      margin: -2px 0 8px;
      color: var(--muted);
      font-size: 13px; line-height: 1.45;
      font-family: var(--serif); font-style: italic;
    }}
    .meta {{ color: var(--muted); font-size: 13px; }}
    .snippet {{ margin-top: 10px; color: var(--text); font-size: 14px; line-height: 1.7; }}
    .zh {{
      margin-top: 10px;
      padding: 10px 14px;
      background: var(--bg-paper);
      border-left: 3px solid var(--accent-soft);
      color: var(--text); font-size: 14px; line-height: 1.75;
      border-radius: 0 4px 4px 0;
    }}
    .zh.empty {{ color: var(--muted); font-style: italic; background: transparent; border-left-color: var(--line); }}
    .tagline {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; align-items: center; }}
    .tag {{
      border: 1px solid var(--line);
      border-radius: 999px;
      padding: 2px 9px;
      font-size: 12px; color: var(--muted);
      background: var(--bg-paper);
    }}
    .grade {{
      display: inline-flex; align-items: center; gap: 4px;
      border-radius: 4px;
      padding: 3px 9px;
      font-size: 12px; font-weight: 500;
      background: var(--accent-soft);
      color: var(--accent-deep);
      border: 1px solid rgba(15, 107, 91, 0.2);
    }}
    .grade.context {{ background: var(--archival-soft); color: var(--archival); border-color: rgba(139, 94, 52, 0.25); }}
    .issue {{
      display: inline-flex; align-items: center; gap: 4px;
      border-radius: 4px;
      padding: 3px 9px;
      font-size: 12px; font-weight: 500;
      border: 1px solid rgba(168, 107, 26, 0.3);
      color: var(--warn); background: var(--warn-soft);
    }}
    .issue.high {{
      border-color: rgba(168, 50, 32, 0.35);
      color: #8a2d1f;
      background: #fbe3df;
    }}
    .cite {{
      text-align: right;
      font-size: 13px;
      color: var(--muted);
      font-family: var(--serif);
    }}
    .cite a {{ display: block; padding: 2px 0; }}
    .doc-head {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 18px;
      align-items: start;
      padding: 22px 24px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel);
      margin-bottom: 20px;
      scroll-margin-top: 82px;
      box-shadow: var(--shadow-sm);
    }}
    .doc-head h1 {{ margin: 0 0 6px; font-size: 22px; line-height: 1.35; font-family: var(--serif); }}
    .doc-tools {{ display: flex; gap: 8px; flex-wrap: wrap; justify-content: flex-end; }}
    .button {{
      display: inline-flex; align-items: center; gap: 5px;
      min-height: 34px;
      padding: 6px 12px;
      border: 1px solid var(--line);
      border-radius: 6px;
      background: var(--panel);
      color: var(--text);
      font: 13px var(--sans);
      transition: all 0.12s;
    }}
    .button:hover {{ border-color: var(--accent); color: var(--accent); text-decoration: none; }}
    .button.active {{
      border-color: var(--accent);
      color: var(--accent-deep);
      background: var(--accent-soft);
      font-weight: 500;
    }}
    .filters {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 0 0 18px;
      padding: 12px 14px;
      background: var(--panel-warm);
      border: 1px solid var(--line-soft);
      border-radius: 8px;
    }}
    .reader {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
    }}
    .segment {{ display: contents; }}
    .pane {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel);
      min-width: 0;
      scroll-margin-top: 76px;
      box-shadow: var(--shadow-sm);
    }}
    .pane-head {{
      display: flex;
      justify-content: space-between;
      gap: 10px;
      padding: 12px 16px;
      border-bottom: 1px solid var(--line-soft);
      color: var(--muted);
      font: 13px var(--serif);
      font-style: italic;
      background: var(--panel-warm);
      border-radius: 10px 10px 0 0;
    }}
    .pane-body {{
      padding: 18px 20px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      font-size: 15px; line-height: 1.85;
    }}
    /* 中文译文区用衬线，呼应学术阅读体例 */
    .pane.zh-pane .pane-body {{ font-family: var(--serif); }}
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
    mark {{ background: var(--mark); padding: 0 3px; border-radius: 2px; }}
    .notice {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: var(--panel);
      padding: 18px 22px;
      color: var(--muted);
      font: 14px var(--sans);
    }}
    .notice.archival {{
      background: var(--panel-warm);
      border-color: var(--archival-soft);
      color: var(--text);
    }}
    /* 学术引用块 */
    blockquote, .quote {{
      font-family: var(--serif);
      font-style: italic;
      color: var(--text);
      border-left: 3px solid var(--archival);
      padding: 6px 18px;
      margin: 14px 0;
      background: var(--panel-warm);
      border-radius: 0 4px 4px 0;
    }}
    /* 长文阅读优化：限制行宽 */
    .reader-doc {{ max-width: 760px; margin: 0 auto; font-family: var(--serif); font-size: 16px; line-height: 1.9; }}

    /* === 学术元数据卡 === */
    .meta-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 18px 22px;
      margin-bottom: 22px;
      box-shadow: var(--shadow-sm);
    }}

    /* === CIA 档案专属版式（情报蓝色调，与 FRUS 外交褐区分）=== */
    .doc-head.cia-doc {{
      border-left: 4px solid #1f4d7a;
      background: linear-gradient(90deg, rgba(31, 77, 122, 0.045), var(--panel) 35%);
    }}
    .meta-card.cia-cite {{
      border-color: rgba(31, 77, 122, 0.35);
      background: rgba(31, 77, 122, 0.025);
    }}
    .meta-card.cia-cite .meta-card-head h3,
    .meta-card.cia-cite .meta-card-head .ico {{ color: #1f4d7a; }}
    .src-badge {{
      display: inline-flex; align-items: center; gap: 4px;
      padding: 2px 9px; border-radius: 4px;
      font-size: 12px; font-weight: 500;
      vertical-align: 2px;
      letter-spacing: 0.04em;
    }}
    .src-badge .ico {{ width: 13px; height: 13px; }}
    .src-badge.cia {{
      background: #1f4d7a; color: #ffffff;
    }}
    .cia-ocr-notice {{
      border-left: 3px solid #1f4d7a !important;
      background: rgba(31, 77, 122, 0.04) !important;
      font-size: 13.5px;
      color: var(--muted);
    }}
    .cia-ocr-notice .ico {{ color: #1f4d7a; vertical-align: -2px; margin-right: 4px; }}
    .cia-ocr-notice a {{ color: #1f4d7a; }}

    /* FRUS 来源徽章（外交褐配色，与 CIA 蓝徽章呼应）*/
    .src-badge.frus {{
      background: var(--archival); color: #ffffff;
    }}

    /* === 年表月度密度热力图 === */
    .density-card {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 10px;
      padding: 14px 18px;
      margin-bottom: 22px;
      box-shadow: var(--shadow-sm);
    }}
    .density-title {{
      font-size: 13px;
      color: var(--muted);
      margin-bottom: 8px;
      letter-spacing: 0.04em;
    }}
    .density-grid {{
      display: flex;
      flex-direction: column;
      gap: 2px;
      font-family: var(--mono);
      font-size: 11px;
    }}
    .density-row {{
      display: grid;
      grid-template-columns: 56px repeat(12, 1fr);
      gap: 2px;
    }}
    .density-cell {{
      min-height: 22px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 3px;
      text-decoration: none;
      color: var(--text);
      font-size: 11px;
    }}
    .density-axis {{
      color: var(--muted-soft);
      background: transparent;
      font-size: 10.5px;
    }}
    .density-ylabel {{
      justify-content: flex-end;
      padding-right: 6px;
    }}
    .density-mlabel {{
      font-weight: 500;
    }}
    .density-empty {{
      background: #f0eee8;
    }}
    .density-hot {{
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }}
    .density-hot:hover {{
      outline: 2px solid var(--accent-deep);
      outline-offset: -1px;
      text-decoration: none;
    }}
    .tl-year {{
      scroll-margin-top: 20px;
    }}

    /* === 关键事件页 对比视图（FRUS↔CIA 并排）=== */
    .compare-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      margin-top: 12px;
    }}
    .compare-col {{
      min-width: 0;
    }}
    .compare-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      padding: 10px 14px;
      margin-bottom: 8px;
      background: var(--panel-warm);
      border-radius: 6px;
      border-left: 3px solid var(--line);
    }}
    .compare-col:first-child .compare-head {{ border-left-color: var(--archival); }}
    .compare-col:last-child .compare-head {{ border-left-color: #1f4d7a; }}
    .compare-list .result {{ font-size: 14px; }}
    .compare-list .result .pane-body,
    .compare-list .result .snippet,
    .compare-list .result .zh {{ font-size: 13.5px; }}
    /* 窄屏退化为单列 */
    @media (max-width: 1100px) {{
      .compare-grid {{ grid-template-columns: 1fr; }}
    }}
    /* button.active 高亮 */
    .button.active {{
      background: var(--accent);
      color: var(--accent-ink);
      border-color: var(--accent-deep);
    }}
    .meta-card-head {{
      display: flex; align-items: center; justify-content: space-between;
      gap: 12px; flex-wrap: wrap;
      margin-bottom: 12px;
    }}
    .meta-card-head h3 {{
      margin: 0;
      display: inline-flex; align-items: center; gap: 8px;
      color: var(--archival);
    }}
    .meta-card-head .ico {{ color: var(--archival); }}
    .cite-tabs {{ display: flex; gap: 6px; align-items: center; flex-wrap: wrap; }}
    .cite-tab {{
      border: 1px solid var(--line); background: var(--bg-paper);
      padding: 5px 12px; border-radius: 5px;
      font: 13px var(--sans); color: var(--muted);
      cursor: pointer;
    }}
    .cite-tab:hover {{ color: var(--archival); border-color: var(--archival); }}
    .cite-tab.active {{ background: var(--archival-soft); color: var(--archival); border-color: var(--archival); font-weight: 500; }}
    .cite-content {{
      font-family: var(--mono);
      font-size: 13px; line-height: 1.7;
      background: var(--bg-paper);
      border: 1px solid var(--line-soft);
      border-radius: 6px;
      padding: 14px 16px;
      margin: 0 0 12px;
      color: var(--text);
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-word;
    }}
    .meta-card-foot {{
      display: flex; flex-wrap: wrap; gap: 18px;
      padding-top: 12px;
      border-top: 1px dashed var(--line-soft);
      font-size: 13px; color: var(--muted);
    }}
    .meta-card-foot strong {{ color: var(--text); font-weight: 500; margin-right: 4px; }}

    /* === 面包屑 === */
    .breadcrumb {{
      display: flex; align-items: center; flex-wrap: wrap;
      gap: 8px;
      font-size: 13px; color: var(--muted);
      margin-bottom: 16px;
      font-family: var(--serif);
    }}
    .breadcrumb a {{ color: var(--muted); }}
    .breadcrumb a:hover {{ color: var(--accent); }}
    .breadcrumb .sep {{ color: var(--muted-soft); }}
    .breadcrumb .current {{ color: var(--text); }}

    /* === 术语表 === */
    .glossary-letters {{
      display: flex; flex-wrap: wrap; gap: 6px;
      margin-bottom: 22px;
      padding: 14px 18px;
      background: var(--panel-warm);
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      position: sticky; top: 80px; z-index: 5;
    }}
    .glossary-letters a {{
      display: inline-flex; align-items: center; justify-content: center;
      width: 30px; height: 30px;
      border-radius: 4px;
      color: var(--accent-deep);
      font-family: var(--serif); font-weight: 600;
      transition: all 0.12s;
    }}
    .glossary-letters a:hover {{ background: var(--accent-soft); text-decoration: none; }}
    .glossary-letters a.disabled {{ color: var(--muted-soft); pointer-events: none; }}
    .glossary-section {{ margin-bottom: 26px; scroll-margin-top: 140px; }}
    .glossary-section h2 {{
      font-size: 22px; color: var(--archival);
      border-bottom: 2px solid var(--archival-soft);
      padding-bottom: 6px; margin-bottom: 12px;
    }}
    .glossary-table {{
      width: 100%; border-collapse: collapse;
      background: var(--panel);
      border: 1px solid var(--line-soft); border-radius: 8px;
      overflow: hidden;
    }}
    .glossary-table th, .glossary-table td {{
      padding: 10px 14px; text-align: left;
      border-bottom: 1px solid var(--line-soft);
      font-size: 14px;
    }}
    .glossary-table th {{
      background: var(--panel-warm); color: var(--muted);
      font-family: var(--serif); font-weight: 500;
      font-size: 13px; letter-spacing: 0.04em;
    }}
    .glossary-table tr:last-child td {{ border-bottom: 0; }}
    .glossary-table .term {{ font-family: var(--serif); font-style: italic; color: var(--text); }}
    .glossary-table .zh-term {{ font-weight: 500; color: var(--accent-deep); }}
    .glossary-table .note {{ color: var(--muted); font-size: 13px; }}
    .glossary-table .lookup {{ font-size: 12px; }}

    @media (max-width: 980px) {{
      .topbar {{ grid-template-columns: 1fr; gap: 12px; padding: 12px 18px; }}
      nav.mainnav {{ overflow-x: auto; padding-bottom: 4px; }}
      main {{ padding: 18px 16px; }}
      .stats {{ grid-template-columns: repeat(2, minmax(120px, 1fr)); }}
      .result {{ grid-template-columns: 1fr; padding: 16px 18px; }}
      .cite {{ text-align: left; padding-top: 10px; border-top: 1px dashed var(--line-soft); }}
      .doc-head {{ grid-template-columns: 1fr; padding: 18px; }}
      .doc-tools {{ justify-content: flex-start; }}
      .reader {{ grid-template-columns: 1fr; }}
      .hero {{ padding: 24px 22px; }}
      .hero h1 {{ font-size: 24px; }}
      .footer-inner {{ grid-template-columns: 1fr; gap: 18px; }}
      .footer-meta {{ text-align: left; }}
    }}
    @media (max-width: 540px) {{
      .stats {{ grid-template-columns: 1fr 1fr; }}
      .platforms {{ grid-template-columns: 1fr; }}
    }}

    /* === 页尾 === */
    .site-footer {{
      margin-top: 48px;
      padding: 32px 28px 28px;
      background: linear-gradient(180deg, var(--bg) 0%, #ece6d6 100%);
      border-top: 1px solid var(--line);
    }}
    .footer-inner {{
      max-width: 1320px; margin: 0 auto;
      display: grid;
      grid-template-columns: 1fr auto auto;
      gap: 32px;
      align-items: start;
    }}
    .footer-title {{
      font-family: var(--serif); font-weight: 600;
      font-size: 15px; color: var(--text);
      display: block; margin-bottom: 4px;
    }}
    .footer-desc {{
      font-size: 12.5px; color: var(--muted);
      line-height: 1.6;
    }}
    .footer-links {{
      display: flex; flex-direction: column; gap: 6px;
    }}
    .footer-links a {{
      font-size: 13px; color: var(--muted);
      transition: color 0.15s;
    }}
    .footer-links a:hover {{ color: var(--accent); text-decoration: none; }}
    .footer-meta {{
      font-size: 11.5px; color: var(--muted-soft);
      line-height: 1.7;
      text-align: right;
    }}
  </style>
</head>
<body>
  {ICONS_SVG}
  <header class="topbar">
    <a class="brand" href="/">
      <span>民盟历史文献研究库</span>
      <span class="brand-sub">FRUS / Wilson / CIA</span>
    </a>
    <form class="search" method="get" action="/search" role="search">
      <input name="q" value="{h(query)}" placeholder="搜索英文原文或中文译文，例如「罗隆基」「Marshall」「政协」">
      <button type="submit"><svg class="ico"><use href="#i-search"/></svg>搜索</button>
    </form>
    <nav class="mainnav">
      {nav_html}
    </nav>
  </header>
  <main>{body}</main>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-brand">
        <span class="footer-title">民盟历史文献研究库</span>
        <span class="footer-desc">系统整理 1941–1950 年代海外档案中关于中国民主同盟的一手史料</span>
      </div>
      <div class="footer-links">
        <a href="/">首页</a>
        <a href="/docs">全部文档</a>
        <a href="/people">人物索引</a>
        <a href="/timeline">文献年表</a>
        <a href="/dashboard">研究仪表盘</a>
      </div>
      <div class="footer-meta">
        数据来源：FRUS · Wilson Center · CIA FOIA<br>
        本站为学术研究工具，所有档案均保留原始出处引用
      </div>
    </div>
  </footer>
</body>
</html>""".encode("utf-8")


PLATFORM_META = {
    "frus": {
        "name": "FRUS",
        "long_name": "Foreign Relations of the United States",
        "cn_name": "《美国对外关系文件集》",
        "subtitle": "美国对外关系文件集 1941-1950 中国卷",
        "intro": "美国国务院公开编辑、按外交决策线索精选的官方文献年鉴。1861 年至今由 Office of the Historian 主持，是研究美国外交史最权威的一手史料丛书。本平台聚焦其 1941-1950 年中国卷册中与民盟相关的部分。",
        "perspective": "美方驻华外交官视角 —— 大使馆/领事馆给国务院的报告 + 马歇尔来华使团与民盟领袖的会谈记录",
        "coverage": "1941.3 民盟成立 — 1947.10 民盟被取缔 — 1949.10 新中国成立 — 1950 内战收尾",
        "highlights": [
            "马歇尔与张澜、罗隆基、张君劢、周恩来等的逐字会谈记录",
            "司徒雷登大使关于民盟政治处境的连续报告（特别是 1947 取缔前后）",
            "罗隆基 1947.10.28 在使馆软禁期间的亲历对话备忘录（page 316）",
            "张君劢 1947.11.1 致马歇尔函（page 333）—— 民盟取缔后第 5 天的民盟人士陈情",
            "12 位民盟政协代表 1946 联名声明（page 228）",
        ],
        "status": None,
        "status_class": "ok",
        "active": True,
    },
    "wilson": {
        "name": "Wilson Center",
        "long_name": "Wilson Center Digital Archive",
        "cn_name": "威尔逊中心数字档案",
        "subtitle": "数字伍德罗·威尔逊中心档案",
        "intro": "美国伍德罗·威尔逊国际学者中心（Woodrow Wilson International Center for Scholars）建立的数字档案，聚焦冷战及国际关系一手史料。最大特点是收录大量来自苏联档案、东欧档案、中国共产党档案的解密文件。",
        "perspective": "苏联档案 + 中共内部档案 + 东欧档案视角 —— FRUS 美方视角不可替代的「另一面」",
        "coverage": "1945-1950 中共与苏联高层互动 / 1949 米高扬西柏坡密访 / 1949.7 刘少奇访苏 / 苏联驻华大使彼得罗夫、罗申会谈记录",
        "highlights": [
            "米高扬访华回忆录（1949.1.31 - 2.7 西柏坡密访）⭐⭐⭐",
            "刘少奇 ↔ 斯大林会谈备忘录（1949 年 7 月访苏，中苏分工框架）⭐⭐⭐",
            "民主党派与政协预备委员会（苏联档案分类下的民盟代表人物名单）",
            "彼得罗夫大使 ↔ 周恩来 / 毛泽东 / 王若飞 多次会谈",
            "毛泽东、刘少奇、科瓦廖夫、斯大林之间 1949 年建政前后密电",
            "罗申大使 ↔ 周恩来 1949.11.10 会谈记录",
        ],
        "status": None,
        "status_class": "ok",
        "active": True,
        "todo_note": "",
    },
    "cia": {
        "name": "CIA FOIA",
        "long_name": "CIA FOIA Reading Room",
        "cn_name": "美国中央情报局已解密文件阅览室",
        "subtitle": "美国中央情报局已解密文件（archive.org 镜像）",
        "intro": "美国中央情报局根据《信息自由法》（FOIA）公开的已解密文件全文检索系统，本平台通过 archive.org 的 ciareadingroom collection 镜像获取一手 PDF 与 OCR 文本。",
        "perspective": "美方情报系统视角 —— 与 FRUS 外交部门视角形成互补",
        "coverage": "1946-1954 民盟相关档案 21 篇（核心专题）",
        "highlights": [
            "1949-05-23 CHINA DEMOCRATIC LEAGUE MEMBERS' ESCAPE FROM SHANGHAI（民盟成员上海撤离香港）",
            "1949-12-20 LO LUNG-CHI（罗隆基专档）",
            "1950-04-04 CHANG LAN（张澜专档）",
            "1950-07-12 LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE（民盟领导成员名单）",
            "1950-11-09 ROLE OF NON-COMMUNIST POLITICAL PARTIES IN PEIPING（第三方面政党在北平的作用）",
            "1954-09-16 ROSTER OF PRESIDIUM OF FIRST CONGRESS（一届人大主席团名单）",
        ],
        "status": None,
        "status_class": "ok",
        "active": True,
        "todo_note": "",
    },
    "hoover": {
        "name": "Hoover Institution",
        "long_name": "Hoover Institution Library & Archives",
        "cn_name": "斯坦福大学胡佛档案馆",
        "subtitle": "胡佛档案馆 · 现场调档实物拍照",
        "intro": "斯坦福大学胡佛研究所档案馆收藏 20 世纪重要政治、外交人物的私人卷宗。本卡片下的资料系研究者亲赴斯坦福现场调阅原件、实物拍照后整理成 PDF 入库，并非公网下载。",
        "perspective": "人物个人卷宗视角 —— 私人通信、未刊文稿、信件原件等无法从公网获得的一手实物",
        "coverage": "张君劢档案（Carsun Chang Papers, 1946-1962, 2 oversize boxes）—— 联合政府前景、军事改编协议、与第三方面联络通信等",
        "highlights": [
            "Carsun Chang Papers（张君劢档案）· 1946-1962 · 2 oversize boxes · 现场调档实物",
            "民盟筹建期、政协会议期间张君劢与第三方面人物私人通信",
            "1946-1947 联合政府讨论手稿与未刊文献",
        ],
        "status": "现场调档 · 实物拍照入库",
        "status_class": "active",
        "active": True,
        "todo_note": "区别于公网批量抓取——所有资料系研究者赴斯坦福现场调阅、拍照、整理为 PDF 后入库。下一步：扫描件 OCR + 翻译 + 入库。",
    },
    "hathitrust": {
        "name": "HathiTrust / IA",
        "long_name": "HathiTrust / Internet Archive",
        "cn_name": "数字图书馆联盟",
        "subtitle": "公开出版一手资料 / 当时报刊",
        "intro": "HathiTrust 由美国大学图书馆联盟建立的数字图书馆；Internet Archive 是开放的全球数字资源平台。本平台已接入 1946-1949 香港英文报纸（China Mail / Hong Kong Telegraph）对民盟事件的当时报道，构成完整的港媒时间序列。",
        "perspective": "1940s 香港英文报刊视角 —— 民盟从政协参与、国大缺席、被宣布「非法」到响应五一口号、张澜软禁的当时舆论现场记录",
        "coverage": "1946-1949 香港 China Mail / Hong Kong Telegraph 共 42 期，覆盖民盟史关键节点：1946 政协会议 → 1946 国民大会 → 1947 联合政府讨论 → 1947 民盟「非法」 → 1948 民盟香港一届三中全会 → 1948 响应五一口号 → 1949 张澜上海软禁 → 1949 解放战争南下",
        "highlights": [
            "1946-01-11 / 01-28 / 01-29 / 02-01 / 02-26 China Mail：政协会议召开期间到决议落幕（共 5 期连续追踪）",
            "1946-08-23 / 10-22 / 10-30 / 11-26 / 11-27 港媒:张澜动向 + 第三方面对国民大会的拒绝立场",
            "1947-03-10 / 03-24 / 04-14 / 04-26 / 05-26 / 06-05 / 06-19 / 06-27 / 07-31 China Mail：1947 上半年联合政府讨论、政府改组、学生运动到内战全面化（9 期高密度报道）",
            "1947-08-04 / 08-29 港媒：内战阶段民盟动向",
            "1947-10-06 / 10-24 / 10-29 / 10-30 / 11-05 China Mail：民盟被宣布「非法」+ 总部解散全过程港媒 5 期系列报道",
            "1947-12-23 / 12-31 / 1948-01-06 / 02-03 / 03-02 / 03-09 China Mail：民盟解散后到香港一届三中全会前后港媒持续追踪（6 期）",
            "1948-04-23 / 05-19 / 08-30 / 09-04 / 12-02 China Mail：响应中共「五一口号」+ 解放战争战略反攻期（5 期）",
            "1949-01-07 / 01-12 / 01-17 / 06-03 / 06-20 港媒：张澜上海软禁期 + 联合政府筹建讨论（5 期）",
        ],
        "status": "已上线（42 期港媒 · 1946-1949）",
        "status_class": "active",
        "active": True,
        "todo_note": "",
    },
    "nara": {
        "name": "NARA",
        "long_name": "National Archives and Records Administration",
        "cn_name": "美国国家档案馆",
        "subtitle": "美国国家档案馆 RG59 国务院全本",
        "intro": "美国国家档案馆 RG59 (Record Group 59) 是美国国务院档案的官方全本，FRUS 是从中精选的版本。",
        "perspective": "国务院档案全本视角 —— FRUS 是节选，NARA 是源头",
        "coverage": "893.00 decimal file（中国相关国务院档案 1910-1963）",
        "highlights": [
            "893.00/xxxx 系列：中国政治形势综合报告",
            "893.00B/xxxx 系列：中共相关",
            "数十万页档案（绝大多数未数字化）",
        ],
        "status": "Phase 5 待开发",
        "status_class": "todo",
        "active": False,
        "todo_note": "工程难度最大。NARA Catalog API 仍可用但需要 API key；大部分 RG59 中国 decimal file 仍未数字化，需现场调阅或缩微胶片。建议先做 FRUS → NARA locator 索引。",
    },
}


def platforms_panel_html(c: sqlite3.Connection) -> str:
    """海外民盟资料平台入口面板。FRUS 已上线，其余平台显示路线图。"""
    # 动态计算每个平台的数据规模
    plat_counts = {}
    try:
        for r in c.execute("SELECT COALESCE(source_platform,'frus') AS p, count(*) AS n FROM documents GROUP BY p"):
            plat_counts[r['p']] = r['n']
    except sqlite3.OperationalError:
        plat_counts = {}
    frus_docs = plat_counts.get('frus', 0)
    frus_pages = c.execute("SELECT count(*) FROM pages").fetchone()[0]
    frus_zh = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN'").fetchone()[0]
    frus_human = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN' AND status='human-reviewed'").fetchone()[0]
    frus_pct = (frus_human * 100 // frus_zh) if frus_zh else 0

    cards = []
    for key, meta in PLATFORM_META.items():
        cls = "platform-card" + (" active" if meta["active"] else " upcoming")
        n = plat_counts.get(key, 0)
        if key == "frus":
            desc = f"已收 {frus_docs} 篇民盟相关文档 / {frus_pages} 个页面 / {frus_zh} 个中文译文片段，人工复核覆盖率 {frus_pct}%。"
        else:
            if n > 0:
                desc = f"已收 {n} 篇文档。{meta['intro'][:60]}…"
            else:
                desc = meta['intro'][:120] + "…" if len(meta['intro']) > 120 else meta['intro']
        # 动态生成状态文本：已上线平台显示文档数
        if meta["status"] is not None:
            status_text = meta["status"]
        elif meta["active"] and n > 0:
            status_text = f"已上线 · {n} 篇"
        elif meta["active"]:
            status_text = "已上线"
        else:
            status_text = meta.get("status", "待开发")
        cards.append(f'''
<a class="{cls}" href="/sources/{key}">
  <h3>{h(meta["name"])}</h3>
  <div class="pmeta">{h(meta["subtitle"])}</div>
  <div class="pdesc">{h(desc)}</div>
  <div class="pstatus {meta["status_class"]}">{h(status_text)}</div>
</a>''')
    return '<h2 style="font-size:18px;margin:18px 0 10px;">📚 海外民盟资料平台</h2>\n<section class="platforms">' + "".join(cards) + "</section>"


def source_page(platform_key: str) -> bytes:
    """单个海外档案平台的专属栏目页。"""
    meta = PLATFORM_META.get(platform_key)
    if not meta:
        return layout("未知平台", '<div class="notice">未知的平台。可选：' + " / ".join(PLATFORM_META.keys()) + "</div>")

    with conn() as c:
        # 取此平台的文档清单（前台过滤 grade='前台不展示'）
        try:
            docs_rows = c.execute("""
                SELECT documents.*, dc.grade
                FROM documents
                LEFT JOIN document_classifications dc ON dc.document_id=documents.id
                WHERE COALESCE(source_platform, 'frus')=?
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                ORDER BY documents.date_guess, documents.volume_id, CAST(documents.doc_number AS INTEGER)
            """, (platform_key,)).fetchall()
        except sqlite3.OperationalError:
            docs_rows = []
        # 文档统计
        n_docs = len(docs_rows)

    highlights_html = "".join(f"<li>{h(item)}</li>" for item in meta.get("highlights", []))

    body = breadcrumb_html([("/", "首页"), (None, f"海外档案平台 · {meta['name']}")]) + f"""
<section class="hero" style="padding:32px 36px;">
  <h1>{h(meta['name'])} <span style="font-size:18px;color:var(--muted);font-weight:400;">· {h(meta['cn_name'])}</span></h1>
  <p class="hero-sub">{h(meta['intro'])}</p>
  <div class="hero-meta">
    <span><b>视角</b> {h(meta['perspective'])}</span>
    <span><b>时间覆盖</b> {h(meta['coverage'])}</span>
    <span><b>状态</b> <span class="pstatus {meta['status_class']}" style="margin-left:4px;">{h(meta['status'])}</span></span>
  </div>
</section>

<div class="section-head">
  <h2><svg class="ico"><use href="#i-archive"/></svg>核心档案亮点</h2>
</div>
<section class="notice archival" style="margin-bottom:22px;">
  <ul style="margin:0;padding-left:22px;font-family:var(--serif);line-height:1.85;">{highlights_html}</ul>
</section>
"""

    if meta["active"] and n_docs > 0:
        body += f"""
<div class="section-head">
  <h2><svg class="ico"><use href="#i-book"/></svg>本平台收录文档 ({n_docs} 篇)</h2>
  <a class="more" href="/docs">完整列表 →</a>
</div>
<section class="result-list">
"""
        for r in docs_rows[:20]:
            body += f"""
<article class="result">
  <div>
    {title_block(r["title"], f"/doc/{quote(r['doc_key'])}")}
    <div class="meta">{h(r["volume_id"])}/{h(r["doc_id"])} · {h(r["date_guess"])} {grade_badge(r)}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(t.strip())}</span>' for t in (r["matched_terms"] or "").split(";") if t.strip())}</div>
  </div>
  <div class="cite"><a href="{h(r["url"])}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
        if n_docs > 20:
            body += f'<div style="padding:14px 22px;text-align:center;border-top:1px solid var(--line-soft);"><a class="button" href="/docs">查看全部 {n_docs} 篇 →</a></div>'
        body += "</section>"
    elif meta["active"]:
        body += '<div class="notice">本平台已上线，但当前数据库中尚无文档。</div>'
    else:
        body += f'''
<div class="section-head">
  <h2><svg class="ico"><use href="#i-clock"/></svg>开发路线</h2>
</div>
<section class="notice archival">
  <p style="margin:0;font-family:var(--serif);line-height:1.85;">{h(meta.get("todo_note", "暂无说明。"))}</p>
</section>
'''
    return layout(f"{meta['name']} · 海外档案平台", body)


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


def yearmonth_from_row(row: sqlite3.Row) -> str:
    """返回 YYYY-MM 格式（如 "1946-07"），用于按月分组的年表。"""
    d = (row['date_guess'] or '').strip()
    # 优先匹配 YYYY-MM-DD 或 YYYY-MM
    m = re.match(r"(19[4-5][0-9])-(\d{1,2})", d)
    if m:
        return f"{m.group(1)}-{int(m.group(2)):02d}"
    # 次选：YYYY only
    m2 = re.search(r"\b(19[4-5][0-9])\b", d)
    if m2:
        return f"{m2.group(1)}-00"  # "00" 表示该年内未注明月份
    # fallback: volume_id 中的年份
    text = f"{row['volume_id'] or ''} {row['doc_key'] or ''}"
    m3 = re.search(r"\b(19[4-5][0-9])\b", text)
    if m3:
        return f"{m3.group(1)}-00"
    return "未注明"


def format_yearmonth(ym: str) -> str:
    """1946-07 → 1946 年 7 月；1946-00 → 1946 年（未注明月份）；未注明 → 未注明"""
    if ym == "未注明":
        return "未注明"
    if ym.endswith("-00"):
        return f"{ym[:4]} 年（月份未注明）"
    y, m = ym.split("-", 1)
    return f"{y} 年 {int(m)} 月"


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
          AND (dc.grade IS NULL OR dc.grade != '前台不展示')
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
            WHERE (pages.text LIKE ? OR documents.title LIKE ? OR documents.matched_terms LIKE ?)
              AND (dc.grade IS NULL OR dc.grade != '前台不展示')
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
              AND (dc.grade IS NULL OR dc.grade != '前台不展示')
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

    body = breadcrumb_html([("/", "首页"), ("/tasks", "研究工作台"), (None, "进度仪表盘")]) + f"""
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
        # 改：取"最近人工校订过的 8 条"替代旧的"按 volume 顺序最新 12 条"
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
                translations.status AS zh_status,
                translations.translator AS zh_translator,
                translations.id AS tid
            FROM translations
            JOIN pages ON pages.id = translations.page_id
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            WHERE translations.language='zh-CN' AND translations.status='human-reviewed'
            ORDER BY translations.id DESC
            LIMIT 8
            """
        ).fetchall()

        # 顶部 Hero 封面区
        platforms_html_block = platforms_panel_html(c)
        # 关键指标摘要
        n_docs = c.execute("SELECT count(*) FROM documents").fetchone()[0]
        n_pages = c.execute("SELECT count(*) FROM pages").fetchone()[0]
        n_zh = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN'").fetchone()[0]
        n_human = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN' AND status='human-reviewed'").fetchone()[0]
        n_events = c.execute("SELECT count(*) FROM research_events").fetchone()[0]
        cov_pct = (n_human * 100 // n_zh) if n_zh else 0

        body = f"""
<section class="hero">
  <h1>海外民盟历史文献研究库</h1>
  <p class="hero-sub">系统整理 1941–1950 年代海外档案中关于<strong>中国民主同盟</strong>的一手史料 ——
  抓取、校验、翻译、引用、事件梳理、研究输出。以
  <em>FRUS</em>（美国对外关系文件集）为基础，逐步扩展至 Wilson Center、CIA FOIA、
  Hoover、NARA 等海外档案系统。</p>
  <div class="hero-meta">
    <span><b>{n_docs}</b> 篇文档</span>
    <span><b>{n_pages}</b> 个页面/段落</span>
    <span><b>{n_zh}</b> 个中文译文</span>
    <span><b>{cov_pct}%</b> 人工复核覆盖率</span>
    <span><b>{n_events}</b> 条事件线索</span>
  </div>
</section>

<div class="section-head">
  <h2><svg class="ico"><use href="#i-globe"/></svg>海外档案平台</h2>
  <a class="more" href="/dashboard">研究进度仪表盘 →</a>
</div>
{platforms_html_block}
"""

        # focus 区
        focus_links = focus_config.get("links", [])
        focus_buttons = ""
        if isinstance(focus_links, list):
            for link in focus_links:
                if isinstance(link, dict):
                    focus_buttons += f'<a class="button" href="{h(link.get("href", "#"))}">{h(link.get("label", "入口"))}</a>'
        body += f"""
<div class="section-head">
  <h2><svg class="ico"><use href="#i-clock"/></svg>{h(focus_config.get("title", "今日继续研究"))}</h2>
  <a class="more" href="/focus">管理清单 →</a>
</div>
<section class="doc-head" style="margin-bottom:14px;">
  <div>
    <div class="meta" style="font-size:14px;line-height:1.7;">{h(focus_config.get("description", ""))}</div>
  </div>
  <div class="doc-tools">{focus_buttons}</div>
</section>
"""
        if focus_rows:
            body += '<section class="result-list">'
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
  <div class="cite"><a href="/cite/{h(row["page_id"])}"><svg class="ico"><use href="#i-quote"/></svg>摘录卡片</a><a href="{h(doc_href)}"><svg class="ico"><use href="#i-book"/></svg>并排阅读</a><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer"><svg class="ico"><use href="#i-arrow-right"/></svg>FRUS 原文</a></div>
</article>"""
            body += "</section>"

        # 民盟人物索引入口（按分组各取最热 1-2 人作为预览，余略）
        # 统计每位人物在 FRUS 命中数，按片段数倒序取前 8 张作为首页缩略卡片
        person_hits = []
        for person in PEOPLE:
            where_p, params_p = alias_where(
                ["documents.matched_terms", "documents.title", "pages.text", "translations.text"],
                person["aliases"],
            )
            row_p = c.execute(
                f"""
                SELECT count(DISTINCT documents.id) AS doc_count,
                       count(DISTINCT pages.id) AS page_count
                FROM pages
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                WHERE {where_p}
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                """,
                tuple(params_p),
            ).fetchone()
            person_hits.append((person, row_p["doc_count"] or 0, row_p["page_count"] or 0))
        person_hits.sort(key=lambda x: (-x[2], -x[1]))
        top_persons = person_hits[:8]
        body += f"""
<div class="section-head" style="margin-top:28px;">
  <h2><svg class="ico"><use href="#i-people"/></svg>民盟人物索引</h2>
  <a class="more" href="/people">全部 {len(PEOPLE)} 位人物 →</a>
</div>
<section class="doc-head" style="margin-bottom:14px;background:var(--panel-warm);">
  <div>
    <div class="meta" style="font-size:14px;line-height:1.7;">
      按民盟历史角色（创立期主席团 / 上海支部创始人 / 烈士 / 救国会七君子 / 文化界 / 历任主席）
      分组索引 <b>{len(PEOPLE)}</b> 位核心人物，每位人物可查所有 FRUS 原文片段、中文译文、事件年表和来源链接。
      下方按 FRUS 命中片段数列出前 8 位。
    </div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/people">进入人物索引</a>
  </div>
</section>
<section class="result-list">
"""
        for person, dc, pc in top_persons:
            profile_snip = compact(person.get("profile", ""), 110) if person.get("profile") else ""
            body += f"""
<article class="result">
  <div>
    <h2><a href="/people/{h(person["slug"])}">{h(person["name"])}</a></h2>
    <div class="title-en">{h(' / '.join(person["aliases"][:3]))}</div>
    <div class="meta">{dc} 篇文档 · {pc} 个片段</div>
    <div class="zh" style="font-size:13.5px;color:var(--muted);">{h(profile_snip)}</div>
  </div>
  <div class="cite"><a href="/people/{h(person['slug'])}">人物页</a><br><a href="/timeline?person={h(person['slug'])}">年表</a></div>
</article>"""
        body += "</section>"

        # 民盟史关键事件入口
        # 取 FRUS 命中片段数 Top 5 的事件作为首页快览
        event_hits = []
        for evt in KEY_EVENTS:
            where_e, params_e = _key_event_match_clause(evt)
            if where_e == "0":
                event_hits.append((evt, 0, 0))
                continue
            row_e = c.execute(
                f"""
                SELECT count(DISTINCT documents.id) AS doc_count,
                       count(DISTINCT pages.id) AS page_count
                FROM pages
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                WHERE {where_e}
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                """,
                tuple(params_e),
            ).fetchone()
            event_hits.append((evt, row_e["doc_count"] or 0, row_e["page_count"] or 0))
        event_hits.sort(key=lambda x: (-x[2], -x[1], x[0].get("sort_date", "")))
        top_events = event_hits[:5]
        total_event_with_hit = sum(1 for _, _, pc in event_hits if pc > 0)

        body += f"""
<div class="section-head" style="margin-top:28px;">
  <h2><svg class="ico"><use href="#i-clock"/></svg>民盟史关键事件</h2>
  <a class="more" href="/events/key">全部 {len(KEY_EVENTS)} 个事件 →</a>
</div>
<section class="doc-head" style="margin-bottom:14px;background:var(--panel-warm);">
  <div>
    <div class="meta" style="font-size:14px;line-height:1.7;">
      按民盟史 5 阶段（创立期 / 政协斡旋期 / 受难期 / 香港复盘新政协期 / 建国后）
      整理 <b>{len(KEY_EVENTS)}</b> 个关键历史事件，
      <b>{total_event_with_hit}</b> 个已有 FRUS 档案命中。
      点击事件查看简介、关联人物与所有原文片段。下方按 FRUS 命中片段数列出前 5 件。
    </div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/events/key">进入事件索引</a>
  </div>
</section>
<section class="result-list">
"""
        for evt, dc, pc in top_events:
            summary_snip = compact(evt.get("summary", ""), 130)
            body += f"""
<article class="result">
  <div>
    <h2><a href="/events/key/{h(evt["slug"])}">{h(evt["name"])}</a></h2>
    <div class="title-en" style="color:var(--archival);">{h(evt["date_label"])}</div>
    <div class="meta">{dc} 篇文档 · {pc} 个片段</div>
    <div class="zh" style="font-size:13.5px;color:var(--muted);">{h(summary_snip)}</div>
  </div>
  <div class="cite"><a href="/events/key/{h(evt['slug'])}">事件页</a></div>
</article>"""
        body += "</section>"

        # 最近人工校订
        body += """
<div class="section-head">
  <h2><svg class="ico"><use href="#i-checks"/></svg>最近人工校订（8 条）</h2>
  <a class="more" href="/docs">查看全部文档 →</a>
</div>
<section class="result-list">
"""
        body += "".join(result_html(row) for row in latest)
        body += "</section>"
    return layout("首页", body, active_path="/")


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


def _build_citations(doc: sqlite3.Row) -> dict[str, str]:
    """生成 BibTeX / Chicago / GB/T 7714 三种引用格式（按 source_platform 分支）"""
    title_zh = translate_title(doc["title"])
    title_en = doc["title"]
    vol = doc["volume_id"] or ""
    docnum = doc["doc_id"] or ""
    date = doc["date_guess"] or ""
    url = doc["url"] or ""
    platform = (doc["source_platform"] if "source_platform" in doc.keys() else None) or "frus"
    year = ""
    m = re.search(r"\b(19\d{2}|20\d{2})\b", date)
    if m:
        year = m.group(1)
    elif vol:
        m = re.search(r"\b(19\d{2})\b", vol)
        if m:
            year = m.group(1)

    if platform == "cia":
        # CIA Records Reading Room 解密档案
        rdp_id = docnum  # 即 archive.org identifier，含 RDP 编号
        bibkey = f"CIA_{rdp_id}".replace(".", "_").replace("-", "_")
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title  = {{{title_en}}},\n"
            f"  author = {{Central Intelligence Agency}},\n"
            f"  howpublished = {{CIA Records Reading Room, declassified report}},\n"
            f"  year   = {{{year}}},\n"
            f"  note   = {{Document ID: {rdp_id}; declassified, mirrored at Internet Archive}},\n"
            f"  url    = {{{url}}},\n"
            f"  urldate = {{2026-05-16}}\n"
            f"}}"
        )
        chicago = (
            f'Central Intelligence Agency. "{title_en}." Declassified report, {date}. '
            f'Document ID {rdp_id}. CIA Records Reading Room (mirrored at Internet Archive). {url}.'
        )
        gb = (
            f"美国中央情报局. {title_zh}: {title_en}[R/OL]. ({date}) [2026-05-16]. {url}. "
            f"CIA 解密档案，档案编号 {rdp_id}（Internet Archive 镜像）."
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # FRUS 默认格式
    bibkey = f"FRUS_{vol}_{docnum}".replace(".", "_").replace("-", "_")
    bibtex = (
        f"@incollection{{{bibkey},\n"
        f"  title  = {{{title_en}}},\n"
        f"  booktitle = {{Foreign Relations of the United States ({vol})}},\n"
        f"  publisher = {{U.S. Department of State, Office of the Historian}},\n"
        f"  year   = {{{year}}},\n"
        f"  note   = {{Document {docnum}, {date}}},\n"
        f"  url    = {{{url}}},\n"
        f"  urldate = {{2026-05-15}}\n"
        f"}}"
    )
    chicago = (
        f'"{title_en}." In *Foreign Relations of the United States* ({vol}), document {docnum}, {date}. '
        f'Washington, D.C.: U.S. Department of State, Office of the Historian. {url}.'
    )
    gb = (
        f"美国国务院历史档案办公室. {title_zh}: {title_en}[EB/OL]. ({date}) [2026-05-15]. {url}. "
        f"载《美国对外关系文件集》{vol}号文件 {docnum}."
    )
    return {"bibtex": bibtex, "chicago": chicago, "gb": gb}


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
    citations = _build_citations(doc)
    matched_chips = "".join(
        f'<a class="tag" href="/search?q={quote(t.strip())}">{h(t.strip())}</a>'
        for t in (doc["matched_terms"] or "").split(";") if t.strip()
    )

    # 按 source_platform 决定头部按钮和元数据卡片
    platform = doc["source_platform"] or "frus"
    is_cia = (platform == "cia")
    if is_cia:
        rdp_id = doc["doc_id"] or ""
        archive_detail_url = doc["url"] or f"https://archive.org/details/{rdp_id}"
        pdf_url = f"https://archive.org/download/{rdp_id}/{rdp_id}.pdf"
        ocr_text_url = f"https://archive.org/download/{rdp_id}/{rdp_id}_djvu.txt"
        tools_html = (
            f'<a class="button" href="{archive_detail_url}" target="_blank" rel="noreferrer">'
            f'<svg class="ico"><use href="#i-archive"/></svg>archive.org 详情</a>'
            f'<a class="button" href="{pdf_url}" target="_blank" rel="noreferrer">'
            f'<svg class="ico"><use href="#i-book"/></svg>下载 PDF 原档</a>'
            f'<a class="button" href="{ocr_text_url}" target="_blank" rel="noreferrer">'
            f'<svg class="ico"><use href="#i-globe"/></svg>OCR 英文原文</a>'
            f'<a class="button" href="/search?q={quote(doc["matched_terms"] or doc["title"])}">'
            f'<svg class="ico"><use href="#i-search"/></svg>相关搜索</a>'
        )
        platform_badge = (
            '<span class="src-badge cia">'
            '<svg class="ico"><use href="#i-lock"/></svg>CIA · 已解密 · archive.org 镜像'
            '</span>'
        )
        meta_card_foot = (
            f'<span><strong>档案集</strong> CIA Records Reading Room</span>'
            f'<span><strong>RDP 编号</strong> {h(rdp_id)}</span>'
            f'<span><strong>解密日期</strong> {h(doc["date_guess"])}</span>'
            f'<span><strong>本库 ID</strong> doc/{h(doc["doc_key"])}</span>'
        )
    else:
        tools_html = (
            f'<a class="button" href="{source_link}" target="_blank" rel="noreferrer">'
            f'<svg class="ico"><use href="#i-globe"/></svg>FRUS 原文</a>'
            f'<a class="button" href="/search?q={quote(doc["matched_terms"] or doc["title"])}">'
            f'<svg class="ico"><use href="#i-search"/></svg>相关搜索</a>'
        )
        platform_badge = ''
        meta_card_foot = (
            f'<span><strong>FRUS 卷号</strong> {h(doc["volume_id"])}</span>'
            f'<span><strong>文件号</strong> {h(doc["doc_id"])}</span>'
            f'<span><strong>日期</strong> {h(doc["date_guess"])}</span>'
            f'<span><strong>本库 ID</strong> doc/{h(doc["doc_key"])}</span>'
        )

    body = breadcrumb_html([("/", "首页"), ("/docs", "全部文档"), (None, translate_title(doc["title"])[:36])]) + f"""
<section class="doc-head{' cia-doc' if is_cia else ''}">
  <div>
    {title_block(doc["title"], None, "h1")}
    <div class="meta">{platform_badge} {h(doc["volume_id"])}/{h(doc["doc_id"])} · {h(doc["date_guess"])} {grade_badge(doc)}</div>
    <div class="tagline" style="margin-top:8px;">{matched_chips}</div>
    <div class="meta" style="margin-top:8px;">{h(doc["reason"] or "")}</div>
  </div>
  <div class="doc-tools">{tools_html}</div>
</section>

<section class="meta-card{' cia-cite' if is_cia else ''}" id="cite-card">
  <div class="meta-card-head">
    <h3><svg class="ico"><use href="#i-quote"/></svg>学术引用</h3>
    <div class="cite-tabs">
      <button type="button" class="cite-tab active" data-fmt="bibtex">BibTeX</button>
      <button type="button" class="cite-tab" data-fmt="chicago">Chicago</button>
      <button type="button" class="cite-tab" data-fmt="gb">GB/T 7714</button>
      <button type="button" class="button cite-copy" id="cite-copy-btn"><svg class="ico"><use href="#i-check"/></svg>复制</button>
    </div>
  </div>
  <pre class="cite-content" id="cite-content" data-bibtex="{h(citations['bibtex'])}" data-chicago="{h(citations['chicago'])}" data-gb="{h(citations['gb'])}">{h(citations['bibtex'])}</pre>
  <div class="meta-card-foot">{meta_card_foot}</div>
</section>

{('<div class="notice cia-ocr-notice" style="margin-bottom:14px;">'
  '<svg class="ico"><use href="#i-globe"/></svg>'
  '本档案为 CIA 解密报告的 <b>archive.org OCR 文本</b>，可能含扫描识别噪声（页眉/水印残留）。'
  '正式引用请以 <a href="' + archive_detail_url + '" target="_blank">archive.org 原始 PDF</a> 为准。'
  '</div>') if is_cia else ''}

<section class="reader">"""
    for row in rows:
        page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
        selected = " id=\"selected\"" if page_id and str(row["page_id"]) == str(page_id) else ""
        zh = row["zh_text"] or "尚未翻译"
        zh_class = "" if row["zh_text"] else " empty"
        status = row["zh_status"] or "needs-translation"
        source_label = "archive.org 原档" if is_cia else "FRUS 段落"
        body += f"""
  <div class="segment">
    <article class="pane"{selected}>
      <div class="pane-head"><span>原文 · {h(page)}</span><span><a href="/cite/{h(row["page_id"])}">摘录卡片</a> · <a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">{source_label}</a></span></div>
      <div class="pane-body">{h(row["original_text"])}</div>
    </article>
    <article class="pane zh-pane">
      <div class="pane-head"><span>中文译文 · {h(status)}</span><a href="/review/{h(row["page_id"])}"><svg class="ico"><use href="#i-edit"/></svg>校订</a></div>
      <div class="pane-body{zh_class}">{h(zh)}</div>
    </article>
  </div>"""
    body += "</section>"
    body += """
<script>
(function(){
  const tabs = document.querySelectorAll('.cite-tab');
  const content = document.getElementById('cite-content');
  const btn = document.getElementById('cite-copy-btn');
  if (!content || !btn) return;
  tabs.forEach(tab => tab.addEventListener('click', () => {
    tabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    const fmt = tab.dataset.fmt;
    content.textContent = content.dataset[fmt] || '';
  }));
  btn.addEventListener('click', () => {
    navigator.clipboard.writeText(content.textContent).then(() => {
      const oldHTML = btn.innerHTML;
      btn.innerHTML = '<svg class="ico"><use href="#i-check"/></svg>已复制';
      setTimeout(() => { btn.innerHTML = oldHTML; }, 1500);
    });
  });
})();
</script>
"""
    if page_id:
        body += "<script>document.getElementById('selected')?.scrollIntoView({block:'center'});</script>"
    return layout(translate_title(doc["title"]), body)


def docs(active_grade: str = "", active_translation: str = "") -> bytes:
    with conn() as c:
        where_parts = []
        params: list[str] = []
        # 前台默认过滤 grade='前台不展示' 的档案
        where_parts.append("(dc.grade IS NULL OR dc.grade != '前台不展示')")
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
    body = breadcrumb_html([("/", "首页"), (None, "全部文档")])
    body += grade_filters(active_grade, active_translation)
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


def glossary_page() -> bytes:
    """术语表页面，从 data/translation_glossary.csv 读 109 条标准译名。"""
    import csv as _csv
    glossary_path = ROOT / "data" / "translation_glossary.csv"
    entries = []
    if glossary_path.exists():
        with open(glossary_path, encoding="utf-8") as f:
            for row in _csv.DictReader(f):
                term = (row.get("term") or "").strip()
                trans = (row.get("translation") or "").strip()
                note = (row.get("note") or "").strip()
                if term and trans:
                    entries.append((term, trans, note))
    # 按首字母分组
    from collections import defaultdict
    groups = defaultdict(list)
    for term, trans, note in entries:
        first = term[0].upper() if term[0].isascii() and term[0].isalpha() else "#"
        groups[first].append((term, trans, note))
    letters_used = sorted(groups.keys())

    body = breadcrumb_html([("/", "首页"), (None, "术语表")])
    body += f"""
<section class="hero" style="padding:24px 28px;">
  <h1 style="font-size:26px;">标准译名表</h1>
  <p class="hero-sub">本平台中英文术语对照表，共 <strong>{len(entries)}</strong> 条。
  按英文首字母分组排序。所有人工校订与机器翻译均以此表为准；译文质量复核脚本
  亦根据此表生成 <code>glossary_miss</code> 提示。</p>
</section>
<nav class="glossary-letters">"""
    full_alphabet = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ#")
    for letter in full_alphabet:
        if letter in groups:
            body += f'<a href="#g-{letter}">{letter}</a>'
        else:
            body += f'<a class="disabled">{letter}</a>'
    body += "</nav>"

    for letter in letters_used:
        body += f'<section class="glossary-section" id="g-{letter}"><h2>{letter} ({len(groups[letter])})</h2>'
        body += '<table class="glossary-table"><thead><tr><th style="width:32%;">英文术语</th><th style="width:24%;">标准中文</th><th style="width:32%;">备注</th><th style="width:12%;">查看</th></tr></thead><tbody>'
        for term, trans, note in sorted(groups[letter], key=lambda x: x[0].lower()):
            body += f'<tr><td class="term">{h(term)}</td><td class="zh-term">{h(trans)}</td><td class="note">{h(note)}</td><td class="lookup"><a href="/search?q={quote(term)}">查文档 →</a></td></tr>'
        body += "</tbody></table></section>"

    return layout("术语表", body)


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

    body = breadcrumb_html([("/", "首页"), (None, "校订任务")]) + f"""
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
    # 第一步：扫描每位人物在 FRUS 库中的命中统计
    stats: dict[str, sqlite3.Row] = {}
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
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                """,
                tuple(params),
            ).fetchone()
            stats[person["slug"]] = row

    # 全库命中总览
    total_hit_persons = sum(1 for r in stats.values() if (r["doc_count"] or 0) > 0)
    total_docs = sum((r["doc_count"] or 0) for r in stats.values())
    total_pages = sum((r["page_count"] or 0) for r in stats.values())

    body = breadcrumb_html([("/", "首页"), ("/topics", "专题与人物"), (None, "人物索引")])
    body += f"""
<section class="doc-head">
  <div>
    <h1>民盟人物索引</h1>
    <div class="meta">
      按民盟历史角色分 {len(PERSON_GROUPS)} 组共 <b>{len(PEOPLE)}</b> 位人物，
      其中 <b>{total_hit_persons}</b> 位在 FRUS 档案中已有命中（覆盖 {total_docs} 篇文档 / {total_pages} 个片段）。
      点击姓名查看该人物所有原文、译文、来源链接和事件年表。
    </div>
    <div class="meta" style="margin-top:6px;color:var(--muted-soft);font-size:13px;">
      本平台只收录 <b>国外一手原始档案</b>（FRUS / Wilson / CIA / Hoover / NARA / HathiTrust）。
      下方人物索引是档案翻译过程中用于规范人名、提供历史上下文的内部研究编排，<b>不构成资料库收录内容</b>。
    </div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/tasks?queue=people">人物校订任务</a>
    <a class="button" href="/timeline">人物年表</a>
  </div>
</section>
"""

    # 第二步：按 PERSON_GROUPS 顺序分组渲染
    for group_key, group_label, group_brief in PERSON_GROUPS:
        members = [p for p in PEOPLE if p.get("group") == group_key]
        if not members:
            continue
        # 组内按命中片段数倒序，无命中的按 slug 字母序排到末尾
        members.sort(
            key=lambda p: (
                -(stats[p["slug"]]["page_count"] or 0),
                -(stats[p["slug"]]["doc_count"] or 0),
                p["slug"],
            )
        )
        group_doc_total = sum((stats[p["slug"]]["doc_count"] or 0) for p in members)
        group_page_total = sum((stats[p["slug"]]["page_count"] or 0) for p in members)
        body += f"""
<div class="section-head" style="margin-top:28px;">
  <h2 style="margin:0;">{h(group_label)}</h2>
  <span class="meta" style="color:var(--muted);font-size:13px;">{len(members)} 人 · FRUS 共 {group_doc_total} 篇 / {group_page_total} 段</span>
</div>
<section class="doc-head" style="margin-bottom:10px;background:var(--panel-warm);">
  <div><div class="meta" style="line-height:1.7;">{h(group_brief)}</div></div>
</section>
<section class="result-list">
"""
        for person in members:
            row = stats[person["slug"]]
            doc_count = row["doc_count"] or 0
            page_count = row["page_count"] or 0
            core_hits = row["core_hits"] or 0
            no_hit_cls = "" if doc_count > 0 else ' style="opacity:.6;"'
            hit_meta = (
                f'{doc_count} 篇文档 · {page_count} 个片段 · 核心命中 {core_hits}'
                if doc_count > 0
                else '<span style="color:var(--muted-soft);">FRUS 暂无命中（待 Wilson / CIA 等档案补充）</span>'
            )
            profile_snip = compact(person.get("profile", ""), 120) if person.get("profile") else ""
            profile_html = (
                f'<div class="zh" style="font-size:13.5px;color:var(--muted);">{h(profile_snip)}</div>'
                if profile_snip
                else ""
            )
            body += f"""
<article class="result"{no_hit_cls}>
  <div>
    <h2><a href="/people/{h(person["slug"])}">{h(person["name"])}</a></h2>
    <div class="title-en">{h(' / '.join(person["aliases"][:4]))}</div>
    <div class="meta">{hit_meta}</div>
    {profile_html}
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
              AND (dc.grade IS NULL OR dc.grade != '前台不展示')
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
    # 人物传记摘要卡片（如有 profile 字段）
    profile_text = person.get("profile", "")
    if profile_text:
        group_label = ""
        for g_key, g_label, _ in PERSON_GROUPS:
            if person.get("group") == g_key:
                group_label = g_label
                break
        body += f"""
<section class="doc-head" style="background:var(--panel-warm);border-left:4px solid var(--accent);margin-bottom:16px;">
  <div style="max-width:none;">
    <div class="meta" style="color:var(--accent-deep);font-size:13px;letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px;">
      人物档案 {('· ' + h(group_label)) if group_label else ''}
    </div>
    <div style="font-family:var(--serif);font-size:16px;line-height:1.8;color:var(--text);">{h(profile_text)}</div>
    <div class="meta" style="margin-top:10px;font-size:12.5px;color:var(--muted-soft);">
      本卡为内部研究编排参考，便于理解下方档案译文的人物上下文；
      本平台资料库本身只收录 <b>国外一手原始档案</b>（FRUS / Wilson / CIA / Hoover / NARA / HathiTrust）。
    </div>
  </div>
</section>
"""
    if not rows:
        body += '<div class="notice">FRUS 档案中暂无命中。待 Wilson Center / CIA FOIA / NARA 等海外档案补充后会自动出现。</div>'
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
        # 前台展示边界：过滤 grade='前台不展示'
        prefix = "WHERE " if not where else where + " AND "
        full_where = (prefix + "(dc.grade IS NULL OR dc.grade != '前台不展示')") if (where or True) else ""
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
                documents.source_platform,
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
            {full_where}
            GROUP BY pages.id
            ORDER BY documents.date_guess, documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
            LIMIT 600
            """,
            tuple(params),
        ).fetchall()
    # 按月（YYYY-MM）和年（YYYY）双重分组
    months: dict[str, list[sqlite3.Row]] = {}
    years_for_density: dict[str, int] = {}
    for row in rows:
        ym = yearmonth_from_row(row)
        months.setdefault(ym, []).append(row)
        yr = ym[:4] if ym != "未注明" else "未注明"
        years_for_density[yr] = years_for_density.get(yr, 0) + 1

    # 月度密度热力图（CSS 网格）：1941-1955 × 12 月
    density_html = ""
    month_counts = {ym: len(rs) for ym, rs in months.items()}
    max_n = max(month_counts.values()) if month_counts else 1
    years_range = list(range(1941, 1956))
    rows_html = ['<div class="density-row"><div class="density-cell density-axis"></div>'
                 + ''.join(f'<div class="density-cell density-axis density-mlabel">{m}</div>' for m in range(1, 13))
                 + '</div>']
    for yr in years_range:
        cells = [f'<div class="density-cell density-axis density-ylabel">{yr}</div>']
        for mo in range(1, 13):
            key = f"{yr}-{mo:02d}"
            n = month_counts.get(key, 0)
            if n == 0:
                cells.append('<div class="density-cell density-empty"></div>')
            else:
                # 5 档离散色阶（仿 GitHub 贡献图）：低密度也能一眼看清
                # 阈值按经验值：1 / 2-3 / 4-7 / 8-15 / 16+
                if   n >= 16: bg, fg = "#0f6b5b", "#ffffff"   # 最深
                elif n >= 8:  bg, fg = "#2f8a76", "#ffffff"
                elif n >= 4:  bg, fg = "#6ab09a", "#ffffff"
                elif n >= 2:  bg, fg = "#a8d0c1", "#0a3d34"
                else:         bg, fg = "#d4e8de", "#0a3d34"   # 最浅（n=1）
                cells.append(
                    f'<a class="density-cell density-hot" href="#m-{key}" '
                    f'style="background:{bg};color:{fg};" '
                    f'title="{yr} 年 {mo} 月 · {n} 个片段">{n}</a>'
                )
        rows_html.append('<div class="density-row">' + ''.join(cells) + '</div>')
    density_html = (
        '<div class="density-card">'
        '<div class="density-title">月度密度热力图（点击跳转到对应月份）</div>'
        '<div class="density-grid">' + ''.join(rows_html) + '</div>'
        '</div>'
    )

    filter_links.append('<a class="button" href="/timeline">全部年表</a>')
    filter_links.extend(f'<a class="button" href="/timeline?topic={h(topic["slug"])}">{h(topic["name"])}</a>' for topic in TOPICS[:5])
    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(title)}</h1>
    <div class="meta">{h(subtitle)}</div>
    <div class="meta">{len({row["doc_key"] for row in rows})} 篇文档 · {len(rows)} 个片段 · 按月细化</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/topics">专题</a>
    <a class="button" href="/people">人物</a>
    <a class="button" href="/events">事件线索</a>
    <a class="button" href="/events/key">关键事件</a>
  </div>
</section>
<div class="filters">{''.join(filter_links)}</div>
{density_html}
"""
    if not rows:
        body += '<div class="notice">暂无匹配年表材料。</div>'
    else:
        # 按 YYYY-MM 排序，未注明放最后
        cur_year = None
        for ym in sorted(months.keys(), key=lambda x: (x == "未注明", x)):
            yr = ym[:4] if ym != "未注明" else "未注明"
            if yr != cur_year:
                body += f'<h2 class="tl-year" style="font-size:22px;margin:28px 0 4px;color:var(--accent-deep);border-bottom:2px solid var(--accent-soft);padding-bottom:4px;">{h(yr)} 年</h2>'
                cur_year = yr
            month_label = format_yearmonth(ym)
            anchor = f'm-{ym}' if ym != '未注明' else 'm-unknown'
            body += (
                f'<h3 id="{anchor}" style="font-size:16px;margin:14px 0 6px;color:var(--archival);'
                f'font-weight:500;">{h(month_label)} '
                f'<span style="color:var(--muted);font-size:13px;font-weight:400;">'
                f'· {len(months[ym])} 个片段</span></h3>'
            )
            body += '<section class="result-list">'
            for row in months[ym]:
                page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
                href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
                issue = ""
                if row["issue_count"]:
                    issue = f'<span class="issue{" high" if (row["max_severity"] or 0) >= 3 else ""}">{row["issue_count"]} 个校订提示</span>'
                # source 徽章
                src_platform = row["source_platform"] if "source_platform" in row.keys() else None
                src_badge = ('<span class="src-badge cia" style="font-size:11px;">CIA</span> '
                             if src_platform == 'cia'
                             else '<span class="src-badge frus" style="font-size:11px;">FRUS</span> ')
                body += f"""
<article class="result">
  <div>
    {title_block(row["title"], href)}
    <div class="meta">{src_badge}{h(row["date_guess"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(page)} {grade_badge(row)}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 230))}</div>
    <div class="zh">中文: {h(compact(row["zh_text"], 230))}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(tag)}</span>' for tag in topic_tags(row))}{issue}</div>
  </div>
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">来源</a></div>
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


# ---------- 民盟史关键事件视图（/events/key/...） ----------

def _key_event_match_clause(event: dict) -> tuple[str, list[str]]:
    """构造 SQL WHERE 子句，匹配该事件的 search_terms 命中 FRUS 库的相关 page。"""
    terms = event.get("search_terms", []) or []
    if not terms:
        return "0", []
    parts: list[str] = []
    params: list[str] = []
    columns = ["documents.matched_terms", "documents.title", "pages.text", "translations.text"]
    for term in terms:
        like = f"%{term}%"
        for col in columns:
            parts.append(f"{col} LIKE ?")
            params.append(like)
    return "(" + " OR ".join(parts) + ")", params


def _key_event_hit_stats(event: dict) -> dict[str, int]:
    """返回某事件在 FRUS 库的命中统计（过滤 grade='前台不展示'）。"""
    where, params = _key_event_match_clause(event)
    if where == "0":
        return {"doc_count": 0, "page_count": 0}
    with conn() as c:
        row = c.execute(
            f"""
            SELECT
                count(DISTINCT documents.id) AS doc_count,
                count(DISTINCT pages.id) AS page_count
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            WHERE {where}
              AND (dc.grade IS NULL OR dc.grade != '前台不展示')
            """,
            tuple(params),
        ).fetchone()
    return {"doc_count": row["doc_count"] or 0, "page_count": row["page_count"] or 0}


def key_events_index() -> bytes:
    """民盟史关键事件总览 /events/key —— 按 6 阶段分组 + 时间序展示。"""
    # 收集每个事件的 FRUS 命中统计
    stats: dict[str, dict[str, int]] = {evt["slug"]: _key_event_hit_stats(evt) for evt in KEY_EVENTS}
    total_with_hit = sum(1 for s in stats.values() if s["page_count"] > 0)
    total_docs = sum(s["doc_count"] for s in stats.values())
    total_pages = sum(s["page_count"] for s in stats.values())

    body = breadcrumb_html([("/", "首页"), ("/events", "事件线索"), (None, "民盟史关键事件")])
    body += f"""
<section class="doc-head">
  <div>
    <h1>民盟史关键事件</h1>
    <div class="meta">
      按民盟历史 5 个阶段共整理 <b>{len(KEY_EVENTS)}</b> 个关键事件节点，
      其中 <b>{total_with_hit}</b> 个事件在 FRUS 档案中已有命中。
      点击事件名称查看简介、关联人物和所有 FRUS 命中片段。
    </div>
    <div class="meta" style="margin-top:6px;color:var(--muted-soft);font-size:13px;">
      本平台只收录 <b>国外一手原始档案</b>。
      事件清单与时间标注是档案聚合的内部研究编排，<b>不构成资料库收录内容</b>。
    </div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/events">事件线索总览</a>
    <a class="button" href="/people">人物索引</a>
    <a class="button" href="/timeline">文档年表</a>
  </div>
</section>
"""
    # 按 phase 分组渲染，组内按 sort_date 升序
    for phase_slug, phase_label in EVENT_PHASES:
        members = [evt for evt in KEY_EVENTS if evt.get("phase") == phase_slug]
        if not members:
            continue
        members.sort(key=lambda e: e.get("sort_date", ""))
        phase_doc_total = sum(stats[e["slug"]]["doc_count"] for e in members)
        phase_page_total = sum(stats[e["slug"]]["page_count"] for e in members)
        body += f"""
<div class="section-head" style="margin-top:28px;">
  <h2 style="margin:0;">{h(phase_label)}</h2>
  <span class="meta" style="color:var(--muted);font-size:13px;">{len(members)} 件 · FRUS 共 {phase_doc_total} 篇 / {phase_page_total} 段</span>
</div>
<section class="result-list">
"""
        for evt in members:
            st = stats[evt["slug"]]
            no_hit = (st["page_count"] == 0)
            no_hit_cls = ' style="opacity:.6;"' if no_hit else ""
            hit_meta = (
                f'{st["doc_count"]} 篇文档 · {st["page_count"]} 个片段'
                if not no_hit
                else '<span style="color:var(--muted-soft);">FRUS 暂无命中（待 Wilson / CIA 等档案补充）</span>'
            )
            summary_snip = compact(evt.get("summary", ""), 200)
            related = evt.get("related_persons", [])
            person_chips = ""
            for ps in related[:6]:
                p = next((x for x in PEOPLE if x["slug"] == ps), None)
                if p:
                    person_chips += f'<a class="tag" href="/people/{h(ps)}" style="text-decoration:none;">{h(p["name"])}</a>'
            body += f"""
<article class="result"{no_hit_cls}>
  <div>
    <h2><a href="/events/key/{h(evt["slug"])}">{h(evt["name"])}</a></h2>
    <div class="title-en" style="color:var(--archival);">{h(evt["date_label"])}</div>
    <div class="meta">{hit_meta}</div>
    <div class="zh" style="font-size:13.5px;color:var(--muted);">{h(summary_snip)}</div>
    <div class="tagline">{person_chips}</div>
  </div>
  <div class="cite"><a href="/events/key/{h(evt['slug'])}">查看事件页</a></div>
</article>"""
        body += "</section>"
    return layout("民盟史关键事件", body)


def key_event_page(slug: str, view: str = "mixed") -> bytes:
    """单个关键事件详情页 /events/key/<slug>

    view: "mixed"（默认，按年份混合）/ "compare"（FRUS 左 + CIA 右并排对比）
    """
    evt = event_by_slug(slug)
    if not evt:
        return layout("未找到事件", '<div class="notice">未找到对应的关键事件。</div>')

    phase_label = ""
    for p_slug, p_label in EVENT_PHASES:
        if evt.get("phase") == p_slug:
            phase_label = p_label
            break

    # 查 FRUS + CIA 命中片段（含 source_platform 字段）
    where, params = _key_event_match_clause(evt)
    rows: list[sqlite3.Row] = []
    if where != "0":
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
                    documents.source_platform,
                    COALESCE(dc.grade, '') AS grade,
                    translations.text AS zh_text,
                    translations.status AS zh_status
                FROM pages
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                WHERE {where}
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                GROUP BY pages.id
                ORDER BY documents.date_guess, documents.volume_id, CAST(documents.doc_number AS INTEGER), pages.id
                LIMIT 300
                """,
                tuple(params),
            ).fetchall()

    doc_count = len({r["doc_key"] for r in rows})
    core_count = sum(1 for r in rows if r["grade"] == "核心文献")
    n_frus = sum(1 for r in rows if (r["source_platform"] or "frus") == "frus")
    n_cia = sum(1 for r in rows if r["source_platform"] == "cia")

    # 关联人物详情
    related_persons_html = ""
    for ps in evt.get("related_persons", []):
        p = next((x for x in PEOPLE if x["slug"] == ps), None)
        if p:
            related_persons_html += (
                f'<a class="tag" href="/people/{h(ps)}" '
                f'style="text-decoration:none;font-size:13px;">{h(p["name"])}</a>'
            )

    body = breadcrumb_html([
        ("/", "首页"),
        ("/events", "事件线索"),
        ("/events/key", "民盟史关键事件"),
        (None, str(evt["name"])),
    ])

    # 视图模式切换链接
    base_path = f"/events/key/{slug}"
    mixed_link = base_path
    compare_link = base_path + "?view=compare"
    mixed_class = "button" + (" active" if view != "compare" else "")
    compare_class = "button" + (" active" if view == "compare" else "")

    body += f"""
<section class="doc-head">
  <div>
    <h1>{h(evt["name"])}</h1>
    <div class="title-en" style="color:var(--archival);font-size:16px;margin-top:4px;">
      {h(evt["date_label"])} · {h(phase_label)}
    </div>
    <div class="meta">
      <span class="src-badge frus" style="font-size:11px;">FRUS</span> {n_frus} 段 ·
      <span class="src-badge cia" style="font-size:11px;">CIA</span> {n_cia} 段 ·
      合计 {doc_count} 篇文档 / {len(rows)} 片段 · 核心 {core_count}
    </div>
  </div>
  <div class="doc-tools">
    <a class="{mixed_class}" href="{mixed_link}">混合视图（按时间）</a>
    <a class="{compare_class}" href="{compare_link}">对比视图（FRUS↔CIA 并排）</a>
    <a class="button" href="/events/key">关键事件索引</a>
    <a class="button" href="/people">人物索引</a>
  </div>
</section>

<section class="doc-head" style="background:var(--panel-warm);border-left:4px solid var(--accent);margin-bottom:16px;">
  <div style="max-width:none;">
    <div class="meta" style="color:var(--accent-deep);font-size:13px;letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px;">
      事件简介
    </div>
    <div style="font-family:var(--serif);font-size:16px;line-height:1.9;color:var(--text);">{h(evt.get("summary", ""))}</div>
    {('<div style="margin-top:14px;"><div class="meta" style="font-size:12.5px;color:var(--muted);margin-bottom:6px;">关联人物：</div><div class="tagline">' + related_persons_html + '</div></div>') if related_persons_html else ''}
    <div class="meta" style="margin-top:12px;font-size:12.5px;color:var(--muted-soft);">
      本卡为内部研究编排参考；下方 FRUS 命中片段为本平台收录的国外一手档案原文与中译。
    </div>
  </div>
</section>
"""

    if not rows:
        body += (
            '<div class="notice">FRUS 档案中暂无与本事件直接命中的片段。'
            '待 Wilson Center / CIA FOIA / NARA 等海外档案补充后会自动出现。</div>'
        )
    else:
        # 渲染上限：宽搜事件（如政协、民盟成立）容易命中数百段，单页渲染过大
        RENDER_LIMIT = 50
        total_rows = len(rows)
        truncated = total_rows > RENDER_LIMIT
        display_rows = rows[:RENDER_LIMIT]
        if truncated:
            body += (
                f'<div class="notice" style="background:var(--warn-soft);border-left-color:var(--warn);">'
                f'共命中 <b>{total_rows}</b> 个片段，本页仅展示前 <b>{RENDER_LIMIT}</b> 段（按文档年份排序）。'
                f'完整结果可用 <a href="/search?q={quote(evt["name"])}">站内搜索</a> 或'
                f' <a href="/timeline">文档年表</a> 进一步浏览。'
                f'</div>'
            )

        def render_card(row, compact_zh: int = 260) -> str:
            page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
            href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
            sp = row["source_platform"] or "frus"
            badge = (
                '<span class="src-badge cia" style="font-size:11px;">CIA</span> '
                if sp == "cia"
                else '<span class="src-badge frus" style="font-size:11px;">FRUS</span> '
            )
            return f"""
<article class="result">
  <div>
    {title_block(row["title"], href)}
    <div class="meta">{badge}{h(row["volume_id"])}/{h(row["doc_id"])} · {h(row["date_guess"])} · {h(page)} {grade_badge(row)}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 220))}</div>
    <div class="zh">中文: {h(compact(row["zh_text"], compact_zh))}</div>
  </div>
  <div class="cite"><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(row["page_url"])}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""

        if view == "compare":
            # 双列并排：FRUS 左 / CIA 右，按 source_platform 分组
            frus_rows = [r for r in display_rows if (r["source_platform"] or "frus") == "frus"]
            cia_rows = [r for r in display_rows if r["source_platform"] == "cia"]

            body += f"""
<div style="margin:18px 0 8px;font-size:14px;color:var(--muted);">
  对比视图：左列展示 <span class="src-badge frus" style="font-size:11px;">FRUS</span> 美国外交档案的命中片段，
  右列展示 <span class="src-badge cia" style="font-size:11px;">CIA</span> 中央情报局解密档案的命中片段，
  便于研究者跨数据源对比两类视角对同一事件的不同记述。
</div>
<div class="compare-grid">
  <div class="compare-col">
    <div class="compare-head"><span class="src-badge frus">FRUS · 美国外交档案</span> <span class="meta">{len(frus_rows)} 段</span></div>
    <section class="result-list compare-list">
"""
            if not frus_rows:
                body += '<div class="notice" style="margin:8px;">FRUS 暂无命中片段。</div>'
            else:
                for r in frus_rows:
                    body += render_card(r, compact_zh=200)
            body += '</section></div>\n<div class="compare-col">'
            body += f"""
    <div class="compare-head"><span class="src-badge cia">CIA · 中央情报局解密</span> <span class="meta">{len(cia_rows)} 段</span></div>
    <section class="result-list compare-list">
"""
            if not cia_rows:
                body += '<div class="notice" style="margin:8px;">CIA 暂无命中片段（待后续档案补充）。</div>'
            else:
                for r in cia_rows:
                    body += render_card(r, compact_zh=200)
            body += '</section></div></div>'
        else:
            # 混合视图：按文档年份分组
            years_map: dict[str, list[sqlite3.Row]] = {}
            for r in display_rows:
                yr = (r["date_guess"] or "")[:4] if r["date_guess"] else "未注明"
                years_map.setdefault(yr or "未注明", []).append(r)
            for year in sorted(years_map.keys(), key=lambda y: (y == "未注明", y)):
                body += f'<h2 style="font-size:18px;margin:22px 0 8px;">{h(year)}</h2><section class="result-list">'
                for row in years_map[year]:
                    body += render_card(row)
                body += "</section>"
    return layout(str(evt["name"]), body)


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        _request.path = parsed.path  # 让 layout() 知道当前页面，自动 highlight 导航
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
        elif parsed.path == "/glossary":
            payload = glossary_page()
        elif parsed.path.startswith("/sources/"):
            payload = source_page(unquote(parsed.path.removeprefix("/sources/")))
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
        elif parsed.path == "/events/key":
            payload = key_events_index()
        elif parsed.path.startswith("/events/key/"):
            payload = key_event_page(
                unquote(parsed.path.removeprefix("/events/key/")),
                view=qs.get("view", ["mixed"])[0],
            )
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
        try:
            sys.stderr.write((fmt % args) + "\n")
            sys.stderr.flush()
        except (BrokenPipeError, OSError):
            pass


def main() -> None:
    server = ReusableThreadingHTTPServer(("127.0.0.1", 8765), Handler)
    print("Serving http://127.0.0.1:8765")
    server.serve_forever()


if __name__ == "__main__":
    main()
