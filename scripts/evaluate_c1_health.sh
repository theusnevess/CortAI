#!/usr/bin/env bash
set -euo pipefail

# Avalia C1 health a partir de CSV(s) do run_p2_matrix.sh e retorna:
# - JSON em stdout
# - exit 1 se score final for FAIL, exit 0 caso PASS/WARN
#
# Uso:
#   scripts/evaluate_c1_health.sh --csv direct=.tmp_p2/p2_a_summary_direct.csv [--csv edge=.tmp_p2/p2_a_summary_edge.csv]

P99_WARN_OVERVIEW_MS="${P99_WARN_OVERVIEW_MS:-1500}"
P99_WARN_RUNS_MS="${P99_WARN_RUNS_MS:-1500}"
P99_WARN_REPORT_MS="${P99_WARN_REPORT_MS:-1500}"
P99_FAIL_OVERVIEW_MS="${P99_FAIL_OVERVIEW_MS:-2500}"
P99_FAIL_RUNS_MS="${P99_FAIL_RUNS_MS:-2500}"
P99_FAIL_REPORT_MS="${P99_FAIL_REPORT_MS:-2500}"
PCT5XX_FAIL="${PCT5XX_FAIL:-1}"

declare -a CSV_SPECS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --csv)
      CSV_SPECS+=("${2:-}")
      shift 2
      ;;
    *)
      echo "argumento inesperado: $1" >&2
      echo "uso: $0 --csv <path_label=arquivo.csv> [--csv ...]" >&2
      exit 2
      ;;
  esac
done

