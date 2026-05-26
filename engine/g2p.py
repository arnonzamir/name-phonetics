"""Grapheme-to-phoneme: turn a Hebrew or English name into normalized IPA.

Hebrew path  : phonikud-onnx (predict niqqud) -> phonikud (niqqud -> IPA)
English path : espeak-ng (-v en-us --ipa)

Both outputs are run through `normalize_ipa` so they live in one comparable
symbol space (stress/length stripped, espeak quirks folded, the two rhotics
and a few systematic variants unified). The matching engine in distance.py
does the rest with articulatory features + a small equivalence table.
"""
from __future__ import annotations

import os
import re
import subprocess
from functools import lru_cache

HEB_RANGE = re.compile(r"[֐-׿]")
NIQQUD = re.compile(r"[ְ-ׇ]")  # already-vocalized?
_DEFAULT_MODEL = os.path.join(os.path.dirname(__file__), "..", "models", "phonikud-1.0.int8.onnx")
_HF_REPO = "thewh1teagle/phonikud-onnx"
_HF_FILE = "phonikud-1.0.int8.onnx"


def _model_path() -> str:
    path = os.environ.get("PHONIKUD_MODEL", _DEFAULT_MODEL)
    if os.path.exists(path):
        return path
    # download once and cache locally (no 307 MB blob committed to the repo)
    from huggingface_hub import hf_hub_download
    os.makedirs(os.path.dirname(path), exist_ok=True)
    cached = hf_hub_download(repo_id=_HF_REPO, filename=_HF_FILE)
    try:
        os.symlink(cached, path)
    except OSError:
        path = cached
    return path

# espeak-ng emits a handful of symbols panphon does not know; fold them to the
# nearest standard IPA so no segment is silently dropped.
_ESPEAK_FOLD = str.maketrans({
    "ᵻ": "ɪ", "ᵿ": "ʊ", "ɚ": "ə", "ɝ": "ɜ", "ɫ": "l", "g": "ɡ",
})
# Strip: primary/secondary stress, length, syllable/word breaks, ties.
_STRIP = re.compile(r"[ˈˌːˑ.‿͡ ]")
# Unify both rhotics (English ɹ, Hebrew/uvular ʁ) and trill to one symbol r.
_RHOTIC = str.maketrans({"ɹ": "r", "ʁ": "r", "ʀ": "r", "ɾ": "r"})

# panphon has no precomposed affricate, so fold them to a single base segment
# chosen to align cross-script name variants:
#   dʒ -> j  (English J-names romanize Hebrew yod: Joseph/Yosef, Jacob/Yaakov)
#   tʃ -> x  (English "ch" reading of Hebrew ח/כ: Chaim/חיים, Rachel/רחל)
_AFFRICATE = [("d͡ʒ", "j"), ("dʒ", "j"), ("t͡ʃ", "x"), ("tʃ", "x")]


def normalize_ipa(ipa: str) -> str:
    ipa = ipa.translate(_ESPEAK_FOLD)
    for src, dst in _AFFRICATE:
        ipa = ipa.replace(src, dst)
    ipa = _STRIP.sub("", ipa)
    ipa = ipa.translate(_RHOTIC)
    # espeak diphthongs like oʊ/eɪ/aɪ are kept as-is; panphon segments them.
    return ipa.strip()


def detect_lang(text: str) -> str:
    return "he" if HEB_RANGE.search(text) else "en"


class _Phonikud:
    """Lazy holder for the 307 MB ONNX niqqud model + phonemizer."""
    _model = None

    @classmethod
    def ipa(cls, text: str) -> str:
        from phonikud import phonemize
        if NIQQUD.search(text):
            voweled = text
        else:
            if cls._model is None:
                from phonikud_onnx import Phonikud
                cls._model = Phonikud(_model_path())
            voweled = cls._model.add_diacritics(text)
        return phonemize(voweled)


def _espeak_ipa(text: str, voice: str = "en-us") -> str:
    out = subprocess.run(
        ["espeak-ng", "-v", voice, "--ipa", "-q", text],
        capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


@lru_cache(maxsize=4096)
def to_ipa(text: str, lang: str | None = None) -> str:
    """Return normalized IPA for a name. `lang` in {'he','en'} or None to auto-detect."""
    text = text.strip()
    if not text:
        return ""
    lang = lang or detect_lang(text)
    raw = _Phonikud.ipa(text) if lang == "he" else _espeak_ipa(text)
    return normalize_ipa(raw)
