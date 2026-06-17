"""Tests for TiMEM adapter ingest payload."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from adapters.timem_adapter import TiMEMAdapter, _message_payload
from models.records import LoCoMoMessage


def test_message_payload_includes_timestamp_when_present():
    msg = LoCoMoMessage(role="user", content="hi", timestamp="2023-05-08T13:56:00")
    assert _message_payload(msg) == {
        "role": "user",
        "content": "hi",
        "timestamp": "2023-05-08T13:56:00",
    }


def test_message_payload_omits_timestamp_when_absent():
    msg = LoCoMoMessage(role="user", content="hi")
    assert _message_payload(msg) == {"role": "user", "content": "hi"}
    assert "timestamp" not in _message_payload(msg)


@pytest.mark.asyncio
async def test_ingest_chunk_posts_timestamp_in_json_body():
    adapter = TiMEMAdapter(client=httpx.AsyncClient())
    captured: dict = {}

    async def fake_post(url, *, headers=None, json=None):
        captured["json"] = json
        return httpx.Response(
            200,
            json=[{"id": "m1"}],
            request=httpx.Request("POST", url),
        )

    with patch.object(adapter._client, "post", AsyncMock(side_effect=fake_post)):
        result = await adapter._ingest_message_chunk(
            "timem_run_persona",
            "run_session_00",
            [
                LoCoMoMessage(role="user", content="a", timestamp="2023-05-08T13:56:00"),
                LoCoMoMessage(role="assistant", content="b", timestamp="2023-05-08T13:57:00"),
            ],
        )

    assert result.success is True
    messages = captured["json"]["messages"]
    assert messages[0]["timestamp"] == "2023-05-08T13:56:00"
    assert messages[1]["timestamp"] == "2023-05-08T13:57:00"
    await adapter.close()


@pytest.mark.asyncio
async def test_ingest_chunk_without_timestamps():
    adapter = TiMEMAdapter(client=httpx.AsyncClient())
    captured: dict = {}

    async def fake_post(url, *, headers=None, json=None):
        captured["json"] = json
        return httpx.Response(
            200,
            json=[{"id": "m1"}],
            request=httpx.Request("POST", url),
        )

    with patch.object(adapter._client, "post", AsyncMock(side_effect=fake_post)):
        await adapter._ingest_message_chunk(
            "timem_run_persona",
            "run_session_00",
            [LoCoMoMessage(role="user", content="a")],
        )

    assert "timestamp" not in captured["json"]["messages"][0]
    await adapter.close()
