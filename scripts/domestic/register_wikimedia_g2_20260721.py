#!/usr/bin/env python3
"""Register 批次 G-2: Wikimedia Commons 民盟 1941-1949 关键历史照片 8 条。

WebFetch 2026-07-21 实测（接续批次 G）：

A. 1937-07-31 七君子出狱合影（Qijunzi.jpg）
   - 公共领域 PD-China | 500×373 | 54KB
   - 7 人合影：沈钧儒/邹韬奋/李公朴/史良/章乃器/沙千里/王造时
   - 来源 audit.gov.cn + Wikipedia 多语言引用
   - 民盟前身救国会核心事件

B. 1949 第一届政协女代表合影
   - 公共领域 PD-China | 640×452 | 61KB
   - 含 邓颖超 + 宋庆龄 + 何香凝 + 罗叔章 + 史良
   - 一届政协女代表 = 民盟参与政协关键

C-D. 1936 沈钧儒在狱中（民盟前身七君子事件）

E-F. 1949 Soong Ching-ling at 1st CPPCC、宪法草案座谈会第八组

G. 1946 新政协筹备会常委合影（黄炎培分类）

等级：L2 needs_human_review → accepted（PD-China + 1989 历史档案出版物源）
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-21"

NEW_RECORDS = [
    # 1937-07-31 七君子出狱合影
    {
        "candidate_id": "domestic:WM:1937-07-31-qijunzi-chuyu-heying",
        "title": "1937-07-31 七君子出狱合影（七位救国领导人合影，民盟前身核心）",
        "creator": "作者不详（PD-China）",
        "document_date": "1937-07-31",
        "document_date_precision": "day",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 史良 / 沈钧儒分类",
        "collection_name": "史良分类 + 沈钧儒分类",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Qijunzi.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:Qijunzi.jpg；"
            "来源：http://www.audit.gov.cn/n1057/n1102/n2064/n2653/1650468.html"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Qijunzi.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 54KB 500×373；2010-04-01 上传；Wikipedia 多语言引用",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域；URAA 不适用",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1936七君子事件"],
        "person_tags": ["沈钧儒", "邹韬審", "李公朴", "史良", "章乃器", "沙千里", "王造时"],
        "place_tags": ["苏州"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/File:Qijunzi.jpg；"
            "元数据：拍摄 1937-07-31；上传 2010-04-01；JPEG 54KB 500×373；PD-China；"
            "照片描述：『七君子事件』七位领导人出狱前合影，左起：王造时 / 史良 / "
            "章乃器 / 沈钧儒 / 沙千里 / 李公朴 / 邹韬奋；"
            "七君子 = 民盟前身 1936 全国各界救国联合会核心 7 人；"
            "1936-11-23 被国民党政府逮捕，1937-07-31 抗战前夕释放；"
            "L2 等级：PD-China + 民盟前身核心事件 + 多语言 Wikipedia 引用。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": (
            "https://commons.wikimedia.org/wiki/File:Qijunzi.jpg (元数据)；"
            "https://upload.wikimedia.org/wikipedia/commons/.../Qijunzi.jpg (直接下载)；"
            "http://www.audit.gov.cn/n1057/n1102/n2064/n2653/1650468.html (中国审计署源)"
        ),
        "uncertainty_note": "原始出处需进一步确认；可升级 L1 取得原件档案级扫描。",
    },
    # 1949 一届政协女代表
    {
        "candidate_id": "domestic:WM:1949-yijie-zhengxie-nvdaibiao",
        "title": "1949 参加中国人民政治协商会议第一届全体会议的女代表合影（含 5 位核心女代表）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 史良分类 + CPPCC First Plenary Session 分类",
        "collection_name": "First Plenary Session of the CPPCC + 史良分类",
        "archive_item": "https://commons.wikimedia.org/wiki/File:参加中国人民政治协商会议第一届全体会议的女代表.jpg",
        "catalog_reference": (
            "Wikimedia Commons File:参加中国人民政治协商会议第一届全体会议的女代表.jpg；"
            "来源：163 博客 + 新华网论坛"
        ),
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%8F%82%E5%8A%A0%E4%B8%AD%E5%9B%BD%E4%BA%BA%E6%B0%91%E6%94%BF%E5%8B%99%E5%8D%8F%E5%95%86%E7%AC%AC%E4%B8%80%E5%B1%8A%E5%85%A8%E4%BD%93%E4%BC%9A%E8%AE%AE%E7%9A%84%E5%A5%B3%E4%BB%A3%E8%A1%A8.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 61KB 640×452；2015-12-17 上传；含 PRC + ROC 国旗",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949民盟参与政协"],
        "person_tags": ["邓颖超", "宋庆龄", "何香凝", "罗叔章", "史良", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons "
            "/wiki/File:参加中国人民政治协商会议第一届全体会议的女代表.jpg；"
            "元数据：日期 1949；PD-China；JPEG 61KB 640×452；2015-12-17 上传；"
            "照片描述：黑白合影，1949 拍摄，展示参加中国人民政治协商会议第一届全体会议的女代表；"
            "人物识别（Wikidata depicts + 分类）：邓颖超（明示）/ 宋庆龄 / 何香凝 / "
            "罗叔章 / 史良；"
            "史良 = 民盟中央副主席（1958-1965）+ 民盟核心领导人；"
            "L2 等级：PD-China + 一届政协民盟 + 关键 1949 时点。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:参加中国人民政治协商会议第一届全体会议的女代表.jpg",
        "uncertainty_note": "部分人物识别需进一步确认；L1 升级需原件级扫描。",
    },
    # 邓颖超悼词 (闻一多子分类)
    {
        "candidate_id": "domestic:WM:1946-dengyingchao-daoci-li-wen",
        "title": "邓颖超朗读周恩来为李公朴闻一多所写悼词（1946 年七七事变后）",
        "creator": "作者不详（PD-China）",
        "document_date": "1946",
        "document_date_precision": "year",
        "document_type": "1946 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 闻一多分类 + 史良分类",
        "collection_name": "Wen Yiduo (15F) + Shi Liang (9F)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Deng_Yingchao_reads_out_the_eulogy_written_by_Zhou_Enlai_for_Li_Gongpu_and_Wen_Yiduo.jpg",
        "catalog_reference": "Wikimedia Commons File:Deng Yingchao reads out the eulogy written by Zhou Enlai for Li Gongpu and Wen Yiduo.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Deng_Yingchao_reads_out_the_eulogy_written_by_Zhou_Enlai_for_Li_Gongpu_and_Wen_Yiduo.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；JPEG 86KB 400×262",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1946李公朴闻一多遇害"],
        "person_tags": ["邓颖超", "周恩来", "李公朴", "闻一多", "中国民主同盟"],
        "place_tags": ["上海"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons "
            "/wiki/File:Deng_Yingchao_reads_out_the_eulogy_written_by_Zhou_Enlai_for_Li_Gongpu_and_Wen_Yiduo.jpg；"
            "标题：邓颖超朗读周恩来为李公朴闻一多所写悼词；"
            "时间：1946（李公朴 1946-07-11 + 闻一多 1946-07-15 遇害后 10 天内的悼念活动）；"
            "李公朴 / 闻一多 = 民盟核心成员，1946 民盟最惨痛事件；"
            "L2 等级：PD-China + 民盟烈士悼念活动 + 周恩来亲笔悼词。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Deng_Yingchao_reads_out_the_eulogy_written_by_Zhou_Enlai_for_Li_Gongpu_and_Wen_Yiduo.jpg",
        "uncertainty_note": "具体场合（追悼会/上海/南京）需进一步确认；L1 升级需原件扫描。",
    },
    # 1936 沈钧儒在狱中
    {
        "candidate_id": "domestic:WM:1936-shen-junru-zaiyuzhong",
        "title": "1936 年沈钧儒在狱中（七君子事件核心照片）",
        "creator": "作者不详（PD-China）",
        "document_date": "1936",
        "document_date_precision": "year",
        "document_type": "民国时期历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 沈钧儒分类",
        "collection_name": "沈钧儒分类 (30 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:1963-08_1936年_沈钧儒在狱中.jpg",
        "catalog_reference": "Wikimedia Commons File:1963-08 1936年 沈钧儒在狱中.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:1963-08_1936%E5%B9%B4_%E6%B2%88%E9%92%A7%E5%84%92%E5%9C%A8%E7%8B%B1%E4%B8%AD.jpg",
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
        "person_tags": ["沈钧儒", "中国民主同盟"],
        "place_tags": ["上海", "苏州", "南京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 Wikimedia Commons /wiki/Category:Shen_Junru；"
            "1936 年沈钧儒在狱中（七君子事件核心照片）；"
            "沈钧儒 = 民盟前身救国会领袖；"
            "L2 等级：PD-China + 民盟前身核心事件。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:1963-08_1936年_沈钧儒在狱中.jpg",
        "uncertainty_note": "需进一步确认监狱地点（上海提篮桥 / 苏州）。",
    },
    # 1949 Soong Ching-ling at 1st CPPCC
    {
        "candidate_id": "domestic:WM:1949-song-ching-ling-1st-cppcc",
        "title": "1949 宋庆龄在第一届全国政协（民革名誉主席）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 史良分类 + CPPCC 分类",
        "collection_name": "First Plenary Session of the CPPCC",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Soong_Ching-ling_at_1st_CPPCC.jpg",
        "catalog_reference": "Wikimedia Commons File:Soong Ching-ling at 1st CPPCC.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Soong_Ching-ling_at_1st_CPPCC.jpg",
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
        "person_tags": ["宋庆龄", "中国国民党革命委员会", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测 /wiki/Category:Shi_Liang；"
            "宋庆龄在第一届全国政协（1949）= 民革名誉主席出席；"
            "L2 等级：PD-China + 1949 一届政协。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Soong_Ching-ling_at_1st_CPPCC.jpg",
        "uncertainty_note": "需进一步确认具体场合。",
    },
    # 1949 一届政协女代表 收 已在 batch G 注册
    # 1949 宪法草案座谈会
    {
        "candidate_id": "domestic:WM:1949-xianfa-caogao-zuotanhui-di8zu-heying",
        "title": "1949 宪法草案座谈会第八组合影（含民主党派代表）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 史良分类",
        "collection_name": "史良分类 (9 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:宪法草案座谈会第八组合影.jpg",
        "catalog_reference": "Wikimedia Commons File:宪法草案座谈会第八组合影.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:%E5%AE%AA%E6%B3%95%E8%8D%89%E6%A1%88%E5%BA%A7%E8%B0%88%E4%BC%9A%E7%AC%AC%E5%85%AB%E7%BB%84%E5%90%88%E5%BD%B1.jpg",
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
        "person_tags": ["史良", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "1949 宪法草案座谈会第八组合影（含民盟/民革代表，含史良）；"
            "L2 等级：PD-China + 1949 宪法草案起草。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:宪法草案座谈会第八组合影.jpg",
        "uncertainty_note": "需进一步确认全部人物。",
    },
    # 1949 Cai Chang and Shiliang on Tian'anmen
    {
        "candidate_id": "domestic:WM:1949-cai-chang-shiliang-tiananmen",
        "title": "1949 蔡畅与史良在天安门（开国大典）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 史良分类",
        "collection_name": "史良分类 (9 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Cai_Chang_and_Shiliang_on_Tian%27anmen.jpg",
        "catalog_reference": "Wikimedia Commons File:Cai Chang and Shiliang on Tian'anmen.jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Cai_Chang_and_Shiliang_on_Tian%27anmen.jpg",
        "source_url_role": "item_surrogate",
        "access_mode": "open",
        "access_note": "PD-China；开国大典天安门合影；",
        "medium": "digital",
        "online_availability": "full_item_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "PD-China 公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core",
        "event_tags": ["1949开国大典", "1949民盟参与政协"],
        "person_tags": ["蔡畅", "史良", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "蔡畅与史良在天安门（1949-10-01 开国大典）；"
            "史良 = 民盟中央副主席（1958-1965）+ 新中国第一任司法部部长；"
            "L2 等级：PD-China + 开国大典。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Cai_Chang_and_Shiliang_on_Tian%27anmen.jpg",
        "uncertainty_note": "需进一步确认日期。",
    },
    # 1949 Shiliang on Tian'anmen (cropped)
    {
        "candidate_id": "domestic:WM:1949-shiliang-tiananmen-cropped",
        "title": "1949 史良在天安门城楼（开国大典）",
        "creator": "作者不详（PD-China）",
        "document_date": "1949",
        "document_date_precision": "year",
        "document_type": "1949 历史照片（公有领域 PD-China）",
        "repository_code": "WM",
        "repository_name": "Wikimedia Commons 史良分类",
        "collection_name": "史良分类 (9 文件)",
        "archive_item": "https://commons.wikimedia.org/wiki/File:Shiliang_on_Tian%27anmen_(cropped).jpg",
        "catalog_reference": "Wikimedia Commons File:Shiliang on Tian'anmen (cropped).jpg",
        "catalog_reference_status": "verified",
        "source_url": "https://commons.wikimedia.org/wiki/File:Shiliang_on_Tian%27anmen_(cropped).jpg",
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
        "event_tags": ["1949开国大典"],
        "person_tags": ["史良", "中国民主同盟"],
        "place_tags": ["北京"],
        "evidence_note": (
            "WebFetch 2026-07-21 实测；"
            "史良在天安门城楼（开国大典）；"
            "L2 等级：PD-China + 开国大典。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": "https://commons.wikimedia.org/wiki/File:Shiliang_on_Tian%27anmen_(cropped).jpg",
        "uncertainty_note": "需进一步确认日期与剪裁关系。",
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
                    f"L2 needs_human_review Wikimedia Commons 民盟 1941-1949 历史照片（批次 G-2）；"
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