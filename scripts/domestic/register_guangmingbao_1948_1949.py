#!/usr/bin/env python3
"""Register the verified 1948-1949 Guangming Bao anchor scans and page-level leads."""

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
    {
        "archive_item": "NLC404-01J000514-10484",
        "volume": "1948年1卷1期",
        "date": "1948-03-01",
        "pages": 24,
        "filename": "NLC404-01J000514-10484_光明報_1948年1卷1期.pdf",
        "topics": ["民盟三中全会的成就", "略论民主同盟当前的任务", "坚持路线击破阴谋"],
        "event_tag": "1948五一口号",
        "issue_id": "v1n1",
        "article": "民盟三中全会的成就",
        "article_creator": "沈钧儒；《光明報》",
        "article_locator": "PDF第2页目录列于第4页；正文PDF第4页；work/domestic/guangmingbao_1948_1949/v1n1_pages/page-04.png；work/domestic/guangmingbao_1948_1949/v1n1_ocr/page-04.ocr.md",
        "article_note": "PDF第2页目录列出《民盟三中全会的成就》并署沈钧儒；PDF第4页版面大标题和右下署名均可见，第5页已转入《略论民主同盟当前的任务》。",
    },
    {
        "archive_item": "NLC404-01J000514-10514",
        "volume": "1948年1卷12期",
        "date": "1948-08-16",
        "pages": 20,
        "filename": "NLC404-01J000514-10514_光明報_1948年1卷12期.pdf",
        "topics": ["反對美國援蔣扶日", "民盟政治声明", "民族独立"],
        "event_tag": "1948五一口号",
        "issue_id": "v1n12",
        "article": "反對美國援蔣扶日",
        "article_creator": "《光明報》社",
        "article_locator": "PDF第2页标题与正文；work/domestic/guangmingbao_1948_1949/v1n12_pages/page-02.png；work/domestic/guangmingbao_1948_1949/v1n12_ocr/page-02.ocr.md",
        "article_note": "PDF第2页可视核到《反對美國援蔣扶日》标题与正文；第3页已转入《二個前提與五項原則》，因此当前文章页界为PDF第2页；OCR仅作定位辅助。",
    },
    {
        "archive_item": "NLC404-01J000514-10515",
        "volume": "1949年2卷1期",
        "date": "1949-01-10",
        "pages": 20,
        "filename": "NLC404-01J000514-10515_光明報_1949年2卷1期.pdf",
        "topics": ["新政协问题笔谈", "加强掠夺的币制改革", "民主人士笔谈"],
        "event_tag": "1949第一届政协",
        "issue_id": "v2n1",
        "article": "新政协问题笔谈",
        "article_creator": "《光明報》编辑部；罗子为、沈志远、马叙伦等",
        "article_locator": "本地首面目录与 PDF 第2页；文章正文连续页待逐页核读",
        "article_note": "首面目录列出《新政协问题笔谈》并列出10名投稿者；PDF第2页可见编者提出由新政协到成立民主联合政府、共同纲领和未来共同纲领等三项问题。",
    },
    {
        "archive_item": "NLC404-01J000514-72821",
        "volume": "1949年2卷12期",
        "date": "1949-02-12",
        "pages": 20,
        "filename": "NLC404-01J000514-72821_光明報_1949年2卷12期.pdf",
        "topics": ["我們對和平的態度", "談台灣解放問題", "追悼馮裕芳同志特輯"],
        "event_tag": "1949第一届政协",
        "issue_id": "v2n12",
        "article": "我們對和平的態度",
        "article_creator": "《光明報》社",
        "article_locator": "本地首面；PDF 第2页正文",
        "article_note": "首面列出《我們對和平的態度》《談台灣解放問題》和《追悼馮裕芳同志特輯》；PDF第2页正文回顾本盟三中全会以来的和平主张，并与1949年新政协/和平议题直接相连。出版日期由公开文章对该卷期的同期说明与报面卷期互证。",
    },
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def item_url(item: dict[str, object]) -> str:
    return "https://commons.wikimedia.org/wiki/File:" + str(item["archive_item"]) + "_光明報_" + str(item["volume"]) + ".pdf"


def source_record(item: dict[str, object]) -> dict[str, object]:
    path = SCAN_DIR / str(item["filename"])
    return {
        "source_id": f"domestic:source:nlc_guangmingbao_1948_1949_{item['issue_id']}",
        "source_name": f"《光明報》{item['volume']}国家图书馆原刊扫描",
        "institution": "中国国家图书馆数字化民国期刊；Wikimedia Commons公开镜像",
        "source_type": "同期政论报刊原刊整期扫描／国家图书馆数字化镜像",
        "authority_level": "国家图书馆原刊数字化扫描的公开镜像；不是原始馆藏系统直链",
        "official_url": "https://read.nlc.cn/",
        "record_or_search_url": item_url(item),
        "material_types": [f"《光明報》{item['volume']}整期原刊", *item["topics"]],
        "shanghai_relevance": "中；补充1948—1949年民盟及民主人士在香港出版物中的同期政治表达和新政协前后语境",
        "access_mode": "公开 PDF；Commons文件页提供原始下载入口",
        "rights_status": "public_domain_claimed_unknown",
        "verification_note": (
            f"已下载本地副本 {path.relative_to(ROOT)}，共{item['pages']}页；"
            f"SHA256为{sha256(path)}。首面完成可视核验，"
            f"PDF第2页及目录/正文完成定向核读；英文馆藏日期戳不作为出版日期，"
            f"出版日期以报面民国纪年和卷期记录为准。"
        ),
        "checked_at": "2026-07-19",
        "status": "verified_entry",
    }


