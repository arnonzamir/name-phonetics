# name-phonetics

Phonetic comparison and **entity resolution** for Hebrew & English contact
names. Converts names to IPA, then matches with an articulatory-feature engine
tuned for cross-script name matching. Built to replace Beider-Morse for fuzzy
dedup and bilingual contact search. Runs **fully local** — no data leaves the
machine.

## What it does

```
raw contact name
   │  enrich/         clean → tokenize → classify (name/org/role/anchor/context)
   │                  → phonemize (IPA + folded key) → nickname expansion
   ▼
EnrichedDoc ──to_es()──▶ Elasticsearch  (es/mapping.json)
   │
   │  match/          blocking (shared phonetic key)  →  IDF-weighted,
   ▼                  symmetric token-set re-rank
similarity / clusters
```

- **Hebrew G2P** (the hard part — no written vowels): `phonikud-onnx` predicts
  niqqud, `phonikud` gives IPA (`משה → מֹשֶׁה → moʃe`, `דוד → david`). espeak
  alone drops Hebrew vowels.
- **English G2P**: `espeak-ng`.
- **Matching**: segment edit distance weighted by panphon articulatory features,
  + HE↔EN equivalence classes (ח/כ `x χ k h`, sibilants, `v b w`…), consonant
  skeleton dominance, affricate folding (`dʒ→j`, `tʃ→x` for Y/J and "ch").
- **Phonetic key**: folded consonant skeleton for cheap cross-script blocking
  (`Sunbit`/`סנביט`→`snbt`) — our IPA-derived answer to Soundex.
- **Taxonomy**: lexicon + heuristics classify tokens into names / orgs / roles
  (`אמא של`) / anchors (the referenced person) / context / dropped (emoji,
  years). See `enrich/lexicons.py`.
- **Nicknames**: curated local map (`data/nicknames.json`) bridges what
  phonetics can't — `דודו↔David`, `איתוש↔איתמר`, `Bob↔Robert`.

## Setup

Requires **Python 3.10–3.12** (phonikud needs <3.13) and `espeak-ng`.

```bash
brew install espeak-ng            # or: apt-get install espeak-ng
pip install -e ".[service,dev]"   # the 307 MB phonikud model downloads on first use
```

## Usage

```bash
nameph-compare "משה" "Moses"                       # two names
python eval.py                                      # labeled benchmark
python cluster.py data/wa_names.txt --persons-only  # cluster a contact list
uvicorn service.app:app --port 8099                 # HTTP service (see below)
```

## Service (the integration point)

| route | purpose |
|---|---|
| `POST /enrich {names:[...]}` | raw names → typed ES docs (index-time) |
| `POST /compare {a,b}` | IPA-level phonetic similarity |
| `POST /score {a,b}` | full entity-resolution score (names+roles+anchors+nicknames) |

Run as a local sidecar; `Dockerfile` builds it. See **INTEGRATION.md** for the
Elasticsearch wiring (mapping, blocking query, re-rank).

## Results (deliberately adversarial 78-pair benchmark)

| method | F1 | precision | recall |
|---|---|---|---|
| **phonetic engine** | **0.881** | 0.814 | 0.960 |
| flat IPA edit distance | 0.855 | 0.783 | 0.940 |
| raw orthographic (Jaro-W) | 0.781 | 0.641 | 1.000 |

Validated on ~1200 real-world contacts: correctly merges cross-script
duplicates (`Impact`/`אימפקט`, `Meir`/`מאיר`) at scale (blocking scores
~6 K pairs vs ~356 K brute force).

## Known limits

- **Phonetic near-twins** (Tamar/Tomer, Michael/Michal) — combine with an
  orthographic signal or raise the threshold.
- **Open-class classification** — orgs without a marker word (`Makers`, `XLN`)
  and places (`Tel Aviv`) are misread as person names. A classifier LLM would
  fix this, but small local models corrupt Hebrew and are too slow on CPU
  (evaluated; rejected for the local-only requirement).
- Clustering is single-linkage; tune `--threshold` / `--idf-floor`.

## Layout

```
engine/   G2P + feature-weighted distance + phonetic key
enrich/   normalize, classify (taxonomy), nicknames → EnrichedDoc
match/    blocking + IDF-weighted re-rank
es/       Elasticsearch mapping + blocking-query builder
service/  FastAPI app
data/     testcases, lexicon/place/nickname data (contact lists are gitignored)
tests/    unit + benchmark regression gate
```

## Acknowledgments

This project stands on excellent open work:

- **[phonikud](https://github.com/thewh1teagle/phonikud)** (CC BY 4.0) &
  **[phonikud-onnx model](https://huggingface.co/thewh1teagle/phonikud-onnx)**
  (MIT) by thewh1teagle — Hebrew niqqud prediction + grapheme-to-phoneme.
  ([paper / demo](https://thewh1teagle.github.io/phonikud-paper/))
- **[panphon](https://github.com/dmort27/panphon)** (MIT, Mortensen et al.) —
  articulatory feature vectors for IPA segments.
- **[espeak-ng](https://github.com/espeak-ng/espeak-ng)** (GPL-3.0) —
  multilingual G2P/IPA, invoked as a **separate process** (not linked).
- **[PHOIBLE](https://phoible.org/)** — phonological inventory data that
  informed the Hebrew↔English equivalence classes (referenced, not copied).
- **[num2words](https://github.com/savoirfairelinux/num2words)** (LGPL-2.1) and
  **[jellyfish](https://github.com/jamesturk/jellyfish)** (MIT).

## License

name-phonetics is **MIT** — see [LICENSE](LICENSE). Dependencies carry their own
licenses; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the full
breakdown (notably espeak-ng is GPL-3.0, used as a separate process).
