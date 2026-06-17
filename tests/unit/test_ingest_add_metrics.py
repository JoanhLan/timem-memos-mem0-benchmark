"""Tests for per-add ingest latency aggregation."""

from __future__ import annotations

from utils.ingest_add_metrics import (
    add_latencies_from_session_detail,
    aggregate_add_metrics,
    enrich_session_detail,
)


def test_add_latencies_from_pair_details():
    detail = {
        "success": True,
        "latency_ms": 3000,
        "api_calls": 3,
        "ingest_mode": "pair",
        "pair_details": [
            {"pair_index": 0, "latency_ms": 800, "success": True},
            {"pair_index": 1, "latency_ms": 1000, "success": True},
            {"pair_index": 2, "latency_ms": 1200, "success": True},
        ],
    }
    assert add_latencies_from_session_detail(detail) == [800.0, 1000.0, 1200.0]


def test_add_latencies_estimated_from_session():
    detail = {
        "success": True,
        "latency_ms": 9000,
        "api_calls": 3,
        "ingest_mode": "pair",
    }
    assert add_latencies_from_session_detail(detail) == [3000.0, 3000.0, 3000.0]


def test_aggregate_add_metrics_preserves_session_sum():
    details = [
        {
            "success": True,
            "latency_ms": 9000,
            "api_calls": 3,
            "ingest_mode": "pair",
            "input_tokens": 100,
        },
        {
            "success": True,
            "latency_ms": 400,
            "api_calls": 1,
            "ingest_mode": "session",
            "input_tokens": 50,
        },
    ]
    metrics = aggregate_add_metrics(details, estimated=True)
    assert metrics["add_count"] == 4
    assert metrics["add_success_count"] == 4
    assert metrics["session_count"] == 2
    assert metrics["add_latency_estimated"] is True
    assert metrics["sum_latency_ms"] == 9400.0
    assert metrics["session_latency"]["p50"] == 4700.0
    assert metrics["details"][0]["avg_add_latency_ms"] == 3000.0


def test_enrich_session_detail_creates_estimated_pairs():
    row = enrich_session_detail(
        {"success": True, "latency_ms": 1000, "api_calls": 2, "ingest_mode": "pair"}
    )
    assert row["avg_add_latency_ms"] == 500.0
    assert len(row["pair_details"]) == 2
    assert row["pair_details"][0]["estimated"] is True
