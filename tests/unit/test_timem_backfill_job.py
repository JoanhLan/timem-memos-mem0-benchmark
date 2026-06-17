"""Tests for manual TiMEM backfill job options."""

from __future__ import annotations

import pytest

from benchmark_jobs import JobOptions
from runners.timem_backfill_run import normalize_backfill_layers


def test_normalize_backfill_layers_dedupes_and_uppercases():
    assert normalize_backfill_layers(["l2", "L2", "L3"]) == ["L2", "L3"]


def test_normalize_backfill_layers_from_string():
    assert normalize_backfill_layers("L2,L4") == ["L2", "L4"]


def test_normalize_backfill_layers_rejects_empty():
    with pytest.raises(ValueError, match="cannot be empty"):
        normalize_backfill_layers([])


def test_normalize_backfill_layers_rejects_invalid_layer():
    with pytest.raises(ValueError, match="invalid backfill layer"):
        normalize_backfill_layers(["L1"])


def test_job_options_parses_backfill_layers_string():
    opts = JobOptions.from_dict({"backfill_layers": "L2,L4"})
    assert opts.backfill_layers == ["L2", "L4"]


def test_job_options_default_backfill_layers():
    opts = JobOptions.from_dict({})
    assert opts.backfill_layers == ["L2"]
