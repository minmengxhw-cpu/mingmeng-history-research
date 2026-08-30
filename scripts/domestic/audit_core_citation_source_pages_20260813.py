#!/usr/bin/env python3
"""Audit source-file and page-locator readiness for the core PDF batch.

This is a read-only audit.  It does not change SQLite and never includes page
body text in its output.  A page is eligible for a later visual review only if
the local PDF hash matches, the page URL has an exact ``#page=N`` locator, and
the OCR row does not look like a whole-book/chunk collapse.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BATCH = ROOT / "work" / "domestic" / "core_citation_batch_20260813" / "BATCH.json"
DEFAULT_OUT = ROOT / "work" / "domestic" / "core_citation_batch_20260813" / "VISUAL_REVIEW.json"
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_root_for(db_path: Path) -> Path:
    return db_path.resolve().parent.parent


def resolve_source(root: Path, raw: str) -> Path:
    path = Path(raw).expanduser()
    return path if path.is_absolute() else root / path


def page_locator(page_url: str, expected_page: int | None) -> dict[str, object]:
    fragment = urlsplit(page_url or "").fragment
    match = re.fullmatch(r"page=0*(\d+)(?:-0*(\d+))?", fragment)
    if not match:
        return {"type": "missing_or_non_page", "fragment": fragment, "exact": False}
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else None
    if end is None:
        return {
            "type": "exact_page",
            "fragment": fragment,
            "start": start,
            "end": start,
            "exact": expected_page is not None and start == expected_page,
        }
    return {
        "type": "range_locator",
        "fragment": fragment,
        "start": start,
        "end": end,
        "exact": False,
    }


def audit_pages(batch: dict, source_root: Path, render_dir: Path | None) -> tuple[list[dict], dict]:
    cache: dict[str, dict[str, str]] = {}
    pages: list[dict] = []
    for item in batch.get("pages", []):
        raw_source = str(item.get("source_file") or "")
        source_path = resolve_source(source_root, raw_source) if raw_source else None
        cache_key = str(source_path) if source_path else ""
        if cache_key not in cache:
            if source_path is None:
                cache[cache_key] = {"status": "missing_path", "actual_sha256": "", "resolved": ""}
            elif not source_path.is_file():
                cache[cache_key] = {"status": "missing_file", "actual_sha256": "", "resolved": str(source_path)}
            else:
                actual = sha256_file(source_path)
                expected = str(item.get("source_sha256") or "").lower()
                cache[cache_key] = {
                    "status": "hash_match" if expected and actual == expected else "hash_mismatch" if expected else "no_expected_hash",
                    "actual_sha256": actual,
                    "resolved": str(source_path),
                }
        source_audit = cache[cache_key]
        expected_page = int(item["pdf_page_no"]) if str(item.get("pdf_page_no") or "").isdigit() else None
        locator = page_locator(str(item.get("page_url") or ""), expected_page)
        render_path = ""
        rendered = None
        if render_dir and expected_page is not None:
            stem = Path(raw_source).stem.replace(" ", "_")
            render_file = render_dir / f"{stem}__p{expected_page:04d}.png"
            render_path = str(render_file)
            rendered = render_file.is_file()
        flags: list[str] = []
        if not raw_source.lower().endswith(".pdf"):
            flags.append("source_is_not_pdf")
        if source_audit["status"] != "hash_match":
            flags.append(f"source_{source_audit['status']}")
        if locator["type"] != "exact_page":
            flags.append(locator["type"])
        elif not locator["exact"]:
            flags.append("page_locator_mismatch")
        if int(item.get("text_chars") or 0) > 12000:
            flags.append("possible_whole_book_or_chunk_text")
        if rendered is False:
            flags.append("rendered_page_missing")
        eligible = not flags or flags == ["rendered_page_missing"]
        pages.append(
            {
                "page_id": int(item["page_id"]),
                "document_id": int(item["document_id"]),
                "page_label": str(item.get("page_label") or ""),
                "title": str(next((doc.get("title") for doc in batch.get("documents", []) if int(doc["document_id"]) == int(item["document_id"])), "")),
                "source_file": raw_source,
                "resolved_source_path": source_audit["resolved"],
                "source_sha256": str(item.get("source_sha256") or ""),
                "source_actual_sha256": source_audit["actual_sha256"],
                "source_audit_status": source_audit["status"],
                "pdf_page_no": expected_page,
                "physical_page_no": item.get("physical_page_no"),
                "printed_page": item.get("printed_page"),
                "page_url": str(item.get("page_url") or ""),
                "locator": locator,
                "text_chars": int(item.get("text_chars") or 0),
                "rendered_page_path": render_path,
                "rendered_page_exists": rendered,
                "flags": flags,
                "eligible_for_visual_review": eligible,
                "review_status": "pending",
            }
        )
    counts = Counter(
        "eligible" if page["eligible_for_visual_review"] else page["flags"][0] if page["flags"] else "unknown"
        for page in pages
    )
    return pages, {
        "pages": len(pages),
        "eligible_for_visual_review": sum(1 for page in pages if page["eligible_for_visual_review"]),
        "held_out": sum(1 for page in pages if not page["eligible_for_visual_review"]),
        "status_counts": dict(sorted(counts.items())),
        "source_files": len(cache),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch", type=Path, default=DEFAULT_BATCH)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--render-dir", type=Path)
    args = parser.parse_args()
    batch = json.loads(args.batch.read_text(encoding="utf-8"))
    pages, counts = audit_pages(batch, source_root_for(args.db), args.render_dir)
    payload = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "database": batch.get("database", {}),
        "batch_selection": batch.get("selection", {}),
        "audit": counts,
        "body_text_included": False,
        "pages": pages,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"out": str(args.out), **counts}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
