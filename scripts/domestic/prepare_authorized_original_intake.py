#!/usr/bin/env python3
"""Prepare a safe intake manifest for authorized domestic primary originals.

The command is intentionally a boundary tool. It inventories files placed in
an incoming directory, computes SHA256, and joins them only to an explicit
target mapping. It does not decode or extract body text, OCR, rename, delete,
write the formal SQLite database, or promote citation/readiness flags.

An authorized browser or archive workflow supplies the file and a JSONL
mapping record. Missing mappings, missing rights metadata, and missing page
identity review remain HOLD states rather than becoming research evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import mimetypes
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_TARGETS = ROOT / "data/domestic/authorized_original_intake_targets_20260821.json"
DEFAULT_INCOMING = ROOT / "data/domestic/raw/authorized_originals/incoming"
DEFAULT_OUTPUT = ROOT / "work/domestic/authorized_original_intake_20260821"
DEFAULT_MAPPING = DEFAULT_OUTPUT / "EXPLICIT_MAPPING.jsonl"
ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp"}

REQUIRED_MAPPING_FIELDS = (
    "target_id",
    "local_path",
    "source_url_or_catalog_reference",
    "record_id_or_catalog_reference",
    "accessed_at",
    "save_permission",
    "copy_permission",
    "public_display",
)


def sha256_file(path: Path) -> str:
    """Hash file bytes without parsing or decoding the document body."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_number}: mapping row must be an object")
        rows.append(value)
    return rows


