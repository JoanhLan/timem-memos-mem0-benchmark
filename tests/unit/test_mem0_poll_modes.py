"""Tests for Mem0 adapter poll modes (mocked HTTP)."""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import patch

import httpx
import pytest

from adapters.mem0_platform_adapter import Mem0PlatformAdapter
from models.records import LoCoMoMessage


class _FakeResponse:
    def __init__(self, status_code: int, payload: dict[str, Any]) -> None:
        self.status_code = status_code
        self._payload = payload
        self.request = httpx.Request("POST", "https://example.com")

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("error", request=self.request, response=self)

    def json(self) -> dict[str, Any]:
        return self._payload


class _FakeClient:
    def __init__(self) -> None:
        self.post_calls = 0
        self.get_calls = 0

    async def post(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.post_calls += 1
        return _FakeResponse(200, {"event_id": f"evt-{self.post_calls}"})

    async def get(self, url: str, **kwargs: Any) -> _FakeResponse:
        self.get_calls += 1
        return _FakeResponse(200, {"status": "SUCCEEDED"})

    async def aclose(self) -> None:
        pass


@pytest.mark.asyncio
async def test_deferred_poll_waits_after_all_pairs() -> None:
    client = _FakeClient()
    adapter = Mem0PlatformAdapter(client=client)
    messages = [
        LoCoMoMessage(role="user", content="a"),
        LoCoMoMessage(role="assistant", content="b"),
        LoCoMoMessage(role="user", content="c"),
        LoCoMoMessage(role="assistant", content="d"),
    ]

    with patch("adapters.mem0_platform_adapter.resolve_ingest_config") as mock_cfg:
        mock_cfg.return_value.mem0_poll_mode = "deferred"
        mock_cfg.return_value.mem0_poll_concurrency = 4
        result = await adapter.ingest("u1", "sess1", messages)

    assert result.success
    assert client.post_calls == 2
    assert client.get_calls == 2
    assert result.raw.get("poll_mode") == "deferred"


@pytest.mark.asyncio
async def test_flush_pending_events() -> None:
    client = _FakeClient()
    adapter = Mem0PlatformAdapter(client=client)
    adapter._pending_event_ids = ["e1", "e2"]

    info = await adapter.flush_pending_events()
    assert info["pending_events_flushed"] == 2
    assert info["flush_ms"] >= 0
    assert adapter._pending_event_ids == []
