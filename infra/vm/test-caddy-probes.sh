#!/usr/bin/env bash
# Local test for the (wac_probes) snippet in infra/vm/Caddyfile (docs/plans/scanner-defense.md, Task A).
# The real Caddyfile can't be validated off the VM (it needs /etc/caddy/origin.pem and the staging
# auth import), so this extracts the snippet between the "# BEGIN wac_probes" / "# END wac_probes"
# markers, serves it in front of a stub app on 127.0.0.1, and checks:
#   - every scanner fixture path gets 404 "Not Found" (at least 98% must, the rest fall through)
#   - every must-pass path reaches the app (body "app")
# Usage: bash infra/vm/test-caddy-probes.sh   (needs caddy and curl on PATH)
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
caddyfile="$repo_root/infra/vm/Caddyfile"
fixture="$repo_root/docs/plans/scanner-probe-paths-2026-11-25.txt"
must_pass="$repo_root/docs/plans/scanner-must-pass-paths.txt"
min_pct=98

command -v caddy >/dev/null || { echo "caddy not found on PATH" >&2; exit 2; }

tmp="$(mktemp -d)"
caddy_pid=""
# Inline rather than a function: shellcheck 0.11 misreports a trap-only function as unused (SC2329).
trap 'if [[ -n "$caddy_pid" ]]; then kill "$caddy_pid" 2>/dev/null || true; wait "$caddy_pid" 2>/dev/null || true; fi; rm -rf "$tmp"' EXIT

snippet="$(awk '/^# BEGIN wac_probes$/ {on=1; next} /^# END wac_probes$/ {on=0} on' "$caddyfile")"
if [[ -z "$snippet" ]]; then
	echo "no wac_probes snippet between the markers in $caddyfile" >&2
	exit 2
fi

port="$(python3 -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1", 0)); print(s.getsockname()[1]); s.close()')"
base="http://127.0.0.1:$port"

cat >"$tmp/Caddyfile" <<EOF
{
	admin off
}

$snippet

$base {
	import wac_probes
	respond "app" 200
}
EOF

caddy run --config "$tmp/Caddyfile" --adapter caddyfile >"$tmp/caddy.log" 2>&1 &
caddy_pid=$!

ready=0
for _ in $(seq 1 50); do
	if curl -s -o /dev/null "$base/"; then
		ready=1
		break
	fi
	if ! kill -0 "$caddy_pid" 2>/dev/null; then
		break
	fi
	sleep 0.1
done
if [[ "$ready" -ne 1 ]]; then
	echo "caddy did not start; log:" >&2
	cat "$tmp/caddy.log" >&2
	exit 2
fi

# Prints "<status> <body>" for a path.
fetch() {
	local code
	code="$(curl -g -s -o "$tmp/body" -w '%{http_code}' "$base$1")"
	printf '%s %s' "$code" "$(cat "$tmp/body")"
}

total=0
blocked=0
fell_through=()
other=()
while IFS= read -r path || [[ -n "$path" ]]; do
	[[ -z "$path" || "$path" == \#* ]] && continue
	total=$((total + 1))
	result="$(fetch "$path")"
	case "$result" in
	"404 Not Found") blocked=$((blocked + 1)) ;;
	"200 app") fell_through+=("$path") ;;
	*) other+=("$path -> $result") ;;
	esac
done <"$fixture"

mp_fail=()
mp_total=0
while IFS= read -r line || [[ -n "$line" ]]; do
	[[ -z "$line" || "$line" == \#* ]] && continue
	path="${line%% *}"
	mp_total=$((mp_total + 1))
	result="$(fetch "$path")"
	[[ "$result" == "200 app" ]] || mp_fail+=("$path -> $result")
done <"$must_pass"

echo "blocked $blocked/$total, fell through ${#fell_through[@]}"
for p in "${fell_through[@]+"${fell_through[@]}"}"; do echo "  fell through: $p"; done
for p in "${other[@]+"${other[@]}"}"; do echo "  unexpected: $p"; done
echo "must-pass reached the app: $((mp_total - ${#mp_fail[@]}))/$mp_total"
for p in "${mp_fail[@]+"${mp_fail[@]}"}"; do echo "  MUST-PASS BLOCKED: $p"; done

status=0
if [[ "$total" -eq 0 || $((blocked * 100)) -lt $((total * min_pct)) ]]; then
	echo "FAIL: fewer than $min_pct% of fixture paths blocked" >&2
	status=1
fi
if [[ "${#mp_fail[@]}" -gt 0 ]]; then
	echo "FAIL: ${#mp_fail[@]} must-pass path(s) did not reach the app" >&2
	status=1
fi
[[ "$status" -eq 0 ]] && echo "PASS"
exit "$status"
