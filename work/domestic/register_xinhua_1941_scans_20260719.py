#!/usr/bin/env python3
"""Register verified National Library newspaper scans used for an early-gap check."""

import json
from pathlib import Path

root = Path(__file__).resolve().parents[2]
path = root / "data/domestic/source_registry.json"
source_id = "domestic:source:nlc_xinhua_daily_1941_early_issue_scans"
source = {
    "source_id": source_id,
    "source_name": "《新华日报》1941年10月10日、10月16日、10月28日国家图书馆原刊扫描",
    "institution": "中国国家图书馆数字化民国报纸；Wikimedia Commons公开镜像",
    "source_type": "同期报刊原刊全版扫描／国家图书馆数字化镜像",
    "authority_level": "国家图书馆原刊数字化扫描的公开镜像；不是原始馆藏系统直链",
    "official_url": "https://read.nlc.cn/",
    "record_or_search_url": "https://commons.wikimedia.org/wiki/Commons:Library_back_up_project/file_list/NLC/民國報紙",
    "material_types": [
        "《新华日报》1941-10-10全版扫描",
        "《新华日报》1941-10-16全版扫描",
        "《新华日报》1941-10-28全版扫描",
        "1941年民盟成立同期中文报刊对照与负向核查",
    ],
    "shanghai_relevance": "中；用于1941年民盟成立材料的同期中文报刊对照、日期核验和排除重复追索，不替代香港《光明报》原刊",
    "access_mode": "公开 PDF；Commons 文件页提供原始下载入口",
    "rights_status": "public_domain_claimed_unknown",
    "verification_note": "已下载并核验三件公开 PDF：1941-10-10共6页、1941-10-16共2页、1941-10-28共2页，均未加密；文件分别为 NLC1080-00N000846-8631、NLC1080-00N000846-8658、NLC1080-00N000846-8712。Codex以120 dpi逐页可视核读，未在三期版面中发现可直接登记为中国民主政团同盟成立宣言、十大纲领或《民主运动的生力军》的明确报道标题；该结果是负向核查，不证明目标文件不存在，也不新增候选。三件本地文件和SHA256详见 docs/domestic/press_scan_manifest.md 与 work/domestic/nlc_xinhua_1941_early_scans_review_20260719.md。",
    "checked_at": "2026-07-19",
    "status": "verified_entry",
}

registry = json.loads(path.read_text(encoding="utf-8"))
if not any(item.get("source_id") == source_id for item in registry):
    registry.append(source)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    added = True
else:
    added = False
print(json.dumps({"source_id": source_id, "added": added}, ensure_ascii=False))
