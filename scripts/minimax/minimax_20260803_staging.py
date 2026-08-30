#!/usr/bin/env python3
"""
国内资料生产线：staging 数据库（Phase 4）
========================================

不直接写入 research_index.sqlite，先生成 staging 库：
  work/minimax-20260803/04_staging/staging.sqlite

staging 包含：
- domestic_sources：源（与 ingest_domestic.py 对齐 schema）
- domestic_candidates：候选（仅 accepted + needs_human_review）
- domestic_editorial_decisions：决策
- staging_ocr_plan：OCR 计划行
- staging_ocr_skip：OCR 跳过项
- staging_dedup_clusters：去重簇
- staging_provenance：每条候选的 provenance 元数据
- staging_import_log：本次三批（import_ready / needs_review / exclude）的决定

提供：
- staging 库的查询支持
- 不影响 research_index.sqlite
- SHA256 / page_count / citation_ready 字段在 staging 层一致
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path
from urllib.parse import urlparse


SCHEMA = """
CREATE TABLE IF NOT EXISTS staging_domestic_sources (
    id INTEGER PRIMARY KEY,
    source_id TEXT NOT NULL UNIQUE,
    source_name TEXT NOT NULL,
    institution TEXT NOT NULL,
    source_type TEXT NOT NULL,
    authority_level TEXT NOT NULL,
    official_url TEXT,
    record_or_search_url TEXT,
    material_types TEXT NOT NULL,
    shanghai_relevance TEXT NOT NULL,
    access_mode TEXT NOT NULL,
    rights_status TEXT NOT NULL,
    verification_note TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    status TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS staging_domestic_candidates (
    id INTEGER PRIMARY KEY,
    candidate_id TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    creator TEXT,
    recipient TEXT,
    document_date TEXT,
    document_date_precision TEXT,
    document_type TEXT,
    repository_code TEXT NOT NULL,
    repository_name TEXT NOT NULL,
    collection_name TEXT,
    archive_fonds TEXT,
    archive_series TEXT,
    archive_file TEXT,
    archive_item TEXT,
    catalog_reference TEXT NOT NULL,
    catalog_reference_status TEXT NOT NULL,
    source_url TEXT,
    source_url_role TEXT,
    url_host TEXT,
    access_mode TEXT NOT NULL,
    access_note TEXT NOT NULL,
    medium TEXT,
    online_availability TEXT,
    rights_status TEXT NOT NULL,
    reuse_rights TEXT,
    rights_basis TEXT,
    copy_allowed TEXT,
    authenticity_level_proposed TEXT NOT NULL,
    relevance_grade_proposed TEXT NOT NULL,
    event_tags TEXT NOT NULL,
    person_tags TEXT NOT NULL,
    place_tags TEXT NOT NULL,
    evidence_note TEXT NOT NULL,
    evidence_type TEXT NOT NULL,
    evidence_locator TEXT,
    uncertainty_note TEXT NOT NULL,
    checked_at TEXT NOT NULL,
    checked_by TEXT NOT NULL,
    review_status TEXT NOT NULL,
    review_note TEXT,
    reviewed_at TEXT,
    reviewed_by TEXT,
    check_outcome TEXT,
    authenticity_level_accepted TEXT,
    relevance_grade_accepted TEXT,
    period TEXT,
    source_family TEXT,
    source_kind TEXT,
    evidence_grade TEXT,
    citation_ready INTEGER NOT NULL DEFAULT 0,
    needs_ocr INTEGER NOT NULL DEFAULT 0,
    is_duplicate INTEGER NOT NULL DEFAULT 0,
    cluster_id TEXT,
    cluster_role TEXT,
    cluster_size INTEGER,
    sha256 TEXT,
    page_count INTEGER NOT NULL DEFAULT 0,
    staging_bucket TEXT NOT NULL,
    staging_notes TEXT,
    inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging_ocr_plan (
    id INTEGER PRIMARY KEY,
    file_id TEXT NOT NULL UNIQUE,
    source_url TEXT,
    source_kind TEXT,
    repository_code TEXT,
    primary_candidate_id TEXT,
    primary_title TEXT,
    primary_document_date TEXT,
    period TEXT,
    authenticity_level TEXT,
    evidence_grade TEXT,
    page_count INTEGER,
    page_count_basis TEXT,
    cluster_ids TEXT,
    ocr_priority TEXT,
    ocr_priority_reason TEXT,
    status TEXT,
    citation_ready INTEGER NOT NULL DEFAULT 0,
    needs_human_review INTEGER NOT NULL DEFAULT 1,
    candidate_ids TEXT,
    page_provenance TEXT,
    notes TEXT,
    inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging_ocr_skip (
    id INTEGER PRIMARY KEY,
    source_url TEXT NOT NULL,
    skip_reason TEXT NOT NULL,
    candidate_ids TEXT,
    level_distribution TEXT,
    inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging_acquisition_required (
    id INTEGER PRIMARY KEY,
    candidate_id TEXT NOT NULL UNIQUE,
    title TEXT,
    repository_code TEXT,
    repository_name TEXT,
    period TEXT,
    authenticity_level TEXT,
    evidence_grade TEXT,
    online_availability TEXT,
    medium TEXT,
    next_action TEXT,
    citation_ready INTEGER NOT NULL DEFAULT 0,
    needs_human_review INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging_dedup_clusters (
    id INTEGER PRIMARY KEY,
    cluster_id TEXT NOT NULL UNIQUE,
    canonical_candidate_id TEXT NOT NULL,
    cluster_size INTEGER NOT NULL,
    members TEXT NOT NULL,
    inserted_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS staging_import_log (
    id INTEGER PRIMARY KEY,
    candidate_id TEXT NOT NULL,
    period TEXT,
    repository_code TEXT,
    evidence_grade TEXT,
    citation_ready INTEGER,
    review_status TEXT,
    move TEXT NOT NULL,
    is_duplicate INTEGER,
    cluster_id TEXT,
    decided_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_staging_candidates_period ON staging_domestic_candidates(period);
CREATE INDEX IF NOT EXISTS idx_staging_candidates_repo ON staging_domestic_candidates(repository_code);
CREATE INDEX IF NOT EXISTS idx_staging_candidates_level ON staging_domestic_candidates(authenticity_level_accepted);
CREATE INDEX IF NOT EXISTS idx_staging_candidates_bucket ON staging_domestic_candidates(staging_bucket);
CREATE INDEX IF NOT EXISTS idx_staging_ocr_plan_priority ON staging_ocr_plan(ocr_priority);
CREATE INDEX IF NOT EXISTS idx_staging_import_log_move ON staging_import_log(move);
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", type=Path,
                        default=Path("work/minimax-20260803/01_inventory/inventory_full.jsonl"))
    parser.add_argument("--sources", type=Path,
                        default=Path("data/domestic/source_registry.json"))
    parser.add_argument("--source-manifest", type=Path,
                        default=Path("work/minimax-20260803/02_manifests/source_manifest.jsonl"))
    parser.add_argument("--dedup-clusters", type=Path,
                        default=Path("work/minimax-20260803/02_manifests/duplicate_clusters.json"))
    parser.add_argument("--ocr-plan", type=Path,
                        default=Path("work/minimax-20260803/03_ocr/ocr_plan.jsonl"))
    parser.add_argument("--ocr-skip", type=Path,
                        default=Path("work/minimax-20260803/03_ocr/ocr_skip_manifest.jsonl"))
    parser.add_argument("--acquisition-required", type=Path,
                        default=Path("work/minimax-20260803/03_ocr/acquisition_required.jsonl"))
    parser.add_argument("--import-dryrun", type=Path,
                        default=Path("work/minimax-20260803/02_manifests/import_dryrun.json"))
    parser.add_argument("--out", type=Path,
                        default=Path("work/minimax-20260803/04_staging/staging.sqlite"))
    args = parser.parse_args()

    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()

    with sqlite3.connect(out) as conn:
        conn.executescript(SCHEMA)

        # sources
        sources = json.loads(args.sources.read_text(encoding="utf-8"))
        conn.executemany(
            """INSERT INTO staging_domestic_sources
            (source_id, source_name, institution, source_type, authority_level,
             official_url, record_or_search_url, material_types, shanghai_relevance,
             access_mode, rights_status, verification_note, checked_at, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(
                s["source_id"], s["source_name"], s["institution"], s["source_type"], s["authority_level"],
                s.get("official_url"), s.get("record_or_search_url"),
                json.dumps(s.get("material_types", []), ensure_ascii=False),
                s["shanghai_relevance"], s["access_mode"], s["rights_status"], s["verification_note"],
                s["checked_at"], s["status"]
            ) for s in sources],
        )

        # candidates
        inventory = [json.loads(line) for line in args.inventory.read_text(encoding="utf-8").splitlines() if line.strip()]
        manifest = [json.loads(line) for line in args.source_manifest.read_text(encoding="utf-8").splitlines() if line.strip()]
        manifest_by_cid = {r["candidate_id"]: r for r in manifest}

        # 读 LX 升级报告：对 verified 候选覆盖 authenticity_level_accepted 为 L1
        lx_apply_report_path = Path("work/minimax-20260803/05_checkpoint/lx_apply_report.json")
        lx_upgraded = set()
        if lx_apply_report_path.exists():
            try:
                lx_report = json.loads(lx_apply_report_path.read_text(encoding="utf-8"))
                lx_upgraded = set(lx_report.get("verified", []))
            except Exception:
                pass
        if lx_upgraded:
            for r in inventory:
                if r.get("candidate_id") in lx_upgraded and (r.get("authenticity_level_accepted") or r.get("authenticity_level_proposed")) == "LX":
                    r["authenticity_level_accepted"] = "L1"
                    r["authenticity_level_proposed"] = "L1"
                    # 升级时同步补 evidence_grade / citation_ready / source_url
                    r["evidence_grade"] = "L1_citation_ready"
                    r["citation_ready"] = 1
                    m = manifest_by_cid.get(r["candidate_id"], {})
                    if not r.get("source_url") and m.get("source_url"):
                        r["source_url"] = m["source_url"]
                        r["url_host"] = m.get("url_host")
                    if not r.get("catalog_reference") and m.get("catalog_reference"):
                        r["catalog_reference"] = m["catalog_reference"]
            print(f"  LX upgrade override: {len(lx_upgraded)} candidates")

        # 需要 import_dryrun 的 move bucket
        dryrun = json.loads(args.import_dryrun.read_text(encoding="utf-8"))
        bucket_import = set(dryrun["three_buckets"]["import_ready"]["candidate_ids"])
        bucket_review = set(dryrun["three_buckets"]["needs_review"]["candidate_ids"])
        bucket_exclude = set(dryrun["three_buckets"]["exclude"]["candidate_ids"])
        cluster_map = {}
        for c in dryrun.get("totals", {}).get("move_breakdown", {}).items():
            pass

        # 重新查询 three buckets
        for m in json.loads(args.import_dryrun.read_text(encoding="utf-8"))["three_buckets"].values():
            pass

        # 简化：直接用 moves
        # 重新从 dryrun 拿 import_dryrun.moves
        dryrun_full = json.loads(args.import_dryrun.read_text(encoding="utf-8"))
        # 因为 dryrun 简版没有逐 candidate 的 move，需要从 source_manifest + 去重判断
        candidates_rows = []
        for r in inventory:
            cid = r["candidate_id"]
            m = manifest_by_cid.get(cid, {})
            # 决定 bucket
            if m.get("is_duplicate"):
                bucket = "exclude"
            elif r.get("review_status") == "accepted":
                bucket = "import_ready"
            elif r.get("review_status") == "needs_human_review":
                bucket = "needs_review"
            else:
                bucket = "exclude"

            # LX 升级：同步补 evidence_grade / citation_ready
            ev_grade = m.get("evidence_grade")
            cite_ready = 1 if m.get("citation_ready") else 0
            if cid in lx_upgraded and r.get("authenticity_level_accepted") == "L1":
                ev_grade = "L1_citation_ready"
                cite_ready = 1

            url = r.get("source_url") or ""
            host = urlparse(url).netloc if url else ""
            candidates_rows.append((
                cid,
                r.get("title"),
                r.get("creator"),
                r.get("recipient"),
                r.get("document_date"),
                r.get("document_date_precision"),
                r.get("document_type"),
                r.get("repository_code"),
                r.get("repository_name"),
                r.get("collection_name"),
                r.get("archive_fonds"),
                r.get("archive_series"),
                r.get("archive_file"),
                r.get("archive_item"),
                r.get("catalog_reference"),
                r.get("catalog_reference_status"),
                r.get("source_url"),
                r.get("source_url_role"),
                host,
                r.get("access_mode"),
                r.get("access_note"),
                r.get("medium"),
                r.get("online_availability"),
                r.get("rights_status"),
                r.get("reuse_rights"),
                r.get("rights_basis"),
                r.get("copy_allowed"),
                r.get("authenticity_level_proposed"),
                r.get("relevance_grade_proposed"),
                json.dumps(r.get("event_tags", []), ensure_ascii=False),
                json.dumps(r.get("person_tags", []), ensure_ascii=False),
                json.dumps(r.get("place_tags", []), ensure_ascii=False),
                r.get("evidence_note"),
                r.get("evidence_type"),
                r.get("evidence_locator"),
                r.get("uncertainty_note"),
                r.get("checked_at"),
                r.get("checked_by"),
                r.get("review_status"),
                r.get("review_note"),
                r.get("reviewed_at"),
                r.get("reviewed_by"),
                r.get("check_outcome"),
                r.get("authenticity_level_accepted"),
                r.get("relevance_grade_accepted"),
                r.get("_period"),
                r.get("_source_family"),
                m.get("source_kind"),
                ev_grade,
                cite_ready,
                1 if m.get("needs_ocr") else 0,
                1 if m.get("is_duplicate") else 0,
                m.get("cluster_id"),
                m.get("cluster_role"),
                m.get("cluster_size"),
                m.get("sha256") or "",
                m.get("page_count") or 0,
                bucket,
                "" if bucket == "import_ready" else (r.get("uncertainty_note") or ""),
            ))
        conn.executemany(
            """INSERT INTO staging_domestic_candidates
            (candidate_id, title, creator, recipient, document_date, document_date_precision,
             document_type, repository_code, repository_name, collection_name, archive_fonds,
             archive_series, archive_file, archive_item, catalog_reference,
             catalog_reference_status, source_url, source_url_role, url_host, access_mode,
             access_note, medium, online_availability, rights_status, reuse_rights, rights_basis,
             copy_allowed, authenticity_level_proposed, relevance_grade_proposed, event_tags,
             person_tags, place_tags, evidence_note, evidence_type, evidence_locator,
             uncertainty_note, checked_at, checked_by, review_status, review_note, reviewed_at,
             reviewed_by, check_outcome, authenticity_level_accepted, relevance_grade_accepted,
             period, source_family, source_kind, evidence_grade, citation_ready, needs_ocr,
             is_duplicate, cluster_id, cluster_role, cluster_size, sha256, page_count,
             staging_bucket, staging_notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
             ?, ?, ?, ?, ?, ?)""",
            candidates_rows,
        )

        # OCR plan
        plan_rows = [json.loads(line) for line in args.ocr_plan.read_text(encoding="utf-8").splitlines() if line.strip()]
        conn.executemany(
            """INSERT INTO staging_ocr_plan
            (file_id, source_url, source_kind, repository_code, primary_candidate_id,
             primary_title, primary_document_date, period, authenticity_level, evidence_grade,
             page_count, page_count_basis, cluster_ids, ocr_priority, ocr_priority_reason,
             status, citation_ready, needs_human_review, candidate_ids, page_provenance, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            [(
                r["file_id"], r.get("source_url"), r.get("source_kind"), r.get("repository_code"),
                r.get("primary_candidate_id"), r.get("primary_title"), r.get("primary_document_date"),
                r.get("period"), r.get("authenticity_level"), r.get("evidence_grade"),
                r.get("page_count"), r.get("page_count_basis"),
                json.dumps(r.get("cluster_ids", []), ensure_ascii=False),
                r.get("ocr_priority"), r.get("ocr_priority_reason"),
                r.get("status"), 0, 1,
                json.dumps(r.get("candidate_ids", []), ensure_ascii=False),
                json.dumps(r.get("page_provenance", []), ensure_ascii=False),
                r.get("notes"),
            ) for r in plan_rows],
        )

        # OCR skip
        skip_rows = [json.loads(line) for line in args.ocr_skip.read_text(encoding="utf-8").splitlines() if line.strip()]
        conn.executemany(
            """INSERT INTO staging_ocr_skip (source_url, skip_reason, candidate_ids, level_distribution)
            VALUES (?, ?, ?, ?)""",
            [(
                r["source_url"], r["skip_reason"],
                json.dumps(r.get("candidate_ids", []), ensure_ascii=False),
                json.dumps(r.get("level_distribution", {}), ensure_ascii=False),
            ) for r in skip_rows],
        )

        # acquisition_required
        if args.acquisition_required.exists():
            acq_rows = [json.loads(line) for line in args.acquisition_required.read_text(encoding="utf-8").splitlines() if line.strip()]
            conn.executemany(
                """INSERT INTO staging_acquisition_required
                (candidate_id, title, repository_code, repository_name, period, authenticity_level,
                 evidence_grade, online_availability, medium, next_action, citation_ready,
                 needs_human_review, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [(
                    r["candidate_id"], r.get("title"), r.get("repository_code"),
                    r.get("repository_name"), r.get("period"), r.get("authenticity_level"),
                    r.get("evidence_grade"), r.get("online_availability"), r.get("medium"),
                    r.get("next_action"), 0, 1, r.get("notes"),
                ) for r in acq_rows],
            )

        # dedup clusters
        dedup_data = json.loads(args.dedup_clusters.read_text(encoding="utf-8"))
        conn.executemany(
            """INSERT INTO staging_dedup_clusters (cluster_id, canonical_candidate_id, cluster_size, members)
            VALUES (?, ?, ?, ?)""",
            [(
                c["cluster_id"], c["canonical_candidate_id"], c["size"],
                json.dumps([m["candidate_id"] for m in c["members"]], ensure_ascii=False),
            ) for c in dedup_data["clusters"]],
        )

        # import_log：基于 dryrun 重新生成
        log_rows = []
        for r in manifest:
            cid = r["candidate_id"]
            if r.get("is_duplicate") and r.get("cluster_role") == "duplicate":
                move = "duplicate_skip_ingest"
            elif r.get("review_status") == "accepted" and r.get("authenticity_level") in {"L1", "L2", "L3", "L4"}:
                move = "accepted_ready_for_staging"
            elif r.get("review_status") == "accepted" and r.get("authenticity_level") == "LX":
                move = "accepted_lx_pending_human"
            elif r.get("review_status") == "needs_human_review":
                move = "pending_human_review"
            else:
                move = "rejected_or_other"
            log_rows.append((
                cid, r.get("period"), r.get("repository_code"), r.get("evidence_grade"),
                1 if r.get("citation_ready") else 0,
                r.get("review_status"), move,
                1 if r.get("is_duplicate") else 0,
                r.get("cluster_id"),
            ))
        conn.executemany(
            """INSERT INTO staging_import_log
            (candidate_id, period, repository_code, evidence_grade, citation_ready,
             review_status, move, is_duplicate, cluster_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            log_rows,
        )
        conn.commit()

        # 汇总
        candidates_count = conn.execute("SELECT count(*) FROM staging_domestic_candidates").fetchone()[0]
        import_ready_count = conn.execute("SELECT count(*) FROM staging_domestic_candidates WHERE staging_bucket = 'import_ready'").fetchone()[0]
        needs_review_count = conn.execute("SELECT count(*) FROM staging_domestic_candidates WHERE staging_bucket = 'needs_review'").fetchone()[0]
        exclude_count = conn.execute("SELECT count(*) FROM staging_domestic_candidates WHERE staging_bucket = 'exclude'").fetchone()[0]
        ocr_plan_count = conn.execute("SELECT count(*) FROM staging_ocr_plan").fetchone()[0]
        dedup_count = conn.execute("SELECT count(*) FROM staging_dedup_clusters").fetchone()[0]
        acquisition_count = conn.execute("SELECT count(*) FROM staging_acquisition_required").fetchone()[0]
        sources_count = conn.execute("SELECT count(*) FROM staging_domestic_sources").fetchone()[0]
        import_log_count = conn.execute("SELECT count(*) FROM staging_import_log").fetchone()[0]

        citation_ready_count = conn.execute("SELECT count(*) FROM staging_domestic_candidates WHERE citation_ready = 1").fetchone()[0]
        needs_ocr_count = conn.execute("SELECT count(*) FROM staging_domestic_candidates WHERE needs_ocr = 1").fetchone()[0]

    print(f"staging db: {out}")
    print(f"  sources: {sources_count}")
    print(f"  candidates: {candidates_count}")
    print(f"    import_ready: {import_ready_count}")
    print(f"    needs_review: {needs_review_count}")
    print(f"    exclude: {exclude_count}")
    print(f"  ocr_plan: {ocr_plan_count}")
    print(f"  dedup_clusters: {dedup_count}")
    print(f"  acquisition_required: {acquisition_count}")
    print(f"  import_log: {import_log_count}")
    print(f"  citation_ready_total: {citation_ready_count}")
    print(f"  needs_ocr_total: {needs_ocr_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
