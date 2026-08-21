"""国内开放主证据追索队列的结构和安全边界测试。"""

from __future__ import annotations

from scripts.domestic.build_primary_retrieval_queue import build_queue, read_formal_page_scopes


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
    result = build_queue(
        coverage,
        chains,
        candidates,
        audits,
        formal_index={
            "c-catalogue": {
                "formal_ingested_document_id": 7,
                "formal_doc_key": "contemporary-report",
                "formal_page_count": 2,
                "formal_strict_citation_page_count": 0,
                "formal_provenance_page_count": 2,
                "formal_anchored_page_count": 2,
                "formal_ingest_status": "FORMAL_PAGES_REVIEW_ONLY",
            }
        },
        formal_index_available=True,
    )
    target = result["topics"][0]["missing_primary"][0]
    assert target["retrieval_class"] == "AUTHORIZED_VIEWER_REQUIRED"
    assert "有权限账户" in target["next_action"]
    assert "不能替代" in target["next_action"]
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


def test_retrieval_queue_uses_explicit_metadata_action_override():
    result = build_queue(
        [{"event_id": "e", "event_name": "事件", "primary_evidence_status": "partial"}],
        {"e": {"layers": {"missing_primary": [{"target": "目标", "status": "open"}]} }},
        {},
        {},
        action_overrides={("e", "目标"): "按已确认馆藏路线取得影像并记录哈希"},
    )
    assert result["topics"][0]["missing_primary"][0]["next_action"] == "按已确认馆藏路线取得影像并记录哈希"


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


