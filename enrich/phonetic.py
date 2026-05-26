"""Attach IPA + blocking key to a name-like token."""
from __future__ import annotations

from engine.g2p import to_ipa
from engine.distance import phonetic_key
from .normalize import script_of


def phonemize_token(text: str) -> dict:
    sc = script_of(text)
    lang = "he" if sc == "heb" else "en"
    ipa = to_ipa(text, lang) if sc in ("heb", "lat") else ""
    return {"text": text, "script": sc, "ipa": ipa, "key": phonetic_key(ipa)}
