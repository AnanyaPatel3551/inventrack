#!/usr/bin/env bash
# Sends parallel requests to the InvenTrack API to generate traffic for Grafana and CPU load for the HPA.
#
# Usage:
#   ./scripts/load-test.sh
#   TOTAL=5000 CONCURRENCY=50 ./scripts/load-test.sh
#   URL=http://localhost:8000/api/products ./scripts/load-test.sh
#
# Watch the effect in another terminal:
#   kubectl get hpa -n inventrack -w
set -euo pipefail

URL="${URL:-http://inventrack.local/api/products}"
TOTAL="${TOTAL:-2000}"
CONCURRENCY="${CONCURRENCY:-20}"
TIMEOUT="${TIMEOUT:-10}"

if ! command -v curl >/dev/null 2>&1; then
  echo "curl is required" >&2
  exit 1
fi

echo "Target:      $URL"
echo "Requests:    $TOTAL"
echo "Concurrency: $CONCURRENCY"
echo

start=$(date +%s)

# xargs -P keeps CONCURRENCY curl processes running at once.
# Each curl prints only its HTTP status code (000 means the connection failed).
results=$(seq 1 "$TOTAL" | xargs -P "$CONCURRENCY" -I{} \
  curl -s -o /dev/null -w "%{http_code}\n" --max-time "$TIMEOUT" "$URL" || true)

end=$(date +%s)
elapsed=$(( end - start ))
[ "$elapsed" -eq 0 ] && elapsed=1

echo "Status codes:"
# tr strips the \r that curl adds on Windows (Git Bash), so identical codes group together
echo "$results" | tr -d '\r' | grep -v '^$' | sort | uniq -c | sort -rn | awk '{printf "  %s  x %s\n", $2, $1}'
echo
echo "Finished $TOTAL requests in ${elapsed}s (~$(( TOTAL / elapsed )) req/s)"
