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
STATUS_REQUESTS="${STATUS_REQUESTS:-200}"
STATUS_TIMEOUT="${STATUS_TIMEOUT:-20}"

ENDPOINTS=(
  "/api/v1/metrics/overview?days=7"
  "/api/v1/metrics/runs?start_date=2026-02-13&end_date=2026-02-20&limit=200&offset=0"
  "/api/v1/observability/report?window_days=7&timing_minutes=15"
)

mkdir -p "$OUTDIR"
SUMMARY="$OUTDIR/p2_a_summary.csv"
echo "endpoint,C,p90,p99,req_per_sec,timeouts,pct_429,pct_503,pct_5xx" > "$SUMMARY"

to_milliseconds() {
  local raw="${1:-}"
  if [[ -z "$raw" || "$raw" == "NA" ]]; then
    echo "NA"
    return
  fi
  awk -v v="$raw" '
    BEGIN {
      if (v ~ /ms$/) {
        gsub(/ms$/, "", v);
        printf("%.2f\n", v + 0.0);
        exit;
      }
      if (v ~ /us$/) {
        gsub(/us$/, "", v);
        printf("%.2f\n", (v + 0.0) / 1000.0);
        exit;
      }
      if (v ~ /s$/) {
        gsub(/s$/, "", v);
        printf("%.2f\n", (v + 0.0) * 1000.0);
        exit;
      }
      printf("NA\n");
    }
  '
}

mean_or_na() {
  local values="${1:-}"
  if [[ -z "$values" ]]; then
    echo "NA"
    return
  fi
  awk '
    {
      for (i = 1; i <= NF; i++) {
        if ($i != "NA") {
          sum += $i;
          count += 1;
        }
      }
    }
    END {
      if (count == 0) {
        print "NA";
      } else {
        printf("%.2f\n", sum / count);
      }
    }
  ' <<< "$values"
}

run_status_probe() {
  local url="$1"
  local concurrency="$2"
  local out="$3"

  if command -v hey >/dev/null 2>&1; then
    hey -n "$STATUS_REQUESTS" -c "$concurrency" -t "$STATUS_TIMEOUT" "$url" > "$out" 2>&1 || true
    return
  fi

  local statuses
  statuses="$(mktemp)"
  local i=0
  while [[ "$i" -lt "$STATUS_REQUESTS" ]]; do
    curl -sS --max-time "$STATUS_TIMEOUT" -o /dev/null -w "%{http_code}\n" "$url" >> "$statuses" || echo "000" >> "$statuses"
    i=$((i + 1))
  done
  {
    echo "Status code distribution:"
    awk '
      { counts[$1] += 1; total += 1 }
      END {
        for (code in counts) {
          printf("  [%s] %d responses\n", code, counts[code]);
        }
      }
    ' "$statuses"
  } > "$out"
  rm -f "$statuses"
}

parse_hey_status() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    echo "NA,NA,NA"
    return
  fi
  awk '
    BEGIN {
      total = 0;
      c429 = 0;
      c503 = 0;
      c5xx = 0;
    }
    /^\s*\[[0-9][0-9][0-9]\][[:space:]]+[0-9]+[[:space:]]+responses/ {
      code = $1;
      gsub(/\[/, "", code);
      gsub(/\]/, "", code);
      count = $2 + 0;
      total += count;
      if (code == 429) c429 += count;
      if (code == 503) c503 += count;
      if (code >= 500 && code < 600) c5xx += count;
    }
    END {
      if (total == 0) {
        print "NA,NA,NA";
      } else {
        printf("%.2f,%.2f,%.2f\n", (100.0 * c429) / total, (100.0 * c503) / total, (100.0 * c5xx) / total);
      }
    }
  ' "$file"
}

for ep in "${ENDPOINTS[@]}"; do
  name="$(echo "$ep" | cut -d'?' -f1 | awk -F'/' '{print $NF}')"
  for c in $CONCURRENCY_LIST; do
    p90_values=""
    p99_values=""
    rps_values=""
    timeout_sum=0

    for rep in $(seq 1 "$REPS"); do
      raw="$OUTDIR/wrk_${name}_c${c}_r${rep}.txt"
      wrk -t"$THREADS" -c"$c" -d"$DURATION" --timeout "$TIMEOUT" --latency "${BASE_URL}${ep}" > "$raw" 2>&1 || true

      p90="$(grep -E '^\s*90(\.000)?%' "$raw" | awk '{print $2}' | tail -n1 || true)"
      p99="$(grep -E '^\s*99(\.000)?%' "$raw" | awk '{print $2}' | tail -n1 || true)"
      rps="$(grep -E 'Requests/sec:' "$raw" | awk '{print $2}' | tail -n1 || true)"
      timeouts="$(grep -Eo 'timeout [0-9]+' "$raw" | awk '{sum+=$2} END {print sum+0}' || true)"

      p90_ms="$(to_milliseconds "${p90:-NA}")"
      p99_ms="$(to_milliseconds "${p99:-NA}")"
      p90_values="${p90_values} ${p90_ms}"
      p99_values="${p99_values} ${p99_ms}"
      rps_values="${rps_values} ${rps:-0}"
      timeout_sum=$((timeout_sum + ${timeouts:-0}))
    done

    p90_avg="$(mean_or_na "$p90_values")"
    p99_avg="$(mean_or_na "$p99_values")"
    rps_avg="$(mean_or_na "$rps_values")"

    status_file="$OUTDIR/status_${name}_c${c}.txt"
    run_status_probe "${BASE_URL}${ep}" "$c" "$status_file"
    IFS=',' read -r pct429 pct503 pct5xx <<< "$(parse_hey_status "$status_file")"

    echo "${name},${c},${p90_avg},${p99_avg},${rps_avg},${timeout_sum},${pct429},${pct503},${pct5xx}" >> "$SUMMARY"
  done
done

echo "wrote: $SUMMARY"
