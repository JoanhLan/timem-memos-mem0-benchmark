"""Tests for parallel TiMEM backfill scheduling."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from benchmark_data.locomo_loader import LoCoMoPersona
from models.records import BackfillResult
from runners.retrieval_run import _timem_backfill_all


@pytest.mark.asyncio
async def test_timem_backfill_runs_with_bounded_concurrency():
    active = 0
    peak = 0
    lock = asyncio.Lock()

    adapter = MagicMock()

    async def fake_backfill(user_id: str, layers: list[str]) -> BackfillResult:
        nonlocal active, peak
        async with lock:
            active += 1
            peak = max(peak, active)
        await asyncio.sleep(0.05)
        async with lock:
            active -= 1
        return BackfillResult(success=True, latency_ms=10.0)

    async def fake_count_layers(user_id: str) -> dict[str, int]:
        return {"L2": 1, "L3": 1, "L4": 1, "L5": 1}

    adapter.backfill = AsyncMock(side_effect=fake_backfill)
    adapter.count_layers = AsyncMock(side_effect=fake_count_layers)

    personas = [
        LoCoMoPersona(persona_id=f"p{i}", sessions=[], qa_pairs=[])
        for i in range(6)
    ]
    settings = MagicMock()
    settings.benchmark_backfill_timeout_sec = 5

    rows = await _timem_backfill_all(
        adapter,
        "RUN1",
        personas,
        settings,
        ["L2", "L3", "L4", "L5"],
        backfill_concurrency=3,
    )

    assert len(rows) == 6
    assert peak <= 3
    assert peak >= 2
    assert adapter.backfill.await_count == 6
