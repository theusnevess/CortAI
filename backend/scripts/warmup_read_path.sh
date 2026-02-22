#!/usr/bin/env bash
set -euo pipefail

# Warm-up read-path snapshots from inside cortai_api container.

BASE_URL="${BASE_URL:-http://localhost:8000}"
JOB_LIMIT="${JOB_LIMIT:-100}"
TIMEOUT_TOTAL="${TIMEOUT_TOTAL:-60}"
MAX_GET_RETRIES="${MAX_GET_RETRIES:-3}"
BACKOFF_SECONDS="${BACKOFF_SECONDS:-2}"

DAYS="${DAYS:-7}"
RUNS_LIMIT="${RUNS_LIMIT:-200}"
RUNS_OFFSET="${RUNS_OFFSET:-0}"

_today_utc() {
  python - <<'PY'
from datetime import datetime, timezone
print(datetime.now(timezone.utc).date().isoformat())
PY
}

_days_ago_utc() {
  python - "$1" <<'PY'
from datetime import datetime, timezone, timedelta
import sys
days = int(sys.argv[1])
print((datetime.now(timezone.utc).date() - timedelta(days=days)).isoformat())
PY
}

if [[ -z "${RUNS_END_DATE:-}" ]]; then
  RUNS_END_DATE="$(_today_utc)"
fi
if [[ -z "${RUNS_START_DATE:-}" ]]; then
  RUNS_START_DATE="$(_days_ago_utc $(( DAYS - 1 )))"
fi

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT
deadline_epoch=$(( $(date +%s) + TIMEOUT_TOTAL ))

http_json() {
  local url="$1"
  local body_file="$2"
  if command -v curl >/dev/null 2>&1; then
    local code
    code="$(curl -sS --max-time 20 -o "$body_file" -w '%{http_code}' "$url" || true)"
    echo "$code"
    return
  fi
  python - "$url" "$body_file" <<'PY'
import sys, urllib.request, urllib.error
url, body_file = sys.argv[1], sys.argv[2]
try:
    with urllib.request.urlopen(url, timeout=20) as resp:
        body = resp.read()
        open(body_file, "wb").write(body)
        print(resp.getcode())
except urllib.error.HTTPError as exc:
    body = exc.read()
    open(body_file, "wb").write(body)
    print(exc.code)
except Exception:
    open(body_file, "wb").write(b"")
    print("")
PY
}

require_code() {
  local got="$1"
  local expected="$2"
  local label="$3"
  if [[ "$got" != "$expected" ]]; then
    echo "ERROR: ${label} expected HTTP ${expected}, got ${got}" >&2
    return 1
  fi
}

print_status_summary() {
  local status_file="$1"
  python - "$status_file" <<'PY'
import json, sys
path = sys.argv[1]
try:
    data = json.load(open(path, "r", encoding="utf-8"))
except Exception as exc:
    print(f"status_parse_error={exc}")
    sys.exit(0)
rp = data.get("read_path", {}) or {}
print(
    " ".join(
        [
            f"overview_snapshot_status={rp.get('overview_snapshot_status')}",
            f"overview_freshness_seconds={rp.get('overview_freshness_seconds')}",
            f"runs_snapshot_status={rp.get('runs_snapshot_status')}",
            f"runs_freshness_seconds={rp.get('runs_freshness_seconds')}",
            f"jobs_queued_count={rp.get('jobs_queued_count')}",
        ]
    )
)
PY
}

overview_live_url="${BASE_URL}/api/v1/metrics/overview?days=${DAYS}&force_live=true"
overview_get_url="${BASE_URL}/api/v1/metrics/overview?days=${DAYS}"
runs_query="start_date=${RUNS_START_DATE}&end_date=${RUNS_END_DATE}&limit=${RUNS_LIMIT}&offset=${RUNS_OFFSET}"
runs_live_url="${BASE_URL}/api/v1/metrics/runs?${runs_query}&force_live=true"
runs_get_url="${BASE_URL}/api/v1/metrics/runs?${runs_query}"
status_url="${BASE_URL}/api/v1/status?window_days=1"

echo "warmup_read_path(container): base_url=${BASE_URL} days=${DAYS} runs_start=${RUNS_START_DATE} runs_end=${RUNS_END_DATE} job_limit=${JOB_LIMIT}"

code="$(http_json "$overview_live_url" "$tmpdir/overview_force_live.json")"
require_code "$code" "202" "overview force_live"
echo "overview_force_live=202"

code="$(http_json "$runs_live_url" "$tmpdir/runs_force_live.json")"
require_code "$code" "202" "runs force_live"
echo "runs_force_live=202"

echo "running refresh jobs..."
python scripts/run_read_refresh_jobs.py --limit "${JOB_LIMIT}"

overview_code="000"
runs_code="000"
attempt=1
while [[ "$attempt" -le "$MAX_GET_RETRIES" ]]; do
  if [[ $(date +%s) -ge "$deadline_epoch" ]]; then
    echo "ERROR: warm-up timeout (${TIMEOUT_TOTAL}s)" >&2
    break
  fi

  overview_code="$(http_json "$overview_get_url" "$tmpdir/overview_get.json")"
  runs_code="$(http_json "$runs_get_url" "$tmpdir/runs_get.json")"

  if [[ "$overview_code" == "200" && "$runs_code" == "200" ]]; then
    break
  fi

  if [[ "$attempt" -lt "$MAX_GET_RETRIES" ]]; then
    sleep "$BACKOFF_SECONDS"
  fi
  attempt=$((attempt + 1))
done

status_code="$(http_json "$status_url" "$tmpdir/status.json")"
echo "overview_get_http=${overview_code}"
echo "runs_get_http=${runs_code}"
echo "status_http=${status_code}"
if [[ "$status_code" == "200" ]]; then
  print_status_summary "$tmpdir/status.json"
fi

if [[ "$overview_code" != "200" || "$runs_code" != "200" ]]; then
  echo "ERROR: warm-up incomplete (overview=${overview_code} runs=${runs_code})" >&2
  exit 1
fi

echo "warmup_read_path: ok"
