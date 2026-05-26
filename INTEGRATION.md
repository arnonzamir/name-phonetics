# Integrating as an Elasticsearch sidecar

name-phonetics is Python (phonikud needs Python <3.13 + a 307 MB ONNX model +
the espeak-ng binary — not portable to `npm install`). The simplest integration
for a non-Python application is a **local sidecar service**: enrichment is an
**index-time** job (run once per contact), so a localhost HTTP call is cheap and
nothing leaves the host.

## Flow

```
your app  ──on new/updated name──▶  POST /enrich  ──▶  typed doc
   │                                                     │
   │                                                     ▼
   └────────────────────────────────────▶  Elasticsearch index (+ phonetic fields)

search:  query name ─▶ /enrich ─▶ build blocking query (es/query.py) ─▶ ES top-K
                                                               │
                                                        POST /score (re-rank)
```

## Steps

1. **Deploy the sidecar** — build the `Dockerfile`, expose `:8099`. Mount a
   volume at `/root/.cache/huggingface` so the 307 MB model persists across
   restarts. Health-gate on `/health` (model load takes a few seconds). Keep it
   on an internal network, not public.

2. **Index mapping** — apply the phonetic fields from `es/mapping.json`
   (`name_ipa`, `name_keys`, `org_ipa`, `roles`, `anchor_keys`, `context`, and
   the `ipa_tokens` analyzer). These are additive to whatever name fields your
   index already has.

3. **Enrich at ingest** — before writing a name document, POST the raw name to
   `/enrich` and merge the returned fields. Batch (`{"names":[...]}`) for bulk
   reindexes.

4. **Search = blocking + re-rank**
   - Enrich the query name (`/enrich`), build the ES query with the logic in
     `es/query.py` (`name_keys` term + `name_ipa` fuzzy + org/anchor/role). That
     JSON construction is ~30 lines and can be reimplemented in any language at
     search time.
   - Take ES top-K, call `/score` per candidate to re-rank, return sorted.

## Avoiding the sidecar (later)

The matching half (`engine/distance.py`, `match/`, `enrich/` logic) ports to
other languages cleanly — it's a DP over a bundled feature table plus string
logic. Only the **G2P** is sticky: `phonikud-onnx` can run via
`onnxruntime-node` / other ONNX runtimes, but phonikud's phonemizer rules and
espeak would need reimplementing. Defer unless the sidecar is operationally
annoying.

## Operational notes

- **System dep**: espeak-ng must be in the image (the Dockerfile installs it).
- **Python**: pinned `<3.13` (phonikud constraint).
- **Cold start**: first `/enrich` triggers the model download (or load from the
  mounted cache) — keep the container warm.
- **Throughput**: phonikud inference is the bottleneck (~tens of ms per Hebrew
  name, CPU). Fine for ingest; batch large backfills off the request path.

## Pulling a sample name list

`scripts/pull_names_from_es.sh` reads distinct names from an Elasticsearch index
into a newline-delimited file for `cluster.py`. Set `ELASTICSEARCH_URL`,
`INDEX_PATTERN`, and `NAME_FIELD` to match your deployment.
