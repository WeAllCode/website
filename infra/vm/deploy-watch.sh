#!/usr/bin/env bash
# Instant-deploy trigger. Runs as root from wac-deploy-watch.service. Installed to
# /usr/local/sbin/wac-deploy-watch.
#
# release.sh sets the instance metadata key deploy-nonce-<target> to "<sha>:<time>" after it
# writes the pointer. This loop long-polls the metadata server (wait_for_change + last_etag)
# and, when a nonce differs from the last one seen, starts wac-deploy@<target>.service with
# --no-block. wac-deploy@<target>.timer stays as the 15-minute fallback.
#
# - Last-seen nonces live in $STATE_DIR/nonce-<target>. With no state file (first start) the
#   current value is recorded without firing; with one, any difference fires, so a release
#   made while the watcher was down still deploys.
# - wac-deploy@ is a oneshot: `systemctl start` while it is already running merges into that
#   run instead of queueing another. So a nonce change while the target's unit is active or
#   activating is kept pending and fired once the unit is inactive.
# - The recursive attributes body holds secrets (wac-origin-key). It stays in a 0700 runtime
#   dir and only the two nonce values are read from it. Never `set -x` here.
#
# Metadata is reached with curl and Metadata-Flavor: Google over IPv6, like deploy-pull.sh.
set -uo pipefail

MD=${WAC_WATCH_MD:-http://metadata.google.internal/computeMetadata/v1}
STATE_DIR=${WAC_WATCH_STATE_DIR:-/var/lib/wac-deploy-watch}
RUN_DIR=${WAC_WATCH_RUN_DIR:-${RUNTIME_DIRECTORY:-/run/wac-deploy-watch}}
SYSTEMCTL=${WAC_WATCH_SYSTEMCTL:-systemctl}
WAIT_SEC=${WAC_WATCH_WAIT_SEC:-300}      # long-poll timeout_sec
PENDING_SEC=${WAC_WATCH_PENDING_SEC:-15} # timeout_sec while a fire is pending
MAX_BACKOFF=${WAC_WATCH_MAX_BACKOFF:-60}
TARGETS=(prod staging)

log() { echo "wac-deploy-watch: $*"; }

umask 077
mkdir -p "$STATE_DIR" "$RUN_DIR"
body=$RUN_DIR/attributes.json

declare -A pending=()

unit_busy() { # TARGET -> 0 when wac-deploy@TARGET is running or starting
	local s
	s=$("$SYSTEMCTL" is-active "wac-deploy@$1.service" 2>/dev/null) || true
	[ "$s" = active ] || [ "$s" = activating ] || [ "$s" = reloading ]
}

fire() { # TARGET
	if unit_busy "$1"; then
		[ -n "${pending[$1]:-}" ] || log "wac-deploy@$1 is already running; starting it again when it finishes"
		pending[$1]=1
		return
	fi
	if "$SYSTEMCTL" start --no-block "wac-deploy@$1.service"; then
		log "started wac-deploy@$1.service"
		unset 'pending[$1]'
	else
		log "systemctl start wac-deploy@$1.service failed; retrying on the next loop"
		pending[$1]=1
	fi
}

save_nonce() { # TARGET VALUE
	printf '%s\n' "$2" >"$STATE_DIR/nonce-$1.tmp" && mv -f "$STATE_DIR/nonce-$1.tmp" "$STATE_DIR/nonce-$1"
}

# check BODYFILE: compare each target's nonce with the saved one
check() {
	local t cur last
	for t in "${TARGETS[@]}"; do
		cur=$(jq -r --arg k "deploy-nonce-$t" '.[$k] // "" | tostring' "$1") || return 1
		if [ ! -f "$STATE_DIR/nonce-$t" ]; then
			save_nonce "$t" "$cur"
			log "first start: recorded $t nonce '${cur:-none}' without deploying"
			continue
		fi
		last=$(cat "$STATE_DIR/nonce-$t")
		[ "$cur" = "$last" ] && continue
		save_nonce "$t" "$cur"
		if [ -n "$cur" ]; then
			log "$t nonce changed '${last:-none}' -> '$cur'"
			fire "$t"
		fi
	done
}

etag=""
backoff=2
while true; do
	# Retry pending fires whose unit has finished.
	for t in "${!pending[@]}"; do
		fire "$t"
	done

	wait=$WAIT_SEC
	[ "${#pending[@]}" -gt 0 ] && wait=$PENDING_SEC
	url="$MD/instance/attributes/?recursive=true"
	# The first request (and the first after an error) returns at once with the current
	# values and their etag; later ones block until the attributes change or `wait` passes.
	[ -n "$etag" ] && url="$url&wait_for_change=true&last_etag=$etag&timeout_sec=$wait"

	out=$(curl -sS -o "$body" -w '%{http_code} %header{etag}' --max-time $((wait + 30)) \
		-H 'Metadata-Flavor: Google' "$url")
	rc=$?
	code=${out%% *}
	new_etag=$(printf '%s' "${out#* }" | tr -d '\r\n"[:space:]')

	if [ "$rc" -ne 0 ] || [ "$code" != 200 ] || [ -z "$new_etag" ]; then
		log "metadata request failed (curl rc=$rc, HTTP ${code:-none}); retrying in ${backoff}s"
		rm -f "$body"
		etag=""
		sleep "$backoff"
		backoff=$((backoff * 2 > MAX_BACKOFF ? MAX_BACKOFF : backoff * 2))
		continue
	fi
	backoff=2

	if ! check "$body"; then
		log "could not parse the metadata attributes; retrying in 5s"
		etag=""
		rm -f "$body"
		sleep 5
		continue
	fi
	rm -f "$body"
	etag=$new_etag
done
