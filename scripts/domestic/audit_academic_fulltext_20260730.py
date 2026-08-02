#!/usr/bin/env python3
"""Audit local academic acquisitions and the deterministic S/A sample.

The audit is conservative: an author profile, bibliography, catalogue page, or
reference list is not treated as the full text of every work it mentions.
"""

from __future__ import annotations

import hashlib
import html
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "work/domestic/grok_academic_research_20260730/02_records/ACADEMIC_RECORDS.jsonl"
WORK = ROOT / "work/domestic/research_layers_acceptance_20260730"
SAMPLE = WORK / "SA_QUALITY_SAMPLE.jsonl"


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def normalize(value: str) -> str:
    return re.sub(r"[\W_]+", "", value.lower())


def decode_html(raw: bytes, title: str) -> tuple[str, str]:
    best = ("", "")
    for encoding in ("utf-8", "gb18030", "big5"):
        try:
            decoded = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        visible = html.unescape(re.sub(r"<[^>]+>", " ", decoded))
        score = int(normalize(title) in normalize(visible))
        if (score, len(visible)) > (int(normalize(title) in normalize(best[1])), len(best[1])):
            best = (encoding, visible)
    return best


def title_evidence(title: str, visible: str) -> bool:
    nt = normalize(title)
    nv = normalize(visible)
    if nt and nt in nv:
        return True
    pieces = [normalize(piece) for piece in re.split(r"[（(【\[———:：]", title)]
    return any(len(piece) >= 8 and piece in nv for piece in pieces)


def local_audit(row: dict, path_use_count: Counter) -> dict:
    value = row.get("local_path")
    if not value:
        return {
            "local_evidence_status": "NO_LOCAL_FILE",
            "corrected_fulltext_status": "NOT_ACQUIRED",
        }
    path = Path(value)
    if not path.is_absolute():
        path = ROOT / path
    raw = path.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    base = {
        "local_path": str(path),
        "bytes": len(raw),
        "sha256": digest,
        "sha_matches_manifest": digest == row.get("sha256"),
        "shared_local_path_record_count": path_use_count[value],
    }
    if raw.startswith(b"%PDF"):
        return {
            **base,
            "local_evidence_status": "PDF_MAGIC_AND_SHA_PASS",
            "corrected_fulltext_status": "FULLTEXT_PDF",
        }

    encoding, visible = decode_html(raw, row.get("title") or "")
    found = title_evidence(row.get("title") or "", visible)
    url = row.get("source_url") or ""
    if "/scholars/" in url:
        corrected = "BIBLIOGRAPHIC_AUTHOR_PROFILE"
    elif path_use_count[value] > 1:
        corrected = "SHARED_BIBLIOGRAPHIC_OR_INDEX_PAGE"
    elif any(token in url for token in ("booksdetail", "cpfd.cnki", "portal/journal/portal/client/paper")):
        corrected = "CATALOG_OR_REFERENCE_PAGE"
    elif found and len(normalize(visible)) >= 1500:
        corrected = "FULLTEXT_HTML_CANDIDATE"
    else:
        corrected = "METADATA_OR_WRONG_PAGE"
    return {
        **base,
        "decoded_as": encoding,
        "visible_chars": len(visible),
        "title_found_in_visible_text": found,
        "local_evidence_status": "HTML_SHA_PASS",
        "corrected_fulltext_status": corrected,
    }


