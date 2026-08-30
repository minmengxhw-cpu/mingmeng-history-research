#!/usr/bin/env python3
"""Register the newly verified 1944 民憲 volume 1 issue 10 scan."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data/domestic/press_scans/NLC404-00J001436-85451_民憲_第一卷第十期.pdf"
SOURCE_PATH = ROOT / "data/domestic/source_registry.json"
CANDIDATE_PATH = ROOT / "data/domestic/candidates.jsonl"
COVERAGE_PATH = ROOT / "data/domestic/event_coverage.json"

ARCHIVE_ITEM = "NLC404-00J001436-85451"
FILE_URL = "https://commons.wikimedia.org/wiki/File:NLC404-00J001436-85451_%E6%B0%91%E6%86%B2_1944%E2%80%931945%E5%B9%B4%E7%AC%AC%E4%B8%80%E5%8D%B7%E7%AC%AC%E5%8D%81%E6%9C%9F.pdf"
SHA256 = "7383f69dd74477969acf50708456b2975e167c16eaa3d6ed7deb6243616b6328"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    actual = sha256(PDF)
    if actual != SHA256:
        raise SystemExit(f"SHA256 mismatch: expected {SHA256}, got {actual}")

    source_id = "domestic:source:nlc_minxian_1944_v1n10"
    sources = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if not any(row.get("source_id") == source_id for row in sources):
        sources.append({
            "source_id": source_id,
            "source_name": "《民憲》1944年第一卷第十期国家图书馆原刊扫描",
            "institution": "中国国家图书馆数字化民国期刊；Wikimedia Commons公开镜像",
            "source_type": "同期政论刊物原刊整期扫描／国家图书馆数字化镜像",
            "authority_level": "国家图书馆原刊数字化扫描的公开镜像；不是原始馆藏系统直链",
            "official_url": "https://read.nlc.cn/",
            "record_or_search_url": FILE_URL,
            "material_types": ["《民憲》第一卷第十期", "民主政治", "1944年改组前后政治传播"],
            "shanghai_relevance": "中；补充1944年民盟改组前后重庆民主政论刊物的同期传播环境",
            "access_mode": "公开PDF；Commons文件页提供原始下载入口",
            "rights_status": "public_domain_claimed_unknown",
            "verification_note": (
                "已下载本地副本 data/domestic/press_scans/"
                "NLC404-00J001436-85451_民憲_第一卷第十期.pdf；共49页、未加密，"
                f"SHA256为{actual}。PDF第2页可视核定第一卷第十期、民国三十三年十二月二十日（1944-12-20）"
                "及目录；尚未将目录题名直接当作民盟正式文件。"
            ),
            "checked_at": "2026-07-19",
            "status": "verified_entry",
        })
    SOURCE_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    candidate_id = "domestic:NLC:minxian-v1n10-1944-12-20"
    candidate = {
        "candidate_id": candidate_id,
        "title": "《民憲》第一卷第十期",
        "creator": "左舜生主编／《民憲》编辑委员会",
        "document_date": "1944-12-20",
        "document_date_precision": "day",
        "document_type": "同期政论刊物原刊整期扫描",
        "repository_code": "NLC",
        "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
        "collection_name": "《民憲》第一卷",
        "archive_item": ARCHIVE_ITEM,
        "catalog_reference": ARCHIVE_ITEM,
        "catalog_reference_status": "verified",
        "source_url": FILE_URL,
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "公开49页PDF；本地副本：data/domestic/press_scans/NLC404-00J001436-85451_民憲_第一卷第十期.pdf",
        "medium": "hybrid",
        "online_availability": "full_item_online",
        "rights_status": "unknown",
        "reuse_rights": "citation_only",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L1",
        "relevance_grade_proposed": "related",
        "event_tags": ["1944改组更名"],
        "person_tags": ["左舜生", "张澜", "中国民主同盟"],
        "place_tags": ["重庆"],
        "evidence_note": (
            "PDF第2页目录可视核到第一卷第十期、民国三十三年十二月二十日；"
            "目录列有《威尔斯氏政治思想及其近作人权宣言》《论今日习气之由来及其教治法》、"
            "《民主与哲学》、巴黎光复后法国政情、麦克阿瑟和西南太平洋战场等同期政论题目。"
            "该期可作为1944年改组后政治传播环境的原刊材料，但不能替代民盟组织规程、政治报告或正式纲领原件。"
        ),
        "evidence_type": "digital_image",
        "evidence_locator": f"{ARCHIVE_ITEM}；本地PDF第1—2页；共49页；SHA256 {actual}",
        "uncertainty_note": "已核验刊名、卷期、日期、目录页和整期可访问性；具体文章正文、作者、页码和与民盟正式文件的直接关系仍待逐页转录。",
        "checked_at": "2026-07-19",
        "checked_by": "codex",
        "review_status": "needs_human_review",
        "review_note": "新增1944年同期政论刊物原刊；保持L1/needs_human_review，待逐篇转录并与1944年民盟改组文件互校。",
    }
    rows = {}
    for line in CANDIDATE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["candidate_id"]] = row
    rows.setdefault(candidate_id, candidate)
    CANDIDATE_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows.values()) + "\n",
        encoding="utf-8",
    )

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    for event in coverage:
        if "1944改组更名" in event.get("event_tags", []):
            ids = event.setdefault("domestic_candidate_ids", [])
            if candidate_id not in ids:
                ids.append(candidate_id)
            event["domestic_status"] = "已补入1944年《民憲》同期政论刊物原刊；民盟改组文件原件仍待互校"
    COVERAGE_PATH.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_id": source_id, "candidate_id": candidate_id, "sha256": actual}, ensure_ascii=False))


if __name__ == "__main__":
    main()
