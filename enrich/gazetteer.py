"""Place / organisation gazetteer lookup (keeps open-class tokens out of names).

Loads data/gazetteer.json. Matching is case-insensitive on a single token or a
2-3 word phrase ("tel aviv", "new york"). Extend the JSON freely; to go massive,
merge a permissively-licensed source (GeoNames, CC-BY) and attribute it.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

_PATH = os.environ.get(
    "GAZETTEER_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "gazetteer.json"),
)


@lru_cache(maxsize=1)
def _load():
    with open(_PATH, encoding="utf-8") as f:
        data = json.load(f)
    places = {p.lower() for p in data.get("places", [])}
    orgs = {o.lower() for o in data.get("orgs", [])}
    return places, orgs


def is_place(phrase: str) -> bool:
    return phrase.lower() in _load()[0]


def is_org(phrase: str) -> bool:
    return phrase.lower() in _load()[1]
