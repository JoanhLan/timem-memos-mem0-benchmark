"""Tests for pipeline job (Ingest → optional Backfill → T0)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from benchmark_jobs import JobManager, JobOptions


def test_job_options_allows_empty_backfill_layers():
    opts = JobOptions.from_dict({"backfill_layers": []})
    assert opts.backfill_layers == []


@pytest.mark.asyncio
async def test_pipeline_runs_backfill_when_timem_and_layers(tmp_path, monkeypatch):
    monkeypatch.setattr("benchmark_jobs.REPORTS_DIR", tmp_path)
    manager = JobManager()
    run_id = "pipe-1"
    manager.create_run(run_id)
    options = JobOptions.from_dict(
        {
            "systems": ["timem", "memos"],
            "backfill_layers": ["L2"],
            "wait_timem_l2_on_ingest": False,
        }
    )

    ingest_mock = AsyncMock(return_value={})
    backfill_mock = AsyncMock(return_value={})
    retrieve_mock = AsyncMock(return_value={})

    with (
        patch("benchmark_jobs.run_ingest", ingest_mock),
        patch("benchmark_jobs.run_timem_backfill", backfill_mock),
        patch("benchmark_jobs.run_retrieval", retrieve_mock),
    ):
        await manager._execute(run_id, "pipeline", options, persona_count=1)

    ingest_mock.assert_awaited_once()
    backfill_mock.assert_awaited_once()
    retrieve_mock.assert_awaited_once()
    assert retrieve_mock.await_args.kwargs["mode"] == "T0"


@pytest.mark.asyncio
async def test_pipeline_skips_backfill_without_timem(tmp_path, monkeypatch):
    monkeypatch.setattr("benchmark_jobs.REPORTS_DIR", tmp_path)
    manager = JobManager()
    run_id = "pipe-2"
    manager.create_run(run_id)
    options = JobOptions.from_dict(
        {
            "systems": ["memos"],
            "backfill_layers": ["L2"],
        }
    )

    backfill_mock = AsyncMock(return_value={})

    with (
        patch("benchmark_jobs.run_ingest", AsyncMock(return_value={})),
        patch("benchmark_jobs.run_timem_backfill", backfill_mock),
        patch("benchmark_jobs.run_retrieval", AsyncMock(return_value={})),
    ):
        await manager._execute(run_id, "pipeline", options, persona_count=1)

    backfill_mock.assert_not_called()


@pytest.mark.asyncio
async def test_pipeline_skips_backfill_when_layers_empty(tmp_path, monkeypatch):
    monkeypatch.setattr("benchmark_jobs.REPORTS_DIR", tmp_path)
    manager = JobManager()
    run_id = "pipe-3"
    manager.create_run(run_id)
    options = JobOptions.from_dict(
        {
            "systems": ["timem"],
            "backfill_layers": [],
        }
    )

    backfill_mock = AsyncMock(return_value={})

    with (
        patch("benchmark_jobs.run_ingest", AsyncMock(return_value={})),
        patch("benchmark_jobs.run_timem_backfill", backfill_mock),
        patch("benchmark_jobs.run_retrieval", AsyncMock(return_value={})),
    ):
        await manager._execute(run_id, "pipeline", options, persona_count=1)

    backfill_mock.assert_not_called()
