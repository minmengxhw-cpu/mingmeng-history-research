#!/usr/bin/env python3
"""
T58 — Build isolated dry-run SQLite db with research_materials, entities, relations, source_series, etc.

Per master task: dry-run must contain:
- research_materials
- research_material_fts_trigram
- entities
- entity_aliases
- events
- places
- relations
- source_series
- dossiers
- page_provenance_candidate

This script READS from existing JSONL files and writes to a new isolated dry-run DB.
"""
from __future__ import annotations
import hashlib
import json
import os
import sqlite3
from pathlib import Path

ROOT = Path(".")
DRYRUN_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/dryrun"
DRYRUN_DIR.mkdir(parents=True, exist_ok=True)
DRYRUN_DB = DRYRUN_DIR / "minimax_autonomous_research_20260730_dryrun.sqlite"
RESEARCH_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/research"
ACQUISITION_DIR = ROOT / "data/domestic/official_research_public_20260730"
DOSSIERS_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/dossiers"
RELATIONS_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/relations"
ENTITIES_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/entities"


def sha256_file(path):
    if not path.exists():
        return None
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    if DRYRUN_DB.exists():
        DRYRUN_DB.unlink()
    conn = sqlite3.connect(DRYRUN_DB)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check")
    # Schema
    cur.executescript("""
    CREATE TABLE research_materials (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_id TEXT UNIQUE,
        title TEXT,
        source_url TEXT,
        local_path TEXT,
        local_sha256 TEXT,
        institution_type TEXT,
        research_card_category TEXT,
        research_theme_phase TEXT,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0,
        rights_status TEXT,
        created_at TEXT,
        updated_at TEXT
    );
    CREATE VIRTUAL TABLE research_material_fts_trigram USING fts5(
        candidate_id UNINDEXED, title, source_title, period, year, institution_type,
        research_card_category, content=''
    );
    CREATE TABLE entities (
        entity_id TEXT PRIMARY KEY,
        entity_type TEXT,
        canonical_name TEXT,
        aliases TEXT,
        evidence_count INTEGER DEFAULT 0,
        confidence TEXT,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0,
        created_at TEXT,
        updated_at TEXT,
        dossier_appearance_count INTEGER DEFAULT 0
    );
    CREATE TABLE entity_aliases (
        alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
        entity_id TEXT,
        alias TEXT,
        alias_type TEXT,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0
    );
    CREATE TABLE events (
        event_id TEXT PRIMARY KEY,
        event_type TEXT,
        label TEXT,
        period TEXT,
        source_record_id TEXT,
        confidence TEXT,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0,
        created_at TEXT
    );
    CREATE TABLE places (
        place_id TEXT PRIMARY KEY,
        place_name TEXT,
        evidence_count INTEGER DEFAULT 0,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0
    );
    CREATE TABLE relations (
        relation_id TEXT PRIMARY KEY,
        subject_id TEXT,
        predicate TEXT,
        object_id TEXT,
        relation_scope TEXT,
        valid_time TEXT,
        machine_confidence REAL,
        conflict_status TEXT,
        evidence_source_url TEXT,
        evidence_local_path TEXT,
        evidence_excerpt TEXT,
        dossier_id TEXT,
        machine_status TEXT,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0
    );
    CREATE TABLE source_series (
        series_id TEXT PRIMARY KEY,
        title TEXT,
        publisher TEXT,
        place TEXT,
        year_start INTEGER,
        year_end INTEGER,
        cycle_count INTEGER,
        mapping_pages INTEGER
    );
    CREATE TABLE dossiers (
        dossier_id TEXT PRIMARY KEY,
        title TEXT,
        period TEXT,
        status TEXT,
        primary_sources INTEGER,
        official_retrospectives INTEGER,
        scholarly_research INTEGER,
        timeline_count INTEGER,
        people_count INTEGER,
        organizations_count INTEGER,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0
    );
    CREATE TABLE page_provenance_candidate (
        provenance_id TEXT PRIMARY KEY,
        source_id TEXT,
        source_file TEXT,
        source_sha256 TEXT,
        physical_page_no INTEGER,
        page_image_path TEXT,
        page_image_sha256 TEXT,
        ocr_md_path TEXT,
        ocr_md_sha256 TEXT,
        ocr_engine TEXT,
        ocr_model TEXT,
        ocr_mode TEXT,
        machine_visual_status TEXT,
        citation_ready INTEGER DEFAULT 0,
        human_verified INTEGER DEFAULT 0,
        year INTEGER,
        period TEXT
    );
    """)
    # Load research_materials from T03 + T21 + T25 + T37 + T18 + T55
    materials = []
    for path in [
        RESEARCH_DIR / "T03_OFFICIAL_IDENTITY_AUDIT.jsonl",
        RESEARCH_DIR / "T21_1948_1949_OFFICIAL.jsonl",
        RESEARCH_DIR / "T25_1950_1976_OFFICIAL.jsonl",
        RESEARCH_DIR / "T37_1949_1957_OFFICIAL.jsonl",
        RESEARCH_DIR / "T18_OFFICIAL_1977_2000.jsonl",
        RESEARCH_DIR / "T55_1977_2000_OFFICIAL.jsonl",
        RESEARCH_DIR / "T06_PRIMARY_SOURCE_ACCEPTANCE.json",
        RESEARCH_DIR / "T17_HK_PRIMARY_LEDGER.jsonl",
        RESEARCH_DIR / "T22_1941_1943_ARCHIVE_CATALOG.jsonl",
        RESEARCH_DIR / "T30_1941_1945_SCHOLARLY.jsonl",
    ]:
        if not path.exists():
            continue
        if path.suffix == ".jsonl":
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        r = json.loads(line)
                    except Exception:
                        continue
                    cid = r.get("candidate_id") or r.get("record_id")
                    if not cid:
                        continue
                    materials.append({
                        "candidate_id": cid,
                        "title": r.get("title", ""),
                        "source_url": r.get("source_url", ""),
                        "local_path": r.get("local_path"),
                        "local_sha256": r.get("local_sha256"),
                        "institution_type": r.get("institution_type"),
                        "research_card_category": r.get("research_card_category") or r.get("layer"),
                        "research_theme_phase": r.get("research_theme_phase") or r.get("period"),
                        "rights_status": r.get("rights_status", "PUBLIC_LEGAL_SOURCE"),
                    })
    # Add T53 + T57 1957-1976 candidates
    for path in [
        ROOT / "data/domestic/1957_1976_acquisition_20260730/T53_1957_1976_ACQUISITION.jsonl",
        ROOT / "data/domestic/1957_1976_acquisition_v2_20260730/T57_1957_1976_V2_CANDIDATES.jsonl",
    ]:
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                cid = r.get("candidate_id")
                if not cid:
                    continue
                materials.append({
                    "candidate_id": cid,
                    "title": r.get("title", ""),
                    "source_url": r.get("source_url", ""),
                    "local_path": None,
                    "local_sha256": None,
                    "institution_type": r.get("institution_type"),
                    "research_card_category": r.get("research_card_category"),
                    "research_theme_phase": r.get("research_theme_phase") or r.get("period"),
                    "rights_status": r.get("rights_status", "PUBLIC_LEGAL_SOURCE"),
                })
    # Dedup
    seen = set()
    deduped = []
    for m in materials:
        if m["candidate_id"] not in seen:
            seen.add(m["candidate_id"])
            deduped.append(m)
    print(f"research_materials: {len(deduped)}")
    for m in deduped:
        cur.execute("""INSERT INTO research_materials (candidate_id, title, source_url, local_path, local_sha256, institution_type, research_card_category, research_theme_phase, citation_ready, human_verified, rights_status)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (m["candidate_id"], m["title"], m["source_url"], m["local_path"], m["local_sha256"], m["institution_type"], m["research_card_category"], m["research_theme_phase"], 0, 0, m["rights_status"]))
    # Load entities
    for path in [
        ENTITIES_DIR / "PEOPLE.jsonl",
        ENTITIES_DIR / "ORGANIZATIONS.jsonl",
        ENTITIES_DIR / "PLACES.jsonl",
    ]:
        if not path.exists():
            continue
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                cur.execute("""INSERT OR REPLACE INTO entities (entity_id, entity_type, canonical_name, aliases, evidence_count, confidence, citation_ready, human_verified, created_at, updated_at, dossier_appearance_count)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                            (r["entity_id"], r["entity_type"], r["canonical_name"], json.dumps(r.get("aliases", [])), r.get("evidence_count", 0), r.get("confidence"), 0, 0, r.get("created_at"), r.get("updated_at"), r.get("dossier_appearance_count", 0)))
    # Load events
    if (ENTITIES_DIR / "EVENTS.jsonl").exists():
        with open(ENTITIES_DIR / "EVENTS.jsonl") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                cur.execute("""INSERT OR REPLACE INTO events (event_id, event_type, label, period, source_record_id, confidence, citation_ready, human_verified, created_at)
                               VALUES (?,?,?,?,?,?,?,?,?)""",
                            (r["event_id"], r.get("event_type"), r.get("label"), r.get("period"), r.get("source_record_id"), r.get("confidence"), 0, 0, r.get("created_at")))
    # Load dossier relations
    rel_count = 0
    for d in sorted(DOSSIERS_DIR.iterdir()):
        if not d.is_dir():
            continue
        rel_path = d / "RELATIONS.jsonl"
        if not rel_path.exists():
            continue
        with open(rel_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                ev = r.get("evidence", {})
                cur.execute("""INSERT OR REPLACE INTO relations (relation_id, subject_id, predicate, object_id, relation_scope, valid_time, machine_confidence, conflict_status, evidence_source_url, evidence_local_path, evidence_excerpt, dossier_id, machine_status, citation_ready, human_verified)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (r["relation_id"], r.get("subject_id"), r.get("predicate"), r.get("object_id"), r.get("relation_scope"), r.get("valid_time"), r.get("machine_confidence"), r.get("conflict_status"), ev.get("source_url", ""), ev.get("local_path"), ev.get("excerpt", ""), r.get("dossier_id"), r.get("machine_status"), 0, 0))
                rel_count += 1
    # Load T39 reclassified
    if (RELATIONS_DIR / "RELATIONS_RECLASSIFIED.jsonl").exists():
        with open(RELATIONS_DIR / "RELATIONS_RECLASSIFIED.jsonl") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                ev = r.get("evidence", {})
                cur.execute("""INSERT OR REPLACE INTO relations (relation_id, subject_id, predicate, object_id, relation_scope, valid_time, machine_confidence, conflict_status, evidence_source_url, evidence_local_path, evidence_excerpt, dossier_id, machine_status, citation_ready, human_verified)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (r.get("relation_id") or f"REL-MAIN-{rel_count}", r.get("subject_id"), r.get("predicate"), r.get("object_id"), r.get("relation_scope"), r.get("valid_time"), r.get("machine_confidence"), r.get("conflict_status"), ev.get("source_url", ""), ev.get("local_path"), ev.get("excerpt", ""), "MAIN", r.get("machine_status"), 0, 0))
                rel_count += 1
    print(f"relations: {rel_count}")
    # Load source_series
    ss_path = RESEARCH_DIR / "source_series_registry_20260730.jsonl"
    if ss_path.exists():
        with open(ss_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                cur.execute("""INSERT OR REPLACE INTO source_series (series_id, title, publisher, place, year_start, year_end, cycle_count, mapping_pages)
                               VALUES (?,?,?,?,?,?,?,?)""",
                            (r.get("series_id"), r.get("title"), r.get("publisher"), r.get("place"), r.get("year_start"), r.get("year_end"), r.get("cycle_count"), r.get("mapping_pages")))
    # Load dossiers
    for d in sorted(DOSSIERS_DIR.iterdir()):
        if not d.is_dir():
            continue
        dossier_md = d / "DOSSIER.md"
        ps = sum(1 for _ in (d / "PRIMARY_SOURCES.jsonl").open() if _.strip())
        orec = sum(1 for _ in (d / "OFFICIAL_RETROSPECTIVES.jsonl").open() if _.strip()) if (d / "OFFICIAL_RETROSPECTIVES.jsonl").exists() else 0
        sr = sum(1 for _ in (d / "SCHOLARLY_RESEARCH.jsonl").open() if _.strip()) if (d / "SCHOLARLY_RESEARCH.jsonl").exists() else 0
        t = sum(1 for _ in (d / "TIMELINE.jsonl").open() if _.strip()) if (d / "TIMELINE.jsonl").exists() else 0
        pe = sum(1 for _ in (d / "PEOPLE.jsonl").open() if _.strip()) if (d / "PEOPLE.jsonl").exists() else 0
        og = sum(1 for _ in (d / "ORGANIZATIONS.jsonl").open() if _.strip()) if (d / "ORGANIZATIONS.jsonl").exists() else 0
        cur.execute("""INSERT OR REPLACE INTO dossiers (dossier_id, title, period, status, primary_sources, official_retrospectives, scholarly_research, timeline_count, people_count, organizations_count, citation_ready, human_verified)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (d.name, d.name, "MACHINE_PROVISIONAL", "MACHINE_PROVISIONAL", ps, orec, sr, t, pe, og, 0, 0))
    # Load page_provenance_candidate from T09-T29b + T35 + T42 + T43 + T50 + T54
    OCR_DIR = ROOT / "work/domestic/minimax_autonomous_research_20260730/ocr"
    page_paths = list(OCR_DIR.glob("T*_PAGE_PROVENANCE.v2.jsonl"))
    page_count = 0
    for pp in page_paths:
        with open(pp) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                pid = r.get("provenance_id")
                if not pid:
                    continue
                cur.execute("""INSERT OR REPLACE INTO page_provenance_candidate (provenance_id, source_id, source_file, source_sha256, physical_page_no, page_image_path, page_image_sha256, ocr_md_path, ocr_md_sha256, ocr_engine, ocr_model, ocr_mode, machine_visual_status, citation_ready, human_verified, year, period)
                               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (pid, r.get("source_id"), r.get("source_file"), r.get("source_sha256"), r.get("physical_page_no"), r.get("page_image_path"), r.get("page_image_sha256"), r.get("ocr_md_path"), r.get("ocr_md_sha256"), r.get("ocr_engine"), r.get("ocr_model"), r.get("ocr_mode"), r.get("machine_visual_status"), 0, 0, r.get("year"), r.get("period")))
                page_count += 1
    print(f"page_provenance_candidate: {page_count}")
    # FTS5 trigram insertion
    for m in deduped:
        cur.execute("""INSERT INTO research_material_fts_trigram (candidate_id, title, source_title, period, year, institution_type, research_card_category)
                       VALUES (?,?,?,?,?,?,?)""",
                    (m["candidate_id"], m["title"], m["title"], m["research_theme_phase"] or "", 0, m["institution_type"] or "", m["research_card_category"] or ""))
    conn.commit()
    # FTS probe
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '民盟'")
    mk = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '中华民国'")
    zhh = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '三次'")
    san = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM research_material_fts_trigram WHERE research_material_fts_trigram MATCH '政协'")
    zhx = cur.fetchone()[0]
    cur.execute("PRAGMA integrity_check")
    integrity = cur.fetchone()[0]
    summary = {
        "task_id": "T58",
        "dryrun_db": str(DRYRUN_DB),
        "rows": {
            "research_materials": len(deduped),
            "entities": sum(1 for _ in (ENTITIES_DIR / "PEOPLE.jsonl").open() if _.strip()) + sum(1 for _ in (ENTITIES_DIR / "ORGANIZATIONS.jsonl").open() if _.strip()) + sum(1 for _ in (ENTITIES_DIR / "PLACES.jsonl").open() if _.strip()),
            "events": sum(1 for _ in (ENTITIES_DIR / "EVENTS.jsonl").open() if _.strip()) if (ENTITIES_DIR / "EVENTS.jsonl").exists() else 0,
            "relations": rel_count,
            "page_provenance_candidate": page_count,
        },
        "fts_probes": {
            "民盟": mk,
            "中华民国": zhh,
            "三次": san,
            "政协": zhx,
        },
        "integrity_check": integrity,
        "formal_db_touched": False,
        "citation_ready_created": 0,
        "human_verified_created": 0,
    }
    out_json = RESEARCH_DIR / "T58_DRYRUN_BUILD.json"
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    conn.close()


if __name__ == "__main__":
    main()
