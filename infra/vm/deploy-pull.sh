#!/usr/bin/env bash
# Pull-based deploy for one target (prod|staging). Runs as root on the VM from
# wac-deploy@<target>.service. Installed to /usr/local/sbin/wac-deploy-pull.
# That oneshot unit is started by its 15-minute timer and by wac-deploy-watch (instant deploys).
# systemd never runs two copies of one unit (a start while it runs merges into that run), and
# the flock below serializes prod and staging; the pointer is read only after the lock.
#
# 1. Read gs://<deploy-bucket>/current-<target>: "<sha>" or "<sha>:<nonce>" (release.sh --force).
# 2. Do nothing if it equals /srv/wac/<target>/deployed (whole-string compare, R7), or equals
#    /srv/wac/<target>/failed (a pointer that already failed is skipped until it changes, R16).
# 3. Download releases/<sha>.tar.gz, read the latest wac-env-<target> secret, uv sync,
#    migrate and collectstatic (as the target's user via wac-manage), then install the env,
#    (prod only) reinstall changed infra/vm files, flip `current`, restart the service.
# On any failure `current` and the env file stay as they were and the pointer goes to `failed`.
#
# GCS and Secret Manager are reached with curl and the metadata-server token over IPv6.
set -euo pipefail

MD=http://metadata.google.internal/computeMetadata/v1
UV=/usr/local/bin/uv
WAC_MANAGE=/usr/local/bin/wac-manage
KEEP_RELEASES=3

log() { echo "wac-deploy[${target:-?}]: $*"; }
die() {
	log "ERROR: $*" >&2
	exit 1
}

md_get() {
	curl -fsS --retry 5 --retry-connrefused --retry-delay 2 -H 'Metadata-Flavor: Google' "$MD/$1"
}

gcp_token() {
	md_get instance/service-accounts/default/token | jq -er .access_token
}

urlencode() {
	jq -rn --arg s "$1" '$s|@uri'
}

# gcs_fetch BUCKET OBJECT OUTFILE -> 0 ok, 3 not found, 1 other error
gcs_fetch() {
	local tok code
	tok=$(gcp_token) || return 1
	code=$(curl -sS --retry 3 -o "$3" -w '%{http_code}' \
		-H "Authorization: Bearer $tok" \
		"https://storage.googleapis.com/storage/v1/b/$1/o/$(urlencode "$2")?alt=media") || {
		rm -f "$3"
		return 1
	}
	case "$code" in
	200) return 0 ;;
	404)
		rm -f "$3"
		return 3
		;;
	*)
		log "GET gs://$1/$2 returned HTTP $code" >&2
		rm -f "$3"
		return 1
		;;
	esac
}

# secret_fetch NAME OUTFILE: latest version of a Secret Manager secret
secret_fetch() {
	local tok project
	tok=$(gcp_token)
	project=$(md_get project/project-id)
	curl -fsS --retry 3 -H "Authorization: Bearer $tok" \
		"https://secretmanager.googleapis.com/v1/projects/$project/secrets/$1/versions/latest:access" |
		jq -er .payload.data | base64 -d >"$2"
	[ -s "$2" ] || die "secret $1 is empty"
}

