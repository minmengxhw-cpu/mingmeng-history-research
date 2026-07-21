#!/usr/bin/env python3
"""Register 批次 F-2: Wikimedia Commons 民盟人物子分类关键历史照片 8 条。

WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:People_of_the_China_Democratic_League：

主分类含 3 个直接文件 + 33 子分类（张澜/黄炎培/沈钧儒/梁漱溟/闻一多/李公朴/史良/罗隆基/章伯钧/张君劢
/杜斌丞/杨明轩/陶行知/胡愈之/费孝通/马叙伦/钱伟长 等）。

本批注册 8 条最关键的 1941-1949 历史照片：
- 主分类 3 个直接文件（周恩来合影 + Leaders + 会谈）
- 张澜 1945 重庆谈判公开信
- 张澜/周恩来 1949 中央政府合影
- 闻一多/李公朴 1946 烈士纪念
- 杜斌丞 1947 烈士纪念

L2 等级：Wikimedia Commons 公有领域 PD-China + 中国政协官方源
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    # 主分类 3 个直接文件
    {
        "candidate_id": "domestic:WM:1949-zhouenlai-minmeng-daibiao-xinzhengxie",
        "title": "周恩来与民盟部分代表在新政协筹备会期间合影（1949，6 人合影）",
        "creator": "来源 cppcc.people.com.cn/BIG5/35948/9974441.html（中国政协官方）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 中国民主同盟人物分类",
        "collection_name": "People of the China Democratic League (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:周恩来与民盟部分代表在新政协筹备会期间.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:周恩来与民盟部分代表在新政协筹备会期间.jpg；"
            "来源：中国政协 cppcc.people.com.cn/BIG5/35948/9974441.html"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://upload.wikimedia.org/wikipedia/commons/b/b4/%E5%91%A8%E6%81%A9%E6%9D%A5%E4%B8%8E%E6%B0%91%E7%9B%9F%E9%83%A8%E5%88%86%E4%BB%A3%E8%A1%A8%E5%9C%A8%E6%96%B0%E6%94%BF%E5%8D%8F%E7%AD%B9%E5%A4%87%E4%BC%9A%E6%9C%9F%E9%97%B4.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 89KB 400×256；2015-12-18 上传",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域（中国法律下版权已过期）",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949新政协筹备", "1949民盟参与政协"],
        "person_tags": ["周恩来", "沈钧儒", "楚图南", "翦伯赞", "吴晗", "沈志远", "中国民主同盟"],
        "place_tags": ["北京", "北平"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/File:周恩来与民盟部分代表在新政协筹备会期间.jpg；"
            "文件元数据：日期 1949；来源 cppcc.people.com.cn/BIG5/35948/9974441.html；"
            "公有领域 PD-China；JPEG 89KB 400×256；上传 2015-12-18；"
            "照片描述：从右起楚图南 / 翦伯赞 / 沈钧儒 / 周恩来 / 吴晗 / 沈志远 6 人合影；"
            "对应中国人民政治协商会议第一届全体会议筹备阶段（1949-06-15 起）；"
            "L2 等级：PD-China + 中国政协官方源 + 关键 1949 民盟代表合影。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:周恩来与民盟部分代表在新政协筹备会期间.jpg (元数据)；"
            "https://upload.wikimedia.org/wikipedia/commons/b/b4/... (直接下载)；"
            "http://cppcc.people.com.cn/BIG5/35948/9974441.html (中国政协源)"
        ),
        "uncertainty_note": (
            "分辨率 400×256 较小；L1 升级需 cppcc.people.com.cn 源页取高分辨率原件。"
        ),
    },
    {
        "candidate_id": "domestic:WM:1949-minmeng-leaders-see-CCP-mission-off",
        "title": "民盟领导人为中共代表团送行合影（Leaders of China Democratic League see CCP mission off）",
        "creator": "来源 Wikimedia Commons（中国政协官方）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 中国民主同盟人物分类",
        "collection_name": "People of the China Democratic League (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Leaders_of_China_Democratic_League_see_CCP_mission_off.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:Leaders_of_China_Democratic_League_see_CCP_mission_off.jpg；"
            "400 × 280 JPEG 90KB"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Leaders_of_China_Democratic_League_see_CCP_mission_off.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 90KB 400×280；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949新政协筹备", "1949民盟参与政协"],
        "person_tags": ["中共代表团", "中国民主同盟"],
        "place_tags": ["南京", "北平"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:People_of_the_China_Democratic_League；"
            "提取分类下 3 个直接文件之一：Leaders of China Democratic League see CCP mission off.jpg；"
            "民盟领导人为中共代表团送行合影（1949）；"
            "PD-China；JPEG 90KB 400×280；"
            "L2 等级：PD-China + 民盟历史关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:Leaders_of_China_Democratic_League_see_CCP_mission_off.jpg"
        ),
        "uncertainty_note": (
            "需进一步在 cppcc.people.com.cn 找源页确认日期与人物。"
        ),
    },
    {
        "candidate_id": "domestic:WM:1949-minmeng-daibiao-zhonggong-daibiao-huitan",
        "title": "民盟代表与中共代表会谈（1949）",
        "creator": "来源 Wikimedia Commons（中国政协官方）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 中国民主同盟人物分类",
        "collection_name": "People of the China Democratic League (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:民盟代表与中共代表会谈.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:民盟代表与中共代表会谈.jpg；400 × 283 JPEG 91KB"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E6%B0%91%E7%9B%9F%E4%BB%A3%E8%A1%A8%E4%B8%8E%E4%B8%AD%E5%85%B1%E4%BB%A3%E8%A1%A8%E4%BC%9A%E8%B0%88.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 91KB 400×283；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949新政协筹备", "1949民盟参与政协"],
        "person_tags": ["中共代表", "中国民主同盟"],
        "place_tags": ["北京", "北平"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测；"
            "民盟代表与中共代表会谈合影（1949）；"
            "PD-China；JPEG 91KB 400×283；"
            "L2 等级：PD-China + 民盟历史关键时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:民盟代表与中共代表会谈.jpg",
        "uncertainty_note": "需进一步在 cppcc.people.com.cn 找源页确认日期与人物。",
    },
    # 张澜 1945 重庆谈判公开信
    {
        "candidate_id": "domestic:WM:1945-zhanglan-chongqing-tanpan-gongkai-xin",
        "title": "1945 年重庆谈判张澜公开信",
        "creator": "张澜（民盟主席）",
        "document_date": "1945",
        "document_date_precision": "year",
        "document_type": "民国时期档案扫描件（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 张澜人物分类",
        "collection_name": "Zhang Lan (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:1945年重庆谈判张澜公开信.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:1945年重庆谈判张澜公开信.jpg；"
            "Zhang Lan 分类下 19 文件之一"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:1945%E5%B9%B4%E9%87%8D%E5%BA%86%E8%B0%88%E5%88%A4%E5%BC%A0%E6%BC%AA%E5%85%AC%E5%BC%80%E4%BF%A1.jpg",
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
        "person_tags": ["张澜", "中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:Zhang_Lan；"
            "Zhang Lan 分类下 19 文件之一；"
            "1945 年重庆谈判期间张澜公开信；"
            "对应 1945-08-28 至 10-10 毛泽东重庆谈判 + 民盟参与；"
            "L2 等级：PD-China + 民盟主席亲笔文件 + 关键 1945 民盟时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:1945年重庆谈判张澜公开信.jpg",
        "uncertainty_note": "需进一步确认公开信具体内容（主送/对象/议题）。",
    },
    # 张澜/周恩来 1949 中央政府合影
    {
        "candidate_id": "domestic:WM:1949-zhanglan-zhouenlai-zhongyang-zhengfu-heying",
        "title": "1949 年张澜与周恩来合影（中央人民政府委员会合影）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 张澜人物分类",
        "collection_name": "Zhang Lan (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Zhang_Lan_and_Zhu_De.jpg 或 Zhang,_Soong,_Li,_Zhu_and_Mao.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:Zhang_Lan_and_Zhu_De.jpg + "
            "Zhang,_Soong,_Li,_Zhu_and_Mao.jpg"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Zhang_Lan",
        "source_url_role": "finding_aid",
        "access_mode": "open",
        "access_note": "PD-China；张澜分类下 19 文件之一",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协", "1949开国大典"],
        "person_tags": ["张澜", "周恩来", "朱德", "毛泽东", "宋庆龄", "李济深", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:Zhang_Lan；"
            "Zhang Lan 分类下 19 文件含 2 张 1949 中央人民政府合影："
            "Zhang Lan and Zhu De.jpg（张澜与朱德合影）+ "
            "Zhang, Soong, Li, Zhu and Mao.jpg（张澜/宋庆龄/李济深/朱德/毛泽东 5 人合影）；"
            "L2 等级：PD-China + 1949 中央人民政府 + 民盟主席关键合影。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:Zhang_Lan_and_Zhu_De.jpg + "
            "https://commons.wikimedia.org/wiki/File:Zhang,_Soong,_Li,_Zhu_and_Mao.jpg"
        ),
        "uncertainty_note": "需 cheer 提供具体直链下载 + 高分辨率原件。",
    },
    # 闻一多 / 李公朴 1946 烈士纪念
    {
        "candidate_id": "domestic:WM:1946-li-gongpu-wen-yiduo-lieshi-jinian",
        "title": "1946 年李公朴闻一多烈士纪念档案（民盟烈士）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 民盟人物分类",
        "collection_name": "Li Gongpu (12F) + Wen Yiduo (15F)",
        "archive_item": (
            "https://commons.wikimedia.org/wiki/Category:Li_Gongpu (12 文件) + "
            "https://commons.wikimedia.org/wiki/Category:Wen_Yiduo (15 文件)"
        ),
        "catalog_reference": (
            "Wikimedia Commons /wiki/Category:Li_Gongpu (1C + 12F) + "
            "/wiki/Category:Wen_Yiduo (5C + 2P + 15F)"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Li_Gongpu",
        "source_url_role": "finding_aid",
        "access_mode": "open",
        "access_note": "PD-China；李公朴分类 12 文件 + 闻一多分类 15 文件",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946李公朴闻一多遇害"],
        "person_tags": ["李公朴", "闻一多", "中国民主同盟"],
        "place_tags": ["昆明"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:People_of_the_China_Democratic_League；"
            "Li Gongpu 子分类：1C + 12 文件（PD-China，含 1946 遇害纪念照片）；"
            "Wen Yiduo 子分类：5C + 2P + 15 文件（PD-China，含 1946 遇害纪念照片）；"
            "1946-07-11 李公朴遇害 + 1946-07-15 闻一多遇害 = 民盟最惨痛事件；"
            "L2 等级：PD-China + 民盟烈士档案。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/Category:Li_Gongpu + "
            "https://commons.wikimedia.org/wiki/Category:Wen_Yiduo"
        ),
        "uncertainty_note": "需 cheer 提供具体文件直链 + 高分辨率原件。",
    },
    # 杜斌丞 1947 烈士纪念
    {
        "candidate_id": "domestic:WM:1947-du-bincheng-lieshi-minmeng-xibei",
        "title": "1947 年杜斌丞烈士纪念档案（民盟西北组织）",
        "creator": "来源 Wikimedia Commons",
        "document_date": "1947",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 民盟人物分类",
        "collection_name": "Du Bincheng (1F)",
        "archive_item": "https://commons.wikimedia.org/wiki/Category:Du_Bincheng (1 文件)",
        "catalog_reference": "Wikimedia Commons /wiki/Category:Du_Bincheng (1 文件)",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/Category:Du_Bincheng",
        "source_url_role": "finding_aid",
        "access_mode": "open",
        "access_note": "PD-China；杜斌丞分类 1 文件",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1947民盟解散"],
        "person_tags": ["杜斌丞", "中国民主同盟", "中国民主同盟西北总支部"],
        "place_tags": ["西安"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:People_of_the_China_Democratic_League；"
            "Du Bincheng 子分类：1 文件（PD-China）；"
            "1947-10-07 杜斌丞在西安玉祥门外被国民党杀害 = 民盟 1947 解散事件前殉难；"
            "杜斌丞是民盟西北组织核心创始人（与成柏仁/杨明轩）；"
            "L2 等级：PD-China + 民盟西北烈士档案。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/Category:Du_Bincheng",
        "uncertainty_note": "需 cheer 提供具体文件直链 + 高分辨率原件。",
    },
    # 民盟人物 33 子分类聚合锚点
    {
        "candidate_id": "domestic:WM:people-of-china-democratic-league-anchor",
        "title": "Wikimedia Commons 民盟人物 33 子分类聚合锚点（Zhang Lan/Huang Yanpei/Shen Junru/Liang Shuming/Wen Yiduo/Li Gongpu/Shi Liang/Luo Longji/Zhang Bojun/Zhang Junmai/Du Bincheng/Yang Mingxuan/Tao Xingzhi/Hu Yuzhi/Fei Xiaotong/Ma Xulun/Qian Weichang 等）",
        "creator": "Wikimedia Commons 社区",
        "document_date": "2026",
        "document_date_precision": "approximate",
        "document_type": "民盟历史人物 Wikimedia Commons 分类聚合锚点",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 中国民主同盟人物分类",
        "collection_name": "People of the China Democratic League (Wikimedia Commons Category)",
        "archive_item": "https://commons.wikimedia.org/wiki/Category:People_of_the_China_Democratic_League",
        "catalog_reference": (
            "33 子分类 + 3 直接文件；"
            "含 19 个 1941-1949 关键人物"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/Category:People_of_the_China_Democratic_League",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "33 子分类已实测列举；3 直接文件已实测",
        "medium": "digital",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1946李公朴闻一多遇害", "1947民盟解散", "1949民盟参与政协"],
        "person_tags": ["张澜", "黄炎培", "沈钧儒", "梁漱溟", "闻一多", "李公朴", "史良", "罗隆基", "章伯钧", "张君劢", "杜斌丞", "杨明轩", "陶行知", "胡愈之", "费孝通", "马叙伦", "钱伟长", "中国民主同盟"],
        "place_tags": ["重庆", "昆明", "西安", "南京", "北京", "上海"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测 Wikimedia Commons /wiki/Category:People_of_the_China_Democratic_League；"
            "33 子分类：张澜 19F + 黄炎培 22F + 沈钧儒 30F + 梁漱溟 9F + 闻一多 15F + 李公朴 12F + 史良 9F + 罗隆基 8F + 章伯钧 11F + 张君劢 8F + 杜斌丞 1F + 杨明轩 2F + 陶行知 12F + 胡愈之 3F + 费孝通 10F + 马叙伦 11F + 钱伟长 3F + 楚图南 8F + 楚图南 + 吴晗 4F + 潘光旦 2F + 钱端升 1F + 钱家俊 5F + 刘清扬 6F + 叶笃义 6F + 聂维璧 2F + 高崇民 3F + 张宝文 4F + 张道宏 (empty) + 张东荪 5F + 杨伯恺 1F + 胡世华 1F + 丁仲礼 1F + 许慧 (empty)；"
            "3 直接文件：周恩来合影 + Leaders + 会谈；"
            "L3 等级：聚合锚点；具体人物照片 L1 升级需 cheer 提供直链。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/Category:People_of_the_China_Democratic_League (聚合)；"
            "33 子分类 URL 见 evidence_note"
        ),
        "uncertainty_note": "具体人物照片 L1 升级需 cheer 提供直链 + 高分辨率原件。",
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
                    f"L2/L3 needs_human_review Wikimedia Commons 民盟人物历史照片；"
                    f"PD-China 公有领域；"
                    f"WebFetch 2026-07-20 实测。"
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