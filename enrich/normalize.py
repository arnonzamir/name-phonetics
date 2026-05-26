"""String cleanup + tokenization for raw contact names."""
from __future__ import annotations

import re

# Emoji + pictographs + variation selectors + ZWJ.
_EMOJI = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U0001F1E6-\U0001F1FF"
    "\U0000FE00-\U0000FE0F\U00002190-\U000021FF\U00002B00-\U00002BFF\U0000200D]"
)
_HEB = re.compile(r"[֐-׿]")
_LAT = re.compile(r"[A-Za-z]")
# A token: run of Hebrew (incl. geresh/gershayim) or Latin letters, or digits.
_TOKEN = re.compile(r"[A-Za-z]+|[א-ת׳״\"']+|\d+")
_PAREN = re.compile(r"[\(\[]([^\)\]]*)[\)\]]")


def script_of(tok: str) -> str:
    if _HEB.search(tok):
        return "heb"
    if _LAT.search(tok):
        return "lat"
    return "other"


def strip_emoji(s: str) -> str:
    return _EMOJI.sub(" ", s)


def extract_parens(s: str):
    """Return (string_without_parens, [paren_contents])."""
    parens = [m.group(1).strip() for m in _PAREN.finditer(s) if m.group(1).strip()]
    return _PAREN.sub(" ", s), parens


def tokenize(s: str) -> list[str]:
    return _TOKEN.findall(s)
