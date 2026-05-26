"""Top-level name comparison API."""
from __future__ import annotations

from dataclasses import dataclass

from .g2p import to_ipa, detect_lang
from .distance import similarity


@dataclass
class Match:
    name_a: str
    name_b: str
    ipa_a: str
    ipa_b: str
    score: float

    def __repr__(self) -> str:
        return (f"Match({self.name_a!r}/{self.ipa_a} <-> "
                f"{self.name_b!r}/{self.ipa_b} = {self.score:.3f})")


def compare(name_a: str, name_b: str,
            lang_a: str | None = None, lang_b: str | None = None) -> Match:
    ia = to_ipa(name_a, lang_a or detect_lang(name_a))
    ib = to_ipa(name_b, lang_b or detect_lang(name_b))
    return Match(name_a, name_b, ia, ib, similarity(ia, ib))
