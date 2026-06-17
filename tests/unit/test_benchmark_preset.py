"""Tests for benchmark preset / TiMEM search defaults."""

from __future__ import annotations

from utils.config import resolve_benchmark_config


def test_stable_preset_uses_enhanced_semantic():
    cfg = resolve_benchmark_config(preset="stable", mode="T0")
    assert cfg.timem.search_mode == "enhanced_semantic"
    assert cfg.top_k == 10


def test_paper_preset_uses_enhanced_semantic_for_t0_and_t1():
    t0 = resolve_benchmark_config(preset="paper", mode="T0")
    t1 = resolve_benchmark_config(preset="paper", mode="T1")
    assert t0.timem.search_mode == "enhanced_semantic"
    assert t1.timem.search_mode == "enhanced_semantic"
    assert t0.top_k == 20
