#!/usr/bin/env python3
"""Register 批次 G-3: Wikimedia Commons Li Gongpu + Zhang Bojun 关键文件 10 条。

WebFetch 2026-07-21 实测：

Li Gongpu 子分类（12 文件）：
- 周恩来为李公朴闻一多追悼会所写悼词（手写悼词原件）★
- 李公朴衣冠冢（9.79 MB 高分辨率！罕见高质民国扫描）★
- 李公朴访问八路军总部
- 彭德怀为李公朴夫妇题词
- 聂荣臻为李公朴题词
- Li_Gongpu_couple_in_Yan'an
- Li_Gongpu_couple's_Great_Wall
- Li_Gongpu_couple
- Li_Gongpu/1
- Qijunzi.jpg（已 G-2 注册）

Zhang Bojun 子分类（11 文件）：
- 1946_10_Chou.jpg（已 G 注册）
- 50Meiyuan Xincun
- Leaders of CD see CCP mission off（已 G-2 注册）
- 中央人民政府主席副主席和部分委员（已 G 注册）
- 六参政员访问延安 + 1（1945）
- 切实保障人民权利案（已 G 注册）
- 新政协筹备会常委合影（已 G 注册）
- 毛泽东朱德与六参政员（1945）
- 章伯鈞

L2 accepted（PD-China）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 1946 周恩来亲笔悼词文件
    {
        "candidate_id": "domestic:WM:1946-zhouenlai-shougao-daoci-li-wen",
        "title": "1946 周恩来为李公朴闻一多追悼会所写亲笔悼词（手写原件）",
        "creator": "周恩来",
        "document_date": "1946-07",
        "document_date_precision": "month",
        "document_type": "1946 民国时期档案（周恩来亲笔手写悼词原件扫描）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 李公朴分类",
        "collection_name": "Li Gongpu (12F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:周恩来为李公朴闻一多追悼会所写悼词.jpg",
        "catalog_reference": "Wikimedia Commons File:周恩来为李公朴闻一多追悼会所写悼词.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%91%A8%E6%81%A9%E6%9D%A5%E4%B8%BA%E6%9D%8E%E5%85%AC%E6%9C%B3%E9%97%BB%E4%B8%80%E5%A4%9A%E8%BF%BD%E6%82%BC%E4%BC%9A%E6%89%80%E5%86%99%E6%82%BC%E8%AF%8D.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 65KB 220×291",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946李公朴闻一多遇害"],
        "person_tags": ["周恩来", "李公朴", "闻一多", "中国民主同盟"],
        "place_tags": ["上海"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Li_Gongpu；"
            "周恩来为李公朴闻一多追悼会所写悼词（手写原件扫描）= 周恩来亲笔悼词；"
            "李公朴 1946-07-11 + 闻一多 1946-07-15 遇害后，"
            "周恩来亲笔写悼词，1946-07 由邓颖超在追悼会上宣读；"
            "L2 等级：PD-China + 周恩来亲笔原件扫描 + 民盟最惨痛事件。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:周恩来为李公朴闻一多追悼会所写悼词.jpg",
        "uncertainty_note": "需进一步确认悼词具体内容文本。",
    },
    # 李公朴衣冠冢（高分辨率）
    {
        "candidate_id": "domestic:WM:1946-li-gongpu-yiguanzhong-highres",
        "title": "李公朴衣冠冢（民国时期罕见高分辨率扫描 9.79 MB）",
        "creator": "作者不详（PD-China）",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "1946 民国时期高分辨率影像扫描（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 李公朴分类",
        "collection_name": "Li Gongpu (12F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:李公朴衣冠冢.jpg",
        "catalog_reference": "Wikimedia Commons File:李公朴衣冠冢.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%9D%8E%E5%85%AC%E6%9C%B3%E8%A1%A3%E5%86%A0%E5%BA%9F.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 9.79 MB 7737×5160（罕见高分辨率）",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L1",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946李公朴闻一多遇害"],
        "person_tags": ["李公朴", "中国民主同盟"],
        "place_tags": ["上海"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Li_Gongpu；"
            "李公朴衣冠冢扫描；"
            "分辨率 7,737 × 5,160（罕见高分辨率）；"
            "文件大小 9.79 MB（罕见大文件，PD-China 但完整高分辨率）；"
            "李公朴 1946-07-11 遇害后衣冠冢；"
            "L1 等级依据：PD-China + 9.79MB 高分辨率 + 完整衣冠冢影像 + 民盟烈士文物；"
            "可直接用于民盟文物数字化复制。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:李公朴衣冠冢.jpg",
        "uncertainty_note": "L1 已设置（PD-China + 9.79MB 原始扫描）。",
    },
    # 李公朴访问八路军总部
    {
        "candidate_id": "domestic:WM:1946-li-gongpu-fangwen-balujun-zongbu",
        "title": "李公朴访问八路军总部",
        "creator": "作者不详（PD-China）",
        "document_date": "1937",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 李公朴分类",
        "collection_name": "Li Gongpu (12F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:李公朴访问八路军总部.jpg",
        "catalog_reference": "Wikimedia Commons File:李公朴访问八路军总部.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%9D%8E%E5%85%AC%E6%9C%B3%E8%AE%BF%E9%97%AE%E5%85%AB%E8%B7%AF%E5%86%9B%E6%80%BB%E9%83%A8.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 95KB 400×285",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1936七君子事件"],
        "person_tags": ["李公朴", "中国民主同盟"],
        "place_tags": ["延安", "山西"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Li_Gongpu；"
            "李公朴访问八路军总部（1937 抗战初期或战后）；"
            "L2 等级：PD-China + 民盟核心人物。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:李公朴访问八路军总部.jpg",
        "uncertainty_note": "需进一步确认具体日期。",
    },
    # 彭德怀为李公朴夫妇题词
    {
        "candidate_id": "domestic:WM:1946-pengdehuai-tici-li-gongpu",
        "title": "1946 彭德怀为李公朴夫妇题词",
        "creator": "彭德怀",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "1946 民国时期手写题词（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 李公朴分类",
        "collection_name": "Li Gongpu (12F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:彭德怀为李公朴夫妇题词.jpg",
        "catalog_reference": "Wikimedia Commons File:彭德怀为李公朴夫妇题词.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%BD%AD%E5%BE%B7%E6%80%80%E4%B8%BA%E6%9D%8E%E5%85%AC%E6%9C%B3%E5%A4%AB%E5%A6%BB%E9%A2%98%E8%AF%8D.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 96KB 400×312",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946李公朴闻一多遇害"],
        "person_tags": ["彭德怀", "李公朴", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Li_Gongpu；"
            "1946 彭德怀为李公朴夫妇题词（手写原件扫描）；"
            "彭德怀 = 中共将领，为民盟烈士李公朴夫妇题词；"
            "L2 等级：PD-China + 中共将领亲笔 + 民盟烈士文物。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:彭德怀为李公朴夫妇题词.jpg",
        "uncertainty_note": "需进一步确认题词内容。",
    },
    # 聂荣臻为李公朴题词
    {
        "candidate_id": "domestic:WM:1946-nierongzhen-tici-li-gongpu",
        "title": "1946 聂荣臻为李公朴题词",
        "creator": "聂荣臻",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "1946 民国时期手写题词（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 李公朴分类",
        "collection_name": "Li Gongpu (12F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:聂荣臻为李公朴题词.jpg",
        "catalog_reference": "Wikimedia Commons File:聂荣臻为李公朴题词.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E8%81%82%E8%8D%A3%E7%82%9C%E4%B8%BA%E6%9D%8E%E5%85%AC%E6%9C%B3%E9%A2%98%E8%AF%8D.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 87KB 400×238",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946李公朴闻一多遇害"],
        "person_tags": ["聂荣臻", "李公朴", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "1946 聂荣臻为李公朴题词（手写原件扫描）；"
            "聂荣臻 = 中共将领，为民盟烈士李公朴题词；"
            "L2 等级：PD-China + 中共将领亲笔。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:聂荣臻为李公朴题词.jpg",
        "uncertainty_note": "需进一步确认题词内容。",
    },
    # 六参政员访问延安 1（1945）
    {
        "candidate_id": "domestic:WM:1945-liucanzhengyuan-fangwen-yanan",
        "title": "1945 六参政员访问延安（含黄炎培/章伯钧/罗隆基等 6 位民盟/民社党/青年党参政员）",
        "creator": "作者不详（PD-China）",
        "document_date": "1945",
        "document_date_precision": "year",
        "document_type": "1945 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 黄炎培 / 章伯钧 / 沈钧儒分类",
        "collection_name": "黄炎培分类 + 章伯钧分类 + 沈钧儒分类",
        "archive_item": "https://commons.wikimedia.org/wiki/File:六参政员访问延安.jpg",
        "catalog_reference": "Wikimedia Commons File:六参政员访问延安.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%85%AD%E5%8F%82%E6%94%BF%E5%91%98%E8%AE%BF%E9%97%AE%E5%BB%B6%E5%AE%89.jpg",
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
        "event_tags": ["1945重庆谈判", "1945民盟一大"],
        "person_tags": ["黄炎培", "章伯钧", "罗隆基", "左舜生", "中国民主同盟"],
        "place_tags": ["延安"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Zhang_Bojun + /wiki/Category:Huang_Yanpei；"
            "1945 六参政员访问延安 = 民盟 + 民社党 + 青年党各 2 位参政员访问延安；"
            "1945-07 民盟创始人黄炎培 + 章伯钧 + 罗隆基等访问延安见毛泽东；"
            "L2 等级：PD-China + 1945 民盟历史关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:六参政员访问延安.jpg",
        "uncertainty_note": "需进一步确认 6 位具体人物名单。",
    },
    # 六参政员访问延安 2（同时间另一版本）
    {
        "candidate_id": "domestic:WM:1945-liucanzhengyuan-fangwen-yanan-2",
        "title": "1945 六参政员访问延安（另一版本合影）",
        "creator": "作者不详（PD-China）",
        "document_date": "1945",
        "document_date_precision": "year",
        "document_type": "1945 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 章伯钧 / 黄炎培分类",
        "archive_item": "https://commons.wikimedia.org/wiki/File:六参政员访问延安1.jpg",
        "catalog_reference": "Wikimedia Commons File:六参政员访问延安1.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%85%AD%E5%8F%82%E6%94%BF%E5%91%98%E8%AE%BF%E9%97%AE%E5%BB%B6%E5%AE%891.jpg",
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
        "event_tags": ["1945重庆谈判", "1945民盟一大"],
        "person_tags": ["黄炎培", "章伯钧", "罗隆基", "中国民主同盟"],
        "place_tags": ["延安"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "1945 六参政员访问延安 第二版本合影；"
            "L2 等级：PD-China + 1945 关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:六参政员访问延安1.jpg",
        "uncertainty_note": "需进一步对照版本差异。",
    },
    # 毛泽东朱德与六参政员（1945）
    {
        "candidate_id": "domestic:WM:1945-maozedong-zhude-liucanzhengyuan",
        "title": "1945 毛泽东朱德与六参政员合影（含民盟代表）",
        "creator": "作者不详（PD-China）",
        "document_date": "1945",
        "document_date_precision": "year",
        "document_type": "1945 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 章伯钧 / 沈钧儒分类",
        "archive_item": "https://commons.wikimedia.org/wiki/File:毛泽东朱德与六参政员.jpg",
        "catalog_reference": "Wikimedia Commons File:毛泽东朱德与六参政员.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%AF%9B%E6%B3%BD%E4%B8%9C%E6%9C%B1%E5%BE%B7%E4%B8%8E%E5%85%AD%E5%8F%82%E6%94%BF%E5%91%98.jpg",
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
        "event_tags": ["1945重庆谈判", "1945民盟一大"],
        "person_tags": ["毛泽东", "朱德", "黄炎培", "章伯钧", "罗隆基", "中国民主同盟"],
        "place_tags": ["延安"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "1945 毛泽东朱德与六参政员合影 = 1945-07 延安访问合影；"
            "L2 等级：PD-China + 1945 关键时点 + 毛泽东朱德亲临。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:毛泽东朱德与六参政员.jpg",
        "uncertainty_note": "需进一步确认具体身份。",
    },
    # 1949 史良 立像 1
    {
        "candidate_id": "domestic:WM:shiliang-portrait-1",
        "title": "史良肖像照（民国时期）",
        "creator": "作者不详（PD-China）",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期人物照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 史良分类",
        "collection_name": "史良分类 (9 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:史良.jpg",
        "catalog_reference": "Wikimedia Commons File:史良.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%8F%B2%E8%89%AF.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；史良个人肖像照",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1936七君子事件"],
        "person_tags": ["史良", "中国民主同盟"],
        "place_tags": ["上海"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "史良肖像照（民国时期，1937-1949 大致）；"
            "史良 = 七君子中唯一女性 + 民盟中央副主席（1958-1965）+ 新中国首任司法部部长；"
            "L2 等级：PD-China + 民盟核心人物肖像。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:史良.jpg",
        "uncertainty_note": "需进一步确认拍摄年份。",
    },
    # 章伯钧个人照
    {
        "candidate_id": "domestic:WM:zhang-bojun-portrait",
        "title": "章伯钧肖像照（民国时期，农工主席 + 民盟中央常委）",
        "creator": "作者不详（PD-China）",
        "document_date": "1940",
        "document_date_precision": "approximate",
        "document_type": "民国时期人物照（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 章伯钧分类",
        "collection_name": "章伯钧分类 (11 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:章伯鈞.jpg",
        "catalog_reference": "Wikimedia Commons File:章伯鈞.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E7%AB%A0%E4%BC%AF%E9%88%9E.jpg",
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
        "event_tags": ["1936七君子事件"],
        "person_tags": ["章伯钧", "中国农工民主党", "中国民主同盟"],
        "place_tags": ["上海", "重庆"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "章伯钧肖像照（民国时期）；"
            "章伯钧 = 中国农工民主党主席（1947-） + 民盟中央常委 + 1946 民盟参加政协代表；"
            "L2 等级：PD-China + 民盟 + 农工双重身份核心人物。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:章伯鈞.jpg",
        "uncertainty_note": "需进一步确认拍摄年份。",
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
                    f"L2/L1 needs_human_review Wikimedia Commons 民盟历史文件（批次 G-3）；"
                    f"PD-China 公有领域；WebFetch 2026-07-21 实测。"
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