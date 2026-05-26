"""Build the Elasticsearch blocking query for an enriched query name.

Stage 1 (this query): cheap, recall-oriented candidate generation. It scores
natively over the stored values with these priorities:

    exact raw            boost 10   identical string
    name_keys term       boost 5    shared folded consonant skeleton (x-script)
    name_ipa match~1     boost 4    fuzzy phoneme overlap (edit distance <=1)
    org_ipa match~1      boost 3
    anchor_keys term     boost 2    same referenced person ("mom of Uri")
    roles term           boost 1    same relationship (disambiguation only)

`minimum_should_match: 1` keeps it a candidate generator; precision comes from
re-ranking the top-K with match.rerank.score (the feature-weighted engine ES
cannot run itself).
"""
from __future__ import annotations

from enrich import EnrichedDoc


def blocking_query(doc: EnrichedDoc, size: int = 50) -> dict:
    should = [
        {"term": {"raw.kw": {"value": doc.raw, "boost": 10}}},
    ]
    for k in doc.name_keys:
        should.append({"term": {"name_keys": {"value": k, "boost": 5}}})
    if doc.name_ipa:
        should.append({"match": {"name_ipa": {
            "query": " ".join(doc.name_ipa), "fuzziness": 1, "boost": 4}}})
    if doc.org_ipa:
        should.append({"match": {"org_ipa": {
            "query": " ".join(doc.org_ipa), "fuzziness": 1, "boost": 3}}})
    for k in doc.anchor_keys:
        should.append({"term": {"anchor_keys": {"value": k, "boost": 2}}})
    for r in doc.roles:
        should.append({"term": {"roles": {"value": r, "boost": 1}}})

    return {
        "size": size,
        "query": {"bool": {"should": should, "minimum_should_match": 1}},
    }
