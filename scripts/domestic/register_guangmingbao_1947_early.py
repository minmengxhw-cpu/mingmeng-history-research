#!/usr/bin/env python3
"""Register the newly acquired 1947 Guangming Bao issue scans.

Only whole-issue records are created in this pass.  The first page proves the
issue number and publication date; article-level records wait for page-by-page
transcription and boundary review.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_DIR = ROOT / "data" / "domestic" / "press_scans"
SOURCE_PATH = ROOT / "data" / "domestic" / "source_registry.json"
CANDIDATE_PATH = ROOT / "data" / "domestic" / "candidates.jsonl"
COVERAGE_PATH = ROOT / "data" / "domestic" / "event_coverage.json"


ITEMS = [
    ("NLC404-01J000514-72818", "新十二號", "1947-08-08", 16, "1947年12期", "目录列有民盟二中全会、反对美军暴行和国内局势等文章"),
    ("NLC404-01J000514-10453", "新十三號", "1947-08-18", 16, "1947年13期", "目录列有民盟二中全会、张澜主席开幕讲词和政治局势等文章"),
    ("NLC404-01J000514-10454", "新十四號", "1947-08-28", 20, "1947年14期", "目录列有民盟二中全会政治报告、民主运动和上海各党派活动等文章"),
    ("NLC404-01J000514-10455", "新十五號", "1947-09-08", 16, "1947年15期", "目录列有民盟任务、政协路线和民主运动等文章"),
    ("NLC404-01J000514-10456", "新十六—十七號", "1947-10-08", 17, "1947年16–17期", "封面实物标示新十七号；目录列有民盟政治主张、时局和民主运动等文章"),
    ("NLC404-01J000514-10457", "新十八號", "1947-10-18", 16, "1947年18期", "目录列有民盟南总主席彭泽民讲话、时局意见和民盟基层活动等文章"),
    ("NLC404-01J000514-10458", "新十九號", "1947-10-28", 16, "1947年19期", "目录列有《我们对于和平的态度》、民盟上海支部对学生运动的意见等文章"),
    ("NLC404-01J000514-10459", "新二十號", "1947-06-23", 16, "1947年20期", "封面目录列有国民党独裁派、和平老人和民主运动等文章；日期按封面实物登记，不能按期号推定为10月之后"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def filename(ident: str, volume: str) -> str:
    return f"{ident}_光明報_{volume}.pdf"


def item_url(ident: str, volume: str) -> str:
    return f"https://commons.wikimedia.org/wiki/File:{ident}_光明報_{volume}.pdf"


def main() -> None:
    sources = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    source_ids = {row["source_id"] for row in sources}
    existing = {
        row["candidate_id"]: row
        for row in (json.loads(line) for line in CANDIDATE_PATH.read_text(encoding="utf-8").splitlines() if line.strip())
    }
    added = []
    for ident, issue, date, pages, volume, topics in ITEMS:
        path = SCAN_DIR / filename(ident, volume)
        if not path.exists():
            raise SystemExit(f"missing scan: {path}")
        digest = sha256(path)
        source_id = f"domestic:source:nlc_guangmingbao_1947_{volume.replace('年', '_').replace('期', '')}"
        if source_id not in source_ids:
            sources.append({
                "source_id": source_id,
                "source_name": f"《光明報》{volume}国家图书馆原刊扫描",
                "institution": "中国国家图书馆数字化民国期刊；Wikimedia Commons公开镜像",
                "source_type": "同期政论报刊原刊整期扫描／国家图书馆数字化镜像",
                "authority_level": "国家图书馆原刊数字化扫描的公开镜像；不是原始馆藏系统直链",
                "official_url": "https://read.nlc.cn/",
                "record_or_search_url": item_url(ident, volume),
                "material_types": [f"《光明報》{volume}整期原刊", "民盟政治活动", "1947年国内民主运动语境"],
                "shanghai_relevance": "中；补充1947年民盟在非法化前的同期机关报和香港出版政治表达",
                "access_mode": "公开 PDF；Commons文件页提供原始下载入口",
                "rights_status": "public_domain_claimed_unknown",
                "verification_note": f"本地副本 {path.relative_to(ROOT)}；共{pages}页；SHA256 {digest}；首面已可视核对卷期和日期。",
                "checked_at": "2026-07-19",
                "status": "verified_entry",
            })
            source_ids.add(source_id)
        candidate_id = f"domestic:NLC:guangmingbao-1947-{volume.replace('年', '-').replace('期', '')}"
        existing[candidate_id] = {
            "candidate_id": candidate_id,
            "title": f"《光明報》{issue}（{date}）",
            "creator": "《光明報》社；北平全民報社",
            "document_date": date,
            "document_date_precision": "day",
            "document_type": "同期政论报刊原刊整期扫描",
            "repository_code": "NLC",
            "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
            "collection_name": "民国期刊／光明報",
            "archive_item": ident,
            "catalog_reference": f"{ident}；《光明報》{issue}",
            "catalog_reference_status": "verified",
            "source_url": item_url(ident, volume),
            "source_url_role": "item_digital",
            "access_mode": "open",
            "access_note": f"公开{pages}页PDF；本地副本：{path.relative_to(ROOT)}",
            "medium": "hybrid",
            "online_availability": "full_item_online",
            "rights_status": "unknown",
            "reuse_rights": "citation_only",
            "copy_allowed": "unknown",
            "authenticity_level_proposed": "L1",
            "relevance_grade_proposed": "core",
            "event_tags": ["1947民盟被宣布非法"],
            "person_tags": ["中国民主同盟", "张澜", "沈钧儒", "罗隆基"],
            "place_tags": ["香港", "上海"],
            "evidence_note": f"首面可视确认《光明報》{issue}、日期{date}、馆藏号{ident}；目录显示{topics}。当前只登记整期，不预先猜测文章页界。",
            "evidence_type": "digital_image",
            "evidence_locator": f"{ident}；本地PDF第1页；{path.relative_to(ROOT)}；共{pages}页；SHA256 {digest}",
            "uncertainty_note": "首面卷期和日期已核验；全文逐字转录、目录文章页码、形成者细化、跨来源关系和复制权利仍待完成。",
            "checked_at": "2026-07-19",
            "checked_by": "codex",
            "review_status": "needs_human_review",
            "review_note": "新增1947年非法化前连续期号原刊；保持L1/needs_human_review，待逐页转录和文章级拆分，不替代内政部公函或民盟解散公告。",
        }
        added.append(candidate_id)
    SOURCE_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CANDIDATE_PATH.write_text("\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in existing.values()) + "\n", encoding="utf-8")

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    event = next(row for row in coverage if "1947民盟被宣布非法" in row.get("event_tags", []))
    for candidate_id in added:
        if candidate_id not in event["domestic_candidate_ids"]:
            event["domestic_candidate_ids"].append(candidate_id)
    event["domestic_status"] = "已补入1947年8—10月《光明報》连续原刊；10月27日公函、11月解散公告和文章级转录仍待完成"
    COVERAGE_PATH.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"added_candidates": added, "sources": len(sources), "candidates": len(existing)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
