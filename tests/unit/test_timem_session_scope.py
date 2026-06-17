"""Tests for TiMEM run-scoped session_id and backfill validation."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from adapters.timem_adapter import TiMEMAdapter, _evaluate_backfill_response
from utils.ids import scoped_session_id


def test_scoped_session_id_prefixes_run():
    assert scoped_session_id("LJY-123", "conv-26_session_09") == "LJY-123_conv-26_session_09"


def test_scoped_session_id_rejects_empty_session():
    with pytest.raises(ValueError, match="session_id cannot be empty"):
        scoped_session_id("LJY-123", "")


def test_scoped_session_id_rejects_too_long():
    run_id = "r" * 64
    long_session = "s" * 65
    with pytest.raises(ValueError, match="exceeds 128"):
        scoped_session_id(run_id, long_session)


def test_evaluate_backfill_success():
    ok, err = _evaluate_backfill_response(
        {"success": True, "stats": {"total_tasks": 3, "failed_tasks": 0}}
    )
    assert ok is True
    assert err is None


def test_evaluate_backfill_noop_when_zero_tasks():
    ok, err = _evaluate_backfill_response(
        {"success": True, "stats": {"total_tasks": 0, "failed_tasks": 0}}
    )
    assert ok is False
    assert "total_tasks=0" in (err or "")


def test_evaluate_backfill_fails_on_failed_tasks():
    ok, err = _evaluate_backfill_response(
        {"success": True, "stats": {"total_tasks": 2, "failed_tasks": 1}}
    )
    assert ok is False
    assert "failed_tasks=1" in (err or "")


def test_evaluate_backfill_success_when_generated_without_total_tasks():
    ok, err = _evaluate_backfill_response(
        {
            "success": True,
            "stats": {"total_tasks": 0, "failed_tasks": 0, "generated_memories": 2},
        }
    )
    assert ok is True
    assert err is None


@pytest.mark.asyncio
async def test_backfill_parses_stats_from_response():
    adapter = TiMEMAdapter(client=httpx.AsyncClient())
    response = httpx.Response(
        200,
        json={
            "success": True,
            "stats": {"total_tasks": 5, "failed_tasks": 0, "generated_memories": 5},
        },
        request=httpx.Request("POST", "http://test/api/v1/backfill/manual"),
    )

    with patch.object(adapter._client, "post", AsyncMock(return_value=response)):
        result = await adapter.backfill("timem_RUN_conv-26", ["L2"])

    assert result.success is True
    assert result.error is None
    assert result.raw["stats"]["total_tasks"] == 5
    await adapter.close()


@pytest.mark.asyncio
async def test_backfill_fails_when_total_tasks_zero():
    adapter = TiMEMAdapter(client=httpx.AsyncClient())
    response = httpx.Response(
        200,
        json={"success": True, "stats": {"total_tasks": 0, "failed_tasks": 0}},
        request=httpx.Request("POST", "http://test/api/v1/backfill/manual"),
    )

    with patch.object(adapter._client, "post", AsyncMock(return_value=response)):
        result = await adapter.backfill("timem_RUN_conv-26", ["L2"])

    assert result.success is False
    assert result.error is not None
    await adapter.close()


@pytest.mark.asyncio
async def test_count_layers_uses_list_memories_api():
    adapter = TiMEMAdapter(client=httpx.AsyncClient())
    settings = MagicMock()
    settings.timem_base_url = "http://test"
    settings.timem_account_id = "acct_1"
    settings.benchmark_expert_id = "benchmark"
    settings.timem_api_key = "key"
    adapter._settings = settings

    async def fake_get(url, *, headers=None, params=None):
        layer = (params or {}).get("layer", "")
        return httpx.Response(
            200,
            json={"total": 7 if layer == "L2" else 1},
            request=httpx.Request("GET", url),
        )

    with patch.object(adapter._client, "get", AsyncMock(side_effect=fake_get)):
        counts = await adapter.count_layers("timem_RUN_conv-26")

    assert counts["L2"] == 7
    assert counts["L1"] == 1
    await adapter.close()


@pytest.mark.asyncio
async def test_count_layers_uses_counts_by_level_when_total_zero():
    adapter = TiMEMAdapter(client=httpx.AsyncClient())
    settings = MagicMock()
    settings.timem_base_url = "http://test"
    settings.timem_account_id = "acct_1"
    settings.benchmark_expert_id = "benchmark"
    settings.timem_api_key = "key"
    adapter._settings = settings

    async def fake_get(url, *, headers=None, params=None):
        layer = (params or {}).get("layer", "")
        return httpx.Response(
            200,
            json={"total": 0, "counts_by_level": {layer: 12} if layer == "L2" else {"L1": 5}},
            request=httpx.Request("GET", url),
        )

    with patch.object(adapter._client, "get", AsyncMock(side_effect=fake_get)):
        counts = await adapter.count_layers("timem_RUN_conv-26")

    assert counts["L2"] == 12
    assert counts["L1"] == 5
    await adapter.close()
