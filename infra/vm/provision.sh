#!/usr/bin/env bash
# VM provisioning for wac-web (Debian 12, IPv6-only e2-micro).
#
# Terraform passes this file as the instance's `startup-script`, so it runs as root on every
# boot and must stay idempotent. Its output goes to the serial console and the journal
# (google-startup-scripts.service).
#
#   provision.sh                         full provisioning (startup script, or by hand)
#   provision.sh --install-files <dir>   only (re)install the infra/vm files from <dir> and
#                                        reload what changed; used by prod deploys (R5)
#
# GCS and Secret Manager are reached with curl and the metadata-server token over IPv6
# (no google-cloud-cli on the VM).
set -euo pipefail

# Object Terraform uploads to the deploy bucket with every file of infra/vm/ (R5).
# A .zip name is handled too, in case the archive provider only builds zip files.
BOOTSTRAP_OBJECT=${WAC_BOOTSTRAP_OBJECT:-bootstrap.tgz}

MD=http://metadata.google.internal/computeMetadata/v1
PG_VERSION=17
PG_ETC=/etc/postgresql/$PG_VERSION/main
SERIAL_ADMIN=wacadmin
export DEBIAN_FRONTEND=noninteractive

log() { echo "wac-provision: $*"; }
die() {
	log "ERROR: $*" >&2
	exit 1
}

# On first boot apt-daily / unattended-upgrades may hold the dpkg lock; wait instead of failing.
apt_get() { apt-get -o DPkg::Lock::Timeout=600 "$@"; }

md_get() {
	curl -fsS --retry 5 --retry-connrefused --retry-delay 2 -H 'Metadata-Flavor: Google' "$MD/$1"
}

# md_attr_optional KEY: print an instance attribute, or nothing (status 1) when it isn't set
md_attr_optional() {
	local out code
	out=$(mktemp)
	code=$(curl -sS --retry 5 --retry-connrefused --retry-delay 2 -o "$out" -w '%{http_code}' \
		-H 'Metadata-Flavor: Google' "$MD/instance/attributes/$1") || code=000
	if [ "$code" = 200 ]; then
		cat "$out"
		rm -f "$out"
		return 0
	fi
	rm -f "$out"
	[ "$code" = 404 ] || log "metadata attribute $1: HTTP $code" >&2
	return 1
}

gcp_token() {
	md_get instance/service-accounts/default/token | jq -er .access_token
}

urlencode() {
	jq -rn --arg s "$1" '$s|@uri'
}

gcs_download() { # BUCKET OBJECT OUTFILE
	local tok
	tok=$(gcp_token)
	curl -fsS --retry 3 -o "$3" -H "Authorization: Bearer $tok" \
		"https://storage.googleapis.com/storage/v1/b/$1/o/$(urlencode "$2")?alt=media"
}

# put_file SRC DST MODE [GROUP]: install only when the content differs; status 0 = changed
put_file() {
	local src=$1 dst=$2 mode=$3 group=${4:-root}
	if [ -f "$dst" ] && cmp -s "$src" "$dst"; then
		chmod "$mode" "$dst"
		chgrp "$group" "$dst"
		return 1
	fi
	install -D -o root -g "$group" -m "$mode" "$src" "$dst.wac-new"
	mv -f "$dst.wac-new" "$dst"
	log "installed $dst"
	return 0
}

# put_content DST MODE GROUP: like put_file, content from stdin
put_content() {
	local tmp rc=0
	tmp=$(mktemp)
	cat >"$tmp"
	put_file "$tmp" "$1" "$2" "$3" || rc=$?
	rm -f "$tmp"
	return "$rc"
}

CHANGED_UNITS=0
CHANGED_CADDY=0
CHANGED_NFT=0
CHANGED_PG=0
CHANGED_WATCH=0

