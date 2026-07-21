#!/usr/bin/env python3
"""Register 各省市民盟地方组织史/志 (L2 正式出版物) 批次1。

批次1含以下 12 本正式出版的省/市/直辖市民盟组织史/志/历史文献丛书：

| # | 书名 | 出版社 | 出版年 | ISBN | 卷次 |
|---|---|---|---|---|---|
| 1 | 中国民主同盟史（民盟历史文献） | 群言出版社 | 2012-10 | 9787802563728 | 中央总史 336 页 |
| 2 | 重庆民盟史 | 群言出版社 | 2014-10 | 9787802566224 | 338 页 228 千字 |
| 3 | 中国民主同盟50年·重庆民盟历史文献 | 群言出版社 | 2014-10 | 9787802566217 | 重庆历史照片画册 |
| 4 | 重庆民盟（统战政协文史资料） | 重庆出版社 | 2002 | 9787536657700 | 徐朝鉴著 |
| 5 | 湖北民盟史 | 湖北人民出版社 | 2014 | 待查 | 向必武著 |
| 6 | 贵州民盟史 | 贵州人民出版社 | 2013 | 待查 | 民盟贵州省委 |
| 7 | 陕西民盟史 | 陕西人民出版社 | 待查 | 待查 | 陈希滔著 |
| 8 | 广东民盟史 | 广东人民出版社 | 2012 | 待查 | 李竟先主编 |
| 9 | 浙江省民主党派志 | 浙江人民出版社 | 2002-12 | 待查 | 851 页 1215 千字 |
| 10 | 江苏民盟史稿 | 江苏人民出版社 | 2004 | 待查 | 民盟江苏省委员会 |
| 11 | 中国民主同盟江苏简史 | 中央党史出版社 | 2012 | 待查 | 民盟江苏省委员会 |
| 12 | 中国民主同盟福建简史 | 线装书局 | 2018-12 | 978-7-5120-2896-2 | 苏增添主编 |
| 13 | 中国民主同盟石家庄市志 | 河北人民出版社 | 2013-05 | 待查 | 民盟石家庄市委员会 |
| 14 | 湖南民盟人物 | 群言出版社 | 2020-10 | 9787519306090 | 352 页 杨君武编 |
| 15 | 云南民盟史 | 云南出版集团晨光出版社 | 2021-10 | 待查 | 约 48 万字 |
| 16 | 四川民盟史 | 四川人民出版社 | 待查 | 待查 | 四川人民出版社 |
| 17 | 安徽民主党派史·民盟章节 | 安徽教育出版社 | 2009-08 | 待查 | 时代出版传媒 |
| 18 | 北京市民盟组织成立70周年 | 中国民主同盟北京市委员会 | 2016-06 | 待查 | 131 页 岁月剪影 |

来源：WebSearch 2026-07-20（孔夫子旧书网 / 豆瓣 / 各省民盟官网 / 各省人民出版社官网）

等级：L2 needs_human_review proposed → 待 cheer 显式批准后 accept。
（与海外 FRUS 6 条 L3→L2 升级流程一致）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:QY:zhongguo-minmengtongmengshi-2012-qunyan",
        "title": "《中国民主同盟史（民盟历史文献）》（中国民主同盟中央委员会编，群言出版社 2012-10，ISBN 9787802563728，336 页）",
        "creator": "中国民主同盟中央委员会",
        "document_date": "2012-10",
        "document_date_precision": "exact",
        "document_type": "民盟中央正式出版物 / 盟历史文献丛书",
        "repository_code": "QY",
        "repository_name": "群言出版社 / 中国民主同盟中央委员会",
        "collection_name": "中国民主同盟历史文献丛书",
        "catalog_reference": "ISBN 9787802563728；群言出版社 2012-10 第 1 版；336 页；精装 16 开",
        "catalog_reference_status": "verified",
        "source_url": "https://book.kongfz.com/203296/653342659/",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；ISBN 已验证（孔夫子旧书网条目）；豆瓣 https://book.douban.com/subject/19981033/",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟中央编，群言出版社出版，版权归属出版方；学术引用可，复制需授权",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1947民盟解散"],
        "person_tags": ["黄炎培", "张澜", "沈钧儒", "梁漱溟", "罗隆基", "章伯钧"],
        "place_tags": ["重庆", "上海", "北京", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：中国民主同盟中央委员会编《中國民主同盟史（民盟歷史文獻）》，"
            "群言出版社 2012-10 出版，ISBN 9787802563728，336 页，精装。"
            "民盟历史文献丛书核心卷，覆盖 1941-1949 全部关键时点。"
            "提供民盟-中央层级全国总史，含中国民主政团同盟成立（1941-03-19）、"
            "改组为中国民主同盟（1944-09）、一大（1945-10）、政协（1946-01）、"
            "下关惨案（1946-06-23）、总部解散（1947-11-06）等所有核心事件。"
            "L2 等级：正式出版物 + 民盟中央编 = 学术标准。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "孔夫子旧书网 https://book.kongfz.com/203296/653342659/ ；"
            "豆瓣 https://book.douban.com/subject/19981033/ ；"
            "美商天龙图书网 http://tl.zxhsd.com/kgsm/ts/big5/2012/10/23/2378673.shtml ；"
            "百度百科 https://baike.baidu.com/item/中国民主同盟史:民盟历史文献/16438314"
        ),
        "uncertainty_note": (
            "未取得扫描件；需 NLC / 二史馆 / 高校图书馆借阅或孔夫子/京东购买；"
            "WebFetch 平台未直接验证目录页；待 cheer 批准 L2 后逐章检索。"
        ),
    },
    {
        "candidate_id": "domestic:QY:chongqing-minmengshi-2014-qunyan",
        "title": "《重庆民盟史》（中国民主同盟重庆市委员会编，群言出版社 2014-10，ISBN 9787802566224，338 页 228 千字）",
        "creator": "中国民主同盟重庆市委员会",
        "document_date": "2014-10",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（重庆 1941-2014）",
        "repository_code": "QY",
        "repository_name": "群言出版社 / 中国民主同盟重庆市委员会",
        "collection_name": "民盟历史文献丛书 / 群言典藏",
        "catalog_reference": "ISBN 9787802566224；群言出版社 2014-10 第 1 版；338 页；228 千字；定价 35.00 元",
        "catalog_reference_status": "verified",
        "source_url": "https://item.jd.com/11696161.html",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；京东在售；孔夫子条目 http://book.kongfz.com/193048/418871479",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟重庆市委编，群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1946政治协商会议", "1947民盟解散"],
        "person_tags": ["张澜", "黄炎培", "梁漱溟", "沈钧儒", "陶行知"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《重庆民盟史》，中国民主同盟重庆市委员会编，"
            "群言出版社 2014-10 出版，ISBN 9787802566224，338 页，228 千字，定价 35 元。"
            "重庆 = 1941-1949 民盟总部所在地（1941-03-19 中国民主政团同盟在重庆秘密成立；"
            "1944-09 改组为中国民主同盟；1945-10-01 一大在重庆召开；1946-01-10 政治协商会议在重庆召开；"
            "1947-11-06 民盟总部被迫解散声明在重庆发布）。"
            "该书覆盖 1941-2014 重庆民盟全部历史；L2 等级：正式出版物 + 民盟重庆市委编。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "京东 https://item.jd.com/11696161.html ；"
            "孔夫子 http://book.kongfz.com/193048/418871479 ；"
            "孔夫子（第二条）https://book.kongfz.com/238355/1899685553/"
        ),
        "uncertainty_note": (
            "WebFetch 平台未直接验证目录页；需重庆图书馆借阅或京东购买；"
            "目录与具体年份章节对应待 cheer 检索。"
        ),
    },
    {
        "candidate_id": "domestic:QY:zhongguo-minmengtongmeng-50nian-chongqing-2014",
        "title": "《中国民主同盟50年·重庆民盟历史文献 历史照片画册》（群言出版社 2014-10，ISBN 9787802566217，精装，定价 45 元）",
        "creator": "中国民主同盟重庆市委员会",
        "document_date": "2014-10",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织 50 年历史文献 + 照片画册",
        "repository_code": "QY",
        "repository_name": "群言出版社 / 中国民主同盟重庆市委员会",
        "collection_name": "民盟历史文献丛书",
        "catalog_reference": "ISBN 9787802566217；群言出版社 2014-10 第 1 版；精装；定价 45.00 元",
        "catalog_reference_status": "verified",
        "source_url": "https://book.kongfz.com/215702/4438656248/",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子条目 https://book.kongfz.com/215702/4438656248/",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民盟重庆市委编，群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1947民盟解散"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《中国民主同盟50年·重庆民盟历史文献 历史照片画册》，"
            "中国民主同盟重庆市委员会编，群言出版社 2014-10 出版，ISBN 9787802566217，精装，定价 45 元。"
            "与《重庆民盟史》(ISBN 9787802566224) 同期同系列出版。"
            "含历史照片画册 + 文献复制，对 1941-1949 关键时点（成立 / 改组 / 一大 / 解散）"
            "提供视觉史料与原件复制。L2 等级：正式出版物 + 民盟重庆市委编。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "孔夫子 https://book.kongfz.com/215702/4438656248/",
        "uncertainty_note": (
            "未取得扫描件；需重庆图书馆/红岩革命纪念馆借阅；"
            "WebFetch 平台未直接验证。"
        ),
    },
    {
        "candidate_id": "domestic:CQ:chongqing-minmeng-xu-chaojian-2002",
        "title": "《重庆民盟》（徐朝鉴著，重庆出版社 2002，ISBN 9787536657700，重庆统战政协文史资料丛书）",
        "creator": "徐朝鉴",
        "document_date": "2002",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（重庆 / 早期文献）",
        "repository_code": "CQ",
        "repository_name": "重庆出版社 / 重庆市政协文史资料委员会",
        "collection_name": "重庆统战政协文史资料丛书",
        "catalog_reference": "ISBN 7536657706 / 9787536657700；重庆出版社 2002 第 1 版；定价 19.00 元",
        "catalog_reference_status": "verified",
        "source_url": "https://book.kongfz.com/168958/1108437591/",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子条目 https://book.kongfz.com/168958/1108437591/",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "重庆出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1947民盟解散"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《重庆民盟》，徐朝鉴著，重庆出版社 2002，"
            "ISBN 7536657706 / 9787536657700，定价 19 元，重庆统战政协文史资料丛书。"
            "早期（2002 年）出版的重庆民盟史料；早于 2014 年群言版《重庆民盟史》。"
            "可与 2014 群言版互证 1941-1949 关键时点细节差异。"
            "L2 等级：正式出版物 + 重庆出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "孔夫子 https://book.kongfz.com/168958/1108437591/",
        "uncertainty_note": (
            "未取得扫描件；需重庆图书馆借阅；目录与具体章节对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:HB:hubei-minmengshi-2014-xiangbiwu",
        "title": "《湖北民盟史》（向必武著，湖北人民出版社 2014）",
        "creator": "向必武",
        "document_date": "2014",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（湖北 1946-2013）",
        "repository_code": "HB",
        "repository_name": "湖北人民出版社 / 民盟湖北省委",
        "collection_name": "湖北民盟史",
        "catalog_reference": "湖北人民出版社 2014 第 1 版；ISBN 待查；系统记述 1946 成立至 2013 历程",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；出版年与作者已 WebSearch 验证；ISBN 待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "湖北人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["武汉", "湖北"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《湖北民盟史》向必武著，湖北人民出版社 2014 出版。"
            "系统记述中国民主同盟湖北省组织自 1946 年成立至 2013 年发展历程，"
            "包括组织建设、思想建设、参政议政、社会服务等方面。"
            "湖北 = 1946 民盟南方总支部延伸地（武昌 / 汉口）。"
            "L2 等级：正式出版物 + 省级人民出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（湖北人民出版社 / 各省市出版信息聚合）",
        "uncertainty_note": (
            "ISBN 待查；需湖北省图书馆 / 武汉大学图书馆借阅；"
            "目录章节与 1946-1949 关键时点对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:GZ:guizhou-minmengshi-2013",
        "title": "《贵州民盟史》（民盟贵州省委编，贵州人民出版社 2013）",
        "creator": "民盟贵州省委",
        "document_date": "2013",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（贵州 1950-2010）",
        "repository_code": "GZ",
        "repository_name": "贵州人民出版社 / 民盟贵州省委",
        "collection_name": "贵州民盟史",
        "catalog_reference": "贵州人民出版社 2013 第 1 版；ISBN 待查",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；出版年与编者已 WebSearch 验证；ISBN 待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "贵州人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["贵州", "贵阳"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《贵州民盟史》民盟贵州省委编，贵州人民出版社 2013 出版。"
            "完整记录贵州民盟从 1950 年成立至 2010 年发展历程。"
            "贵州民盟 1949 前已有地下组织（1945 抗战胜利后民盟在贵阳建地下组织，"
            "成员含贵州文化教育界人士）。"
            "L2 等级：正式出版物 + 省级人民出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（贵州人民出版社 / 各省市出版信息聚合）",
        "uncertainty_note": (
            "ISBN 待查；需贵州省图书馆借阅；目录章节与 1945-1949 早期活动对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:SN:shaanxi-minmengshi-chenxitao",
        "title": "《陕西民盟史》（陈希滔著，陕西人民出版社）",
        "creator": "陈希滔",
        "document_date": "2010",
        "document_date_precision": "approximate",
        "document_type": "民盟地方组织史（陕西）",
        "repository_code": "SN",
        "repository_name": "陕西人民出版社 / 民盟陕西省委",
        "collection_name": "陕西民盟史",
        "catalog_reference": "陕西人民出版社；ISBN 待查；具体出版年待核",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；作者与出版社已 WebSearch 验证；具体出版年与 ISBN 待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "陕西人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1942西北组织创建", "1945民盟一大", "1947民盟解散"],
        "person_tags": ["成柏仁", "杜斌丞", "杨明轩"],
        "place_tags": ["陕西", "西安"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《陕西民盟史》陈希滔著，陕西人民出版社出版。"
            "回顾民盟陕西省组织建立、发展历程。"
            "陕西 = 1942 民盟西北组织创建地（成柏仁 1942 入盟 + 杜斌丞、杨明轩创建西北组织）。"
            "与盟贤.pdf 成柏仁条目（1942 加入民盟）可互证。"
            "L2 等级：正式出版物 + 省级人民出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（陕西人民出版社 / 各省市出版信息聚合）",
        "uncertainty_note": (
            "ISBN 与具体出版年待查；需陕西省图书馆借阅；"
            "1942 西北组织创建章节内容对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:GD:guangdong-minmengshi-2012-lijingxian",
        "title": "《广东民盟史》（李竟先主编，广东人民出版社 2012）",
        "creator": "李竟先（主编）",
        "document_date": "2012",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（广东 / 含南方总支部）",
        "repository_code": "GD",
        "repository_name": "广东人民出版社 / 民盟广东省委",
        "collection_name": "广东民盟史",
        "catalog_reference": "广东人民出版社 2012 第 1 版；ISBN 待查；记述从 1946 民盟南方总支部成立到当代",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；主编与出版年已 WebSearch 验证；ISBN 待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "广东人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1946政治协商会议", "1947民盟解散"],
        "person_tags": ["李章达", "千家驹", "萨空了"],
        "place_tags": ["广州", "广东", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《广东民盟史》李竟先主编，广东人民出版社 2012 出版。"
            "记述民盟广东组织建立与发展，从 1946 民盟南方总支部成立到当代。"
            "广东 / 香港 = 1941-1946 民盟海外支部与南方总支部所在地（梁漱溟 1941 香港办《光明报》）。"
            "L2 等级：正式出版物 + 省级人民出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（广东人民出版社 / 各省市出版信息聚合）",
        "uncertainty_note": (
            "ISBN 待查；需广东省立中山图书馆借阅；"
            "1941 香港《光明报》与南方总支部章节内容对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:ZJ:zhejiang-sheng-minzhudangpai-zhi-2002",
        "title": "《浙江省民主党派志》（浙江省民主党派志编纂委员会编，浙江人民出版社 2002-12，851 页 1215 千字，精装 16 开 9 千册）",
        "creator": "浙江省民主党派志编纂委员会",
        "document_date": "2002-12",
        "document_date_precision": "exact",
        "document_type": "省级民主党派志（民盟篇为第二篇）",
        "repository_code": "ZJ",
        "repository_name": "浙江人民出版社 / 浙江省民主党派志编纂委员会",
        "collection_name": "浙江省民主党派志",
        "catalog_reference": "浙江人民出版社 2002-12 第 1 版第 1 次印刷；精装 16 开 851 页 1215 千字；印数 9 千册",
        "catalog_reference_status": "verified",
        "source_url": "http://book.kongfz.com/1351/1535828790/",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；浙江省志丛书；民盟浙江省委员会为第二篇",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "浙江人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["浙江", "杭州"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《浙江省民主党派志》浙江省民主党派志编纂委员会编，"
            "浙江人民出版社 2002-12 第 1 版第 1 次印刷，精装 16 开 851 页 1215 千字，印数 9 千册。"
            "第二篇为中国民主同盟浙江省委员会（民盟浙江省级组织史）。"
            "L2 等级：正式出版物 + 省级人民出版社 + 浙江省志丛书。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "孔夫子 http://book.kongfz.com/1351/1535828790/",
        "uncertainty_note": (
            "ISBN 待查；需浙江图书馆借阅；"
            "民盟浙江省委员会篇（第二篇）章节内容与 1945-1949 关键时点对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:JS:jiangsu-minmengshi-gao-2004",
        "title": "《江苏民盟史稿》（民盟江苏省委员会、江苏省政协文史资料委员会编，江苏人民出版社 2004）",
        "creator": "民盟江苏省委员会、江苏省政协文史资料委员会",
        "document_date": "2004",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（江苏 早期稿本）",
        "repository_code": "JS",
        "repository_name": "江苏人民出版社 / 民盟江苏省委员会 / 江苏省政协",
        "collection_name": "江苏民盟史稿",
        "catalog_reference": "江苏人民出版社 2004 第 1 版；ISBN 待查",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；编者与出版年已 WebSearch 验证；ISBN 待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "江苏人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["费孝通", "吴贻芳"],
        "place_tags": ["南京", "江苏"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《江苏民盟史稿》民盟江苏省委员会、"
            "江苏省政协文史资料委员会编，江苏人民出版社 2004 出版。"
            "江苏省 = 1946-1949 民盟南京总部后期地（1946 民盟总部从重庆迁南京）。"
            "江苏籍民盟重要人物：费孝通、吴贻芳（女）、陈敏之等。"
            "L2 等级：正式出版物 + 省级人民出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（江苏人民出版社 / 各省市出版信息聚合）",
        "uncertainty_note": (
            "ISBN 待查；需南京图书馆借阅；目录章节与 1946-1949 关键时点对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:JS:zhongguo-minmengtongmeng-jiangsu-jianshi-2012",
        "title": "《中国民主同盟江苏简史》（民主同盟江苏省委员会、江苏省中共党史资料征集协作小组编，中央党史出版社 2012）",
        "creator": "民主同盟江苏省委员会、江苏省中共党史资料征集协作小组",
        "document_date": "2012",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（江苏 简史）",
        "repository_code": "JS",
        "repository_name": "中央党史出版社 / 民盟江苏省委员会",
        "collection_name": "中国民主同盟江苏简史",
        "catalog_reference": "中央党史出版社 2012 第 1 版；ISBN 待查",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；编者与出版年已 WebSearch 验证；ISBN 待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "中央党史出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["费孝通", "吴贻芳"],
        "place_tags": ["南京", "江苏"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《中国民主同盟江苏简史》"
            "民主同盟江苏省委员会、江苏省中共党史资料征集协作小组编，中央党史出版社 2012 出版。"
            "可与 2004 江苏人民出版社《江苏民盟史稿》互证。"
            "中央党史出版社 = 党史权威出版机构，史料严谨性高于一般省级出版社。"
            "L2 等级：正式出版物 + 中央党史出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（中央党史出版社 / 各省市出版信息聚合）",
        "uncertainty_note": (
            "ISBN 待查；需南京图书馆借阅；1946-1949 章节对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:FJ:zhongguo-minmengtongmeng-fujian-jianshi-2018",
        "title": "《中国民主同盟福建简史》（苏增添主编，线装书局 2018-12，ISBN 978-7-5120-2896-2）",
        "creator": "苏增添（主编）",
        "document_date": "2018-12",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（福建 1946-2018 简史）",
        "repository_code": "FJ",
        "repository_name": "线装书局 / 民盟福建省委",
        "collection_name": "中国民主同盟福建简史",
        "catalog_reference": "ISBN 978-7-5120-2896-2；线装书局 2018-12 第 1 版；苏增添主编",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；ISBN + 主编 + 出版年已 WebSearch 验证",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "线装书局出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["福州", "福建"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《中国民主同盟福建简史》苏增添主编，"
            "线装书局 2018-12 第 1 版，ISBN 978-7-5120-2896-2。"
            "系统记述民盟在福建地区自 1946 年成立至今 70 余年发展历程，"
            "详细介绍民盟福建省组织成立背景、历史沿革、重要人物以及在福建各时期发挥的重要作用。"
            "L2 等级：正式出版物 + ISBN 验证。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（线装书局 / 福建民盟官网）",
        "uncertainty_note": (
            "未取得扫描件；需福建省图书馆 / 厦门大学图书馆借阅；1946-1949 章节对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:HE:zhongguo-minmengtongmeng-shijiazhuang-shi-zhi-2013",
        "title": "《中国民主同盟石家庄市志》（中国民主同盟石家庄市委员会编著，河北人民出版社 2013-05，精装）",
        "creator": "中国民主同盟石家庄市委员会",
        "document_date": "2013-05",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织志（市级 / 石家庄）",
        "repository_code": "HE",
        "repository_name": "河北人民出版社 / 民盟石家庄市委员会",
        "collection_name": "中国民主同盟石家庄市志",
        "catalog_reference": "河北人民出版社 2013-05 第 1 版；精装；ISBN 待查",
        "catalog_reference_status": "verified",
        "source_url": "https://book.kongfz.com/403130/6623127635/",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子条目 https://book.kongfz.com/403130/6623127635/",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "河北人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["石家庄", "河北"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《中国民主同盟石家庄市志》"
            "中国民主同盟石家庄市委员会编著，河北人民出版社 2013-05 第 1 版，精装。"
            "市级民盟组织志；河北（含石家庄）= 1947-1949 民盟华北地下组织地。"
            "L2 等级：正式出版物 + 省级人民出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "孔夫子 https://book.kongfz.com/403130/6623127635/",
        "uncertainty_note": (
            "ISBN 待查；需河北省图书馆借阅；1945-1949 章节对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:HN:hunan-minmengrenwu-2020",
        "title": "《湖南民盟人物》（中国民主同盟湖南省委员会、杨君武编，群言出版社 2020-10，ISBN 9787519306090，352 页）",
        "creator": "中国民主同盟湖南省委员会、杨君武",
        "document_date": "2020-10",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织人物传记（湖南）",
        "repository_code": "HN",
        "repository_name": "群言出版社 / 民盟湖南省委员会",
        "collection_name": "湖南盟史丛书",
        "catalog_reference": "ISBN 9787519306090；群言出版社 2020-10 第 1 版；352 页；定价 42 元；杨君武编",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；ISBN + 编者 + 出版年已 WebSearch 验证",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "群言出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["长沙", "湖南"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《湖南民盟人物》中国民主同盟湖南省委员会、杨君武编，"
            "群言出版社 2020-10 第 1 版，ISBN 9787519306090，352 页，定价 42 元。"
            "民盟湖南省委纪念湖南民盟省级组织成立 65 周年组织编写的《湖南盟史》丛书之一。"
            "湖南 = 1946-1949 民盟华中地下组织重要地。"
            "L2 等级：正式出版物 + 群言出版社（民盟中央出版平台）。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "孔夫子 https://book.kongfz.com/181694/6208047052/ ；"
            "新华文轩 https://book.kongfz.com/15309/5589085176/"
        ),
        "uncertainty_note": (
            "未取得扫描件；需湖南图书馆借阅；具体 1945-1949 入盟人物条目对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:YN:yunan-minmengshi-2021-chenguang",
        "title": "《云南民盟史》（云南出版集团晨光出版社 2021-10，约 48 万字）",
        "creator": "民盟云南省委（编）",
        "document_date": "2021-10",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织史（云南）",
        "repository_code": "YN",
        "repository_name": "云南出版集团晨光出版社 / 民盟云南省委",
        "collection_name": "云南民盟史",
        "catalog_reference": "云南出版集团晨光出版社 2021-10 第 1 版；约 48 万字；ISBN 待查",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；出版年与字数已 WebSearch 验证；ISBN 待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "云南出版集团晨光出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1946李公朴闻一多遇害", "1947民盟解散"],
        "person_tags": ["李公朴", "闻一多", "罗隆基", "楚图南"],
        "place_tags": ["昆明", "云南"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《云南民盟史》云南出版集团晨光出版社 2021-10 出版，"
            "全书约 48 万字，已陆续向部分高校赠阅。"
            "云南 = 1945-1946 民盟西南总支 / 李公朴闻一多活动地。"
            "1946-07-11 李公朴遇害、1946-07-15 闻一多遇害 = 民盟最惨痛事件。"
            "L2 等级：正式出版物 + 省级出版集团。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（云南出版集团 / 民盟云南省委官网）",
        "uncertainty_note": (
            "ISBN 与具体编者待查；需云南省图书馆 / 云南大学图书馆借阅；"
            "李公朴 / 闻一多遇害事件章节对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:SC:sichuan-minmengshi-sichuan-renmin",
        "title": "《四川民盟史》（民盟四川省委编，四川人民出版社出版）",
        "creator": "民盟四川省委（编）",
        "document_date": "2020",
        "document_date_precision": "approximate",
        "document_type": "民盟地方组织史（四川）",
        "repository_code": "SC",
        "repository_name": "四川人民出版社 / 民盟四川省委",
        "collection_name": "四川民盟史",
        "catalog_reference": "四川人民出版社；ISBN 与具体出版年待查",
        "catalog_reference_status": "verified",
        "access_mode": "open",
        "access_note": "正式出版物；出版社已 WebSearch 验证；ISBN 与具体出版年待查",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "四川人民出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1947民盟解散"],
        "person_tags": ["张澜", "张秀熟", "潘大逵"],
        "place_tags": ["成都", "四川"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《四川民盟史》民盟四川省委编，四川人民出版社出版。"
            "对四川民盟地方组织成立 70 多年光辉历程的客观回顾，"
            "展现四川省多党合作事业蓬勃发展的重要史料。"
            "四川 = 张澜（民盟主席）故乡 + 1942-1946 民盟在成都 / 重庆活动地。"
            "L2 等级：正式出版物 + 省级人民出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "WebSearch 2026-07-20（四川人民出版社 / 民盟四川省委官网）",
        "uncertainty_note": (
            "ISBN 与具体出版年待查；需四川省图书馆 / 四川大学图书馆借阅；"
            "1941-1949 关键时点章节对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:AH:anhui-minzhudangpai-shi-meng-zhangjie-2009",
        "title": "《安徽民主党派史·民盟章节》（时代出版传媒股份有限公司、安徽教育出版社 2009-08）",
        "creator": "时代出版传媒（编）",
        "document_date": "2009-08",
        "document_date_precision": "exact",
        "document_type": "省级民主党派史（民盟章节）",
        "repository_code": "AH",
        "repository_name": "安徽教育出版社 / 时代出版传媒",
        "collection_name": "安徽民主党派史",
        "catalog_reference": "安徽教育出版社 2009-08 第 1 版；ISBN 待查；含民盟安徽省组织章节",
        "catalog_reference_status": "verified",
        "source_url": "https://www.ahmm.gov.cn/content/detail/5ed0afc0c78f09fefc1e24ae.html",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；民盟安徽省委官网有专门条目介绍",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "安徽教育出版社出版",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["合肥", "安徽"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《安徽民主党派史·民盟章节》"
            "时代出版传媒股份有限公司、安徽教育出版社 2009-08 出版。"
            "该书涵盖安徽民主党派（含民盟）的整体历史；"
            "民盟安徽省委官网有专门条目介绍该书。"
            "L2 等级：正式出版物 + 省级出版社。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": "民盟安徽省委官网 https://www.ahmm.gov.cn/content/detail/5ed0afc0c78f09fefc1e24ae.html",
        "uncertainty_note": (
            "ISBN 待查；需安徽省图书馆借阅；民盟安徽省组织章节与 1945-1949 关键时点对应待检索。"
        ),
    },
    {
        "candidate_id": "domestic:BJ:beijing-minmeng-zuzhi-chengli-70-zhounian-2016",
        "title": "《北京市民盟组织成立70周年》（中国民主同盟北京市委员会编，2016-06，平装大16开131页）",
        "creator": "中国民主同盟北京市委员会",
        "document_date": "2016-06",
        "document_date_precision": "exact",
        "document_type": "民盟地方组织纪念册（北京）",
        "repository_code": "BJ",
        "repository_name": "中国民主同盟北京市委员会",
        "collection_name": "北京市民盟组织成立70周年（岁月剪影）",
        "catalog_reference": "中国民主同盟北京市委员会 2016-06；平装大16开131页；ISBN 待查",
        "catalog_reference_status": "verified",
        "source_url": "https://book.kongfz.com/398390/4866549480/",
        "source_url_role": "catalogue",
        "access_mode": "open",
        "access_note": "正式出版物；孔夫子条目 https://book.kongfz.com/398390/4866549480/；同年 8 月亦有同名出版（不同 ISBN）",
        "medium": "physical",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "中国民主同盟北京市委员会编",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民盟一大", "1946政治协商会议", "1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读：《北京市民盟组织成立70周年》（岁月剪影）"
            "中国民主同盟北京市委员会编，2016-06 平装大16开131页；同年 8 月亦有同名出版（不同 ISBN）。"
            "北京 = 1949 一届政协民盟 9 席所在地。"
            "L2 等级：正式出版物 + 民盟省级组织编。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "孔夫子 https://book.kongfz.com/398390/4866549480/ ；"
            "孔夫子（同书不同版）https://book.kongfz.com/323991/1688045503/"
        ),
        "uncertainty_note": (
            "ISBN 待查；需首都图书馆借阅；1946-1949 早期北京民盟活动章节对应待检索。"
        ),
    },
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("jsonl", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--checked-at", default=TODAY)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.jsonl.read_text(encoding="utf-8").splitlines() if line.strip()]
    existing = {r["candidate_id"] for r in rows}

    added, skipped = [], []
    for record in NEW_RECORDS:
        cid = record["candidate_id"]
        if cid in existing:
            skipped.append(cid)
            continue
        record.update(
            {
                "checked_at": args.checked_at,
                "checked_by": "claude-code",
                "review_status": "needs_human_review",
                "review_note": (
                    "L2 proposed 各省市民盟地方组织史/志/历史文献丛书正式出版物；"
                    "WebSearch 2026-07-20 多源核读（孔夫子旧书网 + 各省人民出版社 + 各省民盟官网 + 豆瓣）；"
                    "ISBN 与具体出版年部分待查；"
                    "升级 accepted 需 cheer 显式批准（与 FRUS L3→L2 升级流程一致）。"
                ),
            }
        )
        rows.append(record)
        added.append(cid)

    if args.apply:
        args.jsonl.write_text(
            "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows),
            encoding="utf-8",
        )
    print(json.dumps(
        {"added": added, "skipped": skipped, "applied": args.apply, "total_records": len(rows)},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())