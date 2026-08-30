#!/usr/bin/env python3
"""Validate the metadata-only four-layer domestic topic evidence chain.

This validator checks that every topic has explicit primary/cross-source/
negative-check/missing-primary layers, that page references resolve to the
formal SQLite index, and that an item labelled strict_citation still satisfies
the formal page_provenance gate.  It never reads page bodies and never writes
to the database.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB = ROOT / "data" / "research_index.sqlite"
DEFAULT_COVERAGE = ROOT / "data" / "domestic" / "event_coverage.json"
DEFAULT_CHAIN = ROOT / "data" / "domestic" / "topic_evidence_chain.json"
LAYERS = ("primary", "cross_source", "negative_checks", "missing_primary")
STRICT_SQL = "pp.citation_ready=1 AND pp.needs_human_review=0 AND pp.review_status='human_verified'"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(db_path: Path, coverage_path: Path, chain_path: Path) -> dict:
    coverage = load_json(coverage_path)
    chains = load_json(chain_path)
    errors: list[str] = []
    coverage_ids = [str(item.get("event_id")) for item in coverage if isinstance(item, dict)]
    chain_ids = [str(item.get("event_id")) for item in chains if isinstance(item, dict)]
    if len(coverage_ids) != len(set(coverage_ids)):
        errors.append("event_coverage.json contains duplicate event_id")
    if len(chain_ids) != len(set(chain_ids)):
        errors.append("topic_evidence_chain.json contains duplicate event_id")
    missing = sorted(set(coverage_ids) - set(chain_ids))
    orphan = sorted(set(chain_ids) - set(coverage_ids))
    if missing:
        errors.append("missing chains: " + ", ".join(missing))
    if orphan:
        errors.append("orphan chains: " + ", ".join(orphan))

    chain_by_id = {str(item.get("event_id")): item for item in chains if isinstance(item, dict)}
    strict_items = 0
    page_items = 0
    page_refs: list[dict[str, object]] = []
    layer_counts = {layer: 0 for layer in LAYERS}
    with sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        for event_id in coverage_ids:
            chain = chain_by_id.get(event_id)
            if not chain:
                continue
            layers = chain.get("layers")
            if not isinstance(layers, dict):
                errors.append(f"{event_id}: layers is not an object")
                continue
            if set(layers) != set(LAYERS):
                errors.append(f"{event_id}: layers must be exactly {','.join(LAYERS)}")
            if not isinstance(layers.get("missing_primary"), list) or not layers.get("missing_primary"):
                errors.append(f"{event_id}: missing_primary must contain at least one open target")
            for layer in LAYERS:
                items = layers.get(layer, [])
                if not isinstance(items, list):
                    errors.append(f"{event_id}/{layer}: must be a list")
                    continue
                layer_counts[layer] += len(items)
                for index, item in enumerate(items):
                    if not isinstance(item, dict):
                        errors.append(f"{event_id}/{layer}[{index}]: must be an object")
                        continue
                    if not str(item.get("label") or item.get("target") or "").strip():
                        errors.append(f"{event_id}/{layer}[{index}]: missing label/target")
                    if layer == "missing_primary" and item.get("status") != "open":
                        errors.append(f"{event_id}/{layer}[{index}]: status must be open")
                    if layer == "missing_primary":
                        if not str(item.get("target") or "").strip():
                            errors.append(f"{event_id}/{layer}[{index}]: missing target")
                        if not str(item.get("why_it_matters") or "").strip():
                            errors.append(f"{event_id}/{layer}[{index}]: missing why_it_matters")
                        if not str(item.get("next_action") or "").strip():
                            errors.append(f"{event_id}/{layer}[{index}]: missing next_action")
                    if "page_id" not in item:
                        continue
                    page_items += 1
                    page_refs.append(
                        {
                            "event_id": event_id,
                            "layer": layer,
                            "page_id": item["page_id"],
                            "status": item.get("status"),
                            "doc_key": item.get("doc_key"),
                        }
                    )
                    row = conn.execute(
                        """SELECT d.doc_key, d.source_platform, pp.review_status,
                                  pp.citation_ready, pp.needs_human_review
                           FROM pages p JOIN documents d ON d.id=p.document_id
                           LEFT JOIN page_provenance pp ON pp.page_id=p.id
                           WHERE p.id=?""",
                        (item["page_id"],),
                    ).fetchone()
                    if row is None:
                        errors.append(f"{event_id}/{layer}[{index}]: unknown page_id {item['page_id']}")
                        continue
                    if row["source_platform"] != "domestic":
                        errors.append(f"{event_id}/{layer}[{index}]: page {item['page_id']} is not domestic")
                    if row["doc_key"] != item.get("doc_key"):
                        errors.append(
                            f"{event_id}/{layer}[{index}]: doc_key mismatch for page {item['page_id']}"
                        )
                    if item.get("status") == "strict_citation":
                        strict_items += 1
                        if not (
                            row["review_status"] == "human_verified"
                            and row["citation_ready"] == 1
                            and row["needs_human_review"] == 0
                        ):
                            errors.append(
                                f"{event_id}/{layer}[{index}]: strict_citation does not satisfy page gate"
                            )

    return {
        "db_path": str(db_path),
        "coverage_path": str(coverage_path),
        "chain_path": str(chain_path),
        "topics": len(coverage_ids),
        "chains": len(chain_ids),
        "page_items": page_items,
        "page_refs": page_refs,
        "strict_citation_items": strict_items,
        "layer_item_counts": layer_counts,
        "missing_chains": missing,
        "orphan_chains": orphan,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--chain", type=Path, default=DEFAULT_CHAIN)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.db, args.coverage, args.chain)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
