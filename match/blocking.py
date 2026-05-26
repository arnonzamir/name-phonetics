"""In-memory candidate generation that mirrors the ES blocking stage.

Inverted index from phonetic key -> doc ids (name keys + anchor keys). Two docs
are candidates iff they share a key. This is exactly what the ES `name_keys`
term query does; we simulate it here so the prototype runs without reindexing
the production cluster.
"""
from __future__ import annotations

from collections import defaultdict

from enrich import EnrichedDoc

MIN_KEY = 2  # keys shorter than this are too common to block on alone


def _block_keys(doc: EnrichedDoc) -> set[str]:
    keys = {k for k in doc.name_keys + doc.anchor_keys if len(k) >= MIN_KEY}
    if not keys:  # very short name (e.g. אנה->'n'): fall back to all keys
        keys = set(doc.name_keys + doc.anchor_keys)
    return keys


class BlockingIndex:
    def __init__(self, docs: list[EnrichedDoc]):
        self.docs = docs
        self.by_key: dict[str, list[int]] = defaultdict(list)
        for i, d in enumerate(docs):
            for k in _block_keys(d):
                self.by_key[k].append(i)

    def candidates(self, i: int) -> set[int]:
        out: set[int] = set()
        for k in _block_keys(self.docs[i]):
            out.update(self.by_key.get(k, ()))
        out.discard(i)
        return out
