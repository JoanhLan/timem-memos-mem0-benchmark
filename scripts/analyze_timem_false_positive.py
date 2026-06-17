"""Analyze TiMEM recall@10=1 but judge can_answer=false cases."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = {"1": "single_hop", "2": "temporal", "3": "multi_hop", "4": "open_domain", "5": "cat5"}


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in re.findall(r"[a-zA-Z0-9\u4e00-\u9fff]+", text) if len(t) > 1}


def classify_reason(reason: str, question: str) -> str:
    r = (reason or "").lower()
    q = (question or "").lower()
    if not r:
        return "empty_reason"
    if "no retrieved" in r or "not available" in r or "(empty)" in r:
        return "no_memories"
    if "according to" in q or "who said" in q or "who stated" in q:
        if any(x in r for x in ("attribution", "source", "who", "speaker", "gina", "evan", "jon", "explicitly states")):
            return "attribution_speaker"
    if any(x in r for x in ("attribution", "who said", "speaker", "source of", "explicitly states that")):
        return "attribution_speaker"
    if any(x in r for x in ("temporal", "time", "date", "when", "timeline", "specific time")):
        return "temporal_missing"
    if any(x in r for x in ("do not contain", "does not contain", "none of", "no memory", "not contain", "lack", "missing", "insufficient")):
        return "content_missing"
    if any(x in r for x in ("partial", "related but", "not enough", "insufficient", "vague", "indirect")):
        return "partial_related"
    if any(x in r for x in ("paraphras", "wording", "exact", "specific phrase", "different wording")):
        return "wording_mismatch"
    if any(x in r for x in ("contradict", "conflict", "incorrect")):
        return "contradiction"
    return "other"


def gold_token_coverage(records: list[dict], gold: str, k: int = 10) -> dict:
    gold_toks = _tokens(gold)
    if not gold_toks:
        return {"hit_ratio": 0, "hits": [], "misses": list(gold_toks), "threshold": 0}
    blob = " ".join((r.get("content") or "") for r in records[:k]).lower()
    hits = [g for g in gold_toks if g in blob]
    misses = [g for g in gold_toks if g not in blob]
    threshold = max(1, len(gold_toks) // 2)
    return {
        "hit_ratio": len(hits) / len(gold_toks),
        "hits": hits,
        "misses": misses,
        "threshold": threshold,
        "passes_recall_rule": len(hits) >= threshold,
    }


def main() -> None:
    retrieval = json.loads((ROOT / "reports/LJY_NEW/retrieval_T0.json").read_text(encoding="utf-8"))
    compare = json.loads((ROOT / "reports/LJY_NEW/token_compare_T0.json").read_text(encoding="utf-8"))

    timem_by_q = {r["question"]: r for r in retrieval["timem"]["details"]}
    compare_by_q = {r["question"]: r for r in compare["questions"]}

    false_pos: list[dict] = []
    for q, row in timem_by_q.items():
        if row.get("recall@10") != 1.0:
            continue
        judge = row.get("judge") or {}
        if judge.get("can_answer"):
            continue
        cmp_row = compare_by_q.get(q, {})
        memos = (cmp_row.get("systems") or {}).get("memos") or {}
        memos_j = memos.get("judge") or {}
        cov = gold_token_coverage(row.get("records") or [], row.get("gold") or "")
        false_pos.append(
            {
                "question": q,
                "gold": row.get("gold"),
                "category": str(row.get("category") or "?"),
                "persona_id": row.get("persona_id"),
                "judge_reason": judge.get("reason", ""),
                "judge_score": judge.get("score", 0),
                "memos_can_answer": memos_j.get("can_answer"),
                "memos_reason": memos_j.get("reason", ""),
                "recalled_tokens": row.get("recalled_tokens"),
                "record_count": len(row.get("records") or []),
                "coverage": cov,
                "records_preview": [
                    (r.get("content") or "")[:200] for r in (row.get("records") or [])[:3]
                ],
            }
        )

    n = len(false_pos)
    print(f"=== TiMEM recall@10=1 & judge=false: {n} cases ===\n")

    # By category
    by_cat = Counter(c["category"] for c in false_pos)
    print("By category:")
    for cat, cnt in by_cat.most_common():
        name = CAT.get(cat, cat)
        print(f"  {cat} ({name}): {cnt} ({100*cnt/n:.1f}%)")

    # Judge reason classification
    reason_cls = Counter(classify_reason(c["judge_reason"], c["question"]) for c in false_pos)
    print("\nJudge reason categories (keyword heuristic):")
    for cls, cnt in reason_cls.most_common():
        print(f"  {cls}: {cnt} ({100*cnt/n:.1f}%)")

    # MemOS comparison on same questions
    memos_yes = sum(1 for c in false_pos if c["memos_can_answer"])
    memos_no = sum(1 for c in false_pos if c["memos_can_answer"] is False)
    memos_na = n - memos_yes - memos_no
    print(f"\nSame questions — MemOS judge:")
    print(f"  can_answer=true:  {memos_yes} ({100*memos_yes/n:.1f}%)")
    print(f"  can_answer=false: {memos_no} ({100*memos_no/n:.1f}%)")
    print(f"  not in compare:   {memos_na}")

    # Gold token coverage analysis
    low_cov = sum(1 for c in false_pos if c["coverage"]["hit_ratio"] < 0.5)
    mid_cov = sum(1 for c in false_pos if 0.5 <= c["coverage"]["hit_ratio"] < 1.0)
    full_cov = sum(1 for c in false_pos if c["coverage"]["hit_ratio"] == 1.0)
    print("\nGold token coverage in top-10 TiMEM records:")
    print(f"  <50% tokens hit: {low_cov} ({100*low_cov/n:.1f}%)")
    print(f"  50-99% hit:      {mid_cov} ({100*mid_cov/n:.1f}%)")
    print(f"  100% hit:        {full_cov} ({100*full_cov/n:.1f}%)")

    # Attribution questions
    attr_q = [c for c in false_pos if "according to" in c["question"].lower()]
    print(f"\n'According to ...' questions in false positives: {len(attr_q)}")
    if attr_q:
        memos_attr_yes = sum(1 for c in attr_q if c["memos_can_answer"])
        print(f"  MemOS can_answer on these: {memos_attr_yes}/{len(attr_q)}")

    # Judge score distribution
    scores = Counter(round(float(c["judge_score"] or 0), 1) for c in false_pos)
    print("\nJudge score distribution:")
    for sc, cnt in sorted(scores.items()):
        print(f"  score={sc}: {cnt}")

    # Sample buckets
    print("\n" + "=" * 60)
    print("SAMPLE CASES")
    print("=" * 60)

    def show_samples(title: str, items: list[dict], limit: int = 3) -> None:
        print(f"\n--- {title} ({len(items)} total, show {min(limit, len(items))}) ---")
        for c in items[:limit]:
            print(f"Q: {c['question'][:120]}")
            print(f"Gold: {c['gold']}")
            print(f"Cat: {CAT.get(c['category'], c['category'])} | tokens={c['recalled_tokens']} | gold_hits={c['coverage']['hits']}")
            print(f"TiMEM judge: {c['judge_reason'][:200]}")
            mj = "YES" if c["memos_can_answer"] else "NO"
            print(f"MemOS judge: {mj} — {(c['memos_reason'] or '')[:150]}")
            for i, prev in enumerate(c["records_preview"][:2], 1):
                print(f"  rec{i}: {prev[:180]}...")
            print()

    memos_rescues = [c for c in false_pos if c["memos_can_answer"]]
    show_samples("MemOS CAN answer (TiMEM retrieval gap)", memos_rescues, 4)

    attr_samples = attr_q[:4]
    show_samples("Attribution questions", attr_samples, min(4, len(attr_samples)))

    full_hit = [c for c in false_pos if c["coverage"]["hit_ratio"] == 1.0 and not c["memos_can_answer"]]
    show_samples("All gold tokens present but both judges NO", full_hit, 3)

    temporal = [c for c in false_pos if c["category"] == "2"]
    show_samples("Temporal category", temporal, 3)

    # Top judge reason phrases
    print("\nTop verbatim judge reasons:")
    for reason, cnt in Counter(c["judge_reason"][:120] for c in false_pos).most_common(8):
        print(f"  [{cnt}x] {reason}...")


if __name__ == "__main__":
    main()
