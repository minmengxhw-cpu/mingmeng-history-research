"""Tests for the parameterized hash-only local/formal reconciliation tool."""

from __future__ import annotations

import json
import sqlite3

from scripts.closeout.reconcile_local_formal_hashes import reconcile, write_outputs


def test_reconcile_matches_bytes_without_parsing_documents(tmp_path):
    formal = tmp_path / "formal.pdf"
    local_same = tmp_path / "copy.pdf"
    local_other = tmp_path / "other.pdf"
    formal.write_bytes(b"same bytes")
    local_same.write_bytes(b"same bytes")
    local_other.write_bytes(b"different bytes")

    db = tmp_path / "research.sqlite"
    connection = sqlite3.connect(db)
    connection.execute("create table sources (local_path text)")
    connection.execute("insert into sources(local_path) values (?)", (str(formal),))
    connection.commit()
    connection.close()

    inventory = tmp_path / "inventory.jsonl"
    inventory.write_text(
        "\n".join(
            json.dumps(
                {
                    "metadata_id": metadata_id,
                    "local_path": str(path),
                    "filename": path.name,
                    "bytes": path.stat().st_size,
                    "suffix": path.suffix,
                }
            )
            for metadata_id, path in (("LOCAL-1", local_same), ("LOCAL-2", local_other))
        )
        + "\n",
        encoding="utf-8",
    )

    report, details, unmatched = reconcile(inventory, db)
    output = tmp_path / "output"
    write_outputs(output, report, details, unmatched)

    assert report["formal_hashed_file_count"] == 1
    assert report["local_hashed_file_count"] == 2
    assert report["exact_formal_source_hash_local_file_count"] == 1
    assert report["unmatched_local_file_count"] == 1
    assert report["body_read"] is False
    assert report["formal_db_written"] is False
    assert len(unmatched) == 1
    assert all("local_path" not in row for row in details)
    assert "/Users/" not in (output / "REPORT.json").read_text(encoding="utf-8")
