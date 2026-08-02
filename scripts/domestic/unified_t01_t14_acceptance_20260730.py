#!/usr/bin/env python3
"""
T40 — Unified acceptance for T01-T14.

Per dual acceptance: build a unified acceptance that checks:
- JSONL parses
- unique keys
- paths exist
- SHA matches
- file magic
- status semantics
- formal DB SHA unchanged
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

ROOT = Path("/Users/cheer/Documents/mm agent/mingmeng-history-research")
WORK = ROOT / "work/domestic/minimax_autonomous_research_20260730"
RESEARCH_DIR = WORK / "research"
OCR_DIR = WORK / "ocr"

FORMAL_DB = ROOT / "data/research_index.sqlite"
FORMAL_DB_SHA_EXPECTED = "822e141dc5818393297f32ad63133eedbf57268c6088b6369505487632115fd3"


def sha256_file(path: Path) -> str | None:
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_file_magic(path: Path) -> str | None:
    if not path.exists():
        return None
    with open(path, "rb") as f:
        head = f.read(8)
    if head.startswith(b"%PDF"):
        return "PDF"
    if head.startswith(b"\x89PNG"):
        return "PNG"
    if head.startswith(b"\xff\xd8\xff"):
        return "JPEG"
    if head.startswith(b"PK"):
        return "ZIP"
    if head.startswith(b"{\n") or head.startswith(b"{\r") or head.startswith(b"["):
        return "TEXT_JSON"
    try:
        head.decode("utf-8")
        return "TEXT"
    except Exception:
        return "BINARY"


def parse_jsonl(path: Path) -> tuple[int, list]:
    rows = []
    if not path.exists():
        return 0, []
    with open(path) as f:
        text = f.read().strip()
    if not text:
        return 0, []
    # Handle single JSON object (top-level dict)
    if text.startswith("{"):
        try:
            obj = json.loads(text)
            if isinstance(obj, list):
                return len(obj), obj
            return 1, [obj]
        except Exception:
            pass
    # JSONL
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception as e:
            raise RuntimeError(f"parse error in {path}: {e}")
    return len(rows), rows


def check_unique_keys(rows: list, key: str) -> dict:
    seen = set()
    dups = []
    for r in rows:
        v = r.get(key)
        if v is None:
            continue
        if v in seen:
            dups.append(v)
        seen.add(v)
    return {"key": key, "unique_count": len(seen), "duplicates": len(dups)}


def check_paths_exist(rows: list, path_fields: list[str]) -> dict:
    total = 0
    missing = 0
    samples = []
    for r in rows:
        for f in path_fields:
            p = r.get(f)
            if not p:
                continue
            total += 1
            full = Path(p) if str(p).startswith("/") else ROOT / p
            if not full.exists():
                missing += 1
                if len(samples) < 5:
                    samples.append(str(p))
    return {"checked": total, "missing": missing, "missing_samples": samples}


def check_sha(rows: list, sha_field: str, path_field: str) -> dict:
    total = 0
    mismatch = 0
    samples = []
    for r in rows:
        expected = r.get(sha_field)
        p = r.get(path_field)
        if not expected or not p:
            continue
        total += 1
        full = Path(p) if str(p).startswith("/") else ROOT / p
        actual = sha256_file(full)
        if actual != expected:
            mismatch += 1
            if len(samples) < 5:
                samples.append({"path": str(p), "expected": expected, "actual": actual})
    return {"checked": total, "mismatches": mismatch, "samples": samples}


def status_semantics_check(rows: list, citation_field: str = "citation_ready") -> dict:
    flagged = []
    for r in rows:
        if r.get(citation_field) is True:
            flagged.append(r.get("provenance_id") or r.get("relation_id") or r.get("task_id"))
    return {"citation_ready_true_count": len(flagged), "samples": flagged[:5]}


def check_task(task_id: str, paths: list[Path], key: str, path_fields: list[str], sha_field: str, has_provenance: bool = False) -> dict:
    """For each path, check parseability, uniqueness, path existence, SHA, magic, status."""
    res = {"task_id": task_id, "files": []}
    for path in paths:
        if not path.exists():
            res["files"].append({"path": str(path), "exists": False})
            continue
        n, rows = parse_jsonl(path)
        file_res = {
            "path": str(path),
            "exists": True,
            "rows": n,
            "jsonl_parse": n > 0,
            "unique_keys": check_unique_keys(rows, key) if key else None,
            "paths_exist": check_paths_exist(rows, path_fields) if rows else None,
            "sha_check": check_sha(rows, sha_field, path_fields[0]) if rows and sha_field and path_fields else None,
            "magic": check_file_magic(path),
            "status_semantics": status_semantics_check(rows),
        }
        res["files"].append(file_res)
    return res


def main():
    formal_sha = sha256_file(FORMAL_DB)
    formal_db_unchanged = formal_sha == FORMAL_DB_SHA_EXPECTED

    tasks = [
        ("T01", [
            RESEARCH_DIR / "T01_FULLTEXT_AUDIT.jsonl",
            RESEARCH_DIR / "T01_FULLTEXT_AUDIT.json",
        ], "record_id", ["local_path"], "sha256"),
        ("T02", [
            RESEARCH_DIR / "T02_FULLTEXT_AUDIT.jsonl",
            RESEARCH_DIR / "T02_FULLTEXT_AUDIT.json",
        ], "record_id", ["local_path"], "sha256"),
        ("T03", [
            RESEARCH_DIR / "T03_OFFICIAL_IDENTITY_AUDIT.jsonl",
            RESEARCH_DIR / "T03_OFFICIAL_IDENTITY_AUDIT.json",
        ], "record_id", ["local_path"], "sha256"),
        ("T04", [
            RESEARCH_DIR / "T04_ENTITY_RELATION_ACCEPTANCE.json",
        ], "entity_id", ["local_path"], "sha256"),
        ("T05", [
            OCR_DIR / "T09_PAGE_INDEX.jsonl",
        ], "mapping_id", ["page_image_path", "ocr_md_path"], "page_image_sha256"),
        ("T05B", [
            RESEARCH_DIR / "T05B_MAPPING_ACCEPTANCE.json",
        ], "task_id", [], ""),
        ("T05C", [
            RESEARCH_DIR / "T05C_MAPPING_ACCEPTANCE.json",
        ], "task_id", [], ""),
        ("T06", [
            RESEARCH_DIR / "T06_PRIMARY_SOURCE_ACCEPTANCE.json",
        ], "record_id", [], ""),
        ("T07", [
            RESEARCH_DIR / "T07_COVERAGE_ACCEPTANCE.json",
        ], "task_id", [], ""),
        ("T08", [
            RESEARCH_DIR / "T08_DOSSIER_ACCEPTANCE.json",
        ], "dossier_id", [], ""),
        ("T09", [
            OCR_DIR / "T09_PAGE_INDEX.jsonl",
            OCR_DIR / "T09_PAGE_PROVENANCE.jsonl",
            OCR_DIR / "T09_PAGE_PROVENANCE.v2.jsonl",
            RESEARCH_DIR / "T09_OCR_ACCEPTANCE.json",
        ], "provenance_id", ["page_image_path", "ocr_md_path"], "page_image_sha256"),
        ("T10", [
            OCR_DIR / "T10_PAGE_INDEX.jsonl",
            OCR_DIR / "T10_PAGE_PROVENANCE.jsonl",
            OCR_DIR / "T10_PAGE_PROVENANCE.v2.jsonl",
            RESEARCH_DIR / "T10_OCR_ACCEPTANCE.json",
        ], "provenance_id", ["page_image_path", "ocr_md_path"], "page_image_sha256"),
        ("T11", [
            RESEARCH_DIR / "T11_DOSSIER_ACCEPTANCE.json",
        ], "dossier_id", [], ""),
        ("T12", [
            RESEARCH_DIR / "T12_ACADEMIC_RELATION_ACCEPTANCE.json",
        ], "relation_id", [], ""),
        ("T13", [
            RESEARCH_DIR / "T13_PHASE_REGISTRY_ACCEPTANCE.json",
            RESEARCH_DIR / "T13_PHASE_REGISTRY_1947_19481949.jsonl",
        ], "record_id", ["local_path"], "sha256"),
        ("T14", [
            OCR_DIR / "T14_PAGE_INDEX.jsonl",
            OCR_DIR / "T14_PAGE_PROVENANCE.jsonl",
            OCR_DIR / "T14_PAGE_PROVENANCE.v2.jsonl",
            RESEARCH_DIR / "T14_OCR_ACCEPTANCE.json",
        ], "provenance_id", ["page_image_path", "ocr_md_path"], "page_image_sha256"),
    ]

    results = []
    for tid, paths, key, pfields, shafield in tasks:
        results.append(check_task(tid, paths, key, pfields, shafield))

    summary = {
        "formal_db_sha_expected": FORMAL_DB_SHA_EXPECTED,
        "formal_db_sha_actual": formal_sha,
        "formal_db_unchanged": formal_db_unchanged,
        "task_count": len(results),
        "tasks": results,
        "totals": {
            "files_inspected": sum(len(r["files"]) for r in results),
            "files_missing": sum(
                len([f for f in r["files"] if not f["exists"]]) for r in results
            ),
            "rows_total": sum(
                sum(f.get("rows", 0) for f in r["files"]) for r in results
            ),
            "sha_mismatches_total": sum(
                sum(
                    (f.get("sha_check") or {}).get("mismatches", 0)
                    for f in r["files"]
                )
                for r in results
            ),
            "citation_ready_true_total": sum(
                sum(
                    (f.get("status_semantics") or {}).get("citation_ready_true_count", 0)
                    for f in r["files"]
                )
                for r in results
            ),
        },
    }
    out = RESEARCH_DIR / "T40_UNIFIED_T01_T14_ACCEPTANCE.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary["totals"], ensure_ascii=False, indent=2))
    print(json.dumps({
        "formal_db_unchanged": summary["formal_db_unchanged"],
        "formal_db_sha_actual": summary["formal_db_sha_actual"],
    }, indent=2))


if __name__ == "__main__":
    main()
