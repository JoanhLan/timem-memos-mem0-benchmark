"""Tests for ingest concurrency scheduler and config."""

from __future__ import annotations

import asyncio
import time

import pytest

from utils.config import resolve_ingest_config
from utils.ingest_scheduler import run_bounded_tasks, run_bounded_tasks_per_key


@pytest.mark.asyncio
async def test_run_bounded_tasks_preserves_order() -> None:
    async def make(n: int):
        await asyncio.sleep(0.01)
        return n * 2

    tasks = [(i, lambda i=i: make(i)) for i in range(5)]
    results = await run_bounded_tasks(tasks, concurrency=2)
    assert [r for _, r in results] == [0, 2, 4, 6, 8]


@pytest.mark.asyncio
async def test_run_bounded_tasks_limits_concurrency() -> None:
    max_seen = 0
    lock = asyncio.Lock()
    active = 0

    async def work(_: int) -> int:
        nonlocal max_seen, active
        async with lock:
            active += 1
            max_seen = max(max_seen, active)
        await asyncio.sleep(0.05)
        async with lock:
            active -= 1
        return 1

    tasks = [(i, lambda i=i: work(i)) for i in range(8)]
    started = time.perf_counter()
    await run_bounded_tasks(tasks, concurrency=2)
    elapsed = time.perf_counter() - started

    assert max_seen <= 2
    assert elapsed >= 0.15


def test_resolve_ingest_config_defaults() -> None:
    cfg = resolve_ingest_config()
    assert cfg.session_concurrency == 10
    assert cfg.mem0_session_concurrency >= 1
    assert cfg.mem0_poll_mode in ("sync", "deferred", "pipeline")


def test_session_concurrency_for_mem0_capped() -> None:
    cfg = resolve_ingest_config(
        {
            "session_concurrency": 8,
            "mem0_session_concurrency": 2,
        }
    )
    assert cfg.session_concurrency_for("timem") == 8
    assert cfg.session_concurrency_for("mem0") == 2
    assert cfg.session_concurrency_for("memos") == 8


@pytest.mark.asyncio
async def test_run_bounded_tasks_per_key_serializes_same_user() -> None:
    max_same_user = 0
    lock = asyncio.Lock()
    active_by_user: dict[str, int] = {}

    async def work(user_id: str, delay: float) -> str:
        nonlocal max_same_user
        async with lock:
            active_by_user[user_id] = active_by_user.get(user_id, 0) + 1
            max_same_user = max(max_same_user, active_by_user[user_id])
        await asyncio.sleep(delay)
        async with lock:
            active_by_user[user_id] -= 1
        return user_id

    tasks = [
        (i, "user_a", lambda i=i: work("user_a", 0.03))
        for i in range(4)
    ] + [
        (i + 10, "user_b", lambda: work("user_b", 0.03))
        for i in range(4)
    ]
    await run_bounded_tasks_per_key(tasks, concurrency=4, key_concurrency=1)
    assert max_same_user == 1


def test_invalid_poll_mode_falls_back_to_deferred() -> None:
    cfg = resolve_ingest_config({"mem0_poll_mode": "invalid"})
    assert cfg.mem0_poll_mode == "deferred"
