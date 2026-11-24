# infra/vm — the wac-web VM

Everything that runs on the single e2-micro VM (Debian 12, IPv6-only): Postgres 17, Caddy, gunicorn for prod and staging, a pull-based deploy and a nightly backup. Terraform (`infra/terraform/`) creates the VM and passes `provision.sh` as its startup script.

## How files reach the VM

The VM can't reach GitHub (no IPv6), so nothing is cloned.

- **First boot:** `provision.sh` runs as the startup script. It downloads `bootstrap.tgz` (an archive of this directory that Terraform uploads to the deploy bucket; the name is `BOOTSTRAP_OBJECT` at the top of `provision.sh`, and a `.zip` works too) and installs every file below.
- **Every prod deploy:** each release tarball contains `infra/vm/`. Root extracts only `infra/vm/` into a root-only temp dir, never the release dir, which the app user can write. It then validates the `Caddyfile` (`caddy validate`) and `nftables-wac.nft` (`nft -c`), installs whatever changed, and runs `systemctl daemon-reload` / `systemctl reload caddy` / `nft -f` as needed. The validated set is saved to `/var/lib/wac/infra-vm` (root-owned).
- **Staging deploys never install infra files.** A branch on staging can't change root-run units or scripts, so it can't touch prod. Test infra changes by reading the diff, then deploy them to prod.
- **Every later boot:** `provision.sh` installs from `/var/lib/wac/infra-vm` once a prod deploy has saved it, otherwise from the bootstrap archive. A reboot never downgrades files to an older bootstrap. After the first prod deploy, a `terraform apply` that changes only `bootstrap.tgz` has no effect on the VM; ship infra changes with a prod release.
- `startup-script` changes take effect only on the next boot: `gcloud compute instances reset wac-web`, or over the serial console run `sudo google_metadata_script_runner startup`. The installed copy, `sudo wac-provision`, runs the last installed version.

| Repo file | Installed as |
|---|---|
| `wac-web.service`, `wac-staging.service`, `wac-deploy@.service`, `wac-deploy@.timer`, `wac-backup.service`, `wac-backup.timer`, `wac-deploy-watch.service` | `/etc/systemd/system/` |
| `Caddyfile` | `/etc/caddy/Caddyfile` |
| `nftables-wac.nft` | `/etc/wac/nftables-wac.nft` |
| `postgresql.conf.d-wac.conf` | `/etc/postgresql/17/main/conf.d/wac.conf` |
| `deploy-pull.sh` | `/usr/local/sbin/wac-deploy-pull` |
| `deploy-watch.sh` | `/usr/local/sbin/wac-deploy-watch` |
| `backup-db.sh` | `/usr/local/sbin/wac-backup-db` |
| `refresh-staging-db.sh` | `/usr/local/sbin/wac-refresh-staging-db` |
| `provision.sh` | `/usr/local/sbin/wac-provision` |
| `wac-manage` | `/usr/local/bin/wac-manage` |
| `release.sh`, `env.*.example`, this README | not installed (laptop and reference only) |

`provision.sh` also writes these from metadata: `/etc/caddy/origin.pem` and `/etc/caddy/origin.key` (from `wac-origin-cert` / `wac-origin-key`), and `/etc/caddy/wac-staging-auth.caddy` (from `wac-staging-basic-auth`).

## GCS and Secret Manager on the VM

There is no `google-cloud-cli` on the VM. Every script uses `curl` with the token from the metadata server (`http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token`, reached over IPv6) against the JSON APIs:

- GCS download: `https://storage.googleapis.com/storage/v1/b/<bucket>/o/<object>?alt=media`
- GCS upload (backups): `https://storage.googleapis.com/upload/storage/v1/b/<bucket>/o?uploadType=media&ifGenerationMatch=0&name=...`
- Secret Manager: `https://secretmanager.googleapis.com/v1/projects/<project>/secrets/<name>/versions/latest:access`

