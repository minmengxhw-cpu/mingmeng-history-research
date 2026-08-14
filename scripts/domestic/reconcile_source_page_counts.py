#!/usr/bin/env python3
"""Reconcile physical source pages with formal page layers and metadata anchors.

This is a metadata-only audit.  It does not read source bodies, write SQLite,
change citation states, delete files, or decide that an original has been
obtained.  Its purpose is to explain why a coverage inventory may report more
indexed pages than a PDF contains: a canonical page chain, a full OCR layer,
and one-page collection anchors can legitimately coexist for one source.
"""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INVENTORY = ROOT / "work/domestic/DOMESTIC_COVERAGE_INVENTORY_20260728.csv"
DEFAULT_DB = ROOT / "data/research_index.sqlite"


def integer(value: object) -> int:
    try:
        return int(str(value or "0").strip())
    except (TypeError, ValueError):
        return 0


def source_suffix(value: object, source_path: str) -> bool:
    """Match both closeout-relative paths and the historical sibling checkout."""

    text = str(value or "").replace("\\", "/").rstrip("/")
    target = source_path.replace("\\", "/").lstrip("/")
    return text == target or text.endswith("/" + target)


def layer_for(doc_key: str, page_count: int) -> str:
    if doc_key.startswith("domestic-page/"):
        return "CANONICAL_PAGE_CHAIN"
    if doc_key.startswith("domestic-ocr/"):
        if "COLLECTION:" in doc_key or "LOCALFULL:" in doc_key:
            return "COLLECTION_ANCHOR"
        if ":S3:" in doc_key or doc_key.startswith("domestic-ocr/S3:"):
            return "TOPIC_EXTRACT"
        if page_count > 1 or doc_key.startswith("domestic-ocr/NLC:"):
            return "FULL_OCR_LAYER"
        return "OCR_RECORD"
    return "OTHER_RECORD"


def page_numbers(rows: list[tuple[Any, ...]]) -> list[int]:
    values: set[int] = set()
    for pdf_page_no, physical_page_no in rows:
        value = pdf_page_no or physical_page_no
        if value is not None:
            values.add(int(value))
    return sorted(values)


def complete_page_layer(page_count: int, physical_pages: int, numbers: list[int]) -> bool:
    return (
        physical_pages > 0
        and page_count == physical_pages
        and numbers == list(range(1, physical_pages + 1))
    )


def build_rows(inventory_path: Path, db_path: Path) -> list[dict[str, Any]]:
    with inventory_path.open(encoding="utf-8-sig", newline="") as handle:
        inventory = list(csv.DictReader(handle))
    if not inventory:
        raise ValueError(f"empty inventory: {inventory_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    documents = conn.execute(
        "SELECT id, doc_key, title, local_txt, local_html FROM documents ORDER BY id"
    ).fetchall()
    provenance = conn.execute(
        "SELECT page_id, document_id, source_file, pdf_page_no, physical_page_no "
        "FROM page_provenance ORDER BY page_id"
    ).fetchall()
    pages_by_document: dict[int, list[tuple[Any, ...]]] = {}
    for row in provenance:
        pages_by_document.setdefault(int(row["document_id"]), []).append(
            (row["pdf_page_no"], row["physical_page_no"])
        )

    output: list[dict[str, Any]] = []
    for source in inventory:
        source_path = str(source.get("source_path", "")).strip()
        physical_pages = integer(source.get("pdf_pages"))
        matched: dict[int, str] = {}
        for doc in documents:
            if source_suffix(doc["local_txt"], source_path) or source_suffix(
                doc["local_html"], source_path
            ):
                matched[int(doc["id"])] = "document_path"
        for row in provenance:
            if source_suffix(row["source_file"], source_path):
                matched.setdefault(int(row["document_id"]), "provenance_path")

        layer_records: dict[str, list[dict[str, Any]]] = {}
        for doc_id in sorted(matched):
            doc = next(item for item in documents if int(item["id"]) == doc_id)
            page_rows = pages_by_document.get(doc_id, [])
            numbers = page_numbers(page_rows)
            layer = layer_for(str(doc["doc_key"]), len(page_rows))
            layer_records.setdefault(layer, []).append(
                {
                    "document_id": doc_id,
                    "doc_key": str(doc["doc_key"]),
                    "title": str(doc["title"] or ""),
                    "page_count": len(page_rows),
                    "page_numbers": numbers,
                    "complete": complete_page_layer(len(page_rows), physical_pages, numbers),
                    "match": matched[doc_id],
                }
            )

        canonical = [r for r in layer_records.get("CANONICAL_PAGE_CHAIN", []) if r["complete"]]
        full_ocr = [r for r in layer_records.get("FULL_OCR_LAYER", []) if r["complete"]]
        anchor_pages = sum(r["page_count"] for r in layer_records.get("COLLECTION_ANCHOR", []))
        topic_pages = sum(r["page_count"] for r in layer_records.get("TOPIC_EXTRACT", []))
        if canonical:
            if full_ocr:
                disposition = "RECONCILED_DUPLICATE_COMPLETE_LAYERS"
                recommendation = "不重复 OCR；以 canonical page chain 为页级展示层，保留 OCR 作为检索/比对层。"
            else:
                disposition = "RECONCILED_CANONICAL_PAGE_CHAIN"
                recommendation = "不重复 OCR；进入定向内容复核，页级 provenance 已有完整链。"
        elif full_ocr:
            disposition = "RECONCILED_COMPLETE_OCR_LAYER"
            recommendation = "不整本重复 OCR；先评估是否需要补建 canonical page chain。"
        elif layer_records:
            disposition = "UNRECONCILED_PARTIAL_OR_NONPAGE_RECORDS"
            recommendation = "保留待对账；不得把局部页、目录或锚点当作完整页链。"
        else:
            disposition = "NO_FORMAL_MATCH"
            recommendation = "仅保留来源清单；取得页链或授权原件后再入库。"

        output.append(
            {
                "source_path": source_path,
                "physical_pages": physical_pages,
                "inventory_indexed_pages": integer(source.get("indexed_pages")),
                "inventory_ocr_draft_pages": integer(source.get("ocr_draft_pages")),
                "inventory_status": source.get("status", ""),
                "matched_document_count": len(matched),
                "canonical_complete_count": len(canonical),
                "full_ocr_complete_count": len(full_ocr),
                "collection_anchor_pages": anchor_pages,
                "topic_extract_pages": topic_pages,
                "layer_records": layer_records,
                "disposition": disposition,
                "recommendation": recommendation,
            }
        )
    conn.close()
    return output


