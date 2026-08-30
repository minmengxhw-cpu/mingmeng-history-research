#!/usr/bin/env python3
"""Register 1943 民盟 key publications found via WebSearch 2026-07-19.

Three L4 records citing publicly-verifiable references to 1943 民盟 primary
publications. The original booklets/articles are primary (e.g. 张澜
《中国需要真正民主政治》小册子), but we have not yet retrieved scanned
originals — only secondary WebSearch results pointing to their existence
and content.

L4 (二级叙述/网页) per project standards: these records are research
leads pointing to primary publications. Upgrade to L2 / L1 requires
access to actual scanned booklets via NLC / 二史馆 / 民盟中央档案.

Reference URLs (all public):
- 张澜纪念馆 zl1872.cn (民盟中央 / 张澜纪念馆官方背景)
- 民主同盟四川省委员会 mmscsw.gov.cn
- 全国政协 cppcc.gov.cn
- 头条号 / 搜狐等综合新闻站点
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


TODAY = "2026-07-19"

NEW_RECORDS = [
    {
        "candidate_id": "domestic:ZLWEB:1943-09-18-zhang-lan-china-needs-real-democracy",
        "title": "张澜《中国需要真正民主政治》小册子（1943-09-18，重庆）",
        "creator": "张澜（中国民主政团同盟主席）",
        "document_date": "1943-09-18",
        "document_date_precision": "day",
        "document_type": "民盟主席时政评论小册子（同期原刊，需寻原件影像）",
        "repository_code": "ZLWEB",
        "repository_name": "张澜纪念馆／张澜网（民盟中央背景）",
        "collection_name": "张澜纪念馆·张澜与中国民主同盟",
        "catalog_reference": "张澜网 zl1872.cn（多个分页）+ 中国民主同盟四川省委员会 mmscsw.gov.cn",
        "catalog_reference_status": "verified",
        "source_url": "http://www.zl1872.cn/zxxnewsview.aspx?producid=1397",
        "source_url_role": "finding_aid",
        "access_mode": "open",
        "access_note": "张澜纪念馆官方页面提供小册子背景、发表时间、影响记载；小册子原件待寻二史馆 / 民盟中央档案 / NLC 民国图书库",
        "medium": "digital",
        "online_availability": "surrogate_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "小册子本身约 1943-09 出版（>80 年），按中国著作权法应进入公有领域；张澜纪念馆页面版权以站点规则为准",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L4",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜", "1941民盟前身"],
        "person_tags": ["张澜", "蒋介石", "中国民主政团同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-19 核读：1943-09-18 张澜以中国民主政团同盟主席身份在重庆发表"
            "小册子《中国需要真正民主政治》（注：部分页面记为《中国需要真正的民主政治》）。"
            "发表契机：1943-09 国民参政会三届二次大会前夕，蒋介石派张群赴成都敦请张澜出席；"
            "9-17 蒋介石请张澜等参政员当面交换意见，张澜直言应『立即结束训政、还政于民』；"
            "9-18 小册子发表后『发行以来，风行一时，对各方影响甚大』。"
            "张澜因此拒绝出席国民参政会。"
            "1944-02-22 中共中央机关报《解放日报》发表长文专门介绍此文，誉之为民主运动『冲锋号』。"
            "小册子原件档号待查二史馆 / 民盟中央档案。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "在线检索词来源：\n"
            "  张澜纪念馆 http://www.zl1872.cn/zxxnewsview.aspx?producid=1397\n"
            "  张澜与中国民主同盟 http://www.zl1872.cn/zxxnewsview.aspx?producid=16\n"
            "  解放前民盟主张的民主制度 http://www.zl1872.cn/zxxnewsview.aspx?producid=519\n"
            "  民盟四川省委员会 mmscsw.gov.cn (《民盟和延安时期的<解放日报>》)\n"
            "  中国人民政治协商会议全国委员会 cppcc.gov.cn 张澜条目"
        ),
        "uncertainty_note": (
            "WebSearch 结果为综合叙述，未取得小册子原件影像或全文逐字转录；"
            "小册子页数、发行机构、ISBN（如有再版）待查；"
            "1944-02-22《解放日报》原文版次待查；"
            "升级 L1 / L2 需 NLC / 二史馆 / 延安革命纪念馆取原刊影像。"
        ),
    },
    {
        "candidate_id": "domestic:ZLWEB:1943-09-17-jiang-zhang-chongqing-exchange",
        "title": "1943-09-17 蒋介石与张澜等参政员重庆当面交锋事件",
        "creator": "张澜（记录）／蒋介石（被记）／陈立夫等（在场）",
        "document_date": "1943-09-17",
        "document_date_precision": "day",
        "document_type": "宪政运动关键事件（同期记录，需寻档案）",
        "repository_code": "ZLWEB",
        "repository_name": "张澜纪念馆／张澜网（民盟中央背景）",
        "collection_name": "张澜纪念馆·张澜与中国民主同盟",
        "catalog_reference": "张澜网 zl1872.cn（多个分页）+ 中国民主同盟四川省委员会",
        "catalog_reference_status": "verified",
        "source_url": "http://www.zl1872.cn/zxxnewsview.aspx?producid=1397",
        "source_url_role": "finding_aid",
        "access_mode": "open",
        "access_note": "事件记载在张澜纪念馆页面及多家研究网站；具体档案原件待寻二史馆或民盟中央",
        "medium": "digital",
        "online_availability": "surrogate_online",
        "rights_status": "public",
        "reuse_rights": "citation_only",
        "rights_basis": "事件记载本身是当代研究叙述，原始档案待查",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L4",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜"],
        "person_tags": ["张澜", "蒋介石", "张群", "中国民主政团同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "WebSearch 2026-07-19 核读：1943-09 中旬，蒋介石派张群赴成都敦请张澜"
            "出席 1943-09-18 国民参政会三届二次大会；张澜答应参加。"
            "9-17 蒋介石请张澜等参政员在重庆当面交换意见，张澜直言『应立即结束训政、"
            "还政于民』，拒绝国民党一党专治的宪政方案。"
            "次日（9-18）张澜发表《中国需要真正民主政治》小册子，发行后风行一时。"
            "张澜随后拒绝出席国民参政会。"
            "这是 1943 国统区宪政运动与民盟组织扩张的关键事件。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "张澜纪念馆 http://www.zl1872.cn/zxxnewsview.aspx?producid=1397\n"
            "民盟四川省委员会 mmscsw.gov.cn"
        ),
        "uncertainty_note": (
            "事件为综合叙述；具体档案原件（《国民参政会记录》《蒋张会谈记录》等）"
            "待寻二史馆或民盟中央档案；张澜自己是否有 1943 日记记载待查（《黄炎培日记》"
            "第 8 卷覆盖此期但本人是黄炎培非张澜）。"
        ),
    },
    {
        "candidate_id": "domestic:JFB:1944-02-22-jiefang-ribao-zhang-lan-booklet-review",
        "title": "1944-02-22《解放日报》长文介绍张澜《中国需要真正民主政治》",
        "creator": "《解放日报》社（中共中央机关报）",
        "document_date": "1944-02-22",
        "document_date_precision": "day",
        "document_type": "中共中央机关报评论文章（同期延安原刊）",
        "repository_code": "JFB",
        "repository_name": "《解放日报》延安版／中共中央机关报",
        "collection_name": "《解放日报》延安 1944 年 2 月",
        "catalog_reference": "WebSearch 提到 1944-02-22 介绍张澜小册子的长文，版次与作者待考",
        "catalog_reference_status": "pending",
        "source_url": "http://www.zl1872.cn/zxxnewsview.aspx?producid=1397",
        "source_url_role": "finding_aid",
        "access_mode": "open",
        "access_note": "《解放日报》1944-02-22 长文版次、作者待寻；延安革命纪念馆或国家图书馆可能有原刊",
        "medium": "digital",
        "online_availability": "surrogate_online",
        "rights_status": "public",
        "reuse_rights": "public_domain",
        "rights_basis": "中共中央机关报延安原刊（>80 年），中国著作权法进入公有领域",
        "copy_allowed": "yes",
        "authenticity_level_proposed": "L4",
        "relevance_grade_proposed": "core",
        "event_tags": ["1944改组前夜"],
        "person_tags": ["张澜", "中国民主政团同盟", "中国共产党"],
        "place_tags": ["延安"],
        "evidence_note": (
            "WebSearch 2026-07-19 核读：1944-02-22《解放日报》（延安版）发表长文"
            "专门介绍张澜《中国需要真正民主政治》小册子，誉之为民主运动的『冲锋号』。"
            "为中共对民盟组织与张澜立场公开背书的标志性事件。"
            "《解放日报》原刊版次与文章作者待寻延安革命纪念馆或 NLC 民国期刊库。"
        ),
        "evidence_type": "official_description",
        "evidence_locator": (
            "在线检索词来源：张澜纪念馆 http://www.zl1872.cn/zxxnewsview.aspx?producid=1397\n"
            "原文未取，待寻《解放日报》1944-02-22 版次"
        ),
        "uncertainty_note": (
            "《解放日报》1944-02-22 长文的版次、作者、文章标题未取得；"
            "升级 L1 需 NLC 民国期刊库 / 延安革命纪念馆 / 银川中共党史馆取原刊影像。"
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
                    "L4 国内官方背景站点（张澜纪念馆 / 民盟四川省委）+ 综合新闻 WebSearch 核读；"
                    "1943 民盟关键文献与事件的研究锚点；"
                    "原件（小册子、《国民参政会记录》、《解放日报》原刊等）"
                    "需 NLC / 二史馆 / 延安革命纪念馆取得后升 L1。"
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
