#!/usr/bin/env python3
"""Batch 12 migrate: demote unsafe short-page citation_ready flags.

Only demotes (never promotes). Applies machine_review_note from Batch12 dispositions.
Safety: exact DB hash guard, backup, transaction, FK/integrity verification.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from _guard import guard

guard()
BASE = Path(__file__).resolve().parents[2]
AN = BASE / "work/deepseek-20260803/02_analysis"
OUT = BASE / "work/deepseek-20260803/04_migration"
OUT.mkdir(parents=True, exist_ok=True)
DEFAULT_DB = BASE / "data" / "research_index.sqlite"
# Must match Batch10 write-after hash.
EXPECTED_SHA = "fb7cefcf70fcee92fb9d020d20b1c610d102f14aa6aaaf004d34f50237859295"
NOTE_PREFIX = "DeepSeek Batch12 short-page demotion"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_demote_ids() -> list[dict]:
    path = AN / "short_pages_citation_demote.csv"
    if not path.exists():
        raise SystemExit(f"missing {path}; run deepseek_20260803_batch12.py first")
    rows = list(csv.DictReader(open(path, encoding="utf-8-sig")))
    if not rows:
        raise SystemExit("demote list empty")
    return rows


def migrate(db: Path, apply: bool) -> dict:
    before = sha(db)
    if apply and before != EXPECTED_SHA:
        raise SystemExit(f"hash mismatch: expected {EXPECTED_SHA}, got {before}")

    demote_rows = load_demote_ids()
    page_ids = [int(r["page_id"]) for r in demote_rows]
    if len(page_ids) != len(set(page_ids)):
        raise SystemExit("duplicate page_id in demote list")

    # disposition lookup for notes
    disp = {
        int(r["page_id"]): r
        for r in csv.DictReader(open(AN / "short_pages_dispositions.csv", encoding="utf-8-sig"))
    }

    target = db
    backup = None
    if not apply:
        target = OUT / "research_index.batch12.dryrun.sqlite"
        shutil.copy2(db, target)
    else:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        backup = db.with_name(db.name + f".pre_deepseek_batch12_{stamp}.bak")
        shutil.copy2(db, backup)
        if sha(backup) != before:
            raise SystemExit("backup hash mismatch")

    now = datetime.now().isoformat(timespec="seconds")
    con = sqlite3.connect(target)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys=ON")
    con.execute("BEGIN IMMEDIATE")
    stats: dict = {}
    try:
        # Verify each target currently has citation_ready=1 and is still short.
        q = ",".join("?" * len(page_ids))
        live = con.execute(
            f"""
            SELECT p.id AS page_id, length(trim(coalesce(p.text,''))) AS n,
                   pp.citation_ready, pp.needs_human_review, pp.review_status
            FROM pages p
            JOIN page_provenance pp ON pp.page_id = p.id
            WHERE p.id IN ({q})
            """,
            page_ids,
        ).fetchall()
        if len(live) != len(page_ids):
            missing = set(page_ids) - {int(r["page_id"]) for r in live}
            raise RuntimeError(f"missing provenance for page_ids: {sorted(missing)[:20]}")
        bad = [dict(r) for r in live if r["citation_ready"] != 1 or r["n"] >= 120]
        if bad:
            raise RuntimeError(f"unexpected state for {len(bad)} pages (sample {bad[:3]})")

        updated = 0
        for r in live:
            pid = int(r["page_id"])
            d = disp.get(pid, {})
            note = (
                f"{NOTE_PREFIX}: text_len={r['n']}; "
                f"code={d.get('disposition_code','')}; "
                f"{d.get('disposition_label','short page')}; "
                f"action=citation_ready 1→0, needs_human_review=1, review_status=review_only"
            )
            cur = con.execute(
                """
                UPDATE page_provenance
                SET citation_ready = 0,
                    needs_human_review = 1,
                    review_status = 'review_only',
                    machine_review_note = CASE
                        WHEN machine_review_note IS NULL OR trim(machine_review_note) = ''
                        THEN ?
                        ELSE machine_review_note || ' | ' || ?
                    END,
                    updated_at = ?
                WHERE page_id = ? AND citation_ready = 1
                """,
                (note, note, now, pid),
            )
            updated += cur.rowcount
        stats["pages_targeted"] = len(page_ids)
        stats["pages_demoted"] = updated
        if updated != len(page_ids):
            raise RuntimeError(f"demoted {updated} != targeted {len(page_ids)}")

        # Also stamp empty pages' notes even if already citation_ready=0 (audit trail).
        empty_ids = [
            int(r["page_id"])
            for r in csv.DictReader(open(AN / "short_pages_batch12_refresh.csv", encoding="utf-8-sig"))
            if r["batch7_bucket"] == "Q0_EMPTY"
        ]
        empty_stamped = 0
        for pid in empty_ids:
            d = disp.get(pid, {})
            note = (
                f"{NOTE_PREFIX} empty-page audit: code={d.get('disposition_code','D0')}; "
                f"{d.get('recommended_action','re-OCR / no citation')}"
            )
            cur = con.execute(
                """
                UPDATE page_provenance
                SET needs_human_review = 1,
                    review_status = CASE
                        WHEN review_status IN ('machine_verified','human_verified') THEN 'review_only'
                        ELSE coalesce(nullif(review_status,''), 'review_only')
                    END,
                    machine_review_note = CASE
                        WHEN machine_review_note IS NULL OR trim(machine_review_note) = '' THEN ?
                        WHEN instr(machine_review_note, ?) > 0 THEN machine_review_note
                        ELSE machine_review_note || ' | ' || ?
                    END,
                    citation_ready = 0,
                    updated_at = ?
                WHERE page_id = ?
                """,
                (note, NOTE_PREFIX, note, now, pid),
            )
            empty_stamped += cur.rowcount
        stats["empty_pages_stamped"] = empty_stamped

        # Post-conditions
        still_ready = con.execute(
            f"""
            SELECT count(*) FROM page_provenance pp
            JOIN pages p ON p.id = pp.page_id
            JOIN documents d ON d.id = p.document_id
            WHERE d.source_platform='domestic'
              AND length(trim(coalesce(p.text,''))) < 120
              AND pp.citation_ready = 1
            """
        ).fetchone()[0]
        stats["short_pages_still_citation_ready"] = still_ready
        if still_ready != 0:
            raise RuntimeError(f"still have {still_ready} short citation_ready pages")

        fk = con.execute("PRAGMA foreign_key_check").fetchall()
        integ = con.execute("PRAGMA integrity_check").fetchone()[0]
        stats["foreign_key_violations"] = len(fk)
        stats["integrity_check"] = integ
        if fk or integ != "ok":
            raise RuntimeError(f"validation failed fk={len(fk)} integrity={integ}")

        con.commit()
    except Exception:
        con.rollback()
        con.close()
        raise
    con.close()

    after = sha(target)
    result = {
        "mode": "apply" if apply else "dry-run",
        "database": str(target),
        "source_sha256": before,
        "result_sha256": after,
        "backup": str(backup) if backup else None,
        "stats": stats,
        "timestamp": datetime.now().isoformat(),
    }
    out_name = "batch12_apply_result.json" if apply else "batch12_dryrun_result.json"
    (OUT / out_name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=DEFAULT_DB)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print(json.dumps(migrate(a.db, a.apply), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
