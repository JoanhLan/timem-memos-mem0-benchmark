"""Tests for retrieval config resolution."""

from __future__ import annotations

from utils.config import resolve_retrieval_config


def test_resolve_retrieval_config_defaults():
    cfg = resolve_retrieval_config()
    assert cfg.query_concurrency == 10
    assert cfg.timem_query_concurrency == 3
    assert cfg.judge_concurrency == 10
    assert cfg.backfill_concurrency == 3
    assert cfg.query_concurrency_for("timem") == 3
    assert cfg.query_concurrency_for("memos") == cfg.query_concurrency
    assert cfg.pipeline_mode is True
    assert cfg.backfill_concurrency >= 1
    assert cfg.judge_max_retries >= 0


def test_resolve_retrieval_config_overrides():
    cfg = resolve_retrieval_config(
        {
            "query_concurrency": 16,
            "judge_concurrency": 8,
            "backfill_concurrency": 5,
            "pipeline_mode": False,
            "judge_max_retries": 2,
        }
    )
    assert cfg.query_concurrency == 16
    assert cfg.judge_concurrency == 8
    assert cfg.backfill_concurrency == 5
    assert cfg.pipeline_mode is False
    assert cfg.judge_max_retries == 2
    report = cfg.to_report_dict()
    assert report["pipeline_mode"] is False
    assert report["backfill_concurrency"] == 5
