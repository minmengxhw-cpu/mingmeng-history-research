from __future__ import annotations

import datetime as dt

from scripts.closeout.refresh_closeout_if_stale import needs_refresh


def test_needs_refresh_distinguishes_fresh_and_stale_snapshots():
    snapshot = {
        "schema_version": "domestic_platform_closeout_snapshot.v1",
        "generated_at": "2026-08-30T00:00:00+00:00",
    }
    now = dt.datetime(2026, 8, 30, 0, 30, tzinfo=dt.timezone.utc)
    assert needs_refresh(snapshot, now=now, max_age_seconds=3600) is False
    assert needs_refresh(snapshot, now=dt.datetime(2026, 8, 30, 2, 0, tzinfo=dt.timezone.utc), max_age_seconds=3600) is True


def test_needs_refresh_rejects_missing_or_invalid_snapshot():
    assert needs_refresh(None) is True
    assert needs_refresh({"schema_version": "wrong"}) is True
    assert needs_refresh(
        {"schema_version": "domestic_platform_closeout_snapshot.v1", "generated_at": "not-a-date"}
    ) is True
