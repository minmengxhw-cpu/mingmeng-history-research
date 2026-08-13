#!/usr/bin/env python3
"""
国内资料生产线：OCR manifest（Phase 3）
====================================

读取 source_manifest.jsonl 和 inventory，输出：

1. ocr_plan.jsonl — 每份需要 OCR 的扫描件生成一条 OCR 计划记录
   字段：file_id, candidate_id, source_url, source_path, sha256,
   page_count, ocr_priority, ocr_priority_reason, status,
   citation_ready, batch, page_provenance (per-page list)
2. ocr_done_manifest.jsonl — 已 OCR 完成的清单（基于 download_manifest）
3. ocr_skip_manifest.jsonl —\u5df2\u6709\u5b8c\u6574\u6570\u5b57\u4ef6\u3001\u4e0d\u9700 OCR \u7684\u8df3\u8fc7\u8bb0\u5f55
4. ocr_manifest_summary.md — 摘要

去重规则：\u201c\u5df2\u6709\u7535\u5b50\u6587\u672c\u4e0d\u91cd\u590d OCR\u201d
- online_availability=full_item_online → skip
- \u540c\u4e00 source_url \u51fa\u73b0\u591a\u6761 candidate \uff08\u540c\u4e00\u4efd\u539f\u4ef6\u7684\u4e0d\u540c\u6587\u7ae0\uff09\u2192 \u53ea OCR \u4e00\u6b21\uff0c\u591a\u6761 candidate \u5171\u4eab
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlparse


def is_already_electronic(c: dict) -> bool:
    """\u5df2\u6709\u5b8c\u6574\u7535\u5b50\u6587\u672c\uff0c\u4e0d\u9700 OCR\u3002"""
    return c.get("online_availability") == "full_item_online"


def page_provenance_template(c: dict, page_count: int) -> list[dict]:
    """\u751f\u6210\u9875\u7ea7 provenance \u6a21\u677f\u3002"""
    pages = []
    for i in range(1, page_count + 1):
        pages.append({
            "page_number": i,
            "page_label": f"p{i:04d}",
            "ocr_status": "pending",
            "ocr_engine": None,
            "ocr_markdown_path": None,
            "num_lines": 0,
            "mean_confidence": 0.0,
            "needs_human_review": True,
            "verified_against_human": False,
            "citation_ready": False,
        })
    return pages


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-manifest", type=Path,
                        default=Path("work/minimax-20260803/02_manifests/source_manifest.jsonl"))
    parser.add_argument("--download-manifest", type=Path,
                        default=Path("data/domestic/collection_download_manifest_20260726.jsonl"))
    parser.add_argument("--out", type=Path, default=Path("work/minimax-20260803/03_ocr"))
    args = parser.parse_args()

    out = args.out
    out.mkdir(parents=True, exist_ok=True)

    # \u8bfb\u5165 source_manifest
    rows = [json.loads(line) for line in args.source_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    print(f"source_manifest rows: {len(rows)}")

    # \u8bfb\u5165 download_manifest
    if args.download_manifest.exists():
        dl = [json.loads(line) for line in args.download_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
    else:
        dl = []
    print(f"download_manifest rows: {len(dl)}")

    # \u6309 source_url \u7684\u552f\u4e00\u4ef6\u5408\u5e76 candidate
    by_url: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        if r.get("source_url"):
            by_url[r["source_url"]].append(r)

    # ====== ocr_plan.jsonl ======
    plan_rows = []
    seen_urls: set[str] = set()
    need_ocr_urls = []
    skip_urls = []

    for url, candidates in by_url.items():
        seen_urls.add(url)
        canonical = candidates[0]
        all_skip = all(is_already_electronic(c) for c in candidates)
        if all_skip:
            skip_urls.append({
                "source_url": url,
                "skip_reason": "full_item_online",
                "candidate_ids": [c["candidate_id"] for c in candidates],
                "level_distribution": {
                    lvl: sum(1 for c in candidates if (c.get("authenticity_level") == lvl))
                    for lvl in {"L1", "L2", "L3", "L4", "LX"}
                },
            })
            continue

        # \u9700\u8981 OCR \u7684 source_url
        # \u4f18\u5148\u7ea7\u5224\u5b9a\uff1a
        #   p0: L1 + (needs_ocr)\uff0c\u4e14\u7528\u4e8e 1941-1943 / 1944-1945 \u4e2d\u7684\u5173\u952e\u4e8b\u4ef6
        #   p1: L2 + surrogate_online
        #   p2: L3 \u671f\u520a\u88c1\u62a5\u6216\u6c47\u7f16
        #   p3: LX / L4 \u9700\u88c1\u522b
        needs_ocr = [c for c in candidates if c.get("needs_ocr")]
        if not needs_ocr:
            continue
        primary = needs_ocr[0]
        # \u9875\u6570\u63a8\u65ad
        page_count = primary.get("page_count") or 1
        if not page_count:
            page_count = 1
        # \u4f18\u5148\u7ea7
        period = primary.get("period", "")
        level = primary.get("authenticity_level", "")
        cluster_ids = sorted(set(c.get("cluster_id") for c in candidates if c.get("cluster_id")))
        if level == "L1" and period in {"1941-1943", "1944-1945"}:
            priority = "p0"
            reason = "L1 + 1941-1945 \u91cd\u70b9\u671f\u5173\u952e\u539f\u4ef6"
        elif level == "L1" and period == "1946-1950":
            priority = "p1"
            reason = "L1 + 1946-1950 \u671f\u5173\u952e\u4ef6"
        elif level == "L2":
            priority = "p2"
            reason = "L2 \u6c47\u7f16\u672c\u3001\u5f85\u9875\u7ea7\u91cd\u65b0\u5b9a\u4f4d"
        elif level == "L3":
            priority = "p3"
            reason = "L3 \u540c\u671f\u62a5\u520a\u88c1\u62a5 / \u4e0d\u5b8c\u6574\u671f\u53f7"
        elif level == "LX":
            priority = "p3"
            reason = "LX \u5f85\u88c1\u522b\uff0c\u9700\u989d\u5916\u9a8c\u8bc1"
        else:
            priority = "p3"
            reason = "L4 \u4e8c\u6b21\u5448\u73b0\uff0c\u4e0d\u5efa\u8ba1 OCR"

        file_id = f"OCR-{len(plan_rows) + 1:04d}"
        provenance = page_provenance_template(primary, page_count)
        primary_cid = primary["candidate_id"]
        plan_rows.append({
            "file_id": file_id,
            "source_url": url,
            "source_kind": primary.get("source_kind"),
            "repository_code": primary.get("repository_code"),
            "candidate_ids": [c["candidate_id"] for c in candidates],
            "primary_candidate_id": primary_cid,
            "primary_title": primary.get("title"),
            "primary_document_date": primary.get("document_date"),
            "period": primary.get("period"),
            "authenticity_level": level,
            "evidence_grade": primary.get("evidence_grade"),
            "page_count": page_count,
            "page_count_basis": "extracted_from_catalog_reference" if primary.get("page_count") else "estimated_single",
            "cluster_ids": cluster_ids,
            "ocr_priority": priority,
            "ocr_priority_reason": reason,
            "status": "planned",
            "citation_ready": False,
            "needs_human_review": True,
            "page_provenance": provenance,
            "notes": "OCR \u8349\u7a3f\u3001\u4e0d\u6807\u8bb0 citation_ready=True\uff1b\u9700\u4eba\u5de5\u590d\u6838\u9875\u7ea7\u9875\u9762\u3001\u68c0\u67e5\u6a21\u7cca\u5b57\u3001\u4fee\u590d\u9875\u7801\u9519\u8bef\u540e\u624d\u80fd\u8fdb citation \u7ea7",
        })
        need_ocr_urls.append(url)

    # acquisition_required：物理书 + 无 URL → 调档
    acquisition_required = []
    for r in rows:
        if r.get("needs_ocr") and not r.get("source_url"):
            acquisition_required.append({
                "candidate_id": r["candidate_id"],
                "title": r["title"],
                "repository_code": r["repository_code"],
                "repository_name": r["repository_name"],
                "period": r["period"],
                "authenticity_level": r["authenticity_level"],
                "evidence_grade": r["evidence_grade"],
                "online_availability": r["online_availability"],
                "medium": r["medium"],
                "next_action": "调档 / 现场核验 / 采购扫描",
                "citation_ready": False,
                "needs_human_review": True,
                "notes": "物理书 + 无 URL：需要进一步调档或扫描，本轮不 OCR",
            })
    acq_path = out / "acquisition_required.jsonl"
    with acq_path.open("w", encoding="utf-8") as f:
        for r in acquisition_required:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    # ocr_plan.jsonl
    plan_path = out / "ocr_plan.jsonl"
    with plan_path.open("w", encoding="utf-8") as f:
        for r in plan_rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    # ocr_skip_manifest.jsonl
    skip_path = out / "ocr_skip_manifest.jsonl"
    with skip_path.open("w", encoding="utf-8") as f:
        for r in skip_urls:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    # ====== ocr_done_manifest.jsonl ======
    # \u57fa\u4e8e download_manifest\uff1a\u5df2\u4e0b\u8f7d\u3001\u5df2 OCR \u8fc7\u7684\u6587\u4ef6
    done_rows = []
    for d in dl:
        if not d.get("file_exists"):
            continue
        # \u67e5\u627e\u6620\u5c04\u5230\u54ea\u4e9b candidate
        matched = []
        for r in rows:
            if r.get("source_url") and r["source_url"] == d.get("source_url"):
                matched.append(r["candidate_id"])
            elif r.get("title") == d.get("title"):
                matched.append(r["candidate_id"])
        done_rows.append({
            "download_id": d.get("download_id"),
            "title": d.get("title"),
            "source_url": d.get("source_url"),
            "local_path": d.get("local_path"),
            "sha256": d.get("sha256"),
            "file_size": d.get("file_size"),
            "evidence_level": d.get("evidence_level"),
            "source_kind": d.get("source_kind"),
            "is_new_download": d.get("is_new_download", False),
            "was_already_local": d.get("was_already_local", False),
            "matched_candidate_ids": matched,
            "citation_ready": False,
            "needs_human_review": True,
            "status": "downloaded_pending_ocr",
            "notes": d.get("notes", ""),
        })
    done_path = out / "ocr_done_manifest.jsonl"
    with done_path.open("w", encoding="utf-8") as f:
        for r in done_rows:
            f.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")

    # ====== summary ======
    from collections import Counter
    priority_counter = Counter(r["ocr_priority"] for r in plan_rows)
    level_counter = Counter(r["authenticity_level"] for r in plan_rows)
    period_counter = Counter(r["period"] for r in plan_rows)
    skipped_counter = Counter(r["skip_reason"] for r in skip_urls)

    summary = {
        "batch_id": "minimax-20260803-phase3-ocr-manifest",
        "produced_at": "2026-08-03",
        "input_source_manifest": str(args.source_manifest),
        "input_download_manifest": str(args.download_manifest),
        "totals": {
            "unique_source_urls": len(by_url),
            "ocr_plan_rows": len(plan_rows),
            "ocr_skip_rows": len(skip_urls),
            "ocr_done_rows": len(done_rows),
            "acquisition_required": len(acquisition_required),
        },
        "ocr_plan_by_priority": dict(priority_counter),
        "ocr_plan_by_level": dict(level_counter),
        "ocr_plan_by_period": dict(period_counter),
        "ocr_skip_reasons": dict(skipped_counter),
        "outputs": {
            "ocr_plan_jsonl": str(plan_path),
            "ocr_done_manifest_jsonl": str(done_path),
            "ocr_skip_manifest_jsonl": str(skip_path),
            "acquisition_required_jsonl": str(acq_path),
        },
    }
    (out / "ocr_manifest_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # markdown summary
    md = [
        "# OCR Manifest 摘要",
        "",
        f"- 唯一 source_url: {len(by_url)}",
        f"- OCR 计划: {len(plan_rows)}",
        f"- OCR 跳过: {len(skip_urls)}",
        f"- 已下载/已 OCR: {len(done_rows)}",
        "",
        "## OCR 计划优先级分布",
        "",
    ]
    for k, v in priority_counter.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## OCR 计划证据等级分布")
    md.append("")
    for k, v in level_counter.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## OCR 计划时期分布")
    md.append("")
    for k, v in period_counter.most_common():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("## OCR 跳过原因")
    md.append("")
    for k, v in skipped_counter.most_common():
        md.append(f"- {k}: {v}")
    (out / "ocr_manifest_summary.md").write_text("\n".join(md), encoding="utf-8")

    print(f"OCR plan: {len(plan_rows)}")
    print(f"OCR skip: {len(skip_urls)}")
    print(f"OCR done: {len(done_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
