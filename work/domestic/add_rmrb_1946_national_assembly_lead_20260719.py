#!/usr/bin/env python3
"""Add one directly inspected 1946 newspaper transcription as a review-held record."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "data/domestic/source_registry.json"
CANDIDATES = ROOT / "data/domestic/candidates.jsonl"

SOURCE_ID = "domestic:source:rmrb_digital_transcription_1946_11_19"
CANDIDATE_ID = "domestic:RMrb:1946-11-19-national-assembly-boycott"

source = {
    "source_id": SOURCE_ID,
    "source_name": "《人民日报》1946年11月19日第1版公开数字转录",
    "institution": "公开数据查询平台；页面标注人民日报历史版面档案",
    "source_type": "同期报刊数字转录／版面索引入口",
    "authority_level": "同期报刊文本的公开数字替身；不是《人民日报》原报面影像",
    "official_url": "https://cn.govopendata.com/renminribao/1946/11/19/1/",
    "record_or_search_url": "https://cn.govopendata.com/renminribao/1946/11/",
    "material_types": ["1946年11月19日《人民日报》第1版", "制宪国民大会开幕后的同期报道", "中共和其他民主党派拒绝出席的数字转录"],
    "shanghai_relevance": "中；用于1946年11月国大开幕后的同期舆论交叉核验，并为《民主报》同日或相邻期号原刊申请提供关键词",
    "access_mode": "公开网页可直接阅读按版面组织的文字转录；原报面影像和正式数据库记录仍需追查",
    "rights_status": "unknown",
    "verification_note": "已直接访问1946-11-19第1版页面；页面正文记录南京国民大会于11月15日开幕，并写明中国共产党及其他民主党派拒绝出席。该页面提供同期文本和日期/版面入口，不提供原报面扫描，不能替代《人民日报》原版或官方报刊数据库影像。",
    "checked_at": "2026-07-19",
    "status": "verified_entry",
}

candidate = {
    "candidate_id": CANDIDATE_ID,
    "title": "《人民日报》1946年11月19日第1版：国民大会开幕后中共和其他民主党派拒绝出席的报道",
    "creator": "新华社；《人民日报》",
    "document_date": "1946-11-19",
    "document_date_precision": "day",
    "document_type": "同期报刊数字转录／版面替身",
    "repository_code": "RMrb",
    "repository_name": "《人民日报》历史版面公开数字转录入口",
    "collection_name": "人民日报1946年11月第1版",
    "archive_fonds": None,
    "archive_series": None,
    "archive_file": None,
    "archive_item": "1946-11-19 第1版",
    "catalog_reference": "公开数字版 URL；1946-11-19 第1版",
    "catalog_reference_status": "verified",
    "source_url": "https://cn.govopendata.com/renminribao/1946/11/19/1/",
    "source_url_role": "item_surrogate",
    "access_mode": "open",
    "access_note": "公开网页可直接阅读按版面组织的文字转录；当前未发现对应原报面扫描或官方影像下载入口",
    "medium": "digital",
    "online_availability": "surrogate_online",
    "rights_status": "unknown",
    "reuse_rights": "citation_only",
    "rights_basis": "页面平台条款与《人民日报》原刊权利待核",
    "copy_allowed": "unknown",
    "authenticity_level_proposed": "L2",
    "relevance_grade_proposed": "core",
    "event_tags": ["1946拒绝国民大会"],
    "person_tags": ["中国民主同盟", "中国共产党"],
    "place_tags": ["南京"],
    "evidence_note": "页面明确标示1946年11月19日《人民日报》第1版；正文报道11月15日南京国民大会开幕，并记载中共和其他民主党派拒绝出席。它是事件发生后的同期文本转录，可补充拒绝参会后的公共报道链条。",
    "evidence_type": "secondary_lead",
    "evidence_locator": "公开数字版页面；1946-11-19第1版标题、日期和正文",
    "uncertainty_note": "取得的是公开网站文字转录，不是《人民日报》原报面扫描；版面位置、转录准确性、原刊字形和版权链仍待官方数据库或纸本影印复核。",
    "checked_at": "2026-07-19",
    "checked_by": "codex",
    "review_status": "needs_human_review",
    "review_note": "作为L2同期数字转录纳入1946拒绝国民大会事件覆盖；待追查人民日报官方历史数据库、国家图书馆或高校民国报刊影像后再决定是否升级。",
}

registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
if not any(item.get("source_id") == SOURCE_ID for item in registry):
    registry.append(source)
    REGISTRY.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

existing = set()
with CANDIDATES.open(encoding="utf-8") as fh:
    for line in fh:
        if line.strip():
            existing.add(json.loads(line)["candidate_id"])
if CANDIDATE_ID not in existing:
    with CANDIDATES.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")) + "\n")

print(json.dumps({"source_added": SOURCE_ID not in existing, "candidate_id": CANDIDATE_ID}, ensure_ascii=False))
