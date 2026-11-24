#!/usr/bin/env bash
# Replace the staging database with a fresh copy of prod. Run by hand as root on the VM:
#   sudo wac-refresh-staging-db
# Installed to /usr/local/sbin/wac-refresh-staging-db.
#
# Uses a local pg_dump of `wac` (R6), not the backup bucket. The dump goes to a private temp
# file instead of a pipe, because the TOC has to be listed and filtered first (R11): the prod
# dump carries EXTENSION entries a non-superuser can't restore.
#
# Refuses to run unless the staging env sends email to the console, so a prod copy can never
# email real people.
set -euo pipefail

STAGING_ENV=/etc/wac/env-staging
CONSOLE_BACKEND=django.core.mail.backends.console.EmailBackend

log() { echo "wac-refresh-staging-db: $*"; }
die() {
	log "ERROR: $*" >&2
	exit 1
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

[ "$(id -u)" -eq 0 ] || die "must run as root"
[ -f "$STAGING_ENV" ] || die "$STAGING_ENV is missing; deploy staging first"

backend=$(env_value "$STAGING_ENV" EMAIL_BACKEND)
[ "$backend" = "$CONSOLE_BACKEND" ] || die "staging EMAIL_BACKEND is '$backend', not $CONSOLE_BACKEND; refusing"
[ "$(env_value "$STAGING_ENV" DB_NAME)" = wac_staging ] || die "staging DB_NAME is not wac_staging; refusing"

work=$(mktemp -d /var/tmp/wac-refresh.XXXXXX)
restart=0
on_exit() {
	rm -rf -- "$work"
	if [ "$restart" = 1 ]; then systemctl start wac-staging || true; fi
}
trap on_exit EXIT
# Readable by wac-staging (pg_restore runs as that user); nobody else.
chgrp wac-staging "$work"
chmod 0750 "$work"
cd /

log "dumping wac"
runuser -u wac -- pg_dump -Fc wac >"$work/wac.dump"
chgrp wac-staging "$work/wac.dump"
chmod 0640 "$work/wac.dump"
pg_restore -l "$work/wac.dump" | grep -v -E 'EXTENSION|COMMENT - EXTENSION' >"$work/toc"
chgrp wac-staging "$work/toc"
chmod 0640 "$work/toc"

if systemctl is-active --quiet wac-staging; then restart=1; fi
systemctl stop wac-staging

log "recreating wac_staging"
runuser -u postgres -- dropdb --if-exists --force wac_staging
runuser -u postgres -- createdb -O wac_staging wac_staging
runuser -u postgres -- psql -X -v ON_ERROR_STOP=1 -qc \
	'REVOKE CONNECT ON DATABASE wac_staging FROM PUBLIC; GRANT CONNECT ON DATABASE wac_staging TO wac_staging'

log "restoring into wac_staging as wac_staging"
# -U: libpq would otherwise ask for role "wac-staging" (the OS user); pg_ident maps it to wac_staging.
runuser -u wac-staging -- pg_restore -L "$work/toc" --no-owner --no-acl --role=wac_staging \
	-U wac_staging -d wac_staging "$work/wac.dump"

if [ -x /srv/wac/staging/current/.venv/bin/python ]; then
	/usr/local/bin/wac-manage staging migrate --noinput
	restart=1
else
	log "staging has no release yet; skipping migrate (the first staging deploy runs it)"
fi

log "done"
