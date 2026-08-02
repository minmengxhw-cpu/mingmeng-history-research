#!/usr/bin/env python3
"""Build a provenance-preserving MMDA 1942-1943 verification queue.

This is a read-only report builder. It does not download, OCR, or modify the
research database. Catalogue-only records remain queue items until a user-
authorized browser session exposes the original document.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_JSONL = ROOT / "work" / "domestic" / "MMDA_1942_1943_PRIORITY_QUEUE_20260728.jsonl"
DEFAULT_CSV = ROOT / "work" / "domestic" / "MMDA_1942_1943_PRIORITY_QUEUE_20260728.csv"
DEFAULT_MD = ROOT / "work" / "domestic" / "MMDA_1942_1943_PRIORITY_QUEUE_20260728.md"


def priority(title: str, document_date: str) -> tuple[int, str]:
    """Rank direct organizational evidence ahead of retrospective histories."""

    direct_terms = ("委员人选", "名单", "情况报告", "秘密活动")
    if any(term in title for term in direct_terms) and document_date in {"1942", "1943"}:
        return 1, "direct_organizational_evidence"
    if document_date in {"1942", "1943"}:
        return 2, "same_period_primary_candidate"
    return 3, "period_spanning_history_candidate"


def load_rows(db_path: Path) -> list[dict[str, object]]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT candidate_id, title, creator, document_date, document_type,
               repository_code, repository_name, collection_name, catalog_reference,
               catalog_reference_status, source_url, source_url_role, access_mode,
               access_note, medium, online_availability, rights_status, copy_allowed,
               authenticity_level_accepted, relevance_grade_accepted, evidence_type,
               evidence_locator, uncertainty_note, review_status
        FROM domestic_candidates
        WHERE repository_code = 'MM1941'
          AND (document_date LIKE '%1942%' OR document_date LIKE '%1943%')
        ORDER BY document_date, title, candidate_id
        """
    ).fetchall()
    conn.close()

    result: list[dict[str, object]] = []
    for row in rows:
        item = dict(row)
        rank, rationale = priority(str(item.get("title") or ""), str(item.get("document_date") or ""))
        item.update(
            {
                "queue_rank": rank,
                "queue_rationale": rationale,
                "next_action": "user_login_then_verify_detail_and_read_pdf",
                "ingest_gate": "do_not_import_original_until_pdf_or_full_image_is_obtained",
                "citation_ready": False,
            }
        )
        result.append(item)
    result.sort(key=lambda item: (int(item["queue_rank"]), str(item["document_date"]), str(item["title"])))
    return result


def write_outputs(rows: list[dict[str, object]], jsonl_path: Path, csv_path: Path, md_path: Path) -> None:
    for path in (jsonl_path, csv_path, md_path):
        path.parent.mkdir(parents=True, exist_ok=True)

    with jsonl_path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    fields = [
        "queue_rank", "candidate_id", "title", "document_date", "catalog_reference",
        "access_mode", "online_availability", "authenticity_level_accepted",
        "relevance_grade_accepted", "review_status", "next_action", "ingest_gate",
    ]
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fields} for row in rows)

    rank1 = sum(int(row["queue_rank"]) == 1 for row in rows)
    rank2 = sum(int(row["queue_rank"]) == 2 for row in rows)
    rank3 = sum(int(row["queue_rank"]) == 3 for row in rows)
    lines = [
        "# MMDA 1942–1943 原件核验队列（2026-07-28）",
        "",
        "本报告由主库 `domestic_candidates` 只读生成，不下载、不 OCR、不修改 SQLite。",
        "当前条目均为民盟全媒体数据库目录记录；在授权浏览器会话取得正文 PDF/完整图片前，不能转为正式正文入库。",
        "",
        f"- 队列总数：{len(rows)}",
        f"- P1 同期组织原始证据候选：{rank1}",
        f"- P2 同期一手候选：{rank2}",
        f"- P3 跨期整理史候选：{rank3}",
        "- 当前统一动作：用户登录后逐条核验详情页、正文入口、原件类型和权限状态",
        "- 当前统一门控：没有取得正文 PDF/完整原图，不启动 OCR，不写入正文层，不标记 citation_ready",
        "",
        "## 队列",
        "",
        "| 优先级 | 日期 | 标题 | 目录定位 | 当前状态 |",
        "|---:|---|---|---|---|",
    ]
    for row in rows:
        title = str(row["title"]).replace("|", "\\|")
        ref = str(row["catalog_reference"]).replace("|", "\\|")
        state = f"{row['access_mode']}; {row['online_availability']}"
        lines.append(f"| P{row['queue_rank']} | {row['document_date']} | {title} | `{ref}` | {state} |")
    lines.extend(
        [
            "",
            "## 执行顺序",
            "",
            "1. 先处理 P1：陕西支部委员人选、支部筹备委员会名单、西北局第二次扩大会议报告。",
            "2. 再处理 P3 中的《民盟在陕西》系列和西安市秘密活动地点条目；它们用于组织史定位和与 P1 原始记录互证。",
            "3. 最后处理 P3：陕西民盟史、陕西民盟 70 年；仅作为整理史和线索，不替代同期原件。",
            "4. 每条下载后保留原文件名、详情 URL、正文 URL、SHA256 和权限/版权说明，再交给 PaddleOCR 做页级试跑。",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()
    rows = load_rows(args.db)
    write_outputs(rows, args.jsonl, args.csv, args.md)
    print(json.dumps({"rows": len(rows), "jsonl": str(args.jsonl), "csv": str(args.csv), "md": str(args.md)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
