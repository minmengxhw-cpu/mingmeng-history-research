#!/usr/bin/env python3
"""Validate the body-free GAR-639 page-identity candidate map.

The candidate map records a proposed continuous printed-page offset for an
already indexed 622-page OCR document.  A small explicit subset has since been
registered from a dated visual-review manifest.  This validator keeps the
full-range offset on hold while checking that only those 17 reviewed pages
are registered in ``page_provenance.printed_page``.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_REUSE_MAP = ROOT / "data" / "domestic" / "academic_formal_reuse_map.json"
DEFAULT_MAP = ROOT / "data" / "domestic" / "academic_gar639_page_identity_candidate.json"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
FORBIDDEN_MARKERS = (
    "/Users/",
    "/private/",
    "/tmp/",
    "file://",
    '"local_path"',
    '"source_file"',
    '"page_image_path"',
    '"derived_text_path"',
)
EXPLICIT_MANIFEST = "data/domestic/mmhist_1946_pcc_page_identity_review_20260822.json"
EXPLICIT_PAIRS = (
    (145, "115"),
    (147, "117"),
    (148, "118"),
    (149, "119"),
    (150, "120"),
    (151, "121"),
    (152, "122"),
    (153, "123"),
    (157, "127"),
    (158, "128"),
    (159, "129"),
    (160, "130"),
    (161, "131"),
    (162, "132"),
    (163, "133"),
    (164, "134"),
    (165, "135"),
)


def load_json(path: Path, label: str) -> tuple[Any, list[str]]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"{label} unreadable: {exc}"]


def integer(value: Any, label: str, errors: list[str], *, minimum: int = 0) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        errors.append(f"{label} must be an integer")
        return minimum - 1
    if result < minimum:
        errors.append(f"{label} must be >= {minimum}")
    return result


def validate(
    db_path: Path = DEFAULT_DB,
    reuse_map_path: Path = DEFAULT_REUSE_MAP,
    candidate_path: Path = DEFAULT_MAP,
) -> dict[str, Any]:
    errors: list[str] = []
    payload, load_errors = load_json(candidate_path, "GAR-639 page-identity candidate")
    errors.extend(load_errors)
    reuse_map, reuse_errors = load_json(reuse_map_path, "academic reuse map")
    errors.extend(reuse_errors)
    if not isinstance(payload, dict):
        errors.append("GAR-639 page-identity candidate must be an object")
        payload = {}
    if payload.get("schema_version") != "domestic_academic_gar639_page_identity_candidate.v1":
        errors.append("unsupported GAR-639 page-identity candidate schema")
    for field in ("body_text_included", "formal_db_written", "local_paths_included", "auto_delete"):
        if payload.get(field) is not False:
            errors.append(f"candidate {field} must be false")
    serialized = json.dumps(payload, ensure_ascii=False)
    for marker in FORBIDDEN_MARKERS:
        if marker in serialized:
            errors.append(f"candidate contains forbidden local/body marker: {marker}")

    expected = {
        "external_id": "GAR-639C5E94AE",
        "source_sha256": "257bb7be70abe374be9864ec451b5a4a90e2442ae8c877b15f4e6bbb8bb30be3",
        "existing_source_type": "domestic_page_ocr",
        "existing_source_id": "domestic-page-ocr/SRC-257bb7be70",
        "existing_doc_key": "domestic-page/SRC-257bb7be70",
    }
    for field, value in expected.items():
        if str(payload.get(field) or "") != value:
            errors.append(f"candidate {field} mismatch")
    if not SHA256_RE.fullmatch(str(payload.get("source_sha256") or "")):
        errors.append("candidate source_sha256 is invalid")

    reuse_records = reuse_map.get("records") if isinstance(reuse_map, dict) else []
    reuse = next(
        (
            record
            for record in reuse_records
            if isinstance(record, dict) and record.get("external_id") == "GAR-639C5E94AE"
        ),
        None,
    )
    if reuse is None:
        errors.append("GAR-639 reuse record is absent")
    else:
        for field in ("source_sha256", "existing_source_type", "existing_source_id", "existing_doc_key"):
            if str(payload.get(field) or "") != str(reuse.get(field) or ""):
                errors.append(f"candidate/reuse map drift: {field}")

    identity = payload.get("database_identity") if isinstance(payload.get("database_identity"), dict) else {}
    candidate = payload.get("candidate_mapping") if isinstance(payload.get("candidate_mapping"), dict) else {}
    for field, expected_value in (
        ("page_count", 622),
        ("pdf_page_min", 1),
        ("pdf_page_max", 622),
        ("physical_page_min", 1),
        ("physical_page_max", 622),
        ("printed_page_registered_count", len(EXPLICIT_PAIRS)),
        ("page_label_printed_count", 17),
        ("citation_ready_page_count", 24),
    ):
        if integer(identity.get(field), f"database_identity.{field}", errors) != expected_value:
            errors.append(f"database_identity.{field} expected {expected_value}")
    if candidate.get("status") != "CANDIDATE_NOT_REGISTERED":
        errors.append("candidate mapping status must remain CANDIDATE_NOT_REGISTERED")
    if candidate.get("status_scope") != "full_range":
        errors.append("candidate mapping status_scope must be full_range")
    if candidate.get("explicit_subset_status") != "PARTIAL_EXPLICIT_REGISTRATION":
        errors.append("candidate mapping explicit_subset_status must be PARTIAL_EXPLICIT_REGISTRATION")
    if candidate.get("formula") != "printed_page = pdf_page_no - 30":
        errors.append("candidate mapping formula mismatch")
    for field, expected_value in (
        ("pdf_page_start", 31),
        ("pdf_page_end", 622),
        ("printed_page_start", 1),
        ("printed_page_end", 592),
        ("offset", -30),
    ):
        if integer(candidate.get(field), f"candidate_mapping.{field}", errors, minimum=-1000) != expected_value:
            errors.append(f"candidate_mapping.{field} expected {expected_value}")
    if candidate.get("strict_registration_allowed") is not False:
        errors.append("candidate strict_registration_allowed must be false")
    if candidate.get("citation_ready_impact") != "unchanged":
        errors.append("candidate citation_ready_impact must be unchanged")

    explicit = payload.get("explicit_printed_page_registration")
    if not isinstance(explicit, dict):
        errors.append("explicit_printed_page_registration must be an object")
        explicit = {}
    if explicit.get("status") != "PARTIAL_EXPLICIT_REGISTRATION":
        errors.append("explicit printed-page registration status mismatch")
    if explicit.get("manifest") != EXPLICIT_MANIFEST:
        errors.append("explicit printed-page registration manifest mismatch")
    if explicit.get("body_text_included") is not False or explicit.get("ocr_text_included") is not False:
        errors.append("explicit printed-page registration must remain body-free and OCR-free")
    if explicit.get("citation_ready_impact") != "unchanged":
        errors.append("explicit printed-page registration must not change citation-ready count")
    if integer(explicit.get("registered_page_count"), "explicit_printed_page_registration.registered_page_count", errors) != len(EXPLICIT_PAIRS):
        errors.append("explicit registered page count mismatch")
    explicit_pdf_pages = explicit.get("registered_pdf_pages")
    explicit_printed_pages = explicit.get("registered_printed_pages")
    expected_pdf_pages = [pdf_page for pdf_page, _ in EXPLICIT_PAIRS]
    expected_printed_pages = [printed_page for _, printed_page in EXPLICIT_PAIRS]
    if explicit_pdf_pages != expected_pdf_pages:
        errors.append("explicit registered PDF page list mismatch")
    if explicit_printed_pages != expected_printed_pages:
        errors.append("explicit registered printed page list mismatch")

    evidence = payload.get("anchor_evidence") if isinstance(payload.get("anchor_evidence"), dict) else {}
    anchors = evidence.get("anchors")
    if not isinstance(anchors, list):
        errors.append("anchor_evidence.anchors must be a list")
        anchors = []
    if integer(evidence.get("anchor_count"), "anchor_evidence.anchor_count", errors) != len(anchors):
        errors.append("anchor_count does not equal anchor list length")
    seen_pages: set[int] = set()
    for index, anchor in enumerate(anchors):
        if not isinstance(anchor, dict):
            errors.append(f"anchor {index} must be an object")
            continue
        pdf_page = integer(anchor.get("pdf_page_no"), f"anchor {index}.pdf_page_no", errors, minimum=1)
        printed_page = integer(anchor.get("printed_page"), f"anchor {index}.printed_page", errors, minimum=1)
        if pdf_page in seen_pages:
            errors.append(f"duplicate anchor PDF page: {pdf_page}")
        seen_pages.add(pdf_page)
        if pdf_page < 31 or pdf_page > 622 or printed_page != pdf_page - 30:
            errors.append(f"anchor {index} does not follow the candidate offset")
        if not str(anchor.get("title") or "").strip():
            errors.append(f"anchor {index} has no title")
        if anchor.get("verification") not in {"visual_and_ocr_anchor", "ocr_anchor"}:
            errors.append(f"anchor {index} has unsupported verification method")

    observation = payload.get("ocr_tail_observation") if isinstance(payload.get("ocr_tail_observation"), dict) else {}
    observed_fields = {
        field: integer(observation.get(field), f"ocr_tail_observation.{field}", errors)
        for field in (
            "pdf_window_start",
            "pdf_window_end",
            "window_page_count",
            "tail_numeric_pages",
            "offset_match_pages",
            "offset_nonmatch_pages",
            "no_numeric_tail_pages",
        )
    }
    if observed_fields.get("pdf_window_start") != 31 or observed_fields.get("pdf_window_end") != 622:
        errors.append("OCR observation window mismatch")
    if observed_fields.get("window_page_count") != 592:
        errors.append("OCR observation page count mismatch")
    if observed_fields.get("tail_numeric_pages") != observed_fields.get("offset_match_pages", -1) + observed_fields.get("offset_nonmatch_pages", -1):
        errors.append("OCR observation match/nonmatch counts do not add up")
    if observed_fields.get("tail_numeric_pages") + observed_fields.get("no_numeric_tail_pages") != observed_fields.get("window_page_count"):
        errors.append("OCR observation tail/no-tail counts do not add up")

    database = {"status": "NOT_CHECKED"}
    if db_path.is_file():
        try:
            with sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True) as connection:
                source_rows = connection.execute(
                    "SELECT id, source_type, source_id FROM sources WHERE source_id=?",
                    (payload.get("existing_source_id"),),
                ).fetchall()
                if len(source_rows) != 1:
                    errors.append("expected exactly one GAR-639 source row")
                    database = {"status": "FAIL", "source_row_count": len(source_rows)}
                else:
                    source_id = source_rows[0][0]
                    document_rows = connection.execute(
                        "SELECT id FROM documents WHERE source_id=? AND doc_key=?",
                        (source_id, payload.get("existing_doc_key")),
                    ).fetchall()
                    if len(document_rows) != 1:
                        errors.append("expected exactly one GAR-639 document row")
                        database = {"status": "FAIL", "document_row_count": len(document_rows)}
                    else:
                        document_id = document_rows[0][0]
                        stats = connection.execute(
                            """SELECT count(*), min(pdf_page_no), max(pdf_page_no), min(physical_page_no),
                                      max(physical_page_no), count(distinct source_sha256),
                                      sum(case when printed_page is not null and trim(printed_page)<>'' then 1 else 0 end),
                                      sum(case when citation_ready=1 then 1 else 0 end),
                                      sum(case when p.page_label LIKE 'pdf-% / printed-%' then 1 else 0 end)
                               FROM page_provenance pp
                               JOIN pages p ON p.id=pp.page_id
                              WHERE pp.document_id=?""",
                            (document_id,),
                        ).fetchone()
                        status_counts = {
                            str(row[0] or ""): int(row[1] or 0)
                            for row in connection.execute(
                                "SELECT review_status, count(*) FROM page_provenance WHERE document_id=? GROUP BY review_status",
                                (document_id,),
                            ).fetchall()
                        }
                        actual = {
                            "status": "PASS",
                            "page_count": int(stats[0] or 0),
                            "pdf_page_min": int(stats[1] or 0),
                            "pdf_page_max": int(stats[2] or 0),
                            "physical_page_min": int(stats[3] or 0),
                            "physical_page_max": int(stats[4] or 0),
                            "source_sha256_distinct_count": int(stats[5] or 0),
                            "printed_page_registered_count": int(stats[6] or 0),
                            "citation_ready_page_count": int(stats[7] or 0),
                            "page_label_printed_count": int(stats[8] or 0),
                            "review_status_counts": dict(sorted(status_counts.items())),
                        }
                        registered_pairs = tuple(
                            (int(row[0]), str(row[1]))
                            for row in connection.execute(
                                """SELECT pdf_page_no, printed_page
                                   FROM page_provenance
                                  WHERE document_id=? AND printed_page IS NOT NULL
                                    AND trim(printed_page)<>''
                                  ORDER BY pdf_page_no""",
                                (document_id,),
                            ).fetchall()
                        )
                        actual["registered_pairs"] = [list(pair) for pair in registered_pairs]
                        if registered_pairs != EXPLICIT_PAIRS:
                            errors.append("database registered printed-page pairs differ from explicit manifest")
                        database = actual
                        for field in (
                            "page_count",
                            "pdf_page_min",
                            "pdf_page_max",
                            "physical_page_min",
                            "physical_page_max",
                            "printed_page_registered_count",
                            "citation_ready_page_count",
                            "page_label_printed_count",
                        ):
                            if actual[field] != identity.get(field):
                                errors.append(f"database drift: {field}")
                        if actual["source_sha256_distinct_count"] != 1:
                            errors.append("GAR-639 has mixed source SHA values")
                        if actual["review_status_counts"] != identity.get("review_status_counts"):
                            errors.append("database drift: review_status_counts")
        except (OSError, sqlite3.Error) as exc:
            errors.append(f"GAR-639 database check failed: {exc}")
            database = {"status": "ERROR"}
    else:
        database = {"status": "NOT_AVAILABLE"}

    decision = payload.get("decision") if isinstance(payload.get("decision"), dict) else {}
    if decision.get("status") != "HOLD":
        errors.append("decision status must remain HOLD")
    return {
        "schema_version": "domestic_academic_gar639_page_identity_candidate_validation.v1",
        "external_id": "GAR-639C5E94AE",
        "candidate_map": str(candidate_path),
        "body_text_included": False,
        "formal_db_written": False,
        "local_paths_included": False,
        "auto_delete": False,
        "database": database,
        "anchor_count": len(anchors),
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--reuse-map", type=Path, default=DEFAULT_REUSE_MAP)
    parser.add_argument("--candidate", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.db, args.reuse_map, args.candidate)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