# install_vm_files SRCDIR: validate, then install every infra/vm file to its place on the VM.
install_vm_files() {
	local src=$1 f
	local units=(wac-web.service wac-staging.service wac-deploy@.service wac-deploy@.timer
		wac-backup.service wac-backup.timer)
	local required=("${units[@]}" Caddyfile nftables-wac.nft postgresql.conf.d-wac.conf
		deploy-pull.sh backup-db.sh refresh-staging-db.sh provision.sh wac-manage)

	for f in "${required[@]}"; do
		[ -f "$src/$f" ] || die "$src/$f is missing"
	done

	# Validate before installing anything, so a bad file never lands on disk.
	nft -c -f "$src/nftables-wac.nft" || die "nftables-wac.nft does not load"
	if command -v caddy >/dev/null && [ -f /etc/caddy/origin.pem ] && [ -f /etc/caddy/wac-staging-auth.caddy ]; then
		# Validate from /etc/caddy so the relative `import wac-staging-auth.caddy` resolves.
		install -m 0644 "$src/Caddyfile" /etc/caddy/Caddyfile.wac-candidate
		if ! caddy validate --adapter caddyfile --config /etc/caddy/Caddyfile.wac-candidate >/dev/null 2>&1; then
			caddy validate --adapter caddyfile --config /etc/caddy/Caddyfile.wac-candidate || true
			rm -f /etc/caddy/Caddyfile.wac-candidate
			die "Caddyfile does not validate"
		fi
		rm -f /etc/caddy/Caddyfile.wac-candidate
	fi

	for f in "${units[@]}"; do
		if put_file "$src/$f" "/etc/systemd/system/$f" 0644; then CHANGED_UNITS=1; fi
	done
	# Optional: at boot $src is /var/lib/wac/infra-vm from the last prod deploy, which may
	# predate the watcher (a newer startup-script, or prod rolled back). Skip, never die.
	if [ -f "$src/wac-deploy-watch.service" ] && [ -f "$src/deploy-watch.sh" ]; then
		if put_file "$src/wac-deploy-watch.service" /etc/systemd/system/wac-deploy-watch.service 0644; then
			CHANGED_UNITS=1
			CHANGED_WATCH=1
		fi
		if put_file "$src/deploy-watch.sh" /usr/local/sbin/wac-deploy-watch 0755; then CHANGED_WATCH=1; fi
	else
		log "$src has no wac-deploy-watch.service/deploy-watch.sh; leaving the deploy watcher as it is"
	fi
	# Optional for the same reason: an older prod release has no reminder units.
	if [ -f "$src/wac-reminders.service" ] && [ -f "$src/wac-reminders.timer" ]; then
		if put_file "$src/wac-reminders.service" /etc/systemd/system/wac-reminders.service 0644; then CHANGED_UNITS=1; fi
		if put_file "$src/wac-reminders.timer" /etc/systemd/system/wac-reminders.timer 0644; then CHANGED_UNITS=1; fi
	else
		log "$src has no wac-reminders.service/.timer; leaving class reminders as they are"
	fi
	if put_file "$src/Caddyfile" /etc/caddy/Caddyfile 0644; then CHANGED_CADDY=1; fi
	if put_file "$src/nftables-wac.nft" /etc/wac/nftables-wac.nft 0644; then CHANGED_NFT=1; fi
	if put_file "$src/postgresql.conf.d-wac.conf" "$PG_ETC/conf.d/wac.conf" 0644; then CHANGED_PG=1; fi
	put_file "$src/deploy-pull.sh" /usr/local/sbin/wac-deploy-pull 0755 || true
	put_file "$src/backup-db.sh" /usr/local/sbin/wac-backup-db 0755 || true
	put_file "$src/refresh-staging-db.sh" /usr/local/sbin/wac-refresh-staging-db 0755 || true
	put_file "$src/provision.sh" /usr/local/sbin/wac-provision 0755 || true
	put_file "$src/wac-manage" /usr/local/bin/wac-manage 0755 || true
}

# Reload whatever install_vm_files changed (deploy-time path; full provisioning restarts).
reload_changed() {
	if [ "$CHANGED_UNITS" = 1 ]; then systemctl daemon-reload; fi
	if [ "$CHANGED_NFT" = 1 ]; then nft -f /etc/wac/nftables-wac.nft; fi
	if [ "$CHANGED_CADDY" = 1 ] && systemctl is-active --quiet caddy; then systemctl reload caddy; fi
	if [ "$CHANGED_PG" = 1 ]; then
		systemctl reload postgresql
		log "postgresql.conf.d-wac.conf changed; shared_buffers/listen_addresses need 'systemctl restart postgresql'"
	fi
	start_watcher
	start_reminders
}

