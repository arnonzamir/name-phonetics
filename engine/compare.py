"""Top-level name comparison API."""
from __future__ import annotations

from dataclasses import dataclass

from .g2p import to_ipa, detect_lang, romanize_ipa
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


def _ipa(name: str, lang: str, cross_script: bool) -> str:
    # On a CROSS-SCRIPT compare, render a Latin name with the cardinal
    # romanizer (it's a transliteration, not an English word) so the same name
    # converges across scripts; Hebrew always goes through phonikud. Same-script
    # uses the native G2P (espeak is right for English-native names).
    if cross_script and lang == "en":
        return romanize_ipa(name)
    return to_ipa(name, lang)


def ipa_pair(name_a: str, name_b: str,
             lang_a: str | None = None, lang_b: str | None = None) -> tuple[str, str]:
    """The IPA pair used for comparison, with cross-script romanization applied.
    Shared by `compare` and the eval harness so both test the same path."""
    la = lang_a or detect_lang(name_a)
    lb = lang_b or detect_lang(name_b)
    cross = la != lb
    return _ipa(name_a, la, cross), _ipa(name_b, lb, cross)


def compare(name_a: str, name_b: str,
            lang_a: str | None = None, lang_b: str | None = None) -> Match:
    ia, ib = ipa_pair(name_a, name_b, lang_a, lang_b)
    return Match(name_a, name_b, ia, ib, similarity(ia, ib))
