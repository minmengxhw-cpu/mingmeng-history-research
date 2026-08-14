import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_versioned_academic_crosswalk_is_metadata_only_and_complete():
    path = ROOT / "data" / "domestic" / "academic_topic_crosswalk.json"
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "academic_topic_crosswalk.v1"
    assert payload["status"] == "PASS"
    assert payload["body_read"] is False
    assert len(payload["topics"]) == 9
    assert payload["total_topic_matches"] == 159
    assert all("fulltext" not in row for row in payload["topics"])


def test_parity_defaults_to_versioned_crosswalk():
    from scripts.domestic.build_domestic_parity_matrix_20260813 import DEFAULT_CROSSWALK

    assert DEFAULT_CROSSWALK == ROOT / "data" / "domestic" / "academic_topic_crosswalk.json"
