"""Tests for search-judge retrieval pipeline."""

from __future__ import annotations

import asyncio
import time

import pytest

from utils.retrieval_pipeline import run_search_judge_pipeline, run_search_judge_two_phase


async def _slow_search(delay: float, tag: str) -> dict:
    await asyncio.sleep(delay)
    return {"question": tag, "_memory_records": [], "latency_ms": delay * 1000}


async def _slow_judge(row: dict) -> dict:
    await asyncio.sleep(0.05)
    row = dict(row)
    row.pop("_memory_records", None)
    row["judge"] = {"can_answer": True}
    return row


@pytest.mark.asyncio
async def test_pipeline_faster_than_two_phase_when_judge_is_bottleneck():
    n = 8
    search_delay = 0.02
    tasks = [
        (f"q{i}", lambda i=i: _slow_search(search_delay, f"q{i}"))
        for i in range(n)
    ]

    async def judge_fn(row: dict) -> dict:
        await asyncio.sleep(0.08)
        row = dict(row)
        row.pop("_memory_records", None)
        row["judge"] = {}
        return row

    started = time.perf_counter()
    await run_search_judge_two_phase(
        tasks,
        query_concurrency=4,
        judge_concurrency=2,
        judge_row_fn=judge_fn,
    )
    two_phase_ms = (time.perf_counter() - started) * 1000

    started = time.perf_counter()
    await run_search_judge_pipeline(
        tasks,
        query_concurrency=4,
        judge_concurrency=2,
        judge_row_fn=judge_fn,
    )
    pipeline_ms = (time.perf_counter() - started) * 1000

    assert pipeline_ms < two_phase_ms


@pytest.mark.asyncio
async def test_pipeline_preserves_order():
    tasks = [
        ("a", lambda: _slow_search(0.01, "a")),
        ("b", lambda: _slow_search(0.01, "b")),
        ("c", lambda: _slow_search(0.01, "c")),
    ]
    results = await run_search_judge_pipeline(
        tasks,
        query_concurrency=2,
        judge_concurrency=2,
        judge_row_fn=_slow_judge,
    )
    assert [key for key, _ in results] == ["a", "b", "c"]


@pytest.mark.asyncio
async def test_pipeline_without_judge():
    tasks = [("x", lambda: _slow_search(0.01, "x"))]
    results = await run_search_judge_pipeline(
        tasks,
        query_concurrency=1,
        judge_concurrency=1,
        judge_row_fn=None,
    )
    _, row = results[0]
    assert row.get("judge") == {}
    assert "_memory_records" not in row
