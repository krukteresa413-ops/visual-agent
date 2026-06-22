#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1}"

html_headers="$(curl -sI "$BASE_URL/index.html" | tr -d '\r')"
if ! printf '%s\n' "$html_headers" | grep -qi '^Cache-Control: .*no-cache'; then
  echo "FAIL: index.html missing Cache-Control no-cache"
  printf '%s\n' "$html_headers" | grep -i '^Cache-Control:' || true
  exit 1
fi

index_html="$(curl -fsS "$BASE_URL/")"
mapfile -t bundles < <(printf '%s' "$index_html" | grep -oE 'assets/[^"<>]+\.(js|css)' | sort -u)

if [ "${#bundles[@]}" -eq 0 ]; then
  echo "FAIL: no js/css bundles referenced by index.html"
  exit 1
fi

for bundle in "${bundles[@]}"; do
  status="$(curl -s -o /dev/null -w '%{http_code}' "$BASE_URL/$bundle")"
  if [ "$status" != "200" ]; then
    echo "FAIL: $bundle returned HTTP $status"
    exit 1
  fi

  asset_headers="$(curl -sI "$BASE_URL/$bundle" | tr -d '\r')"
  if ! printf '%s\n' "$asset_headers" | grep -qi '^Cache-Control: .*max-age=31536000'; then
    echo "FAIL: $bundle missing one-year Cache-Control"
    printf '%s\n' "$asset_headers" | grep -i '^Cache-Control:' || true
    exit 1
  fi
  if ! printf '%s\n' "$asset_headers" | grep -qi '^Cache-Control: .*immutable'; then
    echo "FAIL: $bundle missing immutable Cache-Control"
    printf '%s\n' "$asset_headers" | grep -i '^Cache-Control:' || true
    exit 1
  fi

done

echo "PASS: index no-cache and ${#bundles[@]} hashed bundles are immutable"
