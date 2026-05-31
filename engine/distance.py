"""Phonetic similarity between two IPA strings.

Core idea: a Needleman-Wunsch / edit alignment over IPA *segments*, where the
substitution cost is the articulatory-feature distance between the two
segments (panphon's 24 binary features), not a flat 1. So /x/~/k/ (a couple of
features apart) costs far less than /x/~/m/.

On top of the feature metric we layer an EQUIVALENCE TABLE: pairs that are
phonetically a bit apart but are *systematic Hebrew<->English transliteration
swaps* (e.g. ח/כ /x/ <-> English h or k; צ /ts/ <-> s) get their cost floored
low. This is the PHOIBLE-informed part — it encodes inventory mismatches that
pure feature distance underweights.

Indels for glottals (א/ע /ʔ ʕ/, h) and for vowels are cheap, because those are
the segments most often added or dropped across transliterations.
"""
from __future__ import annotations

from functools import lru_cache

import panphon

_FT = panphon.FeatureTable()
_NFEAT = len(_FT.names)

# --- segment classes -------------------------------------------------------
VOWELS = set("aeiouɑɒɔəɛɜæɪʊʌyøœ")
GLOTTAL = set("ʔʕhɦ")  # aleph / ayin / he — frequently silent or inserted

# Equivalence classes: any two members are "cheaply" interchangeable.
# Cost between two members of the same class is floored at EQUIV_FLOOR.
# NOTE: each entry is an explicit tuple of single IPA segments (do not use
# set("...") here — it would split multi-char strings into chars).
_EQUIV_CLASSES = [
    ("x", "χ", "k", "h"),   # ח/כ kh ~ h ~ k, and folded "ch" (Chaim/Haim/Rachel)
    ("s", "z", "ʃ"),        # sibilants: צ's s, ש/שׂ, voicing slip
    ("v", "b", "w"),        # ב vet/bet ~ w
    ("t", "d"),             # voicing slip
    ("ʔ", "ʕ", "h"),        # glottals interchange / drop
    ("j", "i"),             # י as glide vs vowel (j also covers folded English J)
    ("u", "v", "w"),        # ו vav as u / v / w
    ("o", "u"),             # holam ~ shuruk
]
_EQUIV_INDEX = {}
for _cls in _EQUIV_CLASSES:
    for _m in _cls:
        _EQUIV_INDEX.setdefault(_m, set()).update(_cls)
EQUIV_FLOOR = 0.12

# Per-segment WEIGHT — how much a segment counts toward the score, in both the
# cost and the normalizer. Consonants carry name identity; vowels drift freely
# across transliteration, so they barely count.
W_CONS = 1.0
W_GLOTTAL = 0.35   # א/ע/h: often silent or inserted
W_VOWEL = 0.25

VOWEL_SUB = 0.40        # cap on vowel<->vowel substitution cost (SAME round-class)
CONS_SUB_FLOOR = 0.60   # floor on distinct non-equivalent consonant subs

# Rounded / back vowels. A name's O/U anchor (חולם/שורוק, English o/u) is
# identity-bearing — "Arnon" vs "Oren", "Tamar" vs "Tomer" hinge on it — so an
# O/U <-> A/E/I flip must NOT be cheap like a generic vowel drift.
ROUND_VOWELS = set("ouɔʊoʊøœuː")
VOWEL_ROUND_FLOOR = 0.55  # floor on a rounded<->unrounded vowel sub (uncapped)
W_VOWEL_ROUND = 0.60      # weight of a round-flip vowel sub (vs W_VOWEL=0.25)

# Multiplicative similarity adjustments layered on top of the alignment score:
#  (1) FIRST-SOUND family — humans key on the initial sound. If the first
#      (non-glottal) segments aren't the same family, kill the match hard.
#  (3) SYLLABLE LENGTH — a long name squished onto a short one (Ra-a-nan vs
#      Ar-non) should not pass; penalize a vowel-count gap > 1.
W_FIRST_VOWEL = 0.70     # both vowels but rounded-vs-unrounded (Arnon a- vs Oren o-)
W_FIRST_CROSS = 0.85     # vowel onset vs consonant onset (gentle: ח/yod drop a lot)
W_FIRST_CONS = 0.85      # distinct, non-equivalent initial consonants
SYLLABLE_STEP = 0.20     # penalty per syllable of gap beyond the first


def _weight(seg: str) -> float:
    if seg in GLOTTAL:
        return W_GLOTTAL
    if seg in VOWELS:
        return W_VOWEL
    return W_CONS


def _equiv(a: str, b: str) -> bool:
    return b in _EQUIV_INDEX.get(a, ())


@lru_cache(maxsize=20000)
def _vec(seg: str):
    vs = _FT.word_to_vector_list(seg, numeric=True)
    return vs[0] if vs else None


@lru_cache(maxsize=50000)
def _feature_dist(a: str, b: str) -> float:
    """Unweighted articulatory distance in [0,1] between two segments."""
    if a == b:
        return 0.0
    if _equiv(a, b):
        return EQUIV_FLOOR
    va, vb = _vec(a), _vec(b)
    if va is None or vb is None:
        return 1.0  # unknown symbol -> full mismatch
    diff = sum(abs(x - y) for x, y in zip(va, vb)) / (2.0 * _NFEAT)
    if a in VOWELS and b in VOWELS:
        # A rounded/back <-> unrounded flip (o/u <-> a/e/i) is an identity
        # signal, not free drift — floor it and don't cap. Same round-class
        # vowels still drift cheaply.
        if (a in ROUND_VOWELS) != (b in ROUND_VOWELS):
            return max(diff, VOWEL_ROUND_FLOOR)
        return min(diff, VOWEL_SUB)
    # two distinct, non-equivalent consonants = a real identity difference,
    # even when they share most articulatory features (v/n, d/l, ...).
    if a not in VOWELS and b not in VOWELS:
        return max(diff, CONS_SUB_FLOOR)
    return diff


