#!/usr/bin/env bash
# Nightly backup of the prod database. Runs as root from wac-backup.service.
# Installed to /usr/local/sbin/wac-backup-db.
#
# pg_dump -Fc wac (as wac) -> gs://<backup-bucket>/db/wac-<UTC yyyymmddTHHMMSS>.dump (R6).
# Uploaded with curl and the metadata-server token; ifGenerationMatch=0 means an existing
# object is never overwritten. The bucket's lifecycle rule keeps 30 days.
set -euo pipefail

MD=http://metadata.google.internal/computeMetadata/v1

log() { echo "wac-backup: $*"; }
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

[ "$(id -u)" -eq 0 ] || die "must run as root"

bucket=$(md_get instance/attributes/wac-backup-bucket) || die "metadata key wac-backup-bucket missing"
name=db/wac-$(date -u +%Y%m%dT%H%M%S).dump

work=$(mktemp -d /var/tmp/wac-backup.XXXXXX)
trap 'rm -rf -- "$work"' EXIT
dump=$work/wac.dump

cd /
runuser -u wac -- pg_dump -Fc wac >"$dump"
pg_restore -l "$dump" >/dev/null || die "dump does not list; not uploading"
size=$(stat -c %s "$dump")

tok=$(gcp_token)
curl -fsS --retry 3 -X POST -T "$dump" -o /dev/null \
	-H "Authorization: Bearer $tok" \
	-H 'Content-Type: application/octet-stream' \
	"https://storage.googleapis.com/upload/storage/v1/b/$bucket/o?uploadType=media&ifGenerationMatch=0&name=$(urlencode "$name")"

log "uploaded gs://$bucket/$name ($size bytes)"
