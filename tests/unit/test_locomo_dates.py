"""Tests for LoCoMo date/time parsing."""

from __future__ import annotations

from utils.locomo_dates import message_timestamps, parse_locomo_datetime


def test_parse_locomo_datetime_official_sample():
    assert parse_locomo_datetime("1:56 pm on 8 May, 2023") == "2023-05-08T13:56:00"


def test_parse_locomo_datetime_without_comma_after_month():
    assert parse_locomo_datetime("1:56 pm on 8 May 2023") == "2023-05-08T13:56:00"


def test_parse_locomo_datetime_am():
    assert parse_locomo_datetime("9:05 am on 1 January, 2024") == "2024-01-01T09:05:00"


def test_parse_locomo_datetime_invalid_returns_none():
    assert parse_locomo_datetime("not a date") is None
    assert parse_locomo_datetime("") is None
    assert parse_locomo_datetime(None) is None


def test_message_timestamps_increments_by_step():
    stamps = message_timestamps("2023-05-08T13:56:00", 3, step_sec=60)
    assert stamps == [
        "2023-05-08T13:56:00",
        "2023-05-08T13:57:00",
        "2023-05-08T13:58:00",
    ]


def test_message_timestamps_empty_for_zero_turns():
    assert message_timestamps("2023-05-08T13:56:00", 0) == []
