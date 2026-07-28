#!/usr/bin/env python3
"""Build a ranked human-review queue for derived domestic evidence units."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_INPUT = ROOT / "data" / "domestic" / "evidence_units.jsonl"
DEFAULT_JSONL = ROOT / "work" / "domestic" / "EVIDENCE_UNIT_REVIEW_QUEUE_20260728.jsonl"
DEFAULT_CSV = ROOT / "work" / "domestic" / "EVIDENCE_UNIT_REVIEW_QUEUE_20260728.csv"
DEFAULT_MD = ROOT / "work" / "domestic" / "EVIDENCE_UNIT_REVIEW_QUEUE_20260728.md"


def load_units(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def priority(unit: dict) -> tuple[str, int, str]:
    level = str(unit.get("evidence_level") or "L9")
    status = str(unit.get("ocr_status") or "unknown")
    boundary = str(unit.get("article_boundary_status") or "unknown")
    if status == "verified":
        return "P3", 30, "verify citation locator and final boundary before any citation_ready promotion"
    if level == "L1":
        return "P1", 100 + (20 if boundary == "unknown" else 0), "compare source image with OCR, confirm article boundary and citation locator"
    return "P2", 70 + (20 if boundary == "unknown" else 0), "compare source image with OCR, confirm date/title/boundary and citation locator"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--jsonl", type=Path, default=DEFAULT_JSONL)
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--md", type=Path, default=DEFAULT_MD)
    args = parser.parse_args()

    units = load_units(args.input)
    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    queue: list[dict] = []
    for unit in units:
        doc = conn.execute("SELECT title, doc_key FROM documents WHERE id=?", (unit["document_id"],)).fetchone()
        pages = [
            dict(row)
            for row in conn.execute(
                "SELECT id, page_label, text FROM pages WHERE id IN ({}) ORDER BY id".format(",".join("?" for _ in unit.get("page_ids", []))),
                unit.get("page_ids", []),
            )
        ] if unit.get("page_ids") else []
        queue_name, score, next_action = priority(unit)
        item = {
            "review_priority": queue_name,
            "review_score": score,
            "evidence_id": unit["evidence_id"],
            "document_id": unit["document_id"],
            "page_ids": unit.get("page_ids", []),
            "page_labels": [str(page["page_label"] or "") for page in pages],
            "text_chars": sum(len(str(page["text"] or "")) for page in pages),
            "source_doc_title": doc["title"] if doc else None,
            "source_doc_key": doc["doc_key"] if doc else None,
            "source_id": unit.get("source_id"),
            "article_title_original": unit.get("article_title_original"),
            "date_original": unit.get("date_original"),
            "evidence_level": unit.get("evidence_level"),
            "ocr_status": unit.get("ocr_status"),
            "article_boundary_status": unit.get("article_boundary_status"),
            "citation_ready": bool(unit.get("citation_ready")),
            "uncertainties": unit.get("uncertainties"),
            "next_action": next_action,
            "gate": "hold_until_human_review",
        }
        queue.append(item)
    conn.close()
    queue.sort(key=lambda item: (-int(item["review_score"]), item["evidence_id"]))

    for path in (args.jsonl, args.csv, args.md):
        path.parent.mkdir(parents=True, exist_ok=True)
    with args.jsonl.open("w", encoding="utf-8") as fh:
        for item in queue:
            fh.write(json.dumps(item, ensure_ascii=False, sort_keys=True) + "\n")
    fields = [
        "review_priority", "review_score", "evidence_id", "document_id", "page_ids", "page_labels",
        "text_chars", "source_doc_title", "source_id", "article_title_original", "date_original",
        "evidence_level", "ocr_status", "article_boundary_status", "citation_ready", "next_action", "gate",
    ]
    with args.csv.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for item in queue:
            row = dict(item)
            row["page_ids"] = ",".join(str(value) for value in item["page_ids"])
            row["page_labels"] = ",".join(item["page_labels"])
            writer.writerow({key: row.get(key, "") for key in fields})

    counts = {}
    for item in queue:
        counts[item["review_priority"]] = counts.get(item["review_priority"], 0) + 1
    lines = [
        "# 国内证据单元人工复核队列（2026-07-28）",
        "",
        "本队列只读生成，不修改主库；所有条目在人工复核前保持 `citation_ready=false`。",
        "",
        f"- 总数：{len(queue)}",
        f"- P1 一手/高价值 OCR：{counts.get('P1', 0)}",
        f"- P2 同期候选 OCR：{counts.get('P2', 0)}",
        f"- P3 已标记 verified、仍需引用定位复核：{counts.get('P3', 0)}",
        "",
        "## 复核门控",
        "",
        "1. 对照原图或原 PDF，确认 OCR 字符、日期、标题和文章边界。",
        "2. 写入页码/版面/详情 URL 等可复核定位；不能只凭 OCR 片段升为引用级。",
        "3. 处理完成后再单独生成人工决策文件；本队列本身不执行数据库写入。",
        "",
        "## 优先批次",
        "",
        "| 优先级 | ID | 日期 | 原题名 | 来源 | OCR | 边界 | 页数/字符数 |",
        "|---|---|---|---|---|---|---|---:|",
    ]
    for item in queue:
        title = str(item["article_title_original"] or "").replace("|", "\\|")
        source = str(item["source_id"] or "").replace("|", "\\|")
        lines.append(
            f"| {item['review_priority']} | `{item['evidence_id']}` | {item['date_original']} | {title} | `{source}` | {item['ocr_status']} | {item['article_boundary_status']} | {len(item['page_ids'])}/{item['text_chars']} |"
        )
    args.md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"rows": len(queue), "counts": counts, "jsonl": str(args.jsonl), "csv": str(args.csv), "md": str(args.md)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
