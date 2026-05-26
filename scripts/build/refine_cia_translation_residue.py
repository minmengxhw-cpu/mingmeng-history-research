#!/usr/bin/env python3
"""Polish CIA translations by removing OCR residue and model-facing notes."""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = ROOT / "data" / "research_index.sqlite"


FULL_FIXES: dict[int, str] = {
    429: """**机密/参阅**

**情报报告**
**日期：** 1950年5月
**主题：** 中国人民政治协商会议代表抵达广州
**国家：** 中国
**页数：** 1

本报告为未经评估的信息。

尽管以下人员并非全部是1949年9月北平中国人民政治协商会议（CPPCC）的正式指定代表，但他们很可能均出席了会议。他们于1950年1月20日从北平抵达广州。

1. 李梅侯，又名乃蒙空·纳维加蓬，泰国代表。

2. 关文森，1946年在吉隆坡加入中国民主同盟，是该组织创始成员之一。其代表中国致公党出席中国人民政治协商会议。

3. 戴祖良，前柔佛州中国民主同盟负责人。其代表马来亚民主华侨出席中国人民政治协商会议。

4. 王庆春，前怡保中国民主同盟领导人，坚定左翼人士，与马来亚共产党恩明钦女士有联系，可能出席了中国人民政治协商会议。

5. 刘泰生，据信来自吉打州亚罗士打附近。

6. 陈仁义，澳大利亚中国国民党革命委员会组织者。

【校订说明】

原件页眉、报告编号和解密戳记 OCR 噪声较多，中文侧删去无研究价值的页眉编码，保留人物名单、海外民盟身份、政协出席关系和两条身份比对意见。关文森与戴祖良均可能曾参与1949年6月北平新政协筹备委员会会议，显示海外华侨民盟网络与新政协代表安排之间的联系。""",
    446: """**机密**

**中央情报局情报报告**
**国家：** 中国
**分发日期：** 1949年6月13日
**主题：** 中共关于联合政府的计划
**页数：** 1

本报告为未经评估的信息。

1. 中国共产党已开始在北平同各小党派代表举行会议，商讨联合政府成立后的合作安排。会议被称为“施政纲领”会议。

2. 尚未抵达北平的著名“自由派”人士仍在被召集。与会者在通常为六个月的“军事管制时期”结束以前不得自由行动。此项限制同样适用于中国民主同盟、中国国民党革命委员会、中国农工民主党以及其他类似的小团体。

3. 在南京，上述党派的二十余名代表被拘禁于中山路上一座前华侨招待所内。拘禁理由是声称这些人员面临危险；实际效果则是在联合政府成立前夕，使这些代表除接受中共方案外别无选择。中共预计到那时已能掌控局面。

【校订说明】

原件含较多页眉编号、来源遮盖和解密记录。中文侧删除无实质研究价值的 OCR 编码，保留与民盟相关的核心信息：中共召集小党派、限制民盟等党派代表行动，以及南京代表被集中安置的情况。""",
    471: """**中央情报局情报报告**

本文件包含影响美国国防的信息，其含义见美国法典第18编第793条和第794条。禁止复制此表格。

**国家：** 印度尼西亚
**主题：** 橡胶走私
**分发日期：** 1953年6月29日
**页数：** 1

1953年第一季度，100吨一等和二等烟胶片失踪，据推测是从西婆罗洲坤甸和三发地区的下列亲共公司走私至共产党中国：

1. 大成公司，坤甸大亚路138号。

2. 建诚公司，邦戛萨朱尔市场617号。

3. 永成发公司，坤甸大亚路。

4. 日成公司，邦戛马来由村。

5. 新兴兄弟公司，邦戛中央市场路612号。

6. 钟锡良，邦戛萨朱尔市场。

7. 集益公司，三发帕吉市场。

【校订说明】

本件与民盟主线关系较弱，价值主要在于呈现1950年代初 CIA 对华侨商业网络、亲共公司与对华物资流动的观察。中文侧将印尼地名和市场名转为音译，删除分发代码。""",
    821: """**绝密**

**中央情报局每日简报**
**日期：** 1958年10月15日

## 一、共产主义集团

**台湾海峡局势。** 一份由国民党高级成员出版的国民党中国报纸于10月14日称，如果美国同意防卫金门和马祖，台北可能会接受美国关于减少两岛兵力的要求。该报道可能是一个试探气球，用以观察美国反应。10月14日没有重大的军事活动。

**苏联—南斯拉夫。** 有迹象表明莫斯科与南斯拉夫之间的争端可能正在缓和。赫鲁晓夫在10月8日特意会见即将离任回国的南斯拉夫大使。铁托四天后讲话的温和语气，可能反映其希望贝尔格莱德与莫斯科之间的关系至少不再继续恶化。

**苏联—芬兰。** 苏联对芬兰的经济压力正在加大，可能意在促成一个对苏联更有利的政府取代现有芬兰联合政府。赫尔辛基政府面临严重经济问题，如果不能处理不断增长的失业问题，可能引发内阁危机。

## 二、亚洲—非洲

**伊拉克。** 自七月革命以来，在当地共产党人的鼓动下，伊拉克库尔德人中的分离主义情绪有所增长。库尔德领导人很可能寻求独立或更大自治。最近从苏联返回伊拉克的穆斯塔法·巴尔扎尼公开宣誓效忠现政权；如果他重新采取分离主义立场，很可能获得伊拉克大多数库尔德人的支持。

**印度—巴基斯坦。** 印度政府认为巴基斯坦的新军事政权不会立即威胁印度安全，这增加了双方作出实质性让步的可能性。新德里预计短期内不会受到卡拉奇方面的重大困扰。

**泰国。** 泰国军事集团领导人沙立元帅计划在一周内秘密返回曼谷。他缩短在英国停留时间，显然是因为收到其军事追随者之间持续不和的报告，并受到他侬总理特别请求的影响。

**塞浦路斯。** 北大西洋理事会于10月13日达成协议，英国、希腊和土耳其将在各自政府最终批准后近期就塞浦路斯问题举行会议，这为通过谈判解决问题提供了新的机会。

## 三、西方

**法国—阿尔及利亚。** 戴高乐命令在阿尔及利亚的法国军队停止政治活动，并呼吁广泛参与11月选举，这对欧洲定居者构成挑战。

## 最新消息

**黎巴嫩新内阁。** 贝鲁特宣布就一个四人临时内阁达成协议。卡拉米将作为穆斯林叛乱分子的代表继续担任新联合政府首脑；皮埃尔·杰马耶勒代表前夏蒙“效忠派”；其他成员为资深政治家侯赛因·乌韦尼和雷蒙·埃德。新政府暂时缓和了基督教武装派别对卡拉米政府的压力，但由于仅代表逊尼派穆斯林和马龙派基督徒，未来扩大内阁时仍可能重新出现政治困难。

【校订说明】

原译文含模型说明、页眉噪声和密级 OCR 乱码。此处改为研究用摘译，保留与中国、台湾海峡和冷战背景有关的主要条目；分发名单不再逐项转录。""",
}


