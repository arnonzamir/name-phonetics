#!/usr/bin/env python
"""Compare two names.

  python cli.py "משה" "Moses"                 # phonetic similarity (IPA only)
  python cli.py --full "דודו" "David"         # full entity-resolution score
  python cli.py --lang-a he --lang-b en "חיים" "Chaim"

--full adds the relationship-aware score: nickname expansion (דודו->דוד),
roles and anchors. Without it you get the raw phonetic distance only.
"""
import argparse

from engine import compare
from enrich import enrich
from match import score as resolve_score


def main():
    p = argparse.ArgumentParser(description="Phonetic Hebrew/English name comparison")
    p.add_argument("name_a")
    p.add_argument("name_b")
    p.add_argument("--lang-a", choices=["he", "en"], default=None)
    p.add_argument("--lang-b", choices=["he", "en"], default=None)
    p.add_argument("--full", action="store_true",
                   help="full entity-resolution score (nicknames, roles, anchors)")
    args = p.parse_args()

    m = compare(args.name_a, args.name_b, args.lang_a, args.lang_b)
    print(f"{m.name_a:<14} -> /{m.ipa_a}/")
    print(f"{m.name_b:<14} -> /{m.ipa_b}/")
    print(f"phonetic   = {m.score:.3f}")
    if args.full:
        full = resolve_score(enrich(args.name_a), enrich(args.name_b))
        print(f"resolution = {full:.3f}")


if __name__ == "__main__":
    main()
