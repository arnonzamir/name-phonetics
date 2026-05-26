import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from enrich import enrich          # noqa: E402
from match import score            # noqa: E402


def test_taxonomy():
    d = enrich("אנה אמא של אורי (גן תמר)")
    assert d.type == "person"
    assert "parent" in d.roles
    assert d.anchors and d.anchors[0]["text"] == "אורי"
    assert any(c["text"] == "גן תמר" for c in d.context)

    org = enrich("קהילת מייקינג חינוך")
    assert org.type == "org"


def test_emoji_and_year_dropped():
    d = enrich("😉טל Tal Sunbit")
    assert "😉" not in d.to_es()["name_text"]
    delta = enrich("Delta 2016")
    assert "2016" not in delta.to_es()["name_text"]
    assert "2016" in delta.dropped


def test_nickname_bridge():
    assert score(enrich("דודו"), enrich("דוד")) > 0.8
    assert score(enrich("איתוש"), enrich("איתמר")) > 0.8
    assert score(enrich("Bob"), enrich("Robert")) > 0.8


def test_benchmark_regression():
    """The labeled benchmark must keep beating flat IPA edit distance."""
    import jellyfish
    from engine import to_ipa, detect_lang, similarity
    from data.testcases import PAIRS

    def best_f1(scorer):
        rows = [(scorer(a, b), lab) for a, b, lab, _ in PAIRS]
        best = 0.0
        for t in [i / 100 for i in range(101)]:
            tp = sum(1 for s, l in rows if s >= t and l)
            fp = sum(1 for s, l in rows if s >= t and not l)
            fn = sum(1 for s, l in rows if s < t and l)
            p = tp / (tp + fp) if tp + fp else 0
            r = tp / (tp + fn) if tp + fn else 0
            f1 = 2 * p * r / (p + r) if p + r else 0
            best = max(best, f1)
        return best

    phonetic = best_f1(lambda a, b: similarity(to_ipa(a, detect_lang(a)),
                                               to_ipa(b, detect_lang(b))))
    lev = best_f1(lambda a, b: 1 - jellyfish.levenshtein_distance(
        to_ipa(a, detect_lang(a)), to_ipa(b, detect_lang(b))) / max(
        len(to_ipa(a, detect_lang(a))), len(to_ipa(b, detect_lang(b))), 1))

    assert phonetic >= 0.85
    assert phonetic > lev
