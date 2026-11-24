#!/usr/bin/env bash
# Publish a release for the VM to pick up. Runs on the laptop, never on the VM.
#
#   infra/vm/release.sh --target prod [--force] [git-ref]
#   infra/vm/release.sh --target staging [--force] [git-ref]
#
# Default ref is HEAD. Builds `git archive` of the ref, uploads it to
# gs://<deploy-bucket>/releases/<sha>.tar.gz, then writes the pointer
# gs://<deploy-bucket>/current-<target>, then sets instance metadata deploy-nonce-<target> so
# wac-deploy-watch on the VM deploys within seconds. The VM also polls the pointer every
# 15 minutes, so a failed metadata update only delays the deploy.
# --force writes "<sha>:<nonce>" so the same sha deploys again (migrations, new secret
# version) (R7). Secrets are not touched here; they live in Secret Manager.
#
# Checks: gcloud config `wac` must be ali@weallcode.org on the We All Code project; prod refs
# must be on origin/main; staging refs must be reachable from an origin/ branch (R10).
set -euo pipefail

export CLOUDSDK_ACTIVE_CONFIG_NAME=wac
EXPECTED_ACCOUNT=ali@weallcode.org
# The project ID is wac-website-<suffix> (Checkpoint 0b). Set WAC_PROJECT_ID to pin it exactly.
PROJECT_PATTERN='^wac-website-[a-z0-9-]+$'

die() {
	echo "release.sh: $*" >&2
	exit 1
}

usage() {
	echo "usage: release.sh --target prod|staging [--force] [git-ref]" >&2
	exit 64
}

target=""
force=0
ref=HEAD
while [ $# -gt 0 ]; do
	case "$1" in
	--target)
		[ $# -ge 2 ] || usage
		target=$2
		shift 2
		;;
	--target=*)
		target=${1#--target=}
		shift
		;;
	--force)
		force=1
		shift
		;;
	-h | --help) usage ;;
	-*) usage ;;
	*)
		ref=$1
		shift
		;;
	esac
done
case "$target" in
prod | staging) ;;
*) usage ;;
esac

command -v gcloud >/dev/null || die "gcloud is not installed"
command -v git >/dev/null || die "git is not installed"

# --- Account and project -------------------------------------------------------------------
account=$(gcloud config get account 2>/dev/null || true)
project=$(gcloud config get project 2>/dev/null || true)
[ "$account" = "$EXPECTED_ACCOUNT" ] ||
	die "gcloud config 'wac' account is '$account', expected $EXPECTED_ACCOUNT"
case "$project" in
"" | braven-data-infra) die "gcloud config 'wac' project is '$project'; refusing" ;;
esac
if [ -n "${WAC_PROJECT_ID:-}" ]; then
	[ "$project" = "$WAC_PROJECT_ID" ] || die "project is '$project', WAC_PROJECT_ID is '$WAC_PROJECT_ID'"
else
	[[ "$project" =~ $PROJECT_PATTERN ]] || die "project '$project' doesn't look like the We All Code project (set WAC_PROJECT_ID)"
fi
bucket=wac-deploy-$project

# --- Ref checks ----------------------------------------------------------------------------
repo=$(git rev-parse --show-toplevel)
sha=$(git -C "$repo" rev-parse --verify --quiet "$ref^{commit}") || die "unknown git ref '$ref'"

if [ "$target" = prod ]; then
	git -C "$repo" rev-parse --verify --quiet origin/main >/dev/null || die "no origin/main; run 'git fetch origin'"
	git -C "$repo" merge-base --is-ancestor "$sha" origin/main ||
		die "$sha is not on origin/main; prod deploys only from main (run 'git fetch origin' if it was just merged)"
else
	# Only refs pushed to origin (no fork PR refs or other remotes) may run on staging.
	remote_branches=$(git -C "$repo" branch -r --contains "$sha" --format='%(refname:short)')
	if ! grep -q '^origin/' <<<"$remote_branches"; then
		die "$sha is not on any origin/ branch; push it to origin first (run 'git fetch origin')"
	fi
fi

git -C "$repo" cat-file -e "$sha:infra/vm/deploy-pull.sh" 2>/dev/null ||
	echo "release.sh: warning: $sha has no infra/vm/; the VM keeps its installed units and scripts" >&2

pointer=$sha
if [ "$force" = 1 ]; then
	pointer="$sha:$(date -u +%Y%m%dT%H%M%SZ)"
fi

# --- Upload ----------------------------------------------------------------------------------
work=$(mktemp -d)
trap 'rm -rf -- "$work"' EXIT

object="gs://$bucket/releases/$sha.tar.gz"
if gcloud storage objects describe "$object" >/dev/null 2>&1; then
	echo "release.sh: $object already exists; reusing it"
else
	git -C "$repo" archive --format=tar.gz -o "$work/release.tar.gz" "$sha"
	gcloud storage cp --quiet "$work/release.tar.gz" "$object"
fi

printf '%s\n' "$pointer" >"$work/pointer"
gcloud storage cp --quiet --content-type=text/plain --cache-control=no-store \
	"$work/pointer" "gs://$bucket/current-$target"

echo "release.sh: gs://$bucket/current-$target -> $pointer"

# --- Instant deploy -----------------------------------------------------------------------------
# Change instance metadata deploy-nonce-<target>; wac-deploy-watch on the VM long-polls it and
# starts the deploy within seconds. The VM is the instance whose wac-deploy-bucket metadata is
# this bucket (set WAC_VM_NAME and WAC_VM_ZONE to skip the lookup). Any failure here only loses
# the speed-up: the pointer is written and the 15-minute timer still deploys it.
notified=0
vm_name=${WAC_VM_NAME:-}
vm_zone=${WAC_VM_ZONE:-}
if [ -z "$vm_name" ] || [ -z "$vm_zone" ]; then
	vm_list=$(gcloud compute instances list \
		--filter="metadata.items.key=wac-deploy-bucket AND metadata.items.value=$bucket" \
		--format='value(name,zone.basename())' 2>/dev/null) || vm_list=""
	if [ "$(grep -c . <<<"$vm_list")" = 1 ]; then
		read -r vm_name vm_zone <<<"$vm_list"
	else
		echo "release.sh: warning: expected one VM with wac-deploy-bucket=$bucket, found: '${vm_list//$'\n'/, }'" >&2
		vm_name=""
	fi
fi
if [ -n "$vm_name" ] && [ -n "$vm_zone" ]; then
	nonce="$sha:$(date -u +%Y%m%dT%H%M%SZ)"
	if gcloud compute instances add-metadata "$vm_name" --zone "$vm_zone" --quiet \
		--metadata "deploy-nonce-$target=$nonce" >/dev/null 2>"$work/add-metadata.err"; then
		notified=1
	else
		echo "release.sh: warning: could not set deploy-nonce-$target on $vm_name:" >&2
		sed 's/^/  /' "$work/add-metadata.err" >&2
	fi
fi

if [ "$notified" = 1 ]; then
	echo "release.sh: set deploy-nonce-$target=$nonce on $vm_name; the VM starts the deploy within seconds"
	echo "release.sh: (if wac-deploy-watch isn't running there yet, wac-deploy@$target.timer picks it up within ~15 minutes)"
else
	echo "release.sh: the VM deploys it within ~15 minutes (wac-deploy@$target.timer)."
fi
echo "release.sh: watch with: journalctl -u wac-deploy@$target -f (serial console)"
