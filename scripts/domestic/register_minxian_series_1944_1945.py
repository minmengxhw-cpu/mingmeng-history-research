#!/usr/bin/env python3
"""Register the locally verified NLC 民憲 issue scans and the remaining lead."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parents[2]
SOURCE_PATH = ROOT / "data/domestic/source_registry.json"
CANDIDATE_PATH = ROOT / "data/domestic/candidates.jsonl"
COVERAGE_PATH = ROOT / "data/domestic/event_coverage.json"

ITEMS = [
    # archive item, issue label, date, pages, sha256, event tag
    ("85443", "第一卷第二期", "1944-05-01", 47, "43c91c806af550c60d321793a81cc18bc7866774057f318e364915c70f543118", "1944改组更名"),
    ("85444", "第一卷第三期", "1944-06-15", 41, "c21e3e8464473cf68cafdda3e65d69e32fb2bce986f88aa9593479150c612618", "1944改组更名"),
    ("85445", "第一卷第四期", "1944-06-30", 47, "c88a363f01432f1494adcde3f44c736414deeed2d528fbf550b37a5881f7f730", "1944改组更名"),
    ("85446", "第一卷第五期", "1944-07-16", 53, "25d339490905fc06832f4ddbaf7a367d761ef06e0b40f8439c6c1a8c8d6fd69a", "1944改组更名"),
    ("85448", "第一卷第七期", "1944-09-10", 51, "a1e2269150fea87cfcca1e2016662ecc953f9a9b2a151184aad62fad776f09e0", "1944改组更名"),
    ("85449", "第一卷第八期", "1944-10-12", 55, "867fcca3821c8cc3deb67ba1aae6a76e62f192c0c849805fa2fda4cc9835aa19", "1944改组更名"),
    ("85452", "第一卷第十一期", "1945-01-15", 51, "71edf42b8f1e532edb277c2899f2a9a548f531a1cd76c6f7b79a69b1fdce0d2e", "1945民盟一大"),
    ("85453", "第一卷第十二期", "1945-02-25", 45, "bd753ca717908b0556e04dad0fa18519830a8cd3470d25eafbceae17f3c6fe4a", "1945民盟一大"),
    ("85454", "第二卷第一期", "1945-05-15", 71, "ea8481761246aa26c98f9a7a058e894597c551798fb5ad37f30c400a4cb34fcd", "1945民盟一大"),
    ("85455", "第二卷第二期", "1945-06-13", 45, "449086e77f910796d78a924782cc7cfc830e2a77b0df62c04e6c0fb209cfb7de", "1945民盟一大"),
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def file_url(archive_item: str, issue_label: str) -> str:
    filename = f"NLC404-00J001436-{archive_item}_民憲_1944–1945年{issue_label}.pdf"
    return "https://commons.wikimedia.org/wiki/File:" + quote(filename, safe=":")


def local_pdf(archive_item: str, issue_label: str) -> Path:
    return ROOT / f"data/domestic/press_scans/NLC404-00J001436-{archive_item}_民憲_{issue_label}.pdf"


def add_lead_source(sources: list[dict]) -> None:
    archive_item = "85456"
    issue_label = "第二卷第三期"
    source_id = "domestic:source:nlc_minxian_1945_v2n3_lead"
    if any(row.get("source_id") == source_id for row in sources):
        return
    url = file_url(archive_item, issue_label)
    sources.append({
        "source_id": source_id,
        "source_name": "《民憲》1945年第二卷第三期国家图书馆原刊扫描获取线索",
        "institution": "中国国家图书馆数字化民国期刊；Wikimedia Commons公开镜像",
        "source_type": "同期政论刊物原刊整期扫描获取线索",
        "authority_level": "国家图书馆原刊数字化扫描的公开镜像；不是原始馆藏系统直链",
        "official_url": "https://read.nlc.cn/",
        "record_or_search_url": url,
        "material_types": ["《民憲》第二卷第三期", "1945年民盟一大前后政治传播"],
        "shanghai_relevance": "中；补充1945年民盟一大前后重庆民主政论刊物的同期传播环境",
        "access_mode": "公开文件页可定位；本轮下载受到Commons HTTP 429限流，待冷却后重试",
        "rights_status": "public_domain_claimed_unknown",
        "verification_note": "Commons分类页可定位NLC404-00J001436-85456；本轮下载请求返回HTTP 429，未将未取得文件登记为候选或已验证扫描。",
        "checked_at": "2026-07-19",
        "status": "lead_only",
    })


def main() -> None:
    sources = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    rows = {}
    for line in CANDIDATE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["candidate_id"]] = row

    registered = []
    for archive_item, issue_label, date, pages, expected_sha, event_tag in ITEMS:
        pdf = local_pdf(archive_item, issue_label)
        if not pdf.exists():
            raise SystemExit(f"missing local scan: {pdf}")
        actual_sha = sha256(pdf)
        if actual_sha != expected_sha:
            raise SystemExit(f"SHA256 mismatch for {pdf.name}: expected {expected_sha}, got {actual_sha}")

        source_id = f"domestic:source:nlc_minxian_{archive_item}"
        url = file_url(archive_item, issue_label)
        if not any(row.get("source_id") == source_id for row in sources):
            sources.append({
                "source_id": source_id,
                "source_name": f"《民憲》{date[:4]}年{issue_label}国家图书馆原刊扫描",
                "institution": "中国国家图书馆数字化民国期刊；Wikimedia Commons公开镜像",
                "source_type": "同期政论刊物原刊整期扫描／国家图书馆数字化镜像",
                "authority_level": "国家图书馆原刊数字化扫描的公开镜像；不是原始馆藏系统直链",
                "official_url": "https://read.nlc.cn/",
                "record_or_search_url": url,
                "material_types": [f"《民憲》{issue_label}", "1944—1945年民盟改组及一大前后政治传播"],
                "shanghai_relevance": "中；补充重庆民主政论刊物的同期传播环境",
                "access_mode": f"公开PDF；本地副本：data/domestic/press_scans/{pdf.name}",
                "rights_status": "public_domain_claimed_unknown",
                "verification_note": (
                    f"已下载本地副本；共{pages}页、未加密，SHA256为{actual_sha}。"
                    f"PDF第2页可视核定《民憲》{issue_label}及{date}出版日；目录仅作为整期内容导航，"
                    "不把目录题名直接当作民盟正式文件。"
                ),
                "checked_at": "2026-07-19",
                "status": "verified_entry",
            })

        candidate_id = f"domestic:NLC:minxian-{archive_item}-{date}"
        rows.setdefault(candidate_id, {
            "candidate_id": candidate_id,
            "title": f"《民憲》{issue_label}",
            "creator": "左舜生主编／《民憲》编辑委员会",
            "document_date": date,
            "document_date_precision": "day",
            "document_type": "同期政论刊物原刊整期扫描",
            "repository_code": "NLC",
            "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
            "collection_name": "《民憲》",
            "archive_item": f"NLC404-00J001436-{archive_item}",
            "catalog_reference": f"NLC404-00J001436-{archive_item}",
            "catalog_reference_status": "verified",
            "source_url": url,
            "source_url_role": "item_digital",
            "access_mode": "open",
            "access_note": f"公开{pages}页PDF；本地副本：data/domestic/press_scans/{pdf.name}",
            "medium": "hybrid",
            "online_availability": "full_item_online",
            "rights_status": "unknown",
            "reuse_rights": "citation_only",
            "rights_basis": "Wikimedia页面与国家图书馆数字副本具体再利用规则待核",
            "copy_allowed": "unknown",
            "authenticity_level_proposed": "L1",
            "relevance_grade_proposed": "related",
            "event_tags": [event_tag],
            "person_tags": ["左舜生", "张澜", "中国民主同盟"],
            "place_tags": ["重庆"],
            "evidence_note": (
                f"PDF第2页目录可视核到《民憲》{issue_label}及{date}出版日；"
                "本候选代表可复查的同期政论刊物整期影像，用于观察民盟改组或一大前后的政治传播环境。"
                "它不是民盟组织规程、政治报告、会议记录或正式公告原件。"
            ),
            "evidence_type": "digital_image",
            "evidence_locator": f"NLC404-00J001436-{archive_item}；本地PDF第1—2页封面/目录；整期共{pages}页；SHA256 {actual_sha}",
            "uncertainty_note": "已核验刊名、卷期、日期、目录页和整期可访问性；具体文章正文、作者、页码及与民盟正式文件的直接关系仍待逐页转录。",
            "checked_at": "2026-07-19",
            "checked_by": "codex",
            "review_status": "needs_human_review",
            "review_note": "已取得同期原刊整期扫描；保持L1/needs_human_review，待逐篇转录、建立文章级页码定位并与民盟正式文件互校。",
        })
        registered.append(candidate_id)

    add_lead_source(sources)
    SOURCE_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    CANDIDATE_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows.values()) + "\n",
        encoding="utf-8",
    )

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    by_tag = {item[5]: [] for item in ITEMS}
    for archive_item, issue_label, date, pages, expected_sha, event_tag in ITEMS:
        by_tag[event_tag].append(f"domestic:NLC:minxian-{archive_item}-{date}")
    for event in coverage:
        for tag, ids in by_tag.items():
            if tag in event.get("event_tags", []):
                target = event.setdefault("domestic_candidate_ids", [])
                for candidate_id in ids:
                    if candidate_id not in target:
                        target.append(candidate_id)
                event["domestic_status"] = "已补入《民憲》连续期同期原刊扫描；民盟正式组织文件仍需原件互校"
    COVERAGE_PATH.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"registered": registered, "lead": "NLC404-00J001436-85456", "sources": len(sources), "candidates": len(rows)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
