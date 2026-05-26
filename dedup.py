#!/usr/bin/env python
"""Fuzzy phonetic dedup over a list of names.

Reads one name per line (Hebrew or English/romanized, auto-detected), converts
each to IPA once, then clusters names whose pairwise phonetic similarity is
>= threshold. Prints the clusters with more than one member.

  python dedup.py data/sample_names.txt --threshold 0.78
"""
from __future__ import annotations

import argparse
import sys

from engine import to_ipa, detect_lang, similarity


def load(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip()]


def cluster(names: list[str], threshold: float):
    ipa = {n: to_ipa(n, detect_lang(n)) for n in names}
    parent = {n: n for n in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        parent[find(a)] = find(b)

    uniq = list(dict.fromkeys(names))
    for i in range(len(uniq)):
        for j in range(i + 1, len(uniq)):
            a, b = uniq[i], uniq[j]
            if similarity(ipa[a], ipa[b]) >= threshold:
                union(a, b)

    groups: dict[str, list[str]] = {}
    for n in uniq:
        groups.setdefault(find(n), []).append(n)
    return ipa, [g for g in groups.values() if len(g) > 1]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--threshold", type=float, default=0.78)
    args = p.parse_args()

    names = load(args.file)
    ipa, clusters = cluster(names, args.threshold)
    print(f"{len(set(names))} unique names, "
          f"{len(clusters)} fuzzy clusters at threshold {args.threshold}\n")
    for c in sorted(clusters, key=len, reverse=True):
        print("  cluster:")
        for n in c:
            print(f"    {n:<16} /{ipa[n]}/")
        print()


if __name__ == "__main__":
    sys.exit(main())
