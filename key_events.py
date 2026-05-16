# -*- coding: utf-8 -*-
"""民盟史关键事件数据（AI 内部研究参考，非平台收录内容）
==============================================================

为 app.py 的 /events/key/<slug> 关键事件页提供事件骨架。

**重要边界**：本研究平台只收录 **国外一手原始档案**（FRUS / Wilson / CIA / Hoover /
NARA / HathiTrust 等海外档案的原文与中译）。本文件中的事件清单与时间标注是
**AI 协作时的内部研究编排工具**，用于把档案碎片化的命中聚合到学术意义上的
历史事件节点，**不构成平台的资料库内容**。

**字段说明**：
- slug: URL 短码
- name: 事件名称
- phase: 所属民盟史阶段（p1-p6，对应 person_archive.PERSON_GROUPS）
- date_label: 时间标签（如 "1946.7.11–15"，用于展示）
- sort_date: 用于排序的 YYYY-MM-DD 字符串
- summary: 100-200 字事件简介（中文）
- search_terms: FRUS 数据库的检索关键词列表（中英文混合）
- related_persons: 关联人物 slug 列表（对应 person_archive.PEOPLE）
"""

KEY_EVENTS = [
    # ╔══════════════════════════════════════════════════════════════
    # ║ Ⅰ. 民盟创立与三党三派合组期（1941.3 - 1944.9）
    # ╚══════════════════════════════════════════════════════════════
    {
        "slug": "meng-founded-1941",
        "name": "中国民主政团同盟成立",
        "phase": "p1-founding-1941-1944",
        "date_label": "1941.3.19",
        "sort_date": "1941-03-19",
        "summary": (
            "1941 年 3 月 19 日，由黄炎培、张澜、沈钧儒等以国民参政员为基础，"
            "在重庆秘密成立「中国民主政团同盟」，黄炎培任首任中央委员会主席。"
            "此前 1939 年 11 月，国民参政员已成立「统一建国同志会」作为筹备组织。"
            "民盟成立的直接背景是 1941 年 1 月「皖南事变」破坏国共合作、"
            "抗日民族统一战线危机四伏，国共两党以外主张抗日的政党人士迫切希望联合发声。"
            "1941 年 8 月黄炎培辞主席职，张澜继任。"
        ),
        "search_terms": [
            "Democratic League", "China Democratic League",
            "Huang Yen-pei", "Chang Lan", "三党三派",
            "民主政团同盟", "1941",
        ],
        "related_persons": ["huang-yen-pei", "chang-lan", "shen-chun-ju",
                             "chang-po-chun", "lo-lung-chi", "liang-shu-ming",
                             "carsun-chang", "chang-tung-sun", "tso-shun-sheng"],
    },
    {
        "slug": "salvation-association-joins-1942",
        "name": "救国会加入民盟（三党三派完整形成）",
        "phase": "p1-founding-1941-1944",
        "date_label": "1942",
        "sort_date": "1942-06-01",
        "summary": (
            "1942 年，全国各界救国联合会加入中国民主政团同盟，民盟正式形成"
            "「三党三派」的政治联盟格局：中国青年党、国家社会党、中华民族解放行动委员会、"
            "中华职业教育社、乡村建设协会、全国各界救国联合会。"
            "救国会带来沈钧儒、史良、邹韬奋、章乃器、李公朴、王造时、沙千里"
            "「救国会七君子」等社会知名度极高的爱国民主人士，"
            "民盟政治影响力获得实质性加强。"
        ),
        "search_terms": [
            "National Salvation", "salvation association",
            "seven gentlemen", "救国会",
            "Shen Chun-ju", "Li Kung-pu", "1942",
        ],
        "related_persons": ["shen-chun-ju", "shih-liang", "tsou-tao-fen",
                             "chang-nai-chi", "li-kung-pu", "wang-tsao-shih",
                             "sha-chien-li"],
    },

    # ╔══════════════════════════════════════════════════════════════
    # ║ Ⅱ. 抗胜利与政协斡旋期（1944.9 - 1946.6）
    # ╚══════════════════════════════════════════════════════════════
    {
        "slug": "meng-1st-congress-1945",
        "name": "民盟第一次全国代表大会",
        "phase": "p2-pcc-1944-1946",
        "date_label": "1945.10",
        "sort_date": "1945-10-01",
        "summary": (
            "1945 年 10 月，民盟在重庆召开临时全国代表大会（即第一次全国代表大会），"
            "通过《政治报告》《临时全国代表大会宣言》《中国民主同盟纲领》《组织规程》。"
            "大会产生第一届中央委员会，推选张澜为中央委员会主席。"
            "民盟一大明确提出「**和平、统一、团结、民主**」的政治主张，"
            "这是抗战胜利后中国民主党派最具影响力的政治宣言之一。"
        ),
        "search_terms": [
            "Democratic League congress", "first congress",
            "Chang Lan", "民盟一大", "1945",
        ],
        "related_persons": ["chang-lan", "huang-yen-pei", "shen-chun-ju",
                             "chang-po-chun", "lo-lung-chi", "liang-shu-ming"],
    },
    {
        "slug": "pcc-1946",
        "name": "1946 年政治协商会议",
        "phase": "p2-pcc-1944-1946",
        "date_label": "1946.1.10–31",
        "sort_date": "1946-01-10",
        "summary": (
            "1946 年 1 月 10 日至 31 日在重庆召开的政治协商会议，"
            "是抗战胜利后国共两党与第三方面就和平建国进行的最重要谈判。"
            "民盟派出 9 人代表团（张澜、沈钧儒、章伯钧、罗隆基、张君劢、张东荪等），"
            "与中共代表团周恩来等密切配合，力促和谈成功。"
            "会议通过《和平建国纲领》等 5 项决议，确立联合政府方向。"
            "这是民盟历史上**最高光时刻**，也是国共内战前最后的和平窗口。"
        ),
        "search_terms": [
            "Political Consultative Conference", "PCC", "Steering Committee",
            "Democratic League", "政治协商", "政协", "1946",
            "Chang Lan", "Lo Lung-chi", "Chou En-lai",
        ],
        "related_persons": ["chang-lan", "shen-chun-ju", "chang-po-chun",
                             "lo-lung-chi", "carsun-chang", "chang-tung-sun",
                             "liang-shu-ming", "chou-en-lai"],
    },
    {
        "slug": "shanghai-branch-1946",
        "name": "民盟上海市支部正式成立",
        "phase": "p2-pcc-1944-1946",
        "date_label": "1946.8",
        "sort_date": "1946-08-15",
        "summary": (
            "1946 年 2 月 20 日黄炎培召集在沪中央委员，在上海愚园路 749 弄 31 号"
            "举行茶会，宣布成立民盟上海市支部筹备委员会，沈志远、黄竞武为召集人。"
            "**1946 年 8 月底民盟上海市支部正式建立**，**王绍鏊任首任主任委员**；"
            "执行委员含沙千里、沈志远、施复亮、黄竞武、祝公健、彭文应等。"
            "这是上海民盟组织建立 80 周年（1946-2026）的起点。"
        ),
        "search_terms": [
            "Shanghai", "Democratic League Shanghai",
            "上海", "民盟上海", "1946",
            "Wang Shao-ao", "Shen Chih-yuan",
        ],
        "related_persons": ["wang-shao-ao", "shen-chih-yuan", "huang-ching-wu",
                             "shih-fu-liang", "peng-wen-ying", "sha-chien-li",
                             "huang-yen-pei"],
    },

    # ╔══════════════════════════════════════════════════════════════
    # ║ Ⅲ. 国共内战与民盟受难期（1946.7 - 1947.11）
    # ╚══════════════════════════════════════════════════════════════
    {
        "slug": "li-wen-bloodshed-1946",
        "name": "李闻血案（昆明李公朴、闻一多遇刺）",
        "phase": "p3-martyr-1946-1949",
        "date_label": "1946.7.11–15",
        "sort_date": "1946-07-11",
        "summary": (
            "1946 年 7 月 11 日，民盟中央执行委员、救国会七君子之一**李公朴**"
            "在昆明西仓坡遭国民党特务暗杀；7 月 15 日，民盟昆明支部宣传委员、"
            "清华大学教授、诗人**闻一多**在西南联大住所附近遭国民党特务暗杀，"
            "两案相隔仅 4 天。「李闻血案」震动全国，成为国共内战前夕"
            "民盟与国民党决裂的关键节点。毛泽东在《别了，司徒雷登》中"
            "专门提到「闻一多拍案而起」，李闻精神成为民盟一面旗帜。"
        ),
        "search_terms": [
            "Kunming", "assassin", "assassination",
            "Li Kung-pu", "Wen I-tuo", "李公朴", "闻一多", "昆明",
            "1946 July", "1946 7",
        ],
        "related_persons": ["li-kung-pu", "wen-i-tuo"],
    },
    {
        "slug": "tu-pin-cheng-martyr-1947",
        "name": "杜斌丞西安殉难",
        "phase": "p3-martyr-1946-1949",
        "date_label": "1947.10.7",
        "sort_date": "1947-10-07",
        "summary": (
            "1947 年 10 月 7 日，**民盟西北总支部主任委员、民盟中央常委杜斌丞**"
            "在西安被国民党杨虎城旧部胁迫处决。陕北榆林人，民盟西北烈士。"
            "毛泽东称其为「中国共产党的忠实朋友」。"
            "杜斌丞殉难发生在民盟被宣布「非法」前夕，是国民党对民盟"
            "实施政治和肉体双重打击的标志性事件。"
        ),
        "search_terms": [
            "Tu Pin-cheng", "Sian", "Xi'an", "Yang Hu-cheng",
            "杜斌丞", "西安", "1947",
        ],
        "related_persons": ["tu-pin-cheng"],
    },
    {
        "slug": "meng-banned-1947",
        "name": "民盟被国民党宣布「非法团体」",
        "phase": "p3-martyr-1946-1949",
        "date_label": "1947.10–11",
        "sort_date": "1947-10-28",
        "summary": (
            "**1947 年 10 月**，国民党政府悍然宣布民盟为「非法团体」；"
            "**1947 年 11 月**，民盟总部被迫解散。民盟主席张澜、宣传委员会主任"
            "罗隆基同时被软禁于上海虹桥疗养院。"
            "民盟地方组织和盟员被迫转入地下斗争，海外组织在香港、纽约等地"
            "积极开展活动继续与国民党进行斗争。这一事件标志民盟与国民党"
            "彻底决裂，民盟全面转向与中共合作的道路。"
        ),
        "search_terms": [
            "Democratic League illegal", "banned", "outlawed",
            "Hongqiao", "虹桥", "1947 October", "1947 November",
            "Chang Lan", "Lo Lung-chi",
        ],
        "related_persons": ["chang-lan", "lo-lung-chi", "chang-po-chun"],
    },

    # ╔══════════════════════════════════════════════════════════════
    # ║ Ⅳ. 香港复盘与新政协期（1947.12 - 1949.10）
    # ╚══════════════════════════════════════════════════════════════
    {
        "slug": "meng-3rd-plenum-hk-1948",
        "name": "民盟一届三中全会（香港）",
        "phase": "p4-mao-era-1949-1976",  # 跨期事件，归入建国前后过渡（注：实际应有独立香港复盘阶段，此处归为前期最贴近的过渡）
        "date_label": "1948.1",
        "sort_date": "1948-01-05",
        "summary": (
            "**1948 年 1 月**，民盟在香港召开一届三中全会，成立临时总部，"
            "由章伯钧主持。会议**公开宣布同中国共产党携手合作**，"
            "为彻底摧毁国民党反动政府、实现民主和平独立统一的新中国而奋斗。"
            "这是民盟政治路线的关键转折——从「中间路线」转向"
            "「彻底与中共合作」。"
        ),
        "search_terms": [
            "Hong Kong", "Hongkong", "third plenum",
            "Chang Po-chun", "香港", "1948 January",
        ],
        "related_persons": ["chang-po-chun", "shen-chun-ju"],
    },
    {
        "slug": "may-day-call-1948",
        "name": "响应中共「五一口号」",
        "phase": "p4-mao-era-1949-1976",
        "date_label": "1948.5",
        "sort_date": "1948-05-05",
        "summary": (
            "**1948 年 5 月**，民盟与各民主党派一起通电响应中国共产党"
            "「**五一口号**」（召开新政治协商会议、成立民主联合政府的号召）。"
            "这是民盟历史上具有决定性意义的政治表态，标志民盟"
            "全面认同中共领导下的新政协路线，从此与中共形成稳固政治联盟。"
        ),
        "search_terms": [
            "May Day", "new political consultative",
            "五一口号", "新政协", "1948 May",
        ],
        "related_persons": ["shen-chun-ju", "chang-po-chun", "lo-lung-chi"],
    },
    {
        "slug": "peiping-mediation-1949",
        "name": "北平和平接触（傅作义和平起义）",
        "phase": "p4-mao-era-1949-1976",
        "date_label": "1949.1",
        "sort_date": "1949-01-15",
        "summary": (
            "**1949 年 1 月**，民盟北平负责人**张东荪**（燕京大学哲学教授）"
            "作为民盟代表参与北平和平接触斡旋，向傅作义传达中共条件，"
            "是北平和平解放（1949.1.31）的关键中介之一。"
            "这一事件展现民盟作为「第三方面」在国共对峙末期发挥的独特政治作用。"
        ),
        "search_terms": [
            "Peiping", "Peking", "Beiping", "Fu Tso-yi",
            "Chang Tung-sun", "北平", "傅作义", "1949",
        ],
        "related_persons": ["chang-tung-sun"],
    },
    {
        "slug": "huang-ching-wu-martyr-1949",
        "name": "黄竞武上海殉难",
        "phase": "p4-mao-era-1949-1976",
        "date_label": "1949.5.12",
        "sort_date": "1949-05-12",
        "summary": (
            "**1949 年 5 月 12 日**，上海解放（5.27）前夕，"
            "民盟中央组织委员会委员、黄炎培次子**黄竞武**"
            "被国民党保密局秘密杀害于上海警备司令部，年仅 46 岁。"
            "黄竞武自 1945 年 12 月来沪筹建民盟上海支部，"
            "是上海民盟最知名烈士，也是民盟受难烈士时期的最后一位牺牲者。"
        ),
        "search_terms": [
            "Huang Ching-wu", "Shanghai", "黄竞武", "上海", "1949 May",
        ],
        "related_persons": ["huang-ching-wu", "huang-yen-pei"],
    },
    {
        "slug": "first-cppcc-1949",
        "name": "中国人民政治协商会议第一届全体会议",
        "phase": "p4-mao-era-1949-1976",
        "date_label": "1949.9.21–30",
        "sort_date": "1949-09-21",
        "summary": (
            "**1949 年 9 月 21-30 日**在北平召开新政治协商会议第一届全体会议，"
            "民盟派出代表团出席，参加中华人民共和国的筹建工作。"
            "民盟代表包括张澜（被推选为中央人民政府副主席）、沈钧儒（最高人民法院院长）、"
            "章伯钧、罗隆基、张东荪、史良（首任司法部长）、楚图南、费孝通等 8 位核心人物。"
            "这是民盟从「被取缔的反对党」转为「新中国奠基政党」的标志事件。"
        ),
        "search_terms": [
            "Chinese People's Political Consultative",
            "CPPCC", "new political consultative",
            "新政协", "政协一届", "1949 September",
            "Chang Lan", "Shen Chun-ju", "Shih Liang",
        ],
        "related_persons": ["chang-lan", "shen-chun-ju", "chang-po-chun",
                             "lo-lung-chi", "chang-tung-sun", "shih-liang",
                             "chu-tu-nan", "fei-hsiao-tung"],
    },

    # 关键事件清单聚焦于 1941-1949 民盟史阶段（民盟创立至新政协建国）；
    # 1949 年之后的内容遵循平台前台展示边界，仅作内部档案翻译背景参考。
]


# 阶段元数据（用于事件索引页分组展示）
# 与 person_archive.PERSON_GROUPS 共用 phase slug 体系
EVENT_PHASES = [
    ("p1-founding-1941-1944",
     "Ⅰ. 民盟创立与三党三派合组期（1941.3 - 1944.9）"),
    ("p2-pcc-1944-1946",
     "Ⅱ. 抗胜利与政协斡旋期（1944.9 - 1946.6）"),
    ("p3-martyr-1946-1949",
     "Ⅲ. 国共内战与民盟受难期（1946.7 - 1947.11）"),
    ("p4-mao-era-1949-1976",
     "Ⅳ. 香港复盘与新政协建国期（1947.12 - 1949.10）"),
    ("p5-reform-1979",
     "Ⅴ. 新时期民盟新生期（1976.10 - 至今）"),
]


def event_by_slug(slug: str):
    for evt in KEY_EVENTS:
        if evt["slug"] == slug:
            return evt
    return None