def sub_cost(a: str, b: str) -> float:
    """Weighted substitution cost: feature distance scaled by segment weight.

    Cross-class subs (vowel<->consonant) are penalized at the heavier weight so
    a vowel cannot cheaply absorb a consonant."""
    fd = _feature_dist(a, b)
    av, bv = a in VOWELS, b in VOWELS
    if av and bv and (a in ROUND_VOWELS) != (b in ROUND_VOWELS):
        w = W_VOWEL_ROUND  # round-flip counts far more than a generic vowel drift
    elif av != bv:
        w = max(_weight(a), _weight(b))
    else:
        w = (_weight(a) + _weight(b)) / 2
    return fd * w


def _indel(seg: str) -> float:
    return _weight(seg)


def _segments(ipa: str):
    return _FT.ipa_segs(ipa) or list(ipa)


def align_cost(ipa_a: str, ipa_b: str):
    """Edit distance over segments; returns (cost, normalizer)."""
    A, B = _segments(ipa_a), _segments(ipa_b)
    n, m = len(A), len(B)
    if n == 0 and m == 0:
        return 0.0, 1.0
    d = [[0.0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        d[i][0] = d[i - 1][0] + _indel(A[i - 1])
    for j in range(1, m + 1):
        d[0][j] = d[0][j - 1] + _indel(B[j - 1])
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d[i][j] = min(
                d[i - 1][j] + _indel(A[i - 1]),
                d[i][j - 1] + _indel(B[j - 1]),
                d[i - 1][j - 1] + sub_cost(A[i - 1], B[j - 1]),
            )
    # normalizer: total weight of the heavier string
    norm = max(sum(_weight(s) for s in A), sum(_weight(s) for s in B), 1e-9)
    return d[n][m], norm


def _sound_family(seg: str) -> str:
    """Coarse family of a segment for the first-sound gate: a rounded vowel, an
    unrounded vowel, or a consonant equivalence class."""
    if seg in VOWELS:
        return "V_round" if seg in ROUND_VOWELS else "V_open"
    canon = next(iter(_EQUIV_INDEX.get(seg, {seg})))  # any class member as the key
    return f"C:{_CANON.get(seg, canon)}"


def _first_seg(segs: list[str]) -> str | None:
    """First non-glottal segment (א/ע/h are routinely silent or inserted)."""
    for s in segs:
        if s not in GLOTTAL:
            return s
    return None


def _first_sound_factor(A: list[str], B: list[str]) -> float:
    """Penalize when the two names don't begin with the same sound family.
    Respects the equivalence table, so systematic onset swaps (ח↔h↔k, yod↔i)
    are NOT penalized — only genuinely different onsets are."""
    a, b = _first_seg(A), _first_seg(B)
    if a is None or b is None or a == b or _equiv(a, b):
        return 1.0
    fa, fb = _sound_family(a), _sound_family(b)
    if fa == fb:
        return 1.0
    av, bv = fa.startswith("V"), fb.startswith("V")
    if av and bv:
        return W_FIRST_VOWEL   # rounded vs unrounded onset (Arnon a- vs Oren o-)
    if av != bv:
        return W_FIRST_CROSS   # vowel onset vs consonant onset
    return W_FIRST_CONS        # two distinct initial consonants


def _syllables(segs: list[str]) -> int:
    """Count vowel GROUPS (a run of vowels = one syllable), so a diphthong like
    oʊ/eɪ counts once rather than inflating the length."""
    n, prev_v = 0, False
    for s in segs:
        v = s in VOWELS
        if v and not prev_v:
            n += 1
        prev_v = v
    return n


def _length_factor(A: list[str], B: list[str]) -> float:
    """Penalize a syllable gap beyond one — a long name squished onto a short
    cluster (Ra-a-nan vs Ar-non) shouldn't pass."""
    gap = abs(_syllables(A) - _syllables(B))
    return 1.0 if gap <= 1 else max(0.4, 1.0 - SYLLABLE_STEP * (gap - 1))


def similarity(ipa_a: str, ipa_b: str) -> float:
    """0..1 phonetic similarity (1 = identical phoneme sequence). The alignment
    score is then gated by first-sound family (1) and syllable length (3)."""
    cost, norm = align_cost(ipa_a, ipa_b)
    sim = max(0.0, 1.0 - cost / norm)
    A, B = _segments(ipa_a), _segments(ipa_b)
    return sim * _first_sound_factor(A, B) * _length_factor(A, B)


# --- coarse phonetic key (for cheap cross-script blocking in ES) ------------
# Fold each consonant to a canonical representative of its equivalence class,
# drop vowels and glottals, collapse repeats. Two names that share a key are
# candidates; the precise re-ranker decides. This is our IPA-derived, cross-
# script answer to Soundex/Beider-Morse.
# consonant -> canonical class symbol (reps are always consonants)
_CANON = {
    "x": "k", "χ": "k", "k": "k", "h": "k",   # ח/כ ~ k ~ folded "ch"
    "s": "s", "z": "s", "ʃ": "s",             # sibilants
    "v": "b", "b": "b", "w": "b",             # ב/ו ~ w
    "t": "t", "d": "t",                       # voicing slip
    "j": "j",                                 # yod / folded English J
}


def phonetic_key(ipa: str) -> str:
    out: list[str] = []
    for s in _segments(ipa):
        if s in VOWELS or s in GLOTTAL:
            continue
        c = _CANON.get(s, s)
        if not out or out[-1] != c:
            out.append(c)
    return "".join(out)
