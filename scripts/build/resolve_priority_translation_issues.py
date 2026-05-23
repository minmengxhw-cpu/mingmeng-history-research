#!/usr/bin/env python3
"""Apply curated fixes for high-priority translation quality issues."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"


FIXES: dict[int, tuple[str, str]] = {
    844: (
        "human-excerpt",
        """【相关段落摘译】

报道称，谈到中国和平前景时，欧文斯认为，只要中共坚持保留自己的军队，中国中央政府就不可能组成一个包括中共在内的各党派联合政府。他回顾马歇尔将军一年前为促成中国联合政府所作的努力，并把马歇尔使华失败归因于中共拒绝以放弃军队换取在联合政府之下建立国家军队。

同栏还提到，中国民主同盟的四位主要领导成员近期被政府指控为“中共的……”相关人员，原文此处因 OCR 和版面混栏而残缺。该页还刊有关于联合国善后救济总署物资、华北封锁和反共封锁的报道。

【校订说明】

本页涉及联合政府、马歇尔使华失败解释及民盟领导人遭政府指控，是1947年内战全面化语境下观察民盟政治处境的相关材料。中文侧采用相关段落摘译。""",
    ),
    845: (
        "human-excerpt",
        """【相关段落摘译】

上海8月4日电：中国民主同盟一名发言人称，广西省已有一百多名民盟成员被当局“围捕”。报道说，当局指控这些民盟成员因所谓亲共立场而进行宣传活动。

同页随后转入华北战局背景：北平已被中共包围，是华北少数由国民党控制的孤立据点之一。铁路交通时通时断，取决于中共是否切断补给线。报道概括称，国民党控制城市，中共控制乡村；魏德迈将军可以清楚看到国民党与中共之间的分歧，但和平并未到来。

【校订说明】

该页民盟相关段落清楚，直接价值在于记录1947年8月广西民盟成员遭围捕事件；其余华北战局作为背景保留。""",
    ),
    748: (
        "human-excerpt",
        """【相关段落摘译】

4. 关于工会与资本关系

科瓦廖夫报告称，1949年11月亚洲各国工会会议期间，李立三反对成立亚洲职业组织联络局。报告还批评李立三作为中华全国总工会副主席，参与推动并在报纸上公布“劳资关系规则”。科瓦廖夫认为，这些规则违背政治协商会议共同纲领，并恶化私营企业工人的处境。

5. 关于报刊

自1949年9月起，报刊中关于党内生活、党组织吸收工人入党、巩固人民民主专政以及推进革命改革的材料明显减少。报告认为，这种做法是为了安抚国内外资产阶级资本主义成分。

6. 关于国家机器

科瓦廖夫引述斯大林1949年6月的意见：“不要再拖延中央政府的组建……中国处于无政府状态。从国内政治角度看是危险的，从国际形势角度看也是危险的。”报告称，1949年9月召开的政治协商会议成立中央人民政府，实质上是由各民主党派和团体组成的联合政府。1949年10月，中央政府机关建立，共有37个部委和中央机构，其中22个由共产党人领导，15个由其他党派人士和无党派资产阶级民主人士领导，其中包括前国民党将领傅作义、陈建等被报告称为“反动成分”的人物。报告强调，共产党人掌握主要领导性部委和中央机关。

【校订说明】

本页为科瓦廖夫致斯大林报告的第4至第6节，重点价值在于苏方对1949年新政协、联合政府结构及民主党派进入国家机器的内部观察。中文侧采用相关段落摘译，保留原文全文用于逐字核对。""",
    ),
    827: (
        "not-relevant-excluded",
        """【剔除说明】

本件为1982年 CIA《World Factbook》类综合参考资料，时间晚于本库1941-1950年主线，也不是关于中国民主同盟的专题档案。此前因全文检索命中“Democratic League”而误入相关文献队列。已改为前台不展示，仅保留原始记录以便追溯。""",
    ),
    853: (
        "human-excerpt",
        """【相关段落摘译】

上海8月22日电：《大公报》报道，76岁的中国民主同盟领导人张澜在四川成都遭到袭击并被殴打。报道说，张澜是在参加两名民主同盟重要成员的追悼活动后遇袭的。报道还提到，张澜是辛亥革命以来的知名自由派人物。

同页其他栏还刊有南京谈判、国共冲突、苏联及联合国安理会等新闻，并混有大量广告、启事和国际电讯。与民盟直接相关的核心信息，是港报转述《大公报》关于张澜遇袭的报道，以及该事件发生在国共和谈紧张、民盟人士遭受压力的背景下。

