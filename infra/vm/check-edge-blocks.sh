#!/usr/bin/env bash
# Edge check for the scanner defenses (docs/plans/scanner-defense.md, Task D; AC1, AC2, AC4).
# Requests every scanner fixture path through BASE_URL at about 4 req/s and tallies:
#   403 (Cloudflare WAF), Caddy 404 (body exactly "Not Found"), Django 404 (body over 10 KB), 200, other
# then requests every must-pass path and compares its status to the expected one (expected-404 paths
# must also return the full Django 404 page, body over 10 KB).
# Exits non-zero if any fixture path returns 200, more than 2% reach the Django 404, fewer than
# --min-edge % are 403, or any must-pass path differs.
# Usage: check-edge-blocks.sh [--min-edge N] [--must-pass-only] BASE_URL
#   --min-edge N       minimum % of fixture paths that must be 403 (default 90; Checkpoint 1 uses 0)
#   --must-pass-only   skip the fixture and only check the must-pass list
set -euo pipefail

usage() {
	echo "usage: $0 [--min-edge N] [--must-pass-only] BASE_URL" >&2
	exit 2
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
fixture="$repo_root/docs/plans/scanner-probe-paths-2026-11-25.txt"
must_pass="$repo_root/docs/plans/scanner-must-pass-paths.txt"
ua='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
min_edge=90
max_django_pct=2
django_min_bytes=10240
must_pass_only=0
base=""

while [[ $# -gt 0 ]]; do
	case "$1" in
	--min-edge)
		[[ $# -ge 2 && "$2" =~ ^[0-9]+$ ]] || usage
		min_edge="$2"
		shift 2
		;;
	--must-pass-only)
		must_pass_only=1
		shift
		;;
	-h | --help) usage ;;
	-*) usage ;;
	*)
		[[ -z "$base" ]] || usage
		base="${1%/}"
		shift
		;;
	esac
done
[[ -n "$base" ]] || usage

for f in "$fixture" "$must_pass"; do
	[[ -r "$f" ]] || { echo "missing $f" >&2; exit 2; }
done

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

# Sets code, size and body_is_not_found for a path. Redirects are not followed.
fetch() {
	local out
	out="$(curl -g -s -o "$tmp" --max-time 20 -A "$ua" -w '%{http_code} %{size_download}' "$base$1" || true)"
	code="${out%% *}"
	size="${out##* }"
	[[ -n "$code" ]] || code="000"
	[[ "$size" =~ ^[0-9]+$ ]] || size=0
	body_is_not_found=0
	if [[ "$size" -lt 100 && "$(cat "$tmp" 2>/dev/null || true)" == "Not Found" ]]; then
		body_is_not_found=1
	fi
}

pct() {
	awk -v n="$1" -v d="$2" 'BEGIN { if (d == 0) print "0.0"; else printf "%.1f", n * 100 / d }'
}

status=0
total=0
n403=0
caddy404=0
django404=0
n200=0
other=()
ok200=()

if [[ "$must_pass_only" -eq 0 ]]; then
	while IFS= read -r path || [[ -n "$path" ]]; do
		[[ -z "$path" || "$path" == \#* ]] && continue
		total=$((total + 1))
		fetch "$path"
		if [[ "$code" == "403" ]]; then
			n403=$((n403 + 1))
		elif [[ "$code" == "404" && "$body_is_not_found" -eq 1 ]]; then
			caddy404=$((caddy404 + 1))
		elif [[ "$code" == "404" && "$size" -gt "$django_min_bytes" ]]; then
			django404=$((django404 + 1))
		elif [[ "$code" == "200" ]]; then
			n200=$((n200 + 1))
			ok200+=("$path")
		else
			other+=("$path -> $code ($size bytes)")
		fi
		sleep 0.25
	done <"$fixture"

	echo "Fixture: $total paths via $base"
	printf '  %-12s %4d  %5s%%\n' "403" "$n403" "$(pct "$n403" "$total")"
	printf '  %-12s %4d  %5s%%\n' "Caddy 404" "$caddy404" "$(pct "$caddy404" "$total")"
	printf '  %-12s %4d  %5s%%\n' "Django 404" "$django404" "$(pct "$django404" "$total")"
	printf '  %-12s %4d  %5s%%\n' "200" "$n200" "$(pct "$n200" "$total")"
	printf '  %-12s %4d  %5s%%\n' "other" "${#other[@]}" "$(pct "${#other[@]}" "$total")"
	for p in "${ok200[@]+"${ok200[@]}"}"; do echo "    200: $p"; done
	for p in "${other[@]+"${other[@]}"}"; do echo "    other: $p"; done

	if [[ "$total" -eq 0 ]]; then
		echo "FAIL: no fixture paths read from $fixture" >&2
		status=1
	fi
	if [[ "$n200" -gt 0 ]]; then
		echo "FAIL: $n200 fixture path(s) returned 200" >&2
		status=1
	fi
	if [[ $((django404 * 100)) -gt $((total * max_django_pct)) ]]; then
		echo "FAIL: more than $max_django_pct% of fixture paths reached the Django 404" >&2
		status=1
	fi
	if [[ $((n403 * 100)) -lt $((total * min_edge)) ]]; then
		echo "FAIL: fewer than $min_edge% of fixture paths were 403 at the edge" >&2
		status=1
	fi
fi

mp_total=0
mp_fail=0
echo "Must-pass:"
while IFS= read -r line || [[ -n "$line" ]]; do
	[[ -z "$line" || "$line" == \#* ]] && continue
	path="${line%% *}"
	expected="${line##* }"
	mp_total=$((mp_total + 1))
	fetch "$path"
	if [[ "$code" != "$expected" ]]; then
		echo "  FAIL $path: got $code, expected $expected"
		mp_fail=$((mp_fail + 1))
	elif [[ "$expected" == "404" && "$size" -le "$django_min_bytes" ]]; then
		echo "  FAIL $path: 404 but body $size bytes, expected the full Django 404 (> $django_min_bytes)"
		mp_fail=$((mp_fail + 1))
	else
		echo "  pass $path $code ($size bytes)"
	fi
	sleep 0.25
done <"$must_pass"
echo "Must-pass: $((mp_total - mp_fail))/$mp_total"
if [[ "$mp_total" -eq 0 ]]; then
	echo "FAIL: no must-pass paths read from $must_pass" >&2
	status=1
fi
if [[ "$mp_fail" -gt 0 ]]; then
	echo "FAIL: $mp_fail must-pass path(s) differ" >&2
	status=1
fi

[[ "$status" -eq 0 ]] && echo "PASS"
exit "$status"
