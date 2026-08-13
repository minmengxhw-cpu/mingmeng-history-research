#!/usr/bin/env python3
"""Validate the declaration-only domestic/foreign topic comparison layer.

The cards are research navigation, not evidence assertions.  This check keeps
the nine-topic crosswalk complete and prevents a topic from silently losing its
boundary or next-action note.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_COVERAGE = ROOT / "data/domestic/event_coverage.json"
DEFAULT_CARDS = ROOT / "data/domestic/topic_comparison_cards.json"

REQUIRED = {
    "event_id",
    "research_question",
    "domestic_anchor",
    "foreign_anchor",
    "difference",
    "boundary",
    "next_action",
    "academic_use",
}


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(coverage_path: Path, cards_path: Path) -> dict:
    coverage = read_json(coverage_path)
    cards = read_json(cards_path)
    errors: list[str] = []
    coverage_ids = [str(row.get("event_id")) for row in coverage if isinstance(row, dict)]
    card_ids = [str(row.get("event_id")) for row in cards if isinstance(row, dict)]
    if len(coverage_ids) != len(set(coverage_ids)):
        errors.append("event_coverage.json contains duplicate event_id")
    if len(card_ids) != len(set(card_ids)):
        errors.append("topic_comparison_cards.json contains duplicate event_id")
    missing = sorted(set(coverage_ids) - set(card_ids))
    extra = sorted(set(card_ids) - set(coverage_ids))
    if missing:
        errors.append("missing cards: " + ", ".join(missing))
    if extra:
        errors.append("orphan cards: " + ", ".join(extra))
    for index, card in enumerate(cards):
        if not isinstance(card, dict):
            errors.append(f"card[{index}] is not an object")
            continue
        for field in sorted(REQUIRED - set(card)):
            errors.append(f"card[{index}] missing {field}")
        for field in sorted(REQUIRED - {"event_id"}):
            if field in card and not str(card[field]).strip():
                errors.append(f"card[{index}] empty {field}")
        if "不能" not in str(card.get("boundary", "")) and "不得" not in str(card.get("boundary", "")):
            errors.append(f"card[{index}] boundary does not state a non-equivalence rule")
    return {
        "coverage_path": str(coverage_path),
        "cards_path": str(cards_path),
        "coverage_topics": len(coverage_ids),
        "comparison_cards": len(card_ids),
        "missing_cards": missing,
        "orphan_cards": extra,
        "errors": errors,
        "status": "PASS" if not errors else "FAIL",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--cards", type=Path, default=DEFAULT_CARDS)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    report = validate(args.coverage, args.cards)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
