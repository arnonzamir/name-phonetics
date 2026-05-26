"""Evaluate the matcher against the labeled set and two baselines.

Baselines:
  ipa-lev : flat Levenshtein over the SAME IPA (isolates the value of
            feature-weighting + the equivalence table vs. a plain edit metric)
  jw-raw  : Jaro-Winkler on raw orthography (what you'd get with no G2P at all;
            collapses to ~0 on cross-script pairs — the beider-morse problem)

For each method we sweep the decision threshold and report the best operating
point by F1, plus accuracy/precision/recall there.
"""
from __future__ import annotations

import csv
import os
import sys

import jellyfish

sys.path.insert(0, os.path.dirname(__file__))
from engine import to_ipa, detect_lang, similarity  # noqa: E402
from data.testcases import PAIRS  # noqa: E402


def lev_sim(a: str, b: str) -> float:
    if not a and not b:
        return 1.0
    d = jellyfish.levenshtein_distance(a, b)
    return 1.0 - d / max(len(a), len(b), 1)


def score_all():
    rows = []
    for a, b, label, cat in PAIRS:
        ia, ib = to_ipa(a, detect_lang(a)), to_ipa(b, detect_lang(b))
        rows.append({
            "a": a, "b": b, "label": label, "cat": cat,
            "ipa_a": ia, "ipa_b": ib,
            "phonetic": similarity(ia, ib),
            "ipa_lev": lev_sim(ia, ib),
            "jw_raw": jellyfish.jaro_winkler_similarity(a, b),
        })
    return rows


def best_threshold(rows, key):
    scores = sorted({round(r[key], 3) for r in rows})
    cands = [0.0] + [(scores[i] + scores[i + 1]) / 2 for i in range(len(scores) - 1)] + [1.0]
    best = None
    for t in cands:
        tp = sum(1 for r in rows if r[key] >= t and r["label"])
        fp = sum(1 for r in rows if r[key] >= t and not r["label"])
        fn = sum(1 for r in rows if r[key] < t and r["label"])
        tn = sum(1 for r in rows if r[key] < t and not r["label"])
        prec = tp / (tp + fp) if tp + fp else 0.0
        rec = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
        acc = (tp + tn) / len(rows)
        if best is None or f1 > best["f1"]:
            best = dict(t=t, f1=f1, acc=acc, prec=prec, rec=rec,
                        tp=tp, fp=fp, fn=fn, tn=tn)
    return best


def main():
    rows = score_all()
    print(f"\n{len(rows)} pairs  "
          f"({sum(r['label'] for r in rows)} match / "
          f"{sum(not r['label'] for r in rows)} non-match)\n")

    print(f"{'method':<10} {'thresh':>6} {'F1':>6} {'acc':>6} {'prec':>6} {'rec':>6}")
    print("-" * 48)
    results = {}
    for key in ("phonetic", "ipa_lev", "jw_raw"):
        b = best_threshold(rows, key)
        results[key] = b
        print(f"{key:<10} {b['t']:>6.3f} {b['f1']:>6.3f} {b['acc']:>6.3f} "
              f"{b['prec']:>6.3f} {b['rec']:>6.3f}")

    # errors for the main method at its best threshold
    t = results["phonetic"]["t"]
    print(f"\n--- phonetic errors at threshold {t:.3f} ---")
    for r in rows:
        pred = r["phonetic"] >= t
        if pred != r["label"]:
            kind = "FALSE POS" if pred else "FALSE NEG"
            print(f"  {kind}  {r['a']}/{r['ipa_a']}  ~  {r['b']}/{r['ipa_b']}  "
                  f"= {r['phonetic']:.3f}  [{r['cat']}]")

    out = os.path.join(os.path.dirname(__file__), "eval_scores.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"\nfull scores -> {out}")


if __name__ == "__main__":
    main()
