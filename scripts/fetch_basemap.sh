#!/usr/bin/env bash
# Downloads, once, the offline base map of each territory that declares a `basemap_pmtiles`
# source: an extract of the Protomaps daily build (OpenStreetMap data, ODbL), cut to the
# territory's extent with the go-pmtiles tool. Set REFRESH=1 to download again.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/tiles

BUILD=$(curl -sf https://build-metadata.protomaps.dev/builds.json \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)[-1]["key"])')

docker compose run --rm -T backend python -m app.ingestion basemaps </dev/null \
  | while read -r code maxzoom; do
    out="data/tiles/$code.pmtiles"
    if [ -f "$out" ] && [ -z "${REFRESH:-}" ]; then
      echo "✓ Fond de carte $code : déjà présent (REFRESH=1 make data pour le mettre à jour)."
      continue
    fi
    bbox=$(docker compose run --rm -T backend python -m app.ingestion bbox "$code" </dev/null)
    if [ -z "$bbox" ]; then
      echo "✗ Fond de carte $code : importez d'abord les limites."
      continue
    fi
    echo "… Fond de carte $code (emprise $bbox, zoom max $maxzoom) : téléchargement"
    docker run --rm -v "$PWD/data/tiles:/data" protomaps/go-pmtiles:latest extract \
      "https://build.protomaps.com/$BUILD" "/data/$code.pmtiles" \
      --bbox="$bbox" --maxzoom="$maxzoom" </dev/null
    printf '{"build": "%s", "bbox": "%s", "maxzoom": %s, "retrieved_at": "%s"}\n' \
      "$BUILD" "$bbox" "$maxzoom" "$(date -u +%FT%TZ)" >"data/tiles/$code.json"
    echo "✓ Fond de carte $code : $(du -h "$out" | cut -f1)"
  done
