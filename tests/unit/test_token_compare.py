"""Tests for cross-system token compare report."""

from __future__ import annotations

from runners.token_compare import build_token_compare


def test_build_token_compare_deltas() -> None:
    reports = {
        "timem": {
            "avg_recalled_tokens": 3000,
            "judge_accuracy": 0.3,
            "details": [
                {
                    "question": "Q1",
                    "gold": "A1",
                    "category": "1",
                    "recalled_tokens": 3000,
                    "recall@5": 1,
                    "recall@10": 1,
                }
            ],
        },
        "memos": {
            "avg_recalled_tokens": 450,
            "judge_accuracy": 0.35,
            "details": [
                {
                    "question": "Q1",
                    "gold": "A1",
                    "category": "1",
                    "recalled_tokens": 450,
                    "recall@5": 1,
                    "recall@10": 0,
                }
            ],
        },
    }
    out = build_token_compare(reports, mode="T0", run_id="TEST")
    assert out["question_count"] == 1
    assert out["questions"][0]["token_delta"]["timem_vs_memos"] == 2550
    assert "timem" in out["summary"]["avg_tokens_by_system"]
    assert out["summary"]["efficiency_score"]["memos"] > 0
