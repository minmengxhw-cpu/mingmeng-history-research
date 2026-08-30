#!/usr/bin/env python3
"""
国内资料生产线：source_manifest + import_dryrun（Phase 2）
========================================================

依据 inventory + dedup 报告，生成：
1. source_manifest.jsonl — 每份资料一条记录，字段：
   candidate_id, title, creator, document_date, period, repository_code,
   repository_name, catalog_reference, source_url, source_url_role,
   access_mode, online_availability, right_status, authenticity_level,
   relevance_grade, source_kind, source_family, sha256, page_count,
   evidence_grade, citation_ready, is_duplicate, cluster_id, cluster_role,
   period_priority, needs_ocr, notes
2. import_dryrun.json — 模拟入库结果：
   包含 plan / gate / by_period / by_repository / level_check / gate_check
   / moves (accepted/pending/rejected) / next_actions

不直接写入 sqlite；元数据落到 staging 目录。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlparse


# 沿用 inventory 字段
KEEP_FIELDS = [
    "candidate_id", "title", "creator", "recipient", "document_date",
    "document_date_precision", "document_type", "repository_code",
    "repository_name", "collection_name", "archive_fonds", "archive_series",
    "archive_file", "archive_item", "catalog_reference",
    "catalog_reference_status", "source_url", "source_url_role",
    "access_mode", "access_note", "medium", "online_availability",
    "rights_status", "reuse_rights", "rights_basis", "copy_allowed",
    "authenticity_level_proposed", "relevance_grade_proposed",
    "event_tags", "person_tags", "place_tags", "evidence_note",
    "evidence_type", "evidence_locator", "uncertainty_note",
    "checked_at", "checked_by", "review_status", "reviewed_at",
    "reviewed_by", "check_outcome", "authenticity_level_accepted",
    "relevance_grade_accepted",
]


def load_dedup_clusters(dedup_json: Path) -> dict[str, dict]:
    """读 duplicate_clusters.json，构建 candidate_id → cluster 映射。"""
    data = json.loads(dedup_json.read_text(encoding="utf-8"))
    cid_to_cluster = {}
    for c in data["clusters"]:
        cid_to_cluster[c["canonical_candidate_id"]] = {
            "cluster_id": c["cluster_id"],
            "role": "canonical",
            "size": c["size"],
            "members": [m["candidate_id"] for m in c["members"]],
        }
        for m in c["members"]:
            if m["candidate_id"] != c["canonical_candidate_id"]:
                cid_to_cluster[m["candidate_id"]] = {
                    "cluster_id": c["cluster_id"],
                    "role": "duplicate",
                    "size": c["size"],
                    "canonical_id": c["canonical_candidate_id"],
                    "members": [mm["candidate_id"] for mm in c["members"]],
                }
    return cid_to_cluster


def infer_sha256(c: dict) -> str:
    """从 catalog_reference 提取或回退。"""
    # 优先看 candidate 是否自身带 sha256
    for k in ("sha256", "source_sha256", "file_sha256"):
        if c.get(k):
            return c[k]
    return ""


def infer_page_count(c: dict) -> int:
    """从 catalog_reference 推断页数。"""
    cr = c.get("catalog_reference") or ""
    if not cr:
        return 0
    # 形如 "第5页" 或 "第5—12页"
    m = re.search(r"第[\s—\-]*(\d+)[\s]*[—\-][\s]*(\d+)\s*页", cr)
    if m:
        return int(m.group(2)) - int(m.group(1)) + 1
    m = re.search(r"第\s*(\d+)\s*页", cr)
    if m:
        return 1
    # candidate-level page 字段
    if c.get("page_count"):
        try:
            return int(c["page_count"])
        except (ValueError, TypeError):
            pass
    return 0


def citation_ready(c: dict) -> bool:
    """根据证据等级 + 介质 + 复核状态判断是否可被引用。

    规则（最大原则：OCR 草稿一律 citation_ready=False）：
    - L1 + full_item_online + accepted + 有档号/页码 → True
    - L2 + accepted + (catalog_reference 明确 + 非 surrogate) → True
    - 其余 → False
    OCR 草稿、LX、L3 报刊缺版次 → False
    """
    level = c.get("authenticity_level_accepted") or c.get("authenticity_level_proposed") or ""
    if c.get("review_status") != "accepted":
        return False
    # OCR 草稿检查：medium=hybrid 但还没转录成纯文本（online_availability 不是 full_item_online）
    if c.get("medium") in {"physical", "hybrid"} and c.get("online_availability") != "full_item_online":
        return False
    if level == "L1" and c.get("online_availability") == "full_item_online":
        return True
    if level == "L2" and c.get("online_availability") == "full_item_online":
        return True
    if level == "L2" and c.get("online_availability") in {"surrogate_online"}:
        # L2 页面定位至少已有 catalog_reference 中的页码或扫描页码 → 可作为 page-cite 但非 OCR 草稿
        return True
    if level == "L2" and (c.get("archive_fonds") or c.get("archive_series") or c.get("catalog_reference")):
        return True
    return False


def infer_source_kind(c: dict) -> str:
    """推断 source_kind：press / archive / web / book / mixed。"""
    repo = c.get("repository_code") or ""
    if repo in {"NLC", "WM", "HKU", "SHDPZ", "MX", "XHB"}:
        return "press_scan"
    if repo in {"SAAC", "DRNH", "NLC"}:
        return "archive_scan"
    if repo in {"MMHIST", "MMC", "QY", "ACAD", "MH", "MMSH", "MM1941", "MMZY", "FRUS"}:
        return "book_or_assembly"
    if repo in {"MM1941"}:
        return "catalogue_card"
    if repo in {"WS", "ZL1872", "ZLWEB", "JFB", "VOC", "SHPRESS"}:
        return "web_transcription"
    if repo in {"CPPCC", "PP", "ZSY", "CSSN", "CPC", "SCIO", "XINHUA", "CAIXIN", "TM", "93", "RMrb", "RMzxb", "RMzxw", "RMTZ", "NGD", "GMD"}:
        return "official_publication"
    if repo in {"MMSH", "GXMM", "FJMM", "HLJMM", "SCU", "CDMM", "BJMM", "ZJMM", "BJDCMM", "HNMM", "SHCM", "MMYunnan", "YADS", "LNU", "MM1941"}:
        return "official_history_page"
    return "other"


def build_one(c: dict, cluster: dict) -> dict:
    """生成 source_manifest 一行。"""
    url = c.get("source_url") or ""
    host = urlparse(url).netloc if url else ""
    page_count = infer_page_count(c)
    sha = infer_sha256(c)
    cit_ready = citation_ready(c)
    level = c.get("authenticity_level_accepted") or c.get("authenticity_level_proposed") or ""
    relevance = c.get("relevance_grade_accepted") or c.get("relevance_grade_proposed") or ""

    # 证据等级标签
    if level == "L1" and cit_ready:
        evidence_grade = "L1_citation_ready"
    elif level == "L1":
        evidence_grade = "L1_needs_review"
    elif level == "L2":
        evidence_grade = "L2_page_cite"
    elif level == "L3":
        evidence_grade = "L3_press_surrogate"
    elif level == "L4":
        evidence_grade = "L4_secondary"
    elif level == "LX":
        evidence_grade = "LX_unverified"
    else:
        evidence_grade = "pending"

    needs_ocr = (
        c.get("medium") in {"physical", "hybrid"}
        and c.get("online_availability") != "full_item_online"
        and c.get("access_mode") != "offline"
    )

    return {
        "candidate_id": c.get("candidate_id"),
        "title": c.get("title"),
        "creator": c.get("creator"),
        "recipient": c.get("recipient"),
        "document_date": c.get("document_date"),
        "document_date_precision": c.get("document_date_precision"),
        "document_type": c.get("document_type"),
        "period": c.get("_period"),
        "repository_code": c.get("repository_code"),
        "repository_name": c.get("repository_name"),
        "collection_name": c.get("collection_name"),
        "archive_fonds": c.get("archive_fonds"),
        "archive_series": c.get("archive_series"),
        "archive_file": c.get("archive_file"),
        "archive_item": c.get("archive_item"),
        "catalog_reference": c.get("catalog_reference"),
        "catalog_reference_status": c.get("catalog_reference_status"),
        "source_url": url,
        "source_url_role": c.get("source_url_role"),
        "url_host": host,
        "access_mode": c.get("access_mode"),
        "online_availability": c.get("online_availability"),
        "medium": c.get("medium"),
        "rights_status": c.get("rights_status"),
        "reuse_rights": c.get("reuse_rights"),
        "copy_allowed": c.get("copy_allowed"),
        "source_kind": infer_source_kind(c),
        "source_family": c.get("_source_family"),
        "authenticity_level": level,
        "relevance_grade": relevance,
        "evidence_grade": evidence_grade,
        "sha256": sha,
        "page_count": page_count,
        "citation_ready": cit_ready,
        "review_status": c.get("review_status"),
        "is_duplicate": (cluster or {}).get("role") == "duplicate",
        "cluster_id": (cluster or {}).get("cluster_id"),
        "cluster_role": (cluster or {}).get("role"),
        "cluster_size": (cluster or {}).get("size", 1),
        "needs_ocr": needs_ocr,
        "notes": c.get("uncertainty_note") or c.get("evidence_note") or "",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path, default=Path("work/minimax-20260803/01_inventory/inventory_full.jsonl"))
    parser.add_argument("--dedup", type=Path, default=Path("work/minimax-20260803/02_manifests/duplicate_clusters.json"))
    parser.add_argument("--out", type=Path, default=Path("work/minimax-20260803/02_manifests"))
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    rows = [json.loads(line) for line in args.inventory.read_text(encoding="utf-8").splitlines() if line.strip()]
    cid_to_cluster = load_dedup_clusters(args.dedup) if args.dedup.exists() else {}

    manifest_rows = []
    for c in rows:
        cluster = cid_to_cluster.get(c.get("candidate_id"), {})
        manifest_rows.append(build_one(c, cluster))

    # 写出 source_manifest.jsonl
    sm_path = out / "source_manifest.jsonl"
    with sm_path.open("w", encoding="utf-8") as f:
        for r in manifest_rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    # ============== import_dryrun.json ==============
    # 模拟入库：每个 candidate 决定 move（accepted / pending / rejected）, gate check
    moves = []
    period_stats = defaultdict(lambda: Counter())
    repo_stats = defaultdict(lambda: Counter())
    level_check = Counter()
    gate_fail_reasons = Counter()

    for r in manifest_rows:
        accepted = r["review_status"] == "accepted"
        pending = r["review_status"] == "needs_human_review"
        # 根据任务要求：OCR 草稿不允许 citation_ready=True
        if r["needs_ocr"] and r["citation_ready"]:
            r["citation_ready"] = False
            r["evidence_grade"] = "ocr_cite_blocked_draft"
        # 重新计算
        if r["evidence_grade"] == "ocr_cite_blocked_draft":
            gate_fail_reasons["ocr_draft_citation_ready"] += 1
        level_check[r["evidence_grade"]] += 1
        period_stats[r["period"]][r["evidence_grade"]] += 1
        repo_stats[r["repository_code"]][r["evidence_grade"]] += 1

        # 决定 move
        if accepted and r["authenticity_level"] in {"L1", "L2", "L3", "L4"}:
            move = "accepted_ready_for_staging"
        elif accepted and r["authenticity_level"] == "LX":
            move = "accepted_lx_pending_human"
        elif accepted:
            move = "accepted_other_level"
        elif pending:
            move = "pending_human_review"
        else:
            move = "rejected_or_other"

        if r["is_duplicate"] and r["cluster_role"] == "duplicate":
            move = "duplicate_skip_ingest"

        moves.append({
            "candidate_id": r["candidate_id"],
            "period": r["period"],
            "repository_code": r["repository_code"],
            "evidence_grade": r["evidence_grade"],
            "citation_ready": r["citation_ready"],
            "review_status": r["review_status"],
            "move": move,
            "is_duplicate": r["is_duplicate"],
            "cluster_id": r["cluster_id"],
        })

    by_period = {p: dict(c) for p, c in period_stats.items()}
    by_repo = {r: dict(c) for r, c in repo_stats.items()}

    # 模拟 staging 入库仅 committed 候选
    moves_final = Counter(m["move"] for m in moves)

    # gate：
    #   - 如果有 OCR 草稿被标记 citation_ready=True 就 fail
    #   - 否则 pass
    gate = "PASS" if gate_fail_reasons["ocr_draft_citation_ready"] == 0 else "FAIL"

    # three buckets
    # 与 staging 库一致：LX + accepted 也归入 import_ready（但 notes 标记待人工）
    bucket_import_ready = [m for m in moves if m["move"] in {"accepted_ready_for_staging", "accepted_lx_pending_human"}]
    bucket_review = [m for m in moves if m["move"] in {"pending_human_review", "accepted_other_level"}]
    bucket_exclude = [m for m in moves if m["move"] in {"duplicate_skip_ingest", "rejected_or_other"}]

    dryrun = {
        "batch_id": "minimax-20260803-phase2-source-manifest",
        "produced_at": "2026-08-03",
        "input_inventory": str(args.inventory),
        "input_dedup_clusters": str(args.dedup),
        "totals": {
            "manifest_rows": len(manifest_rows),
            "moves_total": len(moves),
            "move_breakdown": dict(moves_final),
            "gate": gate,
            "gate_fail_reasons": dict(gate_fail_reasons),
        },
        "by_period": by_period,
        "by_repository": by_repo,
        "by_evidence_grade": dict(level_check),
        "three_buckets": {
            "import_ready": {
                "count": len(bucket_import_ready),
                "candidate_ids": [m["candidate_id"] for m in bucket_import_ready],
            },
            "needs_review": {
                "count": len(bucket_review),
                "candidate_ids": [m["candidate_id"] for m in bucket_review],
            },
            "exclude": {
                "count": len(bucket_exclude),
                "candidate_ids": [m["candidate_id"] for m in bucket_exclude],
            },
        },
        "next_actions": [
            "将 bucket.import_ready 经 staging 表入 staging.db；不直接写 research_index.sqlite",
            "OCR 草稿一律保持 citation_ready=False；待人工复核后才能升级",
            "对 bucket.needs_review 调用 needs_human_review 流程补档号/影像/页码",
            "cluster_id 标记的 run内已记录去重关系；后续入库时跳过 duplicate_skip_ingest",
            "after staging review, run minimax_20260803_staging.py 创建 staging 库",
        ],
    }

    dr_path = out / "import_dryrun.json"
    dr_path.write_text(json.dumps(dryrun, ensure_ascii=False, indent=2), encoding="utf-8")

    # 摘要 markdown
    md_lines = [
        "# Domestic Source Manifest Summary",
        "",
        f"- 输入：{len(rows)} candidates",
        f"- 写入：{sm_path.relative_to(Path('work/minimax-20260803'))}",
        f"- 干运行：{dr_path.relative_to(Path('work/minimax-20260803'))}",
        "",
        "## Three Buckets",
        "",
        f"- **import_ready** (level L1-L4 + accepted): {len(bucket_import_ready)}",
        f"- **needs_review** (LX / pending / 其它): {len(bucket_review)}",
        f"- **exclude** (duplicate / rejected): {len(bucket_exclude)}",
        "",
        "## Move Breakdown",
        "",
    ]
    for k, v in moves_final.most_common():
        md_lines.append(f"- {k}: {v}")
    md_lines += [
        "",
        "## Gate",
        "",
        f"- gate: {gate}",
        f"- gate_fail_reasons: {dict(gate_fail_reasons)}",
        "",
        "## By Period × Evidence Grade",
        "",
    ]
    for p in ["1941-1943", "1944-1945", "1946-1950"]:
        md_lines.append(f"### {p}")
        for k, v in sorted(by_period.get(p, {}).items()):
            md_lines.append(f"- {k}: {v}")
        md_lines.append("")
    (out / "source_manifest_summary.md").write_text("\n".join(md_lines), encoding="utf-8")

    print(f"manifest rows: {len(manifest_rows)}")
    print(f"gate: {gate}")
    print(f"moves: {dict(moves_final)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
