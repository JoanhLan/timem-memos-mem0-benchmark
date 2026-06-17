"""Tests for token counting utilities."""

from __future__ import annotations

from evaluators.tokens import count_tokens, recalled_tokens_from_records
from models.records import MemoryRecord, SourceSystem


def test_count_tokens_nonempty() -> None:
    n = count_tokens("hello world")
    assert n > 0


def test_recalled_tokens_per_record() -> None:
    records = [
        MemoryRecord(
            id="1",
            content="short",
            memory_type="factual",
            source_system=SourceSystem.TIMEM,
            layer="L1",
        ),
        MemoryRecord(
            id="2",
            content="another memory snippet",
            memory_type="factual",
            source_system=SourceSystem.TIMEM,
            layer="L1",
        ),
    ]
    metrics = recalled_tokens_from_records(records, limit=2)
    assert metrics["record_count"] == 2
    assert len(metrics["per_record_tokens"]) == 2
    assert metrics["recalled_tokens"] >= sum(metrics["per_record_tokens"]) - 5


def test_empty_records() -> None:
    metrics = recalled_tokens_from_records([], limit=10)
    assert metrics["recalled_tokens"] == 0
    assert metrics["per_record_tokens"] == []