Instance metadata keys read: `wac-deploy-bucket`, `wac-backup-bucket`, `wac-origin-cert`, `wac-origin-key`, `wac-staging-basic-auth`, `wac-serial-password-hash`, and `deploy-nonce-prod` / `deploy-nonce-staging` (set by `release.sh`, not Terraform; long-polled by `wac-deploy-watch`). Secrets read: `wac-env-prod`, `wac-env-staging`, `wac-staging-sa-key`.

## Deploy

From the laptop, at the repo root (needs the `wac` gcloud configuration; the script refuses any other account or project):

```sh
infra/vm/release.sh --target prod             # HEAD; it must be on origin/main
infra/vm/release.sh --target prod <ref>
infra/vm/release.sh --target staging <ref>    # any ref on an origin/ branch (no fork PR refs)
infra/vm/release.sh --target prod --force     # same sha again: rerun migrations, pick up a new secret version
```

`release.sh` uploads `git archive <ref>` to `gs://wac-deploy-<project>/releases/<sha>.tar.gz` and writes `<sha>` (or `<sha>:<nonce>` with `--force`) to `gs://wac-deploy-<project>/current-<target>`. Set `WAC_PROJECT_ID` to pin the exact project ID.

Then it sets instance metadata `deploy-nonce-<target>=<sha>:<UTC time>` with `gcloud compute instances add-metadata`, so the deploy starts within seconds. It finds the VM as the one instance whose `wac-deploy-bucket` metadata is this bucket (`WAC_VM_NAME` and `WAC_VM_ZONE` skip the lookup). If that fails, it warns and exits 0: the pointer is written, and the timer deploys it within 15 minutes. Terraform ignores both nonce keys (`lifecycle.ignore_changes` in `vm.tf`), so they are not drift.

**Instant trigger.** `wac-deploy-watch.service` (root, `Restart=always`) runs `wac-deploy-watch`. It long-polls `computeMetadata/v1/instance/attributes/?recursive=true&wait_for_change=true&last_etag=<etag>&timeout_sec=300` over IPv6 with `Metadata-Flavor: Google`, the same way the deploy scripts reach the metadata server. When `deploy-nonce-prod` or `deploy-nonce-staging` differs from the last value seen, it runs `systemctl start --no-block wac-deploy@<target>.service`.

- Last-seen values live in `/var/lib/wac-deploy-watch/nonce-<target>`. On the very first start it records the current values without deploying. After that, a release made while the watcher was down still deploys when it comes back.
- If that target's deploy is already running, the start is held and fired once the run finishes. A nonce is saved only after its start succeeds, so a held start survives a watcher restart. A `systemctl start` on a running oneshot merges into that run instead of queueing a new one.
- Metadata errors back off up to 60 s and then retry.
- The response body contains the origin key. It stays in a 0700 runtime dir and is deleted after each poll; only the two nonce values are read from it.
- It runs as root because nftables blocks the metadata server for `wac-staging`. That isolation is unchanged.
- Logs: `journalctl -u wac-deploy-watch`.

On the VM, `wac-deploy@prod.timer` and `wac-deploy@staging.timer` also run `wac-deploy-pull <target>` 3 minutes after boot and every 15 minutes after that, as the fallback. For each target it:

1. Reads the pointer. If it equals `/srv/wac/<target>/deployed` (whole-string compare), it stops. If it equals `/srv/wac/<target>/failed`, it also stops: a failed pointer is skipped until it changes.
2. Downloads the tarball and extracts it to `/srv/wac/<target>/releases/<UTC time>-<sha12>`, owned by the target's user.
3. Reads the latest secret version: `wac-env-<target>`, and for staging also `wac-staging-sa-key`. It refuses an env that sets `DATABASE_URL`, or a staging env whose `EMAIL_BACKEND` isn't the console backend.
4. Runs `uv sync --frozen --no-dev` as the target's user (system Python 3.11, no uv Python downloads, its own uv cache).
5. Runs `migrate` and `collectstatic` through `wac-manage`.
6. Prod only: reinstalls changed infra files.
7. Installs `/etc/wac/env-<target>`, flips `current` and restarts `wac-web` or `wac-staging`. If the service doesn't come up, it flips back to the previous release and env and restarts that.
8. Writes `deployed` and keeps the newest 3 releases.

