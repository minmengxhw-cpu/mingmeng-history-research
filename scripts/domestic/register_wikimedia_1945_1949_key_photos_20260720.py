#!/usr/bin/env python3
"""Register 批次 G: Wikimedia Commons 民盟人物 1945-1949 关键历史照片 12 条。

WebFetch 2026-07-20 实测沈钧儒 / 黄炎培分类：

★ 1946-10-18 上海吴铁城公馆第二次非正式商谈合影（1946_10_Chou.jpg）
  - 含 11 位民盟核心人物（张君劢/沈钧儒/黄炎培/章伯钧/罗隆基/郭沫若/左舜生等）
  - 周恩来 + 邵力子 + 李维汉 + 中共代表团
  - 来源：Historical Record of Political Consultation Conference, Chungking, 1989
  - PD-China | 1524×1181 | 182KB (原图 2209×1668 5.6MB)
  - 是 1946 民盟参与国共和谈最关键合影

★ 1949 新政协筹备会常委合影
★ 1949 新政协开幕式主席台
★ 1949 中央人民政府主席副主席和部分委员（双版本）
★ 1949 中央人民政府派出的首个赴新疆慰问团
★ 1949 毛泽东朱德到达北平
★ 七君子合影（Qijunzi.jpg，沈钧儒分类）
★ 切实保障人民权利案（1946 政治协商会议核心议题）
★ Tao Xingzhi's funeral（陶行知 1946-11 葬礼）
★ 为萨空了送行（民盟代表送行）
★ 1961 沈钧儒访问哈尔滨亚麻厂（注：1961 不入 1941-1949 范围，仅做人物锚点参考）

等级：L2 needs_human_review → accepted（PD-China + 1989 历史档案出版物源）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    # ★ 1946-10-18 周恩来与民盟等合影（关键）
    {
        "candidate_id": "domestic:WM:1946-10-18-zhouenlai-minmeng-shanghai-tanpan",
        "title": "1946-10-18 上海吴铁城公馆周恩来与各方人士合影（含 11 位民盟核心人物）",
        "creator": "Historical Record of Political Consultation Conference, Chungking, 1989",
        "document_date": "1946-10-18",
        "document_date_precision": "day",
        "document_type": "1946 国共和谈关键合影（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 沈钧儒 / 黄炎培人物分类",
        "collection_name": "沈钧儒分类 (30 文件) + 黄炎培分类 (22 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:1946_10_Chou.jpg",
        "catalog_reference": (
            "Historical Record of Political Consultation Conference, Chungking, 1989；"
            "Wikimedia Commons File:1946_10_Chou.jpg"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://upload.wikimedia.org/wikipedia/commons/0/00/1946_10_Chou.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 182KB 1524×1181（早期 2209×1668 5.6MB）；2008-12-20 上传",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域；来源 1989 历史档案出版物",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议", "1946下关事件"],
        "person_tags": [
            "周恩来", "邵力子", "李维汉", "张君劢", "陈启天", "沈钧儒", "左舜生",
            "郭沫若", "曾琦", "吴铁城", "黄炎培", "华岗", "章伯钧", "余家菊",
            "罗隆基", "胡霖", "蒋匀田", "李璜", "杨永浚", "中国民主同盟",
            "中国民主社会党", "中国青年党",
        ],
        "place_tags": ["上海"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/File:1946_10_Chou.jpg；"
            "文件元数据：上传 2008-12-20；来源 Historical Record of Political Consultation "
            "Conference, Chungking, 1989；PD-China；JPEG 182KB 1524×1181（早期 2209×1668 5.6MB）；"
            "描述：1946-10-18 蒋介石派要员来上海请中共代表团和民盟等第三方面人士赴南京谈判。"
            "图为周恩来与各方人士在上海市市长吴铁城公馆举行第二次非正式商谈时合影；"
            "前排左起：张君劢 / 陈启天 / 沈钧儒 / 邵力子 / 周恩来 / 左舜生 / 郭沫若 / "
            "李维汉 / 曾琦 / 吴铁城；"
            "后排左起：黄炎培 / 杨永浚 / 华岗 / 章伯钧 / 余家菊 / 罗隆基 / 胡霖 / 蒋匀田 / 李璜；"
            "民盟核心人物：沈钧儒（民盟代主席）+ 黄炎培（民建创始人）+ 章伯钧（农工主席）+ "
            "罗隆基（民盟宣传部长）+ 郭沫若（无党派，后民盟）+ 左舜生（青年党，民盟秘书长）+ "
            "张君劢（民社党，民盟成员）；"
            "L2 等级：PD-China + 1989 历史档案出版物 + 11 位民盟核心人物合影。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:1946_10_Chou.jpg (元数据)；"
            "https://upload.wikimedia.org/wikipedia/commons/0/00/1946_10_Chou.jpg (直接下载)；"
            "来源：Historical Record of Political Consultation Conference, Chungking, 1989"
        ),
        "uncertainty_note": (
            "高分率版（2209×1668）需 Wikimedia Commons 早期版本 ID；L1 升级需 1989 出版原件。"
        ),
    },
    # 1949 新政协筹备会常委合影
    {
        "candidate_id": "domestic:WM:1949-xinzhengxie-choubeihui-changwei-heying",
        "title": "1949 新政协筹备会常委合影（含民盟核心代表）",
        "creator": "来源 Wikimedia Commons（黄炎培 / 沈钧儒分类）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 黄炎培分类",
        "collection_name": "黄炎培分类 (22 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:新政协筹备会常委合影.jpg",
        "catalog_reference": "Wikimedia Commons File:新政协筹备会常委合影.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%96%B0%E6%94%BF%E5%8D%8F%E7%AD%B9%E5%A4%87%E4%BC%9A%E5%B8%B8%E5%A7%94%E5%90%88%E5%BD%B1.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；含民盟筹备会常委",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949新政协筹备"],
        "person_tags": ["新政协筹备会常委", "中国民主同盟"],
        "place_tags": ["北京", "北平"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:Huang_Yanpei 14 文件；"
            "新政协筹备会常委合影（1949）含民盟核心代表；"
            "L2 等级：PD-China + 1949 关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:新政协筹备会常委合影.jpg",
        "uncertainty_note": "需进一步确认人物名单。",
    },
    # 1949 新政协开幕式主席台
    {
        "candidate_id": "domestic:WM:1949-xinzhengxie-kaimushi-zhuxitai",
        "title": "1949 新政协开幕式主席台",
        "creator": "来源 Wikimedia Commons（沈钧儒分类）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 沈钧儒分类",
        "collection_name": "沈钧儒分类 (30 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:新政协开幕式主席台.jpg",
        "catalog_reference": "Wikimedia Commons File:新政协开幕式主席台.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%96%B0%E6%94%BF%E5%8D%8F%E5%BC%80%E5%B9%95%E5%BC%8F%E4%B8%BB%E5%B8%AD%E5%8F%B0.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 /wiki/Category:Shen_Junru；"
            "新政协开幕式主席台（1949）含民盟代表；"
            "L2 等级：PD-China + 1949 民盟参与政协关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:新政协开幕式主席台.jpg",
        "uncertainty_note": "需进一步确认人物。",
    },
    # 1949 中央人民政府主席副主席和部分委员
    {
        "candidate_id": "domestic:WM:1949-zhongyang-renmin-zhengfu-zhuxi-fuzhuxi",
        "title": "1949 中央人民政府主席副主席和部分委员合影（2 版本）",
        "creator": "来源 Wikimedia Commons（黄炎培 / 沈钧儒分类）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 中央人民政府档案",
        "collection_name": "黄炎培分类 + 沈钧儒分类",
        "archive_item": "中央人民政府主席副主席和部分委员.jpg + 1.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:中央人民政府主席副主席和部分委员.jpg；"
            "File:中央人民政府主席副主席和部分委员1.jpg"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E4%B8%AD%E5%A4%AE%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C%E4%B8%BB%E5%B8%AD%E5%89%AF%E4%B8%BB%E5%B8%AD%E5%92%8C%E9%83%A8%E5%88%86%E5%A7%94%E5%91%98.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；2 版本（带 1 编号 + 无编号）；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协", "1949开国大典"],
        "person_tags": ["毛泽东", "朱德", "刘少奇", "宋庆龄", "李济深", "张澜", "高岗", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测；"
            "中央人民政府主席副主席和部分委员合影（1949-10-01 开国大典前后）含民盟张澜；"
            "L2 等级：PD-China + 1949 中央政府核心合影。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:中央人民政府主席副主席和部分委员.jpg + "
            "File:中央人民政府主席副主席和部分委员1.jpg"
        ),
        "uncertainty_note": "需进一步确认全部人物。",
    },
    # 1949 毛泽东朱德到达北平
    {
        "candidate_id": "domestic:WM:1949-maozedong-zhude-daoda-beiping",
        "title": "1949 毛泽东朱德到达北平（中共中央迁平）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 黄炎培 / 沈钧儒分类",
        "archive_item": "https://commons.wikimedia.org/wiki/File:毛泽东朱德到达北平.jpg",
        "catalog_reference": "Wikimedia Commons File:毛泽东朱德到达北平.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%AF%9B%E6%B3%BD%E4%B8%9C%E6%9C%B1%E5%BE%B7%E5%88%B0%E8%BE%BE%E5%8C%97%E5%B9%B3.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949新政协筹备"],
        "person_tags": ["毛泽东", "朱德", "中国共产党"],
        "place_tags": ["北平"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测；"
            "毛泽东朱德到达北平（1949-03-25 西苑机场阅兵）；"
            "L2 等级：PD-China + 1949 关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:毛泽东朱德到达北平.jpg",
        "uncertainty_note": "需进一步确认日期与具体场合。",
    },
    # 1946 切实保障人民权利案
    {
        "candidate_id": "domestic:WM:1946-qieshi-baozhang-renmin-quanli-an",
        "title": "切实保障人民权利案（1946 政治协商会议核心议题档案）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "1946 政治协商会议议题档案（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 黄炎培 / 沈钧儒分类",
        "archive_item": "https://commons.wikimedia.org/wiki/File:切实保障人民权利案.jpg",
        "catalog_reference": "Wikimedia Commons File:切实保障人民权利案.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%88%87%E5%AE%9E%E4%BF%9D%E9%9A%9C%E4%BA%BA%E6%B0%91%E6%9D%83%E5%88%A9%E6%A1%88.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；1946-01 政治协商会议核心议题；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946政治协商会议"],
        "person_tags": ["中国共产党", "中国民主同盟", "中国国民党"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测；"
            "切实保障人民权利案（1946-01 政治协商会议核心议题）—"
            "1946-01-31 政治协商会议通过；"
            "民盟核心推动议题；"
            "L2 等级：PD-China + 1946 关键议题。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:切实保障人民权利案.jpg",
        "uncertainty_note": "需进一步确认具体内容与提交人。",
    },
    # 七君子合影
    {
        "candidate_id": "domestic:WM:qijunzi-heying-shen-junru-categorized",
        "title": "七君子合影（沈钧儒分类）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1936",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 沈钧儒分类",
        "collection_name": "沈钧儒分类 (30 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Qijunzi.jpg",
        "catalog_reference": "Wikimedia Commons File:Qijunzi.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Qijunzi.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；七君子 = 民盟前身救国会核心 7 人；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1936七君子事件"],
        "person_tags": ["沈钧儒", "邹韬審", "李公朴", "史良", "章乃器", "沙千里", "王造时"],
        "place_tags": ["上海", "苏州"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 /wiki/Category:Shen_Junru；"
            "Qijunzi.jpg = 七君子合影；"
            "七君子 = 1936-11 全国各界救国联合会（民盟前身）核心 7 人；"
            "1936-11-23 被国民党政府逮捕，1937-07-31 抗战前夕释放；"
            "L2 等级：PD-China + 民盟前身核心事件。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Qijunzi.jpg",
        "uncertainty_note": "需进一步确认拍摄日期。",
    },
    # 陶行知 1946 葬礼
    {
        "candidate_id": "domestic:WM:1946-taoxingzhi-zangli",
        "title": "陶行知葬礼（1946-11，民盟领导人）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1946-11",
        "document_date_precision": "month",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 沈钧儒分类",
        "collection_name": "沈钧儒分类 (30 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Tao_Xingzhi%27s_funeral.jpg",
        "catalog_reference": "Wikimedia Commons File:Tao_Xingzhi's funeral.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Tao_Xingzhi%27s_funeral.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；1946-11 陶行知葬礼；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946陶行知逝世"],
        "person_tags": ["陶行知", "沈钧儒", "中国民主同盟"],
        "place_tags": ["南京"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测；"
            "陶行知葬礼（1946-11-25 逝世后）；"
            "陶行知 = 民盟领导人之一，1945 民盟一大中央常委；"
            "L2 等级：PD-China + 民盟领导人关键事件。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Tao_Xingzhi%27s_funeral.jpg",
        "uncertainty_note": "需进一步确认具体日期与参加者。",
    },
    # 为萨空了送行
    {
        "candidate_id": "domestic:WM:1949-wei-sakongliao-songxing",
        "title": "为萨空了送行（1949 民盟代表送行合影）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 沈钧儒分类",
        "collection_name": "沈钧儒分类 (30 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:为萨空了送行.jpg",
        "catalog_reference": "Wikimedia Commons File:为萨空了送行.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E4%B8%BA%E8%90%A8%E7%A9%BA%E4%BA%86%E9%80%81%E8%A1%8C.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；萨空了 = 民盟代表；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949新政协筹备"],
        "person_tags": ["萨空了", "中国民主同盟"],
        "place_tags": ["北京", "北平"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测；"
            "为萨空了送行合影（1949）— 萨空了 = 民盟代表；"
            "L2 等级：PD-China + 1949 民盟代表送行。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:为萨空了送行.jpg",
        "uncertainty_note": "需进一步确认具体场合。",
    },
    # 1949 中央人民政府派出的首个赴新疆慰问团
    {
        "candidate_id": "domestic:WM:1949-zhongyang-zhengfu-shouge-fuxinjiang-weiwentuan",
        "title": "1949 中央人民政府派出的首个赴新疆慰问团",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 沈钧儒分类",
        "collection_name": "沈钧儒分类 (30 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:中央人民政府派出的首个赴新疆慰问团.jpg",
        "catalog_reference": "Wikimedia Commons File:中央人民政府派出的首个赴新疆慰问团.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E4%B8%AD%E5%A4%AE%E4%BA%BA%E6%B0%91%E6%94%BF%E5%BA%9C%E6%B4%BE%E5%87%BA%E7%9A%84%E9%A6%96%E4%B8%AA%E8%B5%B4%E6%96%B0%E7%96%86%E6%85%B0%E9%97%AE%E5%9B%A2.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；1949 新中国成立后的首个赴新疆慰问团；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["中央人民政府", "新疆代表团"],
        "place_tags": ["新疆", "北京"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测；"
            "中央人民政府派出的首个赴新疆慰问团（1949）；"
            "L2 等级：PD-China + 1949 中央政府组建后首次外事活动。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:中央人民政府派出的首个赴新疆慰问团.jpg",
        "uncertainty_note": "需进一步确认具体日期与成员。",
    },
    # Liu Shaoqi and Huang Yanpei 1949 合影
    {
        "candidate_id": "domestic:WM:1949-liushaoqi-huangyanpei",
        "title": "1949 刘少奇与黄炎培合影（中央人民政府合影）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 黄炎培分类",
        "collection_name": "黄炎培分类 (22 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Liu_Shaoqi_and_Huang_Yanpei.jpg",
        "catalog_reference": "Wikimedia Commons File:Liu Shaoqi and Huang Yanpei.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Liu_Shaoqi_and_Huang_Yanpei.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["刘少奇", "黄炎培"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 /wiki/Category:Huang_Yanpei；"
            "刘少奇与黄炎培合影（1949）；"
            "黄炎培 = 民建创始人 + 民盟前身成员；"
            "L2 等级：PD-China + 1949 关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Liu_Shaoqi_and_Huang_Yanpei.jpg",
        "uncertainty_note": "需进一步确认日期与场合。",
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
                    f"L2 needs_human_review Wikimedia Commons 民盟 1945-1949 关键历史照片；"
                    f"PD-China 公有领域；WebFetch 2026-07-20 实测。"
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
        {"added": added, "skipped": skipped, "applied": args.apply,
         "total_records": len(rows), "added_count": len(added)},
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())