def write_outputs(rows: list[dict[str, Any]], json_path: Path, md_path: Path) -> dict[str, Any]:
    counts = Counter(row["disposition"] for row in rows)
    payload = {
        "schema": "domestic_source_page_reconciliation.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "body_read": False,
        "formal_db_written": False,
        "citation_state_changed": False,
        "auto_delete": False,
        "source_count": len(rows),
        "disposition_counts": dict(sorted(counts.items())),
        "rows": rows,
    }
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 国内来源页链对账报告",
        "",
        "本报告只读取来源覆盖表和 SQLite 元数据，不读取正文、不写 SQLite、不改变引用状态、不删除文件。",
        "",
        f"- 来源数：{len(rows)}",
        f"- 生成时间：{payload['generated_at']}",
        "",
        "## 结论分布",
        "",
        "| 结论 | 数量 |",
        "|---|---:|",
    ]
    lines.extend(f"| `{key}` | {value} |" for key, value in sorted(counts.items()))
    lines.extend(
        [
            "",
            "## 解释",
            "",
            "- `RECONCILED_DUPLICATE_COMPLETE_LAYERS`：canonical 页链已覆盖物理页，另有完整 OCR 层；统计上的超页数是层重复，不是原件多页。",
            "- `RECONCILED_CANONICAL_PAGE_CHAIN`：canonical 页链已覆盖物理页，可停止重复 OCR，转入定向内容复核。",
            "- `RECONCILED_COMPLETE_OCR_LAYER`：已有完整 OCR 页层，但仍需判断是否补建视觉页链。",
            "- 其余状态继续保持待对账；本报告不会把局部页、目录、汇编重刊或后期转录升级为原始证据。",
            "",
            "## 逐来源",
            "",
            "| 来源 | 物理页 | canonical 完整层 | OCR 完整层 | 锚点页 | 主题抽取页 | 结论 |",
            "|---|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in rows:
        lines.append(
            "| `{source}` | {physical} | {canonical} | {ocr} | {anchors} | {topics} | `{disp}` |".format(
                source=row["source_path"],
                physical=row["physical_pages"],
                canonical=row["canonical_complete_count"],
                ocr=row["full_ocr_complete_count"],
                anchors=row["collection_anchor_pages"],
                topics=row["topic_extract_pages"],
                disp=row["disposition"],
            )
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "source_count": len(rows),
        "disposition_counts": dict(sorted(counts.items())),
        "json": str(json_path),
        "md": str(md_path),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--output-json", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    args = parser.parse_args()
    result = write_outputs(
        build_rows(args.inventory.resolve(), args.db.resolve()),
        args.output_json.resolve(),
        args.output_md.resolve(),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
