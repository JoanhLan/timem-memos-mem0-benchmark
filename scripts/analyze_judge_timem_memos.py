"""Judge-focused TiMEM vs MemOS analysis for LJY_NEW T0."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAT = {"1": "single_hop", "2": "temporal", "3": "multi_hop", "4": "open_domain", "5": "cat5"}


def main() -> None:
    compare = json.loads((ROOT / "reports/LJY_NEW/token_compare_T0.json").read_text(encoding="utf-8"))
    retrieval = json.loads((ROOT / "reports/LJY_NEW/retrieval_T0.json").read_text(encoding="utf-8"))

    rows = compare["questions"]
    n = len(rows)

    # Head-to-head judge matrix
    matrix = Counter()  # (timem, memos) bool pairs
    by_cat: dict[str, Counter] = defaultdict(Counter)
    score_diff: list[float] = []
    timem_only: list[dict] = []
    memos_only: list[dict] = []
    both_yes: list[dict] = []
    both_no: list[dict] = []
    disagree: list[dict] = []

    timem_scores = []
    memos_scores = []

    for row in rows:
        t = row["systems"]["timem"]
        m = row["systems"]["memos"]
        tj = (t.get("judge") or {})
        mj = (m.get("judge") or {})
        tc = bool(tj.get("can_answer"))
        mc = bool(mj.get("can_answer"))
        ts = float(tj.get("score") or 0)
        ms = float(mj.get("score") or 0)
        timem_scores.append(ts)
        memos_scores.append(ms)
        score_diff.append(ms - ts)

        key = ("T+" if tc else "T-", "M+" if mc else "M-")
        matrix[key] += 1
        cat = str(row.get("category") or "?")
        by_cat[cat][key] += 1

        item = {
            "question": row["question"],
            "gold": row.get("gold"),
            "category": cat,
            "timem_score": ts,
            "memos_score": ms,
            "timem_reason": tj.get("reason", ""),
            "memos_reason": mj.get("reason", ""),
            "timem_tokens": t.get("recalled_tokens"),
            "memos_tokens": m.get("recalled_tokens"),
        }
        if tc and mc:
            both_yes.append(item)
        elif not tc and not mc:
            both_no.append(item)
        else:
            disagree.append(item)
            if tc and not mc:
                timem_only.append(item)
            else:
                memos_only.append(item)

    t_hit = sum(1 for r in rows if (r["systems"]["timem"].get("judge") or {}).get("can_answer"))
    m_hit = sum(1 for r in rows if (r["systems"]["memos"].get("judge") or {}).get("can_answer"))

    print("=" * 60)
    print("JUDGE: TiMEM vs MemOS (LJY_NEW T0)")
    print("=" * 60)
    print(f"Aligned questions: {n}")
    print()
    print("Overall judge can_answer:")
    print(f"  TiMEM: {t_hit}/{n} = {100*t_hit/n:.1f}%")
    print(f"  MemOS: {m_hit}/{n} = {100*m_hit/n:.1f}%")
    print(f"  MemOS - TiMEM: +{m_hit - t_hit} questions (+{100*(m_hit-t_hit)/n:.1f}pp)")
    print()
    print(f"Avg judge score:")
    print(f"  TiMEM: {sum(timem_scores)/n:.3f}")
    print(f"  MemOS: {sum(memos_scores)/n:.3f}")
    print(f"  MemOS - TiMEM: {sum(score_diff)/n:+.3f}")
    print()

    print("Head-to-head matrix (can_answer):")
    for k in [("T+", "M+"), ("T+", "M-"), ("T-", "M+"), ("T-", "M-")]:
        cnt = matrix[k]
        label = {
            ("T+", "M+"): "Both YES",
            ("T+", "M-"): "TiMEM only",
            ("T-", "M+"): "MemOS only",
            ("T-", "M-"): "Both NO",
        }[k]
        print(f"  {label:12} {cnt:4} ({100*cnt/n:.1f}%)")

    agree = matrix[("T+", "M+")] + matrix[("T-", "M-")]
    print(f"\n  Agreement rate: {100*agree/n:.1f}%")
    print(f"  Disagreement:   {len(disagree)} ({100*len(disagree)/n:.1f}%)")

    print("\nBy category — judge can_answer rate:")
    print(f"  {'cat':14} {'n':>5} {'TiMEM':>8} {'MemOS':>8} {'MemOS+':>8} {'MemOS_only':>10}")
    for cat in sorted(by_cat.keys(), key=lambda x: (x != "4", x)):
        c = by_cat[cat]
        cn = sum(c.values())
        t_y = c[("T+", "M+")] + c[("T+", "M-")]
        m_y = c[("T+", "M+")] + c[("T-", "M+")]
        mo = c[("T-", "M+")]
        name = CAT.get(cat, cat)
        print(f"  {name:14} {cn:5} {100*t_y/cn:7.1f}% {100*m_y/cn:7.1f}% {100*(m_y-t_y)/cn:+7.1f}pp {mo:10}")

    # When both NO — is it hard question or retrieval failure?
    print("\nBoth NO breakdown by category:")
    both_no_cat = Counter(str(r["category"]) for r in both_no)
    for cat, cnt in both_no_cat.most_common():
        print(f"  {CAT.get(cat, cat)}: {cnt} ({100*cnt/len(both_no):.1f}%)")

    # MemOS-only win patterns (reason keywords)
    def reason_theme(reason: str) -> str:
        r = (reason or "").lower()
        if "explicit" in r or "explicitly" in r:
            return "explicit_fact_in_memory"
        if "no retrieved" in r or "none of" in r or "not contain" in r or "do not contain" in r:
            return "content_not_found"
        if "attribution" in r or "who" in r or "speaker" in r:
            return "attribution"
        if "time" in r or "date" in r or "when" in r:
            return "temporal"
        if "partial" in r or "related" in r or "not enough" in r:
            return "partial_info"
        return "other"

    print("\nMemOS-only wins (TiMEM NO, MemOS YES): reason themes")
    memos_themes = Counter(reason_theme(r["memos_reason"]) for r in memos_only)
    for th, cnt in memos_themes.most_common():
        print(f"  {th}: {cnt}")

    print("\nTiMEM-only wins: reason themes (TiMEM reason)")
    timem_themes = Counter(reason_theme(r["timem_reason"]) for r in timem_only)
    for th, cnt in timem_themes.most_common():
        print(f"  {th}: {cnt}")

    # Token context when MemOS wins
    tok_diff = [r["memos_tokens"] - r["timem_tokens"] for r in memos_only if r["timem_tokens"] is not None and r["memos_tokens"] is not None]
    if tok_diff:
        tok_diff.sort()
        print(f"\nMemOS-only wins — token delta (memos - timem):")
        print(f"  mean={sum(tok_diff)/len(tok_diff):+.0f}, p50={tok_diff[len(tok_diff)//2]:+.0f}")
        print(f"  MemOS used FEWER tokens: {sum(1 for d in tok_diff if d < 0)} ({100*sum(1 for d in tok_diff if d<0)/len(tok_diff):.0f}%)")

    # Samples
    print("\n" + "=" * 60)
    print("SAMPLES: MemOS judge wins, TiMEM loses")
    print("=" * 60)
    for r in sorted(memos_only, key=lambda x: -x["memos_score"])[:5]:
        print(f"\n[{CAT.get(r['category'], r['category'])}] Q: {r['question'][:100]}")
        print(f"Gold: {r['gold']}")
        print(f"TiMEM({r['timem_score']:.1f}): {r['timem_reason'][:180]}")
        print(f"MemOS({r['memos_score']:.1f}): {r['memos_reason'][:180]}")

    print("\n" + "=" * 60)
    print("SAMPLES: TiMEM judge wins, MemOS loses")
    print("=" * 60)
    for r in sorted(timem_only, key=lambda x: -x["timem_score"])[:5]:
        print(f"\n[{CAT.get(r['category'], r['category'])}] Q: {r['question'][:100]}")
        print(f"Gold: {r['gold']}")
        print(f"TiMEM({r['timem_score']:.1f}): {r['timem_reason'][:180]}")
        print(f"MemOS({r['memos_score']:.1f}): {r['memos_reason'][:180]}")

    # From retrieval report aggregates
    print("\n" + "=" * 60)
    print("Retrieval report judge aggregates")
    print("=" * 60)
    for sys in ["timem", "memos"]:
        b = retrieval[sys]
        print(f"{sys}: accuracy={b['judge_accuracy']:.3f}, avg_score={b['judge_avg_score']:.3f}, "
              f"total_judge_tokens={b['total_judge_tokens']}, judge_sum_ms={b['total_judge_latency_ms']/1e6:.1f}M")


if __name__ == "__main__":
    main()
