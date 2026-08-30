from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

from scripts.domestic.reconcile_source_page_counts import build_rows


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    con.executescript(
        """
        create table documents (
            id integer primary key, doc_key text, title text, local_txt text, local_html text
        );
        create table page_provenance (
            page_id integer primary key, document_id integer, source_file text,
            pdf_page_no integer, physical_page_no integer
        );
        """
    )
    con.executemany(
        "insert into documents values (?, ?, ?, ?, ?)",
        [
            (1, "domestic-page/issue", "canonical", "data/domestic/press_scans/issue.pdf", None),
            (2, "domestic-ocr/NLC:issue-full-ocr", "ocr", "data/domestic/press_scans/issue.pdf", None),
            (3, "domestic-ocr/COLLECTION:P3-issue:ocr-draft", "anchor", "data/domestic/press_scans/issue.pdf", None),
        ],
    )
    provenance = []
    page_id = 1
    for document_id in (1, 2):
        for page_no in range(1, 4):
            provenance.append((page_id, document_id, "data/domestic/press_scans/issue.pdf", page_no, page_no))
            page_id += 1
    provenance.append((page_id, 3, "data/domestic/press_scans/issue.pdf", 1, 1))
    con.executemany("insert into page_provenance values (?, ?, ?, ?, ?)", provenance)
    con.commit()
    con.close()


def test_complete_layers_are_not_treated_as_physical_page_conflict(tmp_path: Path):
    db = tmp_path / "index.sqlite"
    make_db(db)
    inventory = tmp_path / "inventory.csv"
    fields = ["source_path", "pdf_pages", "indexed_pages", "ocr_draft_pages", "status"]
    with inventory.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "source_path": "data/domestic/press_scans/issue.pdf",
                "pdf_pages": "3",
                "indexed_pages": "7",
                "ocr_draft_pages": "3",
                "status": "formal_page_count_anomaly",
            }
        )

    row = build_rows(inventory, db)[0]
    assert row["disposition"] == "RECONCILED_DUPLICATE_COMPLETE_LAYERS"
    assert row["canonical_complete_count"] == 1
    assert row["full_ocr_complete_count"] == 1
    assert row["collection_anchor_pages"] == 1


def test_partial_records_stay_unreconciled(tmp_path: Path):
    db = tmp_path / "index.sqlite"
    make_db(db)
    con = sqlite3.connect(db)
    con.execute("delete from page_provenance where document_id=1 and page_id > 1")
    con.execute("delete from page_provenance where document_id=2")
    con.commit()
    con.close()
    inventory = tmp_path / "inventory.csv"
    fields = ["source_path", "pdf_pages", "indexed_pages", "ocr_draft_pages", "status"]
    with inventory.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "source_path": "data/domestic/press_scans/issue.pdf",
                "pdf_pages": "3",
                "indexed_pages": "1",
                "ocr_draft_pages": "0",
                "status": "indexed_partial_no_draft",
            }
        )

    row = build_rows(inventory, db)[0]
    assert row["disposition"] == "UNRECONCILED_PARTIAL_OR_NONPAGE_RECORDS"