# Enable the class reminder timer once its unit is installed, so a deploy turns it on
# without a reprovision. Never fatal: a timer problem must not fail the deploy.
start_reminders() {
	[ -f /etc/systemd/system/wac-reminders.timer ] || return 0
	systemctl enable --now --quiet wac-reminders.timer ||
		log "WARNING: could not enable wac-reminders.timer; class reminders are not scheduled" >&2
	return 0
}

# Enable and (re)start the instant-deploy watcher. Never fatal: the 15-minute timer is the
# fallback, and a watcher problem must not fail the deploy that installs it. The watcher only
# starts wac-deploy@ units with --no-block, so restarting it from inside a deploy never
# touches that deploy.
start_watcher() {
	local verb=start
	if [ ! -f /etc/systemd/system/wac-deploy-watch.service ] || [ ! -x /usr/local/sbin/wac-deploy-watch ]; then
		return 0
	fi
	if [ "$CHANGED_WATCH" = 1 ]; then verb=restart; fi
	if systemctl enable --quiet wac-deploy-watch.service && systemctl "$verb" wac-deploy-watch.service; then
		return 0
	fi
	log "WARNING: could not $verb wac-deploy-watch.service; deploys fall back to the 15-minute timer" >&2
	return 0
}

if [ "${1:-}" = "--install-files" ]; then
	if [ $# -ne 2 ] || [ ! -d "$2" ]; then die "usage: provision.sh --install-files <dir>"; fi
	[ "$(id -u)" -eq 0 ] || die "must run as root"
	install_vm_files "$2"
	reload_changed
	exit 0
fi

[ "$(id -u)" -eq 0 ] || die "must run as root"
log "start $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# --- Swap ----------------------------------------------------------------------------------
if [ ! -f /swapfile ]; then
	fallocate -l 1G /swapfile
	chmod 600 /swapfile
	mkswap /swapfile
fi
active_swap=$(swapon --show=NAME --noheadings)
grep -qx /swapfile <<<"$active_swap" || swapon /swapfile
grep -q '^/swapfile ' /etc/fstab || echo '/swapfile none swap sw 0 0' >>/etc/fstab
echo 'vm.swappiness=10' | put_content /etc/sysctl.d/90-wac.conf 0644 root || true
sysctl -q -p /etc/sysctl.d/90-wac.conf

# --- Base packages -------------------------------------------------------------------------
apt_get update -q
apt_get install -y -q --no-install-recommends \
	ca-certificates curl gnupg jq nftables unattended-upgrades apt-listchanges \
	python3 python3-venv python3.11-venv postgresql-common \
	libjpeg62-turbo zlib1g debian-keyring debian-archive-keyring apt-transport-https

printf '%s\n' 'APT::Periodic::Update-Package-Lists "1";' 'APT::Periodic::Unattended-Upgrade "1";' |
	put_content /etc/apt/apt.conf.d/20auto-upgrades 0644 root || true
systemctl enable --now unattended-upgrades.service

# --- Users and directories -----------------------------------------------------------------
for u in wac wac-staging; do
	id -u "$u" >/dev/null 2>&1 ||
		useradd --system --user-group --no-create-home --home-dir /nonexistent --shell /usr/sbin/nologin "$u"
done

# /etc/wac is traversable but not listable: each file carries its own group (R10).
install -d -o root -g root -m 0711 /etc/wac
install -d -o root -g root -m 0755 /srv/wac
install -d -o root -g wac -m 0755 /srv/wac/prod
install -d -o wac -g wac -m 0755 /srv/wac/prod/releases
install -d -o root -g wac-staging -m 0755 /srv/wac/staging
install -d -o wac-staging -g wac-staging -m 0755 /srv/wac/staging/releases
# Separate uv caches so staging can never poison prod's wheels.
install -d -o wac -g wac -m 0750 /var/cache/wac-uv
install -d -o wac-staging -g wac-staging -m 0750 /var/cache/wac-uv-staging

# --- PostgreSQL 17 (PGDG) ------------------------------------------------------------------
if ! dpkg -s "postgresql-$PG_VERSION" >/dev/null 2>&1; then
	/usr/share/postgresql-common/pgdg/apt.postgresql.org.sh -y
	apt_get install -y -q "postgresql-$PG_VERSION"
fi

# --- Caddy (cloudsmith) --------------------------------------------------------------------
if ! dpkg -s caddy >/dev/null 2>&1; then
	curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/gpg.key |
		gpg --batch --yes --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
	curl -1sLf https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt \
		>/etc/apt/sources.list.d/caddy-stable.list
	apt_get update -q
	apt_get install -y -q caddy
fi

# --- uv from PyPI (GitHub has no IPv6) -----------------------------------------------------
if [ ! -x /opt/uv/bin/uv ]; then
	python3 -m venv /opt/uv
	/opt/uv/bin/pip install --quiet --upgrade pip uv
fi
ln -sfn /opt/uv/bin/uv /usr/local/bin/uv

# --- Origin certificate and staging basic auth from metadata --------------------------------
cert=$(md_attr_optional wac-origin-cert) || die "metadata key wac-origin-cert is missing"
key=$(md_attr_optional wac-origin-key) || die "metadata key wac-origin-key is missing"
if printf '%s\n' "$cert" | put_content /etc/caddy/origin.pem 0640 caddy; then CHANGED_CADDY=1; fi
if printf '%s\n' "$key" | put_content /etc/caddy/origin.key 0640 caddy; then CHANGED_CADDY=1; fi
unset cert key

# The value is a bcrypt hash from `caddy hash-password` (user "staging"), or "<user> <hash>".
auth_user=staging
auth_hash=""
if auth_raw=$(md_attr_optional wac-staging-basic-auth) && [ -n "$auth_raw" ]; then
	auth_raw=$(printf '%s' "$auth_raw" | tr -d '\r\n')
	if [[ "$auth_raw" == *" "* ]]; then
		auth_user=${auth_raw%% *}
		auth_hash=${auth_raw##* }
	else
		auth_hash=$auth_raw
	fi
fi
if ! [[ "$auth_hash" =~ ^\$2[abxy]?\$[0-9]{2}\$[./A-Za-z0-9]{53}$ ]] || ! [[ "$auth_user" =~ ^[A-Za-z0-9._-]+$ ]]; then
	if [ -f /etc/caddy/wac-staging-auth.caddy ] && grep -q '# locked' /etc/caddy/wac-staging-auth.caddy; then
		auth_hash=keep
	else
		log "wac-staging-basic-auth unset or not a bcrypt hash; locking staging with a random password"
		auth_user=staging
		auth_hash=$(caddy hash-password --plaintext "$(head -c 32 /dev/urandom | base64)")
	fi
	locked="# locked: random password, set metadata wac-staging-basic-auth and re-run provisioning"
else
	locked="# from metadata wac-staging-basic-auth"
fi
if [ "$auth_hash" != keep ]; then
	if printf '%s\nbasic_auth {\n\t%s %s\n}\n' "$locked" "$auth_user" "$auth_hash" |
		put_content /etc/caddy/wac-staging-auth.caddy 0640 caddy; then
		CHANGED_CADDY=1
	fi
fi
unset auth_raw auth_hash

# --- Serial-console admin (R25) ------------------------------------------------------------
id -u "$SERIAL_ADMIN" >/dev/null 2>&1 ||
	useradd --create-home --shell /bin/bash --groups sudo "$SERIAL_ADMIN"
if serial_hash=$(md_attr_optional wac-serial-password-hash) && [ -n "$serial_hash" ]; then
	usermod -p "$(printf '%s' "$serial_hash" | tr -d '\r\n')" "$SERIAL_ADMIN"
	log "serial-console user $SERIAL_ADMIN has the temporary password from metadata"
else
	usermod -p '!' "$SERIAL_ADMIN"
	log "serial-console user $SERIAL_ADMIN is locked (no wac-serial-password-hash)"
fi
unset serial_hash

# --- infra/vm files ------------------------------------------------------------------------
# After the first prod deploy, the root-owned copy that deploy saved wins, so a reboot never
# downgrades files to the (possibly older) bootstrap archive from the last terraform apply.
# Never install from /srv/wac/*/current: the app user can write there.
if [ -f /var/lib/wac/infra-vm/provision.sh ]; then
	log "installing infra/vm from the last prod deploy (/var/lib/wac/infra-vm)"
	install_vm_files /var/lib/wac/infra-vm
else
	deploy_bucket=$(md_attr_optional wac-deploy-bucket) || die "metadata key wac-deploy-bucket is missing"
	boot=$(mktemp -d /var/tmp/wac-bootstrap.XXXXXX)
	trap 'rm -rf -- "$boot"' EXIT
	log "downloading gs://$deploy_bucket/$BOOTSTRAP_OBJECT"
	gcs_download "$deploy_bucket" "$BOOTSTRAP_OBJECT" "$boot/archive"
	mkdir "$boot/x"
	case "$BOOTSTRAP_OBJECT" in
	*.zip) python3 -m zipfile -e "$boot/archive" "$boot/x" ;;
	*.tgz | *.tar.gz) tar -xzf "$boot/archive" -C "$boot/x" --no-same-owner ;;
	*) die "unknown bootstrap archive type: $BOOTSTRAP_OBJECT" ;;
	esac
	caddyfile=$(find "$boot/x" -type f -name Caddyfile -print -quit)
	[ -n "$caddyfile" ] || die "bootstrap archive has no Caddyfile"
	install_vm_files "$(dirname "$caddyfile")"
