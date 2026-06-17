"""Tests for retrieval timing metric aggregation."""

from __future__ import annotations

from runners.retrieval_run import _backfill_summary_for_timem


def test_backfill_summary_includes_wall_and_efficiency():
    rows = [
        {"persona_id": "p1", "success": True, "backfill_total_ms": 100.0},
        {"persona_id": "p2", "success": True, "backfill_total_ms": 200.0},
    ]
    summary = _backfill_summary_for_timem("timem", rows, backfill_wall_ms=150.0)
    assert summary["backfill_wall_ms"] == 150.0
    assert summary["sum_persona_backfill_ms"] == 300.0
    assert summary["backfill_parallel_efficiency"] == 2.0