The gunicorn restart in step 7 takes ~20 s (`--preload` on the e2-micro), and its socket is gone meanwhile. Caddy doesn't return 502 straight away: every `reverse_proxy` (snippet `wac_proxy` in the `Caddyfile`) has `lb_try_duration 30s` / `lb_try_interval 250ms`, so it holds the request and redials until gunicorn is back. 30 s is well under Cloudflare's 100 s origin timeout. Only failed dials are retried, so no request reaches gunicorn twice; a restart longer than 30 s still gets a 502. The `Caddyfile` also strips Caddy's `Via` response header.

Any failure leaves `current` and the env file as they were and writes the pointer to `failed`. To retry the same pointer, run `sudo rm /srv/wac/<target>/failed`, or release again with `--force`.

Deploy now instead of waiting: `sudo systemctl start wac-deploy@prod` (or `@staging`).

Only one deploy runs at a time, for both targets together (`flock /run/lock/wac-deploy.lock`). The pointer is read after the lock is taken, so a deploy that waited reads the latest pointer. systemd never runs two copies of `wac-deploy@<target>`, so the timer, the watcher and a manual start can overlap safely.

## Management commands

Always use `wac-manage`. Never `source` an env file: secrets contain `$` and quotes.

```sh
sudo wac-manage prod showmigrations
sudo wac-manage staging migrate --noinput
sudo wac-manage prod shell -c 'from django.conf import settings; print(settings.DEBUG)'
```

It runs `systemd-run --wait --pipe -p User=<user> -p EnvironmentFile=/etc/wac/env-<target> ... .venv/bin/python manage.py <args>`. For staging it first loads the nftables rule and adds `GOOGLE_APPLICATION_CREDENTIALS=/etc/wac/staging-sa.json`. Because it uses `--pipe`, `shell` has no TTY, so pass the code with `-c`.

## Environment files

Each secret (`wac-env-prod`, `wac-env-staging`) is one whole env file, built from the keys in `env.prod.example` / `env.staging.example` and nothing else. When building them from the Heroku config backup, **do not copy** `DATABASE_URL` (it forces `ssl_require` and bypasses the Unix socket), `SENDGRID_*`, `PAPERTRAIL_*`, `HEROKU_*` or `WEB_CONCURRENCY` (R15). `PAYPAL_*` is left out too: no code reads it.

After adding a new secret version, destroy the older ones and keep at most 2 per secret (free tier: 6 active versions). A new version only reaches the VM on the next deploy, so run `release.sh --target <t> --force`.

On the VM:

- `/etc/wac` is `root:root 0711`, so it can be entered but not listed.
- `/etc/wac/env-prod` is `root:wac 0640`.
- `/etc/wac/env-staging` and `/etc/wac/staging-sa.json` are `root:wac-staging 0640`.

## Prod and staging isolation (R10)

| | prod | staging |
|---|---|---|
| Unix user | `wac` | `wac-staging` |
| DB role / database | `wac` / `wac` | `wac_staging` / `wac_staging` (peer map `wac-staging` → `wac_staging` in `pg_ident.conf`) |
| Service | `wac-web` (2 workers, 450 MB) | `wac-staging` (1 worker, 200 MB, `OOMScoreAdjust=500`) |
| GCP identity | VM service account (metadata server) | `wac-staging-vm` key from `wac-staging-sa-key` |
| Socket | `/run/wac-prod/gunicorn.sock` | `/run/wac-staging/gunicorn.sock` |

`CONNECT` on each database is revoked from `PUBLIC` and granted only to its own role. nftables (`nftables-wac.nft`) drops packets from `wac-staging` to `fd20:ce::254` and `169.254.169.254`, so staging can't take the VM's (prod) token from the metadata server. DNS (port 53) to those addresses is still allowed, because the metadata server is also the VM's resolver. The token is only served over HTTP. Staging's email goes to the journal (console backend). The staging site sits behind Caddy basic auth and sends `X-Robots-Tag: noindex, nofollow`.