# env_value FILE KEY: last KEY=value in an env file, without sourcing it
env_value() {
	local v
	v=$(grep -E "^[[:space:]]*$2[[:space:]]*=" "$1" | tail -n 1 | cut -d= -f2-) || true
	v=${v#"${v%%[![:space:]]*}"}
	v=${v%"${v##*[![:space:]]}"}
	v=${v#[\"\']}
	v=${v%[\"\']}
	printf '%s' "$v"
}

target=${1:-}
case "$target" in
prod)
	app_user=wac
	service=wac-web
	;;
staging)
	app_user=wac-staging
	service=wac-staging
	;;
*)
	echo "usage: wac-deploy-pull <prod|staging>" >&2
	exit 64
	;;
esac

[ "$(id -u)" -eq 0 ] || die "must run as root"

base=/srv/wac/$target
env_file=/etc/wac/env-$target
uv_cache=/var/cache/wac-uv-$target
[ "$target" = prod ] && uv_cache=/var/cache/wac-uv

# One deploy at a time across both targets: two uv syncs at once would swap hard on 1 GB.
exec 9>/run/lock/wac-deploy.lock
flock 9

work=$(mktemp -d /var/tmp/wac-deploy.XXXXXX)
pointer=""
release_dir=""
committed=0

on_exit() {
	local rc=$?
	if [ "$rc" -ne 0 ] && [ -n "$pointer" ]; then
		printf '%s\n' "$pointer" >"$base/failed"
		log "deploy of '$pointer' FAILED (rc=$rc); recorded in $base/failed and skipped until the pointer changes"
		if [ "$committed" -eq 0 ] && [ -n "$release_dir" ] && [ -d "$release_dir" ]; then
			rm -rf -- "$release_dir"
		fi
	fi
	rm -f "$env_file.next"
	rm -rf -- "$work"
}
trap on_exit EXIT

bucket=$(md_get instance/attributes/wac-deploy-bucket) || die "metadata key wac-deploy-bucket missing"

rc=0
gcs_fetch "$bucket" "current-$target" "$work/pointer" || rc=$?
if [ "$rc" -eq 3 ]; then
	log "no gs://$bucket/current-$target yet; nothing to deploy"
	exit 0
elif [ "$rc" -ne 0 ]; then
	die "could not read gs://$bucket/current-$target"
fi
candidate=$(tr -d '[:space:]' <"$work/pointer")

if ! [[ "$candidate" =~ ^[0-9a-f]{40}(:[A-Za-z0-9._-]+)?$ ]]; then
	die "pointer '$candidate' is not <sha> or <sha>:<nonce>"
fi

deployed=$(cat "$base/deployed" 2>/dev/null || true)
failed=$(cat "$base/failed" 2>/dev/null || true)
if [ "$candidate" = "$deployed" ]; then
	exit 0
fi
if [ "$candidate" = "$failed" ]; then
	log "pointer '$candidate' failed before; skipping until it changes (rm $base/failed to retry)"
	exit 0
fi

pointer=$candidate
sha=${pointer%%:*}
log "deploying $pointer (was '${deployed:-none}')"

# --- Download and extract ----------------------------------------------------------------
gcs_fetch "$bucket" "releases/$sha.tar.gz" "$work/release.tar.gz" || die "could not download releases/$sha.tar.gz"

release_dir=$base/releases/$(date -u +%Y%m%dT%H%M%S)-${sha:0:12}
mkdir -p -- "$release_dir"
tar -xzf "$work/release.tar.gz" -C "$release_dir" --no-same-owner
if [ ! -f "$release_dir/manage.py" ] || [ ! -f "$release_dir/uv.lock" ]; then
	die "release has no manage.py/uv.lock"
fi
chown -R "$app_user:$app_user" "$release_dir"

# --- Secrets -------------------------------------------------------------------------------
secret_fetch "wac-env-$target" "$work/env"
if grep -qE '^[[:space:]]*DATABASE_URL[[:space:]]*=' "$work/env"; then
	die "wac-env-$target sets DATABASE_URL; the VM uses DB_* over the Unix socket (see README)"
fi
if [ "$target" = staging ]; then
	backend=$(env_value "$work/env" EMAIL_BACKEND)
	[ "$backend" = "django.core.mail.backends.console.EmailBackend" ] ||
		die "staging EMAIL_BACKEND must be django.core.mail.backends.console.EmailBackend (got '$backend')"
fi
install -o root -g "$app_user" -m 0640 "$work/env" "$env_file.next"

if [ "$target" = staging ]; then
	# Staging's own service account key (R10); the staging user cannot use the metadata server.
	secret_fetch wac-staging-sa-key "$work/sa.json"
	jq -e .client_email "$work/sa.json" >/dev/null || die "wac-staging-sa-key is not a service-account key"
	install -o root -g wac-staging -m 0640 "$work/sa.json" /etc/wac/staging-sa.json
	/usr/sbin/nft -f /etc/wac/nftables-wac.nft
fi

# --- Python --------------------------------------------------------------------------------
# .python-version picks the interpreter. 3.11 is Debian's /usr/bin/python3.11. Any other
# version is a uv-managed CPython that root installs into a per-target dir (R2): from cwd /,
# with a clean env and UV_NO_CONFIG, so nothing in the release (pyproject [tool.uv], uv.toml)
# can choose the download source. uv checks each download against its built-in sha256, so a
# staging release can only ever place an official build, and only in staging's own dir.
py_ver=3.11
if [ -f "$release_dir/.python-version" ]; then
	py_ver=$(tr -d '[:space:]' <"$release_dir/.python-version")
fi
[[ "$py_ver" =~ ^3\.1[1-4]$ ]] || die ".python-version '$py_ver' is not 3.11-3.14"

if [ "$py_ver" = 3.11 ]; then
	python=/usr/bin/python3.11
	log "python $py_ver (system): $python"
else
	py_dir=/opt/wac-python-$target
	py_cache=/var/cache/wac-uv-python-$target
	install -d -o root -g root -m 0755 "$py_dir"
	install -d -o root -g root -m 0700 "$py_cache"
	uv_root() {
		(cd / && env -i \
			PATH=/usr/local/bin:/usr/bin:/bin \
			HOME=/root \
			UV_NO_CONFIG=1 \
			UV_PYTHON_PREFERENCE=only-managed \
			UV_PYTHON_INSTALL_DIR="$py_dir" \
			UV_CACHE_DIR="$py_cache" \
			"$UV" "$@")
	}
	log "python $py_ver (uv-managed): installing into $py_dir"
	# --no-bin: no python3.x links in /root/.local/bin. only-managed (above) = never a system one.
	uv_root python install --no-bin "$py_ver"
	chmod -R a+rX "$py_dir"
	python=$(uv_root python find "$py_ver") || die "uv python find $py_ver failed"
	[ -x "$python" ] || die "uv python find $py_ver gave '$python'"
	log "python $py_ver (uv-managed): $python"
	# Never delete an installed version here: kept releases' venvs symlink into $py_dir.
fi

# --- Build ---------------------------------------------------------------------------------
install -d -o "$app_user" -g "$app_user" -m 0750 "$uv_cache"
(
	cd "$release_dir"
	runuser -u "$app_user" -- env -i \
		PATH=/usr/local/bin:/usr/bin:/bin \
		HOME=/nonexistent \
		UV_PYTHON="$python" \
		UV_PYTHON_DOWNLOADS=never \
		UV_CACHE_DIR="$uv_cache" \
		UV_NO_CONFIG=1 \
		"$UV" sync --frozen --no-dev --compile-bytecode
)

WAC_RELEASE_DIR=$release_dir WAC_ENV_FILE=$env_file.next "$WAC_MANAGE" "$target" migrate --noinput
WAC_RELEASE_DIR=$release_dir WAC_ENV_FILE=$env_file.next "$WAC_MANAGE" "$target" collectstatic --noinput

# --- Infra files (prod only) ---------------------------------------------------------------
# Staging refs never install root-run units or scripts, so a branch on staging can't touch prod.
# The files come from a root-only extraction of the tarball, never from the release dir (which
# the app user can write). The validated set is kept in /var/lib/wac/infra-vm for reboots.
if [ "$target" = prod ]; then
	mkdir -p "$work/infra"
	if tar -xzf "$work/release.tar.gz" -C "$work/infra" --no-same-owner infra/vm 2>/dev/null &&
		[ -f "$work/infra/infra/vm/provision.sh" ]; then
		bash "$work/infra/infra/vm/provision.sh" --install-files "$work/infra/infra/vm"
		install -d -o root -g root -m 0755 /var/lib/wac
		rm -rf /var/lib/wac/infra-vm.new
		cp -R "$work/infra/infra/vm" /var/lib/wac/infra-vm.new
		chown -R root:root /var/lib/wac/infra-vm.new
		rm -rf /var/lib/wac/infra-vm.old
		if [ -d /var/lib/wac/infra-vm ]; then mv /var/lib/wac/infra-vm /var/lib/wac/infra-vm.old; fi
		mv /var/lib/wac/infra-vm.new /var/lib/wac/infra-vm
		rm -rf /var/lib/wac/infra-vm.old
	else
		log "release has no infra/vm; leaving installed units and scripts as they are"
	fi
fi

# --- Switch over ---------------------------------------------------------------------------
prev_release=$(readlink "$base/current" 2>/dev/null || true)
[ -f "$env_file" ] && cp -p "$env_file" "$work/env.prev"

mv -f "$env_file.next" "$env_file"
ln -sfn "$release_dir" "$base/current.new"
mv -T "$base/current.new" "$base/current"
committed=1

systemctl daemon-reload
if systemctl restart "$service" && sleep 5 && systemctl is-active --quiet "$service"; then
	log "$service is running $pointer"
else
	log "$service failed to start on $pointer; rolling back to '${prev_release:-none}'"
	journalctl -u "$service" -n 50 --no-pager || true
	if [ -n "$prev_release" ] && [ -d "$prev_release" ]; then
		[ -f "$work/env.prev" ] && install -o root -g "$app_user" -m 0640 "$work/env.prev" "$env_file"
		ln -sfn "$prev_release" "$base/current.new"
		mv -T "$base/current.new" "$base/current"
		systemctl restart "$service" || true
	else
		rm -f "$base/current"
		systemctl stop "$service" || true
	fi
	rm -rf -- "$release_dir"
	exit 1
fi

printf '%s\n' "$pointer" >"$base/deployed"
rm -f "$base/failed"

# --- Keep the newest releases ---------------------------------------------------------------
current_target=$(readlink -f "$base/current")
mapfile -t releases < <(find "$base/releases" -mindepth 1 -maxdepth 1 -type d | sort -r)
for old in "${releases[@]:$KEEP_RELEASES}"; do
	[ "$(readlink -f "$old")" = "$current_target" ] && continue
	rm -rf -- "$old"
done

log "done: $pointer"
