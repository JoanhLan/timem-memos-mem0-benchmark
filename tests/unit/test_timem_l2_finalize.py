"""Tests for TiMEM L2 finalize after ingest."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from benchmark_data.locomo_loader import LoCoMoPersona, LoCoMoSession, LoCoMoMessage
from models.records import BackfillResult
from runners import timem_l2_finalize as mod


def _persona(session_count: int = 2) -> LoCoMoPersona:
    sessions = [
        LoCoMoSession(
            session_id=f"conv-26_session_{i:02d}",
            persona_id="conv-26",
            messages=[LoCoMoMessage(role="user", content="hi")],
        )
        for i in range(session_count)
    ]
    return LoCoMoPersona(persona_id="conv-26", sessions=sessions, qa_pairs=[])


@pytest.mark.asyncio
async def test_finalize_fails_fast_when_backfill_noop():
    adapter = MagicMock()
    adapter.count_layers = AsyncMock(return_value={"L1": 10, "L2": 0, "L3": 0, "L4": 0, "L5": 0})
    adapter.backfill = AsyncMock(
        return_value=BackfillResult(
            success=False,
            latency_ms=1.0,
            layers=["L2"],
            raw={"stats": {"total_tasks": 0, "failed_tasks": 0, "generated_memories": 0}},
            error="backfill noop",
        )
    )

    row = await mod._finalize_one_persona(
        _persona(session_count=3),
        adapter=adapter,
        run_id="RUN1",
        timeout_sec=5,
    )

    assert row["success"] is False
    assert "backfill_wait_ms" not in row
    assert "noop" in (row.get("error") or "").lower() or "total_tasks=0" in (row.get("error") or "")
    adapter.backfill.assert_awaited_once()


@pytest.mark.asyncio
async def test_finalize_succeeds_from_backfill_stats_without_polling():
    adapter = MagicMock()
    adapter.count_layers = AsyncMock(
        side_effect=[
            {"L1": 10, "L2": 0, "L3": 0, "L4": 0, "L5": 0},
            {"L1": 10, "L2": 1, "L3": 0, "L4": 0, "L5": 0},
        ]
    )
    adapter.backfill = AsyncMock(
        return_value=BackfillResult(
            success=True,
            latency_ms=50.0,
            layers=["L2"],
            raw={
                "stats": {
                    "total_tasks": 3,
                    "successful_tasks": 3,
                    "failed_tasks": 0,
                    "generated_memories": 3,
                }
            },
        )
    )

    row = await mod._finalize_one_persona(
        _persona(session_count=3),
        adapter=adapter,
        run_id="RUN1",
        timeout_sec=600,
    )

    assert row["success"] is True
    assert row["l2_count"] == 3
    assert row["backfill_wait_ms"] == 0.0


@pytest.mark.asyncio
async def test_finalize_skips_when_l2_already_complete():
    adapter = MagicMock()
    adapter.count_layers = AsyncMock(return_value={"L1": 10, "L2": 5, "L3": 0, "L4": 0, "L5": 0})

    row = await mod._finalize_one_persona(
        _persona(session_count=5),
        adapter=adapter,
        run_id="RUN1",
        timeout_sec=5,
    )

    assert row["success"] is True
    assert row["skipped"] is True
    adapter.backfill.assert_not_called()
