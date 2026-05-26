"""Nickname / hypocoristic expansion (strictly local, lookup-based).

A name token that is a known nickname also contributes the *canonical* name's
phonetics, so "Dudu"/"דודו" can match "David"/"דוד" and "איתוש" can match
"איתמר" — bridges that phonetic distance alone cannot make.

The map is a curated data file (data/nicknames.json); add entries freely.
"""
from __future__ import annotations

import json
import os
from functools import lru_cache

_PATH = os.environ.get(
    "NICKNAMES_PATH",
    os.path.join(os.path.dirname(__file__), "..", "data", "nicknames.json"),
)


@lru_cache(maxsize=1)
def _table() -> dict[str, str]:
    with open(_PATH, encoding="utf-8") as f:
        data = json.load(f)
    out: dict[str, str] = {}
    for section in ("he", "en"):
        for nick, canon in data.get(section, {}).items():
            out[nick.lower()] = canon
    return out


def canonical(token: str) -> str | None:
    """Return the canonical name for a nickname, or None if not a known nickname."""
    return _table().get(token.lower())
