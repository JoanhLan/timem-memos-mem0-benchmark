"""Tests for MemOS adapter LoCoMo role mapping."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adapters.memos_cloud_adapter import MemOSCloudAdapter, _memos_api_role
from models.records import LoCoMoMessage


def test_memos_api_role_maps_user1_user2():
    assert _memos_api_role("user1") == "user"
    assert _memos_api_role("user2") == "assistant"


def test_memos_api_role_passthrough():
    assert _memos_api_role("user") == "user"
    assert _memos_api_role("assistant") == "assistant"
    assert _memos_api_role("system") == "system"


@pytest.mark.asyncio
async def test_ingest_maps_user1_user2_in_payload():
    adapter = MemOSCloudAdapter(client=httpx.AsyncClient())
    captured: dict = {}

    async def fake_post(url, *, headers=None, json=None):
        captured["json"] = json
        return httpx.Response(
            200,
            json={"code": 0, "data": {"success": True}},
            request=httpx.Request("POST", url),
        )

    with patch.object(adapter._client, "post", AsyncMock(side_effect=fake_post)):
        result = await adapter.ingest(
            "memos_run_persona",
            "run_session_00",
            [
                LoCoMoMessage(role="user1", content="Caroline hi"),
                LoCoMoMessage(role="user2", content="Melanie hi"),
            ],
        )

    assert result.success is True
    roles = [m["role"] for m in captured["json"]["messages"]]
    assert roles == ["user", "assistant"]
    await adapter.close()
