#!/usr/bin/env python
"""Structured fuzzy dedup: enrich -> block -> re-rank -> union-find clusters.

  python cluster.py data/wa_names.txt --threshold 0.82
"""
from __future__ import annotations

import argparse
import math
from collections import Counter

from enrich import enrich
from match import score, BlockingIndex


def load(path):
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def doc_keys(d):
    return {t["key"] for t in (d.names + d.orgs + d.anchors) if t["key"]}


def build_idf(docs):
    df = Counter()
    for d in docs:
        df.update(doc_keys(d))
    n = len(docs)
    # smoothed idf; common tokens (TOM, Makers, owner name) -> near 0
    return {k: math.log(1 + n / (1 + c)) for k, c in df.items()}


def is_person(d):
    return d.type == "person" and 1 <= len(d.names) <= 3


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--threshold", type=float, default=0.82)
    p.add_argument("--max-show", type=int, default=40)
    p.add_argument("--persons-only", action="store_true",
                   help="cluster only person-type contacts with 1-3 name tokens")
    p.add_argument("--idf-floor", type=float, default=4.0,
                   help="a merge needs a shared key at least this discriminative")
    args = p.parse_args()

    raws = list(dict.fromkeys(load(args.file)))
    docs = [enrich(r) for r in raws]
    idf = build_idf(docs)
    if args.persons_only:
        docs = [d for d in docs if is_person(d)]
    idx = BlockingIndex(docs)
    keys = [doc_keys(d) for d in docs]

    parent = list(range(len(docs)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    comparisons = 0
    seen = set()
    for i in range(len(docs)):
        for j in idx.candidates(i):
            if (j, i) in seen or i == j:
                continue
            seen.add((i, j))
            comparisons += 1
            shared = keys[i] & keys[j]
            if not any(idf.get(k, 0) >= args.idf_floor for k in shared):
                continue  # merge must rest on a rare, discriminative shared key
            if score(docs[i], docs[j], idf) >= args.threshold:
                parent[find(i)] = find(j)

    groups: dict[int, list[int]] = {}
    for i in range(len(docs)):
        groups.setdefault(find(i), []).append(i)
    clusters = [g for g in groups.values() if len(g) > 1]

    print(f"{len(docs)} contacts | {comparisons} candidate pairs scored "
          f"(vs {len(docs)*(len(docs)-1)//2} brute force) | "
          f"{len(clusters)} clusters at {args.threshold}\n")
    for g in sorted(clusters, key=len, reverse=True)[:args.max_show]:
        print("  cluster:")
        for i in g:
            d = docs[i]
            tag = d.type if d.type != "person" else ""
            print(f"    {d.raw:<28} {tag}")
        print()


if __name__ == "__main__":
    main()
