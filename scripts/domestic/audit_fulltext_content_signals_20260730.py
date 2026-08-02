#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspect text-layer signals of the seven distinct crosswalk fulltexts."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

try:
    import fitz  # type: ignore
except ImportError:
    fitz = None
try:
    from pypdf import PdfReader  # type: ignore
except ImportError:
    PdfReader = None


ROOT = Path(__file__).resolve().parents[2]
INPUT = ROOT / "work/domestic/staging_20260730/crosswalk_material_review_queue/FULLTEXT_FIRST.jsonl"
OUT = ROOT / "work/domestic/staging_20260730/crosswalk_fulltext_content_audit"


def visible_html(raw: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw))).strip()


def title_runs(title: str) -> list[str]:
    return [run for run in re.findall(r"[\u3400-\u9fff]{4,}|[A-Za-z]{5,}", title or "")]


def pdf_text(path: Path) -> tuple[int, str]:
    if fitz is not None:
        doc = fitz.open(path)
        text = "\n".join(page.get_text("text") for page in doc)
        pages = len(doc)
        doc.close()
        return pages, text
    if PdfReader is not None:
        reader = PdfReader(str(path))
        return len(reader.pages), "\n".join(page.extract_text() or "" for page in reader.pages)
    return 0, ""


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [json.loads(line) for line in INPUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    results = []
    status_counts = Counter()
    for row in rows:
        path = Path(row["local_path"])
        if not path.is_absolute():
            path = ROOT / path
        pages = 0
        text = ""
        file_kind = path.suffix.lower()
        if path.exists() and file_kind == ".pdf":
            pages, text = pdf_text(path)
        elif path.exists() and file_kind in (".html", ".htm"):
            pages = 1
            text = visible_html(path.read_text(encoding="utf-8", errors="replace"))
        normalized = re.sub(r"\s+", "", text)
        runs = title_runs(row["material_title"])
        title_hits = [run for run in runs if re.sub(r"\s+", "", run) in normalized]
        key_terms = [term for term in ("民主同盟", "民盟", "政治协商", "1941", "1946", "1947", "1949") if term in text]
        # A PDF can contain a tiny metadata/header text layer while its pages
        # are actually image-only. Treat very low text density as unusable;
        # this is a signal gate, not a citation decision.
        min_expected_chars = max(200, pages * 20) if file_kind == ".pdf" else 200
        if not text.strip():
            status = "HOLD_NO_TEXT_LAYER"
        elif file_kind == ".pdf" and len(text.strip()) < min_expected_chars:
            status = "HOLD_WEAK_TEXT_LAYER"
        elif title_hits:
            status = "CONTENT_TEXT_AND_TITLE_SIGNAL_PASS"
        else:
            status = "CONTENT_TEXT_PASS_TITLE_UNCONFIRMED"
        status_counts[status] += 1
        results.append({
            "material_external_id": row["material_external_id"],
            "material_title": row["material_title"],
            "fulltext_status": row["fulltext_status"],
            "file_kind": file_kind,
            "page_count": pages,
            "text_char_count": len(text),
            "text_density_gate_min_chars": min_expected_chars,
            "title_runs": runs,
            "title_signal_hits": title_hits,
            "key_term_hits": key_terms,
            "content_status": status,
            "citation_ready": 0,
            "human_verified": 0,
        })
    report = {
        "run_id": "crosswalk_fulltext_content_audit_20260730",
        "input_objects": len(rows),
        "status_counts": dict(status_counts),
        "pdf_parser": "fitz" if fitz is not None else "pypdf" if PdfReader is not None else "unavailable",
        "citation_ready": 0,
        "human_verified": 0,
        "body_excerpts_persisted": False,
        "formal_db_written": False,
    }
    (OUT / "CONTENT_SIGNALS.jsonl").write_text("\n".join(json.dumps(item, ensure_ascii=False) for item in results) + "\n", encoding="utf-8")
    (OUT / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
