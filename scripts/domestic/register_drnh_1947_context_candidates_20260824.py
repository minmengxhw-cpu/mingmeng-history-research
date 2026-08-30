#!/usr/bin/env python3
"""Register verified DRNH catalogue leads for the 1947 pre-dissolution context.

This is a metadata-only registration pass.  It records the official catalogue
identity and public item URL, but never downloads, reads, OCRs, or promotes the
underlying archival body.  The records remain review leads until the item
image/page chain and rights are independently verified.
"""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "data/domestic/source_registry.json"
CANDIDATE_PATH = ROOT / "data/domestic/candidates.jsonl"
COVERAGE_PATH = ROOT / "data/domestic/event_coverage.json"


ITEMS = [
    {
        "candidate_id": "domestic:DRNH:002-080200-00541-008",
        "title": "保密局呈蔣中正民社黨對參加政府態度及民盟二中全會對共黨表不滿等情報提要四則",
        "creator": "保密局",
        "document_date": "1947-01-09",
        "document_type": "國史館官方目錄記錄／1947年民盟政治活動背景材料",
        "archive_file": "002-080200-00541-008",
        "catalog_reference": "002-080200-00541-008",
        "source_url": "https://ahonline.drnh.gov.tw/index.php?act=Archive%2Fsearch%2FeyJxdWVyeSI6W3siZmllbGQiOiJfYWxsIiwidmFsdWUiOiIwMDItMDgwMjAwLTAwNTQxLTAwOCJ9XX0%3D",
        "event_note": "官方题名明确提到民盟二中全会，是1947年政治活动和后续组织危机之间的前置记录。",
        "people": ["张君勱", "张澜", "张东荪", "伍宪子", "孙宝刚"],
        "places": ["上海", "南京", "延安"],
    },
    {
        "candidate_id": "domestic:DRNH:002-080200-00536-014",
        "title": "張鎮等呈蔣中正中共及民社等各黨派動態之情報提要等十四則",
        "creator": "张镇等",
        "document_date": "1947-05-07",
        "document_type": "國史館官方目錄記錄／1947年各黨派活動背景材料",
        "archive_file": "002-080200-00536-014",
        "catalog_reference": "002-080200-00536-014",
        "source_url": "https://ahonline.drnh.gov.tw/index.php?act=Archive%2Fsearch%2FeyJxdWVyeSI6W3siZmllbGQiOiJfYWxsIiwidmFsdWUiOiIwMDItMDgwMjAwLTAwNTM2LTAxNCJ9XX0%3D",
        "event_note": "官方记录列出民社等党派动态及张澜、黄炎培、张君勱等相关人物；作为政治环境交叉材料，不把目录中的相关人物等同于民盟专题正文。",
        "people": ["张澜", "黄炎培", "张君勱", "伍宪子", "徐傅霖"],
        "places": ["上海", "重庆", "南京"],
    },
    {
        "candidate_id": "domestic:DRNH:002-080200-00537-008",
        "title": "甘競生呈蔣中正廣西近情及意見民盟分子李任仁陳良佐與李濟琛互通聲氣等文電日報表",
        "creator": "甘竞生",
        "document_date": "1947-09-05",
        "document_type": "國史館官方目錄記錄／1947年地方民盟活動背景材料",
        "archive_file": "002-080200-00537-008",
        "catalog_reference": "002-080200-00537-008",
        "source_url": "https://ahonline.drnh.gov.tw/index.php?act=Archive%2Fsearch%2FeyJxdWVyeSI6W3siZmllbGQiOiJfYWxsIiwidmFsdWUiOiIwMDItMDgwMjAwLTAwNTM3LTAwOCJ9XX0%3D",
        "event_note": "官方题名直接提到广西民盟成员和地方政治关系，可补充全国组织史的地方维度；其情报性质可能带有形成机关的观察偏向。",
        "people": ["李任仁", "陈良佐", "李济琛"],
        "places": ["广西"],
    },
]


def candidate(item: dict[str, object]) -> dict[str, object]:
    archive_file = str(item["archive_file"])
    return {
        "candidate_id": item["candidate_id"],
        "title": item["title"],
        "creator": item["creator"],
        "document_date": item["document_date"],
        "document_date_precision": "day",
        "document_type": item["document_type"],
        "repository_code": "DRNH",
        "repository_name": "台湾国史馆檔案史料文物查詢系統",
        "collection_name": "蒋中正总统文物／特交档案／一般资料",
        "archive_fonds": "002 蔣中正總統文物",
        "archive_series": "002-080200",
        "archive_file": archive_file,
        "archive_item": f"drnh:{archive_file}",
        "catalog_reference": item["catalog_reference"],
        "catalog_reference_status": "verified",
        "source_url": item["source_url"],
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "国史馆官方目录页可定位具体件号并标示数字档在线阅览；本记录只登记目录身份，不读取或下载正文。",
        "medium": "digital",
        "online_availability": "surrogate_online",
        "rights_status": "unknown",
        "reuse_rights": "citation_only",
        "rights_basis": "国史馆开放、阅览和复制规定及具体件标示待核",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "related",
        "event_tags": ["1947民盟被宣布非法"],
        "person_tags": item["people"],
        "place_tags": item["places"],
        "evidence_note": (
            f"2026-08-24 经国史馆公开目录页核对档号、题名和日期；{item['event_note']} "
            "本条是官方目录候选，不是本地原件、页级影像或正文转录。"
        ),
        "evidence_type": "catalogue",
        "evidence_locator": str(item["source_url"]),
        "uncertainty_note": (
            "尚无本地文件、SHA256、页数或逐页人工核读；情报/报告类记录不能直接代表民盟自身立场，"
            "也不能替代1947-10-27政府公函或1947-11-06解散公告。"
        ),
        "checked_at": "2026-08-24",
        "checked_by": "codex",
        "review_status": "needs_human_review",
        "review_note": "官方目录身份已核；待授权影像、页界、权利和形成链复核后，才可决定是否进入 citation-ready 层。",
        "check_outcome": "needs_info",
    }


def main() -> int:
    sources = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    rows = {}
    for line in CANDIDATE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            record = json.loads(line)
            rows[record["candidate_id"]] = record

    added = []
    for item in ITEMS:
        record = candidate(item)
        if record["candidate_id"] not in rows:
            added.append(record["candidate_id"])
        rows[record["candidate_id"]] = record

    CANDIDATE_PATH.write_text(
        "\n".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) for record in rows.values()) + "\n",
        encoding="utf-8",
    )

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    event = next(row for row in coverage if row.get("event_id") == "domestic-1947-illegal-dissolution")
    for item in ITEMS:
        candidate_id = item["candidate_id"]
        if candidate_id not in event["domestic_candidate_ids"]:
            event["domestic_candidate_ids"].append(candidate_id)
    event["domestic_status"] = (
        "已补入1947年1月、5月、9月国史馆官方目录候选，补足解散前政治活动时间轴；"
        "这些记录仍是L2/needs_human_review，不替代1947-10-27政府公函、1947-11-06解散公告和原件页级转录"
    )
    COVERAGE_PATH.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({"added_candidates": added, "total_registered": len(rows), "body_read": False, "formal_db_written": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