【校订说明】

该页为整版港报 OCR，混栏严重。中文侧采用相关段落摘译；原始 OCR 全文保留，用于日后按版面图像复核。""",
    ),
    834: (
        "human-excerpt",
        """【相关段落摘译】

上海电：在评论美国在华行动时，中国民主同盟把美国当前对华政策同日本过去在中国的军事行动相比较，并警告美国人民注意其政府行为可能造成的后果。报道称，民盟认为中国问题已经成为一个具体案例，关系到美国是否会在中国重演外来干预的危险路径。

同版同时刊有联合国、苏联外交部长莫洛托夫、法国政局、煤矿罢工和航空交通等国际新闻。与本库主题直接相关的是“中国民主同盟对美国在华行动的警告”这一段，反映民盟在国民大会召开期间继续以公开舆论方式批评外部干预和国民政府路线。

【校订说明】

该页为整版英文报纸 OCR，中文侧只摘译民盟相关段落；非中国政情栏目保留在原文全文中，不进入正文译文。""",
    ),
    841: (
        "human-excerpt",
        """【相关段落摘译】

报道提到，中共决定于12月12日在延安自行召集“国民大会”，并成立所谓“民主联合政府”；同时还将八路军与东北民主联军合并。报道认为，这些主张实际上是在要求各方“忘记过去十二个月发生的一切，回到一年前的起点重新尝试”。

报道还指出，各民主党派是否参加南京国民大会，立场仍不明确。蒋介石方面则表示，愿意为和平及政府地位作出牺牲。该页反映出国民大会召开后，国共双方围绕政治代表性与联合政府问题继续角力，第三方面和民主党派的态度仍被视为重要变量。

【校订说明】

本页未出现完整民盟专名，但与国民大会、联合政府和民主党派立场直接相关，保留为相关文献。""",
    ),
    860: (
        "human-excerpt",
        """【相关段落摘译】

本页题注为“第三方面立场”，OCR 文本中混有大量国际新闻、广告和残缺栏文。可辨识信息显示，报道关注国共之外的第三方面政治力量，并把其态度置于国民政府改组、战后中国政局和国际舆论的背景下讨论。

就民盟研究而言，本页的价值主要不在完整新闻叙事，而在于证明香港英文报纸持续把“第三方面”作为解释中国政治的一类独立观察框架。后续若取得版面图像，应优先复核含有 third party / third force / Democratic League 的栏文。

【校订说明】

原译文为拒译说明，现改为研究摘译与复核说明。原文全文仍保留，待图像页校对。""",
    ),
    842: (
        "human-excerpt",
        """【相关段落摘译】

中国民主同盟作为中国第三大政党，当时正与中共共同抵制改组后的政府。民盟发表约1500字宣言，称改组后的政府既不能给中国带来和平，也不能促进民主，因为它并不是按照上一年各党派政治协商会议的精神和程序组成的。

声明还批评现政府对杜鲁门总统反共政策的理解与宣传，认为这一路线会阻碍人类进步。该报道显示，1947年政府改组后，民盟仍以政协程序合法性和和平民主原则为主要论据，反对国民政府单方面改组。

【校订说明】

本页是港报转述民盟公开宣言的高价值材料。非中国政情的国际短讯不纳入中文正文译文。""",
    ),
    866: (
        "human-excerpt",
        """【相关段落摘译】

南京12月22日电：报道讨论民盟被解散后中国战局和第三方面的政治动向。可辨识段落中，政府方面人士谈及中共在满洲的军事行动，并称中共正在利用苏联顾问；报道同时记录沈阳撤离、营城子和阜新煤矿失守、烟台和本溪煤矿被包围等战局信息。

这页对民盟史的价值在于背景层面：民盟被宣布非法、组织活动转向香港之后，港报把“第三方面”政治可能性同国共内战扩大、东北局势恶化联系起来观察。

【校订说明】

该页整版混栏明显，现采用相关背景摘译；原文全文保留以供图像复核。""",
    ),
    847: (
        "human-excerpt",
        """【相关段落摘译】

报道显示，1948年1月初香港舆论同时关注中共在湖南、湖北、豫皖鄂边区及满洲前线的军事行动，以及第三方面政治力量在香港的动向。题注标明该页与民盟香港三中全会期相关，说明港报把民盟在港活动置于内战扩大和国民政府危机的背景中理解。

