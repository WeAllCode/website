# Terraform: weallcode.org on a GCP e2-micro

One IPv6-only e2-micro VM (`wac-web`, Debian 12, us-central1-a), its buckets, secrets, service accounts, firewall, budget, and the Cloudflare DNS/TLS in front of it. The VM scripts live in `../vm/` (shipped to the VM as `bootstrap.tgz`, below).

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
4. `terraform plan` and review: e2-micro, 30 GB `pd-standard`, us-central1, `stack_type = IPV6_ONLY`, no `access_config`. Ali approves, then `terraform apply`.
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

Secrets (Secret Manager, auto replication): `wac-env-prod`, `wac-env-staging`, `wac-staging-sa-key`.

## Access model

| Identity | Grants |
|---|---|
| VM SA `wac-web` | media: objectAdmin; deploy: objectViewer; backups: objectCreator + objectViewer (no delete); transfer: objectViewer; secretAccessor on `wac-env-prod`, `wac-env-staging`, `wac-staging-sa-key` (root deploys both targets) |
| Staging SA `wac-staging-vm` | staging media: objectAdmin; secretAccessor on `wac-env-staging` only |
| `allUsers` | objectViewer on the prod and staging media buckets |

Buckets are all in `US-CENTRAL1`. Deploy: versioned, noncurrent versions beyond 5 deleted. Backups: objects deleted after 30 days. Transfer (one-off DB dumps, R12): not versioned, no soft delete, objects deleted after 1 day; `gcloud storage rm` each dump right after the restore. CORS `GET`: prod media from the apex, `www.` and `gcp.`; staging media from `staging.`.

## Switches

- `cutover` (default `false`): `false` points only `gcp.<domain>` and `staging.<domain>` at the VM. `true` adds the proxied apex AAAA and `www` CNAME (and an apex A when `enable_ipv4`). Delete the Heroku-era apex and `www` records by hand first, or the create fails on the duplicate name. Rollback: `cutover = false`, apply, recreate the Heroku records from `cloudflare-records-before.json`.
- `enable_ipv4` (default `false`): fallback when IPv6-only fails. Adds an external IPv4 (~$3.65/month) and a Cloudflare IPv4 firewall rule. The stack type is immutable, so this **replaces the VM** and wipes Postgres on its boot disk. `prevent_destroy` makes that plan fail on purpose. To go ahead: run `backup-db.sh`, verify the dump restores into a scratch DB, ask Ali, then temporarily remove the `lifecycle { prevent_destroy = true }` block, apply, restore the DB, and put the guard back.
- `serial_console` (default `false`): turns on the interactive serial console (`gcloud compute connect-to-serial-port wac-web`), the only admin path (no SSH, no IAP: IAP needs an internal IPv4). With `serial_console_password_hash` set (`openssl passwd -6`), the hash is passed as `wac-serial-password-hash` for a temporary local login. Turn both off after use; it's a Terraform change, not drift.
- `allow_all_member_domains` (default `false`): project-level `allow_all` override of `iam.allowedPolicyMemberDomains` (R3). Needs Org Policy Admin.

## Firewall and TLS

Ingress is TCP 443 from Cloudflare's IPv6 ranges only (plus its IPv4 ranges when `enable_ipv4`). Nothing on 80, no SSH. The zone SSL mode is `strict`; Caddy serves a Cloudflare Origin CA certificate (ECC, 15 years) for the apex, `www.`, `gcp.` and `staging.`. Its private key is in state (private, versioned bucket) and in instance metadata: accepted risk, see `../vm/README.md`.

## Checks

```sh
terraform fmt -check -recursive && terraform init -backend=false && terraform validate
```

`.terraform.lock.hcl` is committed with hashes for `darwin_arm64` and `linux_amd64` (CI). After changing provider versions: `terraform providers lock -platform=darwin_arm64 -platform=linux_amd64`.