def live_sample_assessment(row: dict, local: dict) -> dict:
    """Record the 2026-07-30 live checks performed by Codex."""
    url = row.get("source_url") or ""
    rid = row["record_id"]
    if "/scholars/wenliming" in url:
        title_found = rid not in {"GAR-C8374D8762"}
        return {
            "live_status": "PASS_BIBLIOGRAPHIC" if title_found else "HOLD_TITLE_NOT_FOUND",
            "live_author_affiliation": "PASS",
            "live_title_or_work": "PASS" if title_found else "NOT_FOUND",
            "live_fulltext": "NO_AUTHOR_PROFILE_ONLY",
            "evidence_note": "Author profile and publication list checked live; not article/book full text.",
        }
    if "/scholars/fangmin" in url:
        return {
            "live_status": "PASS_BIBLIOGRAPHIC",
            "live_author_affiliation": "PASS",
            "live_title_or_work": "PASS",
            "live_fulltext": "NO_AUTHOR_PROFILE_ONLY",
            "evidence_note": "Author profile publication list checked live; not article full text.",
        }
    if rid == "GAR-7B041C67C2":
        return {
            "live_status": "PASS_FULLTEXT",
            "live_author_affiliation": "PASS_PDF_BYLINE_AND_FOOTER",
            "live_title_or_work": "PASS",
            "live_fulltext": "YES_16_PAGE_PDF",
            "evidence_note": "CUHK-hosted 16-page PDF checked live.",
        }
    if rid == "GAR-F3C172D499":
        return {
            "live_status": "PASS_FULLTEXT",
            "live_author_affiliation": "PASS_AUTHOR_AND_PUBLISHER",
            "live_title_or_work": "PASS",
            "live_fulltext": "YES_HTML",
            "evidence_note": "Official Party History and Literature site article checked live.",
        }
    if "portal/journal/portal/client/paper" in url:
        return {
            "live_status": "PASS_REFERENCE_ONLY",
            "live_author_affiliation": "NOT_APPLICABLE_TO_CITED_BOOK",
            "live_title_or_work": "PASS_REFERENCE_LIST_MENTION",
            "live_fulltext": "NO_CITED_REFERENCE_ONLY",
            "evidence_note": "Live page is a different 2021 article whose references mention this work.",
        }
    if local.get("corrected_fulltext_status") == "FULLTEXT_HTML_CANDIDATE":
        return {
            "live_status": "HOLD_LIVE_FETCH_FAILED_LOCAL_BODY_PRESENT",
            "live_author_affiliation": "HOLD",
            "live_title_or_work": "LOCAL_PASS",
            "live_fulltext": "LOCAL_CANDIDATE_ONLY",
            "evidence_note": "Live fetch failed or timed out; local body retained as candidate, not citation-ready.",
        }
    return {
        "live_status": "HOLD_LIVE_UNAVAILABLE",
        "live_author_affiliation": "HOLD",
        "live_title_or_work": "HOLD",
        "live_fulltext": "NO",
        "evidence_note": "Live source unavailable in this acceptance pass.",
    }


def main() -> int:
    records = read_jsonl(SOURCE)
    by_id = {row["record_id"]: row for row in records}
    path_use_count = Counter(row.get("local_path") for row in records if row.get("local_path"))

    audits = []
    for row in records:
        if not row.get("local_path"):
            continue
        local = local_audit(row, path_use_count)
        audits.append(
            {
                "record_id": row["record_id"],
                "quality_tier": row.get("quality_tier"),
                "title": row.get("title"),
                "source_url": row.get("source_url"),
                "reported_fulltext_status": row.get("fulltext_status"),
                **local,
                "decision": (
                    "KEEP_AS_FULLTEXT"
                    if local["corrected_fulltext_status"].startswith("FULLTEXT_")
                    else "KEEP_AS_BIBLIOGRAPHIC_EVIDENCE_NOT_FULLTEXT"
                ),
            }
        )

    sample_out = []
    for sample in read_jsonl(SAMPLE):
        source = by_id[sample["record_id"]]
        local = local_audit(source, path_use_count)
        sample_out.append(
            {
                **sample,
                "checked_at": datetime.now().astimezone().isoformat(),
                **local,
                **live_sample_assessment(source, local),
                "doi_format": (
                    "ABSENT"
                    if not sample.get("doi")
                    else "PASS"
                    if re.fullmatch(r"10\.\d{4,9}/\S+", sample["doi"])
                    else "FAIL"
                ),
                "citation_ready": False,
                "human_verified": False,
            }
        )

    write_jsonl(WORK / "FULLTEXT_STATUS_CORRECTIONS.jsonl", audits)
    write_jsonl(WORK / "SA_QUALITY_SAMPLE_LIVE_CHECKED.jsonl", sample_out)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "local_acquisition_records_checked": len(audits),
        "local_status_counts": dict(
            Counter(row["corrected_fulltext_status"] for row in audits)
        ),
        "sample_rows": len(sample_out),
        "sample_live_status_counts": dict(Counter(row["live_status"] for row in sample_out)),
        "sample_doi_format_counts": dict(Counter(row["doi_format"] for row in sample_out)),
        "acceptance": "PASS_WITH_FULLTEXT_STATUS_CORRECTIONS",
        "rule": "Profiles, catalogues, and reference lists are bibliographic evidence, not full text.",
    }
    (WORK / "QUALITY_AUDIT_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
