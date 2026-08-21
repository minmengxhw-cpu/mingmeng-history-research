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
    gap_note_ids = {"GAR-220939F16F", "GAR-C36FE834C9"}
    shown_ids = {
        record_id
        for topic in payload["topics"]
        for record_id in topic.get("shown_record_ids", [])
    }
    assert not gap_note_ids & shown_ids


def test_academic_metadata_marks_research_gap_notes_outside_the_crosswalk():
    payload = json.loads((ROOT / "data" / "domestic" / "academic_layer_metadata.json").read_text(encoding="utf-8"))
    records = payload["records"]
    gap_notes = [record for record in records if record.get("record_role") == "RESEARCH_GAP_NOTE"]
    assert {record["external_id"] for record in gap_notes} == {
        "GAR-220939F16F",
        "GAR-C36FE834C9",
    }
    assert all(record["academic_crosswalk_eligible"] is False for record in gap_notes)


def test_parity_defaults_to_versioned_crosswalk():
    from scripts.domestic.build_domestic_parity_matrix_20260813 import DEFAULT_CROSSWALK

    assert DEFAULT_CROSSWALK == ROOT / "data" / "domestic" / "academic_topic_crosswalk.json"
