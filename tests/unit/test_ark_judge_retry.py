"""Tests for ARK judge async client reuse and retry."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from evaluators.ark_judge import ARKJudge, _is_retryable


def test_is_retryable_status_codes():
    exc429 = MagicMock()
    exc429.status_code = 429
    assert _is_retryable(exc429) is True

    exc503 = MagicMock()
    exc503.status_code = 503
    assert _is_retryable(exc503) is True

    exc400 = MagicMock()
    exc400.status_code = 400
    assert _is_retryable(exc400) is False


@pytest.mark.asyncio
async def test_judge_async_retries_on_429():
    class RateLimitError(Exception):
        status_code = 429

    judge = ARKJudge(max_retries=2, retry_base_sec=0.01)
    mock_client = AsyncMock()

    ok_resp = MagicMock()
    ok_resp.choices = [MagicMock(message=MagicMock(content='{"can_answer": true, "score": 1.0}'))]
    ok_resp.usage = None

    mock_client.chat.completions.create = AsyncMock(
        side_effect=[RateLimitError("429"), ok_resp]
    )

    with patch.object(judge, "_get_async_client", return_value=mock_client):
        with patch("evaluators.ark_judge.get_settings") as gs:
            settings = MagicMock()
            settings.ark_api_key = "key"
            settings.ark_api_base = "https://example.com"
            settings.judge_model = "m"
            settings.judge_temperature = 0
            gs.return_value = settings
            result = await judge.judge_async("q", "gold", [])

    assert result["can_answer"] is True
    assert mock_client.chat.completions.create.await_count == 2
    await judge.close_async()


@pytest.mark.asyncio
async def test_judge_async_reuses_single_client_instance():
    judge = ARKJudge(max_retries=0, retry_base_sec=0.01)
    mock_client = AsyncMock()
    mock_client.chat.completions.create = AsyncMock(
        return_value=MagicMock(
            choices=[MagicMock(message=MagicMock(content='{"can_answer": false, "score": 0}'))],
            usage=None,
        )
    )
    mock_client.close = AsyncMock()

    def fake_get_client():
        judge._async_client = mock_client
        return mock_client

    with patch.object(judge, "_get_async_client", side_effect=fake_get_client):
        with patch("evaluators.ark_judge.get_settings") as gs:
            settings = MagicMock()
            settings.ark_api_key = "key"
            settings.ark_api_base = "https://example.com"
            settings.judge_model = "m"
            settings.judge_temperature = 0
            gs.return_value = settings
            await judge.judge_async("q1", "g", [])
            await judge.judge_async("q2", "g", [])

    assert judge._async_client is mock_client
    assert mock_client.chat.completions.create.await_count == 2
    await judge.close_async()
