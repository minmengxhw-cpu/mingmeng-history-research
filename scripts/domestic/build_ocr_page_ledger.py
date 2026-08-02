#!/usr/bin/env python3
"""Build a page-level quality ledger for domestic OCR records."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_SHA_SUPPLEMENT = ROOT / "work" / "domestic" / "minimax_two_month_20260730" / "w2" / "SOURCE_SHA_SUPPLEMENT.jsonl"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_manifests(root: Path) -> dict[tuple[str, str], list[dict]]:
    result: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for path in sorted(root.rglob("*.jsonl")):
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeDecodeError):
            continue
        for line in lines:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            record_id = str(row.get("record_id", "")).strip()
            if not record_id:
                continue
            pages = row.get("pages", [])
            if not isinstance(pages, list):
                continue
            for page in pages:
                if not isinstance(page, dict):
                    # Historical manifests contain a small number of legacy
                    # string placeholders. They are not page bindings and
                    # must not abort the read-only ledger build.
                    continue
                label = str(page.get("page_label", "")).strip()
                if label:
                    result[(record_id, label)].append(
                        {
                            "source_path": row.get("source_path", ""),
                            "source_sha256": row.get("source_sha256", ""),
                            "source_kind": row.get("source_kind", ""),
                            "source_url": row.get("source_url", ""),
                            "event_tags": row.get("event_tags", []),
                            "ocr_markdown": page.get("ocr_markdown", ""),
                            "manifest_path": str(path),
                        }
                    )
    return result


def tag_value(tags: str, key: str) -> str:
    match = re.search(rf"(?:^|,){re.escape(key)}=([^,]*)", tags or "")
    return match.group(1).strip() if match else ""


def read_sha_supplement(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    result: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        source_path = str(row.get("source_path", "")).strip()
        source_sha = str(row.get("source_sha256", "")).strip()
        if source_path and source_sha:
            result[source_path] = source_sha
    return result


def period(date_guess: str) -> str:
    year_match = re.match(r"(\d{4})", date_guess or "")
    if not year_match:
        return "未定年"
    year = int(year_match.group(1))
    if year <= 1941:
        return "1941及以前"
    if year <= 1943:
        return "1942-1943"
    if year <= 1945:
        return "1944-1945"
    if year == 1946:
        return "1946"
    if year == 1947:
        return "1947"
    if year <= 1949:
        return "1948-1949"
    return "1950以后"


def priority(confidence: float | None, title: str, tags: str) -> str:
    high_value = any(
        marker in f"{title} {tags}"
        for marker in ("成立", "一大", "民主政治", "政协", "宪政", "观察", "大公", "光明")
    )
    if confidence is not None and confidence < 0.60:
        return "P0"
    if confidence is not None and confidence < 0.80:
        return "P0" if high_value else "P1"
    if high_value and confidence is not None and confidence < 0.90:
        return "P1"
    return "P2"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--manifest-root", type=Path, default=Path("work/domestic"))
    parser.add_argument("--sha-supplement", type=Path, default=DEFAULT_SHA_SUPPLEMENT)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--output-md", type=Path, required=True)
    parser.add_argument("--output-json", type=Path, required=True)
    args = parser.parse_args()

    project = Path.cwd().resolve()
    db_path = args.db if args.db.is_absolute() else project / args.db
    manifest_root = args.manifest_root if args.manifest_root.is_absolute() else project / args.manifest_root
    sha_supplement_path = args.sha_supplement if args.sha_supplement.is_absolute() else project / args.sha_supplement
    manifests = read_manifests(manifest_root)
    sha_supplement = read_sha_supplement(sha_supplement_path)
    source_hashes: dict[str, str] = {}
    rows: list[dict[str, object]] = []

    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        query = """
            SELECT p.id AS page_id, d.id AS document_id, d.doc_key, d.title,
                   d.date_guess, d.local_txt, d.source_id, p.page_label,
                   length(p.text) AS text_chars, f.matched_terms,
                   s.origin_url, s.local_path AS source_local_path
            FROM pages p
            JOIN documents d ON d.id=p.document_id
            LEFT JOIN page_fts f ON f.rowid=p.id
            LEFT JOIN sources s ON s.id=d.source_id
            WHERE d.source_platform='domestic'
            ORDER BY d.date_guess, d.id, p.id
        """
        for item in conn.execute(query):
            tags = item["matched_terms"] or ""
            confidence_text = tag_value(tags, "ocr_mean_confidence")
            confidence = float(confidence_text) if confidence_text else None
            record_id = item["doc_key"].removeprefix("domestic-ocr/")
            bound = manifests.get((record_id, str(item["page_label"])), [])
            manifest = bound[0] if bound else {}
            source_path = str(item["source_local_path"] or manifest.get("source_path", ""))
            actual_sha = ""
            source_file = Path(source_path)
            if not source_file.is_absolute():
                source_file = project / source_file
            if source_path and source_file.is_file():
                if source_path not in source_hashes:
                    source_hashes[source_path] = sha256(source_file)
                actual_sha = source_hashes[source_path]
            expected_sha = str(manifest.get("source_sha256", ""))
            supplement_sha = sha_supplement.get(source_path, "")
            effective_expected_sha = expected_sha or supplement_sha
            if actual_sha and effective_expected_sha and actual_sha == effective_expected_sha:
                sha_status = "verified" if expected_sha else "verified_staging_supplement"
            elif actual_sha and not expected_sha:
                sha_status = "manifest_sha_missing" if not supplement_sha else "staging_supplement_mismatch"
            elif not actual_sha:
                sha_status = "source_missing"
            else:
                sha_status = "sha_mismatch"
            status = tag_value(tags, "ocr_page_status") or "untagged"
            rows.append(
                {
                    "page_id": item["page_id"],
                    "document_id": item["document_id"],
                    "doc_key": item["doc_key"],
                    "record_id": record_id,
                    "title": item["title"] or "",
                    "date_guess": item["date_guess"] or "",
                    "period": period(item["date_guess"] or ""),
                    "page_label": item["page_label"] or "",
                    "text_chars": item["text_chars"] or 0,
                    "ocr_mean_confidence": confidence_text,
                    "ocr_page_status": status,
                    "ocr_status": tag_value(tags, "ocr_status") or "unknown",
                    "review_priority": priority(confidence, item["title"] or "", tags),
                    "source_path": source_path,
                    "source_sha256": actual_sha,
                    "manifest_sha256": expected_sha,
                    "staging_supplement_sha256": supplement_sha,
                    "sha_status": sha_status,
                    "source_url": manifest.get("source_url", item["origin_url"] or ""),
                    "source_kind": manifest.get("source_kind", ""),
                    "event_tags": "；".join(manifest.get("event_tags", [])) if isinstance(manifest.get("event_tags", []), list) else str(manifest.get("event_tags", "")),
                    "ocr_markdown": manifest.get("ocr_markdown", ""),
                    "manifest_path": manifest.get("manifest_path", ""),
                }
            )

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0]) if rows else []
    with args.output_csv.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    args.output_json.write_text(json.dumps({"generated_at": datetime.now().isoformat(timespec="seconds"), "pages": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    counts = defaultdict(int)
    for row in rows:
        counts[str(row["review_priority"])] += 1
    status_counts = defaultdict(int)
    sha_counts = defaultdict(int)
    for row in rows:
        status_counts[str(row["ocr_page_status"])] += 1
        sha_counts[str(row["sha_status"])] += 1
    lines = [
        "# 国内 OCR 页级质量账本",
        "",
        f"生成时间：{datetime.now().isoformat(timespec='seconds')}",
        "",
        f"页面总数：{len(rows)}；优先级：" + "、".join(f"{key} {counts[key]}" for key in ("P0", "P1", "P2")),
        f"OCR 状态：" + "、".join(f"{key} {status_counts[key]}" for key in sorted(status_counts)),
        f"来源 SHA256：" + "、".join(f"{key} {sha_counts[key]}" for key in sorted(sha_counts)),
        "",
        "## 使用规则",
        "",
        "- P0/P1 只代表复核优先级，不代表文本已经可以逐字引用。",
        "- `verified` 表示当前来源文件与原始 manifest SHA256 一致；`verified_staging_supplement` 表示通过独立 staging 补充 manifest 验证；其余 SHA 状态必须在导入前处理。",
        "- 原始 OCR 保留不变，修订文本另存并记录差异。",
        "",
        "## 复核优先级",
        "",
    ]
    for row in rows:
        if row["review_priority"] in {"P0", "P1"}:
            lines.append(f"- {row['review_priority']}：page_id={row['page_id']}；{row['title']}；p.{row['page_label']}；置信度={row['ocr_mean_confidence'] or 'NA'}；{row['period']}")
    args.output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"pages": len(rows), "priority": dict(counts), "ocr_status": dict(status_counts), "sha_status": dict(sha_counts), "csv": str(args.output_csv), "md": str(args.output_md), "json": str(args.output_json)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
