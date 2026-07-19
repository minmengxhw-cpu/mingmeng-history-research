#!/usr/bin/env python3
"""Register representative original scans of 民憲 and create issue-level candidates."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
registry_path = root / "data/domestic/source_registry.json"
candidates_path = root / "data/domestic/candidates.jsonl"
source_id = "domestic:source:nlc_minxian_1944_representative_scans"

source = {
    "source_id": source_id,
    "source_name": "《民憲》1944年第一卷第一、六、九期国家图书馆原刊扫描",
    "institution": "中国国家图书馆数字化民国期刊；Wikimedia Commons公开镜像",
    "source_type": "同期政论刊物原刊整期扫描／国家图书馆数字化镜像",
    "authority_level": "国家图书馆原刊数字化扫描的公开镜像；不是原始馆藏系统直链",
    "official_url": "https://read.nlc.cn/",
    "record_or_search_url": "https://commons.wikimedia.org/wiki/Category:民憲",
    "material_types": [
        "《民憲》第一卷第一期（1944-05-16）",
        "《民憲》第一卷第六期（1944-08-15）",
        "《民憲》第一卷第九期（1944-11-20）",
        "1944年民主宪政讨论与民盟改组前后传播材料",
    ],
    "shanghai_relevance": "中；作为1944年民盟改组前后同期政治传播和刊物网络的原刊对照，补足正式汇编之外的传播载体",
    "access_mode": "公开 PDF；Commons 分类页和文件页提供原始下载入口",
    "rights_status": "public_domain_claimed_unknown",
    "verification_note": "已下载三期公开 PDF：第一卷第一期47页、第一卷第六期51页、第一卷第九期51页，均未加密；三期封面/目录页分别明确标出1944-05-16、1944-08-15、1944-11-20，并可见同期政治、宪政和民主论题。已完成目录页核读，正文逐篇转录和具体文件出处仍待继续，故按整期原刊来源登记、候选保持人工复核。文件哈希和页级记录见 docs/domestic/press_scan_manifest.md 与 work/domestic/nlc_minxian_1944_representative_scans_review_20260719.md。",
    "checked_at": "2026-07-19",
    "status": "verified_entry",
}

issues = [
    {
        "candidate_id": "domestic:NLC:minxian-v1n1-1944-05-16",
        "title": "《民憲》第一卷第一期",
        "date": "1944-05-16",
        "pages": 47,
        "item": "NLC404-00J001436-85442",
        "file": "data/domestic/press_scans/NLC404-00J001436-85442_民憲_第一卷第一期.pdf",
        "sha": "528aa1c147c3ef5ae7af19790cc61b7fe3b261fd3f4afed0cb75b7e58dacbdad",
        "url": "https://commons.wikimedia.org/wiki/File:NLC404-00J001436-85442_%E6%B0%91%E6%86%B2_1944%E2%80%931945%E5%B9%B4%E7%AC%AC%E4%B8%80%E5%8D%B7%E7%AC%AC%E4%B8%80%E6%9C%9F.pdf",
        "event": "1944改组更名",
        "note": "PDF第2页目录页明确刊名、卷期和1944-05-16出版日；目录列出民主要政治、民主与党、改革会稿等同期论题。该期为民盟改组前的第三方面政论传播材料。",
    },
    {
        "candidate_id": "domestic:NLC:minxian-v1n6-1944-08-15",
        "title": "《民憲》第一卷第六期",
        "date": "1944-08-15",
        "pages": 51,
        "item": "NLC404-00J001436-85447",
        "file": "data/domestic/press_scans/NLC404-00J001436-85447_民憲_第一卷第六期.pdf",
        "sha": "680b592ba16a2826f23b46a382ca261f4183523293f82d568f6e6c5b5b6e503c",
        "url": "https://commons.wikimedia.org/wiki/File:NLC404-00J001436-85447_%E6%B0%91%E6%86%B2_1944%E2%80%931945%E5%B9%B4%E7%AC%AC%E4%B8%80%E5%8D%B7%E7%AC%AC%E5%85%AD%E6%9C%9F.pdf",
        "event": "1944改组更名",
        "note": "PDF第2页目录页明确刊名、卷期和1944-08-15出版日；目录列出联合法团中的政治真义、民主政治的哲学问题等栏目。该期处于1944年改组前夕，可用于对照改组议题的同期公共论述。",
    },
    {
        "candidate_id": "domestic:NLC:minxian-v1n9-1944-11-20",
        "title": "《民憲》第一卷第九期",
        "date": "1944-11-20",
        "pages": 51,
        "item": "NLC404-00J001436-85450",
        "file": "data/domestic/press_scans/NLC404-00J001436-85450_民憲_第一卷第九期.pdf",
        "sha": "b6e123c4d90e4b2b596a61e70758f3d0be22cbfbf63ee6ac7853f682de62d5df",
        "url": "https://commons.wikimedia.org/wiki/File:NLC404-00J001436-85450_%E6%B0%91%E6%86%B2_1944%E2%80%931945%E5%B9%B4%E7%AC%AC%E4%B8%80%E5%8D%B7%E7%AC%AC%E4%B9%9D%E6%9C%9F.pdf",
        "event": "1944改组更名",
        "note": "PDF第2页目录页明确刊名、卷期、1944-11-20出版日及馆藏页印记；目录列出民主政治与非民主政治、民主要政治等栏目。该期位于1944-09改组和1944-10政治主张发表之后，可作为改组后政治传播的同期原刊。",
    },
]

article = {
    "candidate_id": "domestic:NLC:minxian-v1n9-democracy-vs-nondemocracy-1944-11-20",
    "title": "民主政治與非民主政治",
    "creator": "陳啟天",
    "document_date": "1944-11-20",
    "item": "NLC404-00J001436-85450",
    "file": "data/domestic/press_scans/NLC404-00J001436-85450_民憲_第一卷第九期.pdf",
    "sha": "b6e123c4d90e4b2b596a61e70758f3d0be22cbfbf63ee6ac7853f682de62d5df",
    "url": "https://commons.wikimedia.org/wiki/File:NLC404-00J001436-85450_%E6%B0%91%E6%86%B2_1944%E2%80%931945%E5%B9%B4%E7%AC%AC%E4%B8%80%E5%8D%B7%E7%AC%AC%E4%B9%9D%E6%9C%9F.pdf",
}

registry = json.loads(registry_path.read_text(encoding="utf-8"))
if not any(item.get("source_id") == source_id for item in registry):
    registry.append(source)
    registry_path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    source_added = True
else:
    source_added = False

existing = set()
with candidates_path.open(encoding="utf-8") as fh:
    for line in fh:
        if line.strip():
            existing.add(json.loads(line)["candidate_id"])

added = 0
with candidates_path.open("a", encoding="utf-8") as fh:
    for issue in issues:
        if issue["candidate_id"] in existing:
            continue
        candidate = {
            "candidate_id": issue["candidate_id"],
            "title": issue["title"],
            "creator": "左舜生主编／《民憲》编辑委员会",
            "document_date": issue["date"],
            "document_date_precision": "day",
            "document_type": "同期政论刊物原刊整期扫描",
            "repository_code": "NLC",
            "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
            "collection_name": "《民憲》第一卷",
            "archive_fonds": None,
            "archive_series": None,
            "archive_file": None,
            "archive_item": issue["item"],
            "catalog_reference": issue["item"],
            "catalog_reference_status": "verified",
            "source_url": issue["url"],
            "source_url_role": "item_digital",
            "access_mode": "open",
            "access_note": f"公开{issue['pages']}页 PDF；本地副本：{issue['file']}",
            "medium": "hybrid",
            "online_availability": "full_item_online",
            "rights_status": "unknown",
            "reuse_rights": "citation_only",
            "rights_basis": "Wikimedia页面与国家图书馆数字副本具体再利用规则待核",
            "copy_allowed": "unknown",
            "authenticity_level_proposed": "L1",
            "relevance_grade_proposed": "related",
            "event_tags": [issue["event"]],
            "person_tags": ["左舜生", "张澜", "中国民主同盟"],
            "place_tags": ["重庆"],
            "evidence_note": issue["note"],
            "evidence_type": "digital_image",
            "evidence_locator": f"{issue['item']}；本地 PDF 第1—2页封面/目录；整期共{issue['pages']}页；SHA256 {issue['sha']}",
            "uncertainty_note": "当前先完成刊期、目录页和整期扫描可访问性核验；具体文章正文、作者、页码和与1944年民盟正式文件的直接关系仍待逐页转录，不把整期扫描自动等同于组织规程或正式政治主张原件。",
            "checked_at": "2026-07-19",
            "checked_by": "codex",
            "review_status": "needs_human_review",
            "review_note": "已取得同期原刊整期扫描并核验目录页；待逐篇转录、建立文章级页码定位后再决定是否拆分文章候选或接受。",
        }
        fh.write(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")) + "\n")
        added += 1

    if article["candidate_id"] not in existing:
        candidate = {
            "candidate_id": article["candidate_id"],
            "title": article["title"],
            "creator": article["creator"],
            "document_date": article["document_date"],
            "document_date_precision": "day",
            "document_type": "同期政论刊物文章原刊扫描",
            "repository_code": "NLC",
            "repository_name": "中国国家图书馆数字化民国期刊（Wikimedia Commons镜像）",
            "collection_name": "《民憲》第一卷第九期",
            "archive_fonds": None,
            "archive_series": None,
            "archive_file": None,
            "archive_item": article["item"],
            "catalog_reference": article["item"],
            "catalog_reference_status": "verified",
            "source_url": article["url"],
            "source_url_role": "item_digital",
            "access_mode": "open",
            "access_note": f"公开51页 PDF；本地副本：{article['file']}",
            "medium": "hybrid",
            "online_availability": "full_item_online",
            "rights_status": "unknown",
            "reuse_rights": "citation_only",
            "rights_basis": "Wikimedia页面与国家图书馆数字副本具体再利用规则待核",
            "copy_allowed": "unknown",
            "authenticity_level_proposed": "L1",
            "relevance_grade_proposed": "related",
            "event_tags": ["1944改组更名", "1944民主宪政论述"],
            "person_tags": ["陈启天", "左舜生", "中国民主同盟"],
            "place_tags": ["重庆"],
            "evidence_note": "原刊目录页（PDF第2页）列出《民主政治與非民主政治》；正文页眉与印刷页码核见该文，正文跨印刷页13—17（PDF第16—20页），末页印刷页17可清楚核读。作者陈启天由公开学术引文与该文题名、刊期、页码互证；学术引文不是替代原刊的一级证据。",
            "evidence_type": "digital_image",
            "evidence_locator": f"{article['item']}；目录 PDF 第2页；正文印刷页13—17（PDF第16—20页）；整期 SHA256 {article['sha']}",
            "uncertainty_note": "当前已核验题名、作者的外部书目互证、刊期和页级影像；尚未完成逐段人工转录、异体字规范化和与1944年民盟正式文件的直接关系判定。",
            "checked_at": "2026-07-19",
            "checked_by": "codex",
            "review_status": "needs_human_review",
            "review_note": "文章级原刊证据已建立；待人工复核作者署名、全文转录和引用关系后再决定是否接受。",
        }
        fh.write(json.dumps(candidate, ensure_ascii=False, separators=(",", ":")) + "\n")
        added += 1

print(json.dumps({"source_added": source_added, "candidates_added": added}, ensure_ascii=False))