本页可辨识的直接政情包括：中共可能向湖南渗透，刘伯承部在湖北发动牵制性攻击，大别山方向部队试图突围，满洲前线暂时平静可能难以持续。与民盟研究直接相关的部分，需结合版面图像进一步核对“香港三中全会”所在栏文。

【校订说明】

OCR 未能完整还原民盟栏文，中文侧先作背景摘译和复核提示。""",
    ),
    872: (
        "human-excerpt",
        """【相关段落摘译】

报道称，拉铁摩尔认为蒋夫人访美或许能激起美国公众对国民党的同情，但中国局势已经发展到难以挽回蒋介石地位的程度。他预测中国将成立联合政府。报道还讨论徐州战役、蚌埠方向突围、沪宁之间防御及汤恩伯部队部署等军事背景。

本页关于“第三方面”的价值在于，它把联合政府预期、国民政府军事危机和美国舆论动员联系在一起，反映1948年底香港英文舆论对国民政府前景及非国共政治空间的判断。

【校订说明】

该页为整版混栏 OCR，现保留相关段落摘译；原文全文继续保留。""",
    ),
}

PREFIX_ONLY: dict[int, tuple[str, str]] = {
    449: (
        "reference-summary",
        """【全页提要】

本件为 CIA 1949年10月《中国行政区划》参考报告，正文和表格极长。它不是民盟专题档案，但可作为1947年前后国民政府行政区划、地名、人口与面积统计的背景工具，用于核对民盟人物活动地点、国共控制区叙述和档案地名。中文侧保留目录和主要说明性段落译文；行政区划长表不强制逐项翻译，原文全文用于检索和核对。

""",
    )
}


def upsert_translation(conn: sqlite3.Connection, page_id: int, text: str, status: str) -> None:
    row = conn.execute(
        "SELECT id FROM translations WHERE page_id=? AND language='zh-CN'",
        (page_id,),
    ).fetchone()
    if row:
        tid = row[0]
        conn.execute(
            "UPDATE translations SET text=?, status=?, translator=? WHERE id=?",
            (text, status, "xiaoban-priority-qc-2026-05-23", tid),
        )
    else:
        cur = conn.execute(
            "INSERT INTO translations(page_id, language, translator, status, text) VALUES (?, 'zh-CN', ?, ?, ?)",
            (page_id, "xiaoban-priority-qc-2026-05-23", status, text),
        )
        tid = cur.lastrowid
    try:
        conn.execute("DELETE FROM translation_fts WHERE rowid=?", (tid,))
        page = conn.execute(
            """
            SELECT d.title, p.page_label
            FROM pages p
            JOIN documents d ON d.id = p.document_id
            WHERE p.id=?
            """,
            (page_id,),
        ).fetchone()
        conn.execute(
            "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
            (tid, page[0], page[1] or "doc-level", text),
        )
    except sqlite3.OperationalError:
        pass


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    for page_id, (status, text) in FIXES.items():
        upsert_translation(conn, page_id, text.strip(), status)
        conn.execute("DELETE FROM translation_quality_issues WHERE page_id=?", (page_id,))

    for page_id, (status, prefix) in PREFIX_ONLY.items():
        row = conn.execute(
            "SELECT text FROM translations WHERE page_id=? AND language='zh-CN'",
            (page_id,),
        ).fetchone()
        text = row[0] if row else ""
        if prefix.strip() not in text:
            text = prefix + text
        upsert_translation(conn, page_id, text.strip(), status)
        conn.execute("DELETE FROM translation_quality_issues WHERE page_id=?", (page_id,))

    conn.execute(
        """
        UPDATE document_classifications
        SET grade='前台不展示',
            score=5,
            reason='1982 年 CIA World Factbook 综合参考资料，时间和主题均不属于 1941-1950 民盟研究主线；保留记录但不进入前台。'
        WHERE document_id = (
            SELECT document_id FROM pages WHERE id=827
        )
        """
    )
    conn.execute(
        """
        UPDATE document_classifications
        SET grade='背景材料',
            score=35,
            reason='CIA 1949 年中国行政区划参考报告，用作地名、行政区划、人口面积统计背景；非民盟专题档案。'
        WHERE document_id = (
            SELECT document_id FROM pages WHERE id=449
        )
        """
    )
    conn.commit()
    conn.close()
    print(f"Applied {len(FIXES)} priority translation fixes.")


if __name__ == "__main__":
    main()