if [[ ${#CSV_SPECS[@]} -eq 0 ]]; then
  echo "uso: $0 --csv <path_label=arquivo.csv> [--csv ...]" >&2
  exit 2
fi

tmp_rows="$(mktemp)"
trap 'rm -f "$tmp_rows"' EXIT

append_rows_from_csv() {
  local spec="$1"
  local path_label="${spec%%=*}"
  local csv="${spec#*=}"

  if [[ -z "$path_label" || -z "$csv" || "$path_label" == "$csv" ]]; then
    echo "spec invalida (--csv): $spec (esperado path=arquivo)" >&2
    return 1
  fi
  if [[ ! -s "$csv" ]]; then
    echo "CSV ausente/vazio: $csv" >&2
    return 1
  fi

  awk -F',' -v path_label="$path_label" \
    -v p99_warn_overview="$P99_WARN_OVERVIEW_MS" \
    -v p99_warn_runs="$P99_WARN_RUNS_MS" \
    -v p99_warn_report="$P99_WARN_REPORT_MS" \
    -v p99_fail_overview="$P99_FAIL_OVERVIEW_MS" \
    -v p99_fail_runs="$P99_FAIL_RUNS_MS" \
    -v p99_fail_report="$P99_FAIL_REPORT_MS" \
    -v pct5xx_fail="$PCT5XX_FAIL" '
    function to_num(v, fallback) {
      if (v == "" || v == "NA") return fallback;
      return v + 0;
    }
    function warn_p99_for(endpoint) {
      if (endpoint == "overview") return p99_warn_overview + 0;
      if (endpoint == "runs") return p99_warn_runs + 0;
      if (endpoint == "report") return p99_warn_report + 0;
      return 1500;
    }
    function fail_p99_for(endpoint) {
      if (endpoint == "overview") return p99_fail_overview + 0;
      if (endpoint == "runs") return p99_fail_runs + 0;
      if (endpoint == "report") return p99_fail_report + 0;
      return 2500;
    }
    NR == 1 { next } # header
    {
      endpoint=$1; c=$2; p90=$3; p99=$4; rps=$5; timeouts=$6; pct429=$7; pct503=$8; pct5xx=$9;
      if (endpoint == "" || c != "1") next;

      rps_num=to_num(rps, 0);
      timeouts_num=to_num(timeouts, 999999);
      p99_num=to_num(p99, 999999);
      pct429_num=to_num(pct429, 0);
      pct503_num=to_num(pct503, 0);
      pct5xx_num=to_num(pct5xx, 999999);
      warn_p99=warn_p99_for(endpoint);
      fail_p99=fail_p99_for(endpoint);

      decision="PASS";
      reason="";
      if (timeouts_num > 0) {
        decision="FAIL"; reason="timeouts>0";
      } else if (rps_num < 1) {
        decision="FAIL"; reason="rps<1";
      } else if (pct5xx_num >= pct5xx_fail) {
        decision="FAIL"; reason="pct_5xx>=limit";
      } else if (p99_num > fail_p99) {
        decision="FAIL"; reason="p99>fail_limit";
      } else if (p99_num > warn_p99) {
        decision="WARN"; reason="p99>warn_limit";
      } else if (pct429_num > 0) {
        decision="WARN"; reason="pct_429>0";
      } else if (pct503_num > 0) {
        decision="WARN"; reason="pct_503>0";
      }

      printf("%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n",
        path_label, endpoint, p99, rps, timeouts, pct429, pct503, pct5xx,
        decision, reason, c);
    }
  ' "$csv" >> "$tmp_rows"
}

for spec in "${CSV_SPECS[@]}"; do
  append_rows_from_csv "$spec"
done

if [[ ! -s "$tmp_rows" ]]; then
  echo '{"c1_health":"FAIL","reason":"no_c1_rows","rows":[]}' 
  exit 1
fi

final_score="PASS"
if grep -q ',FAIL,' "$tmp_rows"; then
  final_score="FAIL"
elif grep -q ',WARN,' "$tmp_rows"; then
  final_score="WARN"
fi

json_escape() {
  local s="$1"
  s="${s//\\/\\\\}"
  s="${s//\"/\\\"}"
  s="${s//$'\n'/ }"
  printf '%s' "$s"
}

{
  printf '{'
  printf '"c1_health":"%s",' "$final_score"
  printf '"thresholds":{'
  printf '"p99_warn_ms":{"overview":%s,"runs":%s,"report":%s},' "$P99_WARN_OVERVIEW_MS" "$P99_WARN_RUNS_MS" "$P99_WARN_REPORT_MS"
  printf '"p99_fail_ms":{"overview":%s,"runs":%s,"report":%s},' "$P99_FAIL_OVERVIEW_MS" "$P99_FAIL_RUNS_MS" "$P99_FAIL_REPORT_MS"
  printf '"pct_5xx_fail":%s' "$PCT5XX_FAIL"
  printf '},'
  printf '"rows":['
  first=1
  while IFS=',' read -r path endpoint p99 rps timeouts pct429 pct503 pct5xx decision reason c; do
    [[ -z "$path" ]] && continue
    if [[ "$first" -eq 0 ]]; then printf ','; fi
    first=0
    printf '{'
    printf '"path":"%s",' "$(json_escape "$path")"
    printf '"endpoint":"%s",' "$(json_escape "$endpoint")"
    printf '"c":%s,' "$(json_escape "$c")"
    printf '"p99_ms":"%s",' "$(json_escape "$p99")"
    printf '"rps":"%s",' "$(json_escape "$rps")"
    printf '"timeouts":"%s",' "$(json_escape "$timeouts")"
    printf '"pct_429":"%s",' "$(json_escape "$pct429")"
    printf '"pct_503":"%s",' "$(json_escape "$pct503")"
    printf '"pct_5xx":"%s",' "$(json_escape "$pct5xx")"
    printf '"decision":"%s",' "$(json_escape "$decision")"
    printf '"reason":"%s"' "$(json_escape "$reason")"
    printf '}'
  done < "$tmp_rows"
  printf ']'
  printf '}'
  printf '\n'
}

if [[ "$final_score" == "FAIL" ]]; then
  exit 1
fi

