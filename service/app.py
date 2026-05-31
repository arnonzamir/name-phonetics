"""FastAPI enrichment + comparison service (the integration point).

Runs locally as a sidecar. An indexer POSTs raw contact names to /enrich at
ingest and stores the returned typed doc in Elasticsearch (see es/mapping.json).
/compare and /score back the search-time re-rank.

  uvicorn service.app:app --host 0.0.0.0 --port 8099
"""
from __future__ import annotations

import re

from fastapi import FastAPI
from pydantic import BaseModel

from enrich import enrich
from engine import compare as _compare
from match import score as _score

app = FastAPI(title="name-phonetics", version="0.1.0")


class EnrichIn(BaseModel):
    names: list[str]


class PairIn(BaseModel):
    a: str
    b: str


class CompareManyIn(BaseModel):
    a: str
    bs: list[str]


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/enrich")
def enrich_batch(body: EnrichIn):
    """Raw contact names -> typed, phonemized ES documents."""
    return {"docs": [enrich(n).to_es() for n in body.names]}


@app.post("/compare")
def compare(body: PairIn):
    """Phonetic similarity of two raw names (IPA-level)."""
    m = _compare(body.a, body.b)
    return {"ipa_a": m.ipa_a, "ipa_b": m.ipa_b, "score": m.score}


_WORD = re.compile(r"[\s,./_|()\-–—]+")


def _best_score(a: str, b: str) -> float:
    """Best phonetic match of query `a` against candidate `b`, scored against the
    whole name AND each of its word tokens (max). A query that is one word of a
    multi-word name ("arnon" in "Arnon Zamir", "ארנון טל") then matches strongly
    instead of being diluted by the other words."""
    cands = [b]
    toks = [t for t in _WORD.split(b) if t]
    if len(toks) > 1:
        cands.extend(toks)
    return max(_compare(a, c).score for c in cands)


@app.post("/compare_many")
def compare_many(body: CompareManyIn):
    """Phonetic similarity of one query name against many candidates, in one
    call (the search-time name re-rank). `a` is G2P'd once and cached."""
    return {"scores": [_best_score(body.a, b) for b in body.bs]}


@app.post("/score")
def score(body: PairIn):
    """Full entity-resolution score (names + roles + anchors + nicknames)."""
    return {"score": _score(enrich(body.a), enrich(body.b))}
