#!/usr/bin/env python3
"""Build a metadata-only domestic core citation review batch.

The batch is deliberately a review queue, not a citation promotion tool.  It
selects accepted L0/L1/L2 domestic candidates, keeps event coverage visible,
and records page-level provenance without copying page text into the output.
Source files are checked against the SHA256 stored in ``page_provenance`` when
they are available locally.  No SQLite rows are changed.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sqlite3
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_OUT = ROOT / "work" / "domestic" / "core_citation_batch_20260813"
COVERAGE_PATH = ROOT / "data" / "domestic" / "event_coverage.json"

CORE_LEVELS = {"L0", "L1", "L2"}
CORE_EVENT_IDS = [
    "domestic-1941-formation",
    "domestic-1944-reorganization",
    "domestic-1945-first-congress",
    "domestic-1946-pcc",
    "domestic-1946-refuse-national-assembly",
    "domestic-1946-li-wen",
    "domestic-1947-illegal-dissolution",
    "domestic-1948-third-plenum-may-day",
    "domestic-1949-new-pcc",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_json_list(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    try:
        parsed = json.loads(text)
    except (TypeError, ValueError):
        parsed = None
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    return [item.strip() for item in text.replace("；", ";").split(";") if item.strip()]


def resolve_local_path(root: Path, raw: str | None) -> Path | None:
    value = str(raw or "").strip()
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def classify_asset(path: Path | None) -> str:
    if path is None:
        return "missing_path"
    suffix = path.suffix.lower()
    if suffix in {".pdf"}:
        return "pdf"
    if suffix in {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".jp2", ".webp"}:
        return "image"
    if suffix in {".md", ".markdown", ".txt", ".html", ".htm", ".json"}:
        return "ocr_or_text"
    return suffix.lstrip(".") or "unknown"


def load_coverage(path: Path) -> tuple[dict[str, set[str]], dict[str, str]]:
    if not path.exists():
        return {}, {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    candidate_events: dict[str, set[str]] = defaultdict(set)
    event_names: dict[str, str] = {}
    for event in payload:
        event_id = str(event.get("event_id") or "").strip()
        if not event_id:
            continue
        event_names[event_id] = str(event.get("event_name") or event_id)
        for candidate_id in event.get("domestic_candidate_ids", []):
            candidate_events[str(candidate_id)].add(event_id)
    return dict(candidate_events), event_names


def effective_level(row: sqlite3.Row) -> str:
    return str(row["authenticity_level_accepted"] or row["authenticity_level_proposed"] or "").strip()


def level_score(level: str) -> int:
    return {"L0": 115, "L1": 100, "L2": 82, "PILOT": 75}.get(level, 0)


def build_candidates(conn: sqlite3.Connection, candidate_events: dict[str, set[str]]) -> dict[int, dict[str, Any]]:
    candidates: dict[int, dict[str, Any]] = {}
    rows = conn.execute(
        """
        SELECT id, candidate_id, title, creator, document_date, document_type,
               repository_code, repository_name, source_url, source_url_role,
               access_mode, medium, rights_status, authenticity_level_proposed,
               authenticity_level_accepted, relevance_grade_proposed,
               relevance_grade_accepted, event_tags, review_status,
               ingested_document_id
        FROM domestic_candidates
        WHERE review_status = 'accepted'
        """
    ).fetchall()
    by_candidate_id: dict[str, dict[str, Any]] = {}
    by_ingested_doc: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        level = effective_level(row)
        if level not in CORE_LEVELS:
            continue
        item = {
            "candidate_db_id": int(row["id"]),
            "candidate_id": str(row["candidate_id"]),
            "title": str(row["title"] or ""),
            "creator": str(row["creator"] or ""),
            "document_date": str(row["document_date"] or ""),
            "document_type": str(row["document_type"] or ""),
            "repository_code": str(row["repository_code"] or ""),
            "repository_name": str(row["repository_name"] or ""),
            "source_url": str(row["source_url"] or ""),
            "source_url_role": str(row["source_url_role"] or ""),
            "access_mode": str(row["access_mode"] or ""),
            "medium": str(row["medium"] or ""),
            "rights_status": str(row["rights_status"] or ""),
            "level": level,
            "relevance": str(row["relevance_grade_accepted"] or row["relevance_grade_proposed"] or ""),
            "event_tags": parse_json_list(row["event_tags"]),
            "event_ids": sorted(candidate_events.get(str(row["candidate_id"]), set())),
            "review_status": str(row["review_status"]),
        }
        by_candidate_id[item["candidate_id"]] = item
        if row["ingested_document_id"] is not None:
            by_ingested_doc[int(row["ingested_document_id"])].append(item)

    docs = conn.execute(
        """
        SELECT d.id, d.doc_key, d.title, d.date_guess, d.url, d.volume_title,
               d.doc_id, d.doc_number, d.source_id, d.hit_type,
               d.ingested_candidate_id, COUNT(p.id) AS page_count,
               SUM(CASE WHEN pp.page_id IS NOT NULL THEN 1 ELSE 0 END) AS provenance_pages,
               SUM(CASE WHEN trim(COALESCE(pp.source_file, '')) <> ''
                         AND length(trim(COALESCE(pp.source_sha256, ''))) = 64
                        THEN 1 ELSE 0 END) AS anchored_pages,
               SUM(CASE WHEN trim(COALESCE(pp.page_image_path, '')) <> ''
                         AND lower(pp.page_image_path) NOT LIKE '%.md'
                         AND lower(pp.page_image_path) NOT LIKE '%.txt'
                        THEN 1 ELSE 0 END) AS image_path_pages,
               SUM(CASE WHEN lower(pp.source_file) LIKE '%.pdf' THEN 1 ELSE 0 END) AS pdf_source_pages,
               SUM(length(COALESCE(p.text, ''))) AS text_chars
        FROM documents d
        LEFT JOIN pages p ON p.document_id = d.id
        LEFT JOIN page_provenance pp ON pp.page_id = p.id
        WHERE d.source_platform = 'domestic'
        GROUP BY d.id
        """
    ).fetchall()
    for row in docs:
        linked = []
        linked.extend(by_ingested_doc.get(int(row["id"]), []))
        if row["ingested_candidate_id"] and row["ingested_candidate_id"] in by_candidate_id:
            linked.append(by_candidate_id[row["ingested_candidate_id"]])
        unique = {item["candidate_id"]: item for item in linked}
        page_count = int(row["page_count"] or 0)
        if not int(row["page_count"] or 0):
            continue
        candidate_rows = list(unique.values())
        source_pdf_pages = int(row["pdf_source_pages"] or 0)
        is_pilot = (
            not unique
            and str(row["hit_type"] or "") == "domestic_ocr_pilot"
            and source_pdf_pages > 0
            and str(row["date_guess"] or "")[:4] in {f"194{year}" for year in range(1, 10)}
        )
        if not unique and not is_pilot:
            continue
        levels = sorted({item["level"] for item in candidate_rows}, key=lambda value: -level_score(value))
        if is_pilot:
            levels = ["PILOT"]
        event_ids = sorted({event_id for item in candidate_rows for event_id in item["event_ids"]})
        event_tags = sorted({tag for item in candidate_rows for tag in item["event_tags"]})
        anchored = int(row["anchored_pages"] or 0)
        image_pages = int(row["image_path_pages"] or 0)
        ratio = anchored / page_count if page_count else 0.0
        source_bonus = 65 if source_pdf_pages else 0
        source_bonus += 20 if image_pages else 0
        score = (
            level_score(levels[0])
            + min(len(event_ids), 3) * 8
            + round(ratio * 24)
            + source_bonus
            + min(int(row["text_chars"] or 0) // 1000, 12)
            + min(page_count, 20) * 3
            - max(page_count - 24, 0)
        )
        candidates[int(row["id"])] = {
            "document_id": int(row["id"]),
            "doc_key": str(row["doc_key"] or ""),
            "title": str(row["title"] or ""),
            "date_guess": str(row["date_guess"] or ""),
            "url": str(row["url"] or ""),
            "volume_title": str(row["volume_title"] or ""),
            "doc_id": str(row["doc_id"] or ""),
            "doc_number": str(row["doc_number"] or ""),
            "source_id": str(row["source_id"] or ""),
            "hit_type": str(row["hit_type"] or ""),
            "page_count": page_count,
            "provenance_pages": int(row["provenance_pages"] or 0),
            "anchored_pages": anchored,
            "image_path_pages": image_pages,
            "pdf_source_pages": source_pdf_pages,
            "text_chars": int(row["text_chars"] or 0),
            "levels": levels,
            "candidate_ids": sorted(unique),
            "candidate_titles": sorted({item["title"] for item in candidate_rows if item["title"]}),
            "repositories": sorted({item["repository_code"] for item in candidate_rows if item["repository_code"]}),
            "event_tags": event_tags,
            "event_ids": event_ids,
            "score": score,
            "selection_basis": "file_backed_ocr_pilot" if is_pilot else "accepted_candidate",
            "review_gate": "hold_until_human_source_comparison",
            "citation_ready": False,
        }
    return candidates


def sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    # A small page-count preference keeps the first human batch reviewable while
    # the level/event/provenance score still controls the selection.
    return (-int(item["score"]), int(item["page_count"]), item["date_guess"] or "9999", item["document_id"])


def compact_sort_key(item: dict[str, Any]) -> tuple[Any, ...]:
    """Prefer representative 3–10 page units while staying within 100–200 pages."""
    page_count = max(int(item["page_count"]), 1)
    size_bonus = min(page_count, 8) * 20 - max(page_count - 10, 0) * 15
    return (
        -(float(item["score"]) + size_bonus),
        int(item["page_count"]),
        item["date_guess"] or "9999",
        item["document_id"],
    )


def select_documents(
    candidates: dict[int, dict[str, Any]],
    event_names: dict[str, str],
    min_documents: int,
    max_documents: int,
    max_pages: int,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    selected_ids: set[int] = set()
    total_pages = 0
    coverage: dict[str, int] = {}

    def add(item: dict[str, Any], force: bool = False) -> bool:
        nonlocal total_pages
        if item["document_id"] in selected_ids or len(selected) >= max_documents:
            return False
        proposed = total_pages + int(item["page_count"])
        if not force and proposed > max_pages:
            return False
        selected.append(item)
        selected_ids.add(item["document_id"])
        total_pages = proposed
        for event_id in item["event_ids"]:
            coverage[event_id] = coverage.get(event_id, 0) + 1
        return True

    # First guarantee that the batch attempts to represent every declared
    # domestic topic.  Overlap is allowed; the report exposes missing topics.
    for event_id in CORE_EVENT_IDS:
        options = sorted(
            (item for item in candidates.values() if event_id in item["event_ids"]),
            key=sort_key,
        )
        if options:
            add(options[0], force=len(selected) < min_documents and total_pages == 0)

    for item in sorted(candidates.values(), key=compact_sort_key):
        if len(selected) >= min_documents:
            break
        if not add(item):
            add(item, force=True)

    compact_candidates = sorted(candidates.values(), key=compact_sort_key)
    for item in compact_candidates:
        if len(selected) >= max_documents:
            break
        if total_pages < 100 or len(selected) < min_documents:
            add(item)

    # If the target page floor was reached before the document ceiling, leave
    # the batch compact.  If it was not reached, add the best fitting records
    # until either the floor or the configured ceiling is reached.
    if total_pages < 100:
        for item in compact_candidates:
            if len(selected) >= max_documents or total_pages >= 100:
                break
            add(item)

    selected.sort(key=lambda item: (-int(item["score"]), item["date_guess"] or "9999", item["document_id"]))
    missing = [event_id for event_id in CORE_EVENT_IDS if not coverage.get(event_id)]
    return selected, {
        "selected_documents": len(selected),
        "selected_pages": total_pages,
        "target_documents": f"{min_documents}-{max_documents}",
        "target_pages": f"100-{max_pages}",
        "event_coverage": {
            event_id: {
                "event_name": event_names.get(event_id, event_id),
                "selected_document_count": coverage.get(event_id, 0),
            }
            for event_id in CORE_EVENT_IDS
        },
        "missing_event_ids": missing,
        "selection_warning": (
            "selected page count exceeds target cap"
            if total_pages > max_pages
            else "selected page count is below 100"
            if total_pages < 100
            else ""
        ),
    }


def build_pages(
    conn: sqlite3.Connection,
    selected: list[dict[str, Any]],
    root: Path,
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    selected_ids = [item["document_id"] for item in selected]
    placeholders = ",".join("?" for _ in selected_ids)
    rows = conn.execute(
        f"""
        SELECT p.id AS page_id, p.document_id, p.page_label, p.page_url,
               length(COALESCE(p.text, '')) AS text_chars,
               pp.source_id, pp.source_file, pp.source_sha256, pp.source_file_size,
               pp.pdf_page_no, pp.physical_page_no, pp.printed_page,
               pp.page_image_path, pp.page_image_sha256, pp.ocr_md_path,
               pp.ocr_engine, pp.ocr_model, pp.ocr_mode, pp.citation_ready,
               pp.needs_human_review, pp.review_status, pp.human_review_note
        FROM pages p
        LEFT JOIN page_provenance pp ON pp.page_id = p.id
        WHERE p.document_id IN ({placeholders})
        ORDER BY p.document_id, p.id
        """,
        selected_ids,
    ).fetchall()
    hash_cache: dict[str, dict[str, Any]] = {}
    page_items: list[dict[str, Any]] = []
    for row in rows:
        raw_source = str(row["source_file"] or "")
        source_path = resolve_local_path(root, raw_source)
        source_key = str(source_path) if source_path else ""
        if source_key not in hash_cache:
            if source_path is None:
                audit = {"status": "missing_path", "resolved_path": "", "actual_sha256": ""}
            elif not source_path.exists():
                audit = {"status": "missing_file", "resolved_path": str(source_path), "actual_sha256": ""}
            elif not source_path.is_file():
                audit = {"status": "not_a_file", "resolved_path": str(source_path), "actual_sha256": ""}
            else:
                try:
                    actual = sha256_file(source_path)
                    expected = str(row["source_sha256"] or "").lower()
                    audit = {
                        "status": "hash_match" if expected and actual == expected else "hash_mismatch" if expected else "no_expected_hash",
                        "resolved_path": str(source_path),
                        "actual_sha256": actual,
                    }
                except OSError as exc:
                    audit = {"status": "unreadable", "resolved_path": str(source_path), "actual_sha256": "", "error": str(exc)}
            hash_cache[source_key] = audit
        audit = hash_cache[source_key]
        image_path = resolve_local_path(root, row["page_image_path"])
        image_exists = bool(image_path and image_path.is_file())
        image_kind = classify_asset(image_path)
        page_items.append(
            {
                "page_id": int(row["page_id"]),
                "document_id": int(row["document_id"]),
                "page_label": str(row["page_label"] or ""),
                "page_url": str(row["page_url"] or ""),
                "text_chars": int(row["text_chars"] or 0),
                "source_id": str(row["source_id"] or ""),
                "source_file": raw_source,
                "source_file_size": row["source_file_size"],
                "source_sha256": str(row["source_sha256"] or ""),
                "source_audit_status": audit["status"],
                "source_actual_sha256": audit.get("actual_sha256", ""),
                "resolved_source_path": audit.get("resolved_path", ""),
                "pdf_page_no": row["pdf_page_no"],
                "physical_page_no": row["physical_page_no"],
                "printed_page": str(row["printed_page"] or ""),
                "page_image_path": str(row["page_image_path"] or ""),
                "page_image_exists": image_exists,
                "page_image_kind": image_kind,
                "ocr_md_path": str(row["ocr_md_path"] or ""),
                "ocr_engine": str(row["ocr_engine"] or ""),
                "ocr_model": str(row["ocr_model"] or ""),
                "ocr_mode": str(row["ocr_mode"] or ""),
                "citation_ready": bool(row["citation_ready"]),
                "needs_human_review": bool(row["needs_human_review"]),
                "review_status": str(row["review_status"] or ""),
                "human_review_recorded": bool(str(row["human_review_note"] or "").strip()),
                "review_gate": "hold_until_human_source_comparison",
            }
        )
    return page_items, hash_cache


def write_outputs(
    out_dir: Path,
    db_path: Path,
    source_root: Path,
    selected: list[dict[str, Any]],
    pages: list[dict[str, Any]],
    audit: dict[str, Any],
    hash_cache: dict[str, dict[str, Any]],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    db_stat = db_path.stat()
    db_sha = sha256_file(db_path)
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "database": {
            "path": str(db_path),
            "size": db_stat.st_size,
            "sha256": db_sha,
        },
        "selection": audit,
        "source_audit": {
            "unique_source_files": len(hash_cache),
            "hash_match": sum(1 for item in hash_cache.values() if item["status"] == "hash_match"),
            "hash_mismatch": sum(1 for item in hash_cache.values() if item["status"] == "hash_mismatch"),
            "missing_file": sum(1 for item in hash_cache.values() if item["status"] == "missing_file"),
            "ocr_or_text_page_image_paths": sum(1 for item in pages if item["page_image_kind"] == "ocr_or_text"),
            "actual_image_page_paths": sum(1 for item in pages if item["page_image_kind"] == "image" and item["page_image_exists"]),
            "pdf_source_pages": sum(1 for item in pages if classify_asset(resolve_local_path(source_root, item["source_file"])) == "pdf"),
            "source_root": str(source_root),
        },
        "documents": selected,
        "pages": pages,
        "citation_ready_count": sum(1 for item in pages if item["citation_ready"]),
        "human_review_record_count": sum(1 for item in pages if item["human_review_recorded"]),
        "body_text_included": False,
    }
    (out_dir / "BATCH.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    document_fields = [
        "document_id", "doc_key", "title", "date_guess", "source_id", "hit_type", "page_count",
        "provenance_pages", "anchored_pages", "image_path_pages", "pdf_source_pages", "text_chars",
        "levels", "candidate_ids", "repositories", "event_tags", "event_ids", "score", "selection_basis",
        "review_gate", "citation_ready",
    ]
    with (out_dir / "DOCUMENTS.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=document_fields, lineterminator="\n")
        writer.writeheader()
        for item in selected:
            row = dict(item)
            for key in ("levels", "candidate_ids", "repositories", "event_tags", "event_ids"):
                row[key] = ";".join(str(value) for value in item[key])
            writer.writerow({key: row.get(key, "") for key in document_fields})

    page_fields = [
        "page_id", "document_id", "page_label", "page_url", "text_chars", "source_id", "source_file",
        "source_file_size", "source_sha256", "source_audit_status", "source_actual_sha256",
        "resolved_source_path", "pdf_page_no", "physical_page_no", "printed_page", "page_image_path",
        "page_image_exists", "page_image_kind", "ocr_md_path", "ocr_engine", "ocr_model", "ocr_mode",
        "citation_ready", "needs_human_review", "review_status", "human_review_recorded", "review_gate",
    ]
    with (out_dir / "PAGES.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=page_fields, lineterminator="\n")
        writer.writeheader()
        for item in pages:
            writer.writerow({key: item.get(key, "") for key in page_fields})

    event_lines = []
    for event_id, item in audit["event_coverage"].items():
        status = "覆盖" if item["selected_document_count"] else "缺口"
        event_lines.append(f"| {event_id} | {item['event_name']} | {item['selected_document_count']} | {status} |")
    status_counts: dict[str, int] = defaultdict(int)
    for item in pages:
        status_counts[item["source_audit_status"]] += 1
    lines = [
        "# 国内核心引用批次（元数据审计队列）",
        "",
        "本目录由 `scripts/domestic/build_core_citation_batch_20260813.py` 只读生成。它是人工页级复核队列，不是正式引用库，也不会修改 SQLite。",
        "",
        f"- 生成时间（UTC）：`{generated_at}`",
        f"- 数据库 SHA256：`{db_sha}`",
        f"- 文档：`{audit['selected_documents']}` 篇；页：`{audit['selected_pages']}` 页",
        f"- 目标：20–30 篇、100–200 页；选择提示：{audit['selection_warning'] or '在目标范围内'}",
        f"- `citation_ready`：`0`（当前批次不自动升级）",
        f"- 正文是否写入报告：`否`",
        "",
        "## 九个专题覆盖",
        "",
        "| event_id | 专题 | 批次文档数 | 状态 |",
        "|---|---|---:|---|",
        *event_lines,
        "",
        "## 来源审计",
        "",
        "| 状态 | 页数 |",
        "|---|---:|",
        *[f"| {key} | {value} |" for key, value in sorted(status_counts.items())],
        "",
        "页级复核顺序：",
        "",
        "1. 先打开 `PAGES.csv` 中对应的 `resolved_source_path` 或 `page_url`，对照原 PDF/原图，不凭 OCR 单独下结论。",
        "2. 核对题名、日期、形成者、页码/版面、正文边界；特别标出 `page_image_kind=ocr_or_text` 的记录，它们没有被证明是原图。",
        "3. `selection_basis=file_backed_ocr_pilot` 表示已有本地 PDF 作为待核原件，但仍不是人工核验结论；不能把试点 OCR 当正式引用。",
        "4. 只有完成来源对照、来源文件哈希匹配、页码可定位并填写人工说明后，才允许通过平台的国内证据复核页进入 `human_verified`。",
        "5. 本批次的 JSON/CSV 不含正文；如需对照正文，请通过平台页面或本地原件打开。",
        "",
        "## 下一阶段",
        "",
        "先完成本批次的页级来源核对，再把有明确原件定位的页升级为正式引用；其余继续保持机器可阅/待核状态。任何缺少原图或原 PDF 的条目继续列入缺口，不用 OCR 结果替代原件。",
    ]
    (out_dir / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--min-documents", type=int, default=20)
    parser.add_argument("--max-documents", type=int, default=30)
    parser.add_argument("--max-pages", type=int, default=200)
    args = parser.parse_args()
    if args.min_documents < 1 or args.max_documents < args.min_documents or args.max_pages < 1:
        parser.error("invalid batch limits")

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    source_root = args.db.resolve().parent.parent
    candidate_events, event_names = load_coverage(COVERAGE_PATH)
    candidates = build_candidates(conn, candidate_events)
    selected, audit = select_documents(
        candidates,
        event_names,
        min_documents=args.min_documents,
        max_documents=args.max_documents,
        max_pages=args.max_pages,
    )
    pages, hash_cache = build_pages(conn, selected, source_root)
    conn.close()
    write_outputs(args.out_dir, args.db, source_root, selected, pages, audit, hash_cache)
    print(
        json.dumps(
            {
                "candidates": len(candidates),
                "selected_documents": len(selected),
                "selected_pages": len(pages),
                "selection_warning": audit["selection_warning"],
                "missing_event_ids": audit["missing_event_ids"],
                "out_dir": str(args.out_dir),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