REPLACEMENTS: dict[int, list[tuple[str, str]]] = {
    449: [
        ("Ol\n\n154 BZ20AZY\n\n", ""),
        ("\n\nRO a ae\n)\n密级变更为：19 fc\n重新审查开放\n", "\n"),
        ("院辖市", "院辖市"),
        ("Ngari", "阿里"),
        ("Tsang", "藏区"),
        ("Tsingtao", "青岛"),
    ],
    470: [
        (": ; IX\\\n\n", ""),
        ("**机密** | 份数编号 OF oe,\n", "**机密**\n"),
        ("| S-E-C-R-E-I 2\n\n", ""),
        ("8~E-C-B-E-I\n\n“\n\n", ""),
        ("\\\n3\nCO)\n\n: | S~E-C-R-E-T\n", "\n**机密**\n"),
        ("\n\\\n\nNS\n\nS-E-C-R-E-T\n", "\n"),
        ("\n\\\na\n\nS-E-C-B-E-T\n", "\n"),
        ("S-E-C-R-E-T", "机密"),
        ("S-E-C-B-E-T", "机密"),
        ("GR-E-T", "机密"),
        ("EC-R-E-IT", "机密"),
        ("SEC-R-E-", "机密"),
    ],
    776: [
        ("```markdown\n", ""),
        ("**美国国务院。** 国务院已授权南京大使馆自行决定是否将埃弗雷特航运公司的SS Coastal Champion号轮船", "**美国国务院。** 国务院已授权南京大使馆自行决定是否将埃弗雷特航运公司的“海岸冠军”号轮船"),
        ("\n---\n", "\n"),
    ],
    798: [
        ("**成本代码：** ZORA", "**成本代码：** 原档代码已略"),
        ("（注：原文为CHIN Chung-hua，疑为笔误，应为赵超构）", "（注：原文疑有误识，按上下文译为赵超构）"),
        ("（注：原文为CHOU Fan-yang，音译）", "（注：原文音译）"),
        ("（注：原文为CHIN Fen-li，应为陈铭德）", "（注：原文疑有误识，按上下文译为陈铭德）"),
        ("（注：原文为PU Hsi-hsiu，应为浦熙修）", "（注：按上下文译为浦熙修）"),
        ("（注：原文为ANG Fao-elt，音译，应为邓季惺）", "（注：原文疑有误识，按上下文译为邓季惺）"),
        ("（注：原文为CHEN Ling-te，音译）", "（注：原文音译）"),
        ("（注：原文为HSÜAN Ti-chih，音译）", "（注：原文音译）"),
        ("（注：原文为CHaG Chao-kou，音译）", "（注：原文音译）"),
    ],
    808: [
        ("**情报报告** 编号：CPNO.\n\n", "**情报报告**\n\n"),
    ],
    826: [
        ("1976年12月1日，星期三 CI NIDC 76-280C", "1976年12月1日，星期三"),
    ],
}


