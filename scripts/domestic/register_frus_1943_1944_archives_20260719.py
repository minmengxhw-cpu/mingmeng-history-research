#!/usr/bin/env python3
"""Register FRUS 1943–1944 民盟 archives from 上海民盟史料长编·FRUS 上卷.

Two high-value L3 records from the unpublished 民盟历史文献研究项目组
re-compilation of FRUS (Foreign Relations of the United States) 1943 China
volume. Each reproduces the English original + Chinese translation of a
specific US Embassy/Consulate dispatch about 中国民主政团同盟 / 民主同盟
activities in 1943–1944, with a stable URL to the original FRUS page.

Raw layer (read-only):
    <local-user>/民盟/研究室文件/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf

Original FRUS digital archive URLs (for cross-verification):
    1943: https://history.state.gov/historicaldocuments/frus1943China/d272
    1944: https://history.state.gov/historicaldocuments/frus1944v06/d445

These are L3 (research-project compilation of L2 official FRUS archives).
Upgrade to L2 would require direct citation of history.state.gov or the
official FRUS printed volume, with FRUS page-cite verified.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


RAW_PDF = "<local-user>/民盟/研究室文件/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf"
TODAY = "2026-07-19"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:FRUS:1943-09-18-d272-atcheson-federation-platform",
        "title": "驻华代办艾其森致国务卿第1594号呈文——附桂林领事关于中国民主政团同盟政治纲领的报告（1943-09-18）",
        "creator": "George Atcheson, Jr.（驻华代办）／Kweilin Consul／U.S. Department of State",
        "document_date": "1943-09-18",
        "document_date_precision": "day",
        "document_type": "美国国务院外交档案·驻华使馆致国务卿呈文（外方一手档案）",
        "repository_code": "FRUS",
        "repository_name": "U.S. Department of State / Foreign Relations of the United States (FRUS) / 民盟历史文献研究项目组（2026-05 编）",
        "collection_name": "上海民盟史料长编·美国对外关系文件集（上卷） 1943 China",
        "archive_item": "doc/frus1943China/d272；FRUS 上卷 PDF 第12页",
        "catalog_reference": "FRUS 1943 China, Volume, Document 272；本库 ID：doc/frus1943China/d272",
        "catalog_reference_status": "verified",
        "source_url": "https://history.state.gov/historicaldocuments/frus1943China/d272",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "原档 FRUS 公开访问；本地 PDF 见民盟历史文献研究项目组 2026-05 编《美国对外关系文件集（上卷）》PDF 第12页",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "美国国务院官方出版（>50 年），公有领域；中文译文为民盟历史文献研究项目组整理",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜", "1941民盟前身"],
        "person_tags": ["George Atcheson Jr.", "梁漱溟", "中国民主政团同盟"],
        "place_tags": ["重庆", "桂林"],
        "evidence_note": (
            "1943-09-18 驻华代办艾其森（George Atcheson, Jr.）致国务卿第1594号呈文，"
            "封面：No. 1594 Chungking, September 18, 1943 [Received October 14]；"
            "正文：『Referring to the Embassy's despatch No. 1458 of August 13, 1943, "
            "in regard to the Federation of Chinese Democratic Parties, I have the honor "
            "to enclose a copy of despatch No. 41 of September 2, 1943, from the Consul "
            "at Kweilin describing the political platform of the Federation.』"
            "配套：1943-08-13 第1458号呈文（未刊印）+ 1943-07-31 桂林领事 Ringwalt 访问梁漱溟记录。"
            "中文译文：『兹参照使馆1943年8月13日第1458号呈文中关于中国民主政团同盟的内容，"
            "本人谨随文附上桂林领事1943年9月2日第41号呈文副本。该呈文说明了该同盟的政治纲领。』"
            "提供 1943 年中国民主政团同盟（民盟前身）组织与政治纲领的美国外交档案记录，"
            "是 1942/1943 空档的关键外方佐证。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "原档 URL：https://history.state.gov/historicaldocuments/frus1943China/d272 ；"
            "本地 PDF：raw/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf 第12页；"
            "页图待抽取（work/domestic/frus_1943_d272_pages/）"
        ),
        "uncertainty_note": (
            "本地 PDF 为民盟历史文献研究项目组 2026-05 编（未公开出版的内部研究汇编）→ 当前等级 L3；"
            "需以 history.state.gov/d272 原始页面或 FRUS 1943 China 印刷本核读后升级 L2；"
            "1943-07-31 桂林领事第24号呈文（d231/d232）注『未刊印』，仅有引述，"
            "d231/d232 完整正文需访问 NARA 缩微（仍为外方一手档案）。"
        ),
    },
    {
        "candidate_id": "domestic:FRUS:1944-09-22-d445-sprouse-democratic-league-principles",
        "title": "驻华大使高斯致国务卿第2991号呈文——附斯普鲁斯关于《民主同盟政治原则草案》的评述（1944-09-22）",
        "creator": "C. E. Gauss（驻华大使）／Philip D. Sprouse（昆明领事）／U.S. Department of State",
        "document_date": "1944-09-22",
        "document_date_precision": "day",
        "document_type": "美国国务院外交档案·驻华使馆致国务卿呈文（外方一手档案）",
        "repository_code": "FRUS",
        "repository_name": "U.S. Department of State / Foreign Relations of the United States (FRUS) / 民盟历史文献研究项目组（2026-05 编）",
        "collection_name": "上海民盟史料长编·美国对外关系文件集（上卷） 1944 China v06",
        "archive_item": "doc/frus1944v06/d445；FRUS 上卷 PDF 第37页",
        "catalog_reference": "FRUS 1944 China v06, Document 445；本库 ID：doc/frus1944v06/d445",
        "catalog_reference_status": "verified",
        "source_url": "https://history.state.gov/historicaldocuments/frus1944v06/d445",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "原档 FRUS 公开访问；本地 PDF 见民盟历史文献研究项目组 2026-05 编《美国对外关系文件集（上卷）》PDF 第37页",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "美国国务院官方出版（>50 年），公有领域；中文译文为民盟历史文献研究项目组整理",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名"],
        "person_tags": ["C. E. Gauss", "Philip D. Sprouse", "罗隆基", "中国民主同盟"],
        "place_tags": ["重庆", "昆明", "成都"],
        "evidence_note": (
            "1944-09-22 驻华大使高斯（C. E. Gauss）致国务卿第2991号呈文，封面：No. 2991 Chungking, "
            "September 22, 1944 [Received October 25]；正文：『关于昆明总领事馆1944年7月14日第51号"
            "函，以及使馆1944年8月23日第2900号函所述民主同盟（旧称中国民主政团同盟）及其他反对国民"
            "政府和国民党的力量之活动，兹随函附上1944年9月13日昆明领事菲利普·D. 斯普鲁斯来信副本一份。"
            "该信转来《民主同盟政治原则草案》译文。』"
            "斯普鲁斯评述：『该草案由罗隆基博士起草……该草案是『盎格鲁-撒克逊民主思想与苏维埃俄国制度"
            "之间的妥协』……其条款似乎完全是乌托邦式和空想式的，在今日中国几乎无法实施和执行。』"
            "中文：『民主同盟近几周似乎并不十分活跃。越来越多人形成这样的印象：构成民盟的各种力量"
            "未能达成相互谅解，普遍缺乏协调和互信。民盟若干成员……出席了1944年9月18日在重庆闭幕的"
            "国民参政会会议……民主同盟拟于不久后在成都召集其代表会议，讨论民盟政策和活动。』"
            "提供 1944-09 民盟组织与政治原则（罗隆基起草）的美国外交档案记录，"
            "含成都代表会议召集的早期外方信号——是 1944 改组前夕的关键外方佐证。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "原档 URL：https://history.state.gov/historicaldocuments/frus1944v06/d445 ；"
            "本地 PDF：raw/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf 第37页；"
            "页图待抽取（work/domestic/frus_1944_d445_pages/）"
        ),
        "uncertainty_note": (
            "本地 PDF 为民盟历史文献研究项目组 2026-05 编（未公开出版的内部研究汇编）→ 当前等级 L3；"
            "需以 history.state.gov/d445 原始页面或 FRUS 1944 China v06 印刷本核读后升级 L2；"
            "《民主同盟政治原则草案》原文（罗隆基起草）注『附件未刊印』，需访问 NARA 缩微；"
            "1944-08-23 第2900号函与 1944-07-14 第51号函均注未刊印，仅有引述。"
        ),
    },
    {
        "candidate_id": "domestic:FRUS:1943-07-31-d232-ringwalt-liang-shuming-interview",
        "title": "驻桂林领事林沃尔特致驻华代办艾其森第24号呈文——访问梁漱溟谈中国民主政团同盟要点（1943-07-31）",
        "creator": "Arthur R. Ringwalt（驻桂林领事）／Troy L. Perkins（远东司）／U.S. Department of State",
        "document_date": "1943-07-31",
        "document_date_precision": "day",
        "document_type": "美国国务院外交档案·驻桂林领事致驻华代办呈文（外方一手档案）",
        "repository_code": "FRUS",
        "repository_name": "U.S. Department of State / Foreign Relations of the United States (FRUS) / 民盟历史文献研究项目组（2026-05 编）",
        "collection_name": "上海民盟史料长编·美国对外关系文件集（上卷） 1943 China",
        "archive_item": "doc/frus1943China/d232；FRUS 上卷 PDF 第11页",
        "catalog_reference": "FRUS 1943 China, Document 232；本库 ID：doc/frus1943China/d232",
        "catalog_reference_status": "verified",
        "source_url": "https://history.state.gov/historicaldocuments/frus1943China/d232",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "原档 FRUS 公开访问；本地 PDF 见民盟历史文献研究项目组 2026-05 编《美国对外关系文件集（上卷）》PDF 第11页",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "美国国务院官方出版（>50 年），公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜", "1941民盟前身"],
        "person_tags": ["梁漱溟", "Arthur R. Ringwalt", "Troy L. Perkins", "中国民主政团同盟"],
        "place_tags": ["桂林"],
        "evidence_note": (
            "1943-07-31 驻桂林领事 Ringwalt（林沃尔特）致驻华代办 Atcheson 第24号呈文，"
            "封面：No. 24 Kweilin, July 31, 1943；"
            "正文：『本人谨报告同梁漱溟先生会谈的要点。梁先生以在河南、山东推动乡村自治实验"
            "而知名，也是中国民主政团同盟的重要成员。梁先生同意同签署人坦率交谈，但条件是必须"
            "严格保护其匿名身份。』附远东司 Troy L. Perkins 1943-09-23 评论：『梁先生或许过于乐观，"
            "认为一旦中国领袖离世，仅凭抵抗精神便能维系局面……中国民主政团同盟并非国民党的反对者；"
            "其主要目标是改善该党的弊端，并最终促成各党派之间的合作。』"
            "提供 1943-07 民盟重要成员梁漱溟（应作梁漱溟）的会谈记录（正文未刊印，仅有引述），"
            "及美国远东司对中国民主政团同盟立场的早期官方评估。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "原档 URL：https://history.state.gov/historicaldocuments/frus1943China/d232 ；"
            "本地 PDF：raw/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf 第11页"
        ),
        "uncertainty_note": (
            "本地 PDF 为民盟历史文献研究项目组 2026-05 编（未公开出版的内部研究汇编）→ 当前等级 L3；"
            "正文注明『Here follows detailed report』，但实际正文未在本汇编中刊印，"
            "完整详细报告需访问 NARA 缩微（仍为外方一手档案）。"
        ),
    },
    {
        "candidate_id": "domestic:FRUS:1944-10-30-d478-gauss-war-final-stage-proposals",
        "title": "驻华大使高斯致国务卿第3104号呈文——中国民主同盟关于战争最后阶段政治行政的提案译文（1944-10-30）",
        "creator": "C. E. Gauss（驻华大使）／U.S. Department of State",
        "document_date": "1944-10-30",
        "document_date_precision": "day",
        "document_type": "美国国务院外交档案·驻华使馆致国务卿呈文（外方一手档案）",
        "repository_code": "FRUS",
        "repository_name": "U.S. Department of State / Foreign Relations of the United States (FRUS) / 民盟历史文献研究项目组（2026-05 编）",
        "collection_name": "上海民盟史料长编·美国对外关系文件集（上卷） 1944 China v06",
        "archive_item": "doc/frus1944v06/d478；FRUS 上卷 PDF 第40页",
        "catalog_reference": "FRUS 1944 China v06, Document 478；本库 ID：doc/frus1944v06/d478",
        "catalog_reference_status": "verified",
        "source_url": "https://history.state.gov/historicaldocuments/frus1944v06/d478",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "原档 FRUS 公开访问；本地 PDF 见民盟历史文献研究项目组 2026-05 编《美国对外关系文件集（上卷）》PDF 第40页",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "美国国务院官方出版（>50 年），公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名"],
        "person_tags": ["C. E. Gauss", "中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "1944-10-30 驻华大使 Gauss（高斯）致国务卿第3104号呈文，"
            "封面：No. 3104 Chungking, October 30, 1944 [Received November 11]；"
            "正文：『关于本馆1944年9月22日第2991号函，内附中国民主同盟（民主政团同盟）政治纲领草案，"
            "现谨随函附上民盟就战争最后阶段政治行政问题所拟提案的译文一份。据了解，民盟原拟公开"
            "发表此提案，但上月政府恢复压制性新闻检查政策，致使该计划无法实现。民盟的提案在许多"
            "方面与最近一届国民参政会所通过的提案相似，但在一个显著方面远远超过国民参政会的提案："
            "即提案要求终止一党政府，并建立由各党派各派系组成的联合政府取而代之。中国民主同盟的提案"
            "不能不说是对执政的国民党的严厉控诉，并要求其放弃独占的政治控制。事实上，这些提案在许多"
            "方面与延安中国共产党人提出的那些提案相似。』"
            "提供 1944-10 民盟抗战最后阶段政治提案（联合政府纲领）的美国外交档案记录，"
            "为 1944 改组前夕到 1945 一大之间民盟政治路线的关键外方佐证。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "原档 URL：https://history.state.gov/historicaldocuments/frus1944v06/d478 ；"
            "本地 PDF：raw/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf 第40页"
        ),
        "uncertainty_note": (
            "本地 PDF 为民盟历史文献研究项目组 2026-05 编（未公开出版的内部研究汇编）→ 当前等级 L3；"
            "需以 history.state.gov/d478 原始页面或 FRUS 1944 China v06 印刷本核读后升级 L2；"
            "附件『民盟战争最后阶段提案』译文注『Not printed』，需访问 NARA 缩微。"
        ),
    },
    {
        "candidate_id": "domestic:FRUS:1944-04-21-d329-gauss-service-minority-parties",
        "title": "驻华大使高斯致国务卿第2466号呈文——附谢伟思关于中国少数党派领导人意见的备忘录（1944-04-21）",
        "creator": "C. E. Gauss（驻华大使）／John S. Service（二等秘书）／U.S. Department of State",
        "document_date": "1944-04-21",
        "document_date_precision": "day",
        "document_type": "美国国务院外交档案·驻华使馆致国务卿呈文（外方一手档案）",
        "repository_code": "FRUS",
        "repository_name": "U.S. Department of State / Foreign Relations of the United States (FRUS) / 民盟历史文献研究项目组（2026-05 编）",
        "collection_name": "上海民盟史料长编·美国对外关系文件集（上卷） 1944 China v06",
        "archive_item": "doc/frus1944v06/d329；FRUS 上卷 PDF 第14—15页",
        "catalog_reference": "FRUS 1944 China v06, Document 329；本库 ID：doc/frus1944v06/d329",
        "catalog_reference_status": "verified",
        "source_url": "https://history.state.gov/historicaldocuments/frus1944v06/d329",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "原档 FRUS 公开访问；本地 PDF 见民盟历史文献研究项目组 2026-05 编《美国对外关系文件集（上卷）》PDF 第14—15页",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "美国国务院官方出版（>50 年），公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名"],
        "person_tags": ["C. E. Gauss", "John S. Service", "史迪威", "中国民主同盟", "中国民主政团同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "1944-04-21 驻华大使 Gauss 致国务卿第2466号呈文，"
            "封面：No. 2466 Chungking, April 21, 1944 [Received May 11]；"
            "正文：『Referring to the Embassy's despatch no. 1594 of September 18, 1943, "
            "in regard to the Federation of Chinese Democratic Parties, and to the Embassy's "
            "despatch no. 2303 of March 14, 1944, in regard to the unification of anti-Central "
            "Government elements, I have the honor to enclose a copy of a memorandum of "
            "April 14, 1944 prepared by Second Secretary John S. Service, on detail to General "
            "Stilwell's staff, reporting the views of Chinese minority party leaders.』"
            "中文：『关于1943年9月18日第1594号公函所述中国民主政团同盟，"
            "以及1944年3月14日第2303号公函所述统一反中央政府各派力量，"
            "谨随函附上1944年4月14日备忘录副本一份，由奉调至史迪威将军参谋部的"
            "二等秘书谢伟思撰写，报告中国少数党派领导人的看法。』"
            "提供 1944-04 改组前夕美国外交档案对中国少数党派（含民盟）"
            "与美国军方（史迪威）合作的关键记录。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "原档 URL：https://history.state.gov/historicaldocuments/frus1944v06/d329 ；"
            "本地 PDF：raw/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf 第14—15页"
        ),
        "uncertainty_note": (
            "本地 PDF 为民盟历史文献研究项目组 2026-05 编（未公开出版的内部研究汇编）→ 当前等级 L3；"
            "需以 history.state.gov/d329 原始页面或 FRUS 1944 China v06 印刷本核读后升级 L2；"
            "Service 备忘录正文注『Enclosure not printed』，需访问 NARA 缩微。"
        ),
    },
    {
        "candidate_id": "domestic:FRUS:1944-07-11-d380-langdon-kunming-democratic-league",
        "title": "昆明总领事兰登致国务卿——关于中国民主同盟在昆明组织活动（1944-07-11）",
        "creator": "Wm. R. Langdon（昆明总领事）／U.S. Department of State",
        "document_date": "1944-07-11",
        "document_date_precision": "day",
        "document_type": "美国国务院外交档案·驻昆明总领事致国务卿呈文（外方一手档案）",
        "repository_code": "FRUS",
        "repository_name": "U.S. Department of State / Foreign Relations of the United States (FRUS) / 民盟历史文献研究项目组（2026-05 编）",
        "collection_name": "上海民盟史料长编·美国对外关系文件集（上卷） 1944 China v06",
        "archive_item": "doc/frus1944v06/d380；FRUS 上卷 PDF 第20—21页",
        "catalog_reference": "FRUS 1944 China v06, Document 380；本库 ID：doc/frus1944v06/d380",
        "catalog_reference_status": "verified",
        "source_url": "https://history.state.gov/historicaldocuments/frus1944v06/d380",
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "原档 FRUS 公开访问；本地 PDF 见民盟历史文献研究项目组 2026-05 编《美国对外关系文件集（上卷）》PDF 第20—21页",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "美国国务院官方出版（>50 年），公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组更名"],
        "person_tags": ["Wm. R. Langdon", "罗隆基", "中国民主同盟"],
        "place_tags": ["昆明"],
        "evidence_note": (
            "1944-07-11 昆明总领事 Langdon（兰登）致国务卿第48号呈文，"
            "归档号 893.00/7–1144；"
            "正文涉及桂林领事馆1944-05-30致重庆大使馆第117号公函，"
            "以及对中国民主同盟在昆明组织活动的报告（具体页码指向 Embassy Political Report for October, 1943 与 1944-10-28 第1747号呈文）。"
            "提供 1944-07 民盟在昆明（罗隆基等核心成员）的美国外交档案记录，"
            "为改组前夕民盟地方组织的外方佐证。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "原档 URL：https://history.state.gov/historicaldocuments/frus1944v06/d380 ；"
            "本地 PDF：raw/研究平台史料长编/民盟史料长编_美国对外关系文件集_上卷_frus.pdf 第20—21页"
        ),
        "uncertainty_note": (
            "本地 PDF 为民盟历史文献研究项目组 2026-05 编（未公开出版的内部研究汇编）→ 当前等级 L3；"
            "需以 history.state.gov/d380 原始页面或 FRUS 1944 China v06 印刷本核读后升级 L2；"
            "本档案有多个『未刊印』交叉引用（Not printed），完整上下文需访问 NARA 缩微。"
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
                    "L3 民盟历史文献研究项目组（2026-05）内部研究汇编，记录级；"
                    "内容为外方一手外交档案（FRUS），原档可在 history.state.gov 公开访问；"
                    "需以 history.state.gov 页面或 FRUS 印刷本核读后升级 L2；"
                    "1943-09-18 d272 / 1944-09-22 d445 入库。"
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
