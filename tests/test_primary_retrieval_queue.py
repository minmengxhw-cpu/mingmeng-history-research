"""国内开放主证据追索队列的结构和安全边界测试。"""

from __future__ import annotations

from scripts.domestic.build_primary_retrieval_queue import build_queue


def test_retrieval_queue_keeps_locked_viewer_open():
    coverage = [
        {
            "event_id": "domestic-1947-illegal-dissolution",
            "event_name": "1947年民盟被宣布非法",
            "primary_evidence_status": "partial",
            "domestic_candidate_ids": ["c-locked", "c-catalogue"],
        }
    ]
    chains = {
        "domestic-1947-illegal-dissolution": {
            "layers": {
                "missing_primary": [
                    {"target": "1947年解散民盟政府公函原件", "why_it_matters": "确认文种", "status": "open"}
                ]
            }
        }
    }
    candidates = {
        "c-locked": {
            "candidate_id": "c-locked",
            "title": "解散民盟政府公函",
            "repository_code": "DRNH",
            "repository_name": "国史馆",
            "catalog_reference": "002-X",
            "evidence_type": "digital_image",
            "access_mode": "open",
            "online_availability": "full_item_online",
            "authenticity_level_proposed": "L2",
            "relevance_grade_proposed": "core",
            "review_status": "accepted",
            "source_url": "https://example.invalid/item",
        },
        "c-catalogue": {
            "candidate_id": "c-catalogue",
            "title": "目录记录",
            "repository_code": "DRNH",
            "repository_name": "国史馆",
            "catalog_reference": "002-Y",
            "evidence_type": "catalogue",
            "access_mode": "open",
            "online_availability": "catalogue_only_online",
            "authenticity_level_proposed": "L2",
            "relevance_grade_proposed": "core",
            "review_status": "accepted",
            "source_url": "https://example.invalid/catalogue",
        },
    }
    audits = {"c-locked": {"candidate_id": "c-locked", "access_status": "official_viewer_locked"}}
    result = build_queue(coverage, chains, candidates, audits)
    target = result["topics"][0]["missing_primary"][0]
    assert target["retrieval_class"] == "AUTHORIZED_VIEWER_REQUIRED"
    assert result["body_read"] is False
    assert result["formal_db_written"] is False
    assert result["auto_download"] is False
    assert result["auto_promote_primary_closed"] is False


def test_retrieval_queue_does_not_fail_when_candidate_is_missing():
    result = build_queue(
        [{"event_id": "e", "event_name": "事件", "primary_evidence_status": "partial", "domestic_candidate_ids": ["missing"]}],
        {"e": {"layers": {"missing_primary": [{"target": "1947年解散民盟原件", "status": "open"}]}}},
        {},
        {},
    )
    assert result["missing_candidate_ids"] == ["missing"]
    assert result["topics"][0]["missing_primary"][0]["retrieval_class"] == "ORIGINAL_ROUTE_UNRESOLVED"


def test_retrieval_queue_keeps_audited_route_when_many_public_candidates_exist():
    candidate_ids = [f"public-{index}" for index in range(13)] + ["locked"]
    coverage = [{"event_id": "e", "event_name": "事件", "primary_evidence_status": "partial", "domestic_candidate_ids": candidate_ids}]
    chains = {"e": {"layers": {"missing_primary": [{"target": "1947年解散民盟原件", "status": "open"}]}}}
    candidates = {
        candidate_id: {
            "candidate_id": candidate_id,
            "title": "解散民盟公函 " + candidate_id,
            "repository_code": "NLC",
            "repository_name": "国家图书馆",
            "evidence_type": "digital_image",
            "online_availability": "full_item_online",
            "access_mode": "open",
            "authenticity_level_proposed": "L1",
            "relevance_grade_proposed": "core",
            "review_status": "accepted",
            "source_url": "https://example.invalid/item",
        }
        for candidate_id in candidate_ids
    }
    result = build_queue(coverage, chains, candidates, {"locked": {"access_status": "official_viewer_locked"}})
    routes = result["topics"][0]["candidate_routes"]
    assert any(row["candidate_id"] == "locked" for row in routes)
    assert result["topics"][0]["missing_primary"][0]["retrieval_class"] == "AUTHORIZED_VIEWER_REQUIRED"