fi

# --- nftables: staging user can't reach the metadata server (R10) --------------------------
nft -f /etc/wac/nftables-wac.nft

# --- PostgreSQL config, roles, databases ---------------------------------------------------
if [ "$CHANGED_PG" = 1 ]; then systemctl restart postgresql; fi
systemctl enable --now postgresql

# Peer auth maps Unix user wac-staging to role wac_staging; wac -> wac needs no map.
grep -qE '^wac[[:space:]]+wac-staging[[:space:]]+wac_staging' "$PG_ETC/pg_ident.conf" ||
	echo 'wac             wac-staging             wac_staging' >>"$PG_ETC/pg_ident.conf"
if ! grep -qE '^local[[:space:]]+wac_staging[[:space:]]+wac_staging[[:space:]]+peer[[:space:]]+map=wac' "$PG_ETC/pg_hba.conf"; then
	sed -i '1i local   wac_staging     wac_staging                             peer map=wac' "$PG_ETC/pg_hba.conf"
fi
systemctl reload postgresql

psql_q() { runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -qtAc "$1"; }
for role in wac wac_staging; do
	[ "$(psql_q "SELECT 1 FROM pg_roles WHERE rolname = '$role'")" = 1 ] ||
		psql_q "CREATE ROLE $role LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE"
done
for db in wac wac_staging; do
	[ "$(psql_q "SELECT 1 FROM pg_database WHERE datname = '$db'")" = 1 ] ||
		runuser -u postgres -- createdb -O "$db" "$db"
	psql_q "REVOKE CONNECT ON DATABASE $db FROM PUBLIC; GRANT CONNECT ON DATABASE $db TO $db"
done

# --- Services ------------------------------------------------------------------------------
systemctl daemon-reload
systemctl enable caddy
if [ "$CHANGED_CADDY" = 1 ]; then systemctl restart caddy; else systemctl start caddy; fi
systemctl enable --now wac-deploy@prod.timer wac-deploy@staging.timer wac-backup.timer
start_watcher
start_reminders
# Both start on their own once a deploy has created /srv/wac/<target>/current.
systemctl enable wac-web.service wac-staging.service

log "done $(date -u +%Y-%m-%dT%H:%M:%SZ)"
