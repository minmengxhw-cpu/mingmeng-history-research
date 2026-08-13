"""受限引用页和负向公报核查的元数据回归。"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = (ROOT / "data" / "research_index.sqlite").resolve()


def test_guangmingbao_issue8_11_pages_have_bounded_scope():
    with sqlite3.connect(DB_PATH) as connection:
        rows = connection.execute(
            """SELECT page_id, citation_ready, needs_human_review, review_status,
                      event_tags, human_review_note
               FROM page_provenance
               WHERE page_id IN (16367, 16634, 16636)
               ORDER BY page_id"""
        ).fetchall()
    assert [row[0] for row in rows] == [16367, 16634, 16636]
    for page_id, citation_ready, needs_human_review, review_status, event_tags, note in rows:
        assert (citation_ready, needs_human_review, review_status) == (1, 0, "human_verified"), page_id
        assert "review_scope=periodical_issue_identity_editorial_title" in (event_tags or ""), page_id
        assert "逐字引文" in (note or ""), page_id


def test_1947_gazette_2974_is_explicit_negative_check():
    chain = json.loads((ROOT / "data" / "domestic" / "topic_evidence_chain.json").read_text(encoding="utf-8"))
    item = next(row for row in chain if row["event_id"] == "domestic-1947-illegal-dissolution")
    checks = item["layers"]["negative_checks"]
    target = next(row for row in checks if "2974" in row["label"])
    assert target["status"] == "negative_control"
    assert "未见目标公文" in target["caveat"]
    assert "不证明行政原件不存在" in target["caveat"]
