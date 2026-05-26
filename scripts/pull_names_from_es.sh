#!/usr/bin/env bash
# Pull distinct names from an Elasticsearch index into a newline-delimited file
# for cluster.py. If your ES is not exposed locally, open a tunnel first:
#
#   ssh -N -L 9200:localhost:9200 <user>@<your-es-host>     # in another terminal
#   ELASTICSEARCH_URL=http://localhost:9200 ./scripts/pull_names_from_es.sh > data/names.txt
#   python cluster.py data/names.txt --persons-only
#
# Configure via env:
#   ELASTICSEARCH_URL   default http://localhost:9200
#   INDEX_PATTERN       default name_*        (indices to scan)
#   NAME_FIELD          default name          (text field; uses <field>.keyword)
set -euo pipefail

ES="${ELASTICSEARCH_URL:-http://localhost:9200}"
PATTERN="${INDEX_PATTERN:-name_*}"
FIELD="${NAME_FIELD:-name}"
SUB="${NAME_FIELD_KEYWORD:-keyword}"   # set to "kw" if your mapping uses .kw

indices="$(curl -s "$ES/_cat/indices/${PATTERN}?h=index" | tr -d ' ')"
[ -z "$indices" ] && { echo "no indices matching '${PATTERN}' at $ES" >&2; exit 1; }

for idx in $indices; do
  after=""
  while :; do
    body="$(cat <<JSON
{"size":0,"aggs":{"names":{"composite":{"size":1000,
  "sources":[{"n":{"terms":{"field":"${FIELD}.${SUB}"}}}]
  ${after:+,"after":${after}}}}}}
JSON
)"
    resp="$(curl -s -H 'Content-Type: application/json' "$ES/$idx/_search" -d "$body")"
    echo "$resp" | python3 -c '
import sys,json
d=json.load(sys.stdin)
b=d.get("aggregations",{}).get("names",{})
for k in b.get("buckets",[]):
    v=k["key"].get("n")
    if v: print(v)
ak=b.get("after_key")
sys.stderr.write(json.dumps(ak) if ak else "")
' 2> /tmp/.after_key
    after="$(cat /tmp/.after_key)"
    [ -z "$after" ] && break
  done
done | sort -u
