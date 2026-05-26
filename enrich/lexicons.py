"""Lexicons + heuristics for classifying contact-name tokens.

Closed-class gazetteers (Hebrew + English). Open-class words (arbitrary
surnames, place descriptions like מהמחצבה) cannot be enumerated and fall
through to the NAME bucket — see classify.py.
"""

# Possessive / linking words: the token(s) after these are an ANCHOR name
# ("אמא של אורי" -> anchor Uri; "בייביסיטר על איתוש" -> anchor Itush).
POSSESSIVE = {"של", "על", "of"}

# Relationship / role phrases -> canonical role. Longest phrase wins.
# NOTE: דוד/דודה are intentionally NOT here — they collide with the very common
# given name David (דוד); we keep them as names and accept the miss.
ROLES = {
    "אמא של": "parent", "אבא של": "parent", "אמא": "parent", "אבא": "parent",
    "אימא": "parent", "ima": "parent", "aba": "parent",
    "בת דודה": "cousin", "בן דוד": "cousin", "בן דודה": "cousin",
    "סבא": "grandparent", "סבתא": "grandparent",
    "בייביסיטר": "babysitter", "baby sitter": "babysitter", "babysitter": "babysitter",
    "מטפלת": "caregiver", "מטפל": "caregiver",
    "מורה": "teacher", "גננת": "teacher", "המורה": "teacher",
    "רופא": "doctor", "רופאה": "doctor", "ד\"ר": "doctor", "דר": "doctor",
    "dr": "doctor", "dr.": "doctor", "doctor": "doctor",
    "שכן": "neighbor", "שכנה": "neighbor",
    "עבודה": "work", "work": "work", "מהעבודה": "work",
}

# Words that mark the whole record as an ORGANISATION / group, not a person.
# The marker + the rest of the string become the org name.
ORG_MARKERS = {
    "קהילת", "קהילה", "צוות", "חברת", "חברה", "עמותת", "עמותה", "ועד", "וועד",
    "קבוצת", "קבוצה", "גן", "ביה\"ס", "בי\"ס", "ביהס", "מייקרספייס",
    "makerspace", "ltd", "ltd.", "inc", "inc.", "llc", "בע\"מ", "co",
    "team", "group", "community", "forum", "פורום", "כיתת", "כיתה",
}
# multi-word org markers (checked as phrases)
ORG_MARKERS_MULTI = {"בית ספר", "make a thon", "bay area"}

# Place / origin prefixes (weak signal): a Hebrew token beginning with "מ" that
# is not a known name often means "from <place>" (מהמחצבה, מהעבודה).
PLACE_PREFIXES = ("מה", "מ")

# Tokens to drop outright.
HEB_YEAR = ("תשפ", "תשע", "תשס")  # Hebrew school-year acronyms תשפ"ה etc.
