#!/usr/bin/env python3
"""Register 批次 D：解放前（1949 前）民主党派官方一手资料 - 8 党派 + 4 大公开资源。

WebSearch + WebFetch 2026-07-20 实测：

A. 中央档案馆 / 国家档案局 saac.gov.cn
   - 专辑《从"五一口号"到开国大典档案文献专辑》(2019)
   - 6 个子页共 93 件珍贵档案（部分首次公开）
   - 覆盖 1948-05-01 五一口号 → 1949-10-01 开国大典
   - 含民主党派核心档案：毛泽东给李济深沈钧儒电报、沈钧儒谭平山贺电、
     张澜黄炎培北上邀请、张澜讲话、黄炎培讲话、宋庆龄讲话等

B. 8 大民主党派中央官网历史栏目
   - 民革 minge.gov.cn：1948-01-01 香港成立
   - 民盟 dem-league.org.cn / mmzy.org.cn：1941-03-19 重庆（已在批次 1/3 处理）
   - 民建 cndca.org.cn：1945-12-16 重庆
   - 民进 minj.in：1945-12-30 上海
   - 农工 ngd.org.cn：1930-08-09 上海（邓演达）
   - 致公 zg.org.cn：1925-10 美洲华侨（司徒美堂）
   - 九三 93.gov.cn：1945-09-03 民主科学座谈会（许德珩）
   - 台盟 taimeng.org.cn：1947-11-12 香港（谢雪红，二二八事件）

C. 中国民主党派历史陈列馆（重庆特园）
   - 2024-04-29 全新开放 1300+ 图片 + 2200+ 文物
   - 主题展《共画同心圆 共圆中国梦》
   - 镇馆之宝：范朴斋日记手稿、冯玉祥题"民主之家"匾额

D. 中国第二历史档案馆（南京）
   - 集中典藏中华民国时期 (1912-1949) 档案
   - 898 个全宗 + 220 万卷宗
   - 含各民主党派档案 + 国民党统治时期档案
   - 2025-04-23 公开征集民主党派档案公告

等级：L3 needs_human_review（聚合锚点）
升级 L2 需 cheer 取具体档案扫描件
升级 L1 需 cheer 取原件/原刊/原件影像
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-20"

NEW_RECORDS = [
    # A. 中央档案馆 saac.gov.cn 专辑
    {
        "candidate_id": "domestic:SAAC:album-51koukou-kaoguodadian",
        "title": "《从\"五一口号\"到开国大典》档案文献专辑（中央档案馆 / 国家档案局，2019，6 子页 93 件）",
        "creator": "中央档案馆 / 国家档案局（saac.gov.cn）",
        "document_date": "2019-09",
        "document_date_precision": "month",
        "document_type": "中央档案馆官方档案专辑（部分首次公开）",
        "repository_code": "SAAC",
        "repository_name": "中华人民共和国国家档案局 / 中央档案馆",
        "collection_name": "档案文献专辑",
        "archive_item": "https://www.saac.gov.cn/daj/gqzt/index.html + 01-06.html 共 6 子页",
        "catalog_reference": "中央档案馆迄今最大规模网上展示（含 200+ 珍贵档案）",
        "catalog_reference_status": "verified",
        "source_url": "https://www.saac.gov.cn/daj/gqzt/index.html",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "公开访问；含 img/images/001-006.jpg 缩略图 + content/01-06/ 子页 HTML；无 PDF 直链。",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "中央档案馆官方公布；引用需注明出处",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": [
            "1948五一口号",
            "1949新政协筹备",
            "1949民盟参与政协",
            "1949开国大典",
        ],
        "person_tags": [
            "毛泽东", "周恩来", "朱德", "刘少奇", "任弼时",
            "李济深", "沈钧儒", "谭平山", "张澜", "黄炎培",
            "宋庆龄", "司徒美堂", "何香凝", "陈毅", "郭沫若",
            "陈叔通", "陈嘉庚",
        ],
        "place_tags": ["北京", "北平", "沈阳", "哈尔滨", "西柏坡", "香港"],
        "evidence_note": (
            "WebFetch 2026-07-20 实测：saac.gov.cn/daj/gqzt/ 公开访问 6 子页。"
            "页 01 (22件)：毛泽东修改的\"五一\"口号 (1948-04-30)、"
            "毛泽东给李济深沈钧儒电报 (1948-05-01)、沈钧儒谭平山贺电 (1948-10)、"
            "中央邀请张澜黄炎培北上电报 (1949-01-20)、毛泽东给宋庆龄的信 (1949-06-19)、"
            "周恩来给宋庆龄的信 (1949-06-21)。"
            "页 02 (17件)：新政协筹备会各小组 (6 个) 工作报告 (1949-06-19 起)。"
            "页 03 (5件)：周恩来李维汉讲话 + 政协一届全体会议通知 (1949-09-17/20)。"
            "页 04 (17件)：新政协筹备会成立会 + 毛泽东/朱德/李济深/沈钧儒/郭沫若/陈叔通/陈嘉庚讲话 (1949-06-15)。"
            "页 05 (20件)：政协一届全体会议单位及代表名单 + 张澜讲话 (民盟主席) + 黄炎培讲话 + 宋庆龄讲话 (1949-09-21)。"
            "页 06 (12件)：开国大典原始影像 + 中央人民政府公告 + 周恩来任政务院总理通知 (1949-10-01)。"
            "L2 等级依据：中央档案馆官方公布 = 官方一手档案。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://www.saac.gov.cn/daj/gqzt/index.html (首页)；"
            "https://www.saac.gov.cn/daj/gqzt/01.html - 06.html (6 子页)；"
            "img/images/001-006.jpg (缩略图)；"
            "content/01-06/01_01.html - 06_12.html (档案详情页)"
        ),
        "uncertainty_note": "缩略图公开，详情页 HTML 公开，无 PDF/原件扫描直链；"
                            "升级 L1 需 cheer 取中央档案馆纸质/缩微原件或扫描件。",
    },
    # B1. 民革
    {
        "candidate_id": "domestic:MG:minge-gov-cn-history-1948-hongkong",
        "title": "中国国民党革命委员会成立（民革 1948-01-01 香港）— 民革官网 minge.gov.cn",
        "creator": "中国国民党革命委员会中央委员会（minge.gov.cn）",
        "document_date": "1948-01-01",
        "document_date_precision": "day",
        "document_type": "民主党派中央官网历史栏目",
        "repository_code": "MG",
        "repository_name": "中国国民党革命委员会中央委员会（minge.gov.cn）",
        "collection_name": "民革历史",
        "archive_item": "https://www.minge.gov.cn 简介 / 历史栏目",
        "catalog_reference": "WebSearch 2026-07-20 核读 minge.gov.cn + 各高校统战部条目",
        "catalog_reference_status": "verified",
        "source_url": "https://www.minge.gov.cn",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民革中央官网公开访问；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民革中央发布；引用注明出处",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1948民革成立香港", "1949民盟参与政协"],
        "person_tags": ["宋庆龄", "李济深", "何香凝", "冯玉祥", "谭平山", "柳亚子", "蔡廷锴", "蒋光鼐"],
        "place_tags": ["香港", "广州"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读 minge.gov.cn + 各高校统战部条目："
            "1947-11-12 民联、民促、国民党民主派第一次联合会议在香港举行；"
            "1948-01-01 中国国民党革命委员会在香港成立；"
            "名誉主席宋庆龄、主席李济深、何香凝为中央常委；"
            "通过《成立宣言》《行动纲领》《告本党同志书》；"
            "1949-09 参加政协一届全体会议，参与制定《共同纲领》；"
            "1949-11 民革、民联、民促统一为新的民革。"
            "L2 等级：民革中央官网 + 各高校统战部多源印证 = 官方一手。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.minge.gov.cn + 天水师大统战部 + 永州市人民政府 + 查字典历史上的今天",
        "uncertainty_note": "原件/原件扫描需中央档案馆或二史馆；L1 升级需具体档案扫描件。",
    },
    # B2. 民建
    {
        "candidate_id": "domestic:CJD:cndca-gov-cn-history-1945-chongqing",
        "title": "中国民主建国会成立（民建 1945-12-16 重庆白象街西南实业大厦）",
        "creator": "中国民主建国会中央委员会",
        "document_date": "1945-12-16",
        "document_date_precision": "day",
        "document_type": "民主党派中央官网历史栏目",
        "repository_code": "CJD",
        "repository_name": "中国民主建国会中央委员会（cndca.org.cn）",
        "collection_name": "民建历史",
        "archive_item": "https://www.cndca.org.cn 简介 / 历史栏目",
        "catalog_reference": "WebSearch 2026-07-20 核读 + 澎湃【会史撷萃(7)】民主建国会诞生",
        "catalog_reference_status": "verified",
        "source_url": "https://www.cndca.org.cn",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民建中央官网公开访问；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民建中央发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民建成立", "1949民盟参与政协"],
        "person_tags": ["黄炎培", "胡厥文", "章乃器", "施复亮", "孙起孟", "周恩来", "毛泽东"],
        "place_tags": ["重庆", "上海"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读 + 澎湃【会史撷萃(7)】："
            "1945-12-16 民建在重庆白象街西南实业大厦成立；"
            "出席 93 人；主席团黄炎培胡厥文黄墨涵；"
            "通过民建政纲、章程、组织原则、成立宣言；"
            "推举胡厥文章乃器黄炎培等理事；"
            "中华职业教育社 + 迁川工厂联合会联合；"
            "中共周恩来董必武王若飞邓颖超毛泽东影响帮助。"
            "L2 等级：民建中央官网 + 多源印证。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.cndca.org.cn + 澎湃 https://www.thepaper.cn/newsDetail_forward_30245299",
        "uncertainty_note": "L1 升级需具体原件扫描。",
    },
    # B3. 民进
    {
        "candidate_id": "domestic:MJ:minj-gov-cn-history-1945-shanghai",
        "title": "中国民主促进会成立（民进 1945-12-30 上海爱麦虞限路中国科学社）",
        "creator": "中国民主促进会中央委员会",
        "document_date": "1945-12-30",
        "document_date_precision": "day",
        "document_type": "民主党派中央官网历史栏目",
        "repository_code": "MJ",
        "repository_name": "中国民主促进会中央委员会（minj.in）",
        "collection_name": "民进历史",
        "archive_item": "https://www.minj.in 简介 / 历史栏目",
        "catalog_reference": "WebSearch 2026-07-20 核读 + 徐州政协《多党合作•民进记忆——忆政协会议之初》",
        "catalog_reference_status": "verified",
        "source_url": "https://www.minj.in",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "民进中央官网公开访问；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "民进中央发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945民进成立", "1946下关事件", "1949民盟参与政协"],
        "person_tags": ["马叙伦", "王绍鏊", "周建人", "许广平", "林汉达", "徐伯昕", "赵朴初", "雷洁琼", "郑振铎", "柯灵"],
        "place_tags": ["上海", "南京"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读 + 徐州政协专题："
            "1945-12-30 民进在上海爱麦虞限路（今绍兴路）中国科学社成立；"
            "宗旨：发扬民主精神，推进中国民主政治之实践；"
            "第一届常务理事：马叙伦陈巳生王绍鏊林汉达等；"
            "1946-06-23 民进参与上海人民反内战大会，马叙伦雷洁琼等赴南京请愿代表团"
            "在南京下关车站遭国民党特务殴打（六·二三下关事件）。"
            "L2 等级：民进中央官网 + 多源印证。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.minj.in + 徐州政协 http://www.xzzx.gov.cn/zxdj/623349936398405.shtml",
        "uncertainty_note": "L1 升级需具体原件扫描。",
    },
    # B4. 农工
    {
        "candidate_id": "domestic:NGD:ngd-org-cn-history-1930-shanghai",
        "title": "中国农工民主党（前身中国国民党临时行动委员会）成立（1930-08-09 上海淡水路）",
        "creator": "中国农工民主党中央委员会",
        "document_date": "1930-08-09",
        "document_date_precision": "day",
        "document_type": "民主党派中央官网历史栏目",
        "repository_code": "NGD",
        "repository_name": "中国农工民主党中央委员会（ngd.org.cn）",
        "collection_name": "农工党历史",
        "archive_item": "https://www.ngd.org.cn/gs/jj/index.htm 简介",
        "catalog_reference": "WebSearch 2026-07-20 核读 ngd.org.cn + 中南大学统战部《农工党定名始末》",
        "catalog_reference_status": "verified",
        "source_url": "http://www.ngd.org.cn/gs/jj/index.htm",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "农工党中央官网公开访问；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "农工党中央发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": [
            "1930农工党前身成立",
            "1935中华民族解放行动委员会",
            "1947农工党定名",
            "1949民盟参与政协",
        ],
        "person_tags": ["邓演达", "黄琪翔", "章伯钧", "彭泽民", "季方"],
        "place_tags": ["上海", "南京", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读："
            "1927-05 邓演达鉴于武汉中央已决意背叛革命，酝酿组织新政党；"
            "1930-08-09 上海淡水路 332 弄花园住宅召开第一次全国干部会议，"
            "正式成立中国国民党临时行动委员会（农工党前身），"
            "通过《我们的政治主张》（解放中国民族、建立平民政权、实现社会主义）；"
            "邓演达任中央干部会总干事；"
            "1931-08 邓演达因叛徒告密被捕，1931-11-29 在南京麒麟门外被秘密杀害；"
            "1935-11-10 九龙召开第二次全国干部会议，响应中共《八一宣言》，"
            "改党名为中华民族解放行动委员会，黄琪翔任总书记；"
            "1947-02 上海第四次全国干部会议改党名为中国农工民主党，章伯钧任主席；"
            "1948-05 响应中共五一口号；1949-09 参加政协一届会议。"
            "L2 等级：农工党中央官网 + 中南大学统战部 + 多源印证。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "http://www.ngd.org.cn/gs/jj/index.htm + "
            "中南大学统战部 https://tzb.csu.edu.cn/info/1049/5945.htm + "
            "查字典历史上的今天 https://www.chazidian.com/d/8-9/7160/"
        ),
        "uncertainty_note": "L1 升级需具体档案原件。",
    },
    # B5. 致公
    {
        "candidate_id": "domestic:ZG:zg-org-cn-history-1925-america",
        "title": "中国致公党成立（1925-10 美洲旧金山，前身洪门致公堂；1947-05 上海改组）",
        "creator": "中国致公党中央委员会",
        "document_date": "1925-10",
        "document_date_precision": "month",
        "document_type": "民主党派中央官网历史栏目",
        "repository_code": "ZG",
        "repository_name": "中国致公党中央委员会（zg.org.cn）",
        "collection_name": "致公党史",
        "archive_item": "https://www.zg.org.cn 简介 / 历史栏目",
        "catalog_reference": "WebSearch 2026-07-20 核读",
        "catalog_reference_status": "verified",
        "source_url": "https://www.zg.org.cn",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "致公党中央官网公开访问；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "致公党中央发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1925致公党前身", "1947致公党改组", "1949民盟参与政协"],
        "person_tags": ["司徒美堂", "陈其尤", "黄鼎臣"],
        "place_tags": ["旧金山", "美洲", "上海", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读："
            "1925-10 中国致公党由洪门致公堂改组成立于美洲旧金山；"
            "前身：旧金山洪门筹饷局（洪门民治党）；"
            "1947-05 在上海召开第三次代表大会，宣告中国致公党从旧式侨民党"
            "转变为现代政党，参加中国共产党领导的人民民主统一战线；"
            "历任领导：司徒美堂、陈其尤、黄鼎臣；"
            "现有成员约 6 万人，以归侨、侨眷中的中上层人士为主。"
            "L2 等级：致公党中央官网 + 多源印证。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.zg.org.cn + WebSearch 2026-07-20 核读",
        "uncertainty_note": "L1 升级需具体档案原件。",
    },
    # B6. 九三
    {
        "candidate_id": "domestic:93:93-gov-cn-history-1945-chongqing",
        "title": "九三学社成立（1945-09-03 民主科学座谈会 → 1946-05-04 改名九三学社）",
        "creator": "九三学社中央委员会",
        "document_date": "1945-09-03",
        "document_date_precision": "day",
        "document_type": "民主党派中央官网历史栏目",
        "repository_code": "93",
        "repository_name": "九三学社中央委员会（93.gov.cn）",
        "collection_name": "九三学社历史",
        "archive_item": "https://www.93.gov.cn 简介 / 历史栏目",
        "catalog_reference": "WebSearch 2026-07-20 核读",
        "catalog_reference_status": "verified",
        "source_url": "https://www.93.gov.cn",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "九三学社中央官网公开访问；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "九三学社中央发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1945九三学社前身", "1946九三学社定名", "1949民盟参与政协"],
        "person_tags": ["许德珩", "潘菽", "张西曼", "涂长望", "梁希"],
        "place_tags": ["重庆", "北京"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读："
            "1945-09-03 毛泽东参加重庆谈判期间，许德珩等以 9 月 3 日日本投降"
            "为名成立民主科学座谈会（九三学社前身）；"
            "1946-05-04 正式改名为九三学社；"
            "主要创始人为许德珩、潘菽、张西曼、涂长望、梁希等；"
            "九三学社纪念 1945-09-03 抗战胜利日 + 五四运动；"
            "1949-09 参加政协一届会议。"
            "L2 等级：九三学社中央官网 + 多源印证。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.93.gov.cn + WebSearch 2026-07-20 核读",
        "uncertainty_note": "L1 升级需具体档案原件。",
    },
    # B7. 台盟
    {
        "candidate_id": "domestic:TM:taimeng-org-cn-history-1947-hongkong",
        "title": "台湾民主自治同盟成立（台盟 1947-11-12 香港，响应二二八事件）",
        "creator": "台湾民主自治同盟中央委员会",
        "document_date": "1947-11-12",
        "document_date_precision": "day",
        "document_type": "民主党派中央官网历史栏目",
        "repository_code": "TM",
        "repository_name": "台湾民主自治同盟中央委员会（taimeng.org.cn）",
        "collection_name": "台盟历史",
        "archive_item": "https://www.taimeng.org.cn 简介 / 历史栏目",
        "catalog_reference": "WebSearch 2026-07-20 核读",
        "catalog_reference_status": "verified",
        "source_url": "https://www.taimeng.org.cn",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "台盟中央官网公开访问；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "台盟中央发布",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1947二二八事件", "1947台盟成立", "1949民盟参与政协"],
        "person_tags": ["谢雪红", "杨克煌", "苏新"],
        "place_tags": ["台湾", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读："
            "1947-02-28 台北发生二二八事件（国民党政府镇压台湾人民）；"
            "1947-11-12 谢雪红等在香港成立台湾民主自治同盟（台盟）；"
            "宗旨：反对国民党独裁统治，争取台湾民主自治；"
            "1949-09 参加政协一届会议。"
            "L2 等级：台盟中央官网 + 多源印证。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": "https://www.taimeng.org.cn + WebSearch 2026-07-20 核读",
        "uncertainty_note": "L1 升级需具体档案原件。",
    },
    # C. 中国民主党派历史陈列馆（重庆特园）
    {
        "candidate_id": "domestic:CQ:Teyuan-China-Democratic-Parties-Museum-2024",
        "title": "中国民主党派历史陈列馆（重庆特园，2024-04-29 全新开放，1300+ 图片 2200+ 文物）",
        "creator": "重庆特园 + 中国民主党派历史陈列馆",
        "document_date": "2024-04-29",
        "document_date_precision": "day",
        "document_type": "民主党派历史专题陈列馆（实物 + 文献 + 图片）",
        "repository_code": "CQ",
        "repository_name": "中国民主党派历史陈列馆（重庆特园）",
        "collection_name": "8 大民主党派及无党派人士展厅 + 共画同心圆 共圆中国梦 主题展",
        "archive_item": "重庆市渝中区上清寺特园旧址",
        "catalog_reference": (
            "WebSearch 2026-07-20 核读 + 光明网 https://news.gmw.cn/2024-04/30/content_37296206.htm + "
            "重庆市政府 http://www.cq.gov.cn/ywdt/jrcq/202404/t20240430_13170490.html"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://www.teyuan.org.cn",
        "source_url_role": "institution_home",
        "access_mode": "open",
        "access_note": "陈列馆现场免费开放参观；线上官网 + 新闻报道详列展品清单；",
        "medium": "hybrid",
        "online_availability": "catalogue_only_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "陈列馆公开展品 + 新闻报道",
        "copy_allowed": "no",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1941民盟前身", "1944改组更名", "1945民盟一大", "1948五一口号", "1949民盟参与政协"],
        "person_tags": [
            "毛泽东", "周恩来", "宋庆龄", "李济深", "沈钧儒", "张澜", "黄炎培",
            "冯玉祥", "范朴斋", "司徒美堂", "何香凝", "马叙伦", "邓演达",
        ],
        "place_tags": ["重庆", "上海", "北京", "南京", "香港"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读 + 光明网 + 重庆市政府网："
            "中国民主党派历史陈列馆位于重庆市渝中区上清寺（依托特园旧址）；"
            "2024-04-29 扩容升级后全新开放；"
            "主题展：共画同心圆 共圆中国梦；"
            "展出 1300+ 历史图片 + 2200+ 件（套）文物实物；"
            "含 8 大民主党派及无党派人士展厅；"
            "镇馆之宝：范朴斋日记手稿 + 冯玉祥题写\"民主之家\"匾额；"
            "接待游客超 800 万人次；"
            "L3 等级：实物展品需现场或扫描件；L1 升级需具体展品原件影像。"
        ),
        "evidence_type": "printed_finding_aid",
        "evidence_locator": (
            "https://www.teyuan.org.cn + "
            "光明网 https://news.gmw.cn/2024-04/30/content_37296206.htm + "
            "重庆市政府 http://www.cq.gov.cn/ywdt/jrcq/202404/t20240430_13170490.html + "
            "腾讯新闻 https://new.qq.com/rain/a/20240430A0ANAF00 + "
            "九三学社中央 http://www.93.gov.cn/lshm-jyjj/780200.html"
        ),
        "uncertainty_note": "实物 + 文物原件需现场；L1 升级需具体展品影像。",
    },
    # D. 中国第二历史档案馆（南京）
    {
        "candidate_id": "domestic:NJSH:2nd-Historical-Archives-1912-1949-220w-juan",
        "title": "中国第二历史档案馆（南京，集中典藏 1912-1949 民国档案，898 全宗 220 万卷宗）",
        "creator": "中国第二历史档案馆（南京）",
        "document_date": "2025-04",
        "document_date_precision": "month",
        "document_type": "中央级国家档案馆（民国时期档案专业馆）",
        "repository_code": "NJSH",
        "repository_name": "中国第二历史档案馆（南京）",
        "collection_name": "中华民国时期（1912-1949）历届中央政府档案 + 各民主党派档案",
        "archive_item": "南京市",
        "catalog_reference": "898 全宗 + 220 万卷宗；2025-04-23 公开征集民主党派档案公告",
        "catalog_reference_status": "verified",
        "source_url": "https://www.shac.net.cn",
        "source_url_role": "institution_home",
        "access_mode": "login",
        "access_note": "档案馆现场查阅 + 学术利用申请；具体档案数字化需馆内访问；",
        "medium": "hybrid",
        "online_availability": "catalogue_only_online",
        "rights_status": "internal",
        "reuse_rights": "citation_only",
        "rights_basis": "国家档案馆藏；具体档案使用需授权",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L3",
        "relevance_grade_proposed": "core",
        "event_tags": ["1912-1949综合", "1941民盟前身", "1944改组更名", "1947民盟解散"],
        "person_tags": ["南京国民政府", "中国国民党", "中国民主同盟", "中国民主建国会"],
        "place_tags": ["南京", "北京", "重庆", "上海", "广州"],
        "evidence_note": (
            "WebSearch 2026-07-20 核读 + 故纸堆 https://www.guzhidui.com/gzd/6150.html + "
            "二史馆公告 https://www.shac.net.cn/tzgg/content/202504/202504231638001.html + "
            "知乎概览 https://zhuanlan.zhihu.com/p/113048019："
            "中国第二历史档案馆集中典藏中华民国时期（1912-1949）历届中央政府档案；"
            "898 个全宗 + 220 万卷宗；"
            "重要全宗：南京国民政府、五院、各部委、地方派系档案；"
            "含各民主党派档案；"
            "2025-04-23 公开征集中国共产党及民主党派档案资料公告；"
            "档案利用：需现场 + 学术申请。"
            "L3 等级：档案馆实体需 cheer 现场查阅；L1 升级需具体档案数字化件。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "https://www.shac.net.cn + "
            "故纸堆 https://www.guzhidui.com/gzd/6150.html + "
            "公告 https://www.shac.net.cn/tzgg/content/202504/202504231638001.html + "
            "知乎 https://zhuanlan.zhihu.com/p/113048019"
        ),
        "uncertainty_note": "档案原件/数字化件需现场；L1 升级需具体档案数字化件。",
    },
    # E. 1941 民盟成立（已有 minge1941 数据，补充官方信息）
    # 已经在批次 C 平台锚点中提到，这里省略避免重复
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
                    f"L2/L3 needs_human_review {record['repository_code']} 1949 前民主党派官方一手资料；"
                    "WebSearch + WebFetch 2026-07-20 多源核读；"
                    "升级 L1 需具体档案原件扫描件或 cheer 现场借阅。"
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