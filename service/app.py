"""FastAPI enrichment + comparison service (the integration point).

Runs locally as a sidecar. An indexer POSTs raw contact names to /enrich at
ingest and stores the returned typed doc in Elasticsearch (see es/mapping.json).
/compare and /score back the search-time re-rank.

  uvicorn service.app:app --host 0.0.0.0 --port 8099
"""
from __future__ import annotations

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


@app.post("/score")
def score(body: PairIn):
    """Full entity-resolution score (names + roles + anchors + nicknames)."""
    return {"score": _score(enrich(body.a), enrich(body.b))}
