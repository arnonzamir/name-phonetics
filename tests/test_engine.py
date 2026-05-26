import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from engine import to_ipa, similarity, compare           # noqa: E402
from engine.distance import phonetic_key                  # noqa: E402


def test_hebrew_g2p_vowels():
    # phonikud must restore vowels (espeak alone drops them)
    assert to_ipa("משה", "he") == "moʃe"
    assert to_ipa("דוד", "he") == "david"


def test_cross_script_key_blocking():
    # same folded consonant skeleton across scripts
    assert phonetic_key(to_ipa("Sunbit")) == phonetic_key(to_ipa("סנביט"))
    assert phonetic_key(to_ipa("Cohen")) == phonetic_key(to_ipa("כהן"))


def test_similarity_bounds_and_order():
    assert compare("דוד", "David").score > 0.75
    assert compare("דוד", "David").score > compare("דוד", "Sarah").score