Staging basic auth: set the Terraform variable for metadata `wac-staging-basic-auth` to the output of `caddy hash-password` (user `staging`), or to `<user> <hash>`. Keep the password in 1Password. If the key is unset or isn't a bcrypt hash, staging is locked with a random password and prod is unaffected. Re-run `sudo wac-provision` after changing it.

## Database

- Nightly backup: `wac-backup.timer` runs at 03:30 America/Chicago (`Persistent=true`). It runs `pg_dump -Fc wac` as `wac` and uploads to `gs://<backup-bucket>/db/wac-<UTC yyyymmddTHHMMSS>.dump`. `ifGenerationMatch=0` means a backup never overwrites an existing object. The bucket lifecycle keeps 30 days. Run one now: `sudo systemctl start wac-backup`.
- Refresh staging from prod: `sudo wac-refresh-staging-db`. It refuses unless the staging env has the console `EMAIL_BACKEND` and `DB_NAME=wac_staging`. Then it:
  1. Dumps `wac` locally to a private temp file. It uses a file, not a pipe, because the TOC must be filtered first.
  2. Stops `wac-staging`, drops and recreates `wac_staging`.
  3. Restores as `wac_staging`.
  4. Runs `migrate` and starts staging.
- Every restore filters extensions out of the TOC (R11). The prod dump has `pg_stat_statements`, which a non-superuser can't create:

```sh
pg_restore -l dump | grep -v -E 'EXTENSION|COMMENT - EXTENSION' > toc
sudo -u wac pg_restore -L toc --no-owner --no-acl --role=wac -d wac dump
```

## Logs

```sh
journalctl -u wac-web -u wac-staging -f
journalctl -u 'wac-deploy@*' -u wac-backup -u caddy
journalctl -u google-startup-scripts    # provision.sh output (also on the serial console)
systemctl list-timers 'wac-*'
```

## Admin access (serial console)

There is no SSH (no rule, no port 80, no IPv4). To get in:

1. Set Terraform `serial_console = true` and set metadata `wac-serial-password-hash` to a crypt hash, for example `openssl passwd -6`.
2. Reboot, or re-run the startup script.
3. Connect with `gcloud compute connect-to-serial-port wac-web` and log in as `wacadmin` (a sudoer).

When the key is absent, `provision.sh` locks `wacadmin` (`usermod -p '!'`). Remove the key and turn the serial console off after use.

## Accepted risk: origin key in metadata

The Cloudflare Origin CA private key is the instance metadata key `wac-origin-key` (and in Terraform state). Anyone with project viewer access, and any process on the VM that can reach the metadata server, can read it. That is every user except `wac-staging`, which nftables blocks. The key only lets someone impersonate this origin to Cloudflare. Accepted.

## Checks for Task F (on the VM)

These are in addition to the plan's list:

- `curl -6 -sI https://secretmanager.googleapis.com` works. It isn't in the planning session's verified IPv6 host list.
- `sudo -u wac-staging curl -6 -m5 -H 'Metadata-Flavor: Google' http://metadata.google.internal/` fails.
- `sudo -u wac-staging getent hosts pypi.org` works (DNS still allowed for staging).
- `sudo -u wac-staging psql -U wac_staging -d wac_staging -c 'select 1'` works (peer map), and `sudo -u wac-staging psql -U wac_staging -d wac -c 'select 1'` fails (no CONNECT).
- `nft -c -f /etc/wac/nftables-wac.nft` passes. It was not checked locally (no nft on macOS).
- `systemd-analyze verify /etc/systemd/system/wac-*.service /etc/systemd/system/wac-deploy@.service`
- `caddy validate --adapter caddyfile --config /etc/caddy/Caddyfile`
- `sudo nft list table inet wac`
- `systemctl list-timers 'wac-*'` shows `wac-deploy@prod`, `wac-deploy@staging` and `wac-backup`.
