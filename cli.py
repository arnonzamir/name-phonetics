#!/usr/bin/env python
"""Compare two names phonetically.

  python cli.py "משה" "Moses"
  python cli.py --lang-a he --lang-b en "חיים" "Chaim"
"""
import argparse

from engine import compare


def main():
    p = argparse.ArgumentParser(description="Phonetic Hebrew/English name comparison")
    p.add_argument("name_a")
    p.add_argument("name_b")
    p.add_argument("--lang-a", choices=["he", "en"], default=None)
    p.add_argument("--lang-b", choices=["he", "en"], default=None)
    args = p.parse_args()
    m = compare(args.name_a, args.name_b, args.lang_a, args.lang_b)
    print(f"{m.name_a:<14} -> /{m.ipa_a}/")
    print(f"{m.name_b:<14} -> /{m.ipa_b}/")
    print(f"similarity = {m.score:.3f}")


if __name__ == "__main__":
    main()
