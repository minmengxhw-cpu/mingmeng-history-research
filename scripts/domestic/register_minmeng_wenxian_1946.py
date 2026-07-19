#!/usr/bin/env python3
"""Register the 1946 contemporaneous Minmeng headquarters document compilation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "data/domestic/sourcebooks/NLC416-01jh004281-12557_民主同盟文獻_1946.pdf"
SOURCE_PATH = ROOT / "data/domestic/source_registry.json"
CANDIDATE_PATH = ROOT / "data/domestic/candidates.jsonl"
COVERAGE_PATH = ROOT / "data/domestic/event_coverage.json"

ARCHIVE_ITEM = "NLC416-01jh004281-12557"
FILE_URL = "https://commons.wikimedia.org/wiki/File:NLC416-01jh004281-12557_%E6%B0%91%E4%B8%BB%E5%90%8C%E7%9B%9F%E6%96%87%E7%8D%BB.pdf"
SHA256 = "276a82242c445bd7d6ca468f9022090922e0c2c243054e0e5af4353a1456e43f"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def base_candidate(candidate_id: str, title: str, date: str, note: str, locator: str, tags: list[str], *, article: bool = False) -> dict[str, object]:
    if candidate_id.endswith("formation-declaration"):
        locator += (
            "；work/domestic/minmeng_wenxian_1946/formation_9_13_images/page-009.png至page-011.png；"
            "work/domestic/minmeng_wenxian_1946/formation_9_13_ocr/page-009.ocr.md至page-011.ocr.md"
        )
    elif candidate_id.endswith("ten-program"):
        locator += (
            "；work/domestic/minmeng_wenxian_1946/formation_9_13_images/page-012.png至page-013.png；"
            "work/domestic/minmeng_wenxian_1946/formation_9_13_ocr/page-012.ocr.md至page-013.ocr.md"
        )
    return {
        "candidate_id": candidate_id,
        "title": title,
        "creator": "中国民主同盟总部编印" if not article else "中国民主同盟总部编印；原文件形成者待从原件互校",
        "document_date": date,
        "document_date_precision": "day",
        "document_type": "1946年官方文献汇编中的同期文件" if article else "1946年民盟总部官方文献汇编",
        "repository_code": "NLC",
        "repository_name": "中国国家图书馆数字化民国图书（Wikimedia Commons镜像）",
        "collection_name": "《民主同盟文獻》",
        "archive_item": ARCHIVE_ITEM,
        "catalog_reference": f"{ARCHIVE_ITEM}；《民主同盟文獻》",
        "catalog_reference_status": "verified",
        "source_url": FILE_URL,
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": "公开176页PDF；本地副本：data/domestic/sourcebooks/NLC416-01jh004281-12557_民主同盟文獻_1946.pdf",
        "medium": "hybrid",
        "online_availability": "full_item_online",
        "rights_status": "unknown",
        "reuse_rights": "citation_only",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L2",
        "relevance_grade_proposed": "core" if article else "related",
        "event_tags": tags,
        "person_tags": ["中国民主同盟", "张澜", "沈钧儒"],
        "place_tags": ["香港", "重庆"],
        "evidence_note": note,
        "evidence_type": "digital_image",
        "evidence_locator": f"{locator}；PDF共176页；SHA256 {SHA256}",
        "uncertainty_note": "这是1946年民盟总部编印的官方文献汇编扫描，不是1941年成立宣言或十大纲领的单独原始印本；原文件形成机关、原始版次、底本关系和复制权利仍需互校。OCR只作定位辅助。",
        "checked_at": "2026-07-19",
        "checked_by": "codex",
        "review_status": "needs_human_review",
        "review_note": "按L2同期官方汇编登记；待逐字转录、页码和底本关系核对，不自动升级为L1或accepted。",
    }


def main() -> None:
    actual = sha256(PDF)
    if actual != SHA256:
        raise SystemExit(f"SHA256 mismatch: expected {SHA256}, got {actual}")

    source_id = "domestic:source:nlc_minmeng_documents_1946"
    sources = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    if not any(row.get("source_id") == source_id for row in sources):
        sources.append({
            "source_id": source_id,
            "source_name": "《民主同盟文獻》（1946）民盟总部编印公开扫描",
            "institution": "中国国家图书馆数字化民国图书；中国民主同盟总部编印；Wikimedia Commons公开镜像",
            "source_type": "1946年官方文献汇编／同期文件汇编扫描",
            "authority_level": "民盟总部同期编印的官方汇编公开扫描；不是单件原始印本的直链",
            "official_url": "https://read.nlc.cn/",
            "record_or_search_url": FILE_URL,
            "material_types": ["1941成立宣言", "1941对时局主张纲领", "1944改组相关文件", "1945大会文件"],
            "shanghai_relevance": "高；补充1941—1945民盟总部同期官方文献汇编，供原刊/原件追索和页码互校",
            "access_mode": "公开PDF；Commons文件页提供原始下载入口",
            "rights_status": "public_domain_claimed_unknown",
            "verification_note": (
                "已下载本地副本 data/domestic/sourcebooks/"
                "NLC416-01jh004281-12557_民主同盟文獻_1946.pdf；176页、未加密，"
                f"SHA256为{actual}。PDF第2页书名页标明中国民主同盟总部编印、中华民国三十五年十二月；"
                "第5—8页目录，第9页起进入文件正文。"
            ),
            "checked_at": "2026-07-19",
            "status": "verified_entry",
        })
    SOURCE_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    rows = {}
    for line in CANDIDATE_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip():
            row = json.loads(line)
            rows[row["candidate_id"]] = row

    candidates = [
        base_candidate(
            "domestic:NLC:minmeng-wenxian-1946-whole",
            "《民主同盟文獻》",
            "1946-12-01",
            "PDF第2页书名页明确为中国民主同盟总部编印、中华民国三十五年十二月；目录列出1941成立宣言、1941对时局主张纲领、1944民主同盟纲领、1945代表大会政治报告和宣言等42件文件。作为1946年官方汇编整体登记，不能替代各件原始印本。",
            "PDF第2页书名页；第5—8页目录；整本176页",
            ["1941成立", "1944改组更名", "1945第一次全国代表大会"],
        ),
        base_candidate(
            "domestic:NLC:minmeng-wenxian-1946-formation-declaration",
            "中国民主政团同盟成立宣言",
            "1941-10-10",
            "PDF第9页正文标题明确为《中国民主政团同盟成立宣言》，题下注明中华民国三十年十月十日；正文连续至PDF第11页。该记录来自1946年民盟总部官方汇编，需与1941-10-10《光明报》原刊互校。",
            "PDF第9—11页；印刷页1—3；目录PDF第5页",
            ["1941成立"],
            article=True,
        ),
        base_candidate(
            "domestic:NLC:minmeng-wenxian-1946-ten-program",
            "中国民主政团同盟对时局主张纲领",
            "1941-10-10",
            "PDF第12页正文标题明确为《中国民主政团同盟对时局主张纲领》，题下注明中华民国三十年十月十日；正文延续至PDF第13页。该记录保存十项主张的同期官方汇编页级入口，不能替代1941年原刊或原始印本。",
            "PDF第12—13页；印刷页1—2；目录PDF第5页",
            ["1941成立"],
            article=True,
        ),
        base_candidate(
            "domestic:NLC:minmeng-wenxian-1946-final-war-political-platform",
            "中国民主同盟对抗战最后阶段的政治主张",
            "1944-10-10",
            "PDF第22页正文标题明确为《对抗战最后阶段的政治主张》，题下注明中华民国三十三年十月十日；正文连续至PDF第25页，内容包含军队国家化、民主政治、宪政、财政外交和教育等主张。该记录来自1946年民盟总部官方汇编，需与1944年同期报刊或独立印本互校。",
            "PDF第22—25页；印刷页14—17；目录PDF第5页",
            ["1944改组更名"],
            article=True,
        ),
        base_candidate(
            "domestic:NLC:minmeng-wenxian-1946-situation-declaration-1945-01-15",
            "时局宣言",
            "1945-01-15",
            "PDF第26页正文标题为《时局宣言》，题下注明中华民国三十四年一月十五日；正文连续至PDF第29页，属于民盟总部同期文献汇编中的公开定位。原始发表载体和独立印本仍需追查。",
            "PDF第26—29页；印刷页18起至下一件文件前；目录PDF第5页",
            ["1945第一次全国代表大会"],
            article=True,
        ),
        base_candidate(
            "domestic:NLC:minmeng-wenxian-1946-minmeng-platform-1945",
            "中国民主同盟纲领",
            "1945-10",
            "PDF第48页正文标题明确为《中国民主同盟纲领》，题下注明“民国三十四年十月临时全国代表大会通过”；正文连续至PDF第72页，覆盖政治、经济、教育、妇女等章节。目录页5—6将其列为1945年10月文件，但正文未给出可确认的具体日，故保留月精度。该记录来自1946年官方汇编，不替代1945年临时全国代表大会原始印本。",
            "PDF第48—72页；印刷页40—64；目录PDF第6页",
            ["1945第一次全国代表大会"],
            article=True,
        ),
        base_candidate(
            "domestic:NLC:minmeng-wenxian-1946-congress-declaration-1945-10-16",
            "中国民主同盟临时全国代表大会宣言",
            "1945-10-16",
            "PDF第73页页首标题明确为《中国民主同盟临时全国代表大会宣言》，题下注明中华民国三十四年十月十六日；正文连续至PDF第78页，PDF第79页起进入下一件1945-12-06昆明惨案文件。该记录来自1946年官方汇编，不替代1945年临时全国代表大会原始印本。",
            "PDF第73—78页；印刷页65—70；目录PDF第6页",
            ["1945第一次全国代表大会"],
            article=True,
        ),
    ]
    candidates[0]["document_date_precision"] = "month"
    candidates[0]["document_date"] = "1946-12"
    candidates[5]["document_date_precision"] = "month"
    for row in candidates:
        rows[row["candidate_id"]] = row
    CANDIDATE_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in rows.values()) + "\n",
        encoding="utf-8",
    )

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    by_tag = {tag: event for event in coverage for tag in event.get("event_tags", [])}
    for row in candidates:
        for tag in row["event_tags"]:
            event = by_tag.get(tag)
            if event is not None:
                ids = event.setdefault("domestic_candidate_ids", [])
                if row["candidate_id"] not in ids:
                    ids.append(row["candidate_id"])
                event["domestic_status"] = "已补入1946年民盟总部官方文献汇编；原刊/原件互校仍待完成"
    COVERAGE_PATH.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"source_id": source_id, "added_candidates": [row["candidate_id"] for row in candidates]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