def candidate_record(item: dict[str, object], article: bool = False) -> dict[str, object]:
    path = SCAN_DIR / str(item["filename"])
    title = str(item["article"] if article else f"《光明報》{item['volume']}（{item['date']}）")
    candidate_id = (
        f"domestic:NLC:guangmingbao-1948-1949-{item['issue_id']}-article"
        if article
        else f"domestic:NLC:guangmingbao-1948-1949-{item['issue_id']}"
    )
    note = str(item["article_note"] if article else (
        f"公开原刊扫描首面可视确认《光明報》{item['volume']}；"
        f"出版日期记录为{item['date']}，整期共{item['pages']}页。"
        f"本期目录/首面与第2页内容显示：" + "、".join(str(x) for x in item["topics"]) + "。"
    ))
    locator = str(item["article_locator"] if article else (
        f"{item['archive_item']}；本地PDF第1—2页；{path.relative_to(ROOT)}；"
        f"SHA256 {sha256(path)}"
    ))
    return {
        "candidate_id": candidate_id,
        "title": title,
        "creator": str(item["article_creator"] if article else "《光明報》社；北平全民報社"),
        "document_date": item["date"],
        "document_date_precision": "day",
        "document_type": "同期政论报刊文章／整期公开原刊影像" if article else "同期政论报刊原刊整期扫描",
        "repository_code": "NLC",
        "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
        "collection_name": "民国期刊／光明報",
        "archive_item": item["archive_item"],
        "catalog_reference": f"{item['archive_item']}；《光明報》{item['volume']}",
        "catalog_reference_status": "verified",
        "source_url": item_url(item),
        "source_url_role": "item_digital",
        "access_mode": "open",
        "access_note": f"公开{item['pages']}页PDF；本地副本：{path.relative_to(ROOT)}",
        "medium": "hybrid",
        "online_availability": "full_item_online",
        "rights_status": "unknown",
        "reuse_rights": "citation_only",
        "copy_allowed": "unknown",
        "authenticity_level_proposed": "L1",
        "relevance_grade_proposed": "core",
        "event_tags": [item["event_tag"]],
        "person_tags": ["中国民主同盟", "张澜", "沈钧儒"] if "1948" in str(item["date"]) else ["中国民主同盟", "沈钧儒", "马叙伦"],
        "place_tags": ["香港"],
        "evidence_note": note,
        "evidence_type": "digital_image",
        "evidence_locator": locator,
        "uncertainty_note": "原刊影像已保存并核验哈希；全文逐字转录、异体字规范化、作者署名与跨来源关系仍待完成。OCR仅作检索辅助，英文馆藏日期戳不作为出版日期。",
        "checked_at": "2026-07-19",
        "checked_by": "codex",
        "review_status": "needs_human_review",
        "review_note": "新增1948—1949连续卷期锚点；保持L1/needs_human_review，待逐页转录、人工复核和与1948三中全会/1949新政协材料互校。",
    }


def main() -> None:
    sources = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    source_ids = {row["source_id"] for row in sources}
    for item in ITEMS:
        row = source_record(item)
        if row["source_id"] not in source_ids:
            sources.append(row)
    SOURCE_PATH.write_text(json.dumps(sources, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    existing = {}
    with CANDIDATE_PATH.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                existing[row["candidate_id"]] = row
    for item in ITEMS:
        for article in (False, True):
            row = candidate_record(item, article=article)
            if item["issue_id"] in {"v1n1", "v1n12"} and article:
                existing[row["candidate_id"]] = row
            else:
                existing.setdefault(row["candidate_id"], row)
    CANDIDATE_PATH.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False, separators=(",", ":")) for row in existing.values()) + "\n",
        encoding="utf-8",
    )

    coverage = json.loads(COVERAGE_PATH.read_text(encoding="utf-8"))
    by_tag = {tag: row for row in coverage for tag in row.get("event_tags", [])}
    for item in ITEMS:
        for article in (False, True):
            row = candidate_record(item, article=article)
            event = by_tag[item["event_tag"]]
            if row["candidate_id"] not in event["domestic_candidate_ids"]:
                event["domestic_candidate_ids"].append(row["candidate_id"])
            event["domestic_status"] = "已补入1948—1949年《光明報》代表性原刊；逐页转录和大会档案互校仍待完成"
    COVERAGE_PATH.write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"sources": len(sources), "candidates": len(existing)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