def load_targets(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != "domestic_authorized_original_intake_targets.v1":
        raise ValueError(f"invalid target schema: {path}")
    targets = payload.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ValueError(f"target list is empty: {path}")
    ids = [str(row.get("target_id", "")) for row in targets]
    if any(not value for value in ids) or len(ids) != len(set(ids)):
        raise ValueError(f"target_id must be present and unique: {path}")
    return targets


def inside(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def discover_files(incoming: Path) -> list[dict[str, Any]]:
    incoming.mkdir(parents=True, exist_ok=True)
    root = incoming.resolve()
    records: list[dict[str, Any]] = []
    for path in sorted(incoming.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(incoming).as_posix()
        if path.is_symlink():
            records.append(
                {
                    "relative_path": relative,
                    "local_path": str(path),
                    "status": "SYMLINK_NOT_ALLOWED",
                    "bytes": None,
                    "sha256": None,
                }
            )
            continue
        resolved = path.resolve()
        if not inside(root, resolved):
            records.append(
                {
                    "relative_path": relative,
                    "local_path": str(path),
                    "status": "PATH_OUTSIDE_INCOMING",
                    "bytes": None,
                    "sha256": None,
                }
            )
            continue
        suffix = path.suffix.lower()
        if suffix not in ALLOWED_SUFFIXES:
            records.append(
                {
                    "relative_path": relative,
                    "local_path": str(path),
                    "suffix": suffix,
                    "status": "UNSUPPORTED_FILE_SUFFIX",
                    "bytes": path.stat().st_size,
                    "sha256": None,
                }
            )
            continue
        records.append(
            {
                "relative_path": relative,
                "local_path": str(path),
                "filename": path.name,
                "suffix": suffix,
                "mime_guess": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                "status": "LOCAL_FILE_HASHED",
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )
    return records


def mapping_required_status(row: dict[str, Any]) -> list[str]:
    missing = []
    for field in REQUIRED_MAPPING_FIELDS:
        value = row.get(field)
        if value is None or str(value).strip() == "":
            missing.append(field)
    for field in ("source_url_or_catalog_reference", "record_id_or_catalog_reference"):
        value = str(row.get(field, "")).strip().lower()
        if value in {"unknown", "n/a", "none", "null"}:
            missing.append(field + "_not_verified")
    return sorted(set(missing))


def path_record_by_relative(files: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("relative_path")): row for row in files}


def build_manifest(
    targets: list[dict[str, Any]],
    files: list[dict[str, Any]],
    mappings: list[dict[str, Any]],
    incoming: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target_by_id = {str(row["target_id"]): row for row in targets}
    file_by_relative = path_record_by_relative(files)
    mapping_by_target: dict[str, list[dict[str, Any]]] = {}
    mapping_errors: list[dict[str, Any]] = []

    for mapping in mappings:
        target_id = str(mapping.get("target_id", ""))
        relative = str(mapping.get("local_path", "")).strip().lstrip("/")
        if target_id not in target_by_id:
            mapping_errors.append({"status": "UNKNOWN_TARGET_ID", "mapping": mapping})
            continue
        if not relative or Path(relative).is_absolute() or ".." in Path(relative).parts:
            mapping_errors.append({"status": "INVALID_RELATIVE_LOCAL_PATH", "mapping": mapping})
            continue
        mapping_by_target.setdefault(target_id, []).append(mapping)

    manifest: list[dict[str, Any]] = []
    for target in targets:
        target_id = str(target["target_id"])
        assigned = mapping_by_target.get(target_id, [])
        if not assigned:
            status = "WAITING_FOR_LOCAL_ORIGINAL" if not files else "WAITING_FOR_EXPLICIT_MAPPING"
            manifest.append(
                {
                    "target_id": target_id,
                    "event_id": target.get("event_id"),
                    "target_class": target.get("target_class"),
                    "title": target.get("title"),
                    "document_date": target.get("document_date"),
                    "candidate_ids": target.get("candidate_ids", []),
                    "status": status,
                    "candidate_local_files": [row.get("relative_path") for row in files],
                    "missing_fields": ["target_id", "local_path"],
                    "citation_ready": False,
                    "human_verified": False,
                    "page_citation_ready": False,
                    "body_read": False,
                    "formal_db_written": False,
                    "ocr_started": False,
                    "auto_promote_primary_closed": False,
                }
            )
            continue

        if len(assigned) > 1:
            mapping_errors.append(
                {
                    "status": "MULTIPLE_FILES_FOR_TARGET_REVIEW",
                    "target_id": target_id,
                    "local_paths": [row.get("local_path") for row in assigned],
                }
            )
        mapping = assigned[0]
        relative = str(mapping.get("local_path", "")).strip().lstrip("/")
        file_row = file_by_relative.get(relative)
        missing = mapping_required_status(mapping)
        if file_row is None:
            status = "MAPPED_FILE_MISSING"
            missing.append("local_file")
            file_info: dict[str, Any] = {"relative_path": relative, "sha256": None, "bytes": None}
        else:
            file_info = file_row
            if file_row.get("status") != "LOCAL_FILE_HASHED":
                status = "HOLD_LOCAL_FILE_NOT_HASHED"
                missing.append("usable_local_file")
            elif mapping.get("claimed_sha256") and str(mapping["claimed_sha256"]).lower() != str(file_row["sha256"]).lower():
                status = "HOLD_SHA256_MISMATCH"
                missing.append("claimed_sha256_match")
            elif missing:
                status = "HOLD_MAPPING_METADATA"
            elif not isinstance(mapping.get("pdf_pages"), int) or int(mapping.get("pdf_pages", 0)) <= 0:
                status = "HASHED_NEEDS_PAGE_COUNT"
                missing.append("pdf_pages")
            elif mapping.get("page_identity_reviewed") is not True:
                status = "STAGED_NEEDS_PAGE_IDENTITY_REVIEW"
                missing.append("page_identity_reviewed=true")
            else:
                status = "STAGED_READY_FOR_DRY_RUN"

        manifest.append(
            {
                "target_id": target_id,
                "event_id": target.get("event_id"),
                "target_class": target.get("target_class"),
                "title": mapping.get("document_title") or target.get("title"),
                "document_date": mapping.get("document_date") or target.get("document_date"),
                "document_date_role": mapping.get("document_date_role") or target.get("document_date_role"),
                "candidate_ids": target.get("candidate_ids", []),
                "local_path": file_info.get("local_path") or str(incoming / relative),
                "relative_path": relative,
                "filename": file_info.get("filename"),
                "bytes": file_info.get("bytes"),
                "sha256": file_info.get("sha256"),
                "mime_guess": file_info.get("mime_guess"),
                "source_url_or_catalog_reference": mapping.get("source_url_or_catalog_reference"),
                "record_id_or_catalog_reference": mapping.get("record_id_or_catalog_reference"),
                "accessed_at": mapping.get("accessed_at"),
                "save_permission": mapping.get("save_permission"),
                "copy_permission": mapping.get("copy_permission"),
                "public_display": mapping.get("public_display"),
                "pdf_pages": mapping.get("pdf_pages"),
                "printed_page_map": mapping.get("printed_page_map"),
                "page_identity_reviewed": bool(mapping.get("page_identity_reviewed") is True),
                "status": status,
                "missing_fields": sorted(set(missing)),
                "citation_ready": False,
                "human_verified": False,
                "page_citation_ready": False,
                "body_read": False,
                "formal_db_written": False,
                "ocr_started": False,
                "auto_promote_primary_closed": False,
            }
        )

    mapped_paths = {
        str(mapping.get("local_path", "")).strip().lstrip("/")
        for values in mapping_by_target.values()
        for mapping in values
    }
    for file_row in files:
        if file_row.get("relative_path") not in mapped_paths:
            mapping_errors.append(
                {
                    "status": "UNMAPPED_LOCAL_FILE",
                    "relative_path": file_row.get("relative_path"),
                    "sha256": file_row.get("sha256"),
                }
            )
    return manifest, mapping_errors


def write_template(path: Path, targets: list[dict[str, Any]]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for target in targets:
            handle.write(
                json.dumps(
                    {
                        "target_id": target["target_id"],
                        "local_path": "填写 incoming 下相对路径",
                        "document_title": target.get("title"),
                        "document_date": target.get("document_date"),
                        "document_date_role": target.get("document_date_role"),
                        "source_url_or_catalog_reference": "填写详情页 URL 或馆藏档号",
                        "record_id_or_catalog_reference": "填写记录号、档号或案卷号",
                        "accessed_at": "填写 ISO 8601 时间",
                        "save_permission": "填写保存许可或用户授权说明",
                        "copy_permission": "填写复制许可或 citation_only",
                        "public_display": "填写允许公开的范围；不允许则写 metadata_only",
                        "pdf_pages": None,
                        "printed_page_map": "填写 PDF 页/物理页/印刷页对应关系",
                        "page_identity_reviewed": False,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--incoming", type=Path, default=DEFAULT_INCOMING)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    targets_path = args.targets if args.targets.is_absolute() else ROOT / args.targets
    incoming = args.incoming if args.incoming.is_absolute() else ROOT / args.incoming
    mapping_path = args.mapping if args.mapping.is_absolute() else ROOT / args.mapping
    output = args.output if args.output.is_absolute() else ROOT / args.output

    targets = load_targets(targets_path)
    write_template(mapping_path, targets)
    mappings = [row for row in read_jsonl(mapping_path) if row.get("local_path") != "填写 incoming 下相对路径"]
    files = discover_files(incoming)
    manifest, mapping_errors = build_manifest(targets, files, mappings, incoming)

    output.mkdir(parents=True, exist_ok=True)
    (output / "LOCAL_FILES.json").write_text(json.dumps(files, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "MAPPING_ERRORS.json").write_text(json.dumps(mapping_errors, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with (output / "INTAKE_MANIFEST.jsonl").open("w", encoding="utf-8") as handle:
        for row in manifest:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    counts = Counter(row["status"] for row in manifest)
    report = {
        "schema": "domestic_authorized_original_intake_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "target_count": len(targets),
        "incoming_file_count": len(files),
        "mapping_count": len(mappings),
        "mapping_error_count": len(mapping_errors),
        "status_counts": dict(sorted(counts.items())),
        "incoming": str(incoming),
        "mapping": str(mapping_path),
        "outputs": [
            str(output / "INTAKE_MANIFEST.jsonl"),
            str(output / "LOCAL_FILES.json"),
            str(output / "MAPPING_ERRORS.json"),
        ],
        "body_read": False,
        "ocr_started": False,
        "formal_db_written": False,
        "citation_ready_written": False,
        "auto_promote_primary_closed": False,
        "auto_delete": False,
        "rule": "hash-only inventory plus explicit target/source/rights/page mapping; all promotion remains a separate reviewed step",
    }
    (output / "REPORT.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
