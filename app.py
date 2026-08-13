#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
import csv
import html
import sys
import json
import os
import re
import sqlite3
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

from scripts.domestic.research_packet import packet_json_bytes, research_packet_page

# 当前请求路径的 thread-local 容器，layout() 用来自动 highlight 当前导航
_request = threading.local()


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts" / "legacy"))
DATA_ROOT = Path(os.environ.get("MINGMENG_DATA_ROOT", str(ROOT / "data"))).expanduser().resolve()
WORK_ROOT = Path(os.environ.get("MINGMENG_WORK_ROOT", str(ROOT / "work"))).expanduser().resolve()
DB_PATH = Path(
    os.environ.get("MINGMENG_RESEARCH_DB", str(DATA_ROOT / "research_index.sqlite"))
).expanduser().resolve()
DOMESTIC_STAGING_DB_PATH = Path(
    os.environ.get("MINGMENG_STAGING_DB", str(WORK_ROOT / "domestic" / "staging_20260730" / "domestic_staging.sqlite"))
).expanduser().resolve()
PHASE2_INVENTORY_REPORT_PATH = WORK_ROOT / "domestic" / "phase2_inventory_20260730" / "REPORT.json"
CORE_GAP_MATRIX_REPORT_PATH = WORK_ROOT / "domestic" / "phase2_inventory_20260730" / "core_gap_matrix_20260730" / "CORE_GAP_MATRIX.json"
SUPPLEMENTAL_1942_1943_REPORT_PATH = WORK_ROOT / "domestic" / "phase2_inventory_20260730" / "supplemental_1942_1943" / "REPORT.json"
RESEARCH_1942_1943_REPORT_PATH = WORK_ROOT / "domestic" / "phase2_inventory_20260730" / "research_1942_1943" / "REPORT.json"
ACADEMIC_PDF_OCR_PILOT_REPORT_PATH = WORK_ROOT / "domestic" / "academic_ocr_pilot_20260730" / "REPORT.json"
ACADEMIC_PDF_OCR_BATCH_REPORT_PATH = WORK_ROOT / "domestic" / "academic_ocr_batch_pilot_20260730" / "REPORT.json"
ACADEMIC_1943_TARGET_REPORT_PATH = WORK_ROOT / "domestic" / "academic_ocr_1943_target_20260730" / "REPORT.json"
GAP_WAVE2_AUDIT_REPORT_PATH = WORK_ROOT / "domestic" / "next_stage_20260730" / "10_gap_wave2_period_page_chain" / "AUDIT_REPORT.json"
W2_SHA_REPAIR_REPORT_PATH = WORK_ROOT / "domestic" / "two_month_20260730" / "w2" / "SOURCE_SHA_REPAIR_REPORT.json"
W2_SHA_SUPPLEMENT_REPORT_PATH = WORK_ROOT / "domestic" / "two_month_20260730" / "w2" / "SOURCE_SHA_SUPPLEMENT_REPORT.json"
MMDA_1942_1943_QUEUE_PATH = WORK_ROOT / "domestic" / "MMDA_1942_1943_PRIORITY_QUEUE_20260728.jsonl"
MMDA_P1_INTAKE_REPORT_PATH = WORK_ROOT / "domestic" / "mmda_p1_intake_20260730" / "REPORT.json"
MMDA_ORIGINAL_PENDING_REPORT_PATH = WORK_ROOT / "domestic" / "mmda_p1_intake_20260730" / "MMDA_1942_1943_ORIGINAL_PENDING_REPORT.json"
MMDA_ORIGINAL_PENDING_QUEUE_PATH = WORK_ROOT / "domestic" / "mmda_p1_intake_20260730" / "MMDA_1942_1943_ORIGINAL_PENDING_QUEUE.jsonl"
MACHINE_STRUCTURE_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "MACHINE_EVIDENCE_STRUCTURE_AUDIT_REPORT.json"
CLAIM_DUPLICATE_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "claim_duplicate_audit" / "REPORT.json"
P0_P1_MACHINE_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "p0_p1_machine_assessment" / "REPORT.json"
P0_P1_CONSISTENCY_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "p0_p1_source_consistency" / "REPORT.json"
CLAIM_CROSSWALK_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "claim_research_crosswalk" / "REPORT.json"
CROSSWALK_QUEUE_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "crosswalk_review_queue" / "REPORT.json"
CROSSWALK_MATERIAL_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "crosswalk_material_review_queue" / "REPORT.json"
FULLTEXT_CONTENT_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "crosswalk_fulltext_content_audit" / "REPORT.json"
FULLTEXT_LOCATOR_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "fulltext_locator_candidates" / "REPORT.json"
FULLTEXT_SEMANTIC_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "fulltext_semantic_signal_queue" / "REPORT.json"
FULLTEXT_OVERLAP_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "fulltext_text_overlap_queue" / "REPORT.json"
FULLTEXT_REVIEW_CARDS_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "fulltext_semantic_review_cards" / "REPORT.json"
STRUCTURED_RELATION_REPORT_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "structured_relation_signals" / "REPORT.json"
STRUCTURED_RELATION_ROWS_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "structured_relation_signals" / "SIGNALS.jsonl"
CONSERVATIVE_RELATION_ROWS_PATH = WORK_ROOT / "domestic" / "staging_20260730" / "conservative_relation_adjudication" / "ADJUDICATION_QUEUE.jsonl"
LOCAL_PRIVATE_OCR_REPORT_PATH = WORK_ROOT / "domestic" / "local_private_ocr_metadata_20260730" / "REPORT.json"
LOCAL_PRIVATE_NORMALIZATION_REPORT_PATH = WORK_ROOT / "domestic" / "local_private_ocr_metadata_20260730" / "NORMALIZATION_REPORT.json"
LOCAL_SEMANTIC_SIGNALS_REPORT_PATH = WORK_ROOT / "domestic" / "local_private_ocr_metadata_20260730" / "semantic_signals" / "REPORT.json"
HOME_FOCUS_PATH = DATA_ROOT / "home_focus.json"
TOPIC_COMPARISON_CARDS_PATH = DATA_ROOT / "domestic" / "topic_comparison_cards.json"
TOPIC_EVIDENCE_CHAIN_PATH = DATA_ROOT / "domestic" / "topic_evidence_chain.json"
ACADEMIC_SOURCE_POLICY_PATH = DATA_ROOT / "domestic" / "academic_source_policy.json"
STYLE_PATH = ROOT / "static" / "style.css"
FONTS_CSS_PATH = ROOT / "static" / "fonts.css"
RESEARCH_PACKAGE_DIR = ROOT / "output" / "research_packages"
PAPER_PDF_DIR = ROOT / "output" / "pdf"
TITLE_TRANSLATIONS_CSV = DATA_ROOT / "newspapersg" / "title_translations.csv"
NEWSPAPERSG_CLEAN_DIR = DATA_ROOT / "newspapersg" / "documents_clean"


def h(value: object) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def source_href(value: object) -> str:
    """Hide machine-specific local roots while preserving stable source links."""
    raw = "" if value is None else str(value).strip()
    if not raw:
        return "#"
    is_local = raw.startswith("file://") or raw.startswith("/")
    if is_local and getattr(_request, "public_mode", False):
        return "#"
    if raw.startswith(("file://data/", "file://work/", "file://output/", "file://exports/")):
        return raw
    if raw.startswith("file://"):
        normalized = unquote(urlparse(raw).path)
        for marker in ("/data/", "/work/", "/output/", "/exports/"):
            if marker in normalized:
                return "file://" + marker.strip("/") + "/" + normalized.split(marker, 1)[1]
        return "#"
    if raw.startswith("/"):
        for marker in ("/data/", "/work/", "/output/", "/exports/"):
            if marker in raw:
                return marker + raw.split(marker, 1)[1]
        return "#"
    return raw


def compact(text: str, limit: int = 260) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def asset_version(path: Path) -> str:
    try:
        return str(int(path.stat().st_mtime))
    except OSError:
        return "1"


def load_title_translations() -> dict[str, str]:
    if not TITLE_TRANSLATIONS_CSV.exists():
        return {}
    out: dict[str, str] = {}
    with TITLE_TRANSLATIONS_CSV.open(encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            title = (row.get("title") or "").strip()
            title_zh = (row.get("title_zh") or "").strip()
            if title and title_zh:
                out[title] = title_zh
    return out


TITLE_TRANSLATIONS = load_title_translations()


def newspapersg_clean_text(doc_key: str) -> str:
    if not doc_key.startswith("newspapersg:"):
        return ""
    rest = doc_key.removeprefix("newspapersg:")
    # 防穿越：与 /static/、/sourcebooks/file/ 等路由统一的纵深防御写法。
    # 目前唯一调用点传入的是数据库落地值而非原始 URL 字符串，理论上不可直接触发，
    # 但仍按同样标准加上校验，避免以后有新调用路径把这个函数当成"安全的"。
    if ".." in rest or "/" in rest or "\\" in rest:
        return ""
    path = (NEWSPAPERSG_CLEAN_DIR / f"{rest}.txt").resolve()
    clean_root = NEWSPAPERSG_CLEAN_DIR.resolve()
    if not str(path).startswith(str(clean_root)) or not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


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
    
    # --- CIA 全部文献 (不含东南亚国家) ---
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
    "POLITICAL INFORMATION: CHINESE COMMUNIST PERSONALITIES IN SOUTH CHINA": "政治情报：华南中共人物",
    "CHINESE COMMUNIST VIEW CONCERNING THIRD WORLD WAR": "中共关于第三次世界大战的看法",
    "CHINESE COMMUNIST WOMEN CONNECTED WITH THE WORLD FEDERATION OF DEMOCRATIC WOMEN": "与世界民主妇女联合会有关联的中共女性",
    "POLITICAL INFORMATION: CHINESE COMMUNIST PLANS FOR COALITION GOVERNMENT": "政治情报：中共的联合政府方案",
    "ADMINISTRATIVE DIVISIONS OF CHINA": "中国行政区划",
    "MINISTERS AND DEPUTY MINISTERS OF THE CENTRAL PEOPLE'S GOVERNMENT": "中央人民政府部长与副部长名单",
    "OFFICIALS OF THE EAST CHINA MILITARY AND POLITICAL COUNCIL": "华东军政委员会官员名单",
    "DIRECTORY OF CCP GOVERNMENT PERSONNEL": "中共政府人员名录",
    "ARRESTS, EXECUTIONS, AND OTHER CHINESE COMMUNIST ACTIVITIES": "逮捕、处决及其他中共活动",
    "CHINESE COMMUNIST ACTIVITIES IN EAST CHINA": "中共在华东的活动",
    "COMMUNISTS PUSH CONSTRUCTION OF T'ANG-KU HARBOR, STOP WORK ON HUANG-P'U HARBOR": "共产党推进塘沽港建设、停建黄浦港",
    "CHINESE COMMUNIST ACTIVITIES IN THE HONG KONG AREA": "中共在香港地区的活动",
    "ORGANIZATION AND PERSONNEL OF UNITED FRONT DEPARTMENT OF SOUTH CHINA BUREAU": "中共华南局统战部组织与人员",
    "GOVERNMENT ADMINISTRATION COUNCIL APPROVES PERSONNEL CHANGES": "政务院批准人事变动",
    "CONFERENCE OF THE CHINA FARMERS&#039; AND WORKERS&#039; DEMOCRATIC PARTY": "中国农工民主党会议",
    "TREATMENT OF REPUDIATION OF COMPROMISE WITH WEST IN CHINESE COMMUNIST PRESS, PERIODICALS, FIRST QUARTER 1952": "1952年第一季度中共报刊中对拒绝与西方妥协的处理",
    "ECONOMIC ORGANIZATION OF COMMUNIST CHINA": "共产党中国的经济组织",
    "SMUGGLING OF RUBBER": "橡胶走私",
    "OUTLINE OF NEW ECONOMICS (REVISED LIBERATION EDITION)": "新经济学大纲（修订解放版）",
    "OUTLINE OF PUBLIC FINANCE": "公共财政概论",
    "SURVEY OF CHINA'S FOOD INDUSTRY, 1950": "1950年中国食品工业概况",
    "COMMUNIST CHINA'S POWER POTENTIAL THROUGH 1957": "至1957年共产党中国的力量潜力",
    "COMMUNIST FIRMS, AND PARTY AND MILITARY ORGANIZATIONS IN FOOCHOW": "福州的共产党企业与党军组织",
    
    # --- 新增的 CIA Reading Room 标题翻译 ---
    "CIA Reading Room cia-rdp79-01090a000400060003-9: OFFICE OF REPORTS AND ESTIMATES, CIA FAR EAST/PACIFIC BRANCH": "CIA报告与评估办公室远东及太平洋分部",
    "CIA Reading Room cia-rdp79-01082a000200020005-2: Preliminary survey of the Scope of Hoover Library Materials in the Slavic Languages and on Communism of Prospective Research Value to CIG": "胡佛图书馆关于斯拉夫语言及共产主义馆藏对中情组（CIG）的潜在研究价值初步调查",
    "CIA Reading Room cia-rdp82-00457r000700710008-2: POLITICAL INFORMATION: DISSIDENCE IN CHINESE COMMUNIST PARTY- DIFFERENCES OF OPINION BETWEEN MAO TSS-TUNG AND CHANG WEN-T'IEN": "政治情报：中共内部的异见——毛泽东与张闻天之间的分歧",
    "CIA Reading Room cia-rdp82-00457r001000500004-5: POLITICAL INFORMATION: KUOMINTANG RE-EDUCATION CAMP, SHANGHAI": "政治情报：上海国民党再教育营",
    "CIA Reading Room cia-rdp82-00457r001100080005-0: POLITICAL INFORMATION: REPORTED RESURGENCE OF LI LI-SAN S POLICIES": "政治情报：据报李立三政策复苏",
    "CIA Reading Room cia-rdp78-01617a004600010007-3: OFFICE OF REPORTS AND ESTIMATES, CIA FAR EAST/PACIFIC BRANCH INTELLIGENCE HIGHLIGHTS -- WEEK OF 6 JANUARY - 12 JANUARY": "远东及太平洋分部情报摘要（1月6日-12日）",
    "CIA Reading Room cia-rdp82-00457r001400250001-2: POLITICAN INFORMATION: KOREAN DEMOCRATIC LEAGUE IN DAIREN": "政治情报：大连的朝鲜民主同盟",
    "CIA Reading Room cia-rdp78-01617a003300010001-3: COMMUNIST STRENGTH IN JAPAN ORE 46-48 PUBLISHED 28 SEPTEMBER 1948": "1948年9月28日出版：日本的共产势力",
    "CIA Reading Room cia-rdp78-01617a002100030001-4: WEEKLY SUMMARY NUMBER 24": "第24期周报摘要",
    "CIA Reading Room cia-rdp78-01617a003200040001-1: POSSIBLE DEVELOPMENTS IN CHINA": "中国可能的局势发展",
    "CIA Reading Room cia-rdp82-00457r002100250001-4: POLITICAL INFORMATION: EDITORIAL STAFF OF THE HONG KONG WEN HUI PAO": "政治情报：香港《文汇报》编辑部人员",
    "CIA Reading Room cia-rdp78-01617a003300210001-1: CHINESE COMMUNIST CAPABILITIES FOR CONTROL OF ALL CHINA": "中共控制全中国的能力评估",
    "CIA Reading Room cia-rdp82-00457r002300020004-4: ECONOMIC INFORMATION: HAIAOFENGMAN POWER PLANT": "经济情报：小丰满发电厂",
    "CIA Reading Room cia-rdp82-00457r002300540002-9: REPLY OF LI TSUNG-JEN TO COMMUNIST FOUR-POINT STATEMENT": "李宗仁对共产党四点声明的答复",
    "CIA Reading Room cia-rdp82-00457r002700450001-6: POLITICAL INFORMATION: SPLIT IN DEMOCRATIC LEAGUE": "政治情报：民主同盟的分裂",
    "CIA Reading Room cia-rdp82-00457r002800130003-8: POLITICAL INFORMATION: CHINA DEMOCRATIC LEAGUE MEMBERS' ESCAPE FROM SHANGHAI TO HONG KONG": "政治情报：民盟成员从上海撤往香港",
    "CIA Reading Room cia-rdp82-00457r002800350009-8: LIAISON BETWEEN PRINCE TE AND LEFTIST ORGANIZATIONS": "德王与左翼组织之间的联系",
    "CIA Reading Room cia-rdp82-00457r003000670005-4: PLAN FOR CHANGE IN POLICY FOR MEMBERSHIP IN DEMOCRATIC LEAGUE - LO LUNG-CHI AND CHANG LAN": "民盟成员政策变更方案——罗隆基与张澜",
    "CIA Reading Room cia-rdp82-00457r003500280004-3: ARREST OF MEMBERS OF NEW DEMOCRATIC LEAGUE ON TAIWAN AND QUIESCANCE OF THE FORMOSAN LEAGUE FOR RE-EMANCIPATION": "台湾新民盟成员被捕及台湾再解放联盟的沉寂",
    "CIA Reading Room cia-rdp82-00457r003600420004-6: CURRENT NEWSPAPERS IN PEIPING": "北平现行报纸",
    "CIA Reading Room cia-rdp82-00457r003600570008-6: CURRENT NEWSPAPERS IN SHANGHAI": "上海现行报纸",
    "CIA Reading Room cia-rdp82-00457r003500520001-9: CHOU SAN TSO TSN HUI AND ATTITUDE OF CHINESE COMMUNIST PARTY LEADERS": "舟山作战会议与中共领导人的态度",
    "CIA Reading Room cia-rdp82-00457r004000270010-1: NON-COMMUNIST PARTIES IN THE CHINESE COMMUNIST GOVERNMENT": "共产党政府中的非共产政党",
    "CIA Reading Room cia-rdp80-00809a000600280705-8: OFFICIALS OF SINKIANG PEOPLE'S GOVERNMENT": "新疆人民政府官员",
    "CIA Reading Room cia-rdp82-00457r004600530002-5: COMMUNIST LIAISON PERSONNEL IN NORTHEAST ASIA": "东北亚地区的共产联络人员",
    "CIA Reading Room cia-rdp80-00809a000600310324-7: OFFICIALS OF WU-HAN MUNICIPAL PEOLPLE'S GOVERNMENT, MEMBERS OF CANTON PEOPLE'S GOVERNMENT COUNCIL": "武汉市人民政府官员、广州市人民政府委员",
    "CIA Reading Room cia-rdp82-00457r005200480001-5: LEADING MEMBERS OF THE CHINA DEMOCRATIC LEAGUE": "中国民主同盟主要领导成员",
    "CIA Reading Room cia-rdp82-00457r006100040009-5: PRINTING OF COMMUNIST PROPAGANDA FOR TAIWAN, HONG KONG": "为台湾及香港印刷的共产党宣传品",
    "CIA Reading Room cia-rdp82-00457r007300270002-4: 1. CHINESE COMMUNIST FACILITIES FOR CARE OF WOUNDED 2. RECRUITING AND TRAINING OF CIVILIAN PERSONNEL FOR KOREA": "一、中共伤员护理设施 二、为朝鲜招募与训练平民人员",
    "CIA Reading Room cia-rdp80-00809a000600390004-4: COUNTERREVOLUTIONARY ACTIVITIES IN CHINA": "中国的反革命活动",
    "CIA Reading Room cia-rdp82-00457r007900210006-0: SUMMER TEACHERS' CLASSES SPONSORED BY CHINA DEMOCRATIC LEAGUE": "中国民主同盟主办的暑期教师进修班",
    "CIA Reading Room cia-rdp82-00457r008000690009-3: ALL-CHINA NATURAL WORKERS REPRESENTATIVE CONFERENCE": "全国自然科学工作者代表大会",
    "CIA Reading Room cia-rdp82-00457r009900020008-7: CONTROL OF TAIWAN COMMUNIST PARTY AND DEMOCRATIC LEAGUE FOR TAIWAN AUTONOMY": "对台湾共产党及台湾民主自治同盟的控制",
    "CIA Reading Room cia-rdp80-00809a000700040409-2: ACTIVITIES OF SHENSI PEOPLE'S GOVERNMENT IN 1950": "1950年陕西省人民政府活动",
    "CIA Reading Room cia-rdp82-00457r011700060005-5: PROTEST BY DEMOCRATIC PARTIES AGAINST THREE-ANTI S CAMPAIGN": "各民主党派对三反运动的抗议",
    "CIA Reading Room cia-rdp79t00975a000800420001-9: CURRENT INTELLIGENCE BULLETIN": "当前情报简报",
    "CIA Reading Room cia-rdp80-00809a000700120224-8: OUTLINE OF THE HISTORY OF MODERN ECONOMIC THOUGHT": "近代经济思想史纲要",
    "CIA Reading Room cia-rdp80s01540r003200080003-1: TRANSLATIONS OF NORTH KOREAN NEWSPAPERS": "朝鲜报纸译文",
    "CIA Reading Room cia-rdp80-00810a003500220002-7: CONDITIONS IN CH ANGCHOU, KIANGSU": "江苏常州情况",
    "CIA Reading Room 03193795: CURRENT INTELLIGENCE BULLETIN - 1956/08/10": "当前情报简报 - 1956/08/10",
    "CIA Reading Room 03192683: CURRENT INTELLIGENCE BULLETIN - 1957/11/21": "当前情报简报 - 1957/11/21",
    "CIA Reading Room cia-rdp78-00915r000700150013-4: Afro-Asian Solidarity Conference, Cairo 26 December 1957 - 1 January 1958": "亚非团结会议，开罗 1957年12月26日-1958年1月1日",
    "CIA Reading Room 03003301: CENTRAL INTELLIGENCE BULLETIN - 1958/10/15": "中央情报简报 - 1958/10/15",
    "CIA Reading Room 02066870: CENTRAL INTELLIGENCE BULLETIN - 1960/04/30": "中央情报简报 - 1960/04/30",
    "CIA Reading Room 03174706: CENTRAL INTELLIGENCE BULLETIN - 1960/05/07": "中央情报简报 - 1960/05/07",
    "CIA Reading Room cia-rdp82-00457r008000250007-3: 1. OBSERVATION PARTY BOUND FOR COMMUNIST CHINA 2. STUDENTS BOUND FOR COMMUNIST CHINA": "一、前往中共的观察团 二、前往中共的学生",
    "CIA Reading Room cia-rdp80t00246a072100330001-4: SOCIOLOGICAL, POLITICAL, AND MILITARY INFORMATION ON NORTH KOREA": "朝鲜社会、政治与军事信息",
    "CIA Reading Room cia-rdp79t00975a029600010002-1: NATIONAL INTELLIGENCE BULLETIN": "国家情报简报",
    "CIA Reading Room cia-rdp08-00534r000100180001-3: FACTBOOK 1982": "世界概况 1982",
    "CIA Reading Room 02036417: DAILY SUMMARY - 1946/07/18": "每日摘要 - 1946/07/18",
    "CIA Reading Room 02931559: DAILY SUMMARY - 1946/11/13": "每日摘要 - 1946/11/13",
    "CIA Reading Room 01068507: DAILY SUMMARY - 1946/08/07": "每日摘要 - 1946/08/07",
    "CIA Reading Room 02036414: DAILY SUMMARY - 1946/07/31": "每日摘要 - 1946/07/31",

    # --- Wilson Center ---
    "Democratic Parties and Groups in the Preparatory Committee to Convene a Political Consultative Conference": "召开政治协商会议筹备委员会中的民主党派与团体",
    "Record of Conversation between Soviet Ambassador in China Apollon Petrov and Zhou Enlai and Wang Ruofei": "苏联驻华大使彼得罗夫与周恩来、王若飞会谈记录",
    "Record of Conversation between Soviet Ambassador in China Apollon Petrov and Mao Zedong, Zhou Enlai and Wang Ruofei": "苏联驻华大使彼得罗夫与毛泽东、周恩来、王若飞会谈记录",
    "Anastas Mikoyan's Recollections of his Trip to China": "米高扬中国之行回忆录",
    "Memorandum of Conversation between Anastas Mikoyan and Mao Zedong": "米高扬与毛泽东会谈备忘录",
    "Cable, Mao Zedong [via Kovalev] to Stalin": "毛泽东[经科瓦廖夫]致斯大林密电",
    "Cable, Filippov [Stalin] to Mao Zedong [via Kovalev]": "菲利波夫[斯大林]致毛泽东[经科瓦廖夫]密电",
    "Kovalev reports to Stalin advice on running a communist government": "科瓦廖夫向斯大林报告关于运作共产主义政府的建议",
    "Memorandum of Conversation between Liu Shaoqi and Stalin": "刘少奇与斯大林会谈备忘录",
    "Liu Shaoqi about his meeting with Stalin": "刘少奇关于其与斯大林会谈的报告",
    "Kovalev reports to Stalin on conversation with Mao Zedong": "科瓦廖夫向斯大林报告与毛泽东的会谈",
    "Telegram Mao Zedong to Liu Shaoqi about meeting with Stalin": "毛泽东致刘少奇关于与斯大林会面的密电",
    "Record of conversation between Stalin and Mao Zedong": "斯大林与毛泽东会谈记录",
    "Roshchin Memorandum of Conversation with Prime Minister and Foreign Minister Zhou Enlai": "罗申与周恩来总理兼外长会谈备忘录",
    "Cable, Mao Zedong to Stalin": "毛泽东致斯大林密电",
    "Cable, Terebin to Stalin [via Kuznetsov]": "特列宾致斯大林[经库兹涅佐夫]密电",
    "Report from the Head of the Delegation of the CC of the Chinese Communist Party, 'The Current State of the Chinese Revolution'": "中共代表团团长报告《中国革命现状》",
    "Report from the Head of the Delegation of the Chinese Communist Party CC to Stalin": "中共代表团团长致斯大林报告",
    "Report, Kovalev to Stalin": "科瓦廖夫致斯大林报告",
    "On the People's Democratic Dictatorship: In Commemoration of the Twenty-eighth Anniversary of the Communist Party of China": "论人民民主专政：纪念中国共产党二十八周年",
    "On the People's Democratic Dictatorship: In Commemoration of the Twenty-eighth Anniversary of the Communist Party of China, June 30, 1949": "论人民民主专政：纪念中国共产党二十八周年，1949年6月30日",
    "Report, Peng Dehuai to Mao Zedong and the CCP Central Committee (Excerpt)": "彭德怀致毛泽东及中共中央报告（节选）",
    
    # --- Hoover Institution ---
    "Carsun Chang to Albert C. Wedemeyer · 1947-07-26": "张君劢致魏德迈将军 · 1947-07-26",
    "Carsun Chang to George C. Marshall · 1947-11-01": "张君劢致马歇尔将军 · 1947-11-01",
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
    if title in TITLE_TRANSLATIONS:
        return TITLE_TRANSLATIONS[title]
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
        f"{row['date_guess'] or ''}, {page}, {source_href(source_url)}"
    ).strip()


def domestic_citation_text(row: sqlite3.Row) -> str:
    """Build a Chinese page citation from the formal domestic provenance row.

    Domestic materials do not have FRUS-style volume/document metadata.  The
    citation therefore keeps the source edition, PDF/physical/printed page
    anchors, stable page URL and the file hash together.  It is intentionally
    derived from the page-level provenance record, not from candidate prose.
    """
    title = str(row["title"] or "未题名")
    source_edition = str(row["volume_title"] or "国内史料页")
    date = str(row["date_guess"] or "日期未注明")
    page = source_page_label(row)
    doc_id = str(row["doc_id"] or row["doc_key"] or "")
    page_url = source_href(row["page_url"] or row["doc_url"] or "")
    pdf_page = row["pdf_page_no"] or "未标注"
    physical_page = row["physical_page_no"] or "未标注"
    printed_page = row["printed_page"] or "未标注"
    pdf_anchor = (
        f"PDF 第 {pdf_page} 页"
        if row["pdf_page_no"]
        else "PDF 页：不适用（独立影像页）"
    )
    source_file = str(row["source_file"] or "未绑定")
    source_sha = str(row["source_sha256"] or "未绑定")
    if getattr(_request, "public_mode", False):
        source_file = "内部 provenance 已保存（公开模式隐藏本地路径）"
    return (
        f"页级引用：{title}，{date}，{page}。\n"
        f"出处：{source_edition}；文献标识：{doc_id}。\n"
        f"页码锚点：{pdf_anchor}；物理页 {physical_page}；印刷页 {printed_page}。\n"
        f"页级来源：{page_url}\n"
        f"本地来源文件：{source_file}\n"
        f"来源文件 SHA256：{source_sha}\n"
        f"人工复核说明：{row['human_review_note'] or '未标注'}"
    )


def domestic_provenance_summary(row: sqlite3.Row) -> str:
    """Return a compact provenance panel for a formally citable domestic page."""
    public = getattr(_request, "public_mode", False)
    source_file = (
        "内部 provenance 已保存（公开模式隐藏本地路径）"
        if public
        else str(row["source_file"] or "未绑定")
    )
    image_path = (
        "内部页图已保存（公开模式隐藏本地路径）"
        if public
        else str(row["page_image_path"] or "未绑定")
    )
    source_url = source_href(row["page_url"] or row["doc_url"] or "")
    pdf_page_display = (
        str(row["pdf_page_no"])
        if row["pdf_page_no"]
        else "不适用（独立影像页）"
    )
    return f"""
<section class="meta-card domestic-provenance-card">
  <div class="meta-card-head"><h3><svg class="ico"><use href="#i-archive"/></svg>国内页级 provenance</h3><span class="pstatus ok">human_verified · citation_ready</span></div>
  <div class="meta-card-foot">
    <span><strong>PDF 页</strong> {h(pdf_page_display)}</span>
    <span><strong>物理页</strong> {h(row["physical_page_no"] or "未标注")}</span>
    <span><strong>印刷页</strong> {h(row["printed_page"] or "未标注")}</span>
    <span><strong>来源 SHA256</strong> {h(row["source_sha256"] or "未绑定")}</span>
  </div>
  <div class="snippet"><strong>来源文件：</strong>{h(source_file)}</div>
  <div class="snippet"><strong>页图入口：</strong>{h(image_path)}</div>
  <div class="snippet"><strong>页级 URL：</strong><a href="{h(source_url)}" target="_blank" rel="noreferrer">{h(source_url)}</a></div>
  <div class="snippet"><strong>人工复核：</strong>{h(row["human_review_note"] or "未标注")}</div>
</section>
"""


# 民盟相关度分级 → 前台统一标签（CSS 类 + 显示名）
# 五级体系：核心 / 相关 / 人物关联 / 背景 / 已剔除（前台不展示）
GRADE_CLASS = {
    "核心文献": "core",
    "相关文献": "related",
    "人物关联": "person",
    "背景材料": "background",
    "前台不展示": "excluded",
    "误收已剔除": "excluded",
    # DRNH 三层校订分层（document_classifications.grade 存 A/B/C）
    "A": "core",
    "B": "background",
    "C": "related",
}
# DRNH A/B/C 的前台显示名（内部分层名翻译为读者可理解的相关度）
GRADE_LABEL = {
    "A": "核心文献",
    "B": "背景材料",
    "C": "相关文献",
}


def grade_badge(row: sqlite3.Row) -> str:
    grade = row["grade"] if "grade" in row.keys() else ""
    if not grade:
        return ""
    cls = GRADE_CLASS.get(grade, "background")
    label = GRADE_LABEL.get(grade, grade)
    return f'<span class="grade {cls}">{h(label)}</span>'


def grade_legend_html() -> str:
    """前台分级图例：统一呈现五级相关度标签的含义。"""
    items = [
        ("lg-core", "核心文献", "直接命中民盟 + 核心人物 + 核心事件"),
        ("lg-related", "相关文献", "民盟为重要内容之一"),
        ("lg-person", "人物关联", "经民盟人物间接关联"),
        ("lg-background", "背景材料", "民盟相关背景，不作主要引用"),
        ("lg-excluded", "已剔除", "名称相似无关 / 误收，前台不展示"),
    ]
    parts = "".join(
        f'<span class="lg-item"><span class="lg-dot {cls}"></span>{h(name)}<span style="color:var(--muted-soft);">· {h(desc)}</span></span>'
        for cls, name, desc in items
    )
    return (
        '<div class="grade-legend">' + parts +
        '<a href="/standards" style="margin-left:auto;">收录与排除标准 →</a></div>'
    )


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
# 本研究平台只收录中国大陆境外一手原始档案；人物档案仅用于档案翻译人名标准化和上下文理解
from person_archive import PEOPLE  # noqa: E402

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
    ("library", "i-library", "资料库", [
        ("/", "首页"),
        ("/about", "项目介绍"),
        ("/docs", "全部文档"),
        ("/domestic", "国内史料库"),
        ("/research", "多源专题研究"),
        ("/domestic/library", "国内核心可阅"),
        ("/domestic/events", "国内事件墙"),
        ("/domestic/sources", "国内来源"),
        ("/domestic/academic", "国内学术研究"),
        ("/papers", "研究论文"),
        ("/sourcebooks", "史料长编"),
        ("/standards", "收录标准"),
        ("/timeline", "年表"),
        ("/glossary", "术语表"),
    ]),
    ("workbench", "i-edit", "研究工作台", [
        ("/domestic?layer=background", "国内背景线索"),
        ("/domestic/search", "国内 staging 检索"),
        ("/domestic/quality", "国内质量底座"),
        ("/domestic/acquisition", "国内调档清单"),
        ("/domestic/review", "国内复核"),
        ("/align", "多源对位"),
        ("/cards", "证据卡片库"),
        ("/tasks", "校订任务"),
        ("/quality", "质量检查"),
        ("/drnh-review", "DRNH校订"),
        ("/first-person", "第一人称史料"),
        ("/hk-press", "香港报刊源"),
        ("/l1-board", "L1升级看板"),
        ("/external-acquisition", "外部调档"),
        ("/open-sources", "开放资料源"),
        ("/dashboard", "进度仪表盘"),
    ]),
    ("topics", "i-people", "人物索引", [("/people", "人物"), ("/places", "地点"), ("/organizations", "机构")]),
]

# 公开模式：隐藏 workbench 组（内部校订/质量/后台路径），保留 library + topics
# 通过 cookie public_mode=1 或 query ?public=1 开启
PUBLIC_HIDDEN_GROUPS = {"workbench"}
PUBLIC_HIDDEN_PATHS = {"/tasks", "/quality", "/drnh-review", "/external-acquisition",
                        "/open-sources", "/dashboard", "/review", "/excluded", "/domestic/review",
                        "/domestic/evidence-review", "/domestic/search", "/domestic/document"}

PUBLIC_DOMESTIC_LEVELS = {"L0", "L1", "L2", "L3"}


def _public_domestic_candidate_visible(row: sqlite3.Row | dict) -> bool:
    """公开模式只允许显式 public 且处于 L0—L3 的国内记录。"""
    accepted = row["authenticity_level_accepted"] if "authenticity_level_accepted" in row.keys() else None
    proposed = row["authenticity_level_proposed"] if "authenticity_level_proposed" in row.keys() else None
    level = str(accepted or proposed or "").strip()
    rights = str(row["rights_status"] or "").strip().lower() if "rights_status" in row.keys() else ""
    return level in PUBLIC_DOMESTIC_LEVELS and rights == "public"


def _public_domestic_document_visible(c: sqlite3.Connection, document_id: int) -> bool:
    """通过候选与文档的显式关系判断正式国内文档是否可公开。"""
    try:
        rows = c.execute(
            """SELECT authenticity_level_proposed, authenticity_level_accepted, rights_status
               FROM domestic_candidates WHERE ingested_document_id=?""",
            (document_id,),
        ).fetchall()
    except sqlite3.Error:
        return False
    return any(_public_domestic_candidate_visible(row) for row in rows)


def nav_active(path: str) -> str:
    """根据当前 path 推断激活的主导航分组。"""
    if path in ("/", "/focus"):
        return "library"
    for group_key, _, _, items in NAV_GROUPS:
        for href, _ in items:
            if path == href or (href != "/" and path.startswith(href + "/")):
                return group_key
    if path.startswith("/doc/") or path.startswith("/cite/") or path.startswith("/papers/"):
        return "library"
    if path.startswith("/review/"):
        return "workbench"
    if path.startswith(("/people/", "/places/", "/organizations/")):
        return "topics"
    return ""


def layout(title: str, body: str, query: str = "", active_path: str = "") -> bytes:
    # 优先使用调用方明确传的 active_path；否则从 thread-local 取（do_GET 设置）
    if not active_path:
        active_path = getattr(_request, "path", "/") or "/"
    # 公开模式：从 thread-local 取（do_GET 解析 cookie/query 后设置）
    public_mode = bool(getattr(_request, "public_mode", False))
    active_group = nav_active(active_path)
    nav_html = ""
    for group_key, icon_id, group_label, items in NAV_GROUPS:
        # 公开模式下隐藏 workbench 组（内部校订/质量/后台路径）
        if public_mode and group_key in PUBLIC_HIDDEN_GROUPS:
            continue
        is_active = group_key == active_group
        cls = "nav-group active" if is_active else "nav-group"
        sub = "".join(
            f'<a class="nav-sub{" current" if href == active_path else ""}" href="{href}">{h(label)}</a>'
            for href, label in items
        )
        nav_html += f'''
        <div class="{cls}">
          <button class="nav-main" type="button" onclick="this.closest('.nav-group').classList.toggle('is-open')"><svg class="ico"><use href="#{icon_id}"/></svg>{h(group_label)}<svg class="ico nav-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg></button>
          <div class="nav-flyout">{sub}</div>
        </div>'''
    # 公开模式 banner（提示用户当前处于公开模式 + 退出按钮）
    public_banner = ""
    if public_mode:
        public_banner = '<div style="background:#f4ead4;border-bottom:1px solid #d4ba7a;padding:6px 14px;font-size:12px;color:#5a4a26;text-align:center;">📖 公开介绍版 · 仅显示公开档案与研究成果 · <a href="/?public=0" style="color:#0f6b5b;font-weight:bold;">退出公开模式</a></div>'
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <title>{h(title)} · 民盟历史文献研究库</title>
  <link rel="stylesheet" href="/static/fonts.css?v={asset_version(FONTS_CSS_PATH)}">
  <link rel="stylesheet" href="/static/style.css?v={asset_version(STYLE_PATH)}">
</head>
<body>
  {ICONS_SVG}
  {public_banner}
  <header class="topbar">
    <a class="brand" href="/">
      <span>民盟历史文献研究库</span>
      <span class="brand-sub">FRUS · CIA · Wilson · Hoover · HathiTrust · DRNH · NewspaperSG · 国内史料</span>
    </a>
    <button class="nav-toggle" type="button" aria-label="打开导航" aria-controls="mainnav" aria-expanded="false" onclick="(function(b){{var n=document.getElementById('mainnav');var o=n.classList.toggle('is-open');b.setAttribute('aria-expanded',o);b.classList.toggle('is-open',o);}})(this)">
      <svg class="ico ico-lg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M4 7h16M4 12h16M4 17h16"/></svg>
    </button>
    <form class="search" method="get" action="/search" role="search">
      <input name="q" value="{h(query)}" placeholder="搜索英文原文或中文译文，例如「罗隆基」「Marshall」「政协」">
      <button type="submit"><svg class="ico"><use href="#i-search"/></svg>搜索</button>
    </form>
    <nav class="mainnav" id="mainnav">
      {nav_html}
    </nav>
  </header>
  <main>{body}</main>
  <footer class="site-footer">
    <div class="footer-inner">
      <div class="footer-top">
        <div class="footer-brand">
          <span class="footer-title">民盟历史文献研究库</span>
          <span class="footer-desc">系统整理 1941—1950 年中国民主同盟境外档案与国内史料 · 分层证据与多源互证体系</span>
        </div>
        <div class="footer-links">
          <a href="/">首页</a>
          <a href="/docs">全部文档</a>
          <a href="/people">人物索引</a>
          <a href="/timeline">文献年表</a>
          <a href="/dashboard">研究仪表盘</a>
          <a href="/sourcebooks">史料长编</a>
        </div>
      </div>
      <div class="footer-meta">
        数据来源：FRUS · CIA FOIA · Wilson Center · Hoover Institution · HathiTrust · 台北档案史料 (DRNH) · NewspaperSG · 国内史料层<br>
        本站为学术研究工具，所有档案均保留原始出处引用
      </div>
    </div>
  </footer>
</body>
</html>""".encode("utf-8")


from platforms import PLATFORM_META  # noqa: E402  (优化 2-F 抽出)


def platforms_panel_html(c: sqlite3.Connection) -> str:
    """档案平台入口面板：境外七源与国内史料层。"""
    # 动态计算每个平台的数据规模
    plat_counts = {}
    try:
        for r in c.execute("""
            SELECT COALESCE(d.source_platform,'frus') AS p, count(*) AS n
            FROM documents d
            LEFT JOIN document_classifications dc ON dc.document_id=d.id
            WHERE COALESCE(dc.grade, '') <> '前台不展示'
            GROUP BY p
        """):
            plat_counts[r['p']] = r['n']
    except sqlite3.OperationalError:
        plat_counts = {}
    frus_docs = plat_counts.get('frus', 0)
    # 全部限定到 FRUS 平台自身（之前是全库统计，被 drnh 稀释导致显示 65%）
    try:
        frus_pages = c.execute(
            "SELECT count(*) FROM pages p JOIN documents d ON p.document_id=d.id "
            "WHERE COALESCE(d.source_platform,'frus')='frus'"
        ).fetchone()[0]
        frus_zh = c.execute(
            "SELECT count(*) FROM translations t "
            "JOIN pages p ON t.page_id=p.id "
            "JOIN documents d ON p.document_id=d.id "
            "WHERE t.language='zh-CN' AND COALESCE(d.source_platform,'frus')='frus'"
        ).fetchone()[0]
        frus_human = c.execute(
            "SELECT count(*) FROM translations t "
            "JOIN pages p ON t.page_id=p.id "
            "JOIN documents d ON p.document_id=d.id "
            "WHERE t.language='zh-CN' AND t.status='human-reviewed' "
            "AND COALESCE(d.source_platform,'frus')='frus'"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        frus_pages = frus_zh = frus_human = 0
    frus_pct = (frus_human * 100 // frus_zh) if frus_zh else 0

    # 排卡片：已上线优先于未上线；台北档案（目前仅案由、无全文内容）固定排最后；
    # 其余按真实文档数降序
    ordered_keys = sorted(
        PLATFORM_META.keys(),
        key=lambda k: (
            0 if PLATFORM_META[k]["active"] else 1,   # 已上线在前
            1 if k == "drnh" else 0,                   # 台北档案固定垫底
            -plat_counts.get(k, 0),                    # 其余按文档数降序
        ),
    )
    cards = []
    for key in ordered_keys:
        meta = PLATFORM_META[key]
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
    domestic_docs = plat_counts.get("domestic", 0)
    try:
        domestic_pages = c.execute(
            "SELECT count(*) FROM pages p JOIN documents d ON p.document_id=d.id "
            "WHERE d.source_platform='domestic'"
        ).fetchone()[0]
    except sqlite3.OperationalError:
        domestic_pages = 0
    cards.append(f'''
<a class="platform-card active" href="/domestic/library">
  <h3>国内资料库</h3>
  <div class="pmeta">国内史料层 · 同期报刊 · 公开扫描 · 官方来源</div>
  <div class="pdesc">已收 {domestic_docs} 篇国内资料文档、{domestic_pages} 个页面；可查看已收文献，候选目录与复核状态另行保留。</div>
  <div class="pstatus ok">已上线 · {domestic_docs} 篇</div>
</a>''')
    return '<section class="platforms">' + "".join(cards) + "</section>"


def sourcebook_paths(platform_key: str) -> list[Path]:
    if platform_key == "drnh" or not (ROOT / "workspace").exists():
        return []
    paths = []
    for path in sorted((ROOT / "workspace").glob("民盟史料长编_*.pdf")):
        key = path.name.rsplit("_", 1)[-1].removesuffix(".pdf")
        if key == platform_key:
            paths.append(path)
    return paths


def file_size_label(path: Path) -> str:
    size = path.stat().st_size
    if size >= 1024 * 1024:
        return f"{size / (1024 * 1024):.1f} MB"
    return f"{max(1, size // 1024)} KB"


def research_package_path(platform_key: str) -> Path | None:
    path = RESEARCH_PACKAGE_DIR / f"民盟研究资料包_{platform_key}.zip"
    return path if path.is_file() else None


def paper_pdf_path(platform_key: str) -> Path | None:
    path = PAPER_PDF_DIR / f"mingmeng-{platform_key}-paper.pdf"
    return path if path.is_file() else None


def paper_pdf_links_html(platform_key: str, button_class: str = "button") -> str:
    path = paper_pdf_path(platform_key)
    if not path:
        return ""
    href = f"/papers/file/{quote(path.name)}"
    return (
        f'<a class="{button_class}" href="{h(href)}" target="_blank">'
        f'<svg class="ico"><use href="#i-book"/></svg>下载论文 PDF '
        f'<span class="muted">({h(file_size_label(path))})</span></a>'
    )


def research_package_links_html(platform_key: str, button_class: str = "button") -> str:
    path = research_package_path(platform_key)
    if not path:
        return ""
    href = f"/packages/file/{quote(path.name)}"
    return (
        f'<a class="{button_class}" href="{h(href)}">'
        f'<svg class="ico"><use href="#i-archive"/></svg>下载资料包 ZIP '
        f'<span class="muted">({h(file_size_label(path))})</span></a>'
    )


def sourcebook_links_html(platform_key: str, button_class: str = "button") -> str:
    links = []
    for path in sourcebook_paths(platform_key):
        href = f"/sourcebooks/file/{quote(path.name)}"
        label = "下载长编上卷" if "_上卷_" in path.name else "下载长编下卷" if "_下卷_" in path.name else "下载史料长编"
        links.append(
            f'<a class="{button_class}" href="{h(href)}" target="_blank">'
            f'<svg class="ico"><use href="#i-book"/></svg>{label} <span class="muted">({h(file_size_label(path))})</span></a>'
        )
    return "".join(links)


def source_page(platform_key: str) -> bytes:
    """单个档案平台或国内史料层的专属栏目页。"""
    meta = PLATFORM_META.get(platform_key)
    if not meta:
        return layout("未知平台", '<div class="notice">未知的平台。可选：' + " / ".join(PLATFORM_META.keys()) + "</div>")

    with conn() as c:
        # 取此平台的文档清单（前台过滤 grade='前台不展示'）
        # drnh 平台特别处理：默认只取 A 档（核心 223 条），按时间线排序
        try:
            if platform_key == "drnh":
                docs_rows = c.execute("""
                    SELECT documents.*, dc.grade
                    FROM documents
                    LEFT JOIN document_classifications dc ON dc.document_id=documents.id
                    WHERE COALESCE(source_platform, 'frus')=?
                      AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                      AND dc.grade='A'
                    ORDER BY documents.date_guess, documents.doc_id
                """, (platform_key,)).fetchall()
            else:
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
        # 取该平台 A/B 档分布（用于动态填入 coverage/todo_note 占位符，避免数据更新后过时）
        try:
            stat_rows = c.execute("""
                SELECT COALESCE(dc.grade, '-') AS g, COUNT(*) AS n
                FROM documents
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                WHERE COALESCE(source_platform, 'frus') = ?
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                GROUP BY g
            """, (platform_key,)).fetchall()
            grade_map = {r["g"]: r["n"] for r in stat_rows}
            n_a = grade_map.get("A", 0)
            n_b = grade_map.get("B", 0)
            n_total = sum(grade_map.values())
        except Exception:
            n_a = n_b = n_total = n_docs

    # 动态填充占位符 {n_a} / {n_b} / {n_total}（仅有占位时才替换，避免影响其他平台）
    def _fmt(s: str) -> str:
        if not s or "{n_" not in s:
            return s
        try:
            return s.format(n_a=n_a, n_b=n_b, n_total=n_total)
        except (KeyError, IndexError):
            return s
    coverage_str = _fmt(meta.get("coverage", ""))
    todo_note_str = _fmt(meta.get("todo_note", ""))
    sourcebook_tools = paper_pdf_links_html(platform_key) + sourcebook_links_html(platform_key) + research_package_links_html(platform_key)
    # 5/26 19:50 新增：研究论文入口
    paper_link = ''
    if platform_key in {"frus", "cia", "drnh", "hathitrust", "wilson", "hoover", "newspapersg"}:
        paper_link = f'<a class="button" href="/papers/{platform_key}"><svg class="ico"><use href="#i-quote"/></svg>研究论文</a>'
    sourcebook_tools = (paper_link + sourcebook_tools) if paper_link else sourcebook_tools

    highlights_html = "".join(f"<li>{item}</li>" for item in meta.get("highlights", []))

    if meta.get("status") is not None:
        status_text = meta["status"]
    elif meta.get("active") and n_docs > 0:
        status_text = f"已上线 · {n_docs} 篇"
    elif meta.get("active"):
        status_text = "已上线"
    else:
        status_text = "待开发"

    platform_scope = "国内研究平台" if platform_key == "domestic" else "境外档案平台"
    body = breadcrumb_html([("/", "首页"), (None, f"{platform_scope} · {meta['name']}")]) + f"""
<section class="hero" style="padding:32px 36px;">
  <h1>{h(meta['name'])} <span style="font-size:18px;color:var(--muted);font-weight:400;">· {h(meta['cn_name'])}</span></h1>
  <p class="hero-sub">{h(meta['intro'])}</p>
  <div class="hero-meta">
    <span><b>视角</b> {h(meta['perspective'])}</span>
    <span><b>时间覆盖</b> {h(coverage_str)}</span>
    <span><b>状态</b> <span class="pstatus {meta['status_class']}" style="margin-left:4px;">{h(status_text)}</span></span>
  </div>
  {f'<div class="doc-tools" style="margin-top:18px;justify-content:center;">{sourcebook_tools}</div>' if sourcebook_tools else ''}
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
  <a class="more" href="/docs?platform={platform_key}">完整列表 →</a>
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
  <div class="cite"><a href="{h(source_href(r["url"]))}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
        if n_docs > 20:
            body += f'<div style="padding:14px 22px;text-align:center;border-top:1px solid var(--line-soft);"><a class="button" href="/docs?platform={platform_key}">查看全部 {n_docs} 篇 →</a></div>'
        body += "</section>"
    elif meta["active"]:
        body += '<div class="notice">本平台已上线，但当前数据库中尚无文档。</div>'
    else:
        body += f'''
<div class="section-head">
  <h2><svg class="ico"><use href="#i-clock"/></svg>开发路线</h2>
</div>
<section class="notice archival">
  <p style="margin:0;font-family:var(--serif);line-height:1.85;">{h(todo_note_str or "暂无说明。")}</p>
</section>
'''
    return layout(f"{meta['name']} · {platform_scope}", body)


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
        ("length_too_short", "译文过短"),
        ("length_long", "译文偏长"),
        ("core_machine_draft", "核心初稿"),
        ("missing_translation", "缺少译文"),
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
    # Domestic topics use the same event-index route as the foreign topics,
    # but remain explicitly marked as a domestic navigation layer.  The
    # loader is defined later in this module; runtime lookup is safe after
    # module initialization and keeps the JSON coverage table authoritative.
    domestic_loader = globals().get("domestic_event_by_slug")
    if domestic_loader:
        return domestic_loader(slug)
    return None


def domestic_event_by_slug(slug: str) -> dict[str, object] | None:
    """Return a domestic coverage event in the shared event-index shape."""
    coverage_loader = globals().get("_load_domestic_event_coverage")
    if not coverage_loader:
        return None
    for item in coverage_loader():
        if str(item.get("event_id")) != str(slug):
            continue
        cards_loader = globals().get("_load_topic_comparison_cards")
        cards = cards_loader() if cards_loader else {}
        comparison = cards.get(str(slug), {})
        academic_terms = comparison.get("academic_terms", []) if isinstance(comparison, dict) else []
        return {
            "slug": str(slug),
            "event_id": str(slug),
            "name": item.get("event_name", slug),
            "brief": item.get("domestic_status", "国内专题导航"),
            "terms": [str(term) for term in academic_terms if str(term).strip()],
            "source": "domestic",
            "domestic_status": item.get("domestic_status", ""),
        }
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


def rows_for_search(
    c: sqlite3.Connection,
    query: str,
    limit: int = 50,
    platform: str | None = None,
    year: str = "",
    grade: str = "",
    person: str = "",
    cited: bool = False,
) -> list[sqlite3.Row]:
    """统一搜索：FTS5 trigram + LIKE 兜底 + 繁简自动展开 + 多词 AND 分词。

    问题修复历史：
    - FTS5 默认 unicode61 不切中文 → 已改 trigram tokenizer（rebuild_fts_trigram.py）
    - trigram 要求 query 至少 3 个 Unicode 字符，2 字符短词（戴笠/张澜/民盟）走 LIKE 兜底
    - 多词 query（如「保密局 魏德邁」）原来用 LIKE 整段必 0 命中，现在按空格拆 + AND 合取
    - 繁简自动展开：搜简体「魏德迈」时自动也搜繁体「魏德邁」
    """
    SELECT_BASE = """
        SELECT
            pages.id AS page_id,
            documents.volume_id, documents.doc_id, documents.doc_key,
            documents.date_guess, documents.title, documents.matched_terms,
            COALESCE(documents.source_platform, 'frus') AS source_platform,
            documents.hit_type,
            dc.grade, dc.score,
            pages.page_label, pages.page_url,
            pages.text AS original_text,
            translations.text AS zh_text,
            translations.status AS zh_status
    """

    filter_clauses: list[str] = []
    filter_params: list[str] = []
    if platform:
        filter_clauses.append("COALESCE(documents.source_platform, 'frus') = ?")
        filter_params.append(platform)
    if year.strip():
        filter_clauses.append("substr(COALESCE(documents.date_guess, ''), 1, 4) = ?")
        filter_params.append(year.strip()[:4])
    if grade.strip():
        filter_clauses.append("dc.grade = ?")
        filter_params.append(grade.strip())
    if person.strip():
        person_like = f"%{person.strip()}%"
        filter_clauses.append(
            "(documents.title LIKE ? OR documents.matched_terms LIKE ? OR pages.text LIKE ? OR IFNULL(translations.text, '') LIKE ?)"
        )
        filter_params.extend([person_like, person_like, person_like, person_like])
    if cited:
        cited_keys = paper_cited_doc_keys(c)
        if not cited_keys:
            return []
        placeholders = ",".join("?" for _ in cited_keys)
        filter_clauses.append(f"documents.doc_key IN ({placeholders})")
        filter_params.extend(cited_keys)

    filter_clause = "".join(f" AND {clause}" for clause in filter_clauses)
    has_filters = bool(filter_clauses)

    if not query.strip():
        if not has_filters:
            return []
        sql = f"""
            {SELECT_BASE}
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            WHERE (dc.grade IS NULL OR dc.grade != '前台不展示')
              {filter_clause}
            ORDER BY documents.date_guess, documents.doc_key, pages.id
            LIMIT ?
        """
        return list(c.execute(sql, tuple(filter_params) + (limit,)))

    # 拆词（空格/逗号分隔）
    tokens = [t for t in re.split(r"[\s,，、;；]+", query.strip()) if t]
    # 繁简双向展开：尝试导入 zhconv
    expanded_tokens = []
    for tok in tokens:
        variants = {tok}
        try:
            import zhconv
            variants.add(zhconv.convert(tok, "zh-cn"))
            variants.add(zhconv.convert(tok, "zh-tw"))
        except Exception:
            pass
        expanded_tokens.append(list(variants))

    seen: set[int] = set()
    out: list[sqlite3.Row] = []

    def _add_rows(sql: str, params: tuple):
        for row in c.execute(sql, params):
            if row["page_id"] in seen:
                continue
            out.append(row)
            seen.add(row["page_id"])

    # 路径 1: FTS5（中文走 bigram 表，英文走 trigram 表），多 token AND
    # - CJK 词 → bigram phrase（预切 bigram，2 字词单 token 命中，多字相邻命中）
    # - 纯英文 3+ 词 → trigram 表（原逻辑）
    # 两类都命中才返回（跨表结果按 page_id 去重合并）
    cjk_re = re.compile(r"[\u3400-\u9fff]+")
    try:
        # CJK token → bigram 表子句（phrase）
        bg_parts = []
        # 纯英文 token（>=3 字符）→ trigram 表子句
        tr_parts = []
        for variants in expanded_tokens:
            any_cjk = any(cjk_re.search(v) for v in variants)
            if any_cjk:
                # 任一变体满足即可（OR），多 token 之间 AND
                phrases = []
                for v in variants:
                    # 把该变体内的连续 CJK 段切成相邻 bigram phrase
                    v_phrases = []
                    for m in cjk_re.finditer(v):
                        seg = m.group(0)
                        bgs = [seg[i : i + 2] for i in range(len(seg) - 1)]
                        if bgs:
                            v_phrases.append('"' + " ".join(bgs) + '"')
                    # 变体内英文片段单独作为词（unicode61 空格分词）
                    for m in re.finditer(r"[A-Za-z0-9]+", v):
                        v_phrases.append(f'"{m.group(0)}"')
                    if v_phrases:
                        phrases.append("(" + " AND ".join(v_phrases) + ")")
                if phrases:
                    bg_parts.append("(" + " OR ".join(phrases) + ")")
            else:
                valid = [v for v in variants if len(v) >= 3]
                if valid:
                    # FTS5 quote: "..."，双引号需转义为 ""，否则用户输入里的 " 能提前闭合短语、
                    # 注入 FTS5 查询语法（如列过滤器/布尔操作符）
                    quoted = " OR ".join('"{}"'.format(v.replace('"', '""')) for v in valid)
                    tr_parts.append(f"({quoted})")

        if bg_parts:
            bg_q = " AND ".join(bg_parts)
            sql = f"""
                {SELECT_BASE}
                FROM page_fts_bigram
                JOIN pages ON pages.id = page_fts_bigram.rowid
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                WHERE page_fts_bigram MATCH ?
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                  {filter_clause}
                LIMIT ?
            """
            _add_rows(sql, (bg_q,) + tuple(filter_params) + (limit,))
            sql2 = f"""
                {SELECT_BASE}
                FROM translation_fts_bigram
                JOIN translations ON translations.id = translation_fts_bigram.rowid
                JOIN pages ON pages.id = translations.page_id
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                WHERE translation_fts_bigram MATCH ?
                  AND translations.language='zh-CN'
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                  {filter_clause}
                LIMIT ?
            """
            _add_rows(sql2, (bg_q,) + tuple(filter_params) + (limit,))

        if tr_parts:
            tr_q = " AND ".join(tr_parts)
            sql = f"""
                {SELECT_BASE}
                FROM page_fts
                JOIN pages ON pages.id = page_fts.rowid
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                WHERE page_fts MATCH ?
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                  {filter_clause}
                LIMIT ?
            """
            _add_rows(sql, (tr_q,) + tuple(filter_params) + (limit,))
            sql2 = f"""
                {SELECT_BASE}
                FROM translation_fts
                JOIN translations ON translations.id = translation_fts.rowid
                JOIN pages ON pages.id = translations.page_id
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                WHERE translation_fts MATCH ?
                  AND translations.language='zh-CN'
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                  {filter_clause}
                LIMIT ?
            """
            _add_rows(sql2, (tr_q,) + tuple(filter_params) + (limit,))
    except sqlite3.OperationalError:
        pass

    # 路径 2: LIKE 兜底（处理短词 < 3 字符 + 中文模糊匹配）
    # 路径 2: LIKE 兜底（处理 1 字中文 + 非 CJK 短词 <3 字符，bigram 表已覆盖 2+ 字中文）
    # 每个 token 用任一变体 LIKE 都算命中（OR），多 token 用 AND 取交
    need_like = any(len(t) < 3 and not cjk_re.search(t) for t in tokens) or any(len(t) < 2 for t in tokens)
    if (not out or need_like) and need_like:
        like_conds_parts = []
        like_params: list = []
        for variants in expanded_tokens:
            # bigram 表已覆盖 2+ 字中文，此处只对「1 字中文 / 非 CJK 短词」走 LIKE
            skip = all(cjk_re.search(v) and len(v) >= 2 for v in variants)
            if skip:
                continue
            # 对单 token 的多变体：在 (text OR title OR matched_terms OR translations.text) 任一字段 LIKE
            sub_parts = []
            for v in variants:
                like_v = f"%{v}%"
                sub_parts.append(
                    "(pages.text LIKE ? OR documents.title LIKE ? OR documents.matched_terms LIKE ? OR IFNULL(translations.text,'') LIKE ?)"
                )
                like_params.extend([like_v, like_v, like_v, like_v])
            if sub_parts:
                like_conds_parts.append("(" + " OR ".join(sub_parts) + ")")
        if like_conds_parts:
            like_where = " AND ".join(like_conds_parts)
            sql = f"""
                {SELECT_BASE}
                FROM pages
                JOIN documents ON documents.id = pages.document_id
                LEFT JOIN document_classifications dc ON dc.document_id = documents.id
                LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
                WHERE {like_where}
                  AND (dc.grade IS NULL OR dc.grade != '前台不展示')
                  {filter_clause}
                LIMIT ?
            """
            _add_rows(sql, tuple(like_params) + tuple(filter_params) + (limit,))
    return out[:limit]


def _search_domestic_evidence_labels(
    c: sqlite3.Connection, rows: list[sqlite3.Row]
) -> dict[int, str]:
    """给统一搜索结果补充国内页级证据状态，不读取正文。

    境外结果沿用原有的档案分级；国内结果还需要告诉研究者“正式可引用”
    和“机器可阅”不是同一件事。测试/全新 checkout 可能没有
    ``page_provenance``，此时安静地返回空映射，不能让统一搜索失效。
    """
    domestic_ids = [
        int(row["page_id"])
        for row in rows
        if str(row["source_platform"] or "frus") == "domestic"
    ]
    if not domestic_ids:
        return {}
    try:
        exists = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='page_provenance'"
        ).fetchone()
        if not exists:
            return {}
        placeholders = ",".join("?" for _ in domestic_ids)
        provenance_rows = c.execute(
            f"""
            SELECT page_id, source_file, source_sha256, citation_ready,
                   needs_human_review, review_status, human_review_note
            FROM page_provenance
            WHERE page_id IN ({placeholders})
            """,
            tuple(domestic_ids),
        ).fetchall()
    except sqlite3.Error:
        return {}

    labels: dict[int, str] = {}
    for row in provenance_rows:
        page_id = int(row["page_id"])
        strict = bool(
            int(row["citation_ready"] or 0) == 1
            and int(row["needs_human_review"] or 0) == 0
            and str(row["review_status"] or "") == "human_verified"
            and str(row["human_review_note"] or "").strip()
        )
        machine = bool(
            int(row["needs_human_review"] or 0) == 0
            and str(row["review_status"] or "") in {"machine_verified", "human_verified"}
        )
        anchored = bool(
            str(row["source_file"] or "").strip()
            and re.fullmatch(r"[0-9a-fA-F]{64}", str(row["source_sha256"] or ""))
        )
        if strict:
            labels[page_id] = "正式可引用"
        elif machine:
            labels[page_id] = "机器可阅" + (" · 已锚定原件" if anchored else "")
        elif anchored:
            labels[page_id] = "原件已锚定 · 待复核"
        else:
            labels[page_id] = "证据待补"
    return labels


def result_html(row: sqlite3.Row, evidence_label: str = "") -> str:
    page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
    href = f"/doc/{quote(row['doc_key'])}?page_id={row['page_id']}"
    terms = [t.strip() for t in (row["matched_terms"] or "").split(";") if t.strip()]
    tags = "".join(f'<span class="tag">{h(t)}</span>' for t in terms[:6])
    grade = grade_badge(row)
    platform = str(row["source_platform"] or "frus")
    if platform == "domestic":
        tags = '<span class="tag">国内史料</span>' + tags
        if evidence_label:
            tags += f'<span class="tag">{h(evidence_label)}</span>'
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
  <div class="cite"><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">原始来源</a><br>{h(page)}</div>
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
    sourcebook_files = sorted((ROOT / "workspace").glob("民盟史料长编_*.pdf")) if (ROOT / "workspace").exists() else []
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
    <a class="button" href="/drnh-review">DRNH校订</a>
    <a class="button" href="/external-acquisition">外部调档</a>
    <a class="button" href="/open-sources">开放资料源</a>
    <a class="button" href="/sourcebooks">史料长编</a>
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
  <div class="stat"><strong>{len(sourcebook_files)}</strong><span>长编 PDF</span></div>
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


def sourcebooks_page() -> bytes:
    platforms = [
        ("frus", "美国对外关系文件集"),
        ("drnh", "国民政府档案"),
        ("cia", "美国中央情报局解密档案"),
        ("wilson", "威尔逊中心数字档案"),
        ("hoover", "胡佛研究所档案"),
        ("hathitrust", "HathiTrust 数字典藏"),
        ("newspapersg", "NewspaperSG 南洋报刊"),
    ]
    files: dict[str, list[Path]] = {key: sourcebook_paths(key) for key, _ in platforms}
    packages: dict[str, Path | None] = {key: research_package_path(key) for key, _ in platforms}
    body = breadcrumb_html([("/", "首页"), ("/dashboard", "研究工作台"), (None, "史料长编")]) + """
<section class="doc-head">
  <div>
    <h1>史料长编</h1>
  <div class="meta">按平台汇编原文与中文译文，供专题阅读、打印和阶段性整理。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/dashboard">仪表盘</a>
    <a class="button" href="/docs">全部文档</a>
  </div>
</section>
<section class="result-list">
"""
    for key, label in platforms:
        paths = files.get(key, [])
        package = packages.get(key)
        links = []
        status_parts = []
        if paths:
            for path in paths:
                href = f"/sourcebooks/file/{quote(path.name)}"
                label_text = "上卷" if "_上卷_" in path.name else "下卷" if "_下卷_" in path.name else "打开 PDF"
                links.append(f'<a href="{h(href)}" target="_blank">{label_text}</a> <span class="muted">({h(file_size_label(path))})</span>')
            status_parts.append(f'<span class="tag">PDF {len(paths)} 份</span>')
        if package:
            href = f"/packages/file/{quote(package.name)}"
            links.append(f'<a href="{h(href)}">整包 ZIP</a> <span class="muted">({h(file_size_label(package))})</span>')
            status_parts.append('<span class="tag">资料包 ZIP</span>')
        if links:
            cite = "<br>".join(links)
            status = "".join(status_parts)
        else:
            cite = "待生成"
            status = '<span class="tag muted">未生成</span>'
        body += f"""
  <article class="result">
    <div>
      <h2>{h(label)}</h2>
      <div class="tagline">{status}<span class="tag">{h(key)}</span></div>
    </div>
    <div class="cite">{cite}</div>
  </article>"""
    body += "</section>"
    return layout("史料长编", body, active_path="/sourcebooks")


def read_csv_rows(path: Path, limit: int = 200) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[:limit]


def drnh_review_page(active_tier: str = "") -> bytes:
    all_rows = read_csv_rows(DATA_ROOT / "drnh_review_layers.csv", 1000)
    rows = [row for row in all_rows if not active_tier or row.get("tier") == active_tier]
    counts: dict[str, int] = {}
    for row in all_rows:
        tier = row.get("tier") or "未分层"
        counts[tier] = counts.get(tier, 0) + 1

    chips = []
    for value, label in [("", "全部"), ("重点校订", "重点校订"), ("常规校订", "常规校订"), ("背景保留", "背景保留")]:
        href = "/drnh-review" + (f"?tier={quote(value)}" if value else "")
        cls = "button active" if value == active_tier else "button"
        chips.append(f'<a class="{cls}" href="{href}">{h(label)}</a>')

    body = breadcrumb_html([("/", "首页"), ("/dashboard", "研究工作台"), (None, "DRNH校订")]) + f"""
<section class="doc-head">
  <div>
    <h1>DRNH 校订队列</h1>
    <div class="meta">把国史馆自动入库材料按研究价值分层；优先处理“重点校订”，其余作为背景材料保留。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/dashboard">仪表盘</a>
    <a class="button" href="/docs?platform=drnh">DRNH文档</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(counts.get("重点校订", 0))}</strong><span>重点校订</span></div>
  <div class="stat"><strong>{h(counts.get("常规校订", 0))}</strong><span>常规校订</span></div>
  <div class="stat"><strong>{h(counts.get("背景保留", 0))}</strong><span>背景保留</span></div>
</section>
<div class="filters">{''.join(chips)}</div>
"""
    if not rows:
        body += '<div class="notice">还没有生成 DRNH 校订队列。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows[:80]:
            page_id = row.get("page_id") or ""
            doc_key = row.get("doc_key") or ""
            doc_href = f"/doc/{quote(doc_key)}?page_id={quote(page_id)}" if doc_key and page_id else "#"
            body += f"""
<article class="result">
  <div>
    {title_block(row.get("title") or "未题名", doc_href)}
    <div class="meta">优先级 {h(row.get("review_score"))} · {h(row.get("date_guess"))} · {h(row.get("doc_key"))}</div>
    <div class="tagline">
      <span class="tag">{h(row.get("tier"))}</span>
      <span class="tag">等级 {h(row.get("grade"))}</span>
      <span class="tag">分类分 {h(row.get("class_score"))}</span>
    </div>
    <div class="snippet">{h(row.get("reason"))}</div>
  </div>
  <div class="cite"><a href="/review/{h(page_id)}">校订</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(row.get("url"))}" target="_blank" rel="noreferrer">馆藏页</a></div>
</article>"""
        body += "</section>"
    return layout("DRNH校订队列", body, active_path="/drnh-review")


def l1_board_page() -> bytes:
    """L1 证据等级升级看板（读 data/l1_upgrade_queue.csv）。"""
    rows = read_csv_rows(DATA_ROOT / "l1_upgrade_queue.csv", 200)
    pri: dict[str, int] = {}
    for row in rows:
        p = (row.get("priority") or "其他").strip()
        pri[p] = pri.get(p, 0) + 1
    body = breadcrumb_html([("/", "首页"), ("/dashboard", "研究工作台"), (None, "L1 升级看板")]) + f"""
<section class="doc-head">
  <div>
    <h1>L1 证据等级升级看板</h1>
    <div class="meta">把各源"待核问题清单"与证据卡片里点名的"待升 L1"判断，汇成一张可跟踪任务表——把研究的下一步从"再写一遍"转成"把 L4 判断坐实成 L1 事实"。等级：L1 一手原档已核 / L2 已下待核 / L3 目录元数据 / L4 LLM 精读。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/cards">证据卡片库</a>
    <a class="button" href="/dashboard">仪表盘</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(pri.get("P0", 0))}</strong><span>P0 最优先</span></div>
  <div class="stat"><strong>{h(pri.get("P1", 0))}</strong><span>P1 重要</span></div>
  <div class="stat"><strong>{h(pri.get("P2", 0))}</strong><span>P2 待查</span></div>
  <div class="stat"><strong>{h(len(rows))}</strong><span>升级任务合计</span></div>
</section>
"""
    if not rows:
        body += '<div class="notice">L1 升级看板为空。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows[:120]:
            body += f"""
<article class="result">
  <div>
    <h3 class="result-title">{h(row.get("claim") or "未命名待核点")}</h3>
    <div class="meta">{h(row.get("priority"))} · {h(row.get("event"))} · 等级 {h(row.get("level_now"))} → {h(row.get("target_level"))} · 状态：{h(row.get("status"))}</div>
    <div class="snippet">来源：{h(row.get("source"))}</div>
    <div class="tagline">
      <span class="tag">待核档案：{h(row.get("archive_to_check"))}</span>
      <span class="tag">动作：{h(row.get("action"))}</span>
    </div>
  </div>
</article>"""
        body += "</section>"
    return layout("L1 证据等级升级看板", body, active_path="/l1-board")


def hk_press_page() -> bytes:
    """香港报刊开放源（读 data/hk_press_sources.csv）——IA 港报可抓源登记。"""
    rows = read_csv_rows(DATA_ROOT / "hk_press_sources.csv", 100)
    grab = sum(1 for r in rows if "可抓" in (r.get("status") or ""))
    body = breadcrumb_html([("/", "首页"), ("/dashboard", "研究工作台"), (None, "香港报刊源")]) + f"""
<section class="doc-head">
  <div>
    <h1>香港报刊·开放可抓源</h1>
    <div class="meta">补"港埠舆论"维度的中文港媒。Internet Archive 已数字化华侨日报、工商晚报、大公报（香港版）等约 4.9 万期，全文 OCR、开放可批量抓取（已实测）；报道民盟非法化与海外活动，与现有 HathiTrust 英文港媒形成中英双语对照。注：1940s 繁体密排 OCR 噪声大，须清洗＋模糊匹配。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/first-person">第一人称史料</a>
    <a class="button" href="/external-acquisition">外部调档</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(len(rows))}</strong><span>登记报刊源</span></div>
  <div class="stat"><strong>{h(grab)}</strong><span>开放可抓（IA）</span></div>
</section>
"""
    if not rows:
        body += '<div class="notice">香港报刊源清单为空。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows[:60]:
            body += f"""
<article class="result">
  <div>
    <h3 class="result-title">{h(row.get("paper") or "未命名")}</h3>
    <div class="meta">{h(row.get("platform"))} · {h(row.get("era"))} · {h(row.get("language"))} · 状态：{h(row.get("status"))}</div>
    <div class="snippet">馆藏：{h(row.get("holdings"))} · 民盟相关：{h(row.get("meng_relevance"))}</div>
    <div class="tagline">
      <span class="tag">访问：{h(row.get("access"))}</span>
      <span class="tag">抓取：{h(row.get("harvest"))}</span>
    </div>
  </div>
</article>"""
        body += "</section>"
    return layout("香港报刊开放源", body, active_path="/hk-press")


def first_person_page() -> bytes:
    """民盟第一人称一手史料获取清单（读 data/first_person_acquisition.csv）。"""
    rows = read_csv_rows(DATA_ROOT / "first_person_acquisition.csv", 200)
    pri: dict[str, int] = {}
    for row in rows:
        p = (row.get("priority") or "其他").strip()
        pri[p] = pri.get(p, 0) + 1
    body = breadcrumb_html([("/", "首页"), ("/dashboard", "研究工作台"), (None, "第一人称史料")]) + f"""
<section class="doc-head">
  <div>
    <h1>民盟第一人称一手史料</h1>
    <div class="meta">补境外七源最大盲区——七源里民盟几乎全是"被观察"，唯一主体之声仅张君劢两函。本清单把"民盟自己说话"的材料（机关报刊／领导人日记文集／自编文献汇编）从线索变为可跟踪任务；中文一手不翻译，仅 OCR、繁简统一与页码引用。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/external-acquisition">外部调档</a>
    <a class="button" href="/dashboard">仪表盘</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(pri.get("P0", 0))}</strong><span>P0 最优先</span></div>
  <div class="stat"><strong>{h(pri.get("P1", 0))}</strong><span>P1 重要</span></div>
  <div class="stat"><strong>{h(pri.get("P2", 0))}</strong><span>P2 待查</span></div>
  <div class="stat"><strong>{h(len(rows))}</strong><span>清单合计</span></div>
</section>
"""
    if not rows:
        body += '<div class="notice">第一人称史料清单为空。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows[:80]:
            body += f"""
<article class="result">
  <div>
    <h3 class="result-title">{h(row.get("material") or "未命名材料")}</h3>
    <div class="meta">{h(row.get("priority"))} · {h(row.get("source_type"))} · 入库代码 {h(row.get("platform_code"))} · 状态：{h(row.get("status"))}</div>
    <div class="snippet">目标范围：{h(row.get("target_scope"))}</div>
    <div class="tagline">
      <span class="tag">渠道：{h(row.get("channel"))}</span>
      <span class="tag">动作：{h(row.get("next_action"))}</span>
      <span class="tag">交付：{h(row.get("deliverable"))}</span>
    </div>
  </div>
</article>"""
        body += "</section>"
    body += """
<section class="doc-head" style="margin-top:18px;">
  <div>
    <div class="meta" style="font-size:13px;line-height:1.8;">
      <b>入库判断规则：</b>本人日记／本人文集原文／本组织机关报刊／本组织自编文件汇编 → <b>一手正式层</b>；
      回忆录、纪念文章、政协文史资料、后人传记 → 仅<b>参考层</b>，不单独支撑结论。
      每件须留来源字段（藏处／卷期／日期／页码／获取方式／是否可公开），并优先与境外七源做"同日／同事件"互证。
    </div>
  </div>
</section>
"""
    return layout("民盟第一人称一手史料", body, active_path="/first-person")


def external_acquisition_page() -> bytes:
    rows = read_csv_rows(DATA_ROOT / "external_acquisition_queue.csv", 200)
    counts: dict[str, int] = {}
    for row in rows:
        archive = row.get("archive") or "未分馆藏"
        if "National Archives" in archive or "HKPRO" in archive:
            group = "Kew / HKPRO"
        elif "中研院" in archive:
            group = "Sinica"
        else:
            group = archive
        counts[group] = counts.get(group, 0) + 1

    body = breadcrumb_html([("/", "首页"), ("/dashboard", "研究工作台"), (None, "外部调档")]) + f"""
<section class="doc-head">
  <div>
    <h1>外部档案调档队列</h1>
    <div class="meta">用于推进未能直接在线批量入库的高价值档案：先询价、确认页数和复制限制，再进入 OCR、翻译和页码引用流程。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/dashboard">仪表盘</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(counts.get("Kew / HKPRO", 0))}</strong><span>Kew / HKPRO</span></div>
  <div class="stat"><strong>{h(counts.get("Sinica", 0))}</strong><span>Sinica 阅览室</span></div>
</section>
"""
    if not rows:
        body += '<div class="notice">还没有外部调档队列。</div>'
    else:
        body += '<section class="result-list">'
        for row in rows[:80]:
            url = row.get("url") or ""
            link = url if url else "#"
            body += f"""
<article class="result">
  <div>
    {title_block(row.get("title") or row.get("ref") or "未题名", link)}
    <div class="meta">{h(row.get("priority"))} · {h(row.get("archive"))} · {h(row.get("ref"))} · {h(row.get("date"))}</div>
    <div class="tagline">
      <span class="tag">{h(row.get("access"))}</span>
      <span class="tag">{h(row.get("next_action"))}</span>
    </div>
    <div class="snippet">{h(row.get("note"))}</div>
  </div>
  <div class="cite"><a href="{h(link)}" target="_blank" rel="noreferrer">馆藏入口</a></div>
</article>"""
        body += "</section>"
    return layout("外部档案调档队列", body, active_path="/external-acquisition")


def open_sources_page() -> bytes:
    rows = read_csv_rows(DATA_ROOT / "open_source_probe.csv", 200)
    records = read_csv_rows(DATA_ROOT / "open_source_records.csv", 200)
    groups: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        groups.setdefault(row.get("source_line") or "未分组", []).append(row)

    available_count = sum(1 for row in rows if (row.get("probe_status") or "").startswith("200"))
    blocked_count = sum(1 for row in rows if not (row.get("probe_status") or "").startswith("200"))
    gpa_count = len(groups.get("GPA 民国报刊开放库", []))
    nus_count = len(groups.get("NUS 南侨日报", []))
    jacar_count = len(groups.get("JACAR 日本亚洲历史资料中心", []))

    body = breadcrumb_html([("/", "首页"), ("/dashboard", "研究工作台"), (None, "开放资料源")]) + f"""
<section class="doc-head">
  <div>
    <h1>开放资料源探勘</h1>
    <div class="meta">用于推进可以免费访问、后续可自动抓取全文或图像的资料源；付费扫描或到馆调档仍放在外部调档队列。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/dashboard">仪表盘</a>
    <a class="button" href="/external-acquisition">外部调档</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(len(rows))}</strong><span>候选入口</span></div>
  <div class="stat"><strong>{h(available_count)}</strong><span>入口可访问</span></div>
  <div class="stat"><strong>{h(blocked_count)}</strong><span>需接口处理</span></div>
  <div class="stat"><strong>{h(gpa_count)}</strong><span>GPA</span></div>
  <div class="stat"><strong>{h(nus_count)}</strong><span>NUS</span></div>
  <div class="stat"><strong>{h(jacar_count)}</strong><span>JACAR</span></div>
  <div class="stat"><strong>{h(len(records))}</strong><span>真实候选</span></div>
</section>
"""
    if records:
        body += """
<div class="section-head">
  <h2><svg class="ico"><use href="#i-check"/></svg>已验证可入库记录</h2>
</div>
<section class="result-list">
"""
        for record in records:
            url = record.get("url") or "#"
            body += f"""
<article class="result">
  <div>
    {title_block(record.get("title") or "未题名", url)}
    <div class="meta">{h(record.get("archive"))} · {h(record.get("date"))} · {h(record.get("pages"))} 页 · {h(record.get("access"))}</div>
    <div class="tagline">
      <span class="tag">{h(record.get("source_line"))}</span>
      <span class="pstatus ok">{h(record.get("status"))}</span>
    </div>
    <div class="snippet">{h(record.get("relevance"))}</div>
    <div class="snippet"><strong>下一步：</strong>{h(record.get("next_action"))}</div>
  </div>
  <div class="cite"><a href="{h(url)}" target="_blank" rel="noreferrer">打开记录</a></div>
</article>"""
        body += "</section>"
    if not rows:
        body += '<div class="notice">还没有开放资料源探勘清单。请先运行 scripts/probe/probe_open_sources.py。</div>'
    else:
        for source_line, items in groups.items():
            body += f"""
<div class="section-head">
  <h2><svg class="ico"><use href="#i-archive"/></svg>{h(source_line)}</h2>
</div>
<section class="result-list">
"""
            for row in items:
                url = row.get("url") or "#"
                status = row.get("probe_status") or ""
                status_cls = "ok" if status.startswith("200") else "warn"
                body += f"""
<article class="result">
  <div>
    {title_block(row.get("title") or row.get("query") or "未题名", url)}
    <div class="meta">{h(row.get("priority"))} · {h(row.get("archive"))} · 检索词：{h(row.get("query"))}</div>
    <div class="tagline">
      <span class="tag">{h(row.get("access"))}</span>
      <span class="pstatus {status_cls}">{h(status)}</span>
    </div>
    <div class="snippet">{h(row.get("note"))}</div>
    <div class="snippet"><strong>下一步：</strong>{h(row.get("next_action"))}</div>
  </div>
  <div class="cite"><a href="{h(url)}" target="_blank" rel="noreferrer">打开入口</a></div>
</article>"""
            body += "</section>"
    return layout("开放资料源探勘", body, active_path="/open-sources")


# 国内前台分层：默认只展示核心可阅/一手层；网页史志与二手线索进背景层。
DOMESTIC_BACKGROUND_REPOS = frozenset({
    "SH", "PP", "CAIXIN", "SCIO", "XINHUA", "CPC", "RMZXB", "RMZXW", "ZSY", "CSSN",
    "RMTZ", "ACAD", "MM1941", "8P", "WM", "QY", "MMHIST", "MMC", "MGCH", "SCU", "ZJ",
})
DOMESTIC_WEB_URL_MARKERS = (
    "sohu.com", "caixin.com", "people.com.cn", "xinhuanet.com", "rmzxb.com.cn",
    "gmw.cn", "cssn.cn", "zysy.org.cn", "thepaper.cn",
)
DOMESTIC_WEB_TYPE_MARKERS = (
    "网站", "网页", "新闻", "转载", "专题报道", "白皮书", "公众号", "政务号", "博士论文", "学术期刊",
)

# Formal citation is deliberately stricter than machine-readable/search-ready.
# A domestic page may be useful for reading after provenance/OCR checks, but it
# is not a formal citation until a human reviewer records an explicit note.
DOMESTIC_STRICT_CITATION_SQL = """
    pp.citation_ready = 1
    AND pp.needs_human_review = 0
    AND pp.review_status = 'human_verified'
    AND trim(COALESCE(pp.human_review_note, '')) <> ''
"""
DOMESTIC_MACHINE_READABLE_SQL = """
    pp.needs_human_review = 0
    AND pp.review_status IN ('machine_verified', 'human_verified')
"""


def _domestic_citation_is_strict(row: sqlite3.Row | dict) -> bool:
    """Return True only for a domestic page that passed recorded human review."""
    return bool(
        int(row["citation_ready"] or 0) == 1
        and int(row["needs_human_review"] or 0) == 0
        and str(row["provenance_review_status"] or "") == "human_verified"
        and str(row["human_review_note"] or "").strip()
    )


def _domestic_level(row: sqlite3.Row | dict) -> str:
    accepted = row["authenticity_level_accepted"] if "authenticity_level_accepted" in row.keys() else None
    proposed = row["authenticity_level_proposed"] if "authenticity_level_proposed" in row.keys() else None
    return str(accepted or proposed or "").strip()


def _domestic_is_background_candidate(row: sqlite3.Row | dict) -> bool:
    """网页史志、二手学术、官网锚点等不得进入默认核心列表。"""
    level = _domestic_level(row)
    if level in {"L3", "L4", "LX"}:
        return True
    repo = str(row["repository_code"] or "").strip()
    if repo in DOMESTIC_BACKGROUND_REPOS:
        return True
    dtype = str(row["document_type"] or "")
    if any(marker in dtype for marker in DOMESTIC_WEB_TYPE_MARKERS):
        return True
    url = str(row["source_url"] or "").lower()
    if any(marker in url for marker in DOMESTIC_WEB_URL_MARKERS):
        return True
    return False


def _domestic_core_documents_sql(term: str = "", core_only: bool = True, limit: int | None = None) -> tuple[str, list[object]]:
    """已入库国内文档：严格引用、机器核验可阅与 OCR 检索稿分层。"""
    params: list[object] = []
    where = ["d.source_platform = 'domestic'"]
    if term:
        where.append("(d.title LIKE ? OR d.doc_key LIKE ? OR COALESCE(d.volume_title, '') LIKE ?)")
        like = f"%{term}%"
        params.extend([like, like, like])
    having = ""
    if core_only:
        having = " HAVING cite_pages > 0 OR machine_pages > 0 OR (text_chars >= 2000 AND page_count >= 2 AND COALESCE(d.hit_type, '') LIKE '%ocr%')"
    sql = f"""
        SELECT
            d.id, d.doc_key, d.title, d.date_guess, d.url, d.volume_title,
            d.doc_id, d.doc_number, d.source_id, d.hit_type,
            COUNT(p.id) AS page_count,
            SUM(CASE WHEN {DOMESTIC_STRICT_CITATION_SQL} THEN 1 ELSE 0 END) AS cite_pages,
            SUM(CASE WHEN {DOMESTIC_MACHINE_READABLE_SQL} THEN 1 ELSE 0 END) AS machine_pages,
            SUM(length(COALESCE(p.text, ''))) AS text_chars
        FROM documents d
        LEFT JOIN pages p ON p.document_id = d.id
        LEFT JOIN page_provenance pp ON pp.page_id = p.id
        WHERE {' AND '.join(where)}
        GROUP BY d.id
        {having}
        ORDER BY
          CASE
            WHEN d.date_guess IS NOT NULL AND d.date_guess >= '1941' AND d.date_guess < '1951' THEN 0
            WHEN d.date_guess IS NULL OR trim(d.date_guess) = '' THEN 1
            ELSE 2
          END,
          cite_pages DESC, machine_pages DESC, text_chars DESC, COALESCE(d.date_guess, '9999-99-99'), d.id
    """
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return sql, params


def domestic_library_page(query: dict[str, list[str]] | None = None) -> bytes:
    """国内核心可阅库：默认只列可阅读的一手/OCR 文档，不混入网页背景。"""
    query = query or {}
    term = query.get("q", [""])[0].strip()
    layer = query.get("layer", ["core"])[0].strip() or "core"
    core_only = layer != "all"
    with conn() as c:
        sql, params = _domestic_core_documents_sql(term=term, core_only=core_only)
        rows = c.execute(sql, params).fetchall()
        total_docs = c.execute(
            "SELECT count(*) FROM documents WHERE source_platform='domestic'"
        ).fetchone()[0]
        core_sql, core_params = _domestic_core_documents_sql(core_only=True)
        core_count = len(c.execute(core_sql, core_params).fetchall())
        total_pages = c.execute(
            """
            SELECT count(*) FROM pages p
            JOIN documents d ON d.id=p.document_id
            WHERE d.source_platform='domestic'
            """
        ).fetchone()[0]
        cite_pages = c.execute(
            f"""
            SELECT count(*) FROM pages p
            JOIN documents d ON d.id = p.document_id
            JOIN page_provenance pp ON pp.page_id = p.id
            WHERE d.source_platform = 'domestic' AND {DOMESTIC_STRICT_CITATION_SQL}
            """
        ).fetchone()[0]
        machine_pages = c.execute(
            f"""
            SELECT count(*) FROM pages p
            JOIN documents d ON d.id = p.document_id
            JOIN page_provenance pp ON pp.page_id = p.id
            WHERE d.source_platform = 'domestic' AND {DOMESTIC_MACHINE_READABLE_SQL}
            """
        ).fetchone()[0]

    core_cls = "button" if core_only else "button secondary"
    all_cls = "button" if not core_only else "button secondary"
    body = breadcrumb_html([("/", "首页"), ("/domestic", "国内史料库"), (None, "核心可阅")]) + f"""
<section class="doc-head">
  <div>
    <h1>国内核心可阅库</h1>
    <div class="meta">对标境外档案源的阅读层：默认同期原刊/原件 OCR 与 citation 页；网页史志与二手线索不在此列。</div>
  </div>
  <div class="doc-tools">
    <a class="{core_cls}" href="/domestic/library?layer=core">仅核心可阅</a>
    <a class="{all_cls}" href="/domestic/library?layer=all">全部已收</a>
    <a class="button secondary" href="/domestic">国内史料库首页</a>
    <a class="button secondary" href="/domestic?layer=background">背景线索</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(core_count)}</strong><span>核心可阅文档</span></div>
  <div class="stat"><strong>{h(total_docs)}</strong><span>全部已收</span></div>
  <div class="stat"><strong>{h(cite_pages)}</strong><span>人工核验可引用页</span></div>
  <div class="stat"><strong>{h(machine_pages)}</strong><span>机器核验可阅页</span></div>
  <div class="stat"><strong>{h(total_pages)}</strong><span>物理页面</span></div>
  <div class="stat"><strong>{h(len(rows))}</strong><span>当前结果</span></div>
</section>
<div class="notice">核心口径：人工核验可引用、机器核验可阅或 OCR 正文≥2000 字且≥2 页。只有 human_verified 且具人工复核说明的页面才计入正式引用；机器核验和 OCR 仅供阅读、检索与待审。</div>
<form method="get" action="/domestic/library" class="filter-form">
  <input type="hidden" name="layer" value="{h(layer)}">
  <label>检索 <input name="q" value="{h(term)}" placeholder="题名、档号或来源"></label>
  <button class="button" type="submit">筛选</button>
  <a class="button secondary" href="/domestic/library?layer={h(layer)}">清除</a>
</form>
<div class="section-head"><h2><svg class="ico"><use href="#i-book"/></svg>{'核心可阅' if core_only else '全部已收'}文档（{h(len(rows))} 篇）</h2></div>
<section class="result-list">
"""
    if not rows:
        body += '<div class="notice">当前筛选没有找到国内资料。</div>'
    else:
        for row in rows:
            href = f"/doc/{quote(row['doc_key'])}" if row["doc_key"] else "/domestic/library"
            source_href = row["url"] or "#"
            cite = int(row["cite_pages"] or 0)
            machine = int(row["machine_pages"] or 0)
            badge = "人工核验可引用" if cite > 0 else ("机器核验可阅" if machine > 0 else "OCR 检索稿")
            body += f"""
<article class="result">
  <div>
    {title_block(row["title"] or "未题名国内资料", href)}
    <div class="meta">{h(row["date_guess"] or "日期未注明")} · {h(row["volume_title"] or row["source_id"] or "来源未标注")} · {h(row["page_count"])} 页 · 人工引用 {h(cite)} · 机器可阅 {h(machine)}</div>
    <div class="tagline"><span class="tag">{h(badge)}</span><span class="tag">{h(row["hit_type"] or "domestic")}</span></div>
  </div>
  <div class="cite"><a href="{h(href)}">阅读文献</a><br><a href="{h(source_href)}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
    body += "</section>"
    return layout("国内核心可阅", body, active_path="/domestic/library")


def domestic_page(query: dict[str, list[str]] | None = None) -> bytes:
    """国内史料库主入口：事件墙 + 核心可阅 + 背景/工作台（默认不把网页线索当核心库）。"""
    query = query or {}
    term = query.get("q", [""])[0].strip()
    level = query.get("level", [""])[0].strip()
    repository = query.get("repository", [""])[0].strip()
    relevance = query.get("relevance", [""])[0].strip()
    review = query.get("review", [""])[0].strip()
    event = query.get("event", [""])[0].strip()
    layer = query.get("layer", ["core"])[0].strip() or "core"
    if layer not in {"core", "background", "all", "workbench"}:
        layer = "core"
    event_options = [
        ("1941民盟前身", "1941民盟前身"),
        ("1944改组更名", "1944改组更名"),
        ("1945民盟一大", "1945民盟一大"),
        ("1946旧政协", "1946旧政协"),
        ("1946拒绝国民大会", "1946拒绝国民大会"),
        ("1946李闻血案", "1946李闻血案"),
        ("1947民盟被宣布非法", "1947民盟被宣布非法"),
        ("1948五一口号", "1948五一口号"),
        ("1949政协一届全会", "1949第一届政协"),
        ("1949开国大典", "1949开国大典"),
    ]
    try:
        coverage_path = DATA_ROOT / "domestic" / "event_coverage.json"
        coverage = json.loads(coverage_path.read_text(encoding="utf-8")) if coverage_path.exists() else []
        with conn() as c:
            total_candidates = c.execute("SELECT count(*) FROM domestic_candidates").fetchone()[0]
            accepted_count = c.execute(
                "SELECT count(*) FROM domestic_candidates WHERE review_status = 'accepted'"
            ).fetchone()[0]
            pending = c.execute(
                "SELECT count(*) FROM domestic_candidates WHERE review_status = 'needs_human_review'"
            ).fetchone()[0]
            repository_options = [
                row[0]
                for row in c.execute(
                    "SELECT DISTINCT repository_code FROM domestic_candidates ORDER BY repository_code"
                ).fetchall()
                if row[0]
            ]
            # 候选全量（含 accepted 等级）供分层
            cand_rows = c.execute(
                """
                SELECT candidate_id, title, document_type, source_url, repository_code,
                       authenticity_level_proposed, authenticity_level_accepted,
                       relevance_grade_proposed, review_status, rights_status, evidence_note,
                       uncertainty_note, event_tags, ingested_document_id
                FROM domestic_candidates
                ORDER BY id
                """
            ).fetchall()
            core_docs_sql, core_docs_params = _domestic_core_documents_sql(core_only=True, limit=24)
            core_docs = c.execute(core_docs_sql, core_docs_params).fetchall()
            core_docs_count_sql, _ = _domestic_core_documents_sql(core_only=True)
            core_docs_total = len(c.execute(core_docs_count_sql).fetchall())
            cite_pages = c.execute(
                f"""
                SELECT count(*) FROM pages p
                JOIN documents d ON d.id = p.document_id
                JOIN page_provenance pp ON pp.page_id = p.id
                WHERE d.source_platform = 'domestic' AND {DOMESTIC_STRICT_CITATION_SQL}
                """
            ).fetchone()[0]
            machine_pages = c.execute(
                f"""
                SELECT count(*) FROM pages p
                JOIN documents d ON d.id = p.document_id
                JOIN page_provenance pp ON pp.page_id = p.id
                WHERE d.source_platform = 'domestic' AND {DOMESTIC_MACHINE_READABLE_SQL}
                """
            ).fetchone()[0]
            domestic_doc_total = c.execute(
                "SELECT count(*) FROM documents WHERE source_platform='domestic'"
            ).fetchone()[0]
            domestic_page_total = c.execute(
                """SELECT count(*) FROM pages p
                   JOIN documents d ON d.id=p.document_id
                   WHERE d.source_platform='domestic'"""
            ).fetchone()[0]
            source_anchored_pages = c.execute(
                """SELECT count(*) FROM page_provenance pp
                   JOIN documents d ON d.id=pp.document_id
                   WHERE d.source_platform='domestic'
                     AND trim(COALESCE(pp.source_file,''))<>''
                     AND length(trim(COALESCE(pp.source_sha256,'')))=64"""
            ).fetchone()[0]
            missing_provenance_pages = c.execute(
                """SELECT count(*) FROM pages p
                   JOIN documents d ON d.id=p.document_id
                   LEFT JOIN page_provenance pp ON pp.page_id=p.id
                   WHERE d.source_platform='domestic' AND pp.page_id IS NULL"""
            ).fetchone()[0]
            missing_date_documents = c.execute(
                """SELECT count(*) FROM documents
                   WHERE source_platform='domestic'
                     AND trim(COALESCE(date_guess,''))=''"""
            ).fetchone()[0]
            # 权威来源卡：优先档案/馆藏类，压低网站门户
            sources = c.execute(
                """
                SELECT source_name, institution, source_type, authority_level,
                       official_url, access_mode, shanghai_relevance, status
                FROM domestic_sources
                WHERE authority_level IN ('A', 'B')
                   OR source_type LIKE '%档案%'
                   OR source_type LIKE '%报刊%'
                   OR source_type LIKE '%馆藏%'
                   OR source_type LIKE '%文献%'
                ORDER BY
                  CASE authority_level WHEN 'A' THEN 0 WHEN 'B' THEN 1 ELSE 2 END,
                  shanghai_relevance DESC, source_name
                LIMIT 18
                """
            ).fetchall()
    except sqlite3.OperationalError:
        return layout(
            "国内史料库",
            '<div class="notice">国内史料表尚未初始化，请先运行 scripts/domestic/ingest_domestic.py。</div>',
            active_path="/domestic",
        )

    if getattr(_request, "public_mode", False):
        cand_rows = [
            row for row in cand_rows
            if _public_domestic_candidate_visible(row)
        ]

    core_cands: list[sqlite3.Row] = []
    background_cands: list[sqlite3.Row] = []
    for row in cand_rows:
        if _domestic_is_background_candidate(row):
            background_cands.append(row)
        else:
            core_cands.append(row)

    def _match_candidate(row: sqlite3.Row) -> bool:
        if term:
            blob = " ".join(
                str(row[k] or "")
                for k in ("title", "document_type", "evidence_note", "uncertainty_note", "event_tags")
            )
            if term not in blob and term not in str(row["candidate_id"]):
                # also check person via evidence only — creator not always selected
                if term.lower() not in blob.lower():
                    return False
        if level:
            if _domestic_level(row) != level and row["authenticity_level_proposed"] != level:
                return False
        if repository and (row["repository_code"] or "") != repository:
            return False
        if relevance and (row["relevance_grade_proposed"] or "") != relevance:
            return False
        if review and (row["review_status"] or "") != review:
            return False
        if event and event not in str(row["event_tags"] or ""):
            return False
        return True

    filtered_core = [r for r in core_cands if _match_candidate(r)]
    filtered_bg = [r for r in background_cands if _match_candidate(r)]
    show_filters = bool(term or level or repository or relevance or review or event or layer in {"background", "all"})

    list_title = ""
    if layer == "background":
        list_rows = filtered_bg
        list_title = "背景与线索（网页史志 / 二手 / 官网锚点）"
    elif layer == "all":
        list_rows = filtered_core + filtered_bg
        list_title = "全部候选（含背景）"
    elif show_filters:
        list_rows = filtered_core
        list_title = "筛选结果（核心候选，不含网页背景）"
    else:
        list_rows = []

    event_value_set = [value for _, value in event_options]
    # 事件墙：核心候选计数 + 原 coverage 元数据
    event_cards = []
    for item in coverage:
        ids = set(item.get("domestic_candidate_ids") or [])
        core_n = sum(1 for r in core_cands if r["candidate_id"] in ids)
        bg_n = sum(1 for r in background_cands if r["candidate_id"] in ids)
        event_tag = ""
        for r in core_cands + background_cands:
            if r["candidate_id"] not in ids:
                continue
            tags = _domestic_tag_values(r["event_tags"])
            for value in event_value_set:
                if value in tags:
                    event_tag = value
                    break
            if event_tag:
                break
        href = f"/domestic?layer=core&event={quote(event_tag)}" if event_tag else "/domestic?layer=core"
        pair_ok = item.get("pair_status") == "pair_available"
        event_cards.append(f"""
<article class="result">
  <div>
    <div class="title">{h(item.get("event_name", "未命名事件"))}</div>
    <div class="meta">国内状态：{h(item.get("domestic_status", ""))}</div>
    <div class="tagline">
      <span class="tag">核心 {h(core_n)}</span>
      <span class="tag">背景 {h(bg_n)}</span>
      <span class="pstatus {'ok' if pair_ok else 'warn'}">{h("境外已关联" if item.get("foreign_event_slugs") else "境外待补")}</span>
    </div>
    <div class="snippet">{h(item.get("review_note", ""))}</div>
  </div>
  <div class="cite"><a href="{h(href)}">查看核心证据</a><br>候选共 {h(len(ids))} 条</div>
</article>""")
    # 核心文档精选
    doc_cards = []
    for row in core_docs:
        href = f"/doc/{quote(row['doc_key'])}" if row["doc_key"] else "/domestic/library"
        cite = int(row["cite_pages"] or 0)
        machine = int(row["machine_pages"] or 0)
        status_label = "人工核验可引用" if cite > 0 else ("机器核验可阅" if machine > 0 else "OCR 检索稿")
        doc_cards.append(f"""
<article class="result">
  <div>
    {title_block(row["title"] or "未题名", href)}
    <div class="meta">{h(row["date_guess"] or "日期未注明")} · {h(row["page_count"])} 页 · 人工引用 {h(cite)} · 机器可阅 {h(machine)} · {h(row["hit_type"] or "")}</div>
    <div class="tagline"><span class="tag">{h(status_label)}</span><span class="pstatus ok">正式库</span></div>
  </div>
  <div class="cite"><a href="{h(href)}">阅读</a></div>
</article>""")

    layer_core_cls = "button" if layer == "core" and not show_filters else "button secondary"
    layer_bg_cls = "button" if layer == "background" else "button secondary"
    layer_all_cls = "button" if layer == "all" else "button secondary"

    body = breadcrumb_html([("/", "首页"), (None, "国内史料库")]) + f"""
<section class="doc-head">
  <div>
    <h1>国内史料库</h1>
    <div class="meta">与境外七源并列的国内阅读层：核心可阅文献 · 九大事件证据墙 · 背景线索与调档工作台分册</div>
  </div>
  <div class="doc-tools">
    <a class="{layer_core_cls}" href="/domestic">核心库首页</a>
    <a class="button" href="/domestic/library?layer=core">核心可阅全文</a>
    <a class="button secondary" href="/domestic/events">事件墙</a>
    <a class="{layer_bg_cls}" href="/domestic?layer=background">背景线索</a>
    <a class="button secondary" href="/domestic/acquisition">调档工作台</a>
    <a class="button secondary" href="/standards">收录标准</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(core_docs_total)}</strong><span>核心可阅文档</span></div>
  <div class="stat"><strong>{h(cite_pages)}</strong><span>人工核验可引用页</span></div>
  <div class="stat"><strong>{h(machine_pages)}</strong><span>机器核验可阅页</span></div>
  <div class="stat"><strong>{h(source_anchored_pages)}/{h(domestic_page_total)}</strong><span>源文件哈希已锚定</span></div>
  <div class="stat"><strong>{h(missing_provenance_pages)}</strong><span>待补 provenance 页</span></div>
  <div class="stat"><strong>{h(missing_date_documents)}</strong><span>日期待核文档</span></div>
  <div class="stat"><strong>{h(len(core_cands))}</strong><span>核心候选</span></div>
  <div class="stat"><strong>{h(len(background_cands))}</strong><span>背景/线索</span></div>
  <div class="stat"><strong>{h(pending)}</strong><span>待人工复核</span></div>
  <div class="stat"><strong>{h(domestic_doc_total)}</strong><span>已收文档(含非核心)</span></div>
</section>
<div class="notice"><strong>证据纪律：</strong>源文件哈希锚定只证明“当前文字能回到哪份本地原件”，不证明 OCR 内容正确。机器核验和 OCR 仍不等于正式引用；只有 human_verified 且有人工复核说明的页面才能生成正式引文。「已接受候选」({h(accepted_count)}/{h(total_candidates)}) 也不等于可引用全文。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-calendar"/></svg>九大关键事件证据墙</h2></div>
<section class="result-list">
{''.join(event_cards) if event_cards else '<div class="notice">事件覆盖表尚未生成。</div>'}
</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-book"/></svg>核心可阅库精选</h2>
  <a class="button secondary" href="/domestic/library?layer=core">查看全部 {h(core_docs_total)} 篇</a>
</div>
<section class="result-list">
{''.join(doc_cards) if doc_cards else '<div class="notice">正式库尚无达到核心可阅口径的国内文档。</div>'}
</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-building"/></svg>权威馆藏与报刊入口</h2>
  <a class="button secondary" href="/domestic/sources">完整来源地图</a>
</div>
<section class="result-list">
"""
    for row in sources:
        link = row["official_url"] or "#"
        body += f"""
<article class="result">
  <div>
    {title_block(row["source_name"], link)}
    <div class="meta">{h(row["institution"])} · {h(row["source_type"])} · 权威 {h(row["authority_level"])}</div>
    <div class="tagline"><span class="tag">上海相关：{h(row["shanghai_relevance"])}</span><span class="pstatus ok">{h(row["status"])}</span></div>
    <div class="snippet">访问：{h(row["access_mode"])}</div>
  </div>
  <div class="cite"><a href="{h(link)}" target="_blank" rel="noreferrer">打开入口</a></div>
</article>"""
    body += "</section>"

    body += f"""
<div class="section-head"><h2><svg class="ico"><use href="#i-edit"/></svg>研究工作台（次级）</h2></div>
<section class="result-list">
<article class="result"><div><div class="title">背景与线索目录</div><div class="meta">网页史志、二手与官网锚点 · {h(len(background_cands))} 条</div><div class="snippet">用于检索导航与调档线索，不进入默认核心库。</div></div><div class="cite"><a href="/domestic?layer=background">打开</a></div></article>
<article class="result"><div><div class="title">staging 检索 / 质量底座</div><div class="meta">文献对象、物理页、OCR provenance</div><div class="snippet">工程与质量层，不等于前台可引用库。</div></div><div class="cite"><a href="/domestic/search">检索</a> · <a href="/domestic/quality">质量</a></div></article>
<article class="result"><div><div class="title">调档与复核</div><div class="meta">待复核 {h(pending)} · 候选总量 {h(total_candidates)}</div><div class="snippet">档号、影像、权利与人工验收。</div></div><div class="cite"><a href="/domestic/acquisition">调档</a> · <a href="/domestic/review">复核</a></div></article>
<article class="result"><div><div class="title">全部候选（含背景）</div><div class="meta">工作清单模式</div><div class="snippet">需要逐条筛查时使用，不作为阅读主入口。</div></div><div class="cite"><a href="/domestic?layer=all">打开</a></div></article>
</section>
"""

    if layer in {"background", "all"} or show_filters:
        body += f"""
<section class="filter-panel">
  <form method="get" action="/domestic" class="filter-form">
    <input type="hidden" name="layer" value="{h(layer)}">
    <label>关键词 <input name="q" value="{h(term)}" placeholder="题名、事件"></label>
    <label>原始性
      <select name="level"><option value="">全部</option><option value="L1"{' selected' if level == 'L1' else ''}>L1</option><option value="L2"{' selected' if level == 'L2' else ''}>L2</option><option value="L3"{' selected' if level == 'L3' else ''}>L3</option><option value="L4"{' selected' if level == 'L4' else ''}>L4</option><option value="LX"{' selected' if level == 'LX' else ''}>LX</option></select>
    </label>
    <label>来源
      <select name="repository"><option value="">全部</option>{''.join(f'<option value="{h(code)}"{" selected" if repository == code else ""}>{h(code)}</option>' for code in repository_options)}</select>
    </label>
    <label>事件
      <select name="event"><option value="">全部</option>{''.join(f'<option value="{h(value)}"{" selected" if event == value else ""}>{h(label)}</option>' for label, value in event_options)}</select>
    </label>
    <label>相关度
      <select name="relevance"><option value="">全部</option><option value="core"{' selected' if relevance == 'core' else ''}>核心</option><option value="related"{' selected' if relevance == 'related' else ''}>相关</option><option value="background"{' selected' if relevance == 'background' else ''}>背景</option></select>
    </label>
    <label>状态
      <select name="review"><option value="">全部</option><option value="needs_human_review"{' selected' if review == 'needs_human_review' else ''}>待复核</option><option value="accepted"{' selected' if review == 'accepted' else ''}>已接受</option></select>
    </label>
    <label>分层
      <select name="layer">
        <option value="core"{' selected' if layer == 'core' else ''}>核心</option>
        <option value="background"{' selected' if layer == 'background' else ''}>背景</option>
        <option value="all"{' selected' if layer == 'all' else ''}>全部</option>
      </select>
    </label>
    <button class="button" type="submit">筛选</button>
    <a class="button secondary" href="/domestic">回核心首页</a>
    <a class="{layer_all_cls}" href="/domestic?layer=all">全部候选</a>
  </form>
  <div class="meta">当前列表 {h(len(list_rows))} 条 · 核心候选池 {h(len(core_cands))} · 背景池 {h(len(background_cands))}</div>
</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>{h(list_title)}（{h(len(list_rows))}）</h2></div>
<section class="result-list">
"""
        if not list_rows:
            body += '<div class="notice">当前筛选无结果。</div>'
        else:
            # 背景层默认截断，避免再次被 600+ 条淹没；可用筛选缩小
            display_rows = list_rows[:120]
            for row in display_rows:
                link = row["source_url"] or "#"
                detail_link = f"/domestic/candidate/{quote(str(row['candidate_id']), safe='')}"
                lvl = _domestic_level(row)
                bg = _domestic_is_background_candidate(row)
                layer_tag = "背景线索" if bg else "核心候选"
                body += f"""
<article class="result">
  <div>
    {title_block(row["title"], detail_link)}
    <div class="meta">{h(row["document_type"])} · 等级 {h(lvl or row["authenticity_level_proposed"])} · 相关度 {h(row["relevance_grade_proposed"])}</div>
    <div class="tagline"><span class="tag">{h(layer_tag)}</span><span class="tag">{h(row["candidate_id"])}</span><span class="pstatus warn">{h(row["review_status"])}</span></div>
    <div class="snippet">{h(row["evidence_note"])}</div>
    <div class="snippet"><strong>不确定性：</strong>{h(row["uncertainty_note"])}</div>
  </div>
  <div class="cite"><a href="{h(detail_link)}">记录详情</a><br><a href="{h(source_href(link))}" target="_blank" rel="noreferrer">打开来源</a></div>
</article>"""
            if len(list_rows) > len(display_rows):
                body += f'<div class="notice">仅显示前 {h(len(display_rows))} 条，请用筛选缩小范围。共 {h(len(list_rows))} 条。</div>'
        body += "</section>"

    return layout("国内史料库", body, active_path="/domestic")


def _domestic_tag_values(raw: object) -> list[str]:
    """读取国内候选中的 JSON 标签；旧记录损坏时降级为空。"""
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(value) for value in raw if str(value).strip()]
    try:
        value = json.loads(str(raw))
    except (TypeError, json.JSONDecodeError):
        return [part.strip() for part in str(raw).split("；") if part.strip()]
    return value if isinstance(value, list) else []


def _domestic_rows() -> list[sqlite3.Row]:
    with conn() as c:
        rows = c.execute(
            """SELECT candidate_id, title, creator, document_date, document_type,
                      repository_code, archive_fonds, archive_series, archive_file,
                      archive_item, catalog_reference, source_url,
                      authenticity_level_proposed, relevance_grade_proposed,
                      authenticity_level_accepted, review_status, rights_status,
                      event_tags, person_tags, place_tags,
                      evidence_note, uncertainty_note, ingested_document_id
               FROM domestic_candidates ORDER BY id"""
        ).fetchall()
    if getattr(_request, "public_mode", False):
        rows = [row for row in rows if _public_domestic_candidate_visible(row)]
    return rows


def _domestic_candidate_row(candidate_id: str) -> sqlite3.Row | None:
    """读取单条国内候选的完整追溯字段；不读取本地正文。"""
    with conn() as c:
        return c.execute(
            "SELECT * FROM domestic_candidates WHERE candidate_id=?",
            (candidate_id,),
        ).fetchone()


def domestic_candidate_page(candidate_id: str) -> bytes:
    """国内候选详情：把目录、来源、权利和复核状态集中展示。"""
    row = _domestic_candidate_row(candidate_id)
    if getattr(_request, "public_mode", False) and row and not _public_domestic_candidate_visible(row):
        row = None
    if not row:
        return layout(
            "国内候选未找到",
            '<div class="notice">没有找到这条国内候选记录，请返回 <a href="/domestic">国内史料库</a>。</div>',
            active_path="/domestic",
        )

    level = row["authenticity_level_accepted"] or row["authenticity_level_proposed"] or "未分级"
    source_url = source_href(row["source_url"])
    source_link = (
        f'<a class="button" href="{h(source_url)}" target="_blank" rel="noreferrer">打开来源入口</a>'
        if source_url != "#" else
        '<span class="button secondary">暂无公开来源入口</span>'
    )
    document = None
    if row["ingested_document_id"]:
        with conn() as c:
            document = c.execute(
                "SELECT doc_key,title FROM documents WHERE id=? AND source_platform='domestic'",
                (row["ingested_document_id"],),
            ).fetchone()
    document_link = ""
    if document:
        document_link = (
            f'<a class="button secondary" href="/doc/{quote(str(document["doc_key"]))}">'
            f'打开已入库原件：{h(document["title"] or document["doc_key"])}'
            "</a>"
        )

    def field(name: str, empty: str = "未标注") -> str:
        value = row[name]
        return h(value if value not in (None, "") else empty)

    event_tags = _domestic_tag_values(row["event_tags"])
    person_tags = _domestic_tag_values(row["person_tags"])
    place_tags = _domestic_tag_values(row["place_tags"])
    event_links = "、".join(
        f'<a href="/domestic?event={quote(tag)}">{h(tag)}</a>' for tag in event_tags
    ) or "未标注"
    body = breadcrumb_html([
        ("/domestic", "国内史料"),
        (None, str(row["title"] or row["candidate_id"])),
    ]) + f"""
<section class="doc-head">
  <div>
    <h1>{h(row["title"] or row["candidate_id"])}</h1>
    <div class="meta">候选 ID：{h(row["candidate_id"])} · {h(row["review_status"] or "未标注")}</div>
  </div>
  <div class="doc-tools">{source_link}{document_link}<a class="button secondary" href="/domestic/review">进入复核看板</a></div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(level)}</strong><span>原始性等级</span></div>
  <div class="stat"><strong>{field("relevance_grade_accepted", field("relevance_grade_proposed", "未分级"))}</strong><span>相关度</span></div>
  <div class="stat"><strong>{field("review_status")}</strong><span>复核状态</span></div>
  <div class="stat"><strong>{field("rights_status")}</strong><span>权利状态</span></div>
</section>
<div class="notice"><strong>证据边界：</strong>本页是候选记录的来源链和编辑状态，不代表已经取得原件全文。只有页级 provenance、原件/影像对照和人工复核门禁齐全后，才可生成正式引文。</div>
<section class="reader">
  <article class="pane">
    <div class="pane-head"><span>形成与目录</span><span>{h(row["document_type"] or "资料")}</span></div>
    <div class="pane-body">
      <p><strong>形成者：</strong>{field("creator")}</p>
      <p><strong>形成日期：</strong>{field("document_date")}</p>
      <p><strong>载体/介质：</strong>{field("medium")}</p>
      <p><strong>保管机构：</strong>{field("repository_name")}</p>
      <p><strong>来源代码：</strong>{field("repository_code")}</p>
      <p><strong>馆藏名称：</strong>{field("collection_name")}</p>
      <p><strong>档号/卷期：</strong>{field("catalog_reference")}</p>
      <p><strong>全宗：</strong>{field("archive_fonds")} · <strong>案卷：</strong>{field("archive_file")} · <strong>件：</strong>{field("archive_item")}</p>
      <p><strong>来源入口角色：</strong>{field("source_url_role")}</p>
    </div>
  </article>
  <article class="pane">
    <div class="pane-head"><span>获取与权利</span><span>{h(row["access_mode"] or "未标注")}</span></div>
    <div class="pane-body">
      <p><strong>访问方式：</strong>{field("access_mode")}</p>
      <p><strong>在线可得性：</strong>{field("online_availability")}</p>
      <p><strong>访问说明：</strong>{field("access_note")}</p>
      <p><strong>权利状态：</strong>{field("rights_status")}</p>
      <p><strong>再利用依据：</strong>{field("rights_basis")}</p>
      <p><strong>复制许可：</strong>{field("copy_allowed")}</p>
      <p><strong>获取日期：</strong>{field("checked_at")}</p>
      <p><strong>核验者：</strong>{field("checked_by")}</p>
    </div>
  </article>
</section>
<section class="result-list">
  <article class="result"><div><h2>研究归属</h2><div class="meta">事件：{event_links}</div><div class="meta">人物：{h("、".join(person_tags) or "未标注")} · 地点：{h("、".join(place_tags) or "未标注")}</div></div></article>
  <article class="result"><div><h2>证据说明</h2><div class="snippet">{field("evidence_note")}</div><div class="snippet"><strong>不确定性：</strong>{field("uncertainty_note")}</div></div></article>
  <article class="result"><div><h2>编辑记录</h2><div class="meta">拟议等级：{field("authenticity_level_proposed")} · 接受等级：{field("authenticity_level_accepted")} · 相关度：{field("relevance_grade_proposed")}</div><div class="snippet">复核备注：{field("review_note")}<br>处理结论：{field("check_outcome")}</div></div></article>
</section>
"""
    return layout("国内候选详情", body, active_path="/domestic")


def domestic_quality_page() -> bytes:
    """展示 canonical 国内 staging 层的可信规模和质量警告。"""
    if not DOMESTIC_STAGING_DB_PATH.exists():
        return layout(
            "国内质量底座",
            '<div class="notice">国内 staging 数据库尚未建立。请先运行 Phase 0 reconciliation 与 staging 构建。</div>',
            active_path="/domestic/quality",
        )
    phase2_report: dict = {}
    if PHASE2_INVENTORY_REPORT_PATH.exists():
        try:
            phase2_report = json.loads(PHASE2_INVENTORY_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            phase2_report = {}
    core_gap_report: dict = {}
    if CORE_GAP_MATRIX_REPORT_PATH.exists():
        try:
            core_gap_report = json.loads(CORE_GAP_MATRIX_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            core_gap_report = {}
    supplemental_1942_1943_report: dict = {}
    if SUPPLEMENTAL_1942_1943_REPORT_PATH.exists():
        try:
            supplemental_1942_1943_report = json.loads(SUPPLEMENTAL_1942_1943_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            supplemental_1942_1943_report = {}
    research_1942_1943_report: dict = {}
    if RESEARCH_1942_1943_REPORT_PATH.exists():
        try:
            research_1942_1943_report = json.loads(RESEARCH_1942_1943_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            research_1942_1943_report = {}
    academic_pdf_ocr_pilot_report: dict = {}
    if ACADEMIC_PDF_OCR_PILOT_REPORT_PATH.exists():
        try:
            academic_pdf_ocr_pilot_report = json.loads(ACADEMIC_PDF_OCR_PILOT_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            academic_pdf_ocr_pilot_report = {}
    academic_pdf_ocr_batch_report: dict = {}
    if ACADEMIC_PDF_OCR_BATCH_REPORT_PATH.exists():
        try:
            academic_pdf_ocr_batch_report = json.loads(ACADEMIC_PDF_OCR_BATCH_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            academic_pdf_ocr_batch_report = {}
    academic_1943_target_report: dict = {}
    if ACADEMIC_1943_TARGET_REPORT_PATH.exists():
        try:
            academic_1943_target_report = json.loads(ACADEMIC_1943_TARGET_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            academic_1943_target_report = {}
    gap_wave2_audit_report: dict = {}
    if GAP_WAVE2_AUDIT_REPORT_PATH.exists():
        try:
            gap_wave2_audit_report = json.loads(GAP_WAVE2_AUDIT_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            gap_wave2_audit_report = {}
    w2_sha_repair_report: dict = {}
    if W2_SHA_REPAIR_REPORT_PATH.exists():
        try:
            w2_sha_repair_report = json.loads(W2_SHA_REPAIR_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            w2_sha_repair_report = {}
    w2_sha_supplement_report: dict = {}
    if W2_SHA_SUPPLEMENT_REPORT_PATH.exists():
        try:
            w2_sha_supplement_report = json.loads(W2_SHA_SUPPLEMENT_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            w2_sha_supplement_report = {}
    mmda_gap_rows: list[dict] = []
    if MMDA_1942_1943_QUEUE_PATH.exists():
        try:
            mmda_gap_rows = [
                json.loads(line)
                for line in MMDA_1942_1943_QUEUE_PATH.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, json.JSONDecodeError):
            mmda_gap_rows = []
    mmda_intake_report: dict = {}
    if MMDA_P1_INTAKE_REPORT_PATH.exists():
        try:
            mmda_intake_report = json.loads(MMDA_P1_INTAKE_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            mmda_intake_report = {}
    mmda_original_pending_report: dict = {}
    if MMDA_ORIGINAL_PENDING_REPORT_PATH.exists():
        try:
            mmda_original_pending_report = json.loads(MMDA_ORIGINAL_PENDING_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            mmda_original_pending_report = {}
    machine_structure_report: dict = {}
    if MACHINE_STRUCTURE_REPORT_PATH.exists():
        try:
            machine_structure_report = json.loads(MACHINE_STRUCTURE_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            machine_structure_report = {}
    claim_duplicate_report: dict = {}
    if CLAIM_DUPLICATE_REPORT_PATH.exists():
        try:
            claim_duplicate_report = json.loads(CLAIM_DUPLICATE_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            claim_duplicate_report = {}
    p0_p1_machine_report: dict = {}
    if P0_P1_MACHINE_REPORT_PATH.exists():
        try:
            p0_p1_machine_report = json.loads(P0_P1_MACHINE_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            p0_p1_machine_report = {}
    p0_p1_consistency_report: dict = {}
    if P0_P1_CONSISTENCY_REPORT_PATH.exists():
        try:
            p0_p1_consistency_report = json.loads(P0_P1_CONSISTENCY_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            p0_p1_consistency_report = {}
    claim_crosswalk_report: dict = {}
    if CLAIM_CROSSWALK_REPORT_PATH.exists():
        try:
            claim_crosswalk_report = json.loads(CLAIM_CROSSWALK_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            claim_crosswalk_report = {}
    crosswalk_queue_report: dict = {}
    if CROSSWALK_QUEUE_REPORT_PATH.exists():
        try:
            crosswalk_queue_report = json.loads(CROSSWALK_QUEUE_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            crosswalk_queue_report = {}
    crosswalk_material_report: dict = {}
    if CROSSWALK_MATERIAL_REPORT_PATH.exists():
        try:
            crosswalk_material_report = json.loads(CROSSWALK_MATERIAL_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            crosswalk_material_report = {}
    fulltext_content_report: dict = {}
    if FULLTEXT_CONTENT_REPORT_PATH.exists():
        try:
            fulltext_content_report = json.loads(FULLTEXT_CONTENT_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            fulltext_content_report = {}
    fulltext_locator_report: dict = {}
    if FULLTEXT_LOCATOR_REPORT_PATH.exists():
        try:
            fulltext_locator_report = json.loads(FULLTEXT_LOCATOR_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            fulltext_locator_report = {}
    fulltext_semantic_report: dict = {}
    if FULLTEXT_SEMANTIC_REPORT_PATH.exists():
        try:
            fulltext_semantic_report = json.loads(FULLTEXT_SEMANTIC_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            fulltext_semantic_report = {}
    fulltext_overlap_report: dict = {}
    if FULLTEXT_OVERLAP_REPORT_PATH.exists():
        try:
            fulltext_overlap_report = json.loads(FULLTEXT_OVERLAP_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            fulltext_overlap_report = {}
    fulltext_review_cards_report: dict = {}
    if FULLTEXT_REVIEW_CARDS_REPORT_PATH.exists():
        try:
            fulltext_review_cards_report = json.loads(FULLTEXT_REVIEW_CARDS_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            fulltext_review_cards_report = {}
    structured_relation_report: dict = {}
    if STRUCTURED_RELATION_REPORT_PATH.exists():
        try:
            structured_relation_report = json.loads(STRUCTURED_RELATION_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            structured_relation_report = {}
    local_private_ocr_report: dict = {}
    if LOCAL_PRIVATE_OCR_REPORT_PATH.exists():
        try:
            local_private_ocr_report = json.loads(LOCAL_PRIVATE_OCR_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            local_private_ocr_report = {}
    local_private_normalization: dict = {}
    if LOCAL_PRIVATE_NORMALIZATION_REPORT_PATH.exists():
        try:
            local_private_normalization = json.loads(LOCAL_PRIVATE_NORMALIZATION_REPORT_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            local_private_normalization = {}
    try:
        c = sqlite3.connect(DOMESTIC_STAGING_DB_PATH)
        c.row_factory = sqlite3.Row
        run = c.execute("SELECT * FROM ingest_runs ORDER BY created_at DESC LIMIT 1").fetchone()
        has_machine_text = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='machine_text_records'"
        ).fetchone() is not None
        has_ocr = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ocr_versions'"
        ).fetchone() is not None
        has_gate = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='citation_gate_results'"
        ).fetchone() is not None
        has_claims = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_candidates'"
        ).fetchone() is not None
        has_annotations = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_candidate_annotations'"
        ).fetchone() is not None
        has_claim_locator_audit = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_locator_audit'"
        ).fetchone() is not None
        has_claim_triage = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_semantic_triage'"
        ).fetchone() is not None
        has_claim_cards = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_cards'"
        ).fetchone() is not None
        has_claim_review_units = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_review_units'"
        ).fetchone() is not None
        has_semantic_queue = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='semantic_review_queue'"
        ).fetchone() is not None
        has_local_source = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_source_objects'"
        ).fetchone() is not None
        has_local_text_audit = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_text_audit'"
        ).fetchone() is not None
        has_local_semantic = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_semantic_signals'"
        ).fetchone() is not None
        has_local_cards = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_evidence_cards'"
        ).fetchone() is not None
        has_research_materials = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domestic_research_materials'"
        ).fetchone() is not None
        counts = {
            "documents": c.execute("SELECT count(*) FROM documents").fetchone()[0],
            "page_assets": c.execute("SELECT count(*) FROM page_assets").fetchone()[0],
            "pdf_or_scan": c.execute("SELECT count(*) FROM page_assets WHERE file_kind = 'pdf_original_or_scan'").fetchone()[0],
            "page_images": c.execute("SELECT count(*) FROM page_assets WHERE file_kind = 'page_image'").fetchone()[0],
            "scholarly": c.execute("SELECT count(*) FROM scholarly_fulltexts").fetchone()[0],
            "local_sources": c.execute("SELECT count(*) FROM local_source_objects").fetchone()[0] if has_local_source else 0,
            "local_related_primary": c.execute("SELECT count(*) FROM local_source_objects WHERE document_class='historical_primary_related_source'").fetchone()[0] if has_local_source else 0,
            "local_text_ready": c.execute("SELECT count(*) FROM local_text_audit WHERE quality_status='TEXT_STRUCTURE_READY'").fetchone()[0] if has_local_text_audit else 0,
            "local_text_holds": c.execute("SELECT count(*) FROM local_text_audit WHERE quality_status != 'TEXT_STRUCTURE_READY'").fetchone()[0] if has_local_text_audit else 0,
            "local_semantic_signals": c.execute("SELECT count(*) FROM local_semantic_signals").fetchone()[0] if has_local_semantic else 0,
            "local_evidence_cards": c.execute("SELECT count(*) FROM local_evidence_cards").fetchone()[0] if has_local_cards else 0,
            "research_materials": c.execute("SELECT count(*) FROM domestic_research_materials").fetchone()[0] if has_research_materials else 0,
            "research_fulltext_candidates": c.execute("SELECT count(*) FROM domestic_research_materials WHERE fulltext_status IN ('FULLTEXT_PDF','FULLTEXT_HTML_CANDIDATE')").fetchone()[0] if has_research_materials else 0,
            "machine_text": c.execute("SELECT count(*) FROM machine_text_records").fetchone()[0] if has_machine_text else 0,
            "ocr_versions": c.execute("SELECT count(*) FROM ocr_versions").fetchone()[0] if has_ocr else 0,
            "evidence_units": c.execute("SELECT count(*) FROM evidence_units").fetchone()[0] if has_ocr else 0,
            "ocr_holds": c.execute("SELECT count(*) FROM ocr_provenance_flags").fetchone()[0] if has_ocr else 0,
            "citation_candidates": c.execute("SELECT count(*) FROM citation_gate_results WHERE eligible=1").fetchone()[0] if has_gate else 0,
            "citation_holds": c.execute("SELECT count(*) FROM citation_gate_results WHERE eligible=0").fetchone()[0] if has_gate else 0,
            "claim_candidates": c.execute("SELECT count(*) FROM evidence_claim_candidates").fetchone()[0] if has_claims else 0,
            "claim_annotations": c.execute("SELECT count(*) FROM evidence_candidate_annotations").fetchone()[0] if has_annotations else 0,
            "claim_locator_ready": c.execute("SELECT count(*) FROM evidence_claim_locator_audit WHERE audit_status='STRUCTURE_READY_CLAIM_INDEX'").fetchone()[0] if has_claim_locator_audit else 0,
            "claim_locator_holds": c.execute("SELECT count(*) FROM evidence_claim_locator_audit WHERE audit_status!='STRUCTURE_READY_CLAIM_INDEX'").fetchone()[0] if has_claim_locator_audit else 0,
            "claim_triage_ready": c.execute("SELECT count(*) FROM evidence_claim_semantic_triage").fetchone()[0] if has_claim_triage else 0,
            "claim_triage_event": c.execute("SELECT count(*) FROM evidence_claim_semantic_triage WHERE triage_class='EVENT_ENTITY_CANDIDATE'").fetchone()[0] if has_claim_triage else 0,
            "claim_cards": c.execute("SELECT count(*) FROM evidence_claim_cards").fetchone()[0] if has_claim_cards else 0,
            "claim_review_units": c.execute("SELECT count(*) FROM evidence_claim_review_units").fetchone()[0] if has_claim_review_units else 0,
            "claim_review_p0p1": c.execute("SELECT count(*) FROM evidence_claim_review_units WHERE priority IN ('P0','P1')").fetchone()[0] if has_claim_review_units else 0,
            "claim_exact_unique_estimate": claim_duplicate_report.get("exact_text_unique_units_estimate", 0),
            "claim_exact_duplicate_groups": claim_duplicate_report.get("exact_text_duplicate_groups", 0),
            "claim_same_page_groups": claim_duplicate_report.get("same_canonical_page_groups", 0),
            "p0_p1_machine_assessed": p0_p1_machine_report.get("input_review_units", 0),
            "p0_p1_machine_weak": p0_p1_machine_report.get("machine_assessment_counts", {}).get("MACHINE_REVIEW_WEAK", 0),
            "p0_p1_source_consistent": p0_p1_consistency_report.get("status_counts", {}).get("SOURCE_CONSISTENT_LOCATABLE", 0),
            "crosswalk_specific": claim_crosswalk_report.get("crosswalk_status_counts", {}).get("METADATA_CROSSWALK_REVIEW_REQUIRED", 0),
            "crosswalk_generic_hold": claim_crosswalk_report.get("generic_only_rows", 0),
            "crosswalk_review_first": crosswalk_queue_report.get("priority_band_counts", {}).get("A_REVIEW_FIRST", 0),
            "crosswalk_fulltext_rows": crosswalk_queue_report.get("fulltext_candidate_rows", 0),
            "crosswalk_material_objects": crosswalk_material_report.get("distinct_material_objects", 0),
            "crosswalk_material_a": crosswalk_material_report.get("priority_band_counts", {}).get("A_REVIEW_FIRST", 0),
            "crosswalk_material_fulltext": crosswalk_material_report.get("fulltext_material_objects", 0),
            "fulltext_content_pass": sum(
                count for status, count in fulltext_content_report.get("status_counts", {}).items()
                if status.startswith("CONTENT_")
            ),
            "fulltext_content_holds": sum(
                count for status, count in fulltext_content_report.get("status_counts", {}).items()
                if status.startswith("HOLD_")
            ),
            "fulltext_locator_found": fulltext_locator_report.get("locator_status_counts", {}).get("TEXT_LOCATOR_FOUND", 0),
            "fulltext_locator_holds": fulltext_locator_report.get("locator_status_counts", {}).get("HOLD_CONTENT_LAYER", 0),
            "fulltext_possible_support": fulltext_semantic_report.get("machine_relation_status_counts", {}).get("POSSIBLE_SUPPORT_SIGNAL_REVIEW_REQUIRED", 0),
            "fulltext_possible_conflict": fulltext_semantic_report.get("machine_relation_status_counts", {}).get("POSSIBLE_CONFLICT_SIGNAL_REVIEW_REQUIRED", 0),
            "fulltext_semantic_unknown": fulltext_semantic_report.get("machine_relation_status_counts", {}).get("UNKNOWN_CONTENT_LAYER_HOLD", 0),
            "fulltext_overlap_strong": fulltext_overlap_report.get("text_overlap_status_counts", {}).get("STRONG_TEXT_OVERLAP_REVIEW_REQUIRED", 0),
            "fulltext_overlap_weak": fulltext_overlap_report.get("text_overlap_status_counts", {}).get("WEAK_TEXT_OVERLAP_REVIEW_REQUIRED", 0),
            "fulltext_overlap_unknown": fulltext_overlap_report.get("text_overlap_status_counts", {}).get("UNKNOWN_CONTENT_LAYER_HOLD", 0) + fulltext_overlap_report.get("text_overlap_status_counts", {}).get("UNKNOWN_NO_TEXT_OVERLAP", 0),
            "fulltext_semantic_review_cards": fulltext_review_cards_report.get("review_cards", 0),
            "structured_same_context": structured_relation_report.get("relation_signal_counts", {}).get("POTENTIAL_SAME_CONTEXT_REVIEW_REQUIRED", 0),
            "structured_context_only": structured_relation_report.get("relation_signal_counts", {}).get("POTENTIAL_CONTEXT_ONLY_REVIEW_REQUIRED", 0),
            "structured_unknown": structured_relation_report.get("relation_signal_counts", {}).get("UNKNOWN_NO_SUBJECT_HIT", 0),
            "core_zero_phases": len(core_gap_report.get("zero_canonical_phases", [])),
            "core_gap_worklist": core_gap_report.get("gap_worklist_rows", 0),
            "supplemental_1942_1943": supplemental_1942_1943_report.get("records", 0),
            "supplemental_primary_candidates": supplemental_1942_1943_report.get("candidate_class_counts", {}).get("PRIMARY_SOURCE_CANDIDATE_UNVERIFIED", 0),
            "supplemental_foreign_comparative": supplemental_1942_1943_report.get("candidate_class_counts", {}).get("FOREIGN_COMPARATIVE_SNAPSHOT", 0),
            "research_1942_1943": research_1942_1943_report.get("rows", 0),
            "research_1942_1943_metadata_only": research_1942_1943_report.get("fulltext_status_counts", {}).get("METADATA_ONLY", 0),
            "research_1942_1943_extractable": research_1942_1943_report.get("local_extractable_content", 0),
            "research_1942_1943_pdf_ocr": research_1942_1943_report.get("pdf_needs_ocr", 0),
            "academic_pdf_ocr_pilot_pages": academic_pdf_ocr_pilot_report.get("completed_pages", 0) + academic_pdf_ocr_batch_report.get("completed_pages", 0),
            "academic_pdf_ocr_low_confidence_pages": sum(1 for value in academic_pdf_ocr_batch_report.get("mean_confidences", {}).values() if float(value) < 0.85),
            "academic_1943_staged_pages": academic_1943_target_report.get("completed_pages", 0),
            "gap_wave2_page_chain_rows": gap_wave2_audit_report.get("page_chain_rows", 0),
            "gap_wave2_page_chain_conflicts": gap_wave2_audit_report.get("1942_1943_phase_conflict_rows", 0),
            "gap_wave2_clean_1942_1943_page_rows": gap_wave2_audit_report.get("clean_1942_1943_rows_for_core_gap", 0),
            "w2_sha_repair_sources": w2_sha_repair_report.get("source_records", 0),
            "w2_sha_repair_pages": w2_sha_repair_report.get("page_rows", 0),
            "w2_sha_supplement_sources": w2_sha_supplement_report.get("verified_supplement_sources", 0),
            "w2_sha_supplement_pages": w2_sha_supplement_report.get("verified_supplement_pages", 0),
            "mmda_original_pending": mmda_original_pending_report.get("rows", 0),
            "mmda_original_pending_1942": mmda_original_pending_report.get("phase_counts", {}).get("1942", 0),
            "mmda_original_pending_1943": mmda_original_pending_report.get("phase_counts", {}).get("1943", 0),
            "semantic_ready": c.execute("SELECT count(*) FROM semantic_review_queue WHERE review_stage='READY_SEMANTIC_REVIEW'").fetchone()[0] if has_semantic_queue else 0,
            "semantic_holds": c.execute("SELECT count(*) FROM semantic_review_queue WHERE review_stage='HOLD_MACHINE_TRIAGE'").fetchone()[0] if has_semantic_queue else 0,
            "structure_ready": machine_structure_report.get("stage_counts", {}).get("STRUCTURE_READY_SEMANTIC_REVIEW", 0),
            "structure_holds": machine_structure_report.get("stage_counts", {}).get("HOLD_STRUCTURE", 0),
            "local_private_ocr": local_private_normalization.get("domestic_scope_objects", local_private_ocr_report.get("rows", 0)),
            "local_private_excluded": local_private_normalization.get("overseas_excluded_objects", 0),
            "flags": c.execute("SELECT count(*) FROM quality_flags").fetchone()[0],
        }
        phases = c.execute(
            "SELECT dominant_phase, count(*) n FROM documents GROUP BY dominant_phase ORDER BY n DESC"
        ).fetchall()
        kinds = c.execute(
            "SELECT file_kind, count(*) n FROM page_assets GROUP BY file_kind ORDER BY n DESC"
        ).fetchall()
        flags = c.execute(
            "SELECT flag_type, severity, count(*) n FROM quality_flags GROUP BY flag_type, severity ORDER BY n DESC"
        ).fetchall()
        c.close()
    except sqlite3.Error as exc:
        return layout(
            "国内质量底座",
            f'<div class="notice">staging 数据库读取失败：{h(exc)}</div>',
            active_path="/domestic/quality",
        )

    phase_html = "".join(
        f'<article class="result"><div><h2>{h(row["dominant_phase"] or "unknown")}</h2>'
        f'<div class="meta">canonical 文献 {h(row["n"])} 个</div></div></article>'
        for row in phases
    )
    phase2_counts = phase2_report.get("phase_document_counts", {})
    phase2_html = (
        f'<article class="result"><div><h2>1941—1946 核心资料</h2>'
        f'<div class="meta">已入 staging 文献 {h(phase2_report.get("document_rows", 0))} 个 · 页/文件资产 {h(phase2_report.get("page_asset_rows", 0))} 个 · 1942—1943 原件 {h(phase2_counts.get("1942-1943", 0))} 个 · 核心零覆盖时期 {h(len(core_gap_report.get("zero_canonical_phases", [])))} 个 · MMDA 目录候选 {h(len(mmda_gap_rows))} 条（P1 {h(sum(1 for row in mmda_gap_rows if row.get("queue_rank") == 1))}）· P1 待接收 {h(mmda_intake_report.get("records_waiting", 0))} 条 · 原件待取队列 {h(mmda_original_pending_report.get("rows", 0))} 条</div></div>'
        f'<div class="cite"><a href="/domestic/search?scope=documents&amp;q=1941">查看</a></div></article>'
        if phase2_report
        else '<div class="notice">1941—1946 核心资料覆盖表尚未生成。</div>'
    )
    local_scope_counts = local_private_normalization.get("scope_counts", {})
    local_scope_html = "".join(
        f'<article class="result"><div><h2>{h(label)}</h2><div class="meta">{h(count)} 个（文件级分类，待来源/正文复核）</div></div></article>'
        for label, count in sorted(local_scope_counts.items())
    ) or '<div class="notice">本地私有 OCR 文献分层尚未生成。</div>'
    kind_html = "".join(
        f'<article class="result"><div><h2>{h(row["file_kind"])}</h2>'
        f'<div class="meta">资产 {h(row["n"])} 个</div></div></article>'
        for row in kinds
    )
    flag_html = "".join(
        f'<article class="result"><div><h2>{h(row["flag_type"])}</h2>'
        f'<div class="meta">{h(row["severity"])} · {h(row["n"])} 组</div></div></article>'
        for row in flags
    ) or '<div class="notice">当前没有 staging 质量警告。</div>'
    formal_status = "未改变" if run and run["formal_db_unchanged"] else "需复核"
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "质量底座")]) + f"""
<section class="doc-head"><div><h1>国内资料质量底座</h1><div class="meta">canonical 文献、物理页资产、学术全文与机器质量警告</div></div><div class="doc-tools"><a class="button" href="/domestic/search">国内检索</a><a class="button secondary" href="/domestic">国内候选目录</a></div></section>
<section class="stats">
  <div class="stat"><strong>{h(counts['documents'])}</strong><span>canonical 文献</span></div>
  <div class="stat"><strong>{h(counts['page_assets'])}</strong><span>物理页/文件资产</span></div>
  <div class="stat"><strong>{h(counts['pdf_or_scan'])}</strong><span>PDF/扫描文件</span></div>
  <div class="stat"><strong>{h(counts['page_images'])}</strong><span>页图资产</span></div>
  <div class="stat"><strong>{h(counts['scholarly'])}</strong><span>学术全文</span></div>
  <div class="stat"><strong>{h(counts['local_sources'])}</strong><span>本地 staging 对象</span></div>
  <div class="stat"><strong>{h(counts['local_related_primary'])}</strong><span>关联本地一手</span></div>
  <div class="stat"><strong>{h(counts['local_text_ready'])}</strong><span>本地文本结构通过</span></div>
  <div class="stat"><strong>{h(counts['local_text_holds'])}</strong><span>本地文本结构 HOLD</span></div>
  <div class="stat"><strong>{h(counts['local_semantic_signals'])}</strong><span>本地机器语义信号</span></div>
  <div class="stat"><strong>{h(counts['local_evidence_cards'])}</strong><span>本地证据卡片草稿</span></div>
  <div class="stat"><strong>{h(counts['research_materials'])}</strong><span>国内研究资料</span></div>
  <div class="stat"><strong>{h(counts['research_fulltext_candidates'])}</strong><span>研究全文候选</span></div>
  <div class="stat"><strong>{h(counts['machine_text'])}</strong><span>官方/机器文本</span></div>
  <div class="stat"><strong>{h(counts['ocr_versions'])}</strong><span>OCR 版本</span></div>
  <div class="stat"><strong>{h(counts['evidence_units'])}</strong><span>证据定位单元</span></div>
  <div class="stat"><strong>{h(counts['ocr_holds'])}</strong><span>OCR 绑定 HOLD</span></div>
  <div class="stat"><strong>{h(counts['citation_candidates'])}</strong><span>citation 候选</span></div>
  <div class="stat"><strong>{h(counts['citation_holds'])}</strong><span>citation 闸门 HOLD</span></div>
  <div class="stat"><strong>{h(counts['claim_candidates'])}</strong><span>语义候选片段</span></div>
  <div class="stat"><strong>{h(counts['claim_annotations'])}</strong><span>机器标签候选</span></div>
  <div class="stat"><strong>{h(counts['claim_locator_ready'])}</strong><span>claim 定位结构通过</span></div>
  <div class="stat"><strong>{h(counts['claim_locator_holds'])}</strong><span>claim 定位 HOLD</span></div>
  <div class="stat"><strong>{h(counts['claim_triage_ready'])}</strong><span>语义分流索引</span></div>
  <div class="stat"><strong>{h(counts['claim_triage_event'])}</strong><span>事件实体候选</span></div>
  <div class="stat"><strong>{h(counts['claim_cards'])}</strong><span>claim 卡片索引</span></div>
  <div class="stat"><strong>{h(counts['claim_review_units'])}</strong><span>去重后复核单元</span></div>
  <div class="stat"><strong>{h(counts['claim_review_p0p1'])}</strong><span>P0/P1 复核单元</span></div>
  <div class="stat"><strong>{h(counts['claim_exact_unique_estimate'])}</strong><span>精确文本唯一估计</span></div>
  <div class="stat"><strong>{h(counts['claim_exact_duplicate_groups'])}</strong><span>精确重复组</span></div>
  <div class="stat"><strong>{h(counts['claim_same_page_groups'])}</strong><span>同页多候选组</span></div>
  <div class="stat"><strong>{h(counts['p0_p1_machine_assessed'])}</strong><span>P0/P1 机器评估</span></div>
  <div class="stat"><strong>{h(counts['p0_p1_machine_weak'])}</strong><span>P0/P1 高风险</span></div>
  <div class="stat"><strong>{h(counts['p0_p1_source_consistent'])}</strong><span>P0/P1 来源可定位</span></div>
  <div class="stat"><strong>{h(counts['crosswalk_specific'])}</strong><span>跨源具体匹配候选</span></div>
  <div class="stat"><strong>{h(counts['crosswalk_generic_hold'])}</strong><span>跨源泛词 HOLD</span></div>
  <div class="stat"><strong>{h(counts['crosswalk_review_first'])}</strong><span>跨源优先复核</span></div>
  <div class="stat"><strong>{h(counts['crosswalk_fulltext_rows'])}</strong><span>跨源全文候选行</span></div>
  <div class="stat"><strong>{h(counts['crosswalk_material_objects'])}</strong><span>跨源资料对象</span></div>
  <div class="stat"><strong>{h(counts['crosswalk_material_a'])}</strong><span>资料对象优先复核</span></div>
  <div class="stat"><strong>{h(counts['crosswalk_material_fulltext'])}</strong><span>资料对象全文优先</span></div>
  <div class="stat"><strong>{h(counts['fulltext_content_pass'])}</strong><span>全文正文可读对象</span></div>
  <div class="stat"><strong>{h(counts['fulltext_content_holds'])}</strong><span>全文内容层 HOLD</span></div>
  <div class="stat"><strong>{h(counts['fulltext_locator_found'])}</strong><span>全文可定位候选</span></div>
  <div class="stat"><strong>{h(counts['fulltext_locator_holds'])}</strong><span>全文定位 HOLD</span></div>
  <div class="stat"><strong>{h(counts['fulltext_possible_support'])}</strong><span>全文可能支持提示</span></div>
  <div class="stat"><strong>{h(counts['fulltext_possible_conflict'])}</strong><span>全文可能冲突提示</span></div>
  <div class="stat"><strong>{h(counts['fulltext_semantic_unknown'])}</strong><span>全文语义未知/HOLD</span></div>
  <div class="stat"><strong>{h(counts['fulltext_overlap_strong'])}</strong><span>全文强重叠提示</span></div>
  <div class="stat"><strong>{h(counts['fulltext_overlap_weak'])}</strong><span>全文弱重叠提示</span></div>
  <div class="stat"><strong>{h(counts['fulltext_overlap_unknown'])}</strong><span>全文重叠未知/HOLD</span></div>
  <div class="stat"><strong>{h(counts['fulltext_semantic_review_cards'])}</strong><span>全文语义复核卡片</span></div>
  <div class="stat"><strong>{h(counts['structured_same_context'])}</strong><span>可能同一语境</span></div>
  <div class="stat"><strong>{h(counts['structured_context_only'])}</strong><span>可能背景关联</span></div>
  <div class="stat"><strong>{h(counts['structured_unknown'])}</strong><span>主体未命中</span></div>
  <div class="stat"><strong>{h(counts['core_zero_phases'])}</strong><span>核心零覆盖时期</span></div>
  <div class="stat"><strong>{h(counts['core_gap_worklist'])}</strong><span>核心补证工作单</span></div>
  <div class="stat"><strong>{h(counts['supplemental_1942_1943'])}</strong><span>1942/43 补充线索</span></div>
  <div class="stat"><strong>{h(counts['supplemental_primary_candidates'])}</strong><span>1942/43 一手候选（未核原件）</span></div>
  <div class="stat"><strong>{h(counts['supplemental_foreign_comparative'])}</strong><span>1942/43 外部对照</span></div>
  <div class="stat"><strong>{h(counts['research_1942_1943'])}</strong><span>1942/43 研究资料</span></div>
  <div class="stat"><strong>{h(counts['research_1942_1943_metadata_only'])}</strong><span>其中仅元数据</span></div>
  <div class="stat"><strong>{h(counts['research_1942_1943_extractable'])}</strong><span>可提取全文候选</span></div>
  <div class="stat"><strong>{h(counts['research_1942_1943_pdf_ocr'])}</strong><span>PDF 待 OCR</span></div>
  <div class="stat"><strong>{h(counts['academic_pdf_ocr_pilot_pages'])}</strong><span>本地 OCR 试跑页</span></div>
  <div class="stat"><strong>{h(counts['academic_pdf_ocr_low_confidence_pages'])}</strong><span>OCR 低置信待复核</span></div>
  <div class="stat"><strong>{h(counts['academic_1943_staged_pages'])}</strong><span>1943 汇编 staging 页</span></div>
  <div class="stat"><strong>{h(counts['gap_wave2_page_chain_rows'])}</strong><span>页链机器完整</span></div>
  <div class="stat"><strong>{h(counts['gap_wave2_page_chain_conflicts'])}</strong><span>1942/43 时期冲突</span></div>
  <div class="stat"><strong>{h(counts['gap_wave2_clean_1942_1943_page_rows'])}</strong><span>1942/43 可计核心页链</span></div>
  <div class="stat"><strong>{h(counts['w2_sha_repair_sources'])}</strong><span>W2 原 manifest 待补来源</span></div>
  <div class="stat"><strong>{h(counts['w2_sha_supplement_pages'])}</strong><span>W2 staging SHA 已验证页</span></div>
  <div class="stat"><strong>{h(counts['mmda_original_pending'])}</strong><span>MMDA 1942/43 原件待取</span></div>
  <div class="stat"><strong>{h(counts['mmda_original_pending_1942'])}</strong><span>其中 1942 待取</span></div>
  <div class="stat"><strong>{h(counts['mmda_original_pending_1943'])}</strong><span>其中 1943 待取</span></div>
  <div class="stat"><strong>{h(counts['semantic_ready'])}</strong><span>语义复核队列</span></div>
  <div class="stat"><strong>{h(counts['semantic_holds'])}</strong><span>语义机器 HOLD</span></div>
  <div class="stat"><strong>{h(counts['structure_ready'])}</strong><span>结构条件通过</span></div>
  <div class="stat"><strong>{h(counts['structure_holds'])}</strong><span>结构条件 HOLD</span></div>
  <div class="stat"><strong>{h(counts['local_private_ocr'])}</strong><span>国内私有 OCR 待审</span></div>
  <div class="stat"><strong>{h(counts['local_private_excluded'])}</strong><span>私有 OCR 海外排除</span></div>
  <div class="stat"><strong>{h(counts['flags'])}</strong><span>质量警告</span></div>
</section>
<div class="notice">这是独立 staging 层，不等同于正式 SQLite。正式库状态：{h(formal_status)}。页图数量不会被当作文献数量；目录、网页快照、未核验 OCR、机器语义信号和 locator-only evidence unit 不会自动成为 citation-ready。“1942/43 一手候选（未核原件）”只是机器筛选线索，不代表已取得原件；claim 卡片数包含同页/同文本的 provenance 候选，精确唯一估计与重复组单独显示。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-calendar"/></svg>文献对象时期分布</h2></div>
<section class="result-list">{phase_html}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-book"/></svg>核心早期资料覆盖</h2></div>
<section class="result-list">{phase2_html}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>本地私有 OCR 文献分层</h2></div>
<section class="result-list">{local_scope_html}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>资产类型分布</h2></div>
<section class="result-list">{kind_html}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-check"/></svg>质量警告</h2></div>
<section class="result-list">{flag_html}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-book"/></svg>数据说明</h2></div>
<div class="notice">本页由 {h(run['run_id'] if run else 'unknown')} staging run 生成，来源：canonical reconciliation、machine-text migration、OCR provenance migration、citation gate、claim-candidate extraction、rule annotation 与 semantic triage。{h(counts['semantic_ready'])} 条进入语义复核队列，{h(counts['semantic_holds'])} 条保留机器 HOLD；正式库 citation-ready 仍为 0。</div>
"""
    return layout("国内质量底座", body, active_path="/domestic/quality")


def domestic_academic_page() -> bytes:
    """国内学术研究层：分级、去重与引用链说明。"""
    policy = _load_academic_source_policy()
    snapshot = _academic_layer_snapshot()
    tier_cards = "".join(
        f'''<article class="result"><div><h2>{h(tier.get("code"))} · {h(tier.get("name"))}</h2>
        <div class="meta">{h(tier.get("rule"))}</div><div class="snippet">使用边界：{h(tier.get("use"))}</div></div></article>'''
        for tier in policy.get("source_tiers", [])
        if isinstance(tier, dict)
    )
    tier_counts = snapshot.get("tiers") or {}
    tier_summary = " · ".join(f"{h(key)} {h(value)} 条" for key, value in tier_counts.items()) or "尚无学术统计"
    status_summary = " · ".join(
        f"{h(key)} {h(value)} 条"
        for key, value in list((snapshot.get("fulltext_statuses") or {}).items())[:8]
    ) or "尚无全文状态统计"
    institution_cards = "".join(
        f'''<article class="result compact-result"><div><h3>{h(row.get("name"))}</h3>
        <div class="meta">{h(row.get("count"))} 条记录</div></div></article>'''
        for row in snapshot.get("institutions", [])
        if isinstance(row, dict)
    ) or '<div class="notice">当前层没有机构分布；正式库 fallback 不复制 staging 机构字段。</div>'
    if snapshot.get("available"):
        availability = f'''<section class="stats">
  <div class="stat"><strong>{h(snapshot["records"])}</strong><span>研究/官方资料</span></div>
  <div class="stat"><strong>{h(snapshot["academic_records"])}</strong><span>学术研究记录</span></div>
  <div class="stat"><strong>{h(snapshot["high_priority"])}</strong><span>S/A 优先记录</span></div>
  <div class="stat"><strong>{h(snapshot["articles"])}</strong><span>学术文章记录</span></div>
  <div class="stat"><strong>{h(snapshot["citation_ready"])}</strong><span>staging citation-ready</span></div>
</section>'''
    else:
        availability = '<div class="notice">当前 checkout 没有可读的国内 staging 数据库；正式学术全文索引也尚未可读，研究资料统计将在 staging 或正式数据库恢复后显示。</div>'
    if snapshot.get("fallback") == "formal_index":
        availability += '<div class="notice">当前显示的是正式 SQLite 中已索引的学术全文 fallback；书目机构字段仍以 staging 为准，正文仅为 review_only 检索层。</div>'
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "学术研究层")]) + f"""
<section class="doc-head"><div><h1>国内学术研究层</h1><div class="meta">把学术论文、专著、档案指南和民盟中央研究资料放入解释层，并与一手史料分开管理。</div></div><div class="doc-tools"><a class="button" href="/domestic/search?scope=research">检索研究资料</a><a class="button secondary" href="/research">多源专题</a></div></section>
{availability}
<div class="notice"><strong>核心口径：</strong>{h(policy.get("purpose") or "学术研究用于解释、索引和交叉核对，不自动替代一手史料。")}
<br><strong>机构核验：</strong>{h(policy.get("institution_rule") or "机构层级必须回到可追溯的记录字段和来源。")}
<br><strong>全文门禁：</strong>{h(policy.get("fulltext_rule") or "目录、摘要、OCR 和索引页不自动进入正式引文。")}</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-book"/></svg>来源层级</h2><span class="meta">{tier_summary}</span></div>
<section class="result-list">{tier_cards or '<div class="notice">学术来源分级策略尚未生成。</div>'}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-check"/></svg>全文与引用状态</h2><span class="meta">{status_summary}</span></div>
<div class="notice">正式引用链必须经过：研究记录 → 来源入口/目录 → 本地文件或稳定全文 → 页码/章节定位 → SHA-256 → 复核状态 → citation-ready。当前统计中的 staging 字段不会自动修改正式库门禁。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-building"/></svg>机构元数据分布</h2><span class="meta">仅显示记录字段，不自动宣称985或任职资格</span></div>
<section class="result-list">{institution_cards}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-arrow-right"/></svg>下一步工作</h2></div>
<section class="result-list">
  <article class="result"><div><h2>优先补全文和页码</h2><div class="snippet">先处理 S/A 层中作者、机构、来源入口完整且与九专题直接相关的文章；目录页和元数据只进入补证队列。</div></div></article>
  <article class="result"><div><h2>建立同文/版本关系</h2><div class="snippet">题名、作者、年份和机构相同的条目先聚类，保留不同版本，不把转载重复计算为多个论据。</div></div></article>
  <article class="result"><div><h2>回接专题和一手证据</h2><div class="snippet">学术文章解释“为什么”和“如何理解”，一手页级材料负责“原文说了什么”；两者在专题页并列但不互相替代。</div></div></article>
</section>
"""
    return layout("国内学术研究层", body, active_path="/domestic/academic")


def _formal_academic_documents(external_ids: list[str]) -> dict[str, sqlite3.Row]:
    """为 staging 学术记录补上正式库全文入口；不改变任何证据等级。"""
    if not external_ids or not DB_PATH.exists():
        return {}
    placeholders = ",".join("?" for _ in external_ids)
    try:
        with conn() as c:
            rows = c.execute(
                f"""SELECT d.doc_key, d.doc_id, d.title,
                           count(DISTINCT p.id) AS page_count,
                           COALESCE(sum(length(COALESCE(p.text, ''))), 0) AS text_chars
                    FROM documents d
                    LEFT JOIN pages p ON p.document_id=d.id
                    WHERE d.source_platform='domestic'
                      AND d.hit_type='domestic_academic_fulltext'
                      AND d.doc_id IN ({placeholders})
                    GROUP BY d.id, d.doc_key, d.doc_id, d.title""",
                external_ids,
            ).fetchall()
    except sqlite3.Error:
        return {}
    return {str(row["doc_id"]): row for row in rows}


def domestic_formal_academic_search_page(raw_q: str = "", phase: str = "") -> bytes:
    """没有 staging 时，用正式库中已索引的学术全文提供可用的研究检索。"""
    clauses = [
        "d.source_platform='domestic'",
        "d.hit_type='domestic_academic_fulltext'",
    ]
    params: list[object] = []
    if raw_q:
        like = f"%{raw_q}%"
        clauses.append("(d.doc_id LIKE ? OR d.title LIKE ? OR d.matched_terms LIKE ? OR p.text LIKE ?)")
        params.extend([like, like, like, like])
    if phase:
        clauses.append("d.date_guess LIKE ?")
        params.append(f"%{phase}%")
    try:
        with conn() as c:
            rows = c.execute(
                f"""SELECT d.doc_key, d.doc_id, d.title, d.date_guess, d.url,
                           d.matched_terms, count(p.id) AS page_count,
                           sum(length(COALESCE(p.text,''))) AS text_chars
                    FROM documents d JOIN pages p ON p.document_id=d.id
                    WHERE {' AND '.join(clauses)}
                    GROUP BY d.id, d.doc_key, d.doc_id, d.title, d.date_guess, d.url, d.matched_terms
                    ORDER BY d.date_guess, d.doc_id LIMIT 100""",
                params,
            ).fetchall()
    except sqlite3.Error as exc:
        return layout("国内检索", f'<div class="notice">正式学术索引读取失败：{h(exc)}</div>', active_path="/domestic/search")
    result_html = "".join(
        f'''<article class="result"><div><h2>{h(row["title"] or row["doc_id"])}</h2>
        <div class="meta">{h(row["doc_id"])} · 正式学术全文索引 · {h(row["date_guess"] or "未标注")}</div>
        <div class="snippet">{h(row["page_count"])} 页 · {h(row["text_chars"] or 0)} 字 · review_only · citation_ready=0</div></div>
        <div class="cite"><a href="{h(source_href(row["url"] or "#"))}">来源入口</a> · <a href="/doc/{quote(str(row["doc_key"]), safe="")}">正式全文页</a></div></article>'''
        for row in rows
    ) or '<div class="notice">正式学术全文索引中没有匹配结果。</div>'
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "国内检索")]) + f"""
<section class="doc-head"><div><h1>国内研究资料检索</h1><div class="meta">formal SQLite academic fallback · staging 不可用时仍可检索已入库全文</div></div><div class="doc-tools"><a class="button secondary" href="/domestic/academic">学术层说明</a></div></section>
<form class="filter-form" method="get" action="/domestic/search">
  <input type="hidden" name="scope" value="research">
  <label>关键词 <input name="q" value="{h(raw_q)}" placeholder="题名、作者、事件词"></label>
  <label>时期 <input name="phase" value="{h(phase)}" placeholder="如 1946"></label>
  <button class="button" type="submit">检索</button>
</form>
<div class="notice">这是解释层全文，不是正式一手证据；当前条目统一保持 review_only / citation_ready=0。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-search"/></svg>正式学术全文（{len(rows)} 条）</h2></div>
<section class="result-list">{result_html}</section>
"""
    return layout("国内检索", body, active_path="/domestic/search")


def domestic_staging_search_page(query: dict[str, list[str]] | None = None) -> bytes:
    """在独立 staging 层分开检索文献对象和物理页资产。"""
    query = query or {}
    raw_q = (query.get("q", [""])[0] or "").strip()[:200]
    scope = (query.get("scope", ["documents"])[0] or "documents").strip()
    if scope not in {"documents", "pages", "machine", "ocr", "claims", "local", "research"}:
        scope = "documents"
    phase = (query.get("phase", [""])[0] or "").strip()[:80]
    if not DOMESTIC_STAGING_DB_PATH.exists():
        if scope == "research":
            return domestic_formal_academic_search_page(raw_q, phase)
        return layout(
            "国内检索",
            '<div class="notice">国内 staging 数据库尚未建立。请先运行 Phase 0 reconciliation 与 staging 构建。</div>',
            active_path="/domestic/search",
        )
    structured_relation_rows: dict[str, dict] = {}
    if STRUCTURED_RELATION_ROWS_PATH.exists():
        try:
            for line in STRUCTURED_RELATION_ROWS_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line)
                    structured_relation_rows[item["representative_candidate_id"]] = item
        except (OSError, json.JSONDecodeError, KeyError):
            structured_relation_rows = {}
    conservative_relation_rows: dict[str, dict] = {}
    if CONSERVATIVE_RELATION_ROWS_PATH.exists():
        try:
            for line in CONSERVATIVE_RELATION_ROWS_PATH.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    item = json.loads(line)
                    conservative_relation_rows[item["representative_candidate_id"]] = item
        except (OSError, json.JSONDecodeError, KeyError):
            conservative_relation_rows = {}
    like = f"%{raw_q}%"
    try:
        c = sqlite3.connect(DOMESTIC_STAGING_DB_PATH)
        c.row_factory = sqlite3.Row
        if scope == "documents":
            clauses = []
            params: list[object] = []
            if raw_q:
                clauses.append("(d.canonical_document_key LIKE ? OR d.title LIKE ? OR d.dominant_phase LIKE ?)")
                params.extend([like, like, like])
            if phase:
                clauses.append("d.dominant_phase = ?")
                params.append(phase)
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            rows = c.execute(
                f"""SELECT d.canonical_document_key, d.title, d.dominant_phase,
                           d.source_row_count, d.page_row_count, d.file_row_count,
                           d.unique_sha256_count, d.evidence_status
                    FROM documents d{where}
                    ORDER BY d.dominant_phase, d.canonical_document_key
                    LIMIT 100""",
                params,
            ).fetchall()
        elif scope == "pages":
            clauses = []
            params = []
            if raw_q:
                clauses.append("(p.object_id LIKE ? OR p.local_path LIKE ? OR p.title LIKE ? OR p.historical_phase LIKE ? OR p.reclass_bucket LIKE ?)")
                params.extend([like, like, like, like, like])
            if phase:
                clauses.append("p.historical_phase = ?")
                params.append(phase)
            where = " WHERE " + " AND ".join(clauses) if clauses else ""
            rows = c.execute(
                f"""SELECT p.object_id, d.canonical_document_key, p.local_path,
                           p.page_no, p.sha256, p.file_kind, p.historical_phase,
                           p.reclass_bucket, p.title
                    FROM page_assets p JOIN documents d ON d.id = p.document_id{where}
                    ORDER BY p.historical_phase, d.canonical_document_key, p.page_no
                    LIMIT 100""",
                params,
            ).fetchall()
        elif scope == "machine":
            has_machine_text = c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='machine_text_records'"
            ).fetchone() is not None
            if not has_machine_text:
                rows = []
            else:
                clauses = []
                params = []
                if raw_q:
                    clauses.append("(m.object_id LIKE ? OR m.title LIKE ? OR m.formation_institution LIKE ? OR m.document_type LIKE ? OR m.evidence_tier LIKE ? OR m.historical_phase LIKE ?)")
                    params.extend([like, like, like, like, like, like])
                if phase:
                    clauses.append("m.historical_phase = ?")
                    params.append(phase)
                where = " WHERE " + " AND ".join(clauses) if clauses else ""
                rows = c.execute(
                    f"""SELECT m.object_id, m.title, m.formation_institution,
                               m.document_type, m.source_url, m.local_path, m.sha256,
                               m.evidence_tier, m.historical_phase, m.access_status,
                               m.rights_note
                        FROM machine_text_records m{where}
                        ORDER BY m.historical_phase, m.object_id
                        LIMIT 100""",
                    params,
                ).fetchall()
        elif scope == "ocr":
            has_ocr = c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='ocr_versions'"
            ).fetchone() is not None
            if not has_ocr:
                rows = []
            else:
                clauses = []
                params = []
                if raw_q:
                    clauses.append("(o.provenance_id LIKE ? OR o.source_id LIKE ? OR o.source_title LIKE ? OR o.source_file LIKE ? OR o.period LIKE ? OR o.ocr_md_path LIKE ?)")
                    params.extend([like, like, like, like, like, like])
                if phase:
                    clauses.append("o.period LIKE ?")
                    params.append(f"%{phase}%")
                where = " WHERE " + " AND ".join(clauses) if clauses else ""
                rows = c.execute(
                    f"""SELECT o.provenance_id, o.canonical_document_key, o.source_id,
                               o.source_title, o.source_file, o.physical_page_no,
                               o.pdf_page_no, o.ocr_md_path, o.ocr_md_sha256,
                               o.ocr_confidence, o.text_structure_status,
                               o.machine_visual_status, o.valid, o.citation_ready,
                               o.human_verified, o.year, o.period, o.binding_status
                        FROM ocr_versions o{where}
                        ORDER BY o.year, o.source_id, o.physical_page_no
                        LIMIT 100""",
                    params,
                ).fetchall()
        elif scope == "local":
            has_local_source = c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_source_objects'"
            ).fetchone() is not None
            if not has_local_source:
                rows = []
            else:
                has_local_semantic = c.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_semantic_signals'"
                ).fetchone() is not None
                has_local_cards = c.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='local_evidence_cards'"
                ).fetchone() is not None
                clauses = []
                params = []
                if raw_q:
                    clauses.append("(l.object_id LIKE ? OR l.title LIKE ? OR l.document_date LIKE ? OR l.document_class LIKE ? OR l.relation_status LIKE ?)")
                    params.extend([like, like, like, like, like])
                if phase:
                    clauses.append("l.document_date LIKE ?")
                    params.append(f"%{phase}%")
                where = " WHERE " + " AND ".join(clauses) if clauses else ""
                semantic_join = "LEFT JOIN local_semantic_signals s ON s.object_id=l.object_id" if has_local_semantic else ""
                semantic_select = ", s.machine_signal_status, s.signal_json" if has_local_semantic else ", NULL AS machine_signal_status, NULL AS signal_json"
                card_join = "LEFT JOIN local_evidence_cards ec ON ec.object_id=l.object_id" if has_local_cards else ""
                card_select = ", ec.card_status" if has_local_cards else ", NULL AS card_status"
                rows = c.execute(
                    f"""SELECT l.object_id, l.title, l.document_date, l.source_path,
                               l.source_sha256, l.derived_text_path,
                               l.derived_text_sha256, l.source_layer,
                               l.document_class, l.relation_status,
                               l.evidence_status, l.citation_ready,
                               l.human_verified, a.quality_status, a.char_count,
                               a.han_character_count{semantic_select}{card_select}
                        FROM local_source_objects l
                        LEFT JOIN local_text_audit a ON a.object_id=l.object_id
                        {semantic_join}
                        {card_join}{where}
                        ORDER BY l.document_date, l.object_id
                        LIMIT 100""",
                    params,
                ).fetchall()
        elif scope == "research":
            has_research_materials = c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domestic_research_materials'"
            ).fetchone() is not None
            if not has_research_materials:
                rows = []
            else:
                clauses = []
                params = []
                if raw_q:
                    clauses.append("(r.external_id LIKE ? OR r.title LIKE ? OR r.author LIKE ? OR r.institution LIKE ? OR r.research_type LIKE ? OR r.fulltext_status LIKE ?)")
                    params.extend([like, like, like, like, like, like])
                if phase:
                    clauses.append("(r.publication_date LIKE ? OR json_extract(r.metadata_json, '$.research_theme_phase') LIKE ?)")
                    params.extend([f"%{phase}%", f"%{phase}%"])
                where = " WHERE " + " AND ".join(clauses) if clauses else ""
                rows = c.execute(
                    f"""SELECT r.external_id, r.title, r.author, r.institution,
                               r.layer, r.publication_date, r.research_type, r.quality_tier,
                               r.source_url, r.local_path, r.fulltext_status,
                               r.review_status, r.citation_ready, r.human_verified
                        FROM domestic_research_materials r{where}
                        ORDER BY r.quality_tier, r.publication_date, r.external_id
                        LIMIT 100""",
                    params,
                ).fetchall()
        else:
            has_claims = c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_candidates'"
            ).fetchone() is not None
            if not has_claims:
                rows = []
            else:
                has_claim_locator_audit = c.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_locator_audit'"
                ).fetchone() is not None
                locator_select = ", la.audit_status AS locator_audit_status" if has_claim_locator_audit else ", NULL AS locator_audit_status"
                locator_join = "LEFT JOIN evidence_claim_locator_audit la ON la.candidate_id=e.candidate_id" if has_claim_locator_audit else ""
                has_claim_triage = c.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_semantic_triage'"
                ).fetchone() is not None
                triage_select = ", ct.triage_class, ct.triage_status" if has_claim_triage else ", NULL AS triage_class, NULL AS triage_status"
                triage_join = "LEFT JOIN evidence_claim_semantic_triage ct ON ct.candidate_id=e.candidate_id" if has_claim_triage else ""
                has_claim_cards = c.execute(
                    "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_claim_cards'"
                ).fetchone() is not None
                card_select = ", cc.card_status" if has_claim_cards else ", NULL AS card_status"
                card_join = "LEFT JOIN evidence_claim_cards cc ON cc.candidate_id=e.candidate_id" if has_claim_cards else ""
                clauses = []
                params = []
                if raw_q:
                    clauses.append("(e.candidate_id LIKE ? OR e.canonical_document_key LIKE ? OR e.source_title LIKE ? OR e.candidate_text LIKE ? OR e.period LIKE ?)")
                    params.extend([like, like, like, like, like])
                if phase:
                    clauses.append("e.period LIKE ?")
                    params.append(f"%{phase}%")
                where = " WHERE " + " AND ".join(clauses) if clauses else ""
                rows = c.execute(
                    f"""SELECT e.candidate_id, e.canonical_document_key,
                               e.physical_page_no, e.source_title, e.period,
                               e.candidate_text, e.candidate_text_sha256,
                               e.claim_status, e.source_ocr_md_path,
                               a.claim_family, a.matched_terms_json,
                               s.review_stage, s.priority{locator_select}{triage_select}{card_select}
                        FROM evidence_claim_candidates e
                        LEFT JOIN evidence_candidate_annotations a ON a.candidate_id=e.candidate_id
                        LEFT JOIN semantic_review_queue s ON s.candidate_id=e.candidate_id
                        {locator_join}
                        {triage_join}
                        {card_join}{where}
                        ORDER BY e.period, e.canonical_document_key, e.physical_page_no
                        LIMIT 100""",
                    params,
                ).fetchall()
        c.close()
    except sqlite3.Error as exc:
        return layout(
            "国内检索",
            f'<div class="notice">staging 数据库读取失败：{h(exc)}</div>',
            active_path="/domestic/search",
        )

    formal_academic = _formal_academic_documents(
        [str(row["external_id"]) for row in rows]
    ) if scope == "research" else {}

    def document_title(raw: object) -> str:
        try:
            value = json.loads(str(raw or ""))
            if isinstance(value, list) and value:
                return "；".join(str(x) for x in value[:2])
        except (TypeError, json.JSONDecodeError):
            pass
        return str(raw or "未命名文献")

    if scope == "documents":
        result_html = "".join(
            f'''<article class="result"><div><h2>{h(document_title(row["title"]))}</h2>
            <div class="meta">{h(row["canonical_document_key"])} · 时期 {h(row["dominant_phase"] or "unknown")} · 页资产 {h(row["page_row_count"])} · 文件 {h(row["file_row_count"])}</div>
            <div class="snippet">来源行 {h(row["source_row_count"])} · 唯一 SHA {h(row["unique_sha256_count"])} · 状态 {h(row["evidence_status"])}</div></div><div class="cite"><a href="/domestic/document?key={quote(str(row["canonical_document_key"]), safe='')}">打开文献</a></div></article>'''
            for row in rows
        )
    elif scope == "pages":
        result_html = "".join(
            f'''<article class="result"><div><h2>{h(row["title"] or row["object_id"] or "未命名页资产")}</h2>
            <div class="meta">{h(row["canonical_document_key"])} · 物理页 {h(row["page_no"] or "未标注")} · {h(row["historical_phase"] or "unknown")} · {h(row["file_kind"])}</div>
            <div class="snippet">{h(row["local_path"] or "无本地路径")} · SHA {h((row["sha256"] or "")[:16])}… · {h(row["reclass_bucket"] or "unknown")}</div></div><div class="cite"><a href="/domestic/document?key={quote(str(row["canonical_document_key"]), safe='')}">查看文献</a></div></article>'''
            for row in rows
        )
    elif scope == "machine":
        result_html = "".join(
            f'''<article class="result"><div><h2>{h(row["title"] or row["object_id"] or "未命名官方文本")}</h2>
            <div class="meta">{h(row["object_id"])} · {h(row["formation_institution"] or "机构未标注")} · 时期 {h(row["historical_phase"] or "unknown")}</div>
            <div class="snippet">{h(row["document_type"] or "未标注类型")} · {h(row["evidence_tier"])} · {h(row["access_status"] or "unknown")} · SHA {h((row["sha256"] or "")[:16])}…</div></div><div class="cite"><a href="{h(source_href(row["source_url"] or row["local_path"] or "#"))}">来源入口</a></div></article>'''
            for row in rows
        )
    elif scope == "ocr":
        result_html = "".join(
            f'''<article class="result"><div><h2>{h(row["source_title"] or row["source_id"] or row["provenance_id"])}</h2>
            <div class="meta">{h(row["source_id"])} · 物理页 {h(row["physical_page_no"] or "未标注")} · {h(row["period"] or "unknown")} · {h(row["binding_status"])}</div>
            <div class="snippet">OCR {h(row["text_structure_status"])} · 置信度 {h(row["ocr_confidence"] or "NA")} · valid={h(row["valid"])} · SHA {h((row["ocr_md_sha256"] or "")[:16])}… · {h(row["ocr_md_path"] or "无 OCR 路径")}</div></div></article>'''
            for row in rows
        )
    elif scope == "local":
        result_html = "".join(
            f'''<article class="result"><div><h2>{h(row["title"] or row["object_id"])}</h2>
            <div class="meta">{h(row["object_id"])} · 日期 {h(row["document_date"] or "unknown")} · {h(row["document_class"])} · {h(row["relation_status"])}</div>
            <div class="snippet">原件/来源 SHA {h((row["source_sha256"] or "")[:16])}… · 派生文本 SHA {h((row["derived_text_sha256"] or "")[:16])}… · 文本结构 {h(row["quality_status"] or "未审计")} · 机器语义 {h(row["machine_signal_status"] or "未提取")} · 证据卡片 {h(row["card_status"] or "未生成")} · 字符 {h(row["char_count"] or 0)} · citation_ready={h(row["citation_ready"])}</div></div></article>'''
            for row in rows
        )
    elif scope == "research":
        result_html = "".join(
            f'''<article class="result"><div><h2>{h(row["title"] or row["external_id"])}</h2>
            <div class="meta">{h(row["external_id"])} · {h(row["layer"] or "研究资料")} · {h(row["research_type"] or "未标注类型")} · 质量 {h(row["quality_tier"] or "未分级")}</div>
            <div class="snippet">{h(row["institution"] or "机构未标注")} · 出版/发表 {h(row["publication_date"] or "未标注")} · {h(row["fulltext_status"])} · citation_ready={h(row["citation_ready"])} · human_verified={h(row["human_verified"])}</div></div><div class="cite"><a href="{h(source_href(row["source_url"] or "#"))}">来源入口</a>{f' · <a href="/doc/{quote(str(formal_academic[str(row["external_id"])] ["doc_key"]), safe="")}">正式全文页</a> <span class="meta">{h(formal_academic[str(row["external_id"])] ["page_count"])}页</span>' if str(row["external_id"]) in formal_academic else ' · <span class="meta">尚未进入正式全文层</span>'}</div></article>'''
            for row in rows
        )
    else:
        claim_results = []
        for row in rows:
            relation = structured_relation_rows.get(row["candidate_id"], {})
            adjudication = conservative_relation_rows.get(row["candidate_id"], {})
            relation_text = (
                f'全文关系 {h(adjudication.get("adjudicated_relation_candidate") or relation.get("relation_signal") or "未建立")} '
                f'· 验证 {h(adjudication.get("verification_status") or relation.get("relation_status") or "未验证")}'
            ) if relation or adjudication else "全文关系 未进入复核卡片"
            claim_results.append(
                f'''<article class="result"><div><h2>{h(row["source_title"] or row["candidate_id"])}</h2>
                <div class="meta">{h(row["canonical_document_key"] or "未绑定")} · 物理页 {h(row["physical_page_no"] or "未标注")} · {h(row["period"] or "unknown")} · {h(row["claim_status"])} · 标签 {h(row["claim_family"] or "未标注")} · 定位 {h(row["locator_audit_status"] or "未审计")} · 分流 {h(row["triage_class"] or "未分流")} · 卡片 {h(row["card_status"] or "未生成")} · {h(row["review_stage"] or "未排队")} {h(row["priority"] or "")} · {relation_text}</div>
                <div class="snippet">{h(compact(row["candidate_text"], 360))} · 片段 SHA {h((row["candidate_text_sha256"] or "")[:16])}…</div></div></article>'''
            )
        result_html = "".join(claim_results)
    if not result_html:
        result_html = '<div class="notice">没有匹配结果。可以换用来源编号、报刊名、时期或文件类型搜索。</div>'
    doc_cls = "button" if scope == "documents" else "button secondary"
    page_cls = "button" if scope == "pages" else "button secondary"
    machine_cls = "button" if scope == "machine" else "button secondary"
    ocr_cls = "button" if scope == "ocr" else "button secondary"
    claims_cls = "button" if scope == "claims" else "button secondary"
    local_cls = "button" if scope == "local" else "button secondary"
    research_cls = "button" if scope == "research" else "button secondary"
    scope_label = {"documents": "文献对象", "pages": "物理页资产", "machine": "官方/机器文本", "ocr": "OCR provenance", "claims": "语义候选片段", "local": "本地 staging 对象", "research": "国内研究资料"}[scope]
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "国内检索")]) + f"""
<section class="doc-head"><div><h1>国内 staging 检索</h1><div class="meta">文献对象、物理页资产、官方/机器文本、OCR provenance、语义候选、本地 staging 材料和研究资料分开计数；结果来自独立 staging，不会修改正式库</div></div><div class="doc-tools"><a class="{doc_cls}" href="/domestic/search?scope=documents&amp;q={quote(raw_q)}&amp;phase={quote(phase)}">文献对象</a><a class="{page_cls}" href="/domestic/search?scope=pages&amp;q={quote(raw_q)}&amp;phase={quote(phase)}">物理页</a><a class="{machine_cls}" href="/domestic/search?scope=machine&amp;q={quote(raw_q)}&amp;phase={quote(phase)}">官方/机器文本</a><a class="{ocr_cls}" href="/domestic/search?scope=ocr&amp;q={quote(raw_q)}&amp;phase={quote(phase)}">OCR provenance</a><a class="{claims_cls}" href="/domestic/search?scope=claims&amp;q={quote(raw_q)}&amp;phase={quote(phase)}">语义候选片段</a><a class="{local_cls}" href="/domestic/search?scope=local&amp;q={quote(raw_q)}&amp;phase={quote(phase)}">本地 staging</a><a class="{research_cls}" href="/domestic/search?scope=research&amp;q={quote(raw_q)}&amp;phase={quote(phase)}">研究资料</a></div></section>
<form class="filter-form" method="get" action="/domestic/search">
  <input type="hidden" name="scope" value="{h(scope)}">
  <label>关键词 <input name="q" value="{h(raw_q)}" placeholder="报刊名、来源编号、时期、文件类型"></label>
  <label>时期 <input name="phase" value="{h(phase)}" placeholder="如 1947"></label>
  <button class="button" type="submit">检索</button>
</form>
<div class="notice">最多显示 100 条。路径和 SHA 只用于 provenance 追踪；机器 OCR、目录和未核验页不会自动成为 citation-ready。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-search"/></svg>{scope_label}（{len(rows)} 条）</h2></div>
<section class="result-list">{result_html}</section>
"""
    return layout("国内检索", body, active_path="/domestic/search")


def domestic_staging_document_page(query: dict[str, list[str]] | None = None) -> bytes:
    """展示一个 staging canonical 文献及其物理页资产。"""
    query = query or {}
    key = (query.get("key", [""])[0] or "").strip()[:500]
    if not key:
        return layout(
            "国内文献",
            '<div class="notice">缺少 canonical 文献键。请从国内检索结果进入。</div>',
            active_path="/domestic/search",
        )
    if not DOMESTIC_STAGING_DB_PATH.exists():
        return layout(
            "国内文献",
            '<div class="notice">国内 staging 数据库尚未建立。</div>',
            active_path="/domestic/search",
        )
    try:
        c = sqlite3.connect(DOMESTIC_STAGING_DB_PATH)
        c.row_factory = sqlite3.Row
        document = c.execute(
            """SELECT id, canonical_document_key, title, dominant_phase,
                      source_row_count, page_row_count, file_row_count,
                      unique_sha256_count, unique_path_count, evidence_status
               FROM documents WHERE canonical_document_key = ?""",
            (key,),
        ).fetchone()
        pages = c.execute(
            """SELECT object_id, local_path, page_no, sha256, file_kind,
                      historical_phase, reclass_bucket, title
               FROM page_assets WHERE document_id = ?
               ORDER BY page_no, local_path LIMIT 500""",
            (document["id"],),
        ).fetchall() if document else []
        c.close()
    except sqlite3.Error as exc:
        return layout("国内文献", f'<div class="notice">staging 数据库读取失败：{h(exc)}</div>', active_path="/domestic/search")
    if document is None:
        return layout("国内文献", f'<div class="notice">未找到 canonical 文献：{h(key)}</div>', active_path="/domestic/search")

    title = document["title"] or "未命名文献"
    try:
        parsed_title = json.loads(str(title))
        if isinstance(parsed_title, list):
            title = "；".join(str(x) for x in parsed_title[:4])
    except (TypeError, json.JSONDecodeError):
        pass
    page_html = "".join(
        f'''<article class="result"><div><h2>物理页 {h(row["page_no"] or "未标注")}</h2>
        <div class="meta">{h(row["file_kind"])} · 来源时期 {h(row["historical_phase"] or "unknown")} · 重分类 {h(row["reclass_bucket"] or "unknown")}</div>
        <div class="snippet">{h(row["local_path"] or "无路径")} · SHA-256 {h(row["sha256"] or "缺失")} · object {h(row["object_id"] or "unknown")}</div></div></article>'''
        for row in pages
    ) or '<div class="notice">该文献目前没有物理页资产。</div>'
    body = breadcrumb_html([("/domestic", "国内史料"), ("/domestic/search", "国内检索"), (None, "文献详情")]) + f"""
<section class="doc-head"><div><h1>{h(title)}</h1><div class="meta">{h(document["canonical_document_key"])}</div></div><div class="doc-tools"><a class="button" href="/domestic/search?scope=pages&amp;q={quote(key)}">检索此文献页</a></div></section>
<section class="stats">
  <div class="stat"><strong>{h(document["page_row_count"])}</strong><span>页资产</span></div>
  <div class="stat"><strong>{h(document["file_row_count"])}</strong><span>文件资产</span></div>
  <div class="stat"><strong>{h(document["unique_sha256_count"])}</strong><span>唯一 SHA</span></div>
  <div class="stat"><strong>{h(document["dominant_phase"] or "unknown")}</strong><span>来源时期标签</span></div>
</section>
<div class="notice">证据状态：{h(document["evidence_status"])}。本页展示的是 staging canonical 对象和物理资产，不代表已经完成 OCR、证据单元或 citation-ready 验收。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>物理页与文件资产（最多显示 500 条）</h2></div>
<section class="result-list">{page_html}</section>
"""
    return layout("国内文献", body, active_path="/domestic/search")


def domestic_sources_page() -> bytes:
    """国内来源家族与机构地图。"""
    with conn() as c:
        rows = c.execute(
            """SELECT source_name, institution, source_type, authority_level,
                      official_url, record_or_search_url, access_mode,
                      rights_status, shanghai_relevance, status, verification_note
               FROM domestic_sources
               ORDER BY shanghai_relevance DESC, source_name"""
        ).fetchall()
    families = {
        "民盟自身文件": {"民盟", "盟史", "民盟中央", "民盟地方"},
        "党政机关档案": {"档案", "政府", "党政"},
        "政协与统一战线": {"政协", "统战"},
        "国内同期报刊": {"报刊", "报纸", "期刊", "文献"},
        "人物与地方组织档案": {"人物", "地方", "上海"},
    }
    family_rows: list[str] = []
    for family, keywords in families.items():
        matched = [row for row in rows if any(k in f"{row['source_name']} {row['institution']} {row['source_type']}" for k in keywords)]
        family_rows.append(
            f'<article class="result"><div><h2>{h(family)}</h2>'
            f'<div class="meta">已登记 {len(matched)} 个来源入口</div>'
            f'<div class="snippet">来源卡仍按机构、权威级别、访问方式和权利状态逐条复核。</div>'
            f'</div><div class="cite"><a href="/domestic/sources?q={quote(family)}">查看</a></div></article>'
        )
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "来源地图")]) + f"""
<section class="doc-head"><div><h1>国内研究平台：来源与馆藏地图</h1><div class="meta">来源家族、权威入口、访问方式与上海关联度</div></div><div class="doc-tools"><a class="button" href="/domestic">候选目录</a></div></section>
<section class="stats"><div class="stat"><strong>{h(len(rows))}</strong><span>来源卡</span></div><div class="stat"><strong>{h(sum(1 for row in rows if row['access_mode'] == 'open'))}</strong><span>开放入口</span></div><div class="stat"><strong>{h(sum(1 for row in rows if row['rights_status'] != 'public'))}</strong><span>权利待核</span></div></section>
<div class="notice"><strong>国内史料层：</strong>来源卡是检索入口，不等于已取得原件；记录级档号、卷期、影像和复制权利仍以候选卡的复核结果为准。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-building"/></svg>五个来源家族</h2></div><section class="result-list">{''.join(family_rows)}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>来源卡明细</h2></div><section class="result-list">"""
    for row in rows:
        link = row["official_url"] or row["record_or_search_url"] or "#"
        body += f"""
<article class="result"><div>{title_block(row['source_name'], link)}
  <div class="meta">{h(row['institution'])} · {h(row['source_type'])} · {h(row['authority_level'])}</div>
  <div class="tagline"><span class="tag">上海相关性：{h(row['shanghai_relevance'])}</span><span class="pstatus {'ok' if row['status'] == 'verified' else 'warn'}">{h(row['status'])}</span></div>
  <div class="snippet">访问：{h(row['access_mode'])} · 权利：{h(row['rights_status'])}</div>
  <div class="snippet">{h(row['verification_note'])}</div></div>
  <div class="cite"><a href="{h(link)}" target="_blank" rel="noreferrer">打开入口</a></div></article>"""
    body += "</section>"
    return layout("国内来源地图", body, active_path="/domestic/sources")


def domestic_events_page(query: dict[str, list[str]] | None = None) -> bytes:
    """九个关键事件的国内候选与境外对位索引。"""
    query = query or {}
    selected = query.get("event", [""])[0].strip()
    coverage_path = DATA_ROOT / "domestic" / "event_coverage.json"
    coverage = json.loads(coverage_path.read_text(encoding="utf-8")) if coverage_path.exists() else []
    rows = _domestic_rows()
    by_id = {row["candidate_id"]: row for row in rows}
    cards: list[str] = []
    for item in coverage:
        if selected and selected not in {item["event_id"], item["event_name"]}:
            continue
        linked = [by_id[cid] for cid in item.get("domestic_candidate_ids", []) if cid in by_id]
        tag = (item.get("event_tags") or [""])[0]
        primary = _primary_evidence_display(item)
        domestic_link = f"/domestic?event={quote(tag)}" if tag else "/domestic"
        foreign_links = []
        for slug in item.get("foreign_event_slugs", []):
            foreign_links.append(f'<a href="{h("/events/key/" + slug if event_by_slug(slug) else "/topics/" + slug)}">{h(slug)}</a>')
        unified_link = f'/events?topic={quote(str(item["event_id"]))}'
        cards.append(f"""
<article class="result"><div><h2>{h(item['event_name'])}</h2>
  <div class="meta">国内候选 {len(linked)} 条 · {h(item['domestic_status'])}</div>
  <div class="tagline"><span class="tag">{h(item['pair_status'])}</span><span class="pstatus {'ok' if item['pair_status'] == 'pair_available' else 'warn'}">{'境外已关联' if item.get('foreign_event_slugs') else '境外待补'}</span><span class="pstatus {primary['class']}">{h(primary['label'])}</span></div>
  <div class="snippet">{h(item['review_note'])}</div></div>
  <div class="cite"><a href="{h(unified_link)}">统一事件线索</a> · <a href="{h(domestic_link)}">查看国内记录</a>{' · ' + ' · '.join(foreign_links) if foreign_links else ''}</div></article>""")
    selector = '<a class="button secondary" href="/domestic/events">显示全部</a>' if selected else ''
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "关键事件")]) + f"""
<section class="doc-head"><div><h1>国内关键事件覆盖</h1><div class="meta">国内记录、境外对位和仍待调档的差异说明</div></div><div class="doc-tools"><a class="button" href="/domestic">候选目录</a>{selector}</div></section>
<div class="notice">“已关联”只表示存在可追踪的境外事件入口，不代表国内原件已经取得；“一手证据部分闭环”也不等于事件定义原件已完成闭环。L4/LX 仍停留在线索层。</div>
<section class="result-list">{''.join(cards) or '<div class="notice">未找到该事件。</div>'}</section>"""
    return layout("国内关键事件", body, active_path="/domestic/events")


def _load_domestic_event_coverage() -> list[dict[str, object]]:
    """读取国内候选与境外事件的声明式关联表。

    这张表是研究导航，不是事实断言：candidate_id 只是候选记录关联，
    foreign_event_slugs 只是指向境外专题入口。正式证据仍须回到文档页、
    原件 provenance 和人工复核门禁。
    """
    coverage_path = DATA_ROOT / "domestic" / "event_coverage.json"
    if not coverage_path.is_file():
        return []
    try:
        payload = json.loads(coverage_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return [item for item in payload if isinstance(item, dict) and item.get("event_id")]


PRIMARY_EVIDENCE_STATUS_META = {
    "closed": ("一手证据已闭环", "ok"),
    "partial": ("一手证据部分闭环", "warn"),
    "unclassified": ("一手证据状态未标注", "warn"),
}


def _primary_evidence_display(item: dict[str, object]) -> dict[str, str]:
    """Return the declared primary-source closure state without inferring it.

    The event coverage table is an editorial acceptance record. Page counts,
    OCR status, and foreign links cannot promote a topic to ``closed`` by
    themselves, so the UI only displays the explicit declaration and gap.
    """
    status = str(item.get("primary_evidence_status") or "unclassified")
    label, css_class = PRIMARY_EVIDENCE_STATUS_META.get(
        status,
        (str(item.get("primary_evidence_label") or "一手证据状态未标注"), "warn"),
    )
    return {
        "status": status,
        "label": str(item.get("primary_evidence_label") or label),
        "class": css_class,
        "gap": str(item.get("primary_evidence_gap") or "覆盖表未提供一手证据闭环说明。"),
    }


def _load_topic_comparison_cards() -> dict[str, dict[str, object]]:
    """读取国内/境外专题对读卡；卡片只负责研究编排，不升级证据等级。"""
    if not TOPIC_COMPARISON_CARDS_PATH.is_file():
        return {}
    try:
        payload = json.loads(TOPIC_COMPARISON_CARDS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(item["event_id"]): item
        for item in payload
        if isinstance(item, dict) and item.get("event_id")
    }


def _load_topic_evidence_chains() -> dict[str, dict[str, object]]:
    """读取专题的四层证据链，不从页面正文反推证据等级。"""
    if not TOPIC_EVIDENCE_CHAIN_PATH.is_file():
        return {}
    try:
        payload = json.loads(TOPIC_EVIDENCE_CHAIN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        str(item["event_id"]): item
        for item in payload
        if isinstance(item, dict) and item.get("event_id")
    }


CHAIN_LAYER_META = {
    "primary": ("主证据（页级）", "说明事件定义或组织表达的直接页级材料"),
    "cross_source": ("同期交叉", "来自不同刊物、版别或相邻时间点的对读材料"),
    "negative_checks": ("负向核查", "已经检查但没有命中的官方/目录来源；不等同于不存在"),
    "missing_primary": ("仍待补原件", "决定事件定义能否严格闭环的开放目标"),
}


def _evidence_chain_item_html(item: dict[str, object], layer: str) -> str:
    """渲染证据链元数据；正文仍由原文页路由负责展示。"""
    label = str(item.get("label") or item.get("target") or "未命名证据")
    status = str(item.get("status") or "open")
    status_label = {
        "strict_citation": "正式可引用页",
        "review_only": "待人工复核",
        "negative_control": "负向核查",
        "open": "开放缺口",
    }.get(status, status)
    status_class = "ok" if status == "strict_citation" else "warn"
    page_id = item.get("page_id")
    doc_key = str(item.get("doc_key") or "")
    if page_id and doc_key:
        href = f"/doc/{quote(doc_key)}?page_id={quote(str(page_id))}"
        link_html = f'<a href="{h(href)}">回到原文页 #{h(page_id)}</a>'
    else:
        link_html = ""
    role = str(item.get("role") or item.get("why_it_matters") or "")
    caveat = str(item.get("caveat") or item.get("next_action") or "")
    return f"""
<article class="result compact-result evidence-chain-item">
  <div>
    <h3>{h(label)}</h3>
    <div class="tagline"><span class="pstatus {status_class}">{h(status_label)}</span>{f'<span class="tag">页 {h(page_id)}</span>' if page_id else ''}</div>
    <div class="snippet">{h(role)}</div>
    {f'<div class="snippet"><strong>边界：</strong>{h(caveat)}</div>' if caveat else ''}
  </div>
  <div class="cite">{link_html}</div>
</article>"""


def _topic_evidence_chain_html(chain: dict[str, object] | None) -> str:
    """把四层证据链呈现为可回溯的小节。"""
    if not chain:
        return '<div class="notice">该专题尚未登记结构化证据链；请回到国内复核和调档清单。</div>'
    layers = chain.get("layers") if isinstance(chain.get("layers"), dict) else {}
    sections: list[str] = []
    for layer, (title, description) in CHAIN_LAYER_META.items():
        rows = layers.get(layer, []) if isinstance(layers, dict) else []
        if not isinstance(rows, list):
            rows = []
        cards = "".join(
            _evidence_chain_item_html(item, layer)
            for item in rows
            if isinstance(item, dict)
        )
        empty = '<div class="notice">当前没有登记条目。</div>'
        sections.append(f"""
<div class="section-head"><h3>{h(title)}</h3><span class="meta">{h(description)}</span></div>
<section class="result-list">{cards or empty}</section>""")
    audit_basis = str(chain.get("audit_basis") or "")
    chain_note = str(chain.get("chain_note") or "")
    return f"""
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>四层证据链</h2><span class="meta">最后审计 {h(chain.get('last_audited') or '未标注')}</span></div>
<div class="notice"><strong>证据链纪律：</strong>主证据、同期交叉、负向核查和待补原件分开登记；报刊报道不能自动升级为行政原件，机器文本不能自动升级为正式引用。{f'<br>{h(chain_note)}' if chain_note else ''}{f'<br><span class="meta">{h(audit_basis)}</span>' if audit_basis else ''}</div>
{''.join(sections)}"""


def _topic_evidence_chain_summary(chain: dict[str, object] | None) -> dict[str, int]:
    """Return a compact, metadata-only summary for the topic index."""
    layers = chain.get("layers") if isinstance(chain, dict) else {}
    if not isinstance(layers, dict):
        layers = {}
    layer_count = sum(
        1 for layer in CHAIN_LAYER_META if isinstance(layers.get(layer), list)
    )
    page_items = sum(
        1
        for values in layers.values()
        if isinstance(values, list)
        for value in values
        if isinstance(value, dict) and "page_id" in value
    )
    return {
        "layer_count": layer_count,
        "page_items": page_items,
        "strict_items": sum(
            1
            for values in layers.values()
            if isinstance(values, list)
            for value in values
            if isinstance(value, dict) and value.get("status") == "strict_citation"
        ),
        "open_targets": len(layers.get("missing_primary", []))
        if isinstance(layers.get("missing_primary"), list)
        else 0,
    }


def _research_gap_rows() -> list[dict[str, object]]:
    """把专题证据链中的开放主证据目标展开成执行看板。

    该看板只读取覆盖表、证据链和候选元数据，不读取正文，也不把候选
    记录自动升级为原件。每一行都必须来自 ``missing_primary``，这样页面
    显示的是明确登记的开放目标，而不是根据搜索结果臆测出的“缺口”。
    """
    coverage = _load_domestic_event_coverage()
    comparison_cards = _load_topic_comparison_cards()
    evidence_chains = _load_topic_evidence_chains()
    try:
        domestic_rows = _domestic_rows()
    except sqlite3.OperationalError:
        domestic_rows = []
    domestic_by_id = {str(row["candidate_id"]): row for row in domestic_rows}
    result: list[dict[str, object]] = []
    for item in coverage:
        event_id = str(item.get("event_id") or "")
        chain = evidence_chains.get(event_id) or {}
        layers = chain.get("layers") if isinstance(chain.get("layers"), dict) else {}
        missing = layers.get("missing_primary", []) if isinstance(layers, dict) else []
        if not isinstance(missing, list):
            missing = []
        comparison = comparison_cards.get(event_id) or {}
        candidate_ids = [str(value) for value in item.get("domestic_candidate_ids", [])]
        linked_candidates = [
            domestic_by_id[candidate_id]
            for candidate_id in candidate_ids
            if candidate_id in domestic_by_id
        ]
        candidate_cards = [
            {
                "candidate_id": str(row["candidate_id"]),
                "title": str(row["title"] or row["candidate_id"]),
                "level": str(_domestic_level(row) or row["authenticity_level_proposed"] or "未分级"),
                "review_status": str(row["review_status"] or "未标注"),
            }
            for row in linked_candidates
        ]
        layer_counts = {
            layer: len(layers.get(layer, [])) if isinstance(layers.get(layer), list) else 0
            for layer in CHAIN_LAYER_META
        }
        for index, target in enumerate(missing, start=1):
            if not isinstance(target, dict):
                continue
            result.append(
                {
                    "gap_id": f"{event_id}#{index}",
                    "event_id": event_id,
                    "event_name": str(item.get("event_name") or event_id),
                    "event_tags": item.get("event_tags") or [],
                    "research_question": str(comparison.get("research_question") or ""),
                    "primary_evidence_label": str(item.get("primary_evidence_label") or "一手证据状态未标注"),
                    "primary_evidence_gap": str(item.get("primary_evidence_gap") or ""),
                    "target": str(target.get("target") or target.get("label") or "未命名开放目标"),
                    "why_it_matters": str(target.get("why_it_matters") or ""),
                    "next_action": str(target.get("next_action") or ""),
                    "status": str(target.get("status") or "open"),
                    "candidate_count": len(candidate_cards),
                    "candidates": candidate_cards[:6],
                    "candidate_overflow": max(0, len(candidate_cards) - 6),
                    "layer_counts": layer_counts,
                }
            )
    return result


def research_gaps_page() -> bytes:
    """国内一手证据的开放目标看板；只展示可执行的元数据缺口。"""
    gaps = _research_gap_rows()
    event_ids = list(dict.fromkeys(str(row["event_id"]) for row in gaps))
    open_count = sum(row["status"] == "open" for row in gaps)
    candidate_count = sum(int(row["candidate_count"]) for row in gaps)
    grouped: dict[str, list[dict[str, object]]] = {}
    for gap in gaps:
        grouped.setdefault(str(gap["event_id"]), []).append(gap)

    topic_sections: list[str] = []
    for event_id in event_ids:
        event_gaps = grouped[event_id]
        first = event_gaps[0]
        target_cards: list[str] = []
        for gap in event_gaps:
            candidates = gap.get("candidates") or []
            candidate_links = " · ".join(
                f'<a href="/domestic/candidate/{quote(str(candidate["candidate_id"]), safe="")}">{h(candidate["title"])}</a>'
                f' <span class="meta">{h(candidate["level"])} / {h(candidate["review_status"])}</span>'
                for candidate in candidates
            )
            if int(gap["candidate_overflow"]):
                candidate_links += f' · <span class="meta">另有 {h(gap["candidate_overflow"])} 条候选记录</span>'
            if not candidate_links:
                candidate_links = '<span class="meta">当前没有可见候选记录，需从来源目录重新定位。</span>'
            layers = gap["layer_counts"]
            target_cards.append(
                f"""
<article class="result compact-result evidence-gap-item">
  <div>
    <h3>{h(gap["target"])}</h3>
    <div class="tagline"><span class="pstatus warn">{h(gap["status"])}</span><span class="tag">主证据 {h(layers["primary"])} 条</span><span class="tag">同期交叉 {h(layers["cross_source"])} 条</span><span class="tag">候选关联 {h(gap["candidate_count"])} 条</span></div>
    <div class="snippet"><strong>为什么重要：</strong>{h(gap["why_it_matters"] or "证据链未登记原因，需先补充审计说明。")}</div>
    <div class="snippet"><strong>下一步：</strong>{h(gap["next_action"] or "证据链未登记下一步，暂不进入收口。")}</div>
    <div class="snippet"><strong>相关候选：</strong>{candidate_links}</div>
  </div>
  <div class="cite"><a href="/research/{quote(str(gap["event_id"]))}">专题详情</a><br><a href="/domestic/acquisition">调档清单</a></div>
</article>"""
            )
        topic_sections.append(
            f"""
<div class="section-head"><h2><a href="/research/{quote(event_id)}">{h(first["event_name"])}</a></h2><span class="meta">{h(first["primary_evidence_label"])} · {len(event_gaps)} 个开放目标</span></div>
<div class="notice"><strong>研究问题：</strong>{h(first["research_question"] or "尚未登记研究问题。")}<br><strong>专题边界：</strong>{h(first["primary_evidence_gap"] or "尚未登记一手闭环边界。")}</div>
<section class="result-list">{"".join(target_cards)}</section>"""
        )

    body = breadcrumb_html([("/", "首页"), ("/research", "多源专题研究"), (None, "一手证据收口看板")]) + f"""
<section class="hero hero-compact">
  <div class="hero-eyebrow">DOMESTIC PRIMARY EVIDENCE CLOSEOUT</div>
  <h1>国内一手证据收口看板</h1>
  <p class="hero-sub">把九个专题的开放主证据目标变成可执行的追索清单。这里显示的是证据链明确登记的缺口，不是“没有资料”的断言；候选记录、报刊报道和汇编页都不会自动替代待补原件。</p>
  <div class="hero-chips"><span><b>{h(len(event_ids))}</b> 个专题</span><span><b>{h(open_count)}</b> 个开放目标</span><span><b>{h(candidate_count)}</b> 条候选关联</span><span><b>0</b> 项自动升级</span></div>
</section>
<div class="notice"><strong>执行规则：</strong>先按“下一步”取得或定位原件，再记录馆藏档号/卷期、版本关系、页级 provenance、源文件 SHA256 和人工复核结果；完成前保持开放状态。正式引用请回到专题详情和 <a href="/domestic/review">国内复核看板</a>，不要把本页当成原件正文。</div>
{"".join(topic_sections) or '<div class="notice">当前没有从证据链读取到开放目标；请先运行证据链校验器。</div>'}
<section class="doc-tools" style="margin-top:20px;justify-content:center;">
  <a class="button" href="/research">返回专题索引</a>
  <a class="button" href="/domestic/acquisition">完整调档清单</a>
  <a class="button" href="/domestic/review">国内复核看板</a>
</section>
"""
    return layout("国内一手证据收口看板", body, active_path="/research")


def _load_academic_source_policy() -> dict[str, object]:
    """读取学术层口径；缺文件时返回安全的空策略。"""
    if not ACADEMIC_SOURCE_POLICY_PATH.is_file():
        return {}
    try:
        payload = json.loads(ACADEMIC_SOURCE_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _academic_layer_snapshot() -> dict[str, object]:
    """读取 staging 学术资料的元数据统计，不读取正文、不写数据库。"""
    snapshot: dict[str, object] = {
        "available": False,
        "records": 0,
        "academic_records": 0,
        "high_priority": 0,
        "articles": 0,
        "citation_ready": 0,
        "human_verified": 0,
        "tiers": {},
        "fulltext_statuses": {},
        "institutions": [],
    }
    if not DOMESTIC_STAGING_DB_PATH.exists():
        # 清洁 checkout 可能只有正式 SQLite，没有本地 staging。此时仍显示
        # 已正式建索引的学术全文，并明确标注为 formal-index fallback。
        try:
            with conn() as c:
                rows = c.execute(
                    """SELECT title, matched_terms
                       FROM documents
                       WHERE source_platform='domestic'
                         AND hit_type='domestic_academic_fulltext'"""
                ).fetchall()
        except sqlite3.Error:
            return snapshot
        tiers: dict[str, int] = {}
        for row in rows:
            tier_match = re.search(r"quality_tier=([^,]+)", str(row["matched_terms"] or ""))
            tier = tier_match.group(1) if tier_match else "未分级"
            tiers[tier] = tiers.get(tier, 0) + 1
        snapshot.update(
            {
                "available": bool(rows),
                "records": len(rows),
                "academic_records": len(rows),
                "high_priority": sum(value for key, value in tiers.items() if key in {"S", "A"}),
                "articles": sum("research_type=SCHOLARLY_ARTICLE" in str(row["matched_terms"] or "") for row in rows),
                "citation_ready": 0,
                "human_verified": 0,
                "tiers": dict(sorted(tiers.items())),
                "fulltext_statuses": {"FORMAL_INDEX_REVIEW_ONLY": len(rows)} if rows else {},
                "institutions": [],
                "fallback": "formal_index",
            }
        )
        return snapshot
    try:
        c = sqlite3.connect(DOMESTIC_STAGING_DB_PATH)
        c.row_factory = sqlite3.Row
        exists = c.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domestic_research_materials'"
        ).fetchone()
        if not exists:
            c.close()
            return snapshot
        rows = c.execute(
            """SELECT layer, quality_tier, research_type, fulltext_status,
                      citation_ready, human_verified, institution
               FROM domestic_research_materials"""
        ).fetchall()
        c.close()
    except sqlite3.Error:
        return snapshot
    tiers: dict[str, int] = {}
    fulltext_statuses: dict[str, int] = {}
    institutions: dict[str, int] = {}
    for row in rows:
        tier = str(row["quality_tier"] or "未分级")
        tiers[tier] = tiers.get(tier, 0) + 1
        status = str(row["fulltext_status"] or "未标注")
        fulltext_statuses[status] = fulltext_statuses.get(status, 0) + 1
        institution = str(row["institution"] or "机构未标注").strip()
        institutions[institution] = institutions.get(institution, 0) + 1
    academic_records = [row for row in rows if row["layer"] == "SCHOLARLY_RESEARCH"]
    snapshot.update(
        {
            "available": True,
            "records": len(rows),
            "academic_records": len(academic_records),
            "high_priority": sum(1 for row in academic_records if row["quality_tier"] in {"S", "A"}),
            "articles": sum(1 for row in academic_records if row["research_type"] == "SCHOLARLY_ARTICLE"),
            "citation_ready": sum(int(row["citation_ready"] or 0) for row in rows),
            "human_verified": sum(int(row["human_verified"] or 0) for row in rows),
            "tiers": dict(sorted(tiers.items())),
            "fulltext_statuses": dict(sorted(fulltext_statuses.items(), key=lambda pair: (-pair[1], pair[0]))),
            "institutions": [
                {"name": name, "count": count}
                for name, count in sorted(institutions.items(), key=lambda pair: (-pair[1], pair[0]))[:12]
            ],
        }
    )
    return snapshot


def _research_foreign_definition(slug: str) -> dict[str, object] | None:
    """把境外事件入口解析成标签和检索词，供专题页做机器命中统计。"""
    event = event_by_slug(slug)
    if event:
        return {
            "slug": slug,
            "name": event.get("name", slug),
            "terms": event.get("search_terms", []),
            "entry": f"/events/key/{quote(slug)}",
        }
    topic = topic_by_slug(slug)
    if topic and topic.get("source") != "domestic":
        return {
            "slug": slug,
            "name": topic.get("name", slug),
            "terms": topic.get("terms", []),
            "entry": f"/events?topic={quote(slug)}",
        }
    return None


def _research_foreign_match_stats(c: sqlite3.Connection, definition: dict[str, object]) -> dict[str, object]:
    """统计境外机器检索命中；不把它呈现为事件事实或人工确认。"""
    terms = [str(term).strip() for term in definition.get("terms", []) if str(term).strip()]
    if not terms:
        return {"documents": 0, "pages": 0, "platforms": {}}
    clauses: list[str] = []
    params: list[str] = []
    for term in terms:
        like = f"%{term}%"
        for column in ("d.title", "d.matched_terms", "p.text", "t.text"):
            clauses.append(f"{column} LIKE ?")
            params.append(like)
    try:
        row = c.execute(
            f"""
            SELECT count(DISTINCT d.id) AS documents, count(DISTINCT p.id) AS pages
            FROM pages p
            JOIN documents d ON d.id = p.document_id
            LEFT JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
            LEFT JOIN document_classifications dc ON dc.document_id = d.id
            WHERE ({' OR '.join(clauses)})
              AND COALESCE(d.source_platform, 'frus') <> 'domestic'
              AND (dc.grade IS NULL OR dc.grade != '前台不展示')
            """,
            tuple(params),
        ).fetchone()
        platforms = c.execute(
            f"""
            SELECT COALESCE(d.source_platform, 'frus') AS platform, count(DISTINCT p.id) AS pages
            FROM pages p
            JOIN documents d ON d.id = p.document_id
            LEFT JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
            LEFT JOIN document_classifications dc ON dc.document_id = d.id
            WHERE ({' OR '.join(clauses)})
              AND COALESCE(d.source_platform, 'frus') <> 'domestic'
              AND (dc.grade IS NULL OR dc.grade != '前台不展示')
            GROUP BY platform ORDER BY pages DESC
            """,
            tuple(params),
        ).fetchall()
    except sqlite3.OperationalError:
        return {"documents": 0, "pages": 0, "platforms": {}}
    return {
        "documents": int(row["documents"] or 0),
        "pages": int(row["pages"] or 0),
        "platforms": {str(item["platform"]): int(item["pages"] or 0) for item in platforms},
    }


def _research_foreign_match_rows(
    c: sqlite3.Connection, definition: dict[str, object], limit: int = 12
) -> list[sqlite3.Row]:
    """返回专题页的境外机器命中样本，供研究者回到原文核验。"""
    terms = [str(term).strip() for term in definition.get("terms", []) if str(term).strip()]
    if not terms:
        return []
    clauses: list[str] = []
    params: list[str | int] = []
    for term in terms:
        like = f"%{term}%"
        for column in ("d.title", "d.matched_terms", "p.text", "t.text"):
            clauses.append(f"{column} LIKE ?")
            params.append(like)
    params.append(limit)
    try:
        return c.execute(
            f"""
            SELECT p.id AS page_id, p.page_label, p.page_url, d.doc_key, d.title,
                   d.date_guess, COALESCE(d.source_platform, 'frus') AS platform,
                   COALESCE(dc.grade, '') AS grade
            FROM pages p
            JOIN documents d ON d.id = p.document_id
            LEFT JOIN translations t ON t.page_id = p.id AND t.language='zh-CN'
            LEFT JOIN document_classifications dc ON dc.document_id = d.id
            WHERE ({' OR '.join(clauses)})
              AND COALESCE(d.source_platform, 'frus') <> 'domestic'
              AND (dc.grade IS NULL OR dc.grade != '前台不展示')
            GROUP BY p.id
            ORDER BY d.date_guess, d.doc_key, p.id
            LIMIT ?
            """,
            tuple(params),
        ).fetchall()
    except sqlite3.OperationalError:
        return []


def _research_domestic_evidence_rows(
    c: sqlite3.Connection, candidates: list[sqlite3.Row], limit: int = 40
) -> list[dict[str, object]]:
    """把专题候选回接到已入库国内文档和物理页。

    候选表是编辑层，documents/pages/page_provenance 才是阅读与证据层。
    这里仅做可重算的导航聚合，不把 accepted 候选或 OCR 自动升级为正式引用。
    """
    by_document: dict[int, list[sqlite3.Row]] = {}
    for candidate in candidates:
        raw_document_id = candidate["ingested_document_id"]
        if raw_document_id is None:
            continue
        try:
            document_id = int(raw_document_id)
        except (TypeError, ValueError):
            continue
        by_document.setdefault(document_id, []).append(candidate)
    if not by_document:
        return []

    placeholders = ",".join("?" for _ in by_document)
    try:
        rows = c.execute(
            f"""
            SELECT d.id AS document_id, d.doc_key, d.title, d.date_guess, d.url, d.hit_type,
                   COUNT(DISTINCT p.id) AS page_count,
                   SUM(length(COALESCE(p.text, ''))) AS text_chars,
                   COUNT(DISTINCT CASE WHEN pp.page_id IS NOT NULL THEN p.id END) AS provenance_pages,
                   COUNT(DISTINCT CASE
                       WHEN trim(COALESCE(pp.source_file, '')) <> ''
                        AND length(trim(COALESCE(pp.source_sha256, ''))) = 64
                       THEN p.id END) AS file_backed_pages,
                   COUNT(DISTINCT CASE WHEN {DOMESTIC_STRICT_CITATION_SQL} THEN p.id END) AS strict_citation_pages,
                   COUNT(DISTINCT CASE WHEN {DOMESTIC_MACHINE_READABLE_SQL} THEN p.id END) AS machine_readable_pages,
                   (SELECT p0.id FROM pages p0 WHERE p0.document_id=d.id ORDER BY p0.id LIMIT 1) AS first_page_id,
                   (SELECT p0.page_label FROM pages p0 WHERE p0.document_id=d.id ORDER BY p0.id LIMIT 1) AS first_page_label
            FROM documents d
            LEFT JOIN pages p ON p.document_id=d.id
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE d.source_platform='domestic' AND d.id IN ({placeholders})
            GROUP BY d.id
            ORDER BY strict_citation_pages DESC, machine_readable_pages DESC,
                     file_backed_pages DESC, d.date_guess, d.id
            LIMIT ?
            """,
            tuple(by_document) + (limit,),
        ).fetchall()
    except sqlite3.OperationalError:
        return []

    result: list[dict[str, object]] = []
    for row in rows:
        document_id = int(row["document_id"])
        linked = by_document.get(document_id, [])
        result.append({
            "document_id": document_id,
            "doc_key": row["doc_key"],
            "title": row["title"],
            "date_guess": row["date_guess"],
            "url": row["url"],
            "hit_type": row["hit_type"],
            "page_count": int(row["page_count"] or 0),
            "text_chars": int(row["text_chars"] or 0),
            "provenance_pages": int(row["provenance_pages"] or 0),
            "file_backed_pages": int(row["file_backed_pages"] or 0),
            "strict_citation_pages": int(row["strict_citation_pages"] or 0),
            "machine_readable_pages": int(row["machine_readable_pages"] or 0),
            "first_page_id": row["first_page_id"],
            "first_page_label": row["first_page_label"],
            "candidate_ids": [str(item["candidate_id"]) for item in linked],
            "candidate_titles": [str(item["title"] or "") for item in linked],
            "candidate_levels": sorted({
                _domestic_level(item) for item in linked if _domestic_level(item)
            }),
        })
    return result


def _research_topic_event_page_stats(
    c: sqlite3.Connection, event_id: str
) -> dict[str, int]:
    """Count pages linked by the shared topic event index.

    This is deliberately separate from candidate aggregation. A curated
    evidence-chain page may be linked to ``research_events`` without its
    document being listed in ``domestic_candidates``. Collapsing those paths
    would make a strict page look absent from the research platform.
    """
    try:
        row = c.execute(
            f"""
            SELECT
                COUNT(DISTINCT CASE WHEN d.source_platform='domestic' THEN e.page_id END) AS domestic_pages,
                COUNT(DISTINCT CASE
                    WHEN d.source_platform='domestic'
                     AND {DOMESTIC_STRICT_CITATION_SQL}
                    THEN e.page_id END) AS domestic_strict_pages,
                COUNT(DISTINCT CASE
                    WHEN d.source_platform='domestic'
                     AND trim(COALESCE(pp.source_file, '')) <> ''
                     AND length(trim(COALESCE(pp.source_sha256, ''))) = 64
                    THEN e.page_id END) AS domestic_file_backed_pages
            FROM research_events e
            JOIN pages p ON p.id=e.page_id
            JOIN documents d ON d.id=p.document_id
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE e.scope_type='topic' AND e.scope_slug=?
            """,
            (event_id,),
        ).fetchone()
    except sqlite3.OperationalError:
        return {
            "domestic_pages": 0,
            "domestic_strict_pages": 0,
            "domestic_file_backed_pages": 0,
        }
    return {
        "domestic_pages": int(row["domestic_pages"] or 0),
        "domestic_strict_pages": int(row["domestic_strict_pages"] or 0),
        "domestic_file_backed_pages": int(row["domestic_file_backed_pages"] or 0),
    }


def _research_academic_matches(
    item: dict[str, object], comparison: dict[str, object], limit: int = 10
) -> dict[str, object]:
    """把 staging 学术元数据按专题词做候选匹配，不读取正文、不升级引用。"""
    result: dict[str, object] = {"rows": [], "total": 0}
    terms = [
        str(term).strip()
        for term in (
            list(comparison.get("academic_terms", []))
            + list(item.get("event_tags", []))
        )
        if str(term).strip()
    ]
    if not terms:
        return result
    if DOMESTIC_STAGING_DB_PATH.exists():
        try:
            c = sqlite3.connect(DOMESTIC_STAGING_DB_PATH)
            c.row_factory = sqlite3.Row
            exists = c.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name='domestic_research_materials'"
            ).fetchone()
            if not exists:
                c.close()
                return result
            source_rows = c.execute(
                """SELECT external_id, title, author, institution, publication_date,
                          research_type, quality_tier, source_url, fulltext_status,
                          review_status, citation_ready, human_verified, metadata_json
                   FROM domestic_research_materials
                   WHERE layer='SCHOLARLY_RESEARCH'"""
            ).fetchall()
            c.close()
        except sqlite3.Error:
            return result
    else:
        # 没有 staging 时，从正式 SQLite 的学术全文层回退；这只使用题名和
        # 已写入的机器标签，仍不读取正文语义，也不改变引用门禁。
        try:
            with conn() as c:
                source_rows = c.execute(
                    """SELECT d.doc_id AS external_id, d.title,
                              '' AS author, '' AS institution, d.date_guess AS publication_date,
                              CASE WHEN d.matched_terms LIKE '%research_type=SCHOLARLY_ARTICLE%' THEN 'SCHOLARLY_ARTICLE' ELSE 'SCHOLARLY_RESEARCH' END AS research_type,
                              CASE WHEN d.matched_terms LIKE '%quality_tier=S%' THEN 'S'
                                   WHEN d.matched_terms LIKE '%quality_tier=A%' THEN 'A' ELSE '未分级' END AS quality_tier,
                              d.url AS source_url, 'FORMAL_INDEX_REVIEW_ONLY' AS fulltext_status,
                              'review_only' AS review_status, 0 AS citation_ready,
                              0 AS human_verified, '' AS metadata_json, d.matched_terms
                       FROM documents d
                       WHERE d.source_platform='domestic'
                         AND d.hit_type='domestic_academic_fulltext'"""
                ).fetchall()
        except sqlite3.Error:
            return result

    matches: list[dict[str, object]] = []
    tier_score = {"S": 4, "A": 3, "B": 2, "C": 1}
    fulltext_score = {
        "FULLTEXT_PDF": 3,
        "FULLTEXT_HTML": 3,
        "ACQUIRED_PUBLIC_HTML": 2,
        "FULLTEXT_HTML_CANDIDATE": 1,
        "FULLTEXT_PDF_CANDIDATE": 1,
    }
    for source in source_rows:
        try:
            metadata = json.loads(str(source["metadata_json"] or "{}"))
        except (TypeError, json.JSONDecodeError):
            metadata = {}
        if not isinstance(metadata, dict):
            metadata = {}
        structured_values: list[str] = []
        for key in ("events", "historical_periods", "people", "places", "research_type"):
            value = metadata.get(key, [])
            if isinstance(value, list):
                structured_values.extend(str(part) for part in value)
            elif value:
                structured_values.append(str(value))
        source_tags = str(source["matched_terms"] or "") if "matched_terms" in source.keys() else ""
        structured = " ".join(structured_values) + " " + source_tags
        general = " ".join(
            str(source[key] or "")
            for key in ("title", "author", "institution", "publication_date", "research_type")
        )
        matched: list[str] = []
        score = 0
        for term in dict.fromkeys(terms):
            if term in str(source["title"] or ""):
                matched.append(term)
                score += 8
            elif term in structured:
                matched.append(term)
                score += 5
            elif term in general:
                matched.append(term)
                score += 2
        specific_match = any(not re.fullmatch(r"\d{4}", term) for term in matched)
        if not matched or not specific_match:
            continue
        quality = str(source["quality_tier"] or "C")
        fulltext_status = str(source["fulltext_status"] or "")
        score += tier_score.get(quality, 0) + fulltext_score.get(fulltext_status, 0)
        matches.append(
            {
                "external_id": source["external_id"],
                "title": source["title"],
                "author": source["author"],
                "institution": source["institution"],
                "publication_date": source["publication_date"],
                "research_type": source["research_type"],
                "quality_tier": quality,
                "source_url": source["source_url"],
                "fulltext_status": fulltext_status,
                "review_status": source["review_status"],
                "citation_ready": int(source["citation_ready"] or 0),
                "human_verified": int(source["human_verified"] or 0),
                "matched_terms": matched[:6],
                "match_score": score,
            }
        )
    matches.sort(
        key=lambda row: (
            -int(row["match_score"]),
            -tier_score.get(str(row["quality_tier"]), 0),
            str(row["publication_date"] or "9999"),
            str(row["external_id"]),
        )
    )
    result["total"] = len(matches)
    result["rows"] = matches[:limit]
    return result


def _research_topic_rows() -> list[dict[str, object]]:
    """为统一专题首页生成国内候选数、境外机器命中数和入口信息。"""
    coverage = _load_domestic_event_coverage()
    comparison_cards = _load_topic_comparison_cards()
    evidence_chains = _load_topic_evidence_chains()
    try:
        domestic_rows = _domestic_rows()
    except sqlite3.OperationalError:
        domestic_rows = []
    domestic_by_id = {str(row["candidate_id"]): row for row in domestic_rows}
    result: list[dict[str, object]] = []
    with conn() as c:
        for item in coverage:
            candidate_ids = [str(value) for value in item.get("domestic_candidate_ids", [])]
            linked = [domestic_by_id[value] for value in candidate_ids if value in domestic_by_id]
            domestic_evidence = _research_domestic_evidence_rows(c, linked)
            comparison = comparison_cards.get(str(item.get("event_id")), {})
            academic_matches = _research_academic_matches(item, comparison)
            foreign_defs = [
                definition
                for slug in item.get("foreign_event_slugs", [])
                if (definition := _research_foreign_definition(str(slug))) is not None
            ]
            foreign_stats = [
                {"definition": definition, "stats": _research_foreign_match_stats(c, definition)}
                for definition in foreign_defs
            ]
            topic_event_stats = _research_topic_event_page_stats(
                c, str(item.get("event_id") or "")
            )
            result.append({
                "item": item,
                "comparison": comparison,
                "evidence_chain": evidence_chains.get(str(item.get("event_id")), {}),
                "evidence_chain_summary": _topic_evidence_chain_summary(
                    evidence_chains.get(str(item.get("event_id")), {})
                ),
                "academic_rows": academic_matches["rows"],
                "academic_total": academic_matches["total"],
                "domestic_rows": linked,
                "domestic_evidence": domestic_evidence,
                "domestic_documents": len(domestic_evidence),
                "domestic_pages": sum(int(row["page_count"]) for row in domestic_evidence),
                "domestic_file_pages": sum(int(row["file_backed_pages"]) for row in domestic_evidence),
                "domestic_citation_pages": sum(int(row["strict_citation_pages"]) for row in domestic_evidence),
                "topic_event_domestic_pages": topic_event_stats["domestic_pages"],
                "topic_event_domestic_file_backed_pages": topic_event_stats["domestic_file_backed_pages"],
                "topic_event_domestic_strict_pages": topic_event_stats["domestic_strict_pages"],
                "foreign_stats": foreign_stats,
                "foreign_pages": sum(int(entry["stats"]["pages"]) for entry in foreign_stats),
                "foreign_documents": sum(int(entry["stats"]["documents"]) for entry in foreign_stats),
            })
    return result


def research_topics_page() -> bytes:
    """国内外共享的专题研究入口。"""
    topics = _research_topic_rows()
    total_domestic = sum(len(topic["domestic_rows"]) for topic in topics)
    total_domestic_documents = sum(int(topic["domestic_documents"]) for topic in topics)
    total_domestic_pages = sum(int(topic["domestic_pages"]) for topic in topics)
    total_foreign = sum(int(topic["foreign_pages"]) for topic in topics)
    total_academic = sum(int(topic.get("academic_total", 0)) for topic in topics)
    total_chain_pages = sum(
        int((topic.get("evidence_chain_summary") or {}).get("page_items", 0))
        for topic in topics
    )
    total_chain_targets = sum(
        int((topic.get("evidence_chain_summary") or {}).get("open_targets", 0))
        for topic in topics
    )
    body = breadcrumb_html([("/", "首页"), (None, "多源专题研究")]) + f"""
<section class="hero hero-compact">
  <div class="hero-eyebrow">UNIFIED RESEARCH TOPICS</div>
  <h1>多源专题研究</h1>
  <p class="hero-sub">把国内候选、境外档案和证据缺口放进同一条研究路径。这里的关联是检索与编排层，正式引用仍必须回到原件、页码、哈希和人工复核。</p>
  <div class="hero-chips"><span><b>{len(topics)}</b> 个专题</span><span><b>{total_domestic}</b> 条国内候选关联</span><span><b>{total_domestic_documents}</b> 篇国内已入库文档</span><span><b>{total_domestic_pages}</b> 个国内物理页</span><span><b>{total_foreign}</b> 个境外机器命中页</span><span><b>{total_academic}</b> 条学术解释候选</span><span><b>{total_chain_pages}</b> 个页级证据链条目</span><span><b>{total_chain_targets}</b> 个待补原件目标</span></div>
</section>
<div class="notice"><strong>阅读纪律：</strong>“国内候选”来自事件覆盖表，“境外机器命中”来自关键词检索；二者都不是自动事实确认。页面将“研究导航可用”和“一手证据闭环”分开显示：当前有入口不等于关键原件已经取得。每个专题还显示可重算的四层证据链摘要；打开专题后，可以分别回到国内候选记录、境外原文页、页级证据和待补原件说明。</div>
<section class="result-list">
"""
    for topic in topics:
        item = topic["item"]
        comparison = topic.get("comparison") or {}
        status = str(item.get("pair_status") or "待核")
        status_cls = "ok" if status == "pair_available" else "warn"
        primary = _primary_evidence_display(item)
        chain_summary = topic.get("evidence_chain_summary") or {}
        body += f"""
<article class="result">
  <div>
    <h2><a href="/research/{quote(str(item['event_id']))}">{h(item.get('event_name'))}</a></h2>
    <div class="meta">国内候选 {len(topic['domestic_rows'])} 条 · 已入库 {h(topic['domestic_documents'])} 篇 / {h(topic['domestic_pages'])} 页 · 境外机器命中 {h(topic['foreign_pages'])} 页 / {h(topic['foreign_documents'])} 篇 · 学术解释候选 {h(topic.get('academic_total', 0))} 条 · 证据链 {h(chain_summary.get('layer_count', 0))}/4 层 · 页级 {h(chain_summary.get('page_items', 0))} 条 · 待补原件 {h(chain_summary.get('open_targets', 0))} 项 · {h(item.get('domestic_status'))}</div>
    <div class="tagline"><span class="pstatus {status_cls}">{h(status)}</span><span class="pstatus {primary['class']}">{h(primary['label'])}</span>{''.join(f'<span class="tag">{h(tag)}</span>' for tag in item.get('event_tags', []))}</div>
    <div class="snippet">{h(item.get('review_note'))}</div>
    <div class="snippet"><strong>一手闭环缺口：</strong>{h(primary['gap'])}</div>
    <div class="snippet"><strong>对读差异：</strong>{h(comparison.get('difference') or '尚未配置差异卡，暂只显示两侧检索入口。')}</div>
  </div>
  <div class="cite"><a href="/research/{quote(str(item['event_id']))}">打开专题</a><br><a href="/research/{quote(str(item['event_id']))}/packet">研究包</a><br><a href="/domestic/events?event={quote(str(item['event_id']))}">国内覆盖</a></div>
</article>"""
    body += "</section>"
    body += """
<section class="doc-tools" style="margin-top:20px;justify-content:center;">
  <a class="button" href="/align">多源对位视图</a>
  <a class="button" href="/research/gaps">一手证据收口看板</a>
  <a class="button" href="/domestic">国内史料库</a>
  <a class="button" href="/domestic/academic">学术研究层</a>
  <a class="button" href="/events/key">境外关键事件</a>
  <a class="button" href="/research/packets">全部研究包</a>
</section>
"""
    return layout("多源专题研究", body, active_path="/research")


def research_packets_page() -> bytes:
    """Index all topic packets and their current evidence state."""
    topics = _research_topic_rows()
    cards: list[str] = []
    for topic in topics:
        item = topic["item"]
        event_id = str(item.get("event_id") or "")
        chain = topic.get("evidence_chain_summary") or {}
        primary = _primary_evidence_display(item)
        status_class = "ok" if primary["status"] == "closed" else "warn"
        cards.append(f"""
<article class="result"><div>
  <h2><a href="/research/{quote(event_id)}/packet">{h(item.get('event_name'))}</a></h2>
  <div class="meta">证据链 {h(chain.get('page_items', 0))} 页 · 严格门禁 {h(chain.get('strict_items', 0))} 页 · 专题回接 {h(topic.get('topic_event_domestic_pages', 0))} 页 / 严格 {h(topic.get('topic_event_domestic_strict_pages', 0))} 页 · 开放原件目标 {h(chain.get('open_targets', 0))} 项 · 学术候选 {h(topic.get('academic_total', 0))} 条</div>
  <div class="tagline"><span class="pstatus {status_class}">{h(primary['label'])}</span><span class="tag">研究包可生成</span><span class="tag">正文不复制</span></div>
  <div class="snippet"><strong>当前缺口：</strong>{h(primary['gap'])}</div>
</div><div class="cite"><a href="/research/{quote(event_id)}/packet">打开研究包</a><br><a href="/research/{quote(event_id)}/packet.json">下载 JSON</a></div></article>""")
    body = breadcrumb_html([("/", "首页"), ("/research", "多源专题研究"), (None, "全部研究包")]) + f"""
<section class="doc-head"><div><h1>全部专题研究包</h1><div class="meta">九个国内专题的统一研究工作台</div></div><div class="doc-tools"><a class="button" href="/research">专题索引</a><a class="button secondary" href="/research/gaps">证据缺口</a></div></section>
<div class="notice"><strong>使用方式：</strong>先从研究问题进入专题，再用研究包统一查看国内材料、境外对读、学术解释、页级 provenance 和待补原件。这里把“证据链页”“专题回接页”和“候选回接严格页”分开统计：三者来源路径不同，不能互相替代。研究包只复制元数据和链接，不复制正文、OCR、译文或逐字引文。</div>
<section class="result-list">{"".join(cards) or '<div class="notice">暂无专题研究包。</div>'}</section>
"""
    return layout("全部专题研究包", body, active_path="/research")


def research_topic_page(event_id: str) -> bytes:
    """单个专题的国内候选 / 境外命中 / 缺口对读页。"""
    topic = next((item for item in _research_topic_rows() if str(item["item"].get("event_id")) == event_id), None)
    if not topic:
        return layout("专题未找到", '<div class="notice">没有找到该专题，返回 <a href="/research">多源专题研究</a>。</div>', active_path="/research")
    item = topic["item"]
    comparison = topic.get("comparison") or {}
    primary = _primary_evidence_display(item)
    evidence_chain = topic.get("evidence_chain") or {}
    foreign_samples: list[dict[str, object]] = []
    with conn() as c:
        for entry in topic["foreign_stats"]:
            definition = entry["definition"]
            foreign_samples.append({
                "definition": definition,
                "stats": entry["stats"],
                "rows": _research_foreign_match_rows(c, definition),
            })

    domestic_cards = []
    for row in topic["domestic_rows"][:24]:
        query = quote(str(row["title"] or row["candidate_id"]))
        domestic_cards.append(f"""
<article class="result compact-result"><div>
  <h3><a href="/domestic?q={query}">{h(row['title'])}</a></h3>
  <div class="meta">{h(row['creator'])} · {h(row['document_date'])} · {h(row['document_type'])}</div>
  <div class="tagline"><span class="tag">拟议 {h(row['authenticity_level_proposed'])}</span><span class="tag">{h(row['review_status'])}</span></div>
  <div class="snippet">{h(row['evidence_note'] or row['uncertainty_note'])}</div>
</div><div class="cite"><a href="/domestic?q={query}">候选记录</a></div></article>""")
    domestic_html = "".join(domestic_cards) or '<div class="notice">该专题当前没有可见的国内候选记录。</div>'

    academic_cards = []
    for academic in topic.get("academic_rows", []):
        source_url = source_href(academic.get("source_url") or "#")
        search_href = f"/domestic/search?scope=research&amp;q={quote(str(academic.get('title') or academic.get('external_id') or ''))}"
        tier = str(academic.get("quality_tier") or "未分级")
        tier_class = "ok" if tier in {"S", "A"} else "warn"
        academic_cards.append(f"""
<article class="result compact-result"><div>
  <h3>{h(academic.get('title') or academic.get('external_id'))}</h3>
  <div class="meta">{h(academic.get('author') or '作者未标注')} · {h(academic.get('institution') or '机构未标注')} · {h(academic.get('publication_date') or '日期未标注')}</div>
  <div class="tagline"><span class="pstatus {tier_class}">学术 {h(tier)}</span><span class="tag">{h(academic.get('research_type') or '研究资料')}</span><span class="tag">命中：{h('、'.join(academic.get('matched_terms') or []))}</span></div>
  <div class="snippet">全文状态：{h(academic.get('fulltext_status') or '未标注')} · citation_ready={h(academic.get('citation_ready'))} · 该条目只作为解释层候选，不自动替代国内一手页级证据。</div>
</div><div class="cite"><a href="{search_href}">研究资料</a> · <a href="/domestic/events?event={quote(str(item.get('event_id')))}">一手对照</a>{f' · <a href="{h(source_url)}" target="_blank" rel="noreferrer">来源入口</a>' if source_url != '#' else ''}</div></article>""")
    academic_total = int(topic.get("academic_total", 0))
    academic_html = "".join(academic_cards) or f'<div class="notice">当前 staging 没有匹配到该专题的学术元数据；这不代表学术资料不存在，只表示本地 staging 尚未提供可重算匹配。请先回到 <a href="/domestic/events?event={quote(str(item.get("event_id")))}">一手对照</a>。</div>'
    if academic_total > len(academic_cards):
        academic_html += f'<div class="notice">当前显示前 {len(academic_cards)} 条，共匹配 {academic_total} 条；请进入研究资料检索继续筛选。</div>'

    domestic_evidence_cards = []
    for evidence in topic["domestic_evidence"]:
        doc_key = str(evidence["doc_key"] or "")
        first_page_id = evidence["first_page_id"]
        href = f"/doc/{quote(doc_key)}"
        if first_page_id:
            href += f"?page_id={quote(str(first_page_id))}"
        strict = int(evidence["strict_citation_pages"])
        machine = int(evidence["machine_readable_pages"])
        file_backed = int(evidence["file_backed_pages"])
        pages = int(evidence["page_count"])
        if strict:
            status_label = f"正式可引用 {strict} 页"
            status_class = "ok"
        elif machine:
            status_label = f"机器核验可阅 {machine} 页"
            status_class = "warn"
        else:
            status_label = "OCR/原文待人工复核"
            status_class = "warn"
        candidate_label = "；".join(evidence["candidate_titles"][:2])
        if len(evidence["candidate_titles"]) > 2:
            candidate_label += f" 等 {len(evidence['candidate_titles'])} 条候选"
        page_tools = (
            f'<br><a href="/review/{h(first_page_id)}">校订</a>'
            f'<br><a href="/cite/{h(first_page_id)}">引用门禁</a>'
            f'<br><a href="/domestic/evidence-review/{h(first_page_id)}">证据复核</a>'
            if first_page_id else ""
        )
        domestic_evidence_cards.append(f"""
<article class="result compact-result"><div>
  <h3><a href="{href}">{h(evidence['title'] or doc_key or '未题名国内文档')}</a></h3>
  <div class="meta">{h(evidence['date_guess'] or '日期未注明')} · {h(evidence['hit_type'] or 'domestic')} · {h(pages)} 页 · {h(evidence['text_chars'])} 字</div>
  <div class="tagline"><span class="pstatus {status_class}">{h(status_label)}</span><span class="tag">源文件锚定 {h(file_backed)}/{h(pages)} 页</span><span class="tag">provenance {h(evidence['provenance_pages'])}/{h(pages)}</span></div>
  <div class="snippet">候选关联：{h(candidate_label or '未标注候选')}。机器可阅与源文件锚定不等于人工确认。</div>
</div><div class="cite"><a href="{href}">打开原文页</a>{page_tools}</div></article>""")
    domestic_evidence_html = "".join(domestic_evidence_cards) or '<div class="notice">该专题当前没有已回接到文档页的国内证据样本；候选记录仍可用于调档和追踪。</div>'

    foreign_sections = []
    for sample in foreign_samples:
        definition = sample["definition"]
        stats = sample["stats"]
        rows = sample["rows"]
        platform_html = "".join(
            f'<span class="tag">{h(PLATFORM_META.get(platform, {}).get("name", platform))} {h(count)} 页</span>'
            for platform, count in stats["platforms"].items()
        ) or '<span class="tag">暂无机器命中</span>'
        cards = []
        for row in rows:
            href = f"/doc/{quote(str(row['doc_key']))}?page_id={row['page_id']}"
            cards.append(f"""
<article class="result compact-result"><div>
  <h3><a href="{href}">{h(row['title'])}</a></h3>
  <div class="meta">{h(row['platform'])} · {h(row['date_guess'])} · {h(row['page_label'] or '页码未标注')}</div>
  <div class="tagline"><span class="tag">机器命中</span> {grade_badge(row)}</div>
</div><div class="cite"><a href="{href}">查看原文</a></div></article>""")
        foreign_sections.append(f"""
<div class="section-head"><h2>{h(definition['name'])}</h2><a class="more" href="{h(definition['entry'])}">进入境外入口 →</a></div>
<div class="tagline" style="margin-bottom:10px;"><span class="tag">{h(stats['documents'])} 篇文档</span><span class="tag">{h(stats['pages'])} 页</span>{platform_html}</div>
<section class="result-list">{''.join(cards) or '<div class="notice">没有展示样本；请从境外入口继续检索。</div>'}</section>""")
    foreign_html = "".join(foreign_sections) or '<div class="notice">尚未配置境外对位入口。</div>'

    comparison_html = f"""
<div class="section-head"><h2><svg class="ico"><use href="#i-book"/></svg>国内—境外对读卡</h2><span class="meta">研究编排层，不改变证据等级</span></div>
<section class="result-list">
  <article class="result compact-result"><div><h3>国内材料能回答什么</h3><div class="snippet">{h(comparison.get('domestic_anchor') or item.get('domestic_status'))}</div></div></article>
  <article class="result compact-result"><div><h3>境外材料能回答什么</h3><div class="snippet">{h(comparison.get('foreign_anchor') or item.get('review_note'))}</div></div></article>
  <article class="result compact-result"><div><h3>差异、边界与下一步</h3><div class="snippet"><strong>差异：</strong>{h(comparison.get('difference') or '两侧材料不能自动互证。')}<br><strong>边界：</strong>{h(comparison.get('boundary') or '正式结论仍需回到原件、页码和复核门禁。')}<br><strong>下一步：</strong>{h(comparison.get('next_action') or '补齐原件、页码和来源链。')}</div></div></article>
  <article class="result compact-result"><div><h3>学术解释层</h3><div class="snippet">{h(comparison.get('academic_use') or '学术资料用于解释和对读，不替代一手来源。')}</div></div><div class="cite"><a href="/domestic/academic">打开学术层</a></div></article>
</section>
"""
    evidence_chain_html = _topic_evidence_chain_html(evidence_chain)

    event_link = f"/domestic/events?event={quote(event_id)}"
    body = breadcrumb_html([("/", "首页"), ("/research", "多源专题研究"), (None, str(item.get("event_name")))]) + f"""
<section class="doc-head">
  <div><h1>{h(item.get('event_name'))}</h1><div class="meta">{h(item.get('domestic_status'))}</div></div>
  <div class="doc-tools"><a class="button" href="/research">专题索引</a><a class="button secondary" href="/research/{quote(event_id)}/packet">打开研究包</a><a class="button secondary" href="/events?topic={quote(event_id)}">统一事件线索</a><a class="button secondary" href="{event_link}">国内覆盖</a></div>
</section>
<section class="stats">
  <div class="stat"><strong>{len(topic['domestic_rows'])}</strong><span>国内候选关联</span></div>
  <div class="stat"><strong>{h(topic['domestic_documents'])}</strong><span>国内已入库文档</span></div>
  <div class="stat"><strong>{h(topic['domestic_file_pages'])}/{h(topic['domestic_pages'])}</strong><span>源文件锚定页</span></div>
  <div class="stat"><strong>{h(topic['domestic_citation_pages'])}</strong><span>正式可引用页</span></div>
  <div class="stat"><strong>{h(topic['foreign_documents'])}</strong><span>境外机器命中文档</span></div>
  <div class="stat"><strong>{h(topic['foreign_pages'])}</strong><span>境外机器命中页</span></div>
  <div class="stat"><strong>{h(item.get('pair_status') or '待核')}</strong><span>对位状态</span></div>
  <div class="stat"><strong>{h(primary['label'])}</strong><span>一手证据闭环</span></div>
</section>
<div class="notice"><strong>证据边界：</strong>{h(item.get('review_note'))}<br><strong>一手闭环缺口：</strong>{h(primary['gap'])}<br>本页是研究导航和机器检索样本；它不把候选记录升级为正式事件证据，也不替代原件页码、源文件哈希或人工复核。</div>
{comparison_html}
{evidence_chain_html}
<div class="section-head"><h2><svg class="ico"><use href="#i-book"/></svg>学术研究资料（解释层）</h2><span class="meta">{h(academic_total)} 条机器主题候选</span></div>
<div class="notice">学术材料用于解释、争议定位和检索扩展；只有全文/页码/哈希/复核齐全后才可能进入正式引用。下方命中依据是书目元数据和结构化主题字段，不是正文语义确认。</div>
<section class="result-list">{academic_html}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>国内已入库证据样本</h2><span class="meta">{h(topic['domestic_documents'])} 篇 / {h(topic['domestic_pages'])} 页</span></div>
<section class="result-list">{domestic_evidence_html}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>国内候选记录</h2><span class="meta">{len(topic['domestic_rows'])} 条可见候选</span></div>
<section class="result-list">{domestic_html}</section>
{foreign_html}
<section class="doc-head" style="margin-top:20px;background:var(--panel-warm);border-left:4px solid var(--accent);">
  <div><h2>下一步核验</h2><div class="meta">优先核对原件、档号/卷期、日期冲突和页码；只有人工复核后才进入正式引用层。</div></div>
  <div class="doc-tools"><a class="button" href="/research/gaps">一手证据收口看板</a><a class="button" href="/domestic/review">国内复核看板</a><a class="button" href="/domestic/acquisition">调档清单</a></div>
</section>
"""
    return layout(str(item.get("event_name")), body, active_path="/research")


def _domestic_facet_page(kind: str) -> bytes:
    """国内人物或地点索引，链接回带关键词的真实候选检索。"""
    field = "person_tags" if kind == "people" else "place_tags"
    label = "人物" if kind == "people" else "地点"
    counts: dict[str, int] = {}
    for row in _domestic_rows():
        for value in _domestic_tag_values(row[field]):
            counts[value] = counts.get(value, 0) + 1
    items = []
    for value, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        items.append(f'<article class="result"><div><h2>{h(value)}</h2><div class="meta">国内候选 {count} 条</div></div><div class="cite"><a href="/domestic?q={quote(value)}">查看记录</a></div></article>')
    path = "/domestic/people" if kind == "people" else "/domestic/places"
    body = breadcrumb_html([("/domestic", "国内史料"), (None, label + "索引")]) + f"""
<section class="doc-head"><div><h1>国内{label}索引</h1><div class="meta">从候选记录中的实体标签回查来源、事件和不确定性</div></div><div class="doc-tools"><a class="button" href="/domestic">国内史料</a></div></section>
<section class="stats"><div class="stat"><strong>{h(len(items))}</strong><span>{label}词条</span></div><div class="stat"><strong>{h(sum(counts.values()))}</strong><span>关联次数</span></div></section>
<section class="result-list">{''.join(items) or '<div class="notice">暂无线索。</div>'}</section>"""
    return layout("国内" + label + "索引", body, active_path=path)


def domestic_acquisition_page() -> bytes:
    """调档清单与待获取项；只显示元数据，不暴露受限影像。"""
    plan_path = ROOT / "docs" / "domestic" / "acquisition_plan.md"
    text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    bullets = re.findall(r"^- (.+)$", text, flags=re.MULTILINE)
    rows = _domestic_rows()
    with_archive = sum(1 for row in rows if row["archive_fonds"] or row["archive_file"] or row["archive_item"])
    mmda_pending_rows: list[dict] = []
    if MMDA_ORIGINAL_PENDING_QUEUE_PATH.exists():
        try:
            mmda_pending_rows = [
                json.loads(line)
                for line in MMDA_ORIGINAL_PENDING_QUEUE_PATH.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
        except (OSError, json.JSONDecodeError):
            mmda_pending_rows = []
    mmda_pending_cards = "".join(
        f'<article class="result"><div><h2>{h(item.get("title") or item.get("queue_id"))}</h2>'
        f'<div class="meta">{h(item.get("phase"))} · {h(item.get("source_evidence"))} · {h(item.get("acquisition_status"))}</div>'
        f'<div class="snippet">{h(item.get("next_action") or "等待原件获取")}</div></div>'
        f'<div class="cite"><a href="/domestic/review">保持待核</a></div></article>'
        for item in mmda_pending_rows
    )
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "调档清单")]) + f"""
<section class="doc-head"><div><h1>国内史料调档与获取清单</h1><div class="meta">记录级档号、卷期、影像和权利的下一步任务</div></div><div class="doc-tools"><a class="button" href="/domestic/review">复核看板</a></div></section>
<section class="stats"><div class="stat"><strong>{h(len(rows))}</strong><span>候选记录</span></div><div class="stat"><strong>{h(with_archive)}</strong><span>含档号字段</span></div><div class="stat"><strong>{h(len(rows) - with_archive)}</strong><span>待定位</span></div><div class="stat"><strong>{h(len(mmda_pending_rows))}</strong><span>MMDA 原件待取</span></div></section>
<div class="notice">本页只列调档元数据和公开入口；受限扫描件、PDF、图片和本地缓存不会通过公开 URL 提供。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>1942—1943 MMDA 原件待取</h2></div><section class="result-list">{mmda_pending_cards or '<div class="notice">当前没有待取条目。</div>'}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-archive"/></svg>当前未闭环重点</h2></div><section class="result-list">{''.join(f'<article class="result"><div><div class="title">{h(item)}</div><div class="snippet">需要回到馆藏目录、同期报刊或正式汇编，补齐档号/卷期、影像和权利字段。</div></div><div class="cite"><a href="/domestic/review">进入复核</a></div></article>' for item in bullets)}</section>"""
    return layout("国内调档清单", body, active_path="/domestic/acquisition")


def domestic_review_page() -> bytes:
    """国内候选的原始性、字段完整性和编辑状态看板。"""
    rows = _domestic_rows()
    with conn() as c:
        decision_count = c.execute("SELECT count(*) FROM domestic_editorial_decisions").fetchone()[0]
        page_review_count = c.execute(
            """
            SELECT count(*)
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE d.source_platform='domestic'
              AND COALESCE(pp.citation_ready, 0)=0
            """
        ).fetchone()[0]
        page_review_queue = c.execute(
            """
            SELECT p.id AS page_id, p.page_label, d.doc_key, d.title, d.date_guess,
                   COALESCE(pp.review_status, 'missing') AS review_status,
                   COALESCE(pp.source_file, '') AS source_file,
                   COALESCE(pp.source_sha256, '') AS source_sha256,
                   COALESCE((
                       SELECT COALESCE(c.authenticity_level_accepted, c.authenticity_level_proposed)
                       FROM domestic_candidates c
                       WHERE c.ingested_document_id=d.id
                       ORDER BY CASE COALESCE(c.authenticity_level_accepted, c.authenticity_level_proposed)
                                  WHEN 'L0' THEN 0 WHEN 'L1' THEN 1 WHEN 'L2' THEN 2
                                  WHEN 'L3' THEN 3 ELSE 4 END,
                                CASE WHEN c.review_status='accepted' THEN 0 ELSE 1 END, c.id
                       LIMIT 1
                   ), '未关联') AS candidate_level,
                   COALESCE((
                       SELECT c.event_tags
                       FROM domestic_candidates c
                       WHERE c.ingested_document_id=d.id
                       ORDER BY CASE WHEN c.review_status='accepted' THEN 0 ELSE 1 END, c.id
                       LIMIT 1
                   ), '') AS candidate_event_tags
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE d.source_platform='domestic'
              AND COALESCE(pp.citation_ready, 0)=0
            ORDER BY
              CASE WHEN pp.page_id IS NULL THEN 0 ELSE 1 END,
              CASE WHEN trim(COALESCE(pp.source_file, ''))<>''
                         AND length(trim(COALESCE(pp.source_sha256, '')))=64 THEN 0 ELSE 1 END,
              CASE COALESCE((
                       SELECT COALESCE(c.authenticity_level_accepted, c.authenticity_level_proposed)
                       FROM domestic_candidates c
                       WHERE c.ingested_document_id=d.id
                       ORDER BY CASE COALESCE(c.authenticity_level_accepted, c.authenticity_level_proposed)
                                  WHEN 'L0' THEN 0 WHEN 'L1' THEN 1 WHEN 'L2' THEN 2
                                  WHEN 'L3' THEN 3 ELSE 4 END, c.id
                       LIMIT 1
                   ), 'LX')
                WHEN 'L0' THEN 0 WHEN 'L1' THEN 1 WHEN 'L2' THEN 2 WHEN 'L3' THEN 3 ELSE 4 END,
              d.date_guess, p.id
            LIMIT 18
            """
        ).fetchall()
    levels: dict[str, int] = {}
    statuses: dict[str, int] = {}
    missing_archive = 0
    for row in rows:
        levels[row["authenticity_level_proposed"]] = levels.get(row["authenticity_level_proposed"], 0) + 1
        statuses[row["review_status"]] = statuses.get(row["review_status"], 0) + 1
        if not (row["archive_fonds"] or row["archive_file"] or row["archive_item"] or row["catalog_reference"]):
            missing_archive += 1
    level_cards = "".join(f'<article class="result"><div><h2>{h(level)}</h2><div class="meta">{count} 条候选</div><div class="snippet">{h("核心或公开展示" if level in {"L0", "L1", "L2", "L3"} else "仅线索/待核")}</div></div><div class="cite"><a href="/domestic?level={h(level)}">查看</a></div></article>' for level, count in sorted(levels.items()))
    status_cards = "".join(f'<article class="result"><div><h2>{h(status)}</h2><div class="meta">{count} 条</div></div><div class="cite"><a href="/domestic?review={h(status)}">查看</a></div></article>' for status, count in sorted(statuses.items()))
    page_queue_cards = "".join(
        f'''<article class="result"><div><h3><a href="/domestic/evidence-review/{row["page_id"]}">{h(row["title"] or row["doc_key"])}</a></h3>
        <div class="meta">{h(row["date_guess"] or "日期未注明")} · {h(source_page_label(row))} · {h(row["review_status"])} · {h(row["candidate_level"])}</div>
        <div class="snippet">{h(row["doc_key"])} · SHA {h((row["source_sha256"] or "")[:16] or "未绑定")}… · 事件 {h(row["candidate_event_tags"] or "未标注")}</div></div>
        <div class="cite"><a href="/domestic/evidence-review/{row["page_id"]}">页级复核</a></div></article>'''
        for row in page_review_queue
    )
    body = breadcrumb_html([("/domestic", "国内史料"), (None, "复核看板")]) + f"""
<section class="doc-head"><div><h1>国内史料复核看板</h1><div class="meta">原始性等级、字段缺口、人工验收和编辑边界</div></div><div class="doc-tools"><a class="button" href="/domestic/acquisition">调档清单</a></div></section>
<section class="stats"><div class="stat"><strong>{h(len(rows))}</strong><span>候选</span></div><div class="stat"><strong>{h(statuses.get('accepted', 0))}</strong><span>已接受</span></div><div class="stat"><strong>{h(statuses.get('needs_human_review', 0))}</strong><span>待人工复核</span></div><div class="stat"><strong>{h(missing_archive)}</strong><span>缺档号/卷期</span></div><div class="stat"><strong>{h(decision_count)}</strong><span>编辑决策</span></div><div class="stat"><strong>{h(page_review_count)}</strong><span>待页级引用复核</span></div></section>
<div class="notice">只有完成形成者、日期、档号/卷期、页码/影像和权利核验的记录，才可从 needs_human_review 升级为 accepted；本看板不把拟议等级当作验收结论。</div>
<div class="section-head"><h2><svg class="ico"><use href="#i-layer"/></svg>原始性分布</h2></div><section class="result-list">{level_cards}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-edit"/></svg>编辑状态</h2></div><section class="result-list">{status_cards}</section>
<div class="section-head"><h2><svg class="ico"><use href="#i-quote"/></svg>页级证据复核队列</h2><span class="meta">未通过 citation_ready {h(page_review_count)} 页，当前展示优先项</span></div>
<div class="notice">优先处理已有源文件和 SHA256 锚定的页；完成原件/影像对照后，从卡片进入页级复核。没有人工说明的页面仍不能生成正式引文。</div>
<section class="result-list">{page_queue_cards or '<div class="notice">当前没有待复核页。</div>'}</section>"""
    return layout("国内复核看板", body, active_path="/domestic/review")


def _domestic_evidence_review_row(page_id: int) -> sqlite3.Row | None:
    with conn() as c:
        return c.execute(
            """
            SELECT
                p.id AS page_id, p.page_label, p.page_url, p.text AS original_text,
                d.doc_key, d.volume_id, d.doc_id, d.title, d.date_guess,
                d.source_platform, d.hit_type,
                pp.source_file, pp.source_sha256, pp.source_file_size,
                pp.pdf_page_no, pp.physical_page_no, pp.printed_page,
                pp.page_image_path, pp.ocr_engine, pp.ocr_model, pp.ocr_mode,
                pp.text_chars, pp.citation_ready, pp.needs_human_review,
                pp.review_status, pp.machine_review_note, pp.human_review_note
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            LEFT JOIN page_provenance pp ON pp.page_id=p.id
            WHERE p.id=? AND d.source_platform='domestic'
            """,
            (page_id,),
        ).fetchone()


def domestic_evidence_review_page(page_id: int, saved: bool = False, error: str = "") -> bytes:
    """国内页级证据复核：只有人工确认才允许打开 citation_ready 门禁。"""
    row = _domestic_evidence_review_row(page_id)
    if not row:
        return layout("国内证据页未找到", '<div class="notice">未找到国内证据页。</div>', active_path="/domestic/review")

    current_status = str(row["review_status"] or "review_only")
    saved_html = '<div class="notice" style="margin-bottom:14px;">页级证据复核已保存；引用状态仍以当前门禁字段为准。</div>' if saved else ""
    error_html = f'<div class="notice" style="border-left-color:#a33b2b;">{h(error)}</div>' if error else ""
    status_options = [
        ("review_only", "待人工复核"),
        ("needs_revision", "需补证/需修订"),
        ("human_verified", "人工核验可引用"),
    ]
    options = "".join(
        f'<option value="{h(value)}"{" selected" if value == current_status else ""}>{h(label)}</option>'
        for value, label in status_options
    )
    page = source_page_label(row)
    doc_href = f"/doc/{quote(str(row['doc_key']))}?page_id={row['page_id']}"
    source_url = row["page_url"] or ""
    citation_ready = int(row["citation_ready"] or 0)
    provenance_label = "已有页级 provenance" if row["source_file"] and row["source_sha256"] else "缺少页级 provenance"
    body = f"""
{saved_html}{error_html}
<section class="doc-head">
  <div>
    {title_block(row["title"], None, "h1")}
    <div class="meta">{h(row["date_guess"] or "日期未注明")} · {h(page)} · {h(row["hit_type"] or "domestic")} · {h(row["review_status"] or "missing")}</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="{doc_href}">并排阅读</a>
    <a class="button secondary" href="/cite/{row['page_id']}">引用门禁</a>
    <a class="button secondary" href="/domestic/review">复核看板</a>
    <a class="button secondary" href="{h(source_href(source_url))}" target="_blank" rel="noreferrer">原始来源</a>
  </div>
</section>
<section class="stats">
  <div class="stat"><strong>{h(citation_ready)}</strong><span>citation_ready</span></div>
  <div class="stat"><strong>{h(row["physical_page_no"] or row["pdf_page_no"] or "未标注")}</strong><span>物理页</span></div>
  <div class="stat"><strong>{h(row["text_chars"] or 0)}</strong><span>页文字数</span></div>
  <div class="stat"><strong>{h(provenance_label)}</strong><span>来源绑定</span></div>
</section>
<div class="notice"><strong>复核门槛：</strong>只有明确记录的研究者或授权审阅代理实际对照原件/影像、页码、形成日期和来源文件后，才可以选择“人工核验可引用”。机器 OCR、候选 accepted、文件存在或 SHA 锚定都不能单独完成这一步。</div>
<section class="reader">
  <article class="pane">
    <div class="pane-head"><span>国内原文 / OCR · {h(page)}</span><span>{h(row["ocr_engine"] or "OCR 引擎未标注")}</span></div>
    <div class="pane-body">{h(row["original_text"])}</div>
  </article>
  <article class="pane">
    <div class="pane-head"><span>页级 provenance</span><span>{h(row["review_status"] or "missing")}</span></div>
    <div class="pane-body">
      <p><strong>源文件：</strong>{h(row["source_file"] or "缺失")}</p>
      <p><strong>SHA256：</strong>{h(row["source_sha256"] or "缺失")}</p>
      <p><strong>文件大小：</strong>{h(row["source_file_size"] or "未标注")}</p>
      <p><strong>物理页 / 印刷页：</strong>{h(row["physical_page_no"] or "未标注")} / {h(row["printed_page"] or "未标注")}</p>
      <p><strong>机器说明：</strong>{h(row["machine_review_note"] or "无")}</p>
      <p><strong>已有人工说明：</strong>{h(row["human_review_note"] or "无")}</p>
    </div>
  </article>
</section>
<section class="doc-head" style="margin-top:20px;background:var(--panel-warm);border-left:4px solid var(--accent);">
  <div><h2>保存页级复核结论</h2><div class="meta">复核者标识和说明会写入本页 provenance；选择人工核验时两者均为必填。</div></div>
</section>
<form method="post" action="/domestic/evidence-review/{row['page_id']}" class="filter-panel">
  <label>结论
    <select name="review_status">{options}</select>
  </label>
  <label>复核者标识
    <input name="reviewer" value="" placeholder="例如：xiaoban / 研究者姓名" autocomplete="off">
  </label>
  <label style="display:block;margin-top:10px;">复核说明
    <textarea class="review-text" name="human_review_note" placeholder="记录你核对了哪些原件、页码、日期、文字差异和不确定性。" style="min-height:150px;">{h(row["human_review_note"] or "")}</textarea>
  </label>
  <label style="display:block;margin-top:10px;"><input type="checkbox" name="source_confirm" value="1"> 我已对照原件/影像、页码和来源文件；我理解这不是对 OCR 自动结果的确认。</label>
  <div class="formbar"><button class="button" type="submit">保存复核结论</button><a class="button secondary" href="{doc_href}">取消</a></div>
</form>
"""
    return layout("国内页级证据复核", body, active_path="/domestic/review")


def save_domestic_evidence_review(page_id: int, form: dict[str, list[str]]) -> tuple[bool, str]:
    status = (form.get("review_status", ["review_only"])[0] or "review_only").strip()
    note = (form.get("human_review_note", [""])[0] or "").strip()
    reviewer = (form.get("reviewer", [""])[0] or "").strip()
    confirmed = form.get("source_confirm", [""])[0] == "1"
    allowed = {"review_only", "needs_revision", "human_verified"}
    if status not in allowed:
        return False, "无效的复核状态。"
    row = _domestic_evidence_review_row(page_id)
    if not row:
        return False, "未找到国内证据页。"
    if status == "human_verified":
        if not confirmed:
            return False, "选择人工核验可引用前，必须确认已对照原件/影像、页码和来源文件。"
        if not reviewer:
            return False, "人工核验必须填写复核者标识。"
        if len(note) < 12:
            return False, "人工核验说明至少需要 12 个字符，记录实际核对内容。"
        if not row["source_file"] or len(str(row["source_sha256"] or "")) != 64:
            return False, "当前页没有完整的源文件与 SHA256 provenance，不能升级为正式引用。"
    stored_note = f"审核者：{reviewer}；{note}" if reviewer and note else (note or None)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    with conn() as c:
        c.execute(
            """
            UPDATE page_provenance
               SET citation_ready=?, needs_human_review=?, review_status=?,
                   human_review_note=?, updated_at=?
             WHERE page_id=?
            """,
            (
                1 if status == "human_verified" else 0,
                0 if status == "human_verified" else 1,
                status,
                stored_note,
                now,
                page_id,
            ),
        )
        if c.total_changes != 1:
            return False, "当前页没有可更新的 provenance 记录，请先补齐来源绑定。"
        c.commit()
    return True, ""


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
        # 顶部 Hero 封面区
        platforms_html_block = platforms_panel_html(c)
        # 关键指标摘要
        n_docs = c.execute("SELECT count(*) FROM documents").fetchone()[0]
        n_pages = c.execute("SELECT count(*) FROM pages").fetchone()[0]
        n_zh = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN'").fetchone()[0]
        # 「人工复核率」只统计需要翻译的档案（外语原文 → 中文译文）；
        # drnh 等中文原档（status='auto-converted'，仅做繁→简自动转换）不算翻译，
        # 应从分母排除，否则比例会被稀释。
        n_translatable = c.execute(
            "SELECT count(*) FROM translations WHERE language='zh-CN' "
            "AND status != 'auto-converted'"
        ).fetchone()[0]
        n_human = c.execute(
            "SELECT count(*) FROM translations WHERE language='zh-CN' "
            "AND status='human-reviewed'"
        ).fetchone()[0]
        n_events = c.execute("SELECT count(*) FROM research_events").fetchone()[0]
        n_domestic_docs = c.execute("SELECT count(*) FROM documents WHERE source_platform='domestic'").fetchone()[0]
        cov_pct = (n_human * 100 // n_translatable) if n_translatable else 0

        body = f"""
<section class="hero hero-compact">
  <h1>民盟历史文献研究库</h1>
  <p class="hero-sub">系统整理 1941—1950 年中国民主同盟<strong>境外档案与国内史料</strong>，<br>汇聚境外七源同代档案，并将国内同期报刊、公开扫描与目录资料按证据等级分层管理。</p>
  <div class="hero-chips">
    <span><b>{n_docs}</b> 篇文档</span>
    <span><b>{n_zh}</b> 条中文译文</span>
    <span><b>{cov_pct}%</b> 人工复核</span>
  </div>
</section>

<div class="section-head">
  <h2><svg class="ico"><use href="#i-globe"/></svg>档案研究平台</h2>
    <span class="section-meta">境外七源 + 国内史料层 · 持续更新</span>
</div>
{platforms_html_block}

<div class="section-head" style="margin-top:48px;">
  <h2><svg class="ico"><use href="#i-quote"/></svg>学术论文总览</h2>
  <a class="more" href="/papers">进入论文总览 →</a>
</div>
<section class="stats stats-card">
  <div class="stat"><strong>总论</strong><span>七源对照框架</span></div>
  <div class="stat"><strong>FRUS</strong><span>美方公开外交</span></div>
  <div class="stat"><strong>CIA</strong><span>美方解密情报</span></div>
  <div class="stat"><strong>DRNH</strong><span>国民政府内部</span></div>
  <div class="stat"><strong>七源</strong><span>平台论文入口</span></div>
</section>

<div class="section-head" style="margin-top:48px;">
  <h2><svg class="ico"><use href="#i-edit"/></svg>档案研究仪表盘</h2>
  <a class="more" href="/dashboard">查看完整仪表盘 →</a>
</div>
<section class="stats stats-card">
  <div class="stat"><strong>{n_docs}</strong><span>篇源文档</span></div>
  <div class="stat"><strong>{n_pages}</strong><span>个页面 / 段落</span></div>
  <div class="stat"><strong>{n_zh}</strong><span>中文译文片段</span></div>
  <div class="stat"><strong>{cov_pct}%</strong><span>人工复核率</span></div>
  <div class="stat"><strong>{n_events}</strong><span>条事件线索</span></div>
  <div class="stat"><strong>{n_domestic_docs}</strong><span>国内资料文档</span></div>
</section>
"""


    return layout("首页", body, active_path="/")


def search_filter_form(query: str, platform: str | None, year: str, grade: str, person: str, cited: bool) -> str:
    platform_options = ['<option value="">全部平台</option>']
    for key, meta in PLATFORM_META.items():
        selected = " selected" if platform == key else ""
        platform_options.append(f'<option value="{h(key)}"{selected}>{h(meta["name"])}</option>')
    grade_options = ['<option value="">全部分级</option>']
    for value in ["核心文献", "相关文献", "人物关联", "背景材料", "A", "B"]:
        selected = " selected" if grade == value else ""
        grade_options.append(f'<option value="{h(value)}"{selected}>{h(value)}</option>')
    checked = " checked" if cited else ""
    return f"""
<form class="filters search-filters" action="/search" method="get">
  <label><span>关键词</span><input type="search" name="q" value="{h(query)}" placeholder="罗隆基、Marshall、政协"></label>
  <label><span>平台</span><select name="platform">{''.join(platform_options)}</select></label>
  <label><span>年份</span><input type="text" name="year" value="{h(year)}" inputmode="numeric" maxlength="4" placeholder="1949"></label>
  <label><span>分级</span><select name="grade">{''.join(grade_options)}</select></label>
  <label><span>人物</span><input type="text" name="person" value="{h(person)}" placeholder="张澜 / Lo Lung-chi"></label>
  <label class="checkline"><input type="checkbox" name="cited" value="1"{checked}>只看论文引用档案</label>
  <button class="button" type="submit"><svg class="ico"><use href="#i-search"/></svg>筛选</button>
</form>
"""


def search(query: str, platform: str | None = None, year: str = "", grade: str = "", person: str = "", cited: bool = False) -> bytes:
    with conn() as c:
        rows = rows_for_search(c, query, platform=platform, year=year, grade=grade, person=person, cited=cited)
        domestic_evidence_labels = _search_domestic_evidence_labels(c, rows)
        body = stats_html(c)
        title_text = f"搜索：{query}" if query.strip() else "筛选档案"
        chips = []
        if platform:
            chips.append(PLATFORM_META.get(platform, {}).get("name", platform))
        if year.strip():
            chips.append(f"{year.strip()[:4]} 年")
        if grade.strip():
            chips.append(grade.strip())
        if person.strip():
            chips.append(person.strip())
        if cited:
            chips.append("论文引用档案")
        chip_html = "".join(f'<span class="tag">{h(chip)}</span>' for chip in chips)
        body += f'<h1 style="font-size:20px;margin:0 0 12px;">{h(title_text)}</h1>'
        body += search_filter_form(query, platform, year, grade, person, cited)
        if chip_html:
            body += f'<div class="tagline" style="margin:-8px 0 14px;">{chip_html}<span class="tag">{len(rows)} 条结果</span></div>'
        if rows:
            body += '<section class="result-list">' + "".join(
                result_html(row, domestic_evidence_labels.get(int(row["page_id"]), ""))
                for row in rows
            ) + "</section>"
        else:
            body += '<div class="notice">没有找到结果。</div>'
    return layout(f"搜索 {query}", body, query)


def _academic_metadata_for_citation(external_id: str) -> dict[str, object]:
    """读取学术条目的书目元数据，避免用境外档案模板生成错误引文。"""
    if not external_id or not DOMESTIC_STAGING_DB_PATH.is_file():
        return {}
    try:
        with sqlite3.connect(f"file:{DOMESTIC_STAGING_DB_PATH}?mode=ro", uri=True) as c:
            c.row_factory = sqlite3.Row
            row = c.execute(
                """SELECT author, institution, research_type, quality_tier,
                          fulltext_status, citation_ready, human_verified
                   FROM domestic_research_materials
                   WHERE external_id=? AND layer='SCHOLARLY_RESEARCH'
                   LIMIT 1""",
                (external_id,),
            ).fetchone()
    except sqlite3.Error:
        return {}
    return dict(row) if row else {}


def _build_citations(doc: sqlite3.Row) -> dict[str, str]:
    """生成 GB/T 7714-2015 / BibTeX / Chicago 三种引用格式（按 source_platform 分支）。

    文献类型代码（GB/T 7714-2015）：
    - G/OL 汇编/在线 → FRUS 等政府汇编出版物
    - A/OL 档案/在线 → CIA 解密档案、Wilson Center 数字档案、Hoover 卷宗
    - N/OL 报纸/在线 → HathiTrust 港媒
    """
    title_zh = translate_title(doc["title"])
    title_en = doc["title"]
    vol = doc["volume_id"] or ""
    docnum = doc["doc_id"] or ""
    date = doc["date_guess"] or ""
    url = doc["url"] or ""
    platform = (doc["source_platform"] if "source_platform" in doc.keys() else None) or "frus"
    today = datetime.date.today().isoformat()  # 引用日期 = 当天
    year = ""
    m = re.search(r"\b(19\d{2}|20\d{2})\b", date)
    if m:
        year = m.group(1)
    elif vol:
        m = re.search(r"\b(19\d{2})\b", vol)
        if m:
            year = m.group(1)

    # ============ 国内学术研究全文（解释层） ============
    if platform == "domestic" and doc["hit_type"] == "domestic_academic_fulltext":
        metadata = _academic_metadata_for_citation(str(docnum))
        author = str(metadata.get("author") or "作者未标注")
        institution = str(metadata.get("institution") or "机构未标注")
        research_type = str(metadata.get("research_type") or "")
        material_code = "J/OL" if research_type == "SCHOLARLY_ARTICLE" else "M/OL"
        bibkey = f"DomesticAcademic_{docnum}".replace(".", "_").replace("-", "_")[:80]
        note = "本地全文检索层；review_only，citation_ready=0，须完成版本、页码和人工复核后方可正式引用"
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  author = {{{author}}},\n"
            f"  title = {{{title_en}}},\n"
            f"  howpublished = {{{institution}; 国内学术研究解释层}},\n"
            f"  year = {{{year}}},\n"
            f"  note = {{{note}}},\n"
            f"  url = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f'{author}. "{title_en}." {institution}, {date}. '
            f'国内学术研究解释层（本地全文检索稿，待复核）. '
            f'Accessed {today}. {url}.'
        )
        gb = (
            f"{author}. {title_zh}[{material_code}]. {institution}, ({date}). "
            f"国内学术研究解释层[{today}]. {url}. 注：{note}。"
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ 国内史料文献级入口（正式引用仍以页卡为准） ============
    if platform == "domestic":
        source_title = str(doc["volume_title"] or "国内史料")
        source_id = str(docnum or doc["doc_key"] or "")
        bibkey = f"Domestic_{source_id}".replace(".", "_").replace("-", "_").replace("/", "_")[:96]
        note = "文献级入口；正式引用请进入具体页的页级引用卡，并核对 human_verified 与 citation_ready 门禁"
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title = {{{title_zh}}},\n"
            f"  author = {{{source_title}}},\n"
            f"  howpublished = {{{source_title}; 国内史料文献级入口}},\n"
            f"  year = {{{year}}},\n"
            f"  note = {{{note}}},\n"
            f"  url = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f"{source_title}. \"{title_zh}.\" {date or '日期未注明'}. "
            f"国内史料研究库，文献级入口。{url}。注：{note}。"
        )
        gb = (
            f"{source_title}. {title_zh}[G/OL]. {date or '日期未注明'}. "
            f"国内史料研究库，文献级入口[{today}]. {url}. 注：{note}。"
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ CIA Records Reading Room 解密档案 ============
    if platform == "cia":
        rdp_id = docnum  # archive.org identifier，含 RDP 编号
        bibkey = f"CIA_{rdp_id}".replace(".", "_").replace("-", "_")
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title  = {{{title_en}}},\n"
            f"  author = {{Central Intelligence Agency}},\n"
            f"  howpublished = {{CIA Records Reading Room (declassified), mirrored at Internet Archive}},\n"
            f"  year   = {{{year}}},\n"
            f"  note   = {{Document ID: {rdp_id}}},\n"
            f"  url    = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f'Central Intelligence Agency. "{title_en}." Declassified report, {date}. '
            f'Document ID {rdp_id}. CIA Records Reading Room (mirrored at Internet Archive). '
            f'Accessed {today}. {url}.'
        )
        gb = (
            f"美国中央情报局. {title_zh}: {title_en}[A/OL]. 解密档案, "
            f"档案编号 {rdp_id}, {date}. CIA Records Reading Room（Internet Archive 镜像）"
            f"[{today}]. {url}."
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ Wilson Center Digital Archive ============
    if platform == "wilson":
        wid = docnum or doc["doc_id"] or ""
        bibkey = f"Wilson_{wid}".replace(".", "_").replace("-", "_")[:80]
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title  = {{{title_en}}},\n"
            f"  author = {{Wilson Center Digital Archive}},\n"
            f"  howpublished = {{Woodrow Wilson International Center for Scholars, Digital Archive}},\n"
            f"  year   = {{{year}}},\n"
            f"  note   = {{Document date: {date}}},\n"
            f"  url    = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f'"{title_en}." {date}. Wilson Center Digital Archive, Woodrow Wilson '
            f'International Center for Scholars. Accessed {today}. {url}.'
        )
        gb = (
            f"威尔逊国际学者中心数字档案 编. {title_zh}: {title_en}[A/OL]. "
            f"({date}). 华盛顿: Woodrow Wilson International Center for Scholars[{today}]. {url}."
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ Hoover Institution Archives 现场调档 ============
    if platform == "hoover":
        hid = docnum or ""
        # title 形如 "Carsun Chang to Albert C. Wedemeyer · 1947-07-26"
        # 抽出作者：第一个 " to " 前的部分
        author_en = ""
        author_zh = ""
        mt = re.match(r"^([^·]+?)\s+to\s+", title_en)
        if mt:
            author_en = mt.group(1).strip()
            if "Carsun Chang" in author_en:
                author_zh = "张君劢"
        # 卷宗名：从 volume_title 抽 "Carsun Chang Papers (1946-1962)"
        vol_clean = (doc["volume_title"] or "").replace("Hoover Institution · ", "").strip()
        bibkey = f"Hoover_{hid}".replace(".", "_").replace("-", "_")[:80]
        author_bib = author_en or "Hoover Institution Archives"
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title  = {{{title_en}}},\n"
            f"  author = {{{author_bib}}},\n"
            f"  howpublished = {{Manuscript, {vol_clean}, Hoover Institution Archives, Stanford University}},\n"
            f"  year   = {{{year}}},\n"
            f"  note   = {{Onsite consultation; folder: {vol_clean}}},\n"
            f"  url    = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f'{author_bib}. "{title_en}." {date}. {vol_clean}, '
            f'Hoover Institution Archives, Stanford University. Accessed {today}. {url}.'
        )
        author_gb = (f"{author_zh}（{author_en}）" if author_zh else author_en) or "胡佛档案馆藏"
        gb = (
            f"{author_gb}. {title_zh}: {title_en}[A]. {vol_clean}, "
            f"({date}). 斯坦福: Stanford University, Hoover Institution Archives"
            f"[{today}]. {url}."
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ 台北档案史料文物查询系统 ============
    if platform == "drnh":
        store_no = docnum  # 典藏号
        fonds_full = (doc["volume_title"] if "volume_title" in doc.keys() else "") or ""
        title_hant = title_en  # 本平台 title 字段存的为繁体原题
        # 实时繁→简
        try:
            import zhconv
            title_hans = zhconv.convert(title_hant, "zh-cn")
            fonds_hans = zhconv.convert(fonds_full, "zh-cn") if fonds_full else fonds_full
        except Exception:
            title_hans = title_hant
            fonds_hans = fonds_full
        bibkey = f"DRNH_{store_no}".replace(".", "_").replace("-", "_")[:80]
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title  = {{{title_hans}}},\n"
            f"  author = {{台北档案史料}},\n"
            f"  howpublished = {{台北档案史料文物查询系统，全宗：{fonds_hans}}},\n"
            f"  year   = {{{year}}},\n"
            f"  note   = {{典藏号 {store_no}; 本件日期 {date}}},\n"
            f"  url    = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f'Taipei "Academia Historica" (Guoshi Guan). "{title_hans}." {date}. '
            f'{fonds_hans}, 典藏号 {store_no}. Accessed {today}. {url}.'
        )
        gb = (
            f"台北档案史料 编. {title_hans}（繁体原题：{title_hant}）[A/OL]. "
            f"{fonds_hans}, 典藏号 {store_no}, ({date}). "
            f"台北档案史料文物查询系统[{today}]. {url}."
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ HathiTrust / Internet Archive 港媒 ============
    if platform == "hathitrust":
        # title 形如 "China Mail 1946-01-28 · 政协会议召开期间"
        # 报刊名 = title 中日期前的部分；事件标签 = " · " 后部分
        paper_en = "China Mail"
        paper_zh = "香港中国邮报"
        mt = re.match(r"^(China Mail|Hong Kong Telegraph)\s+(\d{4}-\d{2}-\d{2})(?:\s+·\s+(.+))?$", title_en)
        event_tag = ""
        if mt:
            paper_en = mt.group(1)
            event_tag = (mt.group(3) or "").strip()
            paper_zh = "香港中国邮报" if paper_en == "China Mail" else "香港电讯报"
        nid = doc["doc_id"] or ""
        bibkey = f"HK_{nid}".replace(".", "_").replace("-", "_")[:80]
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title  = {{{paper_en}, {date} (full issue scan)}},\n"
            f"  author = {{{paper_en}}},\n"
            f"  howpublished = {{{paper_en} (Hong Kong), full-issue scan, Internet Archive mirror}},\n"
            f"  year   = {{{year}}},\n"
            f"  note   = {{Identifier: {nid}}},\n"
            f"  url    = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f'{paper_en}. "{date} (full issue scan)." Hong Kong, {date}. '
            f'Internet Archive mirror, identifier {nid}. Accessed {today}. {url}.'
        )
        event_suffix = f"（覆盖{event_tag}相关报道）" if event_tag else ""
        gb = (
            f"{paper_en}（{paper_zh}）. {date} 整期扫描档{event_suffix}[N/OL]. "
            f"香港: {paper_en}, ({date}). Internet Archive 镜像, 标识号 {nid}[{today}]. {url}."
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ NewspaperSG 新加坡国家图书馆报刊 ============
    if platform == "newspapersg":
        newspaper = "NewspaperSG"
        if title_en.startswith("本") or re.search(r"[\u4e00-\u9fff]", title_en):
            newspaper = "南洋商报"
        elif "maltribune" in (doc["doc_key"] or ""):
            newspaper = "Malaya Tribune"
        elif "morningtribune" in (doc["doc_key"] or ""):
            newspaper = "Morning Tribune"
        elif "indiandailymail" in (doc["doc_key"] or ""):
            newspaper = "Indian Daily Mail"
        elif "sundaytribune" in (doc["doc_key"] or ""):
            newspaper = "Sunday Tribune"
        nid = docnum or (doc["doc_key"] or "").split(":", 1)[-1]
        bibkey = f"NewspaperSG_{nid}".replace(".", "_").replace("-", "_")[:80]
        bibtex = (
            f"@misc{{{bibkey},\n"
            f"  title  = {{{title_en}}},\n"
            f"  author = {{{newspaper}}},\n"
            f"  howpublished = {{NewspaperSG, National Library Board Singapore}},\n"
            f"  year   = {{{year}}},\n"
            f"  note   = {{Article identifier: {nid}; date: {date}}},\n"
            f"  url    = {{{url}}},\n"
            f"  urldate = {{{today}}}\n"
            f"}}"
        )
        chicago = (
            f'{newspaper}. "{title_en}." {date}. NewspaperSG, National Library '
            f'Board Singapore. Accessed {today}. {url}.'
        )
        gb = (
            f"{newspaper}. {title_zh}: {title_en}[N/OL]. "
            f"新加坡: NewspaperSG, National Library Board Singapore, ({date})"
            f"[{today}]. {url}."
        )
        return {"bibtex": bibtex, "chicago": chicago, "gb": gb}

    # ============ FRUS 美国对外关系文件集（默认） ============
    bibkey = f"FRUS_{vol}_{docnum}".replace(".", "_").replace("-", "_")
    bibtex = (
        f"@incollection{{{bibkey},\n"
        f"  title  = {{{title_en}}},\n"
        f"  booktitle = {{Foreign Relations of the United States ({vol})}},\n"
        f"  publisher = {{U.S. Department of State, Office of the Historian}},\n"
        f"  address = {{Washington, D.C.}},\n"
        f"  year   = {{{year}}},\n"
        f"  note   = {{Document {docnum}, {date}}},\n"
        f"  url    = {{{url}}},\n"
        f"  urldate = {{{today}}}\n"
        f"}}"
    )
    chicago = (
        f'"{title_en}." In *Foreign Relations of the United States* ({vol}), '
        f'document {docnum}, {date}. Washington, D.C.: U.S. Department of State, '
        f'Office of the Historian. Accessed {today}. {url}.'
    )
    # FRUS volume_title 更完整：例如 "Foreign Relations of the United States, Diplomatic Papers, 1943, China"
    vol_full = doc["volume_title"] or f"Foreign Relations of the United States ({vol})"
    gb = (
        f"美国国务院历史档案办公室 编. {title_zh}: {title_en}[G/OL]. "
        f"// {vol_full}, 文件 {docnum}, ({date}). "
        f"华盛顿: 美国国务院[{today}]. {url}."
    )
    return {"bibtex": bibtex, "chicago": chicago, "gb": gb}


def doc_page(doc_key: str, page_id: str | None = None) -> bytes:
    with conn() as c:
        doc = c.execute(
            """
            SELECT documents.*, dc.grade, dc.score, dc.reason, dc.needs_review
            FROM documents
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            WHERE documents.doc_key=? OR lower(documents.doc_key)=lower(?)
            LIMIT 1
            """,
            (doc_key, doc_key),
        ).fetchone()
        if not doc:
            return layout("未找到文档", '<div class="notice">未找到文档。</div>')
        if (
            getattr(_request, "public_mode", False)
            and (doc["source_platform"] or "") == "domestic"
            and not _public_domestic_document_visible(c, int(doc["id"]))
        ):
            return layout(
                "公开模式不可用",
                '<div class="notice">该国内文档尚未通过公开等级与权利门禁。请返回 <a href="/public">公开介绍版</a>。</div>',
                active_path="/public",
            )
        rows = c.execute(
            """
            SELECT
                pages.id AS page_id,
                pages.page_label,
                pages.page_url,
                pages.text AS original_text,
                translations.text AS zh_text,
                translations.status AS zh_status,
                COALESCE(pp.citation_ready, 0) AS citation_ready,
                COALESCE(pp.needs_human_review, 1) AS needs_human_review,
                COALESCE(pp.review_status, 'missing') AS provenance_review_status,
                COALESCE(pp.human_review_note, '') AS human_review_note,
                COALESCE(pp.source_file, '') AS provenance_source_file,
                COALESCE(pp.source_sha256, '') AS provenance_source_sha256
            FROM pages
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            LEFT JOIN page_provenance pp ON pp.page_id = pages.id
            WHERE pages.document_id=?
            ORDER BY pages.id
            """,
            (doc["id"],),
        ).fetchall()

    platform = doc["source_platform"] or "frus"
    is_domestic_academic = (
        platform == "domestic" and doc["hit_type"] == "domestic_academic_fulltext"
    )
    academic_metadata = _academic_metadata_for_citation(str(doc["doc_id"] or "")) if is_domestic_academic else {}
    source_link = h(source_href(doc["url"] or ""))
    citations = _build_citations(doc)
    paper_backlinks = paper_backlinks_html(doc["doc_key"])
    event_backlinks = doc_event_links_html([row["page_id"] for row in rows])
    matched_chips = "".join(
        f'<a class="tag" href="/search?q={quote(t.strip())}">{h(t.strip())}</a>'
        for t in (doc["matched_terms"] or "").split(";") if t.strip()
    )

    # 按 source_platform 决定头部按钮和元数据卡片
    is_cia = (platform == "cia")
    if is_domestic_academic:
        academic_status = str(academic_metadata.get("fulltext_status") or "review_only")
        academic_author = str(academic_metadata.get("author") or "作者未标注")
        academic_institution = str(academic_metadata.get("institution") or "机构未标注")
        tools_html = (
            f'<a class="button" href="{source_link}" target="_blank" rel="noreferrer">'
            f'<svg class="ico"><use href="#i-globe"/></svg>来源入口</a>'
            f'<a class="button" href="/domestic/search?scope=research&amp;q={quote(str(doc["doc_id"] or doc["title"]))}">'
            f'<svg class="ico"><use href="#i-search"/></svg>研究资料检索</a>'
            f'<a class="button secondary" href="/domestic/events">'
            f'<svg class="ico"><use href="#i-archive"/></svg>一手对照</a>'
        )
        platform_badge = (
            '<span class="src-badge" style="background:#6b4e71;color:#fff;">'
            '<svg class="ico"><use href="#i-book"/></svg>国内学术研究 · 解释层 · review_only'
            '</span>'
        )
        meta_card_foot = (
            f'<span><strong>作者</strong> {h(academic_author)}</span>'
            f'<span><strong>机构</strong> {h(academic_institution)}</span>'
            f'<span><strong>全文状态</strong> {h(academic_status)}</span>'
            f'<span><strong>本库 ID</strong> doc/{h(doc["doc_key"])}</span>'
        )
    elif is_cia:
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
    elif platform == "drnh":
        # 从数据库 drnh_images 表读取图片关联（表不存在时优雅降级为无图，不致整页崩溃）
        try:
            cached_images = c.execute(
                "SELECT page_num, file_path FROM drnh_images WHERE document_id = ? ORDER BY page_num",
                (doc["id"],)
            ).fetchall()
        except sqlite3.OperationalError:
            cached_images = []
        has_preview = len(cached_images) > 0
        # 该台北档案是否存在访客水印图——仅「有水印图」的档案才展示「史料意旨」摘要卡片
        _drnh_img_dir_name = doc["doc_key"].replace(":", "__").replace("/", "_")
        _drnh_img_dirs = [DATA_ROOT / "drnh_images" / _drnh_img_dir_name]
        # 兼容旧的 drnh__<典藏号> 和下载器当前生成的 <典藏号> 目录。
        if _drnh_img_dir_name.startswith("drnh__"):
            _drnh_img_dirs.append(DATA_ROOT / "drnh_images" / _drnh_img_dir_name.removeprefix("drnh__"))
        _drnh_img_dir = next((p for p in _drnh_img_dirs if p.is_dir()), _drnh_img_dirs[0])
        has_watermark_img = _drnh_img_dir.is_dir() and any(
            list(_drnh_img_dir.glob("p*.jpg")) + list(_drnh_img_dir.glob("page_*.jpg"))
        )


        preview_btn = (
            f'<a class="button" href="#drnh-workspace-start"><svg class="ico"><use href="#i-book"/></svg>'
            f'官方访客预览 · {len(cached_images)} 页</a>'
            if has_preview else ''
        )
        tools_html = (
            preview_btn +
            f'<a class="button" href="{source_link}" target="_blank" rel="noreferrer">'
            f'<svg class="ico"><use href="#i-globe"/></svg>原档系统（按典藏号搜寻）</a>'
            f'<a class="button" href="/search?q={quote(doc["matched_terms"] or doc["title"])}">'
            f'<svg class="ico"><use href="#i-search"/></svg>相关搜索</a>'
        )
        platform_badge = (
            '<span class="src-badge" style="background:#1F4E78;color:#fff;">'
            '<svg class="ico"><use href="#i-archive"/></svg>国史馆官方访客预览 · 非正文'
            '</span>'
        )
        meta_card_foot = (
            f'<span><strong>典藏號</strong> {h(doc["doc_id"])}</span>'
            f'<span><strong>全宗</strong> {h(doc["volume_title"])} ({h(doc["volume_id"])})</span>'
            f'<span><strong>本件日期</strong> {h(doc["date_guess"])}</span>'
            f'<span><strong>本库 ID</strong> doc/{h(doc["doc_key"])}</span>'
        )
    else:
        source_button_labels = {
            "frus": "FRUS 原文",
            "wilson": "Wilson Center 原档",
            "hoover": "Hoover 现场调档来源",
            "hathitrust": "archive.org 镜像",
            "newspapersg": "NewspaperSG 原始报刊",
        }
        source_button_label = source_button_labels.get(platform, "档案原文")
        tools_html = (
            f'<a class="button" href="{source_link}" target="_blank" rel="noreferrer">'
            f'<svg class="ico"><use href="#i-globe"/></svg>{h(source_button_label)}</a>'
            f'<a class="button" href="/search?q={quote(doc["matched_terms"] or doc["title"])}">'
            f'<svg class="ico"><use href="#i-search"/></svg>相关搜索</a>'
        )
        platform_badge = ''
        if platform == "frus":
            meta_card_foot = (
                f'<span><strong>FRUS 卷号</strong> {h(doc["volume_id"])}</span>'
                f'<span><strong>文件号</strong> {h(doc["doc_id"])}</span>'
                f'<span><strong>日期</strong> {h(doc["date_guess"])}</span>'
                f'<span><strong>本库 ID</strong> doc/{h(doc["doc_key"])}</span>'
            )
        else:
            meta_card_foot = (
                f'<span><strong>平台</strong> {h(platform)}</span>'
                f'<span><strong>文档编号</strong> {h(doc["doc_id"] or doc["doc_key"])}</span>'
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
"""

    # 交叉档案印证逻辑：查找相关事件与人物
    related_docs = []
    # 1. 基于关键词查找事件关联
    for evt in KEY_EVENTS:
        if any(term.lower() in (doc["title"] + (doc["matched_terms"] or "")).lower() for term in evt["search_terms"]):
            # 改为参数化查询：即使 search_terms 目前只来自 key_events.py 静态常量，
            # 用 f-string 拼 SQL 仍是一个隐患信号——一旦这份数据未来变成可编辑/外部输入，
            # 这里会立刻变成真实的 SQL 注入点，所以直接改成 ? 占位符。
            terms = evt["search_terms"][:3]
            term_query = " OR ".join(["title LIKE ?"] * len(terms))
            related = c.execute(f"""
                SELECT doc_key, title, source_platform, date_guess
                FROM documents
                WHERE ({term_query}) AND doc_key != ?
                  AND date_guess BETWEEN date(?, '-3 months') AND date(?, '+3 months')
                LIMIT 4
            """, tuple(f"%{t}%" for t in terms) + (doc["doc_key"], doc["date_guess"], doc["date_guess"])).fetchall()
            if related:
                related_docs.append({"title": f"事件印证: {evt['name']}", "docs": related})
            break
            
    # 2. 基于关联人物查找人际网络档案关联
    for p in PEOPLE:
        if p['name'] in (doc["title"] + (doc["matched_terms"] or "")):
            # 查找同人物关联的其它文档
            related_people = c.execute("""
                SELECT doc_key, title, source_platform, date_guess 
                FROM documents 
                WHERE (title LIKE ? OR matched_terms LIKE ?) AND doc_key != ?
                  AND date_guess BETWEEN date(?, '-3 months') AND date(?, '+3 months')
                LIMIT 4
            """, (f"%{p['name']}%", f"%{p['name']}%", doc["doc_key"], doc["date_guess"], doc["date_guess"])).fetchall()
            if related_people:
                related_docs.append({"title": f"人物关联: {p['name']}", "docs": related_people})
            break

    if is_domestic_academic:
        citation_heading = "引用草稿（待复核）"
    elif platform == "domestic":
        citation_heading = "国内史料入口（页级引用）"
    else:
        citation_heading = "学术引用"
    citation_notice = (
        '<div class="notice">该条目属于学术解释层：当前全文仅供检索和研究，不是正式可引用证据；'
        '需完成版本、页码/章节、来源哈希和人工复核后，才可申请 citation-ready。</div>'
        if is_domestic_academic else ""
    )
    if platform == "domestic" and not is_domestic_academic:
        citation_notice = (
            '<div class="notice">这里是文献级来源入口，不是整篇文档的正式引文。请从具体页进入页级引用卡；'
            '只有该页同时通过 <code>human_verified</code>、<code>needs_human_review=0</code>、'
            '<code>citation_ready=1</code> 并有人工复核说明时，才可正式引用。</div>'
        )
    body += f"""
<section class="meta-card{' cia-cite' if is_cia else ''}" id="cite-card">
  <div class="meta-card-head">
    <h3><svg class="ico"><use href="#i-quote"/></svg>{citation_heading}</h3>
    <div class="cite-tabs">
      <button type="button" class="cite-tab active" data-fmt="gb">GB/T 7714</button>
      <button type="button" class="cite-tab" data-fmt="bibtex">BibTeX</button>
      <button type="button" class="cite-tab" data-fmt="chicago">Chicago</button>
      <button type="button" class="button cite-copy" id="cite-copy-btn"><svg class="ico"><use href="#i-check"/></svg>复制</button>
    </div>
  </div>
  <pre class="cite-content" id="cite-content" data-bibtex="{h(citations['bibtex'])}" data-chicago="{h(citations['chicago'])}" data-gb="{h(citations['gb'])}">{h(citations['gb'])}</pre>
  <div class="meta-card-foot">{meta_card_foot}</div>
</section>
{citation_notice}
{paper_backlinks}
{event_backlinks}
"""
    # 渲染交叉档案区块
    if related_docs:
        body += '<section class="meta-card"><h3><svg class="ico"><use href="#i-globe"/></svg>跨源交叉印证</h3>'
        for group in related_docs:
            body += f'<h4>{h(group["title"])}</h4><ul>'
            for d in group["docs"]:
                body += f'<li><a href="/doc/{quote(d["doc_key"])}">{h(d["title"])}</a> <em>({h(d["source_platform"])})</em></li>'
            body += '</ul>'
        body += '</section>'

    body += (('<div class="notice cia-ocr-notice" style="margin-bottom:14px;">'
  '<svg class="ico"><use href="#i-globe"/></svg>'
  '本档案为 CIA 解密报告的 <b>archive.org OCR 文本</b>，可能含扫描识别噪声（页眉/水印残留）。'
  '正式引用请以 <a href="' + archive_detail_url + '" target="_blank">archive.org 原始 PDF</a> 为准。'
  '</div>') if is_cia else '')

    # DRNH 访客水印图预览 section
    if platform == "drnh" and cached_images:
        body += f"""
<div class="drnh-archive-notice">
  <svg class="ico"><use href="#i-book"/></svg>
  <span>
    <strong>国史馆官方访客预览：</strong> 本地影像含重复馆藏水印与「请登入」锁定提示，仅用于确认档号、页数和页面结构；右侧内容是目录卡片，不是扫描正文转录。
    当前页面不会把预览图当作正式引文；只有通过 <code>human_verified</code> 与 <code>citation_ready</code> 门禁的页才会生成正式引用。正式引用如需无水印原图，请至
    <a href="{source_link}" target="_blank" rel="noreferrer">原档系统</a>
    注册会员以查看无水印原图。
  </span>
</div>
"""

    if platform == "drnh":
        body += '<section id="drnh-workspace-start" class="reader reader-drnh">'
    else:
        body += '<section class="reader">'
    for idx, row in enumerate(rows):
        page = f"p. {row['page_label']}" if row["page_label"] else "doc-level"
        selected = " id=\"selected\"" if page_id and str(row["page_id"]) == str(page_id) else ""
        zh = row["zh_text"] or "尚未翻译"
        zh_class = "" if row["zh_text"] else " empty"
        status = row["zh_status"] or "needs-translation"
        # 按平台动态生成来源标签（之前写死「FRUS 段落」对其他平台不合适）
        source_label_map = {
            "frus": "FRUS 段落",
            "cia": "archive.org 原档",
            "wilson": "Wilson Center 原档",
            "hoover": "Hoover 现场调档",
            "hathitrust": "archive.org 镜像",
            "drnh": "台北档案史料原档",
            "newspapersg": "NewspaperSG 原始报刊",
        }
        source_label = source_label_map.get(platform, "档案原文")

        # drnh 是中文原档：去双栏（不展示「中文译文」副栏），只显简体单栏
        if platform == "drnh":
            strict_page = bool(
                int(row["citation_ready"] or 0) == 1
                and int(row["needs_human_review"] or 0) == 0
                and str(row["provenance_review_status"] or "") == "human_verified"
                and str(row["human_review_note"] or "").strip()
            )
            page_citation_label = "正式可引用" if strict_page else "不可直接引用"
            img_url = None
            seg_img = None
            if cached_images:
                # cached_images 为数据库行（含 page_num / file_path）
                m_lbl = re.search(r"\d+", str(row['page_label'] or '').strip())
                if m_lbl:
                    for img in cached_images:
                        if str(img['page_num']) == str(m_lbl.group(0)):
                            seg_img = img
                            break
                if seg_img is None and idx < len(cached_images):
                    seg_img = cached_images[idx]
                if seg_img is not None:
                    fname = Path(seg_img['file_path']).name
                    img_url = f"/drnh-img/{quote(doc['doc_key'])}/{fname}"
            # 段落锚点编号：有图用图片页码，无图用序号——保证胶片导航栏锚点可跳转
            seg_anchor = seg_img['page_num'] if seg_img is not None else (idx + 1)

            # 摘要卡片：仅台北档案中「有访客水印图」且已生成案由摘要的档案才展示，
            # 每篇只在首段出现一次；内容据档案案由机器整理，明确标注待人工校订
            summary_html = ""
            drnh_sum = (doc["drnh_summary"] or "").strip() if has_watermark_img and "drnh_summary" in doc.keys() else ""
            if drnh_sum and idx == 0:
                summary_html = f"""
      <div class="drnh-academic-divider">
        <span class="line"></span>
        <span class="ornament">❈ ❈ ❈</span>
        <span class="line"></span>
      </div>
      <div class="drnh-academic-card">
        <div class="drnh-summary-title">
          <svg class="ico"><use href="#i-quote"/></svg>
          档案内容提要
        </div>
        <div class="drnh-summary-text">{h(drnh_sum)}</div>
        <div class="drnh-summary-footer">
          据台北档案史料案由整理 · 机器初拟，待人工校订
        </div>
      </div>"""

            pane_cls = "drnh-academic-pane selected-pane" if selected else "drnh-academic-pane"
            
            if img_url:
                body += f"""
  <div class="drnh-page-segment-container" id="page-{seg_anchor}"{selected}>
    <div class="drnh-workspace-row">
      <div class="drnh-archive-image-col">
        <figure class="drnh-image-figure">
          <a href="{img_url}" target="_blank" title="查看国史馆官方访客预览（不可直接引用）">
            <img class="drnh-archive-image" src="{img_url}" loading="lazy" />
          </a>
          <figcaption class="drnh-image-caption">国史馆官方访客预览 · 第 {h(row['page_label'])} 页 · {page_citation_label}</figcaption>
        </figure>
      </div>
      <div class="drnh-transcription-col">
        <article class="{pane_cls}">
          <div class="drnh-pane-header">
            <span class="drnh-academic-badge">✦ 目录卡片（非正文） · {h(page)} · {page_citation_label}</span>
            <span class="drnh-actions">
              <a href="/cite/{h(row["page_id"])}">{('引用卡片' if strict_page else '引用门禁（未通过）')}</a> ·
              <a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">国史馆来源入口</a>
            </span>
          </div>
          <div class="drnh-pane-body">
            <div class="notice">该页为国史馆官方访客影像的页级预览；下方仅显示本库目录卡片，不是原件正文转录。</div>
            <div class="drnh-original-text">{h(row["original_text"])}</div>
          </div>
        </article>
      </div>
    </div>
    {summary_html}
  </div>"""
            else:
                body += f"""
  <div class="drnh-page-segment-container" id="page-{seg_anchor}"{selected}>
    <article class="{pane_cls}" style="width: 100%;">
      <div class="drnh-pane-header">
        <span class="drnh-academic-badge">✦ 目录卡片（非正文） · {h(page)} · {page_citation_label}</span>
        <span class="drnh-actions">
          <a href="/cite/{h(row["page_id"])}">{('引用卡片' if strict_page else '引用门禁（未通过）')}</a> ·
          <a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">国史馆来源入口</a>
        </span>
      </div>
      <div class="drnh-pane-body">
        <div class="notice">当前没有绑定页级影像；下方内容仅为目录卡片，不是原件正文转录。</div>
        <div class="drnh-original-text">{h(row["original_text"])}</div>
      </div>
    </article>
    {summary_html}
  </div>"""
        else:
            original_text = row["original_text"] or ""
            display_original = original_text
            original_note = ""
            if platform == "newspapersg":
                clean_text = newspapersg_clean_text(doc["doc_key"])
                if clean_text:
                    display_original = clean_text
                    original_note = (
                        '<details class="notice" style="margin-top:12px;">'
                        '<summary>查看原始 OCR 噪声文本</summary>'
                        f'<pre style="white-space:pre-wrap;margin-top:10px;">{h(original_text)}</pre>'
                        '</details>'
                    )
            domestic_page_status = ""
            domestic_page_action = "摘录卡片"
            if platform == "domestic":
                strict_page = bool(
                    int(row["citation_ready"] or 0) == 1
                    and int(row["needs_human_review"] or 0) == 0
                    and str(row["provenance_review_status"] or "") == "human_verified"
                    and str(row["human_review_note"] or "").strip()
                )
                anchored_page = bool(
                    str(row["provenance_source_file"] or "").strip()
                    and re.fullmatch(r"[0-9a-fA-F]{64}", str(row["provenance_source_sha256"] or ""))
                )
                domestic_page_status = (
                    "正式可引用"
                    if strict_page
                    else "原件已锚定 · 待复核"
                    if anchored_page
                    else "不可直接引用"
                )
                domestic_page_action = "引用卡片" if strict_page else "引用门禁（未通过）"
            body += f"""
  <div class="segment">
    <article class="pane"{selected}>
      <div class="pane-head"><span>{'清洗 OCR · ' if platform == "newspapersg" else '原文 · '}{h(page)}{f' · <strong>{h(domestic_page_status)}</strong>' if domestic_page_status else ''}</span><span><a href="/cite/{h(row["page_id"])}">{domestic_page_action}</a> · <a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">{source_label}</a></span></div>
      <div class="pane-body">{h(display_original)}{original_note}</div>
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
    if platform == "drnh":
        # 重新获取图片以生成导航栏
        filmstrip_items = ""
        for img in cached_images:
            thumb_url = f"/drnh-img/{quote(doc['doc_key'])}/{Path(img['file_path']).name}"
            filmstrip_items += f'''
            <a href="#page-{img['page_num']}" class="drnh-thumb" title="第 {img['page_num']} 页">
                <img src="{thumb_url}" loading="lazy" />
                <span>{img['page_num']}</span>
            </a>'''
        
        # 配图先不展示：无缩略图时不输出空的胶片导航栏
        filmstrip_block = f'<div class="drnh-filmstrip">{filmstrip_items}</div>' if filmstrip_items.strip() else ''
        body = f"""<div class="drnh-layout-wrapper">
{filmstrip_block}
<style>
.drnh-filmstrip {{
    display: flex;
    gap: 8px;
    overflow-x: auto;
    padding: 16px;
    background: #fbf7ee;
    border-bottom: 1px solid #e6dec9;
    margin-bottom: 24px;
    scroll-behavior: smooth;
}}
.drnh-thumb {{
    flex: 0 0 80px;
    text-align: center;
    text-decoration: none;
    color: #8c2d19;
    font-size: 12px;
}}
.drnh-thumb img {{
    width: 80px;
    height: 100px;
    object-fit: cover;
    border: 1px solid #e6dec9;
    border-radius: 4px;
}}
.drnh-thumb:hover img {{ border-color: #8c2d19; }}

.drnh-layout-wrapper {{
    max-width: 100%;
    margin: 0 auto;
}}
.reader.reader-drnh {{
    display: flex !important;
    flex-direction: column !important;
    gap: 40px !important;
    margin-top: 24px !important;
}}
.drnh-page-segment-container {{
    display: block !important;
    margin-bottom: 48px;
    scroll-margin-top: 160px;
    width: 100%;
}}
.drnh-workspace-row {{
    display: flex;
    gap: 24px;
    margin-bottom: 24px;
    align-items: stretch;
}}
@media (max-width: 900px) {{
    .drnh-workspace-row {{
        flex-direction: column;
    }}
}}
.drnh-archive-image-col {{
    flex: 0 0 45%;
    min-width: 0;
}}
.drnh-transcription-col {{
    flex: 0 0 55%;
    min-width: 0;
    display: flex;
    flex-direction: column;
}}
@media (max-width: 900px) {{
    .drnh-archive-image-col, .drnh-transcription-col {{
        flex: 1 1 auto;
        width: 100%;
    }}
}}
.drnh-image-figure {{
    margin: 0;
    padding: 16px;
    background: #fbf7ee;
    border: 1px solid #e6dec9;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgba(42, 40, 32, 0.04);
    text-align: center;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
}}
.drnh-archive-image {{
    max-width: 100%;
    height: auto;
    max-height: 700px;
    object-fit: contain;
    border: 1px solid #e6dec9;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(42, 40, 32, 0.08);
    background: #fff;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    display: inline-block;
}}
.drnh-archive-image:hover {{
    transform: scale(1.015);
    box-shadow: 0 8px 24px rgba(42, 40, 32, 0.14);
}}
.drnh-image-caption {{
    font-size: 13px;
    color: #8b5e34;
    font-family: var(--serif);
    margin-top: 12px;
    font-weight: 600;
}}
.drnh-academic-pane {{
    background: #fdfbf6 !important;
    border: 1px solid #e6dec9 !important;
    border-radius: 14px !important;
    box-shadow: 0 12px 36px rgba(42, 40, 32, 0.05), 0 2px 6px rgba(42, 40, 32, 0.02) !important;
    overflow: hidden;
    height: 100%;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    margin-bottom: 0;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
.drnh-academic-pane:hover {{
    transform: translateY(-2px);
    box-shadow: 0 16px 48px rgba(42, 40, 32, 0.07), 0 3px 8px rgba(42, 40, 32, 0.03) !important;
}}
.drnh-academic-pane.selected-pane {{
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px rgba(15, 107, 91, 0.08) !important;
}}
.drnh-pane-header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
    padding: 14px 24px;
    border-bottom: 1px solid #ece6d6;
    background: #fbf7ee;
}}
.drnh-academic-badge {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #8b5e34;
    font-family: var(--serif);
    font-weight: 600;
    font-size: 14px;
    letter-spacing: 0.04em;
}}
.drnh-actions {{
    font-size: 13px;
    font-family: var(--sans);
}}
.drnh-actions a {{
    color: var(--accent);
    opacity: 0.85;
    transition: opacity 0.15s, color 0.15s;
}}
.drnh-actions a:hover {{
    opacity: 1;
    color: var(--accent-deep);
    text-decoration: underline;
}}
.drnh-pane-body {{
    padding: 28px 32px;
    flex: 1;
    display: flex;
    flex-direction: column;
}}
.drnh-original-text {{
    font-family: var(--serif);
    font-size: 18.5px;
    line-height: 1.9;
    color: #2a2820;
    font-weight: 500;
    border-left: 4px solid var(--accent);
    padding-left: 18px;
    margin-bottom: 0;
    word-break: break-all;
    text-align: justify;
    text-justify: inter-word;
    text-wrap: pretty;
    letter-spacing: 0.03em;
    flex: 1;
}}

/* Elegant Notice Card at top */
.drnh-archive-notice {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 18px 0 24px;
    padding: 16px 20px;
    background: #fdfbf7;
    border: 1px solid #e3dac3;
    border-left: 4px solid #8b5e34;
    border-radius: 10px;
    box-shadow: 0 4px 12px rgba(42, 40, 32, 0.03);
    font-size: 14px;
    color: #5c5545;
    line-height: 1.5;
}}
.drnh-archive-notice svg {{
    width: 20px;
    height: 20px;
    fill: #8b5e34;
    flex-shrink: 0;
}}
.drnh-archive-notice a {{
    color: var(--accent);
    font-weight: 600;
    text-decoration: none;
}}
.drnh-archive-notice a:hover {{
    text-decoration: underline;
}}

/* Beautiful Ornate Divider */
.drnh-academic-divider {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    margin: 24px 0;
    user-select: none;
}}
.drnh-academic-divider .line {{
    flex: 1;
    height: 1px;
    background: linear-gradient(to right, transparent, #d9d2bf 30%, #d9d2bf 70%, transparent);
}}
.drnh-academic-divider .ornament {{
    color: #bba677;
    font-size: 14px;
    letter-spacing: 6px;
    font-family: var(--serif);
}}

/* Outstanding Academic Summary Card */
.drnh-academic-card {{
    background: linear-gradient(135deg, #fdfbf7 0%, #f7f3e8 100%) !important;
    border: 1px solid #e3dac3 !important;
    border-left: 5px solid #8c2d19 !important;
    border-radius: 12px !important;
    padding: 24px 28px 20px !important;
    box-shadow: 0 8px 24px rgba(140, 45, 25, 0.04), 0 1px 3px rgba(140, 45, 25, 0.01) !important;
    position: relative;
    overflow: hidden;
    width: 100%;
    box-sizing: border-box;
}}
.drnh-academic-card::after {{
    content: "”";
    position: absolute;
    right: 20px;
    bottom: -10px;
    font-family: var(--serif);
    font-size: 140px;
    color: rgba(140, 45, 25, 0.03);
    line-height: 1;
    pointer-events: none;
    font-weight: 900;
}}
.drnh-summary-title {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    color: #8c2d19;
    font-family: var(--serif);
    font-size: 16.5px;
    margin-bottom: 14px;
    letter-spacing: 0.05em;
}}
.drnh-summary-title svg {{
    width: 16px;
    height: 16px;
    fill: currentColor;
}}
.drnh-summary-text {{
    font-family: var(--serif);
    font-size: 16.2px;
    line-height: 1.85;
    color: #3d382e;
    text-align: justify;
    text-justify: inter-word;
    text-wrap: pretty;
    letter-spacing: 0.02em;
}}
.drnh-summary-footer {{
    text-align: center;
    font-size: 12.5px;
    color: #8a806d;
    margin-top: 20px;
    font-family: var(--serif);
    letter-spacing: 0.08em;
    border-top: 1px dashed rgba(227, 218, 195, 0.6);
    padding-top: 14px;
    font-weight: 500;
}}
</style>
{body}
</div>"""
    return layout(translate_title(doc["title"]), body)


def docs(active_grade: str = "", active_translation: str = "", platform: str = "") -> bytes:
    with conn() as c:
        where_parts = []
        params: list[str] = []
        # 前台默认过滤 grade='前台不展示' 的档案
        where_parts.append("(dc.grade IS NULL OR dc.grade != '前台不展示')")
        # drnh 平台默认只显示 A 档核心（用户要求「只留民盟有关系的最重要的史料」）
        # 用户可加 ?grade=B 主动看背景档
        effective_grade = active_grade
        if platform == "drnh" and not active_grade:
            effective_grade = "A"
        if effective_grade:
            where_parts.append("dc.grade = ?")
            params.append(effective_grade)
        if active_translation == "translated":
            where_parts.append("translation_stats.translated_pages > 0")
        elif active_translation == "missing":
            where_parts.append("(translation_stats.translated_pages IS NULL OR translation_stats.translated_pages < translation_stats.total_pages)")
        if platform:
            where_parts.append("COALESCE(documents.source_platform, 'frus') = ?")
            params.append(platform)
        where = ("WHERE " + " AND ".join(where_parts)) if where_parts else ""
        # drnh 平台按时间线（本件日期）排序；其他平台保持 volume_id 排序
        order_by = (
            "ORDER BY documents.date_guess, documents.doc_id"
            if platform == "drnh"
            else "ORDER BY documents.volume_id, CAST(documents.doc_number AS INTEGER)"
        )
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
            {order_by}
            """,
            tuple(params),
        ).fetchall()
    # 平台显示名（用于面包屑和标题）
    plat_name = ""
    if platform:
        plat_meta = PLATFORM_META.get(platform, {})
        plat_name = plat_meta.get("name", platform)
        body = breadcrumb_html([("/", "首页"), (f"/sources/{platform}", plat_name), (None, "全部文档")])
        body += f'<h1 style="font-size:22px;margin:0 0 12px;">{h(plat_name)} · 全部文档（共 {len(rows)} 篇）</h1>'
    else:
        body = breadcrumb_html([("/", "首页"), (None, "全部文档")])
    body += grade_filters(active_grade, active_translation)
    body += grade_legend_html()
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
    glossary_path = DATA_ROOT / "translation_glossary.csv"
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
        severe_count = c.execute("SELECT count(*) FROM translation_quality_issues WHERE severity >= 3").fetchone()[0]
        high_count = c.execute("SELECT count(*) FROM translation_quality_issues WHERE severity = 2").fetchone()[0]
        low_count = c.execute("SELECT count(*) FROM translation_quality_issues WHERE severity = 1").fetchone()[0]
        low_english = c.execute(
            "SELECT count(*) FROM translation_quality_issues WHERE severity = 1 AND issue_type='english_residue'"
        ).fetchone()[0]
        low_length = c.execute(
            "SELECT count(*) FROM translation_quality_issues WHERE severity = 1 AND issue_type='length_long'"
        ).fetchone()[0]
        core_issue_pages = c.execute(
            """
            SELECT count(DISTINCT q.page_id)
            FROM translation_quality_issues q
            JOIN pages p ON p.id=q.page_id
            JOIN documents d ON d.id=p.document_id
            LEFT JOIN document_classifications dc ON dc.document_id=d.id
            WHERE COALESCE(dc.grade, '')='核心文献'
            """
        ).fetchone()[0]

    if severe_count:
        triage_status = "有严重问题，需要先处理"
        triage_detail = f"当前仍有 {severe_count} 个严重质量提示，应先处理缺译、已知误译或明显短译。"
        triage_class = "risk-high"
    elif high_count:
        triage_status = "有高优先级问题"
        triage_detail = f"当前仍有 {high_count} 个需要检查的提示，应优先处理术语、短译和密集英文残留。"
        triage_class = "risk-warn"
    else:
        triage_status = "高优先级已清零"
        triage_detail = "剩余提示均为低优先级，主要是 OCR 噪声、馆藏元数据或译文长度偏长提醒。"
        triage_class = "risk-ok"

    body = f"""
<section class="doc-head">
  <div>
    <h1>译文质量检查</h1>
    <div class="meta">有提示的片段 {distinct_pages} 个；高优先级片段 {high_pages} 个。列表只显示前 250 条，优先处理严重度高、核心文献和术语问题。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/docs">返回文档</a>
    <a class="button" href="/tasks">任务队列</a>
    <a class="button" href="/dashboard">仪表盘</a>
  </div>
</section>
<section class="quality-triage">
  <article class="triage-card {triage_class}">
    <div class="triage-label">当前状态</div>
    <strong>{h(triage_status)}</strong>
    <p>{h(triage_detail)}</p>
  </article>
  <article class="triage-card">
    <div class="triage-label">剩余低风险</div>
    <strong>{h(low_count)}</strong>
    <p>英文/OCR 残留 {h(low_english)} 个，长度偏长提示 {h(low_length)} 个。</p>
  </article>
  <article class="triage-card">
    <div class="triage-label">核心文献影响</div>
    <strong>{h(core_issue_pages)}</strong>
    <p>仍有提示的核心文献片段。建议下一轮只抽查核心文献和高引用价值页。</p>
  </article>
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
  <div class="cite"><a href="{h(review_href)}">打开校订</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">原始来源</a></div>
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
                COALESCE(documents.source_platform, 'frus') AS platform,
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
  <div class="cite"><a href="{h(review_href)}">校订</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">原始来源</a></div>
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

    body = breadcrumb_html([("/", "首页"), (None, "人物索引")])
    body += f"""
<section class="doc-head">
  <div>
    <h1>民盟人物索引</h1>
    <div class="meta">
      共 <b>{len(PEOPLE)}</b> 位民盟相关人物，其中 <b>{total_hit_persons}</b> 位在档案中已有命中（覆盖 {total_docs} 篇文档 / {total_pages} 个片段）。
      下方按档案命中数倒序排列，无命中人物排在最后。点击姓名查看该人物所有原文、译文、来源链接和事件年表。
    </div>
    <div class="meta" style="margin-top:6px;color:var(--muted-soft);font-size:13px;">
      本平台只收录 <b>中国大陆境外一手原始档案</b>（FRUS / CIA / Wilson / Hoover / HathiTrust / 台北档案史料 / NewspaperSG 七大档案源）。
      下方人物索引是档案翻译过程中用于规范人名、提供历史上下文的内部研究编排，<b>不构成资料库收录内容</b>。
    </div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/tasks?queue=people">人物校订任务</a>
    <a class="button" href="/timeline">人物年表</a>
  </div>
</section>
"""

    # 单列按命中数倒序（无命中的按 slug 字母序排末尾）
    all_people = sorted(
        PEOPLE,
        key=lambda p: (
            -(stats[p["slug"]]["page_count"] or 0),
            -(stats[p["slug"]]["doc_count"] or 0),
            p["slug"],
        ),
    )
    body += '<section class="result-list">'
    for person in all_people:
        row = stats[person["slug"]]
        doc_count = row["doc_count"] or 0
        page_count = row["page_count"] or 0
        core_hits = row["core_hits"] or 0
        no_hit_cls = "" if doc_count > 0 else ' style="opacity:.6;"'
        hit_meta = (
            f'{doc_count} 篇文档 · {page_count} 个片段 · 核心命中 {core_hits}'
            if doc_count > 0
            else '<span style="color:var(--muted-soft);">档案中暂无命中</span>'
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
                COALESCE(documents.source_platform, 'frus') AS platform,
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
        body += f"""
<section class="doc-head" style="background:var(--panel-warm);border-left:4px solid var(--accent);margin-bottom:16px;">
  <div style="max-width:none;">
    <div class="meta" style="color:var(--accent-deep);font-size:13px;letter-spacing:.05em;text-transform:uppercase;margin-bottom:6px;">
      人物档案
    </div>
    <div style="font-family:var(--serif);font-size:16px;line-height:1.8;color:var(--text);">{h(profile_text)}</div>
    <div class="meta" style="margin-top:10px;font-size:12.5px;color:var(--muted-soft);">
      本卡为内部研究编排参考，便于理解下方档案译文的人物上下文；
      本平台资料库本身只收录 <b>中国大陆境外一手原始档案</b>（FRUS / CIA / Wilson / Hoover / HathiTrust / 台北档案史料 / NewspaperSG 七大档案源）。
    </div>
  </div>
</section>
"""
    body += person_archive_panel(person, rows)
    if not rows:
        body += '<div class="notice">FRUS 档案中暂无命中。可切换查看 CIA / Wilson / Hoover / HathiTrust / 台北档案史料 五个境外档案源。</div>'
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
  <div class="cite"><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">原始来源</a></div>
</article>"""
        body += "</section>"
    return layout(str(person["name"]), body)


def topics() -> bytes:
    """/topics 路由已废弃 — 按民盟事件主题的专题分类已不再使用，重定向到 /people 人物索引。"""
    return layout(
        "已迁移到人物索引",
        '<section class="doc-head"><div><h1>专题分类已合并到人物索引</h1>'
        '<div class="meta">本站不再按民盟事件主题（如政协、马歇尔调处、第三方面等）做分类页面，'
        '所有档案的导航统一通过 <a href="/people">人物索引</a> 完成。</div></div>'
        '<div class="doc-tools"><a class="button" href="/people">前往人物索引 →</a></div></section>'
    )


# ============================================================
# 七篇学术论文展示 (/papers, /papers/<key>) — 5/26 19:50 新增
# ============================================================

PAPERS = [
    ("transnational-1947", "史论 · 被取缔的跨国政党（1947 民盟非法化）",
     "FRUS＋DRNH＋Hoover＋HathiTrust＋NewspaperSG 五源 / 决策先于宣布 · 美援杠杆 · 海外分部不同步回应 / 用档案讲史",
     "docs/_paper-1947-transnational.md", "i-globe", "/papers/transnational-1947", "paper"),
    # 第一组：七源平台学术综述 + 总论（9 篇，含 v1 历史版本与 v2 当前版本）
    ("overview-v2", "七源对照档案体系（总论 v2）",
     "1941-1950 中国民盟史 · 纳入 NewspaperSG 形成七源研究框架 · 2026-06-03",
     "docs/_seven-source-overview-paper-v2.md", "i-library", "/papers/overview-v2", "paper"),
    ("overview", "六源对照档案体系（总论 v1，历史版本）",
     "1941-1950 中国民盟史 · v1 历史版本 · 2026-05-26（保留供研究比对）",
     "docs/_overview-paper.md", "i-library", "/papers/overview", "paper"),
    ("frus", "美方公开外交基准源 · FRUS",
     "11 分卷 / 273 篇直接命中精读 / 罗隆基 62 次为人物之首 / v3 史学叙事版",
     "docs/_frus-paper.md", "i-globe", "/papers/frus", "paper"),
    ("drnh", "国民政府打压方内部档案 · DRNH",
     "282 篇精读 / 124 核心 + 38 保密局呈件 / 1947-10-23 蒋作战会报亲自决策档",
     "docs/_drnh-paper.md", "i-archive", "/papers/drnh", "paper"),
    ("cia", "美方解密情报系统 · CIA",
     "76 篇（剔 26 后）human-reviewed / 民盟海外网络独有档案 / 1949-05 上海撤离档",
     "docs/_cia-paper.md", "i-lock", "/papers/cia", "paper"),
    ("hathitrust", "港埠公开舆论场 · HathiTrust / IA",
     "54 期 China Mail + Hong Kong Telegraph / 1947 民盟「非法」5 期连续报道",
     "docs/_hathitrust-paper.md", "i-book", "/papers/hathitrust", "paper"),
    ("wilson", "苏方与东欧档案 · Wilson Center",
     "24 篇 / wilson:134160 RGASPI 斯大林档新政协民主党派系统报告",
     "docs/_wilson-paper.md", "i-flag", "/papers/wilson", "paper"),
    ("hoover", "民盟创始人致美方私函 · Hoover Institution",
     "张君劢致 Wedemeyer + Marshall 两函 L1 级 / 1947-11 民盟非法化四源对位",
     "docs/_hoover-paper.md", "i-quote", "/papers/hoover", "paper"),
    ("newspapersg", "南洋报刊舆论场 · NewspaperSG",
     "93 篇南洋商报与英文报刊 OCR / 新加坡分部、雪兰莪分部、1947 与 1949 非法化双线",
     "docs/_newspapersg-paper.md", "i-book", "/papers/newspapersg", "paper"),
    # 第二组：六卷待核问题与证据等级清单（社科院方法论实践，6 份）
    ("frus-review", "FRUS 卷 · 待核问题与证据等级清单",
     "4 篇 ⭐ 关键档案 L1 优先 / 4 类单源孤证 / 12 位民盟人物待补 / 论文 v3 中 7 处判断层自查",
     "docs/_frus-待核问题与证据等级清单.md", "i-tag", "/papers/frus-review", "review"),
    ("drnh-review", "DRNH 卷 · 待核问题与证据等级清单",
     "9 篇 LLM 自评误命中分组处置 / 5 类时间冲突待互证 / 「民主同盟」概念 4 重所指方法学说明",
     "docs/_drnh-待核问题与证据等级清单.md", "i-tag", "/papers/drnh-review", "review"),
    ("cia-review", "CIA 卷 · 待核问题与证据等级清单",
     "4 篇 ⭐ 关键档案 L1 优先 / 1949 罗隆基「被囚禁」vs FRUS「新政权要职」反向陈述核验",
     "docs/_cia-待核问题与证据等级清单.md", "i-tag", "/papers/cia-review", "review"),
    ("hathitrust-review", "HathiTrust 卷 · 待核问题与证据等级清单",
     "16 期「空」分两类（真无相关 vs 关键词漏报）/ 6 个关键词遗漏候选 / 港媒立场转变机制",
     "docs/_hathitrust-待核问题与证据等级清单.md", "i-tag", "/papers/hathitrust-review", "review"),
    ("wilson-review", "Wilson 卷 · 待核问题与证据等级清单",
     "wilson:134160 RGASPI 斯大林档 L1 优先 / 革命民主同盟 vs 中国民主同盟术语核 / 双道翻译限制",
     "docs/_wilson-待核问题与证据等级清单.md", "i-tag", "/papers/wilson-review", "review"),
    ("hoover-review", "Hoover 卷 · 待核问题与证据等级清单（精简版）",
     "2 件已 L1 / Box 13—14 全宗补查清单 / 张君劢「双重身份」问题 / 1947-11-01 函因果待 NARA 补",
     "docs/_hoover-待核问题与证据等级清单.md", "i-tag", "/papers/hoover-review", "review"),
    # 第三组：跨源事件证据卡片（社科院方法论第 2 条「互证优先」实践，7 份）
    ("evidence-1947-10", "证据卡片 001 · 1947-10 民盟「非法化」事件",
     "DRNH + Hoover + HathiTrust + FRUS 四源 / 17 张时点卡片 / 民盟史多源最完整覆盖案例",
     "docs/_evidence-card-1947-10-民盟非法化.md", "i-archive", "/papers/evidence-1947-10", "evidence"),
    ("evidence-1946-05", "证据卡片 002 · 1946-05 广西取缔民盟事件",
     "DRNH 国府内部档案孤证事件 / 10 张时点卡片 / 蒋本人 5 件连续电令链 + 同日反差档案",
     "docs/_evidence-card-1946-05-广西取缔民盟.md", "i-archive", "/papers/evidence-1946-05", "evidence"),
    ("evidence-1945-07", "证据卡片 003 · 1945-07 民盟代表团访延安事件",
     "DRNH 7 篇 + FRUS 3 篇双源对位完整 / 7 张时点卡片 / 戴笠+钱大钧同日双线呈报",
     "docs/_evidence-card-1945-07-民盟代表团访延安.md", "i-archive", "/papers/evidence-1945-07", "evidence"),
    ("evidence-newspapersg-1946-quit-china-week", "证据卡片 004 · 1946 南洋反内战与 Quit China Week",
     "NewspaperSG + CIA + FRUS 对照 / 新加坡华人反内战、要求美军撤出中国与民盟海外动员",
     "docs/_evidence-card-newspapersg-1946-quit-china-week.md", "i-archive", "/papers/evidence-newspapersg-1946-quit-china-week", "evidence"),
    ("evidence-newspapersg-1947-outlawed", "证据卡片 005 · 1947 民盟非法化的南洋报刊反应",
     "NewspaperSG + FRUS + DRNH + HathiTrust + Hoover 对照 / 民盟被禁、上海总部与海外反应",
     "docs/_evidence-card-newspapersg-1947-outlawed.md", "i-archive", "/papers/evidence-newspapersg-1947-outlawed", "evidence"),
    ("evidence-newspapersg-overseas-branches", "证据卡片 006 · 1947-1949 海外民盟继续活动",
     "泛马来亚总部、香港节点、新加坡分部继续活动 / 与 CIA、HKPRO、HathiTrust 互证",
     "docs/_evidence-card-newspapersg-1947-1949-overseas-branches.md", "i-archive", "/papers/evidence-newspapersg-overseas-branches", "evidence"),
    ("evidence-newspapersg-1949-malayan-ban", "证据卡片 007 · 1949 新加坡/马来亚宣布中国民主同盟非法",
     "英殖民地政府撤销豁免、宣布非法、警方搜查 / 与 CIA、HKPRO、FRUS 互证",
     "docs/_evidence-card-newspapersg-1949-malayan-ban.md", "i-archive", "/papers/evidence-newspapersg-1949-malayan-ban", "evidence"),
]


CITATION_PATTERNS = [
    r"\bfrus\d{4}[A-Za-z0-9]*/d\d+\b",
    r"\b(?:cia-meng|wilson|hoover|hathi-ia|drnh):[A-Za-z0-9_.:/-]+\b",
    r"\bcia-rdp[0-9a-z-]+\b",
    r"\br[0-9]{4}[0-9a-z-]+\b",
]


def paper_cited_doc_keys_from_markdown(c: sqlite3.Connection, md: str) -> list[str]:
    candidates: list[str] = []
    for pattern in CITATION_PATTERNS:
        candidates.extend(re.findall(pattern, md, flags=re.IGNORECASE))

    resolved: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        token = raw.strip().rstrip(").,;，。；")
        lower = token.lower()
        doc_key = ""
        if lower.startswith("frus"):
            doc_key = token
        elif lower.startswith(("wilson:", "hoover:", "hathi-ia:", "drnh:", "cia-meng:")):
            doc_key = token
        elif lower.startswith("cia-rdp"):
            doc_key = "cia-meng:" + lower
        elif lower.startswith("r"):
            row = c.execute(
                """
                SELECT doc_key FROM documents
                WHERE source_platform='cia'
                  AND lower(doc_key) LIKE ?
                ORDER BY length(doc_key)
                LIMIT 1
                """,
                (f"%{lower}",),
            ).fetchone()
            doc_key = row["doc_key"] if row else ""
        if not doc_key or doc_key.lower() in seen:
            continue
        row = c.execute(
            """
            SELECT doc_key FROM documents
            WHERE doc_key=? OR lower(doc_key)=lower(?)
            LIMIT 1
            """,
            (doc_key, doc_key),
        ).fetchone()
        if row and row["doc_key"].lower() not in seen:
            resolved.append(row["doc_key"])
            seen.add(row["doc_key"].lower())
    return resolved


def paper_cited_doc_keys(c: sqlite3.Connection, key: str = "") -> list[str]:
    targets = [p for p in PAPERS if p[0] != "overview" and (not key or p[0] == key)]
    resolved: list[str] = []
    seen: set[str] = set()
    for p in targets:
        path = p[3]
        fpath = ROOT / path
        if not fpath.exists():
            continue
        for doc_key in paper_cited_doc_keys_from_markdown(c, fpath.read_text(encoding="utf-8")):
            if doc_key.lower() in seen:
                continue
            resolved.append(doc_key)
            seen.add(doc_key.lower())
    return resolved


def render_markdown(md: str) -> str:
    """轻量 markdown → HTML 渲染（针对论文格式）。"""
    lines = md.split("\n")
    out = []
    i = 0
    in_table = False
    in_codeblock = False
    in_list = False
    in_blockquote = False

    def inline(text):
        # 转 HTML entity（先转 & 防止后面替换坏掉）
        t = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        # 行内代码 `code`
        t = re.sub(r"`([^`]+?)`", lambda m_: f"<code>{m_.group(1)}</code>", t)
        # 加粗 **text**
        t = re.sub(r"\*\*([^*]+?)\*\*", lambda m_: f"<strong>{m_.group(1)}</strong>", t)
        # 链接 [text](url)
        t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", lambda m_: f'<a href="{m_.group(2)}">{m_.group(1)}</a>', t)
        return t

    while i < len(lines):
        line = lines[i]
        # 代码块
        if line.startswith("```"):
            if in_codeblock:
                out.append("</pre>")
                in_codeblock = False
            else:
                if in_list: out.append("</ul>"); in_list = False
                out.append('<pre class="md-code">')
                in_codeblock = True
            i += 1; continue
        if in_codeblock:
            out.append(line.replace("<","&lt;").replace(">","&gt;"))
            i += 1; continue

        # 表格（连续含 | 的行）
        if "|" in line and not line.startswith("|") is False and "|" in line.strip().strip("|"):
            # 启发式：看下行是不是分隔行 |---|---|
            if not in_table:
                if i+1 < len(lines) and re.match(r"^\s*\|?[\s\-:|]+\|?\s*$", lines[i+1]):
                    # 开表头
                    if in_list: out.append("</ul>"); in_list = False
                    cells = [c.strip() for c in line.strip().strip("|").split("|")]
                    out.append("<table class='md-table'><thead><tr>")
                    for c in cells: out.append(f"<th>{inline(c)}</th>")
                    out.append("</tr></thead><tbody>")
                    in_table = True
                    i += 2; continue
            else:
                cells = [c.strip() for c in line.strip().strip("|").split("|")]
                out.append("<tr>")
                for c in cells: out.append(f"<td>{inline(c)}</td>")
                out.append("</tr>")
                i += 1; continue
        if in_table:
            out.append("</tbody></table>")
            in_table = False

        # 标题
        m_h = re.match(r"^(#{1,6})\s+(.+)$", line)
        if m_h:
            if in_list: out.append("</ul>"); in_list = False
            lvl = len(m_h.group(1))
            out.append(f"<h{lvl} class='md-h{lvl}'>{inline(m_h.group(2))}</h{lvl}>")
            i += 1; continue

        # 引用
        if line.startswith("> "):
            if in_list: out.append("</ul>"); in_list = False
            if not in_blockquote:
                out.append("<blockquote class='md-quote'>")
                in_blockquote = True
            out.append(f"<p>{inline(line[2:])}</p>")
            i += 1; continue
        else:
            if in_blockquote:
                out.append("</blockquote>")
                in_blockquote = False

        # 列表项
        m_li = re.match(r"^[-*]\s+(.+)$", line)
        if m_li:
            if not in_list:
                out.append("<ul class='md-list'>")
                in_list = True
            out.append(f"<li>{inline(m_li.group(1))}</li>")
            i += 1; continue
        else:
            if in_list:
                out.append("</ul>")
                in_list = False

        # 水平分割
        if re.match(r"^---+$", line.strip()):
            out.append("<hr class='md-hr'>")
            i += 1; continue

        # 空行
        if not line.strip():
            i += 1; continue

        # 普通段落
        out.append(f"<p>{inline(line)}</p>")
        i += 1

    if in_list: out.append("</ul>")
    if in_blockquote: out.append("</blockquote>")
    if in_table: out.append("</tbody></table>")
    return "\n".join(out)


def paper_cited_docs_html(key: str, md: str) -> str:
    """Build a compact cited-document panel for paper pages."""
    if key == "overview":
        return ""

    with conn() as c:
        resolved = paper_cited_doc_keys_from_markdown(c, md)
        if not resolved:
            return ""
        placeholders = ",".join("?" for _ in resolved)
        rows = c.execute(
            f"""
            SELECT documents.doc_key, documents.title, documents.date_guess,
                   COALESCE(dc.grade, '') AS grade,
                   (SELECT pages.id FROM pages WHERE pages.document_id=documents.id ORDER BY pages.id LIMIT 1) AS page_id
            FROM documents
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            WHERE documents.doc_key IN ({placeholders})
            """,
            resolved,
        ).fetchall()

    by_key = {row["doc_key"]: row for row in rows}
    items = []
    for doc_key in resolved[:24]:
        row = by_key.get(doc_key)
        if not row:
            continue
        href = "/doc/" + quote(doc_key, safe=":/")
        cite_href = f'/cite/{row["page_id"]}' if row["page_id"] else href
        items.append(
            f"""
<article class="result compact-result">
  <div>
    <h3><a href="{h(href)}">{h(row["title"] or doc_key)}</a></h3>
    <div class="meta">{h(doc_key)} · {h(row["date_guess"] or "日期未注明")} · {h(row["grade"] or "未分级")}</div>
  </div>
  <div class="cite"><a href="{h(cite_href)}">引用卡片</a></div>
</article>"""
        )
    if not items:
        return ""
    more = "" if len(resolved) <= 24 else f'<p class="meta">已显示前 24 篇，本文共识别 {len(resolved)} 个可点击原档引用。</p>'
    return f"""
<section class="paper-citations">
  <h2 class="md-h2">本文引用的原始档案</h2>
  <div class="meta">从论文正文自动识别 doc_key，并链接到本库中英对照原档与引用卡片。</div>
  <div class="result-list compact-list">{''.join(items)}</div>
  {more}
</section>
"""


def paper_backlinks_html(doc_key: str) -> str:
    matches = []
    wanted = doc_key.lower()
    with conn() as c:
        for p in PAPERS:
            key, name, brief, _, icon, href = p[:6]
            if key == "overview":
                continue
            cited = {value.lower() for value in paper_cited_doc_keys(c, key)}
            if wanted in cited:
                matches.append((name, brief, icon, href))
    if not matches:
        return ""
    items = []
    for name, brief, icon, href in matches:
        items.append(
            f"""
<article class="result compact-result">
  <div>
    <h3><a href="{h(href)}"><svg class="ico"><use href="#{h(icon)}"/></svg>{h(name)}</a></h3>
    <div class="meta">{h(brief)}</div>
  </div>
  <div class="cite"><a href="{h(href)}">论文证据链</a></div>
</article>"""
        )
    return f"""
<section class="paper-citations">
  <h2 class="md-h2">论文引用回链</h2>
  <div class="meta">下列平台论文已把本档案列入原始证据链，可从论文回到原文、译文和引用卡片。</div>
  <div class="result-list compact-list">{''.join(items)}</div>
</section>
"""


def doc_event_links_html(page_ids: list[int]) -> str:
    if not page_ids:
        return ""
    placeholders = ",".join("?" for _ in page_ids)
    with conn() as c:
        try:
            rows = c.execute(
                f"""
                SELECT DISTINCT scope_type, scope_slug, scope_name, event_date, event_title, event_summary
                FROM research_events
                WHERE page_id IN ({placeholders})
                ORDER BY COALESCE(event_date, ''), importance DESC, event_title
                LIMIT 8
                """,
                tuple(page_ids),
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
    if not rows:
        return ""
    items = []
    for row in rows:
        query_key = "topic" if row["scope_type"] == "topic" else "person"
        href = f"/events?{query_key}={quote(row['scope_slug'])}"
        items.append(
            f"""
<article class="result compact-result">
  <div>
    <h3><a href="{h(href)}">{h(row["event_title"])}</a></h3>
    <div class="meta">{h(row["event_date"] or "日期未注明")} · {h(row["scope_name"])}</div>
    <div class="snippet">{h(compact(row["event_summary"], 180))}</div>
  </div>
  <div class="cite"><a href="{h(href)}">事件线索</a></div>
</article>"""
        )
    return f"""
<section class="paper-citations">
  <h2 class="md-h2">事件与人物证据链</h2>
  <div class="meta">本档案片段已进入事件索引，可继续按人物、地点、机构追踪同一问题的跨源材料。</div>
  <div class="result-list compact-list">{''.join(items)}</div>
</section>
"""


def papers_index() -> bytes:
    """所有论文索引页 — 按 category 分三组：paper / review / evidence。"""
    body = breadcrumb_html([("/", "首页"), (None, "研究论文")])
    body += """
<section class="hero hero-compact">
  <div class="hero-eyebrow">PLATFORM RESEARCH PAPERS</div>
  <h1>七源对照档案体系 · 研究产出总览</h1>
  <p class="hero-sub">本平台研究产出分三层：一、<strong>平台学术综述</strong>（七源 + 总论 8 篇）；
  二、<strong>待核问题与证据等级清单</strong>（按社科院方法论「先标疑点」对每卷的核验配套，6 份）；
  三、<strong>跨源事件证据卡片</strong>（按方法论「互证优先」的结构化卡片，7 张）。</p>
  <p style="margin-top:10px;"><a class="button" href="/standards"><svg class="ico"><use href="#i-archive"/></svg>本库收录标准与排除标准</a></p>
</section>
"""
    groups = [
        ("paper", "一、平台学术综述（8 篇）",
         "每篇聚焦档案集合的客观属性、收录边界、关键样本与跨源对照价值"),
        ("review", "二、待核问题与证据等级清单（6 份）",
         "按社科院方法论「先看来源 → 先标疑点」原则，对每卷论文做配套核验：标证据等级（L1—L4）、列单源孤证、自查判断/解释层"),
        ("evidence", "三、跨源事件证据卡片（7 张）",
         "对民盟史关键事件做结构化证据卡片（来源/产出主体/原文摘录/历史背景/人物关系/跨源对应/可信度/研究价值/后续检索/证据等级 8 字段）"),
    ]
    for cat, group_title, group_desc in groups:
        items = [p for p in PAPERS if (p[6] if len(p) >= 7 else "paper") == cat]
        body += f"""
<section style="margin-top:24px;">
  <h2 style="font-size:18px; color:var(--accent-deep); border-bottom:1.5pt solid var(--accent); padding-bottom:4px; margin-bottom:8px;">{h(group_title)}</h2>
  <p class="meta" style="margin:6px 0 12px;">{h(group_desc)}</p>
  <div class="result-list">
"""
        for p in items:
            key, name, brief, _, icon, href = p[:6]
            body += f"""
<article class="result">
  <div>
    <h2 style="font-size:16px;"><a href="{href}"><svg class="ico ico-lg" style="margin-right:6px;"><use href="#{icon}"/></svg>{h(name)}</a></h2>
    <div class="meta" style="margin-top:6px;line-height:1.7;">{h(brief)}</div>
  </div>
  <div class="cite"><a class="button" href="{href}">阅读全文 →</a></div>
</article>"""
        body += "</div></section>"
    return layout("研究论文 · 七源对照档案体系", body)


def paper_page(key: str) -> bytes:
    """单篇论文/清单/卡片渲染（PAPERS 三组共用入口）"""
    meta = next((p for p in PAPERS if p[0] == key), None)
    if not meta:
        return layout("文档未找到", '<div class="notice">未找到该文档。</div>')
    key, name, brief, path, icon, _ = meta[:6]
    category = meta[6] if len(meta) >= 7 else "paper"
    from pathlib import Path as _P
    fpath = _P(__file__).parent / path
    if not fpath.exists():
        return layout(name, f'<div class="notice">论文文件未生成：{path}</div>')
    md = fpath.read_text(encoding="utf-8")
    html_body = render_markdown(md)
    citations_html = paper_cited_docs_html(key, md)
    body = breadcrumb_html([("/", "首页"), ("/papers", "研究论文"), (None, name)])
    # 「前往平台栏目」按钮仅对一级论文（category=paper、非 overview）显示
    platform_btn = ""
    if category == "paper" and key != "overview":
        plat_label = name.split(' · ')[-1] if ' · ' in name else name
        platform_btn = f'<a class="button" href="/sources/{key}">前往 {h(plat_label)} 平台栏目</a>'
    # 待核清单和证据卡片的回链按钮
    related_btn = ""
    if category == "review":
        # 待核清单跳回对应平台论文
        base_key = key.removesuffix("-review")
        related_btn = f'<a class="button" href="/papers/{base_key}">查看 {h(base_key.upper())} 平台论文 →</a>'
    elif category == "evidence":
        related_btn = '<a class="button" href="/papers">← 全部研究论文</a>'

    body += f"""
<article class="paper-content">
{html_body}
</article>
{citations_html}
<div class="doc-tools" style="margin-top:24px;justify-content:center;">
  <a class="button" href="/papers">← 返回研究论文索引</a>
  {related_btn}
  {platform_btn}
</div>
"""
    return layout(f"{name} · 研究产出", body)


def about_page() -> bytes:
    fpath = ROOT / "docs" / "_public-introduction.md"
    body = breadcrumb_html([("/", "首页"), (None, "项目介绍")])
    if not fpath.exists():
        body += '<div class="notice">项目介绍文档未生成。</div>'
        return layout("项目介绍", body, active_path="/about")
    html_body = render_markdown(fpath.read_text(encoding="utf-8"))
    body += f"""
<article class="paper-content">
{html_body}
</article>
<div class="doc-tools" style="margin-top:24px;justify-content:center;">
  <a class="button" href="/papers">研究论文</a>
  <a class="button" href="/sourcebooks">资料包下载</a>
  <a class="button" href="/standards">收录标准</a>
</div>
"""
    return layout("项目介绍 · 民盟历史文献研究库", body, active_path="/about")


def public_page() -> bytes:
    with conn() as c:
        n_docs = c.execute(
            "SELECT count(*) FROM documents d LEFT JOIN document_classifications dc ON dc.document_id=d.id "
            "WHERE dc.grade IS NULL OR dc.grade != '前台不展示'"
        ).fetchone()[0]
        n_zh = c.execute("SELECT count(*) FROM translations WHERE language='zh-CN'").fetchone()[0]
        n_events = c.execute("SELECT count(*) FROM research_events").fetchone()[0]
    body = breadcrumb_html([("/", "首页"), (None, "公开介绍版")]) + f"""
<section class="hero hero-compact">
  <div class="hero-eyebrow">PUBLIC OVERVIEW</div>
  <h1>民盟历史文献研究库</h1>
  <p class="hero-sub">面向中国民主同盟早期历史研究的一手文献平台，系统整理 FRUS、CIA、Wilson、Hoover、HathiTrust、DRNH、NewspaperSG 七类境外与公开档案来源。</p>
  <div class="hero-chips">
    <span><b>{n_docs}</b> 篇公开展示文档</span>
    <span><b>{n_zh}</b> 条中文译文</span>
    <span><b>{n_events}</b> 条事件线索</span>
  </div>
  <div style="margin-top:18px;">
    <a class="button" href="/?public=1" style="background:#0f6b5b;color:#fff;padding:10px 22px;border-radius:6px;text-decoration:none;font-weight:bold;">📖 进入公开浏览模式</a>
    <span style="margin-left:10px;font-size:12px;color:var(--muted-soft);">公开模式下隐藏内部校订入口、质量页与后台路径；保留资料平台、论文、长编、卡片、人物索引、全文搜索</span>
  </div>
</section>
<section class="result-list">
  <article class="result">
    <div><h2>七源同代史料体系</h2><div class="meta">以美方外交、美方情报、国民政府内部、港媒、南洋报刊、苏方档案、民盟领导人私函共同互证。</div></div>
    <div class="cite"><a class="button" href="/sources/frus">平台入口</a></div>
  </article>
  <article class="result">
    <div><h2>研究论文与证据卡片</h2><div class="meta">按平台综述、待核清单、跨源事件证据卡片三层组织研究成果。</div></div>
    <div class="cite"><a class="button" href="/papers">研究论文</a></div>
  </article>
  <article class="result">
    <div><h2>全文检索与人物索引</h2><div class="meta">支持英文原文、中文译文、人物、事件、年份和档案来源交叉检索。</div></div>
    <div class="cite"><a class="button" href="/search?q=罗隆基">搜索样例</a></div>
  </article>
  <article class="result">
    <div><h2>史料长编与资料包</h2><div class="meta">按平台导出论文 PDF、史料长编和研究资料包，方便阅读、引用与阶段性整理。</div></div>
    <div class="cite"><a class="button" href="/sourcebooks">下载入口</a></div>
  </article>
</section>
"""
    return layout("公开介绍版 · 民盟历史文献研究库", body, active_path="/about")


def excluded_page() -> bytes:
    """已剔除清单页 (/excluded)：统一呈现 grade='前台不展示' 的误收档案 + 剔除理由。
    实现"误收已剔除"分级的可追溯展示，与 /standards 收录标准页配套。"""
    body = breadcrumb_html([("/", "首页"), (None, "已剔除清单")])
    body += """
<section class="hero hero-compact">
  <div class="hero-eyebrow">EXCLUDED · 前台不展示</div>
  <h1>已剔除档案清单</h1>
  <p class="hero-sub">下列档案因「名称相似但与中国民主同盟无组织关系」「远离民盟史时段」「误命中」等原因被剔出前台展示，但原始数据完整保留、可追溯、可复核。剔除依据见 <a href="/standards">本库收录标准与排除标准</a>。</p>
</section>
"""
    with conn() as c:
        try:
            rows = c.execute(
                """
                SELECT documents.doc_key, documents.title, documents.date_guess,
                       documents.doc_id, documents.volume_id,
                       COALESCE(documents.source_platform, 'frus') AS platform,
                       dc.reason
                FROM document_classifications dc
                JOIN documents ON documents.id = dc.document_id
                WHERE dc.grade = '前台不展示'
                ORDER BY platform, documents.date_guess, documents.doc_id
                """
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
    if not rows:
        body += '<div class="notice">当前无标记为「前台不展示」的档案，或剔除记录尚未同步到本环境数据库。剔除规则与历史记录详见 <a href="/standards">收录标准页</a>。</div>'
        return layout("已剔除清单 · 前台不展示", body)

    # 按平台分组
    from collections import defaultdict
    by_plat = defaultdict(list)
    for r in rows:
        by_plat[r["platform"]].append(r)

    body += f'<p class="meta" style="margin:8px 0 18px;">共 <strong>{len(rows)}</strong> 篇已剔除档案，分布于 {len(by_plat)} 个档案源。</p>'

    for plat in sorted(by_plat.keys()):
        plat_name = PLATFORM_META.get(plat, {}).get("name", plat.upper())
        items = by_plat[plat]
        body += f'<h2 class="md-h2" style="margin-top:24px;">{h(plat_name)} · {len(items)} 篇</h2>'
        body += '<table class="md-table"><thead><tr><th>标题</th><th style="width:110px;">日期</th><th style="width:30%;">剔除理由</th></tr></thead><tbody>'
        for r in items:
            title = r["title"] or r["doc_key"]
            reason = r["reason"] or "—"
            body += (
                f'<tr><td><span class="grade excluded">{h(title)}</span></td>'
                f'<td>{h(r["date_guess"] or "")}</td>'
                f'<td style="font-size:13px;color:var(--muted);">{h(reason)}</td></tr>'
            )
        body += "</tbody></table>"

    body += """
<div class="doc-tools" style="margin-top:24px;justify-content:center;">
  <a class="button" href="/standards">← 收录与排除标准</a>
  <a class="button" href="/docs">全部前台文档 →</a>
</div>
"""
    return layout("已剔除清单 · 前台不展示", body)


def standards_page() -> bytes:
    """《本库收录标准与排除标准》编辑准则页 (/standards)"""
    from pathlib import Path as _P
    fpath = _P(__file__).parent / "docs" / "_collection-standards.md"
    body = breadcrumb_html([("/", "首页"), (None, "收录标准")])
    if not fpath.exists():
        body += '<div class="notice">收录标准文档未生成。</div>'
        return layout("收录标准与排除标准", body)
    md = fpath.read_text(encoding="utf-8")
    html_body = render_markdown(md)
    body += f"""
<article class="paper-content">
{html_body}
</article>
<div class="doc-tools" style="margin-top:24px;justify-content:center;">
  <a class="button" href="/papers">研究论文索引 →</a>
  <a class="button" href="/excluded">已剔除清单 →</a>
  <a class="button" href="/docs">全部文档 →</a>
</div>
"""
    return layout("收录标准与排除标准 · 编辑准则", body)


def topic_page(slug: str) -> bytes:
    """/topics/<slug> 已废弃 — 重定向到人物索引。"""
    return layout(
        "已迁移",
        '<section class="doc-head"><div><h1>专题分类已合并到人物索引</h1>'
        '<div class="meta">本站不再按民盟事件主题做分类，所有档案通过 <a href="/people">人物索引</a> 导航。</div></div>'
        '<div class="doc-tools"><a class="button" href="/people">前往人物索引 →</a></div></section>'
    )

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
    <a class="button" href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">原始来源</a>
    <a class="button" href="/quality">质量检查</a>
  </div>
</section>
<section class="reader">
  <article class="pane">
    <div class="pane-head"><span>原文 · {h(page)}</span><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">引用</a></div>
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
                documents.id AS document_id,
                documents.doc_key,
                documents.volume_id,
                documents.doc_id,
                documents.volume_title,
                documents.title,
                documents.date_guess,
                documents.url AS doc_url,
                documents.source_platform,
                COALESCE(dc.grade, '') AS grade,
                translations.text AS zh_text,
                translations.status AS zh_status,
                COALESCE(pp.citation_ready, 0) AS citation_ready,
                COALESCE(pp.needs_human_review, 1) AS needs_human_review,
                COALESCE(pp.review_status, 'missing') AS provenance_review_status,
                COALESCE(pp.human_review_note, '') AS human_review_note,
                COALESCE(pp.source_file, '') AS source_file,
                COALESCE(pp.source_sha256, '') AS source_sha256,
                pp.source_file_size,
                pp.pdf_page_no,
                pp.physical_page_no,
                pp.printed_page,
                COALESCE(pp.page_image_path, '') AS page_image_path,
                COALESCE(pp.ocr_engine, '') AS ocr_engine,
                COALESCE(pp.ocr_model, '') AS ocr_model,
                COALESCE(pp.ocr_mode, '') AS ocr_mode,
                COALESCE(pp.event_tags, '') AS event_tags
            FROM pages
            JOIN documents ON documents.id = pages.document_id
            LEFT JOIN document_classifications dc ON dc.document_id = documents.id
            LEFT JOIN translations ON translations.page_id = pages.id AND translations.language='zh-CN'
            LEFT JOIN page_provenance pp ON pp.page_id = pages.id
            WHERE pages.id=?
            """,
            (page_id,),
        ).fetchone()
    if not row:
        return layout("未找到摘录", '<div class="notice">未找到摘录。</div>')
    if row["source_platform"] == "domestic" and getattr(_request, "public_mode", False):
        with conn() as c:
            if not _public_domestic_document_visible(c, int(row["document_id"])):
                return layout(
                    "公开模式不可用",
                    '<div class="notice">该国内文档尚未通过公开等级与权利门禁。请返回 <a href="/public">公开介绍版</a>。</div>',
                    active_path="/public",
                )
    page = source_page_label(row)
    source_url = row["page_url"] or row["doc_url"] or ""
    citation_gated_platform = row["source_platform"] in {"domestic", "drnh"}
    if citation_gated_platform and not _domestic_citation_is_strict(row):
        if row["source_platform"] == "drnh":
            gate_notice = (
                "<strong>DRNH 引用门禁未通过：</strong>本页是国史馆目录卡片或官方访客预览，"
                "当前不含可逐字核验的清洁原件正文；它可以用于检索、档号定位和研究导航，不能生成正式引文。"
            )
            gate_label = "目录卡片/访客预览（不可直接引用）"
        else:
            gate_notice = (
                "<strong>引用门禁未通过：</strong>本页可以用于检索和研究阅读，但尚无 human_verified "
                "人工复核记录及复核说明，因此不生成正式引文。"
            )
            gate_label = "国内史料"
        body = f"""
<section class="doc-head">
  <div>
    {title_block(row["title"], None, "h1")}
    <div class="meta">{h(row["date_guess"] or "日期未注明")} · {h(page)} · {gate_label}</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/doc/{quote(row["doc_key"])}?page_id={h(row["page_id"])}">返回阅读</a>
    <a class="button secondary" href="{h(source_href(source_url))}" target="_blank" rel="noreferrer">查看来源</a>
  </div>
</section>
<div class="notice">{gate_notice} 当前状态：{h(row["provenance_review_status"])}。</div>
<section class="reader">
  <article class="pane">
    <div class="pane-head"><span>{gate_label}</span><span>{h(page)}</span></div>
    <div class="pane-body">{h(row["original_text"])}</div>
  </article>
</section>
"""
        return layout("引用门禁未通过", body)
    metadata_scope_only = (
        row["source_platform"] == "domestic"
        and any(
            scope in str(row["event_tags"] or "")
            for scope in (
                "review_scope=issue_identity_contents_only",
                "review_scope=compiled_text_title_date_page_identity",
                "review_scope=periodical_issue_identity_editorial_title",
            )
        )
    )
    periodical_issue_scope = (
        "review_scope=periodical_issue_identity_editorial_title" in str(row["event_tags"] or "")
    )
    compiled_text_scope = (
        "review_scope=compiled_text_title_date_page_identity" in str(row["event_tags"] or "")
    )
    if row["source_platform"] in {"domestic", "drnh"}:
        if metadata_scope_only:
            event_tags = str(row["event_tags"] or "")
            compiled_year = (
                "1945"
                if "official_compilation_of_1945_text" in event_tags
                else "1944"
                if "official_compilation_of_1944_text" in event_tags
                else ""
            )
            scope_label = (
                f"官方汇编中的 {compiled_year} 文本：本页人工复核仅覆盖汇编版本、篇名、标注日期、PDF 页码和页界。"
                if compiled_text_scope
                else "本页人工复核仅覆盖刊名、期号、出版日、PDF 页码、版面及社论题名。"
                if periodical_issue_scope
                else "本页人工复核仅覆盖刊名、卷期、出版日、目录页身份及页码锚点。"
            )
            citation = (
                f"{domestic_citation_text(row)}\n\n"
                f"证据范围：{scope_label}"
                "下方机器识别文本只用于定位，未作逐字校勘，不得作为文章正文或逐字引文。"
            )
        else:
            citation = (
                f"{domestic_citation_text(row)}\n\n"
                f"原文摘录：\n{row['original_text']}\n\n"
                f"中文译文（{row['zh_status'] or '未标注'}）：\n{row['zh_text'] or ''}"
            )
    else:
        citation = (
            f"短引文：{short_citation(row)}\n"
            f"参考文献：{bibliography_entry(row)}\n\n"
            f"题名：{translate_title(row['title'])}\n"
            f"英文题名：{row['title']}\n"
            f"卷册：{row['volume_id']} / {row['volume_title'] or ''}\n"
            f"日期：{row['date_guess'] or ''}\n"
            f"引用位置：{page}\n"
            f"来源：{source_href(source_url)}\n\n"
            f"原文摘录：\n{row['original_text']}\n\n"
            f"中文译文（{row['zh_status'] or '未标注'}）：\n{row['zh_text'] or ''}"
        )
    domestic_panel = (
        domestic_provenance_summary(row)
        if row["source_platform"] in {"domestic", "drnh"}
        else ""
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
    <a class="button" href="{h(source_href(source_url))}" target="_blank" rel="noreferrer">原始来源</a>
  </div>
</section>
<section class="reader">
  <article class="pane">
    <div class="pane-head"><span>{'机器识别内容（仅供定位，不作逐字引文）' if metadata_scope_only else '原文摘录'}</span><span>{h(page)}</span></div>
    <div class="pane-body">{h(row["original_text"])}</div>
  </article>
  {'' if metadata_scope_only else f'''<article class="pane">
    <div class="pane-head"><span>中文译文 · {h(row["zh_status"] or "未标注")}</span><span>{h(page)}</span></div>
    <div class="pane-body">{h(row["zh_text"] or "")}</div>
  </article>'''}
</section>
{domestic_panel}
<section style="margin-top:14px;">
  <textarea class="copybox" readonly>{h(citation)}</textarea>
</section>
"""
    return layout("引用摘录卡片", body)


# 境外七源 + 国内史料层（用于 timeline 徽章 + 过滤按钮）
TIMELINE_PLATFORMS = [
    ("frus",        "FRUS",        "#0f6b5b"),  # 美方公开外交
    ("cia",         "CIA",         "#8b5e34"),  # 美方情报
    ("drnh",        "DRNH",        "#a86b1a"),  # 国民政府
    ("hathitrust",  "HathiTrust",  "#0a4a3f"),  # 港媒
    ("wilson",      "Wilson",      "#5a3a26"),  # 苏方
    ("hoover",      "Hoover",      "#6b6356"),  # 民盟创始人私函
    ("newspapersg", "NewspaperSG", "#157f73"),  # 南洋报刊
    ("domestic",    "国内史料",   "#b45131"),  # 国内史料层
]
TIMELINE_PLAT_LABEL = {k: lab for k, lab, _ in TIMELINE_PLATFORMS}
TIMELINE_PLAT_COLOR = {k: col for k, _, col in TIMELINE_PLATFORMS}


def timeline(topic_slug: str = "", person_slug: str = "", platform_slug: str = "") -> bytes:
    title = "民盟材料年表"
    subtitle = "按年份排列境内外档案片段，含校订、摘录与原始来源入口。"
    where = ""
    params: list[str] = []
    filter_links = []
    if platform_slug and platform_slug in TIMELINE_PLAT_LABEL:
        plat_label = TIMELINE_PLAT_LABEL[platform_slug]
        title = f"{plat_label} 民盟材料年表"
        subtitle = f"按年份排列 {plat_label} 平台档案片段。"
        # 注意：source_type='hathi_ia' 对应 platform='hathitrust'，需要兼容
        if platform_slug == 'hathitrust':
            where = "(COALESCE(documents.source_platform,'frus') = ? OR COALESCE(documents.source_platform,'frus') = ?)"
            params.extend(['hathitrust', 'hathi_ia'])
        else:
            where = "COALESCE(documents.source_platform,'frus') = ?"
            params.append(platform_slug)
        where = "WHERE " + where
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
            subtitle = "按时间排列该人物在境内外平台档案中的出现。"
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

    # 全部年表入口
    all_active = ' active' if not platform_slug else ''
    filter_links.append(f'<a class="button{all_active}" href="/timeline">全部年表</a>')
    # 平台过滤按钮
    for plat_key, plat_label, _ in TIMELINE_PLATFORMS:
        is_active = (platform_slug == plat_key)
        active_cls = ' active' if is_active else ''
        filter_links.append(f'<a class="button{active_cls}" href="/timeline?platform={plat_key}">{plat_label}</a>')
    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(title)}</h1>
    <div class="meta">{h(subtitle)}</div>
    <div class="meta">{len({row["doc_key"] for row in rows})} 篇文档 · {len(rows)} 个片段 · 按月细化</div>
  </div>
  <div class="doc-tools">
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
                # source 徽章 — 各平台分别识别
                src_platform = row["source_platform"] if "source_platform" in row.keys() else None
                if src_platform == 'hathi_ia':  # ingest 时 source_type='hathi_ia' 对应前台 'hathitrust'
                    src_platform = 'hathitrust'
                _label = TIMELINE_PLAT_LABEL.get(src_platform or 'frus', 'FRUS')
                _color = TIMELINE_PLAT_COLOR.get(src_platform or 'frus', '#0f6b5b')
                src_badge = (f'<span class="src-badge" style="font-size:11px;background:{_color};color:#fff;'
                             f'padding:1px 7px;border-radius:3px;letter-spacing:.02em;">{_label}</span> ')
                body += f"""
<article class="result">
  <div>
    {title_block(row["title"], href)}
    <div class="meta">{src_badge}{h(row["date_guess"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(page)} {grade_badge(row)}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 230))}</div>
    <div class="zh">中文: {h(compact(row["zh_text"], 230))}</div>
    <div class="tagline">{''.join(f'<span class="tag">{h(tag)}</span>' for tag in topic_tags(row))}{issue}</div>
  </div>
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">来源</a></div>
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
    <div class="meta">把国内外专题和人物命中的材料压缩成可浏览事件节点。每个节点都能回到原文、译文、摘录卡片和对应来源；国内关联仍是导航层，不等于事实确认。</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/timeline">文档年表</a>
    <a class="button" href="/people">人物</a>
    <a class="button" href="/places">地点</a>
    <a class="button" href="/organizations">机构</a>
  </div>
</section>
"""
    if not rows:
        body += '<div class="notice">暂无事件线索。</div>'
        return layout("事件线索", body)

    groups = [
        ("topic", "境外专题事件", lambda row: not str(row["scope_slug"]).startswith("domestic-")),
        ("topic", "国内专题事件", lambda row: str(row["scope_slug"]).startswith("domestic-")),
        ("person", "人物事件", lambda row: True),
    ]
    for scope_type, label, predicate in groups:
        group = [
            row for row in rows
            if row["scope_type"] == scope_type and predicate(row)
        ]
        if not group:
            continue
        body += f'<h2 style="font-size:18px;margin:18px 0 8px;">{h(label)}</h2><section class="result-list">'
        for row in group:
            query_key = "topic" if scope_type == "topic" else "person"
            href = f"/events?{query_key}={quote(row['scope_slug'])}"
            domestic = str(row["scope_slug"]).startswith("domestic-")
            related_href = "/timeline?platform=domestic" if domestic else f"/timeline?{query_key}={quote(row['scope_slug'])}"
            body += f"""
<article class="result">
  <div>
    <h2><a href="{h(href)}">{h(row["scope_name"])}</a></h2>
    <div class="meta">{row["event_count"]} 个事件节点 · {row["page_count"]} 个资料片段 · {"国内导航关联" if domestic else "境外/统一检索"}</div>
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
    is_domestic = bool(known.get("source") == "domestic")

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
    back_href = "/domestic/events" if is_domestic else "/people"
    timeline_href = "/timeline?platform=domestic" if is_domestic else f"/timeline?{scope_type}={quote(scope_slug)}"
    if is_domestic:
        related_href = f"/research/{quote(scope_slug)}"
    else:
        related_href = f"/{scope_type}s/{quote(scope_slug)}" if scope_type == "topic" else f"/people/{quote(scope_slug)}"
    title = f"{scope_name}事件线索"
    years: dict[str, list[sqlite3.Row]] = {}
    for row in rows:
        years.setdefault(str(row["event_year"] or "未注明"), []).append(row)

    body = f"""
<section class="doc-head">
  <div>
    <h1>{h(title)}</h1>
    <div class="meta">按事件节点组织资料。{"国内关联来自声明式覆盖表与已入库页，适合快速定位线索；" if is_domestic else "事件摘要来自中文译文和术语规则，适合快速定位线索；"}正式引用仍以原文、页码、来源哈希和人工复核为准。</div>
    <div class="meta">{len(rows)} 个事件节点 · {len({row["page_id"] for row in rows})} 个资料片段 · {len({row["doc_key"] for row in rows})} 篇文档</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/events">事件总览</a>
    <a class="button" href="{h(back_href)}">返回索引</a>
    <a class="button" href="{h(related_href)}">{"专题对读" if is_domestic else "资料列表"}</a>
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
                source_label = "国内原始入口" if is_domestic else "境外原始入口"
                review_href = f"/domestic/evidence-review/{row['page_id']}" if is_domestic else f"/review/{row['page_id']}"
                body += f"""
<article class="result">
  <div>
    <h2><a href="{h(doc_href)}">{h(row["event_title"])}</a></h2>
    <div class="meta">{h(row["event_date"] or row["date_guess"])} · {h(row["volume_id"])}/{h(row["doc_id"])} · {h(page)} {grade_badge(row)}</div>
    <div class="zh">{h(compact(row["event_summary"], 360))}</div>
    <div class="snippet">原文: {h(compact(row["original_text"], 220))}</div>
    <div class="tagline">{actor_tags}{topic_tags_html}{place_tags_html}{org_tags_html}<span class="tag">重要度 {h(row["importance"])}</span></div>
  </div>
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(review_href)}">{"证据复核" if is_domestic else "校订"}</a><br><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">{source_label}</a></div>
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
  <div class="cite"><a href="/cite/{h(row["page_id"])}">摘录卡片</a><br><a href="{h(doc_href)}">并排阅读</a><br><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">FRUS</a></div>
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
        source_url = source_href(row["page_url"] or row["doc_url"] or "")
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

    body = breadcrumb_html([("/", "首页"), (None, "民盟史关键事件")])
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
      本平台只收录 <b>中国大陆境外一手原始档案</b>。
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
      本卡为内部研究编排参考；下方 FRUS 命中片段为本平台收录的中国大陆境外一手档案原文与中译。
    </div>
  </div>
</section>
"""

    if not rows:
        body += (
            '<div class="notice">FRUS 档案中暂无与本事件直接命中的片段。'
            '待其他境外档案源补充后会自动出现。</div>'
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
  <div class="cite"><a href="/review/{h(row["page_id"])}">校订</a><br><a href="{h(source_href(row["page_url"]))}" target="_blank" rel="noreferrer">原始来源</a></div>
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


# ===== 新增功能：多源对位 / 人物档案画像 / 证据卡片库 =====

def alignment_page(date_from: str = "", date_to: str = "", q: str = "") -> bytes:
    # 默认窗口：1947 民盟非法化高密度期（四源对位最密的 50 天）
    date_from = (date_from or "1947-10-01").strip()
    date_to = (date_to or "1947-11-30").strip()
    q = (q or "").strip()

    c = conn()
    where = [
        "COALESCE(documents.date_guess,'') <> ''",
        "substr(documents.date_guess,1,10) >= ?",
        "substr(documents.date_guess,1,10) <= ?",
    ]
    params: list = [date_from, date_to]
    if q:
        where.append("(documents.title LIKE ? OR COALESCE(documents.matched_terms,'') LIKE ?)")
        params += [f"%{q}%", f"%{q}%"]

    rows = c.execute(
        f"""
        SELECT documents.id, documents.doc_key, documents.doc_id, documents.volume_id,
               documents.title, documents.date_guess,
               COALESCE(documents.source_platform, 'frus') AS platform,
               COALESCE(dc.grade, '') AS grade
        FROM documents
        LEFT JOIN document_classifications dc ON dc.document_id = documents.id
        WHERE {' AND '.join(where)}
        ORDER BY documents.date_guess, platform
        """,
        tuple(params),
    ).fetchall()

    # 组矩阵：day -> platform -> [row]
    matrix: dict[str, dict[str, list]] = {}
    plat_totals: dict[str, int] = {}
    for r in rows:
        day = (r["date_guess"] or "")[:10]
        plat = r["platform"]
        matrix.setdefault(day, {}).setdefault(plat, []).append(r)
        plat_totals[plat] = plat_totals.get(plat, 0) + 1

    # 出现过的源，按 PLATFORM_META 顺序（已上线优先）排列为列
    def _plat_order(k: str) -> tuple:
        meta = PLATFORM_META.get(k, {})
        return (0 if meta.get("active") else 1, k)

    platforms = sorted(plat_totals.keys(), key=_plat_order)
    days = sorted(matrix.keys())

    # 预设高密度窗口快捷入口（你库里已建对位卡片的三个转折）
    presets = [
        ("1947-10-01", "1947-11-30", "1947 民盟非法化"),
        ("1946-05-01", "1946-06-30", "1946 广西取缔"),
        ("1945-07-01", "1945-08-31", "1945 访问延安"),
        ("1946-07-01", "1946-08-31", "1946 李闻血案"),
    ]
    preset_html = " · ".join(
        f'<a href="/align?from={a}&to={b}">{h(label)}</a>' for a, b, label in presets
    )

    # 顶部控制条
    head = f"""
<section class="doc-head">
  <div>
    <h1>多源对位视图</h1>
    <div class="meta">同一时点各档案源并排，看清谁记了、谁缺位 · 当前窗口 {h(date_from)} → {h(date_to)}
      {('· 关键词：' + h(q)) if q else ''}</div>
  </div>
</section>
<form class="align-form" method="get" action="/align">
  <label><span>起</span><input type="text" name="from" value="{h(date_from)}" placeholder="1947-10-01"></label>
  <label><span>止</span><input type="text" name="to" value="{h(date_to)}" placeholder="1947-11-30"></label>
  <label class="align-query"><span>关键词</span><input type="text" name="q" value="{h(q)}" placeholder="可选，如 罗隆基"></label>
  <button class="button" type="submit">对位</button>
</form>
<div class="align-presets">快捷窗口：{preset_html}</div>
"""

    if not rows:
        body = head + '<div class="notice">该时间窗内没有带日期的文档。换个窗口或放宽日期试试。</div>'
        return layout("多源对位视图", body, active_path="/align")

    # 各源命中统计
    stat_html = " ".join(
        f'<span class="grade related" style="margin-right:4px;">{h(PLATFORM_META.get(p,{}).get("name",p))} {plat_totals[p]}</span>'
        for p in platforms
    )

    # 对位矩阵表（横向可滚动，移动端友好）
    th = "".join(
        f'<th style="position:sticky;top:0;background:var(--paper);min-width:150px;text-align:left;padding:8px 10px;border-bottom:2px solid var(--line);font-size:13px;">'
        f'{h(PLATFORM_META.get(p,{}).get("name",p))}</th>'
        for p in platforms
    )
    trs = []
    for day in days:
        cells = [
            f'<td style="white-space:nowrap;padding:8px 10px;border-bottom:1px solid var(--line-soft);'
            f'font-variant-numeric:tabular-nums;color:var(--ink);font-weight:600;vertical-align:top;">{h(day)}</td>'
        ]
        for p in platforms:
            docs = matrix[day].get(p, [])
            if not docs:
                cells.append('<td style="padding:8px 10px;border-bottom:1px solid var(--line-soft);color:var(--line);text-align:center;vertical-align:top;">·</td>')
                continue
            items = []
            for r in docs:
                title = translate_title(r["title"]) or r["doc_key"]
                title_short = title if len(title) <= 38 else title[:36] + "…"
                badge = grade_badge(r)
                items.append(
                    f'<div style="margin-bottom:5px;line-height:1.35;">'
                    f'<a href="/doc/{quote(r["doc_key"])}" title="{h(title)}">{h(title_short)}</a> {badge}</div>'
                )
            cells.append(
                f'<td style="padding:8px 10px;border-bottom:1px solid var(--line-soft);vertical-align:top;font-size:13px;">{"".join(items)}</td>'
            )
        trs.append(f'<tr><th style="position:sticky;left:0;background:var(--paper);padding:8px 10px;'
                   f'border-bottom:1px solid var(--line-soft);text-align:left;font-weight:600;font-variant-numeric:tabular-nums;">{h(day)}</th>{"".join(cells[1:])}</tr>')

    table = f"""
<div class="align-stats">{stat_html}</div>
<div class="align-scroll">
  <table class="align-table">
    <thead><tr><th style="position:sticky;left:0;top:0;background:var(--paper);text-align:left;padding:8px 10px;border-bottom:2px solid var(--line);font-size:13px;min-width:90px;">日期</th>{th}</tr></thead>
    <tbody>{''.join(trs)}</tbody>
  </table>
</div>
<div style="font-size:12px;color:var(--muted-soft);margin-top:10px;">
  共 {len(rows)} 篇 / {len(days)} 个日期 / {len(platforms)} 个源 · "·" 表示该源当日无对位档案 · 点标题进单篇详情
</div>
"""
    return layout("多源对位视图", head + table, active_path="/align")


def person_archive_panel(person: dict, rows: list) -> str:
    if not rows:
        return ""

    # 按文档去重（rows 是逐片段，一个 doc 可能多页）——取每个 doc 最早出现的那行
    by_doc: dict = {}
    for r in rows:
        k = r["doc_key"]
        if k not in by_doc:
            by_doc[k] = r

    def _plat(r) -> str:
        return r["platform"] if ("platform" in r.keys() and r["platform"]) else "frus"

    # ① 跨源分布
    plat_count: dict[str, int] = {}
    for r in by_doc.values():
        p = _plat(r)
        plat_count[p] = plat_count.get(p, 0) + 1

    def _plat_order(k: str) -> tuple:
        meta = PLATFORM_META.get(k, {})
        return (0 if meta.get("active") else 1, -plat_count.get(k, 0), k)

    plats = sorted(plat_count.keys(), key=_plat_order)
    total_docs = len(by_doc)
    dist_bar = "".join(
        f'<span class="grade related" style="margin:0 6px 6px 0;display:inline-block;">'
        f'{h(PLATFORM_META.get(p,{}).get("name", p))} · {plat_count[p]} 篇</span>'
        for p in plats
    )

    # ② 在档行迹时间线（按 date_guess 排序，无日期者沉底）
    def _sort_key(r):
        d = (r["date_guess"] or "").strip()
        return (d if d else "9999", r["doc_key"])

    timeline_docs = sorted(by_doc.values(), key=_sort_key)
    rows_html = []
    for r in timeline_docs:
        date = (r["date_guess"] or "").strip() or "日期未注明"
        title = translate_title(r["title"]) or r["doc_key"]
        title_short = title if len(title) <= 52 else title[:50] + "…"
        badge = grade_badge(r)
        src = PLATFORM_META.get(_plat(r), {}).get("name", _plat(r))
        rows_html.append(
            f'<tr>'
            f'<td style="white-space:nowrap;padding:7px 12px 7px 0;vertical-align:top;'
            f'font-variant-numeric:tabular-nums;color:var(--ink);font-weight:600;border-bottom:1px solid var(--line-soft);">{h(date)}</td>'
            f'<td style="padding:7px 10px 7px 0;vertical-align:top;border-bottom:1px solid var(--line-soft);">'
            f'<a href="/doc/{quote(r["doc_key"])}" title="{h(title)}">{h(title_short)}</a> {badge}</td>'
            f'<td style="white-space:nowrap;padding:7px 0;vertical-align:top;border-bottom:1px solid var(--line-soft);'
            f'font-size:12px;color:var(--muted-soft);">{h(src)}</td>'
            f'</tr>'
        )

    # 行迹时间线最多直接展开 60 条，其余提示去事件/搜索看全量
    shown = rows_html[:60]
    more_note = ""
    if len(rows_html) > 60:
        more_note = (
            f'<div style="font-size:12px;color:var(--muted-soft);margin-top:8px;">'
            f'仅列前 60 条（共 {len(rows_html)} 篇）· '
            f'<a href="/timeline?person={h(person["slug"])}">完整年表 →</a> · '
            f'<a href="/events?person={h(person["slug"])}">事件线索 →</a></div>'
        )

    return f"""
<section style="margin:4px 0 18px;">
  <div class="meta" style="color:var(--accent-deep);font-size:13px;letter-spacing:.05em;text-transform:uppercase;margin-bottom:10px;">
    档案画像
  </div>
  <div style="margin-bottom:14px;">
    <div style="font-size:12.5px;color:var(--muted);margin-bottom:6px;">跨源分布 · 共 {total_docs} 篇文档记录此人</div>
    {dist_bar}
  </div>
  <div style="font-size:12.5px;color:var(--muted);margin-bottom:6px;">在档行迹（按档案日期）</div>
  <div class="person-timeline-scroll">
    <table class="person-timeline-table">
      <tbody>{''.join(shown)}</tbody>
    </table>
  </div>
  {more_note}
</section>
"""


def cards_index() -> bytes:
    # 从 PAPERS 中筛出证据卡片（type == "evidence"）
    cards = [p for p in PAPERS if len(p) >= 7 and p[6] == "evidence"]

    # 按事件年份排序（从 key 里抽 4 位年份，抽不到沉底）
    import re as _re

    def _year(key: str) -> str:
        m = _re.search(r"(19\d{2})", key)
        return m.group(1) if m else "9999"

    cards = sorted(cards, key=lambda p: (_year(p[0]), p[0]))

    # 画廊卡片
    items = []
    for key, title, subtitle, md_path, icon, url, _type in cards:
        items.append(f"""
    <a class="card-link" href="{h(url)}">
      <div style="display:flex;align-items:flex-start;gap:10px;">
        <svg class="ico" style="flex:none;margin-top:3px;color:var(--accent);"><use href="#{h(icon)}"/></svg>
        <div style="min-width:0;">
          <div style="font-family:var(--serif);font-size:16.5px;font-weight:600;color:var(--ink);line-height:1.4;margin-bottom:5px;">{h(title)}</div>
          <div style="font-size:13px;color:var(--muted);line-height:1.6;">{h(subtitle)}</div>
          <div style="font-size:12.5px;color:var(--accent-deep);margin-top:8px;">阅读卡片集 →</div>
        </div>
      </div>
    </a>""")

    head = f"""
<section class="doc-head">
  <div>
    <h1>证据卡片库</h1>
    <div class="meta">跨源对位证据卡片集 · 共 {len(cards)} 部 · 社科院方法「孤证不举·互证优先」实践</div>
  </div>
  <div class="doc-tools">
    <a class="button" href="/align">多源对位视图</a>
    <a class="button" href="/papers">研究论文</a>
    <a class="button" href="/events">事件线索</a>
  </div>
</section>
<div style="font-size:13.5px;color:var(--muted);line-height:1.8;margin:6px 0 16px;max-width:62ch;">
  每部卡片集围绕一个民盟史关键事件，把同时点各档案源（FRUS / DRNH / HathiTrust / Hoover / CIA / NewspaperSG）
  的档案逐时点对位，标注原文摘录、可信度、证据等级（L1–L4）与待核问题——用档案讲史，而非堆资料清单。
  想看"同一时点各源自动并排"，去 <a href="/align">多源对位视图</a>。
</div>
"""
    body = head + '<div class="card-grid">' + "".join(items) + "</div>"
    return layout("证据卡片库", body, active_path="/cards")


class Handler(BaseHTTPRequestHandler):
    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        # 顶层异常兜底：任何路由处理函数抛出未预期异常时，
        # 之前会直接断连（客户端收到 Empty reply），现在统一转成 500 页面，
        # 并且绝不把服务端 traceback 回传给客户端（只打到 stderr）。
        try:
            self._do_GET_inner()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            import traceback
            traceback.print_exc()
            try:
                body = layout("服务错误", '<div class="notice">页面渲染出错，已记录服务端日志，请稍后重试。</div>')
                self.send_response(500)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                pass

    def _do_GET_inner(self) -> None:
        # 修复：BaseHTTPRequestHandler 把 self.path 按 ISO-8859-1 解码，
        # 中文 URL 参数会变成乱码。这里重新按 UTF-8 解一遍。
        raw_path = self.path
        try:
            raw_path = raw_path.encode("latin-1").decode("utf-8")
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass
        parsed = urlparse(raw_path)
        qs = parse_qs(parsed.query)
        _request.path = parsed.path  # 让 layout() 知道当前页面，自动 highlight 导航
        # 公开模式解析：query ?public=1 显式开启 / ?public=0 关闭；否则读 cookie
        cookie_hdr = self.headers.get("Cookie", "") or ""
        cookie_public = "public_mode=1" in cookie_hdr
        q_public = qs.get("public", [None])[0]
        if q_public == "1":
            _request.public_mode = True
            self._set_public_cookie = "1"
        elif q_public == "0":
            _request.public_mode = False
            self._set_public_cookie = "0"
        else:
            _request.public_mode = cookie_public
            self._set_public_cookie = None
        # 公开模式下，访问内部路径自动 302 回 /public
        if _request.public_mode and any(parsed.path == p or parsed.path.startswith(p + "/")
                                         for p in PUBLIC_HIDDEN_PATHS):
            self.send_response(302)
            self.send_header("Location", "/public")
            self.end_headers()
            return
        if parsed.path == "/":
            payload = home()
        elif parsed.path == "/focus":
            payload = focus_page(qs.get("saved", [""])[0] == "1")
        elif parsed.path == "/dashboard":
            payload = dashboard()
        elif parsed.path == "/about":
            payload = about_page()
        elif parsed.path == "/public":
            payload = public_page()
        elif parsed.path == "/domestic/document":
            payload = domestic_staging_document_page(qs)
        elif parsed.path == "/domestic/library":
            payload = domestic_library_page(qs)
        elif parsed.path == "/domestic/search":
            payload = domestic_staging_search_page(qs)
        elif parsed.path == "/domestic/quality":
            payload = domestic_quality_page()
        elif parsed.path == "/domestic/academic":
            payload = domestic_academic_page()
        elif parsed.path.startswith("/domestic/candidate/"):
            candidate_id = unquote(parsed.path.removeprefix("/domestic/candidate/"))
            payload = domestic_candidate_page(candidate_id)
        elif parsed.path == "/domestic/sources":
            payload = domestic_sources_page()
        elif parsed.path == "/domestic/events":
            payload = domestic_events_page(qs)
        elif parsed.path == "/research":
            payload = research_topics_page()
        elif parsed.path == "/research/gaps":
            payload = research_gaps_page()
        elif parsed.path == "/research/packets":
            payload = research_packets_page()
        elif parsed.path.startswith("/research/") and parsed.path.endswith("/packet.json"):
            packet_event_id = unquote(parsed.path.removeprefix("/research/").removesuffix("/packet.json").rstrip("/"))
            packet_payload = packet_json_bytes(packet_event_id)
            if packet_payload is None:
                self.send_response(404)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(packet_payload)))
            self.send_header("Content-Disposition", f"attachment; filename=\"{quote(packet_event_id, safe='-_.')}.json\"")
            self.end_headers()
            self.wfile.write(packet_payload)
            return
        elif parsed.path.startswith("/research/") and parsed.path.endswith("/packet"):
            packet_event_id = unquote(parsed.path.removeprefix("/research/").removesuffix("/packet").rstrip("/"))
            payload = research_packet_page(packet_event_id)
        elif parsed.path.startswith("/research/"):
            payload = research_topic_page(unquote(parsed.path.removeprefix("/research/")))
        elif parsed.path == "/domestic/people":
            payload = _domestic_facet_page("people")
        elif parsed.path == "/domestic/places":
            payload = _domestic_facet_page("places")
        elif parsed.path == "/domestic/acquisition":
            payload = domestic_acquisition_page()
        elif parsed.path.startswith("/domestic/evidence-review/"):
            try:
                page_id_int = int(parsed.path.removeprefix("/domestic/evidence-review/"))
            except ValueError:
                page_id_int = 0
            payload = domestic_evidence_review_page(page_id_int, qs.get("saved", [""])[0] == "1")
        elif parsed.path == "/domestic/review":
            payload = domestic_review_page()
        elif parsed.path == "/domestic":
            payload = domestic_page(qs)
        elif parsed.path == "/sourcebooks":
            payload = sourcebooks_page()
        elif parsed.path == "/drnh-review":
            payload = drnh_review_page(qs.get("tier", [""])[0])
        elif parsed.path == "/l1-board":
            payload = l1_board_page()
        elif parsed.path == "/hk-press":
            payload = hk_press_page()
        elif parsed.path == "/first-person":
            payload = first_person_page()
        elif parsed.path == "/external-acquisition":
            payload = external_acquisition_page()
        elif parsed.path == "/open-sources":
            payload = open_sources_page()
        elif parsed.path.startswith("/sourcebooks/file/"):
            try:
                fname = unquote(parsed.path.removeprefix("/sourcebooks/file/"))
                if "/" in fname or ".." in fname or not fname.endswith(".pdf"):
                    raise ValueError("bad sourcebook path")
                fpath = (ROOT / "workspace" / fname).resolve()
                workspace_root = (ROOT / "workspace").resolve()
                if not str(fpath).startswith(str(workspace_root)) or not fpath.is_file():
                    raise FileNotFoundError
                data = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f"inline; filename=\"sourcebook.pdf\"; filename*=UTF-8''{quote(fname)}")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                payload = layout("史料长编未找到", '<div class="notice">未找到该史料长编 PDF。</div>', active_path="/sourcebooks")
        elif parsed.path.startswith("/papers/file/"):
            try:
                fname = unquote(parsed.path.removeprefix("/papers/file/"))
                if "/" in fname or ".." in fname or not fname.endswith(".pdf"):
                    raise ValueError("bad paper pdf path")
                fpath = (PAPER_PDF_DIR / fname).resolve()
                paper_root = PAPER_PDF_DIR.resolve()
                if not str(fpath).startswith(str(paper_root)) or not fpath.is_file():
                    raise FileNotFoundError
                data = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/pdf")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f"inline; filename=\"paper.pdf\"; filename*=UTF-8''{quote(fname)}")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                payload = layout("论文 PDF 未找到", '<div class="notice">未找到该论文 PDF。请先生成 output/pdf。</div>', active_path="/papers")
        elif parsed.path.startswith("/packages/file/"):
            try:
                fname = unquote(parsed.path.removeprefix("/packages/file/"))
                if "/" in fname or ".." in fname or not fname.endswith(".zip"):
                    raise ValueError("bad package path")
                fpath = (RESEARCH_PACKAGE_DIR / fname).resolve()
                package_root = RESEARCH_PACKAGE_DIR.resolve()
                if not str(fpath).startswith(str(package_root)) or not fpath.is_file():
                    raise FileNotFoundError
                data = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Content-Disposition", f"attachment; filename=\"research-package.zip\"; filename*=UTF-8''{quote(fname)}")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                payload = layout("资料包未找到", '<div class="notice">未找到该平台资料包 ZIP。请先生成 output/research_packages。</div>', active_path="/sourcebooks")
        elif parsed.path == "/search":
            payload = search(
                qs.get("q", [""])[0],
                qs.get("platform", [""])[0] if qs.get("platform", [""])[0] else None,
                qs.get("year", [""])[0],
                qs.get("grade", [""])[0],
                qs.get("person", [""])[0],
                qs.get("cited", [""])[0] == "1",
            )
        elif parsed.path == "/docs":
            payload = docs(qs.get("grade", [""])[0], qs.get("translation", [""])[0], qs.get("platform", [""])[0])
        elif parsed.path == "/glossary":
            payload = glossary_page()
        elif parsed.path.startswith("/sources/"):
            payload = source_page(unquote(parsed.path.removeprefix("/sources/")))
        elif parsed.path.startswith("/static/"):
            # 静态文件服务：css/js/svg 等
            try:
                rest = unquote(parsed.path.removeprefix("/static/"))
                if ".." in rest or rest.startswith("/"):
                    raise ValueError("path traversal")
                fpath = (ROOT / "static" / rest).resolve()
                static_root = (ROOT / "static").resolve()
                if not str(fpath).startswith(str(static_root)) or not fpath.is_file():
                    raise FileNotFoundError
                ext = fpath.suffix.lower()
                ctype = {
                    ".css": "text/css; charset=utf-8",
                    ".js": "application/javascript; charset=utf-8",
                    ".png": "image/png", ".jpg": "image/jpeg", ".svg": "image/svg+xml",
                    ".woff": "font/woff", ".woff2": "font/woff2",
                }.get(ext, "application/octet-stream")
                data = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                if ext == ".css":
                    self.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
                else:
                    self.send_header("Cache-Control", "public, max-age=3600")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                self.send_response(404); self.end_headers(); return
        elif parsed.path.startswith("/drnh-img/"):
            # 静态服务台北档案史料已下载的访客水印图：/drnh-img/<doc_key>/p<N>.jpg
            try:
                rest = unquote(parsed.path.removeprefix("/drnh-img/"))
                parts = rest.rsplit("/", 1)
                if len(parts) != 2 or not parts[1].endswith(".jpg"):
                    raise ValueError("bad path")
                doc_key_safe, fname = parts
                # 防穿越
                if "/" in fname or ".." in fname or ".." in doc_key_safe:
                    raise ValueError("path traversal")
                root_resolved = (DATA_ROOT / "drnh_images").resolve()
                sub_name = doc_key_safe.replace(":", "__").replace("/", "_")
                sub_candidates = [root_resolved / sub_name]
                if sub_name.startswith("drnh__"):
                    sub_candidates.append(root_resolved / sub_name.removeprefix("drnh__"))
                fpath = next((p / fname for p in sub_candidates if (p / fname).is_file()), None)
                if fpath is None:
                    raise FileNotFoundError
                fpath = fpath.resolve()
                if not str(fpath).startswith(str(root_resolved)):
                    raise ValueError("escape")
                data = fpath.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                payload = layout("圖像未找到", '<div class="notice">未找到该 DRNH 訪客水印圖。</div>')
        elif parsed.path == "/quality":
            payload = quality(qs.get("severity", [""])[0], qs.get("issue", [""])[0])
        elif parsed.path == "/tasks":
            payload = tasks(qs.get("queue", [""])[0])
        elif parsed.path == "/align":
            payload = alignment_page(qs.get("from", [""])[0], qs.get("to", [""])[0], qs.get("q", [""])[0])
        elif parsed.path == "/cards":
            payload = cards_index()
        elif parsed.path == "/papers":
            payload = papers_index()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Cache-Control","no-cache"); self.end_headers(); self.wfile.write(payload); return
        elif parsed.path.startswith("/papers/"):
            key = parsed.path.removeprefix("/papers/").rstrip("/")
            payload = paper_page(key)
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Cache-Control","no-cache"); self.end_headers(); self.wfile.write(payload); return
        elif parsed.path == "/standards":
            payload = standards_page()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Cache-Control","no-cache"); self.end_headers(); self.wfile.write(payload); return
        elif parsed.path == "/excluded":
            payload = excluded_page()
            self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Cache-Control","no-cache"); self.end_headers(); self.wfile.write(payload); return
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
            payload = timeline(qs.get("topic", [""])[0], qs.get("person", [""])[0], qs.get("platform", [""])[0])
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
            self.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
            self.end_headers()
            self.wfile.write(payload)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
        # 公开模式 cookie 设置（query 显式指定时下发）
        sc = getattr(self, "_set_public_cookie", None)
        if sc == "1":
            self.send_header("Set-Cookie", "public_mode=1; Path=/; Max-Age=31536000; SameSite=Lax")
        elif sc == "0":
            self.send_header("Set-Cookie", "public_mode=0; Path=/; Max-Age=0; SameSite=Lax")
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:
        # 与 do_GET 一致的顶层异常兜底，避免表单保存类接口异常时直接断连。
        try:
            self._do_POST_inner()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError):
            pass
        except Exception:
            import traceback
            traceback.print_exc()
            try:
                body = layout("服务错误", '<div class="notice">提交处理出错，已记录服务端日志，请稍后重试。</div>')
                self.send_response(500)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-cache, max-age=0, must-revalidate")
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                pass

    def _do_POST_inner(self) -> None:
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
        if parsed.path.startswith("/domestic/evidence-review/"):
            try:
                page_id_int = int(parsed.path.removeprefix("/domestic/evidence-review/"))
            except ValueError:
                page_id_int = 0
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            ok, error = save_domestic_evidence_review(page_id_int, parse_qs(body))
            if ok:
                self.send_response(303)
                self.send_header("Location", f"/domestic/evidence-review/{page_id_int}?saved=1")
                self.end_headers()
                return
            payload = domestic_evidence_review_page(page_id_int, error=error)
            self.send_response(400)
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
