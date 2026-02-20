#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-}"
if [[ -z "${BASE_URL}" ]]; then
  echo "uso: $0 <base_url>"
  exit 1
fi

OUTDIR="${OUTDIR:-.tmp_p2}"
DURATION="${DURATION:-60s}"
TIMEOUT="${TIMEOUT:-10s}"
THREADS="${THREADS:-2}"
CONCURRENCY_LIST="${CONCURRENCY_LIST:-1 2 5}"
REPS="${REPS:-3}"

ENDPOINTS=(
  "/api/v1/metrics/overview?days=7"
  "/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=200&offset=0"
  "/api/v1/observability/report?window_days=7&timing_minutes=15"
)

mkdir -p "$OUTDIR"
SUMMARY="$OUTDIR/p2_a_summary.csv"
echo "endpoint,C,rep,p90,p99,req_per_sec,timeouts" > "$SUMMARY"

for ep in "${ENDPOINTS[@]}"; do
  name="$(echo "$ep" | cut -d'?' -f1 | awk -F'/' '{print $NF}')"
  for c in $CONCURRENCY_LIST; do
    for rep in $(seq 1 "$REPS"); do
      raw="$OUTDIR/wrk_${name}_c${c}_r${rep}.txt"
      wrk -t"$THREADS" -c"$c" -d"$DURATION" --timeout "$TIMEOUT" --latency "${BASE_URL}${ep}" > "$raw" 2>&1 || true

      p90="$(grep -E '^\s*90(\.000)?%' "$raw" | awk '{print $2}' | tail -n1)"
      p99="$(grep -E '^\s*99(\.000)?%' "$raw" | awk '{print $2}' | tail -n1)"
      rps="$(grep -E 'Requests/sec:' "$raw" | awk '{print $2}' | tail -n1)"
      timeouts="$(grep -Eo 'timeout [0-9]+' "$raw" | awk '{sum+=$2} END {print sum+0}')"

      echo "${name},${c},${rep},${p90:-NA},${p99:-NA},${rps:-0},${timeouts:-0}" >> "$SUMMARY"
    done
  done
done

echo "wrote: $SUMMARY"