STATUS_OVERRIDES = {
    438: "reference-summary",
    446: "human-excerpt",
    471: "reference-summary",
    821: "human-excerpt",
}


def update_fts(conn: sqlite3.Connection, translation_id: int, page_id: int, text: str) -> None:
    row = conn.execute(
        """
        SELECT d.title, p.page_label
        FROM pages p
        JOIN documents d ON d.id = p.document_id
        WHERE p.id=?
        """,
        (page_id,),
    ).fetchone()
    conn.execute("DELETE FROM translation_fts WHERE rowid=?", (translation_id,))
    conn.execute(
        "INSERT INTO translation_fts(rowid, language, title, page_label, text) VALUES (?, 'zh-CN', ?, ?, ?)",
        (translation_id, row[0], row[1] or "doc-level", text),
    )


def polish_text(page_id: int, text: str) -> str:
    if page_id in FULL_FIXES:
        return FULL_FIXES[page_id].strip()
    for old, new in REPLACEMENTS.get(page_id, []):
        text = text.replace(old, new)
    if page_id == 470:
        text = re.sub(r"\n?\\\n?", "\n", text)
        text = re.sub(r"\n(?:NS|a)\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    page_ids = sorted(set(FULL_FIXES) | set(REPLACEMENTS) | set(STATUS_OVERRIDES))
    changed = 0
    for page_id in page_ids:
        row = conn.execute(
            "SELECT id, text, status FROM translations WHERE page_id=? AND language='zh-CN'",
            (page_id,),
        ).fetchone()
        if not row:
            continue
        new_text = polish_text(page_id, row["text"] or "")
        new_status = STATUS_OVERRIDES.get(page_id, "human-reviewed")
        if new_text == (row["text"] or "") and new_status == (row["status"] or ""):
            continue
        conn.execute(
            """
            UPDATE translations
            SET text=?, status=?, translator='小班-cia-polish-2026-05-26'
            WHERE id=?
            """,
            (new_text, new_status, row["id"]),
        )
        update_fts(conn, int(row["id"]), page_id, new_text)
        changed += 1
    conn.commit()
    conn.close()
    print(f"Refined {changed} CIA translation pages.")


if __name__ == "__main__":
    main()
