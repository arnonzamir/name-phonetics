"""Turn a raw contact name into a typed, phonemized EnrichedDoc.

Lexicon + heuristics (see lexicons.py). Order of decisions per token:
  multi-word role phrase  ->  role (+ following name = anchor)
  multi-word org phrase   ->  org record
  possessive (של/על/of)   ->  next name token is an anchor
  org marker              ->  org record; rest of string is the org name
  digit / Hebrew year     ->  dropped
  otherwise               ->  a NAME token (phonemized)

Open-class descriptive words (e.g. מהמחצבה "from the quarry") are not in any
lexicon and fall through to NAME — a known limitation without a dictionary/POS.
"""
from __future__ import annotations

from .document import EnrichedDoc
from .normalize import strip_emoji, extract_parens, tokenize
from .phonetic import phonemize_token
from .nicknames import canonical
from .lexicons import (
    POSSESSIVE, ROLES, ORG_MARKERS, ORG_MARKERS_MULTI, HEB_YEAR,
)


def _phrase(tokens, i, span):
    return " ".join(tokens[i:i + span]) if i + span <= len(tokens) else None


def enrich(raw: str) -> EnrichedDoc:
    doc = EnrichedDoc(raw=raw)
    s, parens = extract_parens(strip_emoji(raw))
    for p in parens:
        doc.context.append({"text": p, "kind": "paren"})

    toks = tokenize(s)
    n = len(toks)
    i = 0
    mode = "name"          # switches to "org" after an org marker
    expect_anchor = False

    while i < n:
        # --- longest multi-word phrase first (roles, org phrases) ---
        matched = False
        for span in (3, 2):
            ph = _phrase(toks, i, span)
            if ph is None:
                continue
            low = ph.lower()
            if ph in ROLES or low in ROLES:
                role = ROLES.get(ph, ROLES.get(low))
                if role not in doc.roles:
                    doc.roles.append(role)
                expect_anchor = "של" in ph or ph.endswith("ל")
                i += span
                matched = True
                break
            if ph in ORG_MARKERS_MULTI or low in ORG_MARKERS_MULTI:
                doc.type = "org"
                mode = "org"
                i += span
                matched = True
                break
        if matched:
            continue

        tok = toks[i]
        low = tok.lower()

        if tok in POSSESSIVE or low in POSSESSIVE:
            expect_anchor = True
            i += 1
            continue
        if low in ROLES or tok in ROLES:
            role = ROLES.get(tok, ROLES.get(low))
            if role not in doc.roles:
                doc.roles.append(role)
            i += 1
            continue
        if tok in ORG_MARKERS or low in ORG_MARKERS:
            doc.type = "org"
            mode = "org"
            i += 1
            continue
        if tok.isdigit() or tok.startswith(HEB_YEAR):
            doc.dropped.append(tok)
            i += 1
            continue

        info = phonemize_token(tok)
        if info["script"] == "other" or not info["ipa"]:
            doc.dropped.append(tok)
            i += 1
            continue

        if expect_anchor:
            doc.anchors.append(info)
            expect_anchor = False
        elif mode == "org":
            doc.orgs.append(info)
        else:
            doc.names.append(info)
            canon = canonical(tok)
            if canon:  # nickname -> add canonical phonetics as an alternate
                alt = phonemize_token(canon)
                alt["via"] = "nickname"
                doc.names.append(alt)
        i += 1

    # org marker but the descriptive tokens landed in names -> reclassify
    if doc.type == "org" and not doc.orgs and doc.names:
        doc.orgs, doc.names = doc.names, []

    return doc.finalize()
