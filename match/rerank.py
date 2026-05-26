"""Precise re-ranking score between two enriched docs.

Token-set, order-independent and SYMMETRIC: every token on *both* sides must be
covered, so "TOM" vs "Israeli president TOM VN" no longer scores 1.0 just
because TOM matches — the four unmatched tokens drag it down.

Tokens are IDF-weighted: a token shared by many contacts (TOM, Makers, the
owner's own name) contributes little to both the match and the normalizer, so
common words stop bridging unrelated records. Pass `idf` (key -> weight) from
the corpus; default weight 1.0 (no IDF).

Field scores combine by weight, and only fields where BOTH docs carry signal
contribute, so a shared role alone can't merge strangers.
"""
from __future__ import annotations

from engine import similarity
from enrich import EnrichedDoc

W_PRIMARY = 1.0    # names + orgs (identity)
W_ANCHOR = 0.5     # referenced person
W_ROLE = 0.25      # relationship label

Idf = dict  # key -> weight


def _primary_tokens(d: EnrichedDoc):
    return [(t["ipa"], t["key"]) for t in (d.names + d.orgs) if t["ipa"]]


def _weighted_set_sim(a, b, idf: Idf | None):
    """a,b: lists of (ipa,key). Symmetric, IDF-weighted coverage."""
    a = [t for t in a if t[0]]
    b = [t for t in b if t[0]]
    if not a and not b:
        return 0.0, False
    if not a or not b:
        return 0.0, True

    def w(key):
        return idf.get(key, 1.0) if idf else 1.0

    def directed(src, dst):
        num = den = 0.0
        for ipa, key in src:
            wt = w(key)
            num += wt * max(similarity(ipa, d_ipa) for d_ipa, _ in dst)
            den += wt
        return num, den

    na, da = directed(a, b)
    nb, db = directed(b, a)
    return (na + nb) / (da + db), True


def _role_overlap(a, b):
    sa, sb = set(a), set(b)
    if not sa and not sb:
        return 0.0, False
    if not sa or not sb:
        return 0.0, True
    return len(sa & sb) / len(sa | sb), True


def score(a: EnrichedDoc, b: EnrichedDoc, idf: Idf | None = None) -> float:
    fields = [
        (W_PRIMARY, *_weighted_set_sim(_primary_tokens(a), _primary_tokens(b), idf)),
        (W_ANCHOR, *_weighted_set_sim([(t["ipa"], t["key"]) for t in a.anchors],
                                      [(t["ipa"], t["key"]) for t in b.anchors], idf)),
        (W_ROLE, *_role_overlap(a.roles, b.roles)),
    ]
    num = sum(wt * v for wt, v, present in fields if present)
    den = sum(wt for wt, v, present in fields if present)
    return num / den if den else 0.0
