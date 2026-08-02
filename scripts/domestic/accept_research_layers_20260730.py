#!/usr/bin/env python3
"""Validate, deduplicate, sample, and dry-run domestic research layers.

This script never writes the formal research_index.sqlite.  It creates a
separate dry-run SQLite database with two new research-layer tables.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sqlite3
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "work/domestic/research_layers_acceptance_20260730"
GROK = ROOT / "work/domestic/grok_academic_research_20260730"
MINIMAX = ROOT / "work/domestic/minimax_official_research_20260730"
FORMAL_DB = ROOT / "data/research_index.sqlite"
DRYRUN_DB = WORK / "research_index.research_layers_dryrun.sqlite"


def read_jsonl(path: Path) -> list[dict]:
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError(f"{path}:{line_no}: expected object")
        rows.append(value)
    return rows


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value).expanduser()
    return path if path.is_absolute() else ROOT / path


def normalize_text(value: str | None) -> str:
    text = unicodedata.normalize("NFKC", value or "").lower()
    return re.sub(r"[\W_]+", "", text, flags=re.UNICODE)


def normalize_url(value: str | None) -> str:
    if not value:
        return ""
    parts = urlsplit(value.strip())
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if not key.lower().startswith(("utm_", "spm", "from"))
    ]
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            re.sub(r"/+$", "", parts.path),
            urlencode(query),
            "",
        )
    )


def canonical_key(row: dict) -> tuple[str, str]:
    doi = normalize_text(row.get("doi"))
    if doi:
        return "doi", doi
    stable = normalize_text(row.get("stable_id"))
    if stable and any(token in stable for token in ("isbn", "doi", "cnki")):
        return "stable", stable
    url = normalize_url(row.get("source_url"))
    title = normalize_text(row.get("title"))
    if url and title:
        return "url_title", f"{url}|{title}"
    if url:
        return "url", url
    author = normalize_text(row.get("author") or row.get("creator"))
    date = normalize_text(
        row.get("publication_date")
        or row.get("normalized_date")
        or row.get("date_or_period_original")
    )
    return "bibliographic", f"{title}|{author}|{date}"


def file_check(path_value: str | None, expected_sha: str | None) -> dict:
    path = resolve(path_value)
    if path is None:
        return {"status": "NO_LOCAL_FILE"}
    if not path.is_file() or path.stat().st_size == 0:
        return {"status": "MISSING_OR_EMPTY", "path": str(path)}
    actual = sha256(path)
    return {
        "status": "PASS" if not expected_sha or actual == expected_sha else "SHA_MISMATCH",
        "path": str(path),
        "bytes": path.stat().st_size,
        "sha256": actual,
    }


def academic_to_unified(row: dict) -> dict:
    return {
        "external_id": row["record_id"],
        "layer": "SCHOLARLY_RESEARCH",
        "title": row.get("title"),
        "author": row.get("author"),
        "institution": row.get("institution")
        or row.get("author_affiliation_at_publication"),
        "publication_date": row.get("publication_date"),
        "research_type": row.get("research_type"),
        "quality_tier": row.get("quality_tier"),
        "source_url": row.get("source_url"),
        "local_path": row.get("local_path"),
        "sha256": row.get("sha256"),
        "review_status": "machine_accepted",
        "citation_ready": False,
        "human_verified": False,
        "metadata": row,
    }


def official_to_unified(row: dict, card: dict | None) -> dict:
    local_path = (card or {}).get("local_acquisition_path") or row.get("p3_local_path")
    resolved = resolve(local_path)
    local_sha = sha256(resolved) if resolved and resolved.is_file() else row.get("p3_sha256")
    return {
        "external_id": row["candidate_id"],
        "layer": "OFFICIAL_RETROSPECTIVE",
        "title": row.get("title"),
        "author": (card or {}).get("creator") or None,
        "institution": row.get("institution"),
        "publication_date": row.get("normalized_date"),
        "research_type": row.get("research_card_category"),
        "quality_tier": "A"
        if row.get("institution_type") in {"MMZY", "QY"}
        else "B",
        "source_url": row.get("source_url"),
        "local_path": local_path,
        "sha256": local_sha,
        "review_status": "machine_accepted",
        "citation_ready": False,
        "human_verified": False,
        "metadata": row,
    }


def build_sample(rows: list[dict], per_tier: int = 10) -> list[dict]:
    sample = []
    for tier in ("S", "A"):
        pool = [row for row in rows if row.get("quality_tier") == tier]
        pool.sort(key=lambda row: hashlib.sha256(row["record_id"].encode()).hexdigest())
        for row in pool[:per_tier]:
            sample.append(
                {
                    "record_id": row["record_id"],
                    "quality_tier": tier,
                    "title": row.get("title"),
                    "author": row.get("author"),
                    "affiliation": row.get("author_affiliation_at_publication"),
                    "author_title": row.get("author_title"),
                    "journal": row.get("journal"),
                    "publisher": row.get("publisher"),
                    "doi": row.get("doi"),
                    "stable_id": row.get("stable_id"),
                    "source_url": row.get("source_url"),
                    "local_path": row.get("local_path"),
                    "local_file_check": file_check(row.get("local_path"), row.get("sha256")),
                    "live_check_status": "PENDING_CODEX",
                    "sample_reason": f"deterministic_sha_sample_{tier}",
                }
            )
    return sample


def create_dryrun_db(rows: list[dict]) -> dict:
    WORK.mkdir(parents=True, exist_ok=True)
    if not DRYRUN_DB.exists():
        shutil.copy2(FORMAL_DB, DRYRUN_DB)
    with sqlite3.connect(DRYRUN_DB) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS research_materials (
                id INTEGER PRIMARY KEY,
                external_id TEXT NOT NULL UNIQUE,
                layer TEXT NOT NULL CHECK(layer IN (
                    'CONTEMPORARY_PRIMARY',
                    'OFFICIAL_RETROSPECTIVE',
                    'SCHOLARLY_RESEARCH',
                    'CATALOG_METADATA',
                    'HOLD'
                )),
                title TEXT NOT NULL,
                author TEXT,
                institution TEXT,
                publication_date TEXT,
                research_type TEXT,
                quality_tier TEXT,
                source_url TEXT,
                local_path TEXT,
                sha256 TEXT,
                review_status TEXT NOT NULL,
                citation_ready INTEGER NOT NULL DEFAULT 0,
                human_verified INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL,
                inserted_at TEXT NOT NULL
            );
            CREATE VIRTUAL TABLE IF NOT EXISTS research_material_fts
            USING fts5(external_id, layer, title, author, institution, fulltext);
            CREATE VIRTUAL TABLE IF NOT EXISTS research_material_fts_trigram
            USING fts5(
                external_id, layer, title, author, institution, fulltext,
                tokenize='trigram'
            );
            """
        )
        conn.execute("DELETE FROM research_material_fts")
        conn.execute("DELETE FROM research_material_fts_trigram")
        conn.execute("DELETE FROM research_materials")
        inserted = 0
        for row in rows:
            cur = conn.execute(
                """
                INSERT INTO research_materials(
                    external_id,layer,title,author,institution,publication_date,
                    research_type,quality_tier,source_url,local_path,sha256,
                    review_status,citation_ready,human_verified,metadata_json,inserted_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    row["external_id"],
                    row["layer"],
                    row["title"],
                    row.get("author"),
                    row.get("institution"),
                    row.get("publication_date"),
                    row.get("research_type"),
                    row.get("quality_tier"),
                    row.get("source_url"),
                    row.get("local_path"),
                    row.get("sha256"),
                    row["review_status"],
                    0,
                    0,
                    json.dumps(row["metadata"], ensure_ascii=False),
                    datetime.now().astimezone().isoformat(),
                ),
            )
            fulltext = ""
            metadata = row["metadata"]
            text_path = resolve(metadata.get("text_path"))
            if text_path and text_path.is_file():
                fulltext = text_path.read_text(encoding="utf-8", errors="replace")
            conn.execute(
                """
                INSERT INTO research_material_fts(
                    rowid,external_id,layer,title,author,institution,fulltext
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    cur.lastrowid,
                    row["external_id"],
                    row["layer"],
                    row["title"],
                    row.get("author") or "",
                    row.get("institution") or "",
                    fulltext,
                ),
            )
            conn.execute(
                """
                INSERT INTO research_material_fts_trigram(
                    rowid,external_id,layer,title,author,institution,fulltext
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    cur.lastrowid,
                    row["external_id"],
                    row["layer"],
                    row["title"],
                    row.get("author") or "",
                    row.get("institution") or "",
                    fulltext,
                ),
            )
            inserted += 1
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        material_count = conn.execute("SELECT count(*) FROM research_materials").fetchone()[0]
        fts_count = conn.execute("SELECT count(*) FROM research_material_fts").fetchone()[0]
        trigram_count = conn.execute(
            "SELECT count(*) FROM research_material_fts_trigram"
        ).fetchone()[0]
        chinese_probe = conn.execute(
            "SELECT count(*) FROM research_material_fts_trigram "
            "WHERE research_material_fts_trigram MATCH '民主同盟'"
        ).fetchone()[0]
        original_documents = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
        original_pages = conn.execute("SELECT count(*) FROM pages").fetchone()[0]
        original_page_fts = conn.execute("SELECT count(*) FROM page_fts").fetchone()[0]
        conn.commit()
    return {
        "dryrun_db": str(DRYRUN_DB),
        "inserted": inserted,
        "research_materials": material_count,
        "research_material_fts": fts_count,
        "research_material_fts_trigram": trigram_count,
        "chinese_fts_probe_minzhu_tongmeng": chinese_probe,
        "two_character_query_note": "FTS5 trigram requires 3+ characters; use LIKE fallback for 民盟.",
        "integrity_check": integrity,
        "existing_documents_unchanged": original_documents,
        "existing_pages_unchanged": original_pages,
        "existing_page_fts_unchanged": original_page_fts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-dryrun-db", action="store_true")
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)

    academic = read_jsonl(GROK / "02_records/ACADEMIC_RECORDS.jsonl")
    official = read_jsonl(MINIMAX / "02_records/OFFICIAL_RESEARCH_RECORDS.jsonl")
    cards = {
        row["candidate_id"]: row
        for row in read_jsonl(MINIMAX / "05_cards/RESEARCH_CARDS.jsonl")
    }

    issues = []
    for label, rows, id_key in (
        ("academic", academic, "record_id"),
        ("official", official, "candidate_id"),
    ):
        ids = [row.get(id_key) for row in rows]
        if len(ids) != len(set(ids)) or any(not value for value in ids):
            issues.append(f"{label}: missing or duplicate IDs")

    academic_file_checks = [
        {"record_id": row["record_id"], **file_check(row.get("local_path"), row.get("sha256"))}
        for row in academic
        if row.get("local_path")
    ]
    official_file_checks = [
        {
            "candidate_id": row["candidate_id"],
            "registered_p3_sha256": row.get("p3_sha256"),
            **file_check(
                (cards.get(row["candidate_id"]) or {}).get("local_acquisition_path")
                or row.get("p3_local_path"),
                row.get("p3_sha256")
                if row.get("p3_local_path")
                and row.get("p3_local_path")
                == (cards.get(row["candidate_id"]) or {}).get("local_acquisition_path")
                else None,
            ),
        }
        for row in official
        if (cards.get(row["candidate_id"]) or {}).get("local_acquisition_path")
        or row.get("p3_local_path")
    ]
    if any(row["status"] != "PASS" for row in academic_file_checks + official_file_checks):
        issues.append("one or more local file checks failed")

    unified = [academic_to_unified(row) for row in academic]
    unified += [official_to_unified(row, cards.get(row["candidate_id"])) for row in official]
    correction_path = WORK / "FULLTEXT_STATUS_CORRECTIONS.jsonl"
    if correction_path.exists():
        corrections = {
            row["record_id"]: row for row in read_jsonl(correction_path)
        }
        for row in unified:
            correction = corrections.get(row["external_id"])
            if not correction:
                continue
            row["metadata"] = {
                **row["metadata"],
                "reported_fulltext_status": correction.get("reported_fulltext_status"),
                "audited_fulltext_status": correction.get("corrected_fulltext_status"),
                "fulltext_audit_decision": correction.get("decision"),
            }
            row["review_status"] = (
                "machine_fulltext_candidate"
                if correction.get("corrected_fulltext_status", "").startswith("FULLTEXT_")
                else "machine_metadata_accepted"
            )

    existing = read_jsonl(ROOT / "data/domestic/candidates.jsonl")
    existing_by_url = defaultdict(list)
    existing_by_url_title = defaultdict(list)
    existing_by_title = defaultdict(list)
    for row in existing:
        normalized_url = normalize_url(row.get("source_url"))
        normalized_title = normalize_text(row.get("title"))
        if normalized_url:
            existing_by_url[normalized_url].append(row["candidate_id"])
        if normalized_url and normalized_title:
            existing_by_url_title[(normalized_url, normalized_title)].append(
                row["candidate_id"]
            )
        if normalized_title:
            existing_by_title[normalized_title].append(row["candidate_id"])

    groups = defaultdict(list)
    for row in unified:
        key = canonical_key(row["metadata"])
        groups[key].append(row)

    dedup_ledger = []
    accepted = []
    for key, members in sorted(groups.items(), key=lambda item: item[0]):
        members.sort(
            key=lambda row: (
                row["quality_tier"] not in {"S", "A"},
                row["layer"] != "SCHOLARLY_RESEARCH",
                row["external_id"],
            )
        )
        canonical = members[0]
        accepted.append(canonical)
        url = normalize_url(canonical.get("source_url"))
        title = normalize_text(canonical.get("title"))
        existing_matches = sorted(
            set(
                (existing_by_url_title.get((url, title), []) if url and title else [])
                + (existing_by_title.get(title, []) if title else [])
            )
        )
        dedup_ledger.append(
            {
                "dedup_type": key[0],
                "dedup_key": key[1],
                "canonical_external_id": canonical["external_id"],
                "member_external_ids": [row["external_id"] for row in members],
                "cross_new_layer_duplicate_count": len(members) - 1,
                "existing_domestic_candidate_matches": existing_matches,
                "decision": "KEEP_CANONICAL_RESEARCH_LAYER",
            }
        )

    sample = build_sample(academic)
    write_jsonl(WORK / "UNIFIED_ACCEPTED_RECORDS.jsonl", accepted)
    write_jsonl(WORK / "CROSS_LAYER_DEDUP_LEDGER.jsonl", dedup_ledger)
    write_jsonl(WORK / "SA_QUALITY_SAMPLE.jsonl", sample)
    write_jsonl(WORK / "ACADEMIC_FILE_CHECKS.jsonl", academic_file_checks)
    write_jsonl(WORK / "OFFICIAL_FILE_CHECKS.jsonl", official_file_checks)

    dryrun = create_dryrun_db(accepted) if args.build_dryrun_db else None
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(),
        "formal_db_sha256": sha256(FORMAL_DB),
        "academic_input": len(academic),
        "official_input": len(official),
        "combined_input": len(unified),
        "accepted_after_cross_layer_dedup": len(accepted),
        "cross_new_layer_duplicate_groups": sum(
            1 for members in groups.values() if len(members) > 1
        ),
        "existing_domestic_match_groups": sum(
            1 for row in dedup_ledger if row["existing_domestic_candidate_matches"]
        ),
        "academic_tiers": dict(Counter(row.get("quality_tier") for row in academic)),
        "academic_types": dict(Counter(row.get("research_type") for row in academic)),
        "official_types": dict(
            Counter(row.get("research_card_category") for row in official)
        ),
        "academic_local_file_checks": dict(
            Counter(row["status"] for row in academic_file_checks)
        ),
        "official_local_file_checks": dict(
            Counter(row["status"] for row in official_file_checks)
        ),
        "quality_sample_rows": len(sample),
        "quality_sample_live_checks": (
            "completed"
            if (WORK / "SA_QUALITY_SAMPLE_LIVE_CHECKED.jsonl").exists()
            else "pending"
        ),
        "fulltext_corrections_applied": correction_path.exists(),
        "issues": issues,
        "acceptance_state": (
            "PASS_WITH_FULLTEXT_STATUS_CORRECTIONS"
            if not issues
            and (WORK / "SA_QUALITY_SAMPLE_LIVE_CHECKED.jsonl").exists()
            else "STRUCTURE_PASS_LIVE_SAMPLE_PENDING"
            if not issues
            else "BLOCKED"
        ),
        "dryrun": dryrun,
    }
    (WORK / "ACCEPTANCE_SUMMARY.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not issues else 1


if __name__ == "__main__":
    raise SystemExit(main())
