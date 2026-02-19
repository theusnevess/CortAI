#!/usr/bin/env bash
set -euo pipefail

# P2-A throughput matrix runner (client-side).
# Intencao: medir variancia e latencia em runner separado do SUT sem tocar endpoint logic.

BASE_URL="${1:-http://localhost:8000}"
SUT_HOST="${SUT_HOST:-localhost:8000}"
RUNNER_ID="${RUNNER_ID:-$(hostname)}"
API_WORKERS="${API_WORKERS:-unknown}"

DURATION_SEC="${DURATION_SEC:-60}"
CONCURRENCY_VALUES="${CONCURRENCY_VALUES:-1 2 5}"
REPEATS="${REPEATS:-3}"
WARMUP_REQUESTS="${WARMUP_REQUESTS:-10}"
REQUEST_TIMEOUT_SEC="${REQUEST_TIMEOUT_SEC:-10}"

OUTDIR="${OUTDIR:-.tmp_p2}"
mkdir -p "$OUTDIR"

SUMMARY_CSV="$OUTDIR/p2_a_summary.csv"
echo "endpoint,C,repeat,p90_ms,p99_ms,rps,timeouts,runner,sut_host,api_workers" > "$SUMMARY_CSV"

OVERVIEW_PATH="/api/v1/metrics/overview?days=7"
RUNS_PATH="/api/v1/metrics/runs?start_date=2026-02-11&end_date=2026-02-18&limit=200&offset=0"
REPORT_PATH="/api/v1/observability/report?window_days=7&timing_minutes=15"

resolve_python_bin() {
  if command -v python3 >/dev/null 2>&1; then
    echo "python3"
    return
  fi
  if command -v python >/dev/null 2>&1; then
    echo "python"
    return
  fi
  echo "python3/python not found in PATH" >&2
  exit 1
}

PYTHON_BIN="$(resolve_python_bin)"

wait_for_api() {
  local ready=0
  local i
  for ((i = 0; i < 90; i++)); do
    if curl -fsS -m 3 "$BASE_URL/health" > /dev/null 2>&1; then
      ready=1
      break
    fi
    sleep 1
  done
  if [[ "$ready" -ne 1 ]]; then
    echo "API not ready at $BASE_URL" >&2
    exit 1
  fi
}

warmup() {
  local i
  for ((i = 0; i < WARMUP_REQUESTS; i++)); do
    curl -sS -m "$REQUEST_TIMEOUT_SEC" -o /dev/null "$BASE_URL$OVERVIEW_PATH" || true
    curl -sS -m "$REQUEST_TIMEOUT_SEC" -o /dev/null "$BASE_URL$RUNS_PATH" || true
    curl -sS -m "$REQUEST_TIMEOUT_SEC" -o /dev/null "$BASE_URL$REPORT_PATH" || true
  done
}

run_mix_worker() {
  local end_ts="$1"
  local outfile="$2"
  local idx=0
  while [[ "$(date +%s)" -lt "$end_ts" ]]; do
    local path
    case $((idx % 20)) in
      0|1|2|3|4|5|6|7|8|9|10|11) path="$RUNS_PATH" ;;
      12|13|14|15|16) path="$REPORT_PATH" ;;
      *) path="$OVERVIEW_PATH" ;;
    esac

    local payload
    local rc=0
    payload="$(curl -sS -m "$REQUEST_TIMEOUT_SEC" -o /dev/null -w "%{http_code},%{time_total}" "$BASE_URL$path")" || rc=$?
    if [[ "$rc" -eq 0 ]]; then
      printf "%s,%s,0\n" "$path" "$payload" >> "$outfile"
    else
      printf "%s,000,0.000000,1\n" "$path" >> "$outfile"
    fi
    idx=$((idx + 1))
  done
}

summarize_client_metrics() {
  local raw_file="$1"
  local out_file="$2"
  local duration_sec="$3"

  "$PYTHON_BIN" - "$raw_file" "$out_file" "$duration_sec" <<'PY'
import csv
import math
import sys
from collections import defaultdict

raw_file, out_file, duration_sec = sys.argv[1], sys.argv[2], int(sys.argv[3])

def pctl(values, p):
    if not values:
        return None
    values = sorted(values)
    k = (len(values) - 1) * p
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return values[int(k)]
    return values[f] * (c - k) + values[c] * (k - f)

latencies = defaultdict(list)
timeouts = defaultdict(int)
counts = defaultdict(int)

with open(raw_file, newline='', encoding='utf-8') as f:
    reader = csv.reader(f)
    for row in reader:
        if len(row) != 4:
            continue
        endpoint, code, tsec, timeout = row
        counts[endpoint] += 1
        if timeout == '1' or code == '000':
            timeouts[endpoint] += 1
            continue
        try:
            latencies[endpoint].append(float(tsec) * 1000.0)
        except ValueError:
            pass

with open(out_file, 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f)
    w.writerow(['endpoint','p90_ms','p99_ms','rps','timeouts'])
    for endpoint in [
        '/api/v1/metrics/overview?days=7',
        '/api/v1/metrics/runs?start_date=2026-02-11&end_date=2026-02-18&limit=200&offset=0',
        '/api/v1/observability/report?window_days=7&timing_minutes=15',
    ]:
        p90 = pctl(latencies[endpoint], 0.90)
        p99 = pctl(latencies[endpoint], 0.99)
        rps = counts[endpoint] / max(1, duration_sec)
        w.writerow([
            endpoint,
            '' if p90 is None else round(p90, 2),
            '' if p99 is None else round(p99, 2),
            round(rps, 4),
            int(timeouts[endpoint]),
        ])
PY
}

normalize_endpoint() {
  local ep="$1"
  if [[ "$ep" == /api/v1/metrics/overview* ]]; then
    echo "/api/v1/metrics/overview"
  elif [[ "$ep" == /api/v1/metrics/runs* ]]; then
    echo "/api/v1/metrics/runs"
  elif [[ "$ep" == /api/v1/observability/report* ]]; then
    echo "/api/v1/observability/report"
  else
    echo "$ep"
  fi
}

append_summary_rows() {
  local client_csv="$1"
  local c="$2"
  local repeat="$3"
  while IFS=',' read -r endpoint p90 p99 rps timeouts; do
    [[ "$endpoint" == "endpoint" ]] && continue
    endpoint="$(normalize_endpoint "$endpoint")"
    echo "$endpoint,$c,$repeat,$p90,$p99,$rps,$timeouts,$RUNNER_ID,$SUT_HOST,$API_WORKERS" >> "$SUMMARY_CSV"
  done < "$client_csv"
}

wait_for_api
warmup

for c in $CONCURRENCY_VALUES; do
  for r in $(seq 1 "$REPEATS"); do
    run_dir="$OUTDIR/c${c}_r${r}"
    mkdir -p "$run_dir"
    raw_file="$run_dir/load_raw.csv"
    : > "$raw_file"

    end_ts=$(( $(date +%s) + DURATION_SEC ))
    pids=()
    for ((i = 0; i < c; i++)); do
      run_mix_worker "$end_ts" "$raw_file" &
      pids+=("$!")
    done
    for pid in "${pids[@]}"; do
      wait "$pid"
    done

    client_csv="$run_dir/client_metrics.csv"
    summarize_client_metrics "$raw_file" "$client_csv" "$DURATION_SEC"
    append_summary_rows "$client_csv" "$c" "$r"
  done
done

echo "P2-A summary: $SUMMARY_CSV"
cat "$SUMMARY_CSV"
