# Terraform: weallcode.org on a GCP e2-micro

One e2-micro VM (`wac-web`, Debian 12, us-central1-a; dual-stack nic0 with an internal IPv4 but public over IPv6 only), its buckets, secrets, service accounts, firewall, budget, and the Cloudflare DNS/TLS in front of it. The VM scripts live in `../vm/` (shipped to the VM as `bootstrap.tgz`, below).

Everything here is managed by Terraform except the state bucket, the billing account, the gmail project owner (imported later), secret versions, the staging SA key, and the Google Workspace MX/SPF records.

## Credentials

Always use the separate `wac` gcloud configuration and an access token, never ADC:

```sh
export CLOUDSDK_ACTIVE_CONFIG_NAME=wac
gcloud config get account   # must print ali@weallcode.org
gcloud config get project   # must print the We All Code project
export GOOGLE_OAUTH_ACCESS_TOKEN="$(gcloud auth print-access-token)"
export CLOUDFLARE_API_TOKEN="$(op read 'op://<vault>/Cloudflare weallcode Terraform/credential')"
```

Stop if either `gcloud config get` prints the Braven account or `braven-data-infra`.

## Bootstrap (first time)

1. Checkpoint 0b creates the project, links billing, and creates the state bucket by hand: `gcloud storage buckets create gs://wac-tfstate-<project_id> --location=us-central1 --uniform-bucket-level-access --public-access-prevention` then `gcloud storage buckets update gs://wac-tfstate-<project_id> --versioning`.
2. `cp terraform.tfvars.example terraform.tfvars` and fill it in (it is gitignored). `resend_dns_records` comes from the Resend API response in 0b. Set `allow_all_member_domains = true` only if 0b found `iam.allowedPolicyMemberDomains` enforced.
3. `terraform init -backend-config="bucket=wac-tfstate-<project_id>"`
4. `terraform plan` and review: e2-micro, 30 GB `pd-standard`, us-central1, `stack_type = IPV4_IPV6`, no `access_config`. Ali approves, then `terraform apply`.
5. Right after the first apply, check `https://www.weallcode.org` (still Heroku) loads under `ssl = strict`.
6. Add secret versions (Terraform never creates versions, so no values land in state). Pipe them in, never write them to a file in the repo: `... | gcloud secrets versions add wac-env-prod --data-file=-` and the same for `wac-env-staging`. Keep at most 2 versions per secret (free tier: 6 active versions); destroy the older one after adding a new one.
7. Staging SA key (R10). Ali or the lead creates it with gcloud and pipes it straight into the secret (the key never lands in Terraform state or on disk):

   ```sh
   gcloud iam service-accounts keys create /dev/stdout \
     --iam-account="wac-staging-vm@<project_id>.iam.gserviceaccount.com" \
     | gcloud secrets versions add wac-staging-sa-key --data-file=-
   ```

   If key creation fails with `iam.disableServiceAccountKeyCreation` (enforced by default on orgs created after May 2024), stop and ask Ali; it needs a project-level override of that constraint, which this config does not include. The same secure-by-default orgs may enforce `storage.publicAccessPrevention`, which blocks `allUsers` on the media buckets even with the R3 override (the bucket's `inherited` setting yields to it). Check both with `gcloud resource-manager org-policies describe constraints/<name> --effective --project=<project_id>` alongside R3's check in 0b.
8. The gmail owner (R2): Ali invites `daniel.m.conrad@gmail.com` as Owner in the console. After he accepts, add `"user:daniel.m.conrad@gmail.com"` to `project_owners` in `terraform.tfvars` and run `terraform import 'google_project_iam_member.owners["user:daniel.m.conrad@gmail.com"]' "<project_id> roles/owner user:daniel.m.conrad@gmail.com"`. Then `terraform plan` must show no changes.

## What reaches the VM

`provision.sh` is the startup script (metadata `startup-script`); it runs on every boot. It downloads `gs://wac-deploy-<project_id>/bootstrap.tgz` with the metadata token and installs the rest of `infra/vm/` from it.

`bootstrap.tgz` is a gzipped tar built by `data "archive_file"` from `infra/vm/` into `infra/terraform/.build/bootstrap.tgz` (gitignored) at plan time, and uploaded as object `bootstrap.tgz` in the deploy bucket. Any file change re-uploads it on the next apply. Files named `env.*` are excluded unless they end in `.example`. File modes are kept from the checkout, so scripts keep their executable bit. Changes to `startup-script` take effect only on the next boot (`gcloud compute instances reset wac-web`, or re-run it over the serial console).

Instance metadata keys the VM reads:

| Key | Value |
|---|---|
| `startup-script` | `infra/vm/provision.sh` |
| `serial-port-enable` | `TRUE` when `serial_console`, else `FALSE` |
| `serial-port-logging-enable` | `TRUE` |
| `enable-oslogin` | `TRUE` |
| `wac-media-bucket` | prod media/static bucket (`var.media_bucket_name`) |
| `wac-staging-media-bucket` | `wac-staging-media-<project_id>` |
| `wac-deploy-bucket` | `wac-deploy-<project_id>` (releases, `current-<target>` pointers, `bootstrap.tgz`) |
| `wac-backup-bucket` | `wac-backups-<project_id>` |
| `wac-transfer-bucket` | `wac-transfer-<project_id>` |
| `wac-origin-cert` | Cloudflare Origin CA certificate (PEM) |
| `wac-origin-key` | its ECDSA P-256 private key (PEM) |
| `wac-staging-basic-auth` | `var.staging_basic_auth_hash` (bcrypt, from `caddy hash-password`) |
| `wac-serial-password-hash` | `var.serial_console_password_hash`, present only while `serial_console = true` and the hash is set |
| `deploy-nonce-prod`, `deploy-nonce-staging` | not Terraform's: `infra/vm/release.sh` sets them (`gcloud compute instances add-metadata`) to trigger `wac-deploy-watch`; listed in `lifecycle.ignore_changes` so they never show as drift |

Secrets (Secret Manager, auto replication): `wac-env-prod`, `wac-env-staging`, `wac-staging-sa-key`.

## Access model

| Identity | Grants |
|---|---|
| VM SA `wac-web` | media: objectAdmin; deploy: objectViewer; backups: objectCreator + objectViewer (no delete); transfer: objectViewer; secretAccessor on `wac-env-prod`, `wac-env-staging`, `wac-staging-sa-key` (root deploys both targets) |
| Staging SA `wac-staging-vm` | staging media: objectAdmin; secretAccessor on `wac-env-staging` only |
| `allUsers` | legacyObjectReader (`storage.objects.get` only, no listing) on the prod and staging media buckets |

Buckets are all in `US-CENTRAL1`. Deploy: versioned, noncurrent versions beyond 5 deleted. Backups: objects deleted after 30 days. Transfer (one-off DB dumps, R12): not versioned, no soft delete, objects deleted after 1 day; `gcloud storage rm` each dump right after the restore. CORS `GET`: prod media from the apex, `www.` and `gcp.`; staging media from `staging.`.

## Switches

- `cutover` (default `false`): `false` points only `gcp.<domain>` and `staging.<domain>` at the VM. `true` adds the proxied apex AAAA and `www` CNAME (and an apex A when `enable_ipv4`). Delete the Heroku-era apex and `www` records by hand first, or the create fails on the duplicate name. Rollback: `cutover = false`, apply, recreate the Heroku records from `cloudflare-records-before.json`.
- `enable_ipv4` (default `false`): fallback when IPv6-only ingress fails. Adds an external IPv4 (~$3.65/month) and a Cloudflare IPv4 firewall rule. nic0 is always dual-stack (internal IPv4); this only adds the `access_config`, but changing it still **recreates the instance**. `prevent_destroy` makes that plan fail on purpose; use the instance swap below.
- `iap_ssh` (default `true`): firewall rule `wac-ssh-iap` allowing TCP 22 from IAP's TCP-forwarding range `35.235.240.0/20` only (SSH via `gcloud compute ssh --tunnel-through-iap`, see `../vm/README.md`).
- `serial_console` (default `false`): turns on the interactive serial console (`gcloud compute connect-to-serial-port wac-web`), the fallback admin path when IAP SSH is down. With `serial_console_password_hash` set (`openssl passwd -6`), the hash is passed as `wac-serial-password-hash` for a temporary local login. Turn both off after use; it's a Terraform change, not drift.
- `allow_all_member_domains` (default `false`): project-level `allow_all` override of `iam.allowedPolicyMemberDomains` (R3). Needs Org Policy Admin.

## Instance swap (keep the boot disk)

Postgres lives on the boot disk `google_compute_disk.web` (`prevent_destroy`, `auto_delete = false`). Any change that recreates the instance (stack type, `enable_ipv4`, …) is done by hand so Terraform never deletes the VM itself. First run `backup-db.sh`, verify the dump restores into a scratch DB, and ask Ali. Then:

```sh
# only if the disk isn't in state yet
terraform import google_compute_disk.web projects/<project_id>/zones/us-central1-a/disks/wac-web
gcloud compute instances stop wac-web --zone us-central1-a
gcloud compute snapshots create wac-web-pre-swap-$(date +%Y%m%d) --source-disk wac-web --source-disk-zone us-central1-a
gcloud compute instances delete wac-web --zone us-central1-a --keep-disks=boot
terraform state rm google_compute_instance.web
terraform plan    # must create the instance and show no change to google_compute_disk.web
terraform apply
```

Delete the snapshot once the site and DB check out.

## Firewall and TLS

Ingress is TCP 443 from Cloudflare's IPv6 ranges only (plus its IPv4 ranges when `enable_ipv4`), and TCP 22 from IAP's `35.235.240.0/20` only (when `iap_ssh`). Nothing on 80. The zone SSL mode is `strict`; Caddy serves a Cloudflare Origin CA certificate (ECC, 15 years) for the apex, `www.`, `gcp.` and `staging.`. Its private key is in state (private, versioned bucket) and in instance metadata: accepted risk, see `../vm/README.md`.

## Edge cache

`cache.tf` adds one cache rule (`cloudflare_ruleset.cache`) for the apex and `www.` only; `gcp.` and `staging.` are never cached. Requests with a `sessionid` or `messages` cookie, and paths under `/admin/`, `/dj-admin/` and `/account/`, skip it. The rule respects the origin's headers, so the real gate is `coderdojochi/middleware.py`: allowlisted pages served to logged-out visitors with no cookies get `public, max-age=0, s-maxage=60` (60 s at the edge, `PUBLIC_CACHE_SECONDS`), and everything else gets `private` and is never cached. Never switch the rule to `override_origin`.

Kill switch: set `PUBLIC_CACHE_SECONDS=0` in the `wac-env-prod` secret and release (every response becomes `private`), or delete `cache.tf` and apply.

Query strings: the cache key includes the query string, and Free can't ignore it in a cache rule, so every unique `?utm_…`, `?fbclid=…`, `?gclid=…` or Mailchimp `?mc_eid=…` link (or a random `?x=…`) would be a cache miss. `transform.tf` adds one URL-rewrite Transform Rule (`cloudflare_ruleset.transform`, rule `strip_query_public_html`) that removes the query string before the cache lookup, only for logged-out (no `sessionid` or `messages` cookie) GET and HEAD requests to the apex and `www.` on the allowlisted public paths: `/`, `/our-story/`, `/programs/`, `/programs/summer-camps/`, `/team/`, `/join-us/associate-board/`, `/privacy/`, `/credits/`, `/mentors/` and `/mentors/<pk>/` (not the `-avatar/` staff actions). None of those views read `request.GET`, and GA4 still sees the campaign parameters in the browser URL. The path list mirrors `PUBLIC_CACHE_VIEW_NAMES` in `coderdojochi/middleware.py`; change both together (`test_rewrite_paths_match_allowlist` in `weallcode/tests.py` checks it). Kill switch: set `enabled = false` on the rule and apply. Write campaign links with the trailing slash: without it, Django's `APPEND_SLASH` 301 runs at the origin on every click.

Manual purge (the token needs the "Cache Purge" permission; Free allows 5 purge-everything calls per minute):

```sh
curl -X POST "https://api.cloudflare.com/client/v4/zones/<zone_id>/purge_cache" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"purge_everything":true}'
```

## WAF and rate limit

`waf.tf` stops vulnerability scanners at the edge (`docs/plans/scanner-defense.md`). Caddy's probe 404 is the origin backstop behind it. Both rulesets apply to every host (apex, `www.`, `gcp.`, `staging.`). `cloudflare_ruleset.waf_custom` has four custom rules, all `block` (403), using 4 of the 5 Free custom rules (1 spare):

- `block_probe_extensions`: paths ending in a probe extension (`.php`, `.env`, `.asp`, `.jsp`, `.sql`, `.bak`, `.zip`, `.log`, `.ini`, `.conf`, `.pem`, `.key`, `.yml`, `.json`, `.js`, `.xml`, `.txt` …). Exempt: `/robots.txt`, `/sitemap.xml` and anything under `/.well-known/`. In prod, static and media files come from `storage.googleapis.com`, not the site's hosts, so real `.js`/`.json` assets never hit this rule.
- `block_dotfiles`: any path containing `/.` (`/.env`, `/.git/config`, `/.aws/credentials` …), except `/.well-known/`.
- `block_other_stacks`: paths of stacks this site doesn't run: WordPress (`/wp-`, `/wordpress`, `/xmlrpc`), phpMyAdmin (`/phpmyadmin`, `/pma/`), Spring (`/actuator`), `/cgi-bin`, Composer (`/vendor/`), Laravel (`/telescope`, `/_ignition`), Symfony (`/_profiler`), Vite (`/@fs/`), `/phpinfo`.
- `block_probe_names`: editor backups ending in `~`, plus an exact list of probe names (`/Dockerfile`, `/id_rsa`, `/credentials`, `/metrics`, `/health`, `/status`, `/version`, `/graphql`, `/server-status` …). `in` is case-sensitive, Free has no regex and `lower()` isn't confirmed for Free, so the names are written as scanners send them; Caddy catches other casings.

`cloudflare_ruleset.ratelimit` has one rule, `per_ip_60_per_10s`: an IP that sends more than 60 requests in 10 s to one Cloudflare data center is blocked for 10 s. Free allows a 10 s period and 10 s timeout, and `cf.colo.id` must be a characteristic. Cached hits count too. Why 60 per 10 s: it is below the VM's ~120 uncached requests per 10 s, it catches the scanner bursts seen on 2026-11-25 (~470 and ~67 per 10 s), and it leaves room for a classroom behind one NAT (static and media come from `storage.googleapis.com`, so a page view is about one request to weallcode.org). `/anymail/` (Resend webhooks) is exempt. Free allows only path fields in the expression: never add host or response fields.

Kill switch: set `enabled = false` on the rule and apply. Deleting a rule or ruleset in the dashboard also works, but then `terraform plan` shows drift; re-apply or re-import.

Load test: set `enabled = false` on `per_ip_60_per_10s` and apply first, or the test IP gets 429s after 60 requests. Re-enable and apply afterwards.

Blocks show in the dashboard under Security → Events (filter by rule). Bot Fight Mode is off on purpose: on Free it can't be skipped by WAF rules, covers the whole domain, and may challenge `/anymail/` webhooks and uptime monitors. Never add IP or ASN blocks for cloud ranges: the 2026-11-25 scanner came from a Google Cloud IP and cloud IPs rotate, while the same ranges carry Resend webhooks and uptime monitors.

## Checks

```sh
terraform fmt -check -recursive && terraform init -backend=false && terraform validate
```

`.terraform.lock.hcl` is committed with hashes for `darwin_arm64` and `linux_amd64` (CI). After changing provider versions: `terraform providers lock -platform=darwin_arm64 -platform=linux_amd64`.
