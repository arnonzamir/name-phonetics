"""Labeled name pairs for evaluating the matcher.

Each row: (name_a, name_b, is_match, category)
  is_match  True  -> same name (should score high / be deduped together)
            False -> different names (hard negatives: share letters or sounds)
  category  'cross'   Hebrew <-> English/romanized
            'translit' romanization variant (latin <-> latin)
            'heb'      Hebrew spelling/vowel variant
            'en'       English-only variant

Hard negatives are deliberately tempting (shared prefixes, shared consonant
skeletons, gender variants) so the threshold has to actually discriminate.
"""

PAIRS = [
    # ---- cross-script positives (he <-> en) ----
    ("משה", "Moshe", True, "cross"),
    ("משה", "Moses", True, "cross"),
    ("יעקב", "Yaakov", True, "cross"),
    ("יעקב", "Jacob", True, "cross"),
    ("שרה", "Sarah", True, "cross"),
    ("שרה", "Sara", True, "cross"),
    ("יצחק", "Yitzhak", True, "cross"),
    ("יצחק", "Isaac", True, "cross"),
    ("אברהם", "Avraham", True, "cross"),
    ("אברהם", "Abraham", True, "cross"),
    ("דוד", "David", True, "cross"),
    ("יוסף", "Yosef", True, "cross"),
    ("יוסף", "Joseph", True, "cross"),
    ("חיים", "Chaim", True, "cross"),
    ("חיים", "Haim", True, "cross"),
    ("רחל", "Rachel", True, "cross"),
    ("מרים", "Miriam", True, "cross"),
    ("נועה", "Noa", True, "cross"),
    ("יונתן", "Yonatan", True, "cross"),
    ("יונתן", "Jonathan", True, "cross"),
    ("בנימין", "Binyamin", True, "cross"),
    ("בנימין", "Benjamin", True, "cross"),
    ("אסתר", "Esther", True, "cross"),
    ("מיכאל", "Michael", True, "cross"),
    ("גבריאל", "Gabriel", True, "cross"),
    ("שלמה", "Shlomo", True, "cross"),
    ("עומר", "Omer", True, "cross"),
    ("צבי", "Tzvi", True, "cross"),
    ("לוי", "Levi", True, "cross"),
    ("רבקה", "Rivka", True, "cross"),
    ("שירה", "Shira", True, "cross"),
    ("תמר", "Tamar", True, "cross"),

    # ---- romanization variants (latin <-> latin) ----
    ("Moshe", "Moses", True, "translit"),
    ("Yaakov", "Yaacov", True, "translit"),
    ("Yaakov", "Jacob", True, "translit"),
    ("Chaim", "Haim", True, "translit"),
    ("Chaim", "Hayim", True, "translit"),
    ("Yosef", "Yossef", True, "translit"),
    ("Tzvi", "Zvi", True, "translit"),
    ("Cohen", "Kohen", True, "translit"),
    ("Levi", "Levy", True, "translit"),
    ("Yitzhak", "Yitzchak", True, "translit"),
    ("Sara", "Sarah", True, "en"),
    ("Catherine", "Katherine", True, "en"),
    ("Sofia", "Sophia", True, "en"),
    ("Steven", "Stephen", True, "en"),
    ("Yusuf", "Yousef", True, "translit"),

    # ---- Hebrew spelling/vowel variants ----
    ("חיים", "חײם", True, "heb"),
    ("יעקב", "יעקוב", True, "heb"),
    ("שרה", "שרא", True, "heb"),

    # ---- hard negatives: different names, tempting overlap ----
    ("משה", "Maya", False, "cross"),
    ("יעקב", "Joseph", False, "cross"),
    ("שרה", "Shira", False, "cross"),
    ("דוד", "Daniel", False, "cross"),
    ("רבקה", "Rachel", False, "cross"),
    ("מרים", "Michal", False, "cross"),
    ("חיים", "Hannah", False, "cross"),
    ("יוסף", "Yonatan", False, "cross"),
    ("אברהם", "Aharon", False, "cross"),
    ("תמר", "Tomer", False, "cross"),
    ("עומר", "Amir", False, "cross"),
    ("Moshe", "Mordechai", False, "translit"),
    ("Sarah", "Sharon", False, "en"),
    ("David", "Daniel", False, "en"),
    ("Michael", "Michal", False, "en"),
    ("Tamar", "Tomer", False, "translit"),
    ("Rivka", "Rachel", False, "translit"),
    ("Yosef", "Yonatan", False, "translit"),
    ("Noa", "Naomi", False, "en"),
    ("Levi", "Liav", False, "translit"),
    ("Chana", "Chaim", False, "translit"),
    ("Binyamin", "Benzion", False, "translit"),
    ("Gabriel", "Gavriela", False, "en"),
    ("Esther", "Eden", False, "en"),
    ("Miriam", "Miron", False, "en"),
    ("שרה", "סער", False, "heb"),
    ("דן", "דנה", False, "heb"),
    ("רון", "רוני", False, "heb"),

    # ---- the "arnon" r-n family: live collisions from WaSearch ----
    # True: the same name across scripts must still match.
    ("ארנון", "Arnon", True, "cross"),
    ("אורן", "Oren", True, "cross"),
    # False: different people the vowel-cheap skeleton merged into "rn".
    ("Arnon", "Oren", False, "en"),
    ("ארנון", "אורן", False, "heb"),
    ("Arnon", "Roni", False, "translit"),
    ("Arnon", "Aharon", False, "translit"),
    ("Arnon", "Raanan", False, "translit"),
    ("ארנון", "רינה", False, "cross"),
    ("ארנון", "רוני", False, "cross"),
]