def test_retrieval_queue_keeps_exact_archive_lead_when_public_routes_are_capped():
    candidate_ids = [f"public-{index}" for index in range(13)] + ["shac-lead"]
    coverage = [{"event_id": "e", "event_name": "1947年解散民盟", "primary_evidence_status": "partial", "domestic_candidate_ids": candidate_ids}]
    chains = {"e": {"layers": {"missing_primary": [{"target": "1947年解散民盟原件", "status": "open"}]}}}
    candidates = {
        candidate_id: {
            "candidate_id": candidate_id,
            "title": "解散民盟相关候选 " + candidate_id,
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
        for candidate_id in candidate_ids[:-1]
    }
    candidates["shac-lead"] = {
        "candidate_id": "shac-lead",
        "title": "奉令为宣布民主同盟为非法团体转令遵照由",
        "repository_code": "SHAC",
        "repository_name": "上海市档案馆",
        "catalog_reference": "上档6-5-1216",
        "document_date": "1947-11-02",
        "document_date_precision": "day",
        "document_date_role": "source_document",
        "event_context_date": "1947-11-11",
        "event_context_date_precision": "day",
        "evidence_type": "printed_finding_aid",
        "online_availability": "catalogue_only_online",
        "access_mode": "open",
        "authenticity_level_proposed": "L4",
        "relevance_grade_proposed": "related",
        "review_status": "accepted",
        "source_url": "https://example.invalid/finding-aid",
    }
    result = build_queue(coverage, chains, candidates, {})
    routes = result["topics"][0]["candidate_routes"]
    shac = next(row for row in routes if row["candidate_id"] == "shac-lead")
    assert shac["route_status"] == "CATALOGUE_OR_FINDING_AID"
    assert shac["catalog_reference"] == "上档6-5-1216"
    assert shac["document_date"] == "1947-11-02"
    assert shac["event_context_date"] == "1947-11-11"
    # The exact SHAC lead must remain visible, but a direct public-item route
    # still determines the next action for this target.
    assert result["topics"][0]["missing_primary"][0]["retrieval_class"] == "PUBLIC_ITEM_VERIFICATION"


def test_retrieval_queue_surfaces_formal_pages_without_closing_primary_gap():
    coverage = [
        {
            "event_id": "e",
            "event_name": "1947年解散民盟",
            "primary_evidence_status": "partial",
            "domestic_candidate_ids": ["candidate"],
        }
    ]
    chains = {
        "e": {
            "layers": {
                "missing_primary": [
                    {"target": "1947年解散民盟政府公函原件", "status": "open"}
                ]
            }
        }
    }
    candidates = {
        "candidate": {
            "candidate_id": "candidate",
            "title": "解散民盟政府公函影像",
            "evidence_type": "digital_image",
            "online_availability": "full_item_online",
            "access_mode": "open",
            "authenticity_level_proposed": "L2",
            "relevance_grade_proposed": "core",
            "source_url": "https://example.invalid/item",
        }
    }
    result = build_queue(
        coverage,
        chains,
        candidates,
        {},
        formal_index={
            "candidate": {
                "formal_ingested_document_id": 12,
                "formal_doc_key": "domestic-1947-letter",
                "formal_page_count": 4,
                "formal_strict_citation_page_count": 0,
                "formal_provenance_page_count": 4,
                "formal_anchored_page_count": 4,
                "formal_ingest_status": "FORMAL_PAGES_REVIEW_ONLY",
            }
        },
        formal_index_available=True,
    )
    route = result["topics"][0]["candidate_routes"][0]
    target = result["topics"][0]["missing_primary"][0]
    assert route["formal_ingest_status"] == "FORMAL_PAGES_REVIEW_ONLY"
    assert target["formal_page_count"] == 4
    assert "不要重复下载或 OCR" in target["next_action"]
    assert result["formal_index"]["metadata_only"] is True
    assert result["formal_db_written"] is False


def test_retrieval_queue_matches_event_tags_and_keeps_mmhist_surrogate():
    result = build_queue(
        [
            {
                "event_id": "e",
                "event_name": "1946年拒绝国民大会",
                "primary_evidence_status": "partial",
                "domestic_candidate_ids": ["compiled-notice"],
            }
        ],
        {
            "e": {
                "layers": {
                    "missing_primary": [
                        {"target": "1946年民盟正式拒绝参加国民大会的独立原件", "status": "open"}
                    ]
                }
            }
        },
        {
            "compiled-notice": {
                "candidate_id": "compiled-notice",
                "title": "中国民主同盟总部秘书处紧急通告",
                "repository_code": "MMHIST",
                "catalog_reference": "正式汇编印刷页246；公开扫描PDF第276页",
                "document_date": "1946-11-14",
                "event_tags": ["1946拒绝国民大会"],
                "evidence_type": "digital_image",
                "online_availability": "surrogate_online",
                "access_mode": "open",
                "authenticity_level_proposed": "L2",
                "relevance_grade_proposed": "core",
                "review_status": "accepted",
                "source_url": "https://example.invalid/compiled.pdf",
            }
        },
        {},
    )
    route = result["topics"][0]["candidate_routes"][0]
    assert route["target_match"] is True
    assert route["route_status"] == "PUBLIC_SURROGATE"
    assert route["candidate_id"] == "compiled-notice"


def test_retrieval_queue_exposes_existing_event_pages_without_closing_gap():
    result = build_queue(
        [
            {
                "event_id": "e",
                "event_name": "1941年成立",
                "primary_evidence_status": "partial",
                "domestic_candidate_ids": [],
            }
        ],
        {
            "e": {
                "layers": {
                    "missing_primary": [
                        {"target": "1941年成立独立原件", "status": "open"}
                    ]
                }
            }
        },
        {},
        {},
        event_link_pages={
            "e": [
                {
                    "page_id": 1473,
                    "page_label": "009",
                    "doc_key": "domestic-ocr/formation",
                    "strict_citation": True,
                }
            ]
        },
        event_link_index_available=True,
    )
    topic = result["topics"][0]
    target = topic["missing_primary"][0]
    assert result["schema"] == "domestic_primary_retrieval_queue.v3"
    assert result["event_link_index"]["page_count"] == 1
    assert topic["event_link_strict_page_count"] == 1
    assert topic["event_link_pages"][0]["page_id"] == 1473
    assert target["status"] == "open"
    assert "专题导航关联的严格页" in target["next_action"]
    assert "不自动关闭主证据缺口" in target["next_action"]
    assert result["body_read"] is False
    assert result["formal_db_written"] is False


def test_formal_page_scope_metadata_is_explicit_and_deduplicated(tmp_path):
    scope_path = tmp_path / "scopes.json"
    scope_path.write_text(
        '{"schema":"domestic_formal_page_scopes.v1",'
        '"body_read":false,"formal_db_written":false,'
        '"scopes":[{"candidate_id":"c","doc_key":"doc",'
        '"page_ids":[1,2],"scope_label":"label","rationale":"reason"}]}',
        encoding="utf-8",
    )
    scopes = read_formal_page_scopes(scope_path)
    assert scopes["c"]["doc_key"] == "doc"
    assert scopes["c"]["page_ids"] == [1, 2]
    assert scopes["c"]["rationale"] == "reason"
