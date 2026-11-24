# Plan: move weallcode.org from Heroku to a free GCP e2-micro (IPv6-only)

Status: planned 2026-11-23. Not started. Branch: `claude/heroku-free-hosting-migration-a21bab`.

## Goal and done

**User story:** As the We All Code admin, I want the existing Django site (same pages, logins, admin, data) running on one Google Cloud free-tier e2-micro VM built by Terraform, with Cloudflare in front, so the nonprofit stops paying Heroku $56.75/month and pays $0.

**Decisions already made (do not reopen):**

- Host: one GCP e2-micro VM, Debian 12, us-central1, 30 GB `pd-standard` disk. Everything runs natively (no Docker): Postgres, gunicorn via systemd, Caddy.
- Network: IPv6-only VM (no external IPv4, which costs ~$3.65/month). Cloudflare proxies to the VM over IPv6. Fallback if IPv6-only fails: flip one Terraform variable to add an IPv4 (accepted cost ~$3.65/month), and record that in Progress.
- GCP account: `ali@weallcode.org`, new project, We All Code's card. Never use the `ali.karbassi@bebraven.org` account or the `braven-data-infra` project that gcloud on this Mac defaults to.
- Infra as code: Terraform (hashicorp/google `~> 8.11`, cloudflare/cloudflare `~> 5.29`, hashicorp/tls), state in a private, versioned GCS bucket.
- Media and static files: move from AWS S3 to a public GCS bucket (244 MB, 1,973 objects today).
- Email: Resend free plan (100/day, 3,000/month) through django-anymail, replacing SendGrid (a Heroku add-on that dies with Heroku).
- Errors: keep Sentry. Try to transfer the existing Heroku-provisioned org's project to a new direct free org; apply for Sentry for Good (nonprofit).
- Code base: deploy `main` (Django 5.2), not the 2022 code that Heroku runs today (Django 4.0.6, commit `479939c`).
- Access (decided 2026-11-24): GCP project owners are `ali@weallcode.org`, `hello@weallcode.org` and `daniel.m.conrad@gmail.com`, managed in Terraform (`google_project_iam_member`, `roles/owner`). Owner invites to a non-org Gmail account need the invitee to accept by email.
- Uptime (decided 2026-11-24): one Sentry free-plan uptime monitor on `https://www.weallcode.org/`, alerting by email. Set up after cutover (Task H).
- Old AWS S3 bucket (decided 2026-11-24): keep 30 days after cutover as a rollback copy, then the builder (with Ali's OK) deletes it and checks the AWS account for anything else that bills.
- Deploys (decided 2026-11-24): manual, `infra/vm/release.sh --target prod|staging` from Ali's laptop. No auto-deploy on merge.
- Secrets (decided 2026-11-24): GCP Secret Manager holds one secret per environment, `wac-env-prod` and `wac-env-staging`, each an entire env file. The VM reads the latest version at deploy time. The free tier covers 6 active secret versions and 10,000 access operations a month, so after adding a new version, destroy the previous one (keep at most 2 per secret).
- PR checks and staging (decided 2026-11-24): (1) a GitHub Actions CI workflow on every PR (free for this public repo) runs lint, tests, migrations against a Postgres 17 service container, `check --deploy`, and a boot + smoke test; (2) `staging.weallcode.org` runs on the same VM (1 gunicorn worker, its own database `wac_staging` restored from the nightly prod backup, its own media bucket, behind Caddy basic auth, `X-Robots-Tag: noindex`, and email sent only to the console log so real users are never emailed). Ali deploys a PR branch to staging on demand. Rejected: per-PR review apps on Cloud Run + Neon (adds a vendor, differs from prod) and a second VM (not free). Memory budget with staging: prod ~220 MB + staging ~110 MB + Postgres ~120 MB + Caddy ~30 MB + OS ~150 MB ≈ 630 MB of 1 GB, plus 1 GB swap.
- Code delivery (decided 2026-11-24): one PR from this branch, one commit per checkpoint, merged before cutover. A second small PR after day 7 removes the Heroku-only files (`Procfile`, `app.json`, the `release` task in `tasks.py`).
- Scheduled jobs: none. `django_cron` is not in `INSTALLED_APPS` and Heroku has no scheduler, so `coderdojochi/cron.py` never runs today. Keep it that way.

**Acceptance criteria:**

1. AC1: `https://www.weallcode.org` and `https://weallcode.org` are served by the GCP VM through Cloudflare, and the home page, `/programs/`, `/team/`, login, and `/admin/` work with the real data.
2. AC2: Static files and uploaded media load from the GCS bucket (`https://storage.googleapis.com/<bucket>/...`); uploading an image in admin stores it in GCS.
3. AC3: Email sends through Resend from `hello@weallcode.org`, and each recipient of a merged email gets their own values (no `*|field|*` left in the body).
4. AC4: A missing or unreachable Slack webhook never breaks a save (mentor signup, mentor order).
5. AC5: `terraform plan` on a clean checkout shows no changes after apply, and every GCP/Cloudflare resource is in Terraform except the state bucket and the billing account.
6. AC6: The GCP billing report shows $0.00 for the project 3 days after cutover (or, if the IPv4 fallback was used, only the IPv4 SKU).
7. AC7: The production database on the VM has every table and row count of the final Heroku backup.
8. AC8: Heroku `production-wac` is in maintenance mode, then deleted by Ali after 7 days of the new site running (Ali does the delete, not the builder).
9. AC9: A nightly database backup lands in the private backup bucket, and a backup restores into a scratch database with the same row counts.

**Django version:** stay on Django 5.2 LTS (decided 2026-11-24). Per https://www.djangoproject.com/download/ ("Supported Versions"), 5.2 LTS gets security fixes until April 2028, while the latest, 6.1, ends in December 2027; 6.x also needs Python 3.12+ and would mean dropping `django-nose` and replacing stale packages (`django-html5` 2012, `django-common-helpers` 2018, `django-stdimage` 2023, `django-fullurl` 2023). Follow-up after this plan, as its own project: upgrade to Django 6.2 LTS (due April 2027, supported to April 2030) on a Debian 13 / Python 3.13 VM.

**Other Heroku apps (decided 2026-11-24):** delete `wac-nocodb`, `wac-robot-hub` and `wacdrop` on day 7 alongside `production-wac`, then cancel the Eco dynos plan, so the Heroku bill reaches $0. Research found: `wac-nocodb` was a NocoDB one-click install whose Postgres Heroku detached on 2022-12-12 (free-tier shutdown), so no data is left; `wac-robot-hub` was a 2019 Mosquitto MQTT broker for the old NodeMCU robots, unused since 2020, with all four deployed commits on GitHub (`weallcode/robot-hub` master); `wacdrop` was created 2022-05-26 and never deployed. Backed up 2026-11-24 to `~/Projects/we-all-code/heroku-backup-2026-11-23/`: config vars (`config/`), app info, add-ons, domains, releases (text and API JSON), formation (`meta/`). Their container images were already purged from Heroku's registry (`MANIFEST_UNKNOWN` / `BLOB_UNKNOWN`), so none could be saved. The GitHub robot repos stay as they are.

**Out of scope:** the Django upgrade above; archiving GitHub repos; fixing the two pre-existing broken tests; Django/allauth deprecation warnings; turning on `django_cron`; CI/CD.

## Read first

Files (paths from repo root):

- `coderdojochi/settings.py:31-79` — security settings. `DJANGO_SECURE_SSL_REDIRECT` is `False` in prod today (Cloudflare does HTTPS); keep that.
- `coderdojochi/settings.py:161-186` — database config. `DATABASE_URL` forces `ssl_require=True`; on the VM use the `DB_*` vars over the Unix socket instead, so leave `DATABASE_URL` unset.
- `coderdojochi/settings.py:236-328` — static/media. The non-DEBUG branch is broken on main: it imports `SpooledTemporaryFile` from `storages.backends.s3boto3` (removed in django-storages 1.14) and uses `STATICFILES_STORAGE` / `DEFAULT_FILE_STORAGE` (removed in Django 5.1). Running `DEBUG=False` crashes at import. This whole block gets replaced.
- `coderdojochi/settings.py:367-375` — email. Hard-wired SendGrid backend and required `SENDGRID_*` env vars.
- `coderdojochi/settings.py:377-379` — Slack env vars (`SLACK_WEBHOOK_URL` required today).
- `coderdojochi/settings.py:381-397` — Sentry init; unchanged, it only needs a new `SENTRY_DSN`.
- `coderdojochi/settings.py:404-426` — debug toolbar under DEBUG, and `django_heroku.settings(locals(), staticfiles=False)`. With `staticfiles=False` that call only sets: DATABASES from `DATABASE_URL` (unused on the VM), `ALLOWED_HOSTS=['*']` (already set at line 234), a console `LOGGING` dict, and a CI-only test runner. Source: `.venv/lib/python3.11/site-packages/django_heroku/core.py`.
- `coderdojochi/util.py:14-99` — `email()`: renders a template, relies on SendGrid merge tags `*|key|*` (`merge_field_format`), `esp_extra` categories, and `asm` unsubscribe groups. Resend supports none of these (anymail docs: "no stored templates or merge_data").
- `coderdojochi/emailtemplates/_email_base.html:92-96` — SendGrid unsubscribe links, shown only when `unsub_group_id` is truthy. With `SENDGRID_UNSUB_CLASSANNOUNCE` unset they disappear; no template edit needed.
- `coderdojochi/notifications.py:9-29` — `SlackNotification.send()`: `requests.post` with no timeout and no exception handling. Slack has no IPv6 (`hooks.slack.com` has no AAAA record), so on this VM it raises and breaks the save that called it.
- `coderdojochi/models/mentor.py:103,113` and `coderdojochi/models/mentor_order.py:62` — callers of Slack notifications inside model saves.
- `coderdojochi/custom_storages.py` — dead code (imports `storages.backends.s3boto`, referenced nowhere). Leave it alone.
- `pyproject.toml:10-68` — dependencies. `django-heroku` pulls in `psycopg2` (source build). `boto3` is only used by the S3 storage being removed.
- `tasks.py` — Heroku release steps (`collectstatic`, `migrate`). The VM deploy script replaces them.
- `Procfile` — today's gunicorn command: `gunicorn coderdojochi.wsgi --preload`.
- `.gitignore` — add Terraform entries.
- `.pre-commit-config.yaml` — ruff check/format and `detect-private-key`; `docs/` is excluded.

Facts established in the planning session (2026-11-23), with evidence:

- Prod DB: Postgres 17, 35.5 MB, 50 tables. Verified backup: `~/Projects/we-all-code/heroku-backup-2026-11-23/production-wac.dump`. All Heroku config vars: `.../config/production-wac.env` (secrets, mode 600, outside the repo).
- `main` against a copy of the prod DB: all pages render; 11 migrations not yet applied in prod (allauth `account` 0003–0009, `coderdojochi.0040_alter_mentor_avatar`, `socialaccount` 0004–0006). They all applied cleanly on a restored copy.
- Load test of `main` on the prod data copy (2 gunicorn workers, debug toolbar off): ~100 MB per worker, ~18 MB master, ~16 ms CPU/request on an M-series Mac. The e2-micro has 1 GB RAM, so 2 workers + Postgres + Caddy fit.
- Existing tests: only 2, both erroring before this work (`coderdojochi/tests/`). Tests must run with `DEBUG=False` or without the debug toolbar (`debug_toolbar.E001`).
- IPv6 reachability (AAAA records exist): deb.debian.org, security.debian.org, apt.postgresql.org, dl.cloudsmith.io (Caddy), pypi.org, files.pythonhosted.org, storage.googleapis.com, oauth2.googleapis.com, api.resend.com, `o161345.ingest.sentry.io` (Sentry DSN host), accounts.google.com, graph.facebook.com, www.google.com (reCAPTCHA), api.cloudflare.com. **No IPv6:** github.com and its download hosts, hooks.slack.com, paypal (PayPal is client-side only; the server never calls it).
- So the VM cannot `git clone` from GitHub, cannot download uv's standalone installer or uv-managed Pythons (GitHub-hosted). Use Debian 12's system Python 3.11 and install uv from PyPI. Ship code to the VM through GCS (pull-based deploy, below).
- External IPv4 on a VM costs $0.005/hour (~$3.65/month); the free tier covers 1 hour/month. External IPv6 is free: "You are not charged for external IPv6 address ranges that are assigned to subnets or for external IPv6 addresses that are assigned to VM instances." Source for both: https://cloud.google.com/vpc/network-pricing, section "External IP address pricing" (verified 2026-11-23 from the page HTML). Traffic out over IPv6 still counts as internet egress against the VM's 1 GB/month free allowance.
- Terraform fields verified 2026-11-23 against `terraform providers schema -json` (hashicorp/google 8.12.0, cloudflare 5.29.0) and the Compute API discovery document: `google_compute_subnetwork.stack_type` accepts `IPV4_ONLY`, `IPV4_IPV6`, `IPV6_ONLY`, with `ipv6_access_type = "EXTERNAL"`; the instance's `network_interface.stack_type` maps to the API's `NetworkInterface.stackType`, whose enum includes `IPV6_ONLY` (`terraform validate` does not check this value, so a typo only shows at `plan`/`apply`); `ipv6_access_config` takes `network_tier`, `external_ipv6`, `external_ipv6_prefix_length`, `name`, `public_ptr_domain_name`. A minimal IPv6-only subnet + e2-micro config passes `terraform validate`. Cloudflare: `cloudflare_dns_record` (`zone_id`, `name`, `type`, `content`, `proxied`, `ttl`), `cloudflare_zone_setting` (`zone_id`, `setting_id`, `value`), `cloudflare_origin_ca_certificate` (`csr`, `hostnames`, `request_type`, `requested_validity`), data source `cloudflare_ip_ranges` (`ipv4_cidrs`, `ipv6_cidrs`). Google provider supports `access_token`, `billing_project`, `user_project_override`; `google_billing_budget` has `billing_account`, `amount`, `budget_filter`, `threshold_rules`, `all_updates_rule`.
- The SendGrid API key in the backup config still works (2026-11-23): 500+ unsubscribes (first page is full, so paginate), 416 bounces, 0 blocks, 74 spam reports, 1 unsubscribe group.
- Heroku Sentry/SendGrid accounts are tied to the Heroku add-ons; removing the add-on can delete them.

Docs (read the named section before the related task):

- Free tier limits: https://docs.cloud.google.com/free/docs/free-cloud-features, section "Free Tier usage limits" (e2-micro in us-central1/us-west1/us-east1, 30 GB-month pd-standard, 1 GB egress; GCS 5 GB-month US regions, 5k Class A / 50k Class B ops).
- IPv6 VMs: https://docs.cloud.google.com/compute/docs/ip-addresses/configure-ipv6-address — "IPv6-only instances are supported with only Ubuntu and Debian OS images", "You can't change the stack type of an IPv6-only instance" (so the IPv4 fallback recreates the VM), and the implied IPv6 deny-ingress rule.
- Terraform google provider: `google_compute_instance` (use `metadata = { startup-script = ... }`, not `metadata_startup_script`, which forces recreation), `google_compute_network`, `google_compute_subnetwork`, `google_compute_firewall`, `google_storage_bucket`, `google_storage_bucket_iam_member`, `google_billing_budget` (needs `billing_project` and `user_project_override = true` on the provider with user credentials), `google_project_service`. The registry pages are JS-rendered; get exact field names with `terraform providers schema -json | jq` after `terraform init`.
- Cloudflare provider v5 upgrade guide: https://registry.terraform.io/providers/cloudflare/cloudflare/latest/docs/guides/version-5-upgrade (`cloudflare_dns_record` with full-FQDN `name`; `cloudflare_zone_setting` per setting; `cloudflare_origin_ca_certificate`; data source `cloudflare_ip_ranges` with `ipv4_cidrs` / `ipv6_cidrs`).
- Cloudflare Origin CA: https://developers.cloudflare.com/ssl/origin-configuration/origin-ca/ (section "API calls": token needs Zone > SSL and Certificates > Edit).
- Terraform GCS backend: https://developer.hashicorp.com/terraform/language/backend/gcs (bucket must exist first; enable versioning).
- Caddy install on Debian: https://caddyserver.com/docs/install, section "Debian, Ubuntu, Raspbian" (cloudsmith repo; add `--batch --yes` to `gpg` in scripts).
- PostgreSQL apt repo (for PG 17 on Debian 12): https://www.postgresql.org/download/linux/debian/ (the `apt.postgresql.org` setup script section). Needed because the dump is from PG 17 and Debian 12 ships PG 15.
- django-storages GCS: https://django-storages.readthedocs.io/en/latest/backends/gcloud.html, sections "Configuration & Settings" and "Authentication Settings". Backend `storages.backends.gcloud.GoogleCloudStorage`; credentials from the VM's service account (ADC); with uniform bucket-level access keep `default_acl=None` and set `querystring_auth=False`.
- Django `STORAGES` setting: https://docs.djangoproject.com/en/5.2/ref/settings/#storages.
- Anymail Resend: https://anymail.dev/en/stable/esps/resend/ — `EMAIL_BACKEND = "anymail.backends.resend.EmailBackend"`, `ANYMAIL = {"RESEND_API_KEY": ...}`, extra `django-anymail[resend]`, limitations (no merge_data, no templates).
- Anymail test backend for tests: https://anymail.dev/en/stable/tips/testing/ (`anymail.backends.test.EmailBackend`, messages in `django.core.mail.outbox`).
- Resend DNS on Cloudflare: https://resend.com/docs/dashboard/domains/cloudflare (which records Resend needs). Resend API: https://resend.com/docs/api-reference/domains/create-domain, `.../verify-domain`, `.../get-domain`, and https://resend.com/docs/api-reference/api-keys/create-api-key. Checkpoint 0b uses the API and puts the records in Terraform instead of the dashboard's Domain Connect button, so they're tracked in code.
- Sentry project transfer: https://docs.sentry.io/product/teams/roles/ (Owner needed). Sentry for Good: https://sentry.io/for/good.
- SendGrid export before closing: https://www.twilio.com/docs/sendgrid/for-developers/partners/account-migration and the Suppressions API https://www.twilio.com/docs/sendgrid/api-reference/suppressions-suppressions.

Existing code to copy:

- Test settings pattern: `/tmp/e2micro/e2settings.py` from the planning session (import `coderdojochi.settings`, strip `debug_toolbar` from `INSTALLED_APPS` and `MIDDLEWARE`). If `/tmp` was cleared, the code is in Task A below.
- Storage subclass pattern: `coderdojochi/settings.py:293-323` (manifest mixin on a storages backend, separate `location` for static and media).
- Logging dict to keep: `django_heroku/core.py` `config['LOGGING']` (console handler, `verbose` formatter).
- Gunicorn command: `Procfile` line `web:`.

## Tasks

Paths are from repo root. "Proof" is the command the task's sub-agent runs before reporting.

### Task A — Django settings, storage, dependencies (Checkpoint 1)

Owns: `coderdojochi/settings.py`, new `coderdojochi/storage_backends.py`, new `coderdojochi/test_settings.py`, `pyproject.toml`, `uv.lock`, new `coderdojochi/tests/test_storage_settings.py`.

Change:

1. `pyproject.toml`: remove `django-heroku` and `boto3`; add `dj-database-url>=2.0,<4.0` explicitly (it only came in through `django-heroku`, and `settings.py:15` imports it); change `django-storages` to `django-storages[google]` and `django-anymail` to `django-anymail[resend]` (same version ranges). Run `uv lock`. Confirm `psycopg2` is gone from `uv.lock` (`grep -c 'name = "psycopg2"' uv.lock` → 0) and `dj-database-url` is still there.
2. `coderdojochi/storage_backends.py`: two classes based on `storages.backends.gcloud.GoogleCloudStorage`: `StaticStorage(ManifestFilesMixin, GoogleCloudStorage)` with `location = "static"`, and `MediaStorage(GoogleCloudStorage)` with `location = "media"` and `file_overwrite = False`. Keep the `media/` and `static/` prefixes: DB file fields store names relative to the location, so the copied S3 objects keep working.
3. `coderdojochi/settings.py` lines 253-328 (non-DEBUG branch): replace with `INSTALLED_APPS += ["storages"]`, `GS_BUCKET_NAME = env("GS_BUCKET_NAME")`, and a Django 5.2 `STORAGES` dict: `default` → `coderdojochi.storage_backends.MediaStorage`, `staticfiles` → `coderdojochi.storage_backends.StaticStorage`, both with `OPTIONS` `{"bucket_name": GS_BUCKET_NAME, "default_acl": None, "querystring_auth": False, "object_parameters": {"cache_control": "public, max-age=604800"}}`. Set `STATIC_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/static/"` and `MEDIA_URL = f"https://storage.googleapis.com/{GS_BUCKET_NAME}/media/"`. Keep the DEBUG branch (lines 236-251) as is.
4. Email block (lines 367-375): `EMAIL_BACKEND = env("EMAIL_BACKEND", default="anymail.backends.resend.EmailBackend")`, `ANYMAIL = {"RESEND_API_KEY": env("RESEND_API_KEY", default="")}`, and `SENDGRID_UNSUB_CLASSANNOUNCE = env.int("SENDGRID_UNSUB_CLASSANNOUNCE", default=None)`. Keep `DEFAULT_FROM_EMAIL` and `CONTACT_EMAIL` required.
5. Slack (line 378): `SLACK_WEBHOOK_URL = env("SLACK_WEBHOOK_URL", default="")`.
6. Delete `import django_heroku` (line 16) and the call at line 426. Add the `LOGGING` dict copied from `django_heroku/core.py` (console handler, verbose formatter) so logs still go to stdout/journald. Leave `import dj_database_url` and the `DATABASE_URL` block.
7. `coderdojochi/test_settings.py`: before the import, `os.environ.setdefault(...)` for every required var (`DEBUG=False`, `SECRET_KEY`, `GS_BUCKET_NAME=wac-test-bucket`, `DEFAULT_FROM_EMAIL`, `CONTACT_EMAIL`, `SITE_URL=http://testserver`), because settings never call `read_env` and `DEBUG` defaults to False. Then `from coderdojochi.settings import *`, remove `debug_toolbar` from `INSTALLED_APPS` and `MIDDLEWARE` if present (copy `/tmp/e2micro/e2settings.py`), and override: `DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}}` so tests need no Postgres; `STORAGES = {"default": {"BACKEND": "django.core.files.storage.InMemoryStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}}` because the email templates call `{% static %}` (`_email_base.html:1,47`) and the manifest storage raises "Missing manifest entry" without `collectstatic`; `EMAIL_BACKEND = "anymail.backends.test.EmailBackend"`. If a migration fails on SQLite, note it in Progress and fall back to a local Postgres with `DB_*` vars documented in the proof commands.
8. `coderdojochi/tests/test_storage_settings.py`: runs `python -c` in a subprocess with `DEBUG=False`, `GS_BUCKET_NAME=wac-test-bucket` and the other required env vars from `.env.sample`, then prints `settings.STORAGES` and `settings.MEDIA_URL`. Asserts the default backend is `coderdojochi.storage_backends.MediaStorage`, staticfiles is `StaticStorage`, and `MEDIA_URL` starts with `https://storage.googleapis.com/wac-test-bucket/`. (Subprocess because settings are read at import.)

Pitfalls: `ManifestFilesMixin` needs `collectstatic` to have run before templates call `{% static %}` with `DEBUG=False`; that is the deploy script's job, not a test concern. Don't set `default_acl="publicRead"`: uniform bucket-level access rejects ACLs with HTTP 400. Don't touch `ALLOWED_HOSTS`.

Proof: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_storage_settings` passes; `DEBUG=False GS_BUCKET_NAME=x SECRET_KEY=x DEFAULT_FROM_EMAIL=a@b.c CONTACT_EMAIL=a@b.c uv run python manage.py check --deploy` runs without an ImportError (warnings are fine); `uv run ruff check coderdojochi && uv run ruff format --check coderdojochi`.

### Task D — Terraform (Checkpoint 1, parallel with A and E)

Owns: new `infra/terraform/*.tf` (including `email.tf` for the Resend DNS records: a `resend_dns_records` variable, a list of `{type, name, content, priority}` objects that Checkpoint 0b fills in `terraform.tfvars` from the Resend API response, and a `cloudflare_dns_record` per item, DNS-only, not proxied), `infra/terraform/terraform.tfvars.example`, `infra/terraform/README.md`, `.gitignore`.

Change:

1. `versions.tf`: Terraform `>= 1.9`; providers `hashicorp/google ~> 8.11`, `cloudflare/cloudflare ~> 5.29`, `hashicorp/tls ~> 4.0`, `hashicorp/archive ~> 2.7` (added for R5's bootstrap archive; output under gitignored `infra/terraform/.build/`). GCS backend `bucket = "wac-tfstate-<project_id>"` (passed with `-backend-config` so it is not hard-coded), `prefix = "prod"`.
2. `providers.tf`: google provider with `project`, `region = "us-central1"`, `zone = "us-central1-a"`, `billing_project = var.project_id`, `user_project_override = true`. Cloudflare provider reads `CLOUDFLARE_API_TOKEN` from the environment.
3. `variables.tf`: `project_id`, `billing_account_id`, `cloudflare_zone_id`, `domain` (default `weallcode.org`), `enable_ipv4` (bool, default `false`), `serial_console` (bool, default `false`), `cutover` (bool, default `false`; when `false` only `gcp.<domain>` points at the VM, when `true` the apex and `www` do too), `media_bucket_name`.
4. `apis.tf`: `google_project_service` for `compute`, `storage`, `billingbudgets`, `secretmanager` with `disable_on_destroy = false`. (No IAP: IAP TCP forwarding needs an internal IPv4, which an IPv6-only VM doesn't have.)
5. `network.tf`: custom-mode `google_compute_network` (`auto_create_subnetworks = false`); one `google_compute_subnetwork` in us-central1 with `stack_type = "IPV4_IPV6"`, `ipv6_access_type = "EXTERNAL"`, `private_ip_google_access = true`. Firewall rules: (a) TCP 443 from `data.cloudflare_ip_ranges.cf.ipv6_cidrs` (and `ipv4_cidrs` in a second rule only when `enable_ipv4`); (b) nothing else. No SSH rule and nothing on port 80. Admin access is the serial console (`gcloud compute connect-to-serial-port wac-web`), switched on by the `serial_console` variable (bool, default `false`) that sets metadata `serial-port-enable`, so turning it on and off is a Terraform change, not drift. When `enable_ipv4` is true, an SSH rule from the IAP range `35.235.240.0/20` may be added behind the same variable.
6. `vm.tf`: `google_service_account` for the VM; `google_compute_instance` `wac-web`, `e2-micro`, image `debian-cloud/debian-12`, boot disk 30 GB `pd-standard`, `allow_stopping_for_update = true`, `shielded_instance_config` all three on, network interface `stack_type = enable_ipv4 ? "IPV4_IPV6" : "IPV6_ONLY"` with an `ipv6_access_config { network_tier = "PREMIUM" }` and an `access_config {}` only when `enable_ipv4`. Metadata: `startup-script = file("${path.module}/../vm/provision.sh")`, `serial-port-logging-enable = "TRUE"`, `enable-oslogin = "TRUE"`, plus `wac-media-bucket` and `wac-deploy-bucket` keys the script reads. Service account scopes `["cloud-platform"]`. Confirm `IPV6_ONLY` and the `ipv6_access_config` field names against `terraform providers schema -json`.
7. `storage.tf`: media bucket (`location = "US-CENTRAL1"`, `STANDARD`, uniform bucket-level access, `public_access_prevention = "inherited"`, CORS `GET` from `https://weallcode.org` and `https://www.weallcode.org` for fonts) with `allUsers` → `roles/storage.objectViewer`; VM service account → `roles/storage.objectAdmin` on it. Private deploy bucket (`wac-deploy-<project_id>`, versioning on, lifecycle: delete noncurrent versions after 5) with VM SA → `roles/storage.objectViewer`. Private backup bucket (`wac-backups-<project_id>`, `US-CENTRAL1`, lifecycle: delete objects older than 30 days) with VM SA → `roles/storage.objectCreator` only (the VM can write backups but not delete or overwrite them). Media and static are served straight from `storage.googleapis.com`: GCS's free tier includes 100 GB/month of egress from North America (separate from the VM's 1 GB), far above a dormant site's traffic, and the $1 budget alert catches any overrun.
7b. `secrets.tf`: `google_secret_manager_secret` `wac-env-prod` and `wac-env-staging` (replication `auto`), with the VM service account granted `roles/secretmanager.secretAccessor` on each. Terraform creates the secrets only, never versions, so no secret values land in state; versions are added with `gcloud secrets versions add` (Task G). Staging media bucket `wac-staging-media-<project_id>`, same settings as the prod media bucket.
8. `tls.tf` + `dns.tf`: `tls_private_key` (ECDSA P256), `tls_cert_request` for `<domain>`, `www.<domain>`, `gcp.<domain>`, `staging.<domain>`; also a proxied AAAA `staging.<domain>` record (always on); `cloudflare_origin_ca_certificate` (`origin-ecc`, 5475 days). Private key and cert reach the VM as metadata keys `wac-origin-cert` and `wac-origin-key` (state bucket is private; accept that the key is in state and metadata). DNS: `cloudflare_dns_record` AAAA `gcp.<domain>` proxied always; AAAA apex and CNAME `www` → apex, proxied, only when `cutover`; A records only when `enable_ipv4 && cutover`. `cloudflare_zone_setting` `ssl = "strict"` always. Heroku's origin has valid public certificates (Automated Certificate Management is on), so strict mode works for Heroku too, and it is required for `gcp.<domain>` because the VM listens only on 443. Checkpoint 0 records the current mode first; Checkpoint 3 confirms `https://www.weallcode.org` still loads right after this setting is applied.
9. `iam.tf`: `google_project_iam_member` with `roles/owner` for `user:ali@weallcode.org`, `user:hello@weallcode.org`, `user:daniel.m.conrad@gmail.com` (variable `project_owners`, list of members).
10. `budget.tf`: `google_billing_budget` for the project, amount USD 1, thresholds 1% (any spend), 50%, 100%, email alerts to billing admins.
11. `outputs.tf`: VM IPv6 address, media bucket URL, deploy bucket name, backup bucket name.
12. `README.md`: bootstrap (below) and the `enable_ipv4` / `cutover` switches.
13. `.gitignore`: `.terraform/`, `*.tfstate*`, `infra/terraform/terraform.tfvars`, `infra/vm/env.prod`. Commit `.terraform.lock.hcl`.

Pitfalls: the default auto-mode `default` network can't host IPv6 subnets; use a custom network. Changing `enable_ipv4` recreates the VM (stack type is immutable). Don't manage existing Cloudflare records for `weallcode.org` that Heroku uses until `cutover`; import them first (`terraform import`) or delete them by hand in the cutover step, because creating a duplicate name fails. Leave the Google Workspace MX/SPF and Resend records alone (not in Terraform). Billing budget needs `billingbudgets.googleapis.com` enabled on the billing project.

Proof: `cd infra/terraform && terraform fmt -check -recursive && terraform init -backend=false && terraform validate`.

### Task E — VM provisioning and deploy scripts (Checkpoint 1, parallel with A and D)

Owns (updated 2026-11-24 for R5/R10/R21/R25): new `infra/vm/provision.sh`, `infra/vm/wac-web.service`, `infra/vm/wac-deploy@.service`, `infra/vm/wac-deploy@.timer`, `infra/vm/wac-manage`, `infra/vm/nftables-wac.nft`, `infra/vm/deploy-pull.sh`, `infra/vm/wac-backup.service`, `infra/vm/wac-backup.timer`, `infra/vm/backup-db.sh`, `infra/vm/wac-staging.service`, `infra/vm/refresh-staging-db.sh`, `infra/vm/env.staging.example`, `infra/vm/Caddyfile`, `infra/vm/postgresql.conf.d-wac.conf`, `infra/vm/env.prod.example`, `infra/vm/release.sh`, `infra/vm/README.md`.

Design (pull-based deploy, because the VM can't reach GitHub): Ali's laptop builds a release tarball and uploads it to the private deploy bucket, with a pointer per target (`current-prod`, `current-staging`); a systemd timer on the VM checks the pointers every 2 minutes and installs anything new for that target. Env files come from Secret Manager (`wac-env-prod`, `wac-env-staging`), read by the VM at deploy time. No SSH needed for a normal deploy. Prod and staging each have their own release directory (`/srv/wac/prod/`, `/srv/wac/staging/`), gunicorn socket, systemd service, database, and media bucket. Wherever the steps below say `/srv/wac/...`, read it per target.

Change:

1. `provision.sh` (Terraform startup script, runs as root on every boot, so it must be idempotent; `set -euo pipefail`; logs to the serial console):
   - Create a 1 GB swapfile once; `vm.swappiness=10`.
   - Install `unattended-upgrades` and enable it.
   - Add the PGDG apt repo (apt.postgresql.org) and install `postgresql-17`; drop in `postgresql.conf.d-wac.conf` (`shared_buffers=64MB`, `max_connections=20`, `work_mem=4MB`, `maintenance_work_mem=32MB`, `effective_cache_size=256MB`, `listen_addresses=''` meaning socket only). Create role `wac` and databases `wac` and `wac_staging`, both owned by `wac` (peer auth over the Unix socket).
   - Install Caddy from the cloudsmith repo (`gpg --batch --yes --dearmor`).
   - Install `python3.11-venv`, `libjpeg`/`zlib` runtime libs for Pillow if wheels need them; create the `/opt/uv` venv and `pip install uv` from PyPI.
   - Create the system user `wac` (no home), directories `/srv/wac/prod/releases` and `/srv/wac/staging/releases` (wac), `/etc/wac` (root:wac 0750), `/var/cache/wac-uv` (wac).
   - Read the metadata keys `wac-origin-cert` and `wac-origin-key` from `http://metadata.google.internal/computeMetadata/v1/instance/attributes/` (header `Metadata-Flavor: Google`) into `/etc/caddy/origin.pem` and `/etc/caddy/origin.key` (root:caddy 0640). On IPv6-only VMs the metadata server is reached over IPv6; confirm `metadata.google.internal` resolves on the VM in Checkpoint 3 (it has no public AAAA record, which is expected).
   - Install the systemd units and the Caddyfile, `systemctl enable --now` Caddy, `wac-deploy.timer`, `wac-backup.timer`; enable `wac-web` and `wac-staging` (each starts after its first deploy).
2. `Caddyfile`: listen on `:443` only, `tls /etc/caddy/origin.pem /etc/caddy/origin.key`, `encode zstd gzip`, request body limit 10 MB, `header_up X-Forwarded-Proto https`. No automatic HTTPS (Cloudflare does public TLS). Two site blocks: `weallcode.org, www.weallcode.org, gcp.weallcode.org` → `reverse_proxy unix//run/wac-prod/gunicorn.sock`; `staging.weallcode.org` → `basic_auth` (bcrypt hash from `caddy hash-password`; the hash is read from a metadata key `wac-staging-basic-auth`, set from a Terraform variable, so the password itself lives only in 1Password), `header X-Robots-Tag "noindex, nofollow"`, `reverse_proxy unix//run/wac-staging/gunicorn.sock`.
3. `wac-web.service` (prod): user `wac`, `EnvironmentFile=/etc/wac/env-prod`, `WorkingDirectory=/srv/wac/prod/current`, `ExecStart=/srv/wac/prod/current/.venv/bin/gunicorn coderdojochi.wsgi --preload -w 2 --max-requests 500 --max-requests-jitter 50 -b unix:/run/wac-prod/gunicorn.sock --access-logfile -`, `RuntimeDirectory=wac-prod`, `Restart=always`, `MemoryMax=450M`. `wac-staging.service`: the same with `-staging` paths, `-w 1`, `MemoryMax=200M`, and `OOMScoreAdjust=500` so the kernel kills staging before prod under memory pressure.
4. `release.sh --target prod|staging [git-ref]` (runs on the laptop; default ref `HEAD`): sets `CLOUDSDK_ACTIVE_CONFIG_NAME=wac` and refuses to run unless `gcloud config get account` prints `ali@weallcode.org` and `gcloud config get project` prints the We All Code project; refuses `--target prod` unless the ref is on `main` (staging takes any ref, for PR branches); `git archive --format=tar.gz <ref>` → `gs://<deploy-bucket>/releases/<sha>.tar.gz`; writes `<sha>` to `gs://<deploy-bucket>/current-<target>`. It does not touch secrets.
5. `deploy-pull.sh <target>` (runs on the VM from `wac-deploy.service`, a oneshot fired by the timer, once per target): reads `current-<target>`; if it differs from `/srv/wac/<target>/deployed`, downloads the tarball, reads the latest version of `wac-env-<target>` from the Secret Manager API (`secretmanager.googleapis.com`, token from the metadata server; for GCS and Secret Manager either use `curl` with that token against the JSON APIs over IPv6, or install `google-cloud-cli` from Google's apt repo, which has IPv6; pick one and use it everywhere), installs the env file at `/etc/wac/env-<target>` (owner root:wac, mode 0640), extracts to `/srv/wac/<target>/releases/<sha>` (owned by `wac`), runs `uv sync --frozen --no-dev` as `wac` with `UV_PYTHON=/usr/bin/python3.11`, `UV_PYTHON_DOWNLOADS=never` and `UV_CACHE_DIR=/var/cache/wac-uv` (created by `provision.sh`, owned by `wac`; the `wac` user has no home), then `manage.py migrate --noinput` and `manage.py collectstatic --noinput` as `wac` with the env loaded, flips the `/srv/wac/<target>/current` symlink, restarts `wac-web` (prod) or `wac-staging` (staging), keeps the last 3 releases per target, writes `/srv/wac/<target>/deployed`. On any failure it leaves `current` unchanged. Staging deploys never touch prod's database, env or service.
5b. `refresh-staging-db.sh` (run by hand on the VM): downloads the newest nightly backup, stops `wac-staging`, drops and recreates `wac_staging`, restores as `wac` with `--role=wac`, runs `manage.py migrate` with the staging env, starts `wac-staging`. Staging's env always has `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`, so a prod copy can't email real people; the script refuses to run if the staging env's `EMAIL_BACKEND` is anything else.
6. Nightly database backup: `backup-db.sh` runs `pg_dump -Fc wac` as `wac`, uploads it to `gs://<backup-bucket>/db/wac-<UTC date>.dump` with the same metadata-token/`gcloud storage` method as `deploy-pull.sh`, and deletes the local file. `wac-backup.timer` runs it daily at 03:30 America/Chicago with `Persistent=true`. Terraform's lifecycle rule on the backup bucket keeps 30 days (~40 MB × 30 stays well under the 5 GB free tier).
7. `README.md`: deploy steps, how to read logs (`journalctl -u wac-web -u wac-deploy -u caddy`), that `startup-script` changes only take effect on the next reboot (`gcloud compute instances reset` or a re-run of the script over the serial console), and that the Cloudflare origin key lives in instance metadata, so anyone with project viewer access and any process on the VM can read it (accepted risk; it only lets someone impersonate the origin to Cloudflare).
8. `env.prod.example`: every variable the app reads, with blanks: `SECRET_KEY`, `DEBUG=False`, `DJANGO_SECURE_SSL_REDIRECT=False`, `SITE_URL=https://www.weallcode.org`, `DB_HOST=/var/run/postgresql`, `DB_NAME=wac`, `DB_USER=wac`, `DB_PASSWORD=`, `DB_PORT=5432`, `GS_BUCKET_NAME`, `RESEND_API_KEY`, `DEFAULT_FROM_EMAIL=hello@weallcode.org`, `CONTACT_EMAIL=hello@weallcode.org`, `SENTRY_DSN`, `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY`, `PAYPAL_BUSINESS_ID`, `PAYPAL_RECEIVER_EMAIL`, `SLACK_WEBHOOK_URL=` (blank: no IPv6), `SLACK_ALERTS_CHANNEL=`. `env.staging.example`: the same, with `DB_NAME=wac_staging`, `SITE_URL=https://staging.weallcode.org`, the staging bucket, its own `SECRET_KEY`, `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`, no `RESEND_API_KEY`, and `SENTRY_ENVIRONMENT=staging` if Sentry is used. Real values never live in the repo: they go straight into Secret Manager (Task G).

Pitfalls: Debian 12's `python3` is 3.11.2, which satisfies `requires-python = ">=3.11,<3.12"`. Don't add uv's GitHub installer or `uv python install` (no IPv6). The startup script runs on every boot, so guard each step (`id wac || useradd ...`, `[ -f /swapfile ] || ...`). `--preload` with 2 workers keeps memory low; don't use 4 like Heroku.

Proof: `shellcheck infra/vm/*.sh` clean; `bash -n` on each; `systemd-analyze verify` is Linux-only, so skip it here and do it in Checkpoint 3; `caddy validate --config infra/vm/Caddyfile` if `brew install caddy` is acceptable, else Checkpoint 3.

### Task B — Email without SendGrid features (Checkpoint 2)

Owns: `coderdojochi/util.py`, new `coderdojochi/tests/test_email_util.py`. Widened by R8/R13 (2026-11-24): also a new `EmailSuppression` model + one migration, a signed `/unsubscribe/<token>/` view + URL, a `load_suppressions` management command, the unsubscribe link in announcement templates (overrides "Don't change the templates" below for that link only), and `announced_date` set before sending in the announce views.

Waits for Task A because it needs `coderdojochi/test_settings.py` and the anymail Resend extra.

Change `email()` (lines 14-99):

- Build the global merge values exactly as today (lines 39-57).
- Copy `merge_global_data` at the top (`merge_global_data = dict(merge_global_data)`); the mutable default `{}` is mutated today and leaks between calls.
- For each recipient, build that recipient's values (`merge_global_data` overlaid with `merge_data.get(recipient, {})`), replace every `*|key|*` in the rendered body with its value (`None` → `""`), and send one `AnymailMessage` per recipient, with no `merge_data`, `merge_global_data` or `merge_field_format`.
- Resend's free plan allows 100 emails/day and a few requests/second. Announcements (`old_views.py:681`, `766`, `views/meetings.py:232`) can go to every mentor or guardian. So: if `len(recipients) > getattr(settings, "EMAIL_DAILY_LIMIT", 90)` (read this way so Task B doesn't touch `settings.py`, which Task A owns), log an error and raise `ValueError` before sending anything. Between sends, `time.sleep(0.6)`. If a send fails, log which recipients were not sent and re-raise.
- Before building, the lead counts real recipients on the prod copy (`Mentor`/`Guardian` with active users) and records the numbers in Progress, so the limit choice is grounded.
- Only when `"sendgrid" in settings.EMAIL_BACKEND`, keep `esp_extra` `categories` and `asm`; otherwise send no `esp_extra`.
- Keep the signature, `reply_to`, attachments, `mixed_subtype`, and the `anymail_status` error logging. (`bcc` is accepted but never passed to the message today; keep that behavior.)

Test (`coderdojochi/tests/test_email_util.py`, uses `django.core.mail.outbox` with the anymail test backend from `test_settings.py`; patch `time.sleep` to keep it fast): call `email()` with a template that uses `*|first_name|*` (use an existing one: `class_reminder_guardian_one_week`, fed by `cron.py:54`), 2 recipients and different `merge_data`. Assert 2 messages; message 1 has recipient 1's first name and not recipient 2's; no `*|` remains in either body; no message has `esp_extra` with `asm`. Second test: 91 recipients → `ValueError` and an empty outbox.

Pitfalls: the templates render `{{ }}` first (Django) and then rely on `*|key|*` placeholders; keep that order. Don't change the templates.

Proof: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_email_util`; ruff check/format on the file.

### Task C — Slack notifications never break saves (Checkpoint 2, parallel with B)

Owns: `coderdojochi/notifications.py`, new `coderdojochi/tests/test_slack_notifications.py`.

Waits for Task A (test settings, `SLACK_WEBHOOK_URL` default).

Change `SlackNotification.send()` (lines 18-29): return immediately if `settings.SLACK_WEBHOOK_URL` is empty; otherwise `requests.post(..., timeout=5)` inside `try/except requests.RequestException`, logging the error; keep the non-200 logging.

Test: with `override_settings(SLACK_WEBHOOK_URL="")`, `mock.patch("coderdojochi.notifications.requests.post")` is not called. With a URL and `post` raising `requests.ConnectionError`, `send()` returns without raising.

Proof: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_slack_notifications`; ruff on the file.

### Task I — CI workflow for every PR (Checkpoint 2, parallel with B and C)

Owns: new `.github/workflows/ci.yml` only. Copy the action versions and checkout style from `.github/workflows/pre-commit.yml` (`actions/checkout@v6`, `actions/setup-python@v6`). Lint stays in the existing pre-commit workflow; don't duplicate it.

Waits for Checkpoint 1 because it runs Task A's `test_settings.py` and Task D/E's files.

Triggers: `pull_request` and `push` to `main`. Jobs (all on `ubuntu-latest`, Python 3.11, `astral-sh/setup-uv` pinned to a release tag, `uv sync --frozen`):

1. `tests`: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_storage_settings coderdojochi.tests.test_email_util coderdojochi.tests.test_slack_notifications`.
2. `django-postgres`: a `postgres:17` service container. With `DEBUG=True` and `DB_*` pointing at the service (and the other required env vars from `.env.sample`): `manage.py migrate --noinput`, `manage.py makemigrations --check --dry-run`, `manage.py loaddata fixtures/*.json` (the dev fixtures `tasks.py` loads), then start `gunicorn coderdojochi.wsgi -b 127.0.0.1:8000` in the background and `curl` `/`, `/programs/`, `/team/`, `/account/login/`, `/admin/login/`, failing on any 5xx. Then, separately, `DEBUG=False GS_BUCKET_NAME=ci-dummy ... manage.py check --deploy` to prove the production settings import.
3. `infra`: `hashicorp/setup-terraform` pinned; `terraform fmt -check -recursive infra/terraform`, `terraform -chdir=infra/terraform init -backend=false`, `terraform -chdir=infra/terraform validate`; `shellcheck infra/vm/*.sh` (preinstalled on ubuntu-latest).

No secrets: the workflow needs none and must not reference any.

Pitfalls: if a page returns 5xx only because the fixtures lack data, fix the fixture load (not the check), and note it in Progress. Pin every third-party action to a tag.

Proof: `actionlint .github/workflows/ci.yml` (`brew install actionlint`) passes locally; after the PR is opened, all three jobs are green.

### Task F — Provision and verify the IPv6-only VM (Checkpoint 3, lead plus Ali)

No repo files except fixes to Task D/E files found here (those go back to a sub-agent for D/E files).

Steps: Checkpoint 0 done → `terraform init -backend-config="bucket=wac-tfstate-<project_id>"` → `terraform plan` (review: e2-micro, pd-standard 30 GB, us-central1, `IPV6_ONLY`, no IPv4) → Ali approves → `terraform apply`. Then apply with `serial_console = true`, connect with `gcloud compute connect-to-serial-port wac-web` (log in as a user created by OS Login or a temporary password set by the startup script for this step only; pick one and record it), run the verification list below, and apply again with `serial_console = false`. Right after the first apply, confirm `https://www.weallcode.org` (still Heroku) loads under the new strict SSL setting; if it doesn't, set the zone back to the mode recorded in Checkpoint 0 and stop for Ali.

Verification on the VM (all must succeed): `curl -6 -sI https://deb.debian.org`, `https://pypi.org/simple/`, `https://storage.googleapis.com`, `https://api.resend.com`, `https://o4512487667466240.ingest.us.sentry.io` (new org's DSN host, 0b), `https://www.google.com/recaptcha/api/siteverify`; `getent hosts metadata.google.internal`; `systemctl is-active caddy postgresql wac-deploy.timer`; `free -m` shows swap; `systemd-analyze verify /etc/systemd/system/wac-*.service`; `caddy validate --config /etc/caddy/Caddyfile`.

Fallback: if outbound to any required host fails over IPv6, set `enable_ipv4 = true`, apply (recreates the VM), rerun, and write the decision and the ~$3.65/month cost into Progress.

### Task G — Data, media, first deploy on gcp.weallcode.org (Checkpoint 4, lead plus Ali)

1. Media: `aws s3 sync s3://<old-bucket>/media/ /tmp/wac-media/media/` (credentials from the backup config file), then `gcloud storage rsync -r /tmp/wac-media/media gs://<media-bucket>/media`. Compare object counts: `aws s3 ls s3://<old-bucket>/media/ --recursive | wc -l` vs `gcloud storage ls 'gs://<media-bucket>/media/**' | wc -l`. Static is rebuilt by `collectstatic`; don't copy it.
2. Database (rehearsal with today's dump): first `grep -c 's3.amazonaws.com' <(pg_restore -f - production-wac.dump)` locally; if any rows hold hard-coded S3 URLs, list the tables/columns in Progress and stop for Ali. Upload `production-wac.dump` to the private deploy bucket, download it on the VM, `systemctl stop wac-web`, then `sudo -u wac pg_restore --no-owner --no-acl --role=wac -d wac production-wac.dump` (run as `wac` so `wac` owns the tables and can migrate them; as `postgres` the tables would be owned by `postgres`). Delete the dump from the bucket and the VM.
3. Secrets: build the prod env in memory from `~/Projects/we-all-code/heroku-backup-2026-11-23/config/production-wac.env` (or its 1Password copy) plus the new Resend key, Sentry DSN and bucket name, following `infra/vm/env.prod.example`, and pipe it straight in: `... | gcloud secrets versions add wac-env-prod --data-file=-`. Same for `wac-env-staging` with a freshly generated `SECRET_KEY` and the console email backend. Never write either to a file in the repo. Show Ali the variable names (not values) before adding.
4. `infra/vm/release.sh --target prod` → wait for the timer → check `journalctl -u wac-deploy -u wac-web`.
4b. Staging: copy media to the staging bucket (`gcloud storage rsync -r gs://<media-bucket>/media gs://<staging-media-bucket>/media`), run `refresh-staging-db.sh` once the first nightly backup exists (or restore the rehearsal dump into `wac_staging` the same way as step 2), `release.sh --target staging`, then open `https://staging.weallcode.org`: the basic-auth prompt appears, the page loads after login, the response has `X-Robots-Tag: noindex`, and a password reset there prints the email to `journalctl -u wac-staging` instead of sending it. Check `free -m` and `systemctl status wac-web wac-staging` memory with both running.
5. Smoke test through Cloudflare at `https://gcp.weallcode.org`: `/`, `/programs/`, `/team/`, `/account/login/`, `/dj-admin/login/` (the Django admin; `/admin/` is the app's cdc-admin) return 200 (or the same redirect as Heroku: compare with `curl -sI https://www.weallcode.org<path>`); a page's CSS and an uploaded image load from `storage.googleapis.com`; log in to admin; upload a test image in admin and confirm the object appears under `gs://<media-bucket>/media/`; trigger a password reset to Ali's address and confirm the Resend email arrives (this checks Resend; allauth doesn't use `util.email()`); then on the VM run `manage.py shell -c` calling `coderdojochi.util.email()` with `template_name="class_reminder_guardian_one_week"`, `recipients=["<Ali's address>"]` and a `merge_data` entry, and confirm that email arrives with the merged values and no `*|` text.

### Task H — Cutover and Heroku shutdown (Checkpoint 5, lead plus Ali)

1. Pick a quiet time. `heroku maintenance:on -a production-wac` (Ali approves; outward-facing).
2. `heroku pg:backups:capture -a production-wac` and `pg:backups:download` to the backup folder. On the VM: `systemctl stop wac-web wac-deploy.timer`, `sudo -u postgres dropdb wac && sudo -u postgres createdb -O wac wac`, `sudo -u wac pg_restore --no-owner --no-acl --role=wac -d wac <dump>`.
3. Row-count check (AC7), before any migration runs: for every table in `public`, run exact `SELECT count(*)` (a small script that loops over `information_schema.tables`) on a local restore of the same dump and on the VM; save both outputs into the backup folder and `diff` them; they must be identical. Only then `systemctl start wac-deploy.timer` and redeploy so the 11 migrations run. Then re-run `wac-manage prod load_suppressions` with `sendgrid-suppressions.json` (send it through the transfer bucket, then delete it there and on the VM): the restore replaces the rehearsal DB, so `EmailSuppression` comes back empty, and skipping this would mail people who unsubscribed. (Added in session 4.)
4. Delete the Heroku-era Cloudflare records for `weallcode.org` and `www` by hand (their values are saved in `cloudflare-records-before.json` from Checkpoint 0), set `cutover = true`, `terraform apply`.
5. Verify AC1 and AC2 on the real hostnames. Keep Heroku in maintenance mode for 7 days. Rollback: set `cutover = false` and `terraform apply` (removes the GCP apex/www records), recreate the two Heroku records by hand from `cloudflare-records-before.json`, then `heroku maintenance:off -a production-wac`. Any data written on GCP after cutover is lost in a rollback unless dumped and restored to Heroku first.
6. Before Heroku is deleted: SendGrid exports done (Checkpoint 0), Sentry project transferred or history accepted as lost (Ali decides).
6b. Create the Sentry uptime monitor for `https://www.weallcode.org/` in the new Sentry org (UI or Sentry MCP `create_uptime_monitor` if connected), email alerts to Ali. Confirm it shows "up".
7. Day 3: billing report for the project shows $0.00 (AC6); if the IPv6 SKU or any other SKU shows, record it and stop for Ali.
7b. Day 30: with Ali's OK, delete the old S3 bucket (`aws s3 rb s3://<old-bucket> --force` after one last `aws s3 ls --summarize` matches the GCS copy) and review the AWS billing console for other charges. Record in Progress.
8. Day 7: Ali deletes `production-wac`, `wac-nocodb`, `wac-robot-hub` and `wacdrop`, then cancels the Eco dynos plan in Heroku billing (AC8); the builder doesn't. Next month's Heroku invoice should be $0. Update Progress.
9. After step 8: a second small PR removes `Procfile`, `app.json` and the Heroku `release` task in `tasks.py` (keep `start`/`test` tasks if still used), and updates `README.md` deploy notes to point at `infra/`. CI must pass.

## Checkpoints

Build them in order. Each one is committed on its own.

**Checkpoint 0 — accounts and secrets.** Can run while Checkpoints 1-2 are built. Split in two: 0a needs Ali (browser logins, a card, sign-up forms; Claude can't do these); 0b the builder runs from the CLI once 0a's logins exist. The builder checks 0a items off only when Ali confirms.

0a — Ali only (about 20 minutes):

- [ ] GCP login in a separate gcloud configuration (browser OAuth): `gcloud config configurations create wac --no-activate`, then `CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud auth login ali@weallcode.org`. Do **not** run `gcloud auth application-default login`: it overwrites the one global ADC file and would break Braven's tooling.
- [ ] GCP billing account with We All Code's card, created in the console (adding a payment method has no CLI). Tell the builder the billing account ID, or let it find it with `gcloud billing accounts list`.
- [ ] Cloudflare API token, created in the dashboard (API Tokens > Create Token; a token can't be minted without an existing token that has "API Tokens Edit", so the first one is manual): scoped to the `weallcode.org` zone with Zone Read, DNS Edit, Zone Settings Edit, SSL and Certificates Edit. Save it in 1Password as `op://<vault>/Cloudflare weallcode Terraform/credential` and tell the builder the reference.
- [ ] Resend: sign up, then create a full-access API key and save it in 1Password. (The builder does the domain setup through the API.)
- [ ] Sentry: sign up a new free org with a different email (sign-up form), then in the old Heroku org run Project Settings > General > Transfer Project to the new org and approve the emailed request (UI only; Owner role). If transfer isn't offered, open a Sentry support ticket before anything removes the add-on. Fill in the Sentry for Good form at https://sentry.io/for/good.
- [ ] 1Password CLI: make sure `op whoami` works in a terminal (desktop app integration or `op signin`), so the builder can read and write items.

0b — the builder, from the CLI (Ali approves the command list first):

- [ ] Verify the account: `CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud config get account` → `ali@weallcode.org`. Stop otherwise.
- [ ] Create the project and link billing: `gcloud projects create wac-website-<suffix> --name="We All Code website"`, `gcloud config set project ...` (in the `wac` config), `gcloud billing projects link ... --billing-account=<id>`.
- [ ] State bucket (outside Terraform): `gcloud storage buckets create gs://wac-tfstate-<project_id> --location=us-central1 --uniform-bucket-level-access --public-access-prevention`, then `gcloud storage buckets update gs://wac-tfstate-<project_id> --versioning`.
- [ ] Cloudflare snapshot (read-only API calls with the token from 1Password): look up the zone ID; record the zone's current SSL/TLS mode (`GET /zones/<id>/settings/ssl`) and export the current `weallcode.org` and `www` records (`GET /zones/<id>/dns_records?name=...`) into `~/Projects/we-all-code/heroku-backup-2026-11-23/meta/cloudflare-records-before.json`. These are the rollback values.
- [ ] Resend domain: `POST https://api.resend.com/domains` with `{"name": "weallcode.org"}`, write the returned DNS records into Cloudflare (as `cloudflare_dns_record` resources in a new `infra/terraform/email.tf`, added to Task D's files, so they live in Terraform; the records go on the `send` subdomain and `resend._domainkey`, leaving the Google Workspace MX and SPF at the root alone), then `POST /domains/<id>/verify` and poll `GET /domains/<id>` until `verified`. Then create a sending-only API key for the app (`POST /api-keys` with `permission: "sending_access"`, scoped to the domain) and store it in 1Password; the full-access key stays with Ali.
- [ ] SendGrid export (before Heroku is deleted; the key still works): page through `GET /v3/suppression/unsubscribes`, `/suppression/bounces`, `/suppression/blocks`, `/suppression/spam_reports`, `/asm/groups` and each group's `/asm/groups/<id>/suppressions` with `limit=500&offset=...`, saving JSON to `~/Projects/we-all-code/heroku-backup-2026-11-23/sendgrid/`. Report the counts.
- [ ] 1Password: `op item create` one Secure Note (or one item per app) in a vault Ali names, holding each `config/*.env` file from the backup folder; read back with `op item get` to confirm; only then tell Ali the plaintext `config/` files can be deleted (Ali deletes them).
- [ ] Sentry check (if the Sentry MCP tools or a Sentry auth token are available): confirm the transferred project appears in the new org and note its DSN in 1Password.

**Checkpoint 1 — code and infra files build locally.** Tasks A, D, E in parallel (separate files). Check: Task A, D and E proofs all pass; full lint `uv run ruff check . && uv run ruff format --check .`; `uv run pre-commit run --all-files`. Delivers: settings that load with `DEBUG=False`, valid Terraform, lint-clean scripts.

**Checkpoint 2 — email and Slack safe for the new host, CI in place.** Tasks B, C, I in parallel (separate files). They wait for Checkpoint 1 because they use `coderdojochi/test_settings.py`, the dependency changes from Task A, and (Task I) the infra files. Extra check: `actionlint .github/workflows/ci.yml`. Check: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_storage_settings coderdojochi.tests.test_email_util coderdojochi.tests.test_slack_notifications` passes, plus ruff. Delivers: an app that runs on the VM without SendGrid or Slack.

**Checkpoint 3 — VM up, IPv6-only works.** Task F. Needs Checkpoint 0 (accounts) and Checkpoint 1 (Terraform and scripts). Check: the verification list in Task F all succeeds, or the IPv4 fallback is applied and recorded. Delivers: a provisioned VM with Postgres, Caddy and the deploy timer.

**Checkpoint 4 — site works at gcp.weallcode.org with real data.** Task G. Check: every smoke test in Task G step 5 passes. Delivers: a full copy of the site on GCP, Heroku still live.

**Checkpoint 5 — cutover.** Task H. Check: AC1, AC2, AC7 on the real hostnames; AC5 (`terraform plan` shows no changes); AC6 on day 3; AC8 on day 7.

## How to run it

Read this whole plan before starting.

You are the lead. You write no code. At the start of each checkpoint, give every task in it that can run in parallel to its own sub-agent, all in one message. Each sub-agent's brief says: its task letter and text from this plan, the files it owns and that it must touch only those, the bar (its Proof command passes, ruff clean, no other files changed), the report format (files changed, the proof command and its exact output, anything it could not do), and that it must not run git.

You alone run the checkpoint's check, look at the actual diff (`git diff --stat` and the files themselves, never the sub-agent's report), commit, and write the result and evidence into Progress. Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Commit only on this branch, never `main`. After Checkpoint 2, push the branch and open one PR against `main` (with Ali's OK); each later checkpoint adds its commit to that PR. The PR must be merged before Task H's cutover, and prod deploys come only from `main` (`release.sh` enforces it).

Anything that comes up that isn't in this plan (a new file, a changed decision, a fallback) gets written into this plan first, then built.

Run every `gcloud` and Terraform command with `CLOUDSDK_ACTIVE_CONFIG_NAME=wac` in its environment, and give Terraform its Google credentials as `GOOGLE_OAUTH_ACCESS_TOKEN="$(CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud auth print-access-token)"` (never ADC). Before the first command of each session, check that `CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud config get account` prints `ali@weallcode.org` and `... config get project` prints the We All Code project. If either prints the Braven account or `braven-data-infra`, stop.

Ask Ali before: `terraform apply`, any Heroku command that changes state (`maintenance:on`, deletes), changing Cloudflare records for the live hostnames, and anything that sends email to someone other than Ali.

After each checkpoint, if your context window is half full, write which checkpoint is next into Progress and stop; a fresh session continues from this plan.

## Proof

For each acceptance criterion, the test that proves it and the one-line change that should make it fail. When a test is written, make the one-line change, confirm the test fails, then undo it with the exact reverse edit (never `git checkout`/`git restore`).

| AC | Proof | One-line break that must make it fail |
|---|---|---|
| AC1 | Task G step 5 and Task H step 5 `curl` checks on each path (status matches Heroku's for the same path) | Stop `wac-web` (`systemctl stop wac-web`) → Cloudflare returns 502 |
| AC2 | `coderdojochi.tests.test_storage_settings`; manual: page CSS and an image URL start with `https://storage.googleapis.com/`; admin upload appears in the bucket | In `settings.py`, change the `default` backend to `django.core.files.storage.FileSystemStorage` → test fails |
| AC3 | `coderdojochi.tests.test_email_util`; manual password-reset email received via Resend | In `util.py`, skip the placeholder replacement line → `*|` assertion fails |
| AC4 | `coderdojochi.tests.test_slack_notifications` | Remove the empty-URL early `return` in `notifications.py` → the "post not called" assertion fails |
| AC5 | `terraform plan -detailed-exitcode` exits 0 after apply | Edit the VM `machine_type` in `vm.tf` to `e2-small` → exit code 2 (don't apply) |
| AC6 | GCP billing report filtered to the project, day 3: $0.00 | n/a (observed, not testable) |
| AC7 | Exact `count(*)` per table on the VM equals the same on the final dump restored locally, compared before migrations run (Task H step 3) | Delete one row on a scratch local copy → `diff` shows the table |
| AC8 | `heroku apps` lists none of the four apps, and Heroku billing shows no Eco plan (after Ali deletes them) | n/a |
| AC9 | After the first night: `gcloud storage ls gs://<backup-bucket>/db/` shows a dump; on the VM restore it into a scratch DB (`createdb wac_restore_test`) and run the AC7 count script against both | In `backup-db.sh`, point the upload at a wrong bucket name → the timer run fails (`systemctl status wac-backup` shows failed) |

Whole-build checks (run before every commit; all must pass):

- `uv run ruff check . && uv run ruff format --check .`
- `uv run pre-commit run --all-files`
- `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_storage_settings coderdojochi.tests.test_email_util coderdojochi.tests.test_slack_notifications` (the two pre-existing tests in `coderdojochi/tests/` fail before this work and are out of scope; note their status, don't fix them)
- `cd infra/terraform && terraform fmt -check -recursive && terraform validate`
- `shellcheck infra/vm/*.sh`
- `actionlint .github/workflows/ci.yml`; once the PR exists, all CI jobs green
- Manual, from Checkpoint 4: the Task G step 4b staging checks, and the Task G step 5 smoke test.

Before you call it done, use the site the way a user would through `https://www.weallcode.org`: browse the home page and a program page, log in as a test user, open admin, and confirm nothing that worked on Heroku is now broken.

## Plan review findings

A fresh sub-agent reviewed this plan on 2026-11-23. Every finding and what was done about it:

| # | Severity | Finding | Resolution |
|---|---|---|---|
| 1 | Blocker | Removing `django-heroku` also removes `dj-database-url`, which `settings.py:15` imports → ImportError everywhere | Task A step 1 adds `dj-database-url` explicitly |
| 2 | Blocker | Email templates call `{% static %}`; with `DEBUG=False` the manifest storage raises "Missing manifest entry" in tests | `test_settings.py` uses plain `StaticFilesStorage` and in-memory media storage (Task A step 7) |
| 3 | Major | Tests need `GS_BUCKET_NAME`, `DEFAULT_FROM_EMAIL`, `CONTACT_EMAIL` and a Postgres; the proofs set neither | `test_settings.py` sets env defaults before import and uses in-memory SQLite (Task A step 7), with a documented Postgres fallback |
| 4 | Major | Media served from storage.googleapis.com is internet egress; reviewer feared the 1 GB/month limit | Kept direct GCS serving: GCS's free tier has its own 100 GB/month North America egress (free-tier table), separate from the VM's 1 GB; the $1 budget alert catches overruns (Task D step 7) |
| 5 | Major | No database backups after cutover | Nightly `pg_dump` timer to a private, write-only backup bucket with 30-day lifecycle (Task E step 6, Task D step 7, AC9) |
| 6 | Major | Announcement emails can exceed Resend's 100/day and rate limit; partial failures | Hard cap (default 90) checked before any send, 0.6 s between sends, log unsent recipients; lead counts real recipients first (Task B) |
| 7 | Major | `gcloud auth application-default login` overwrites the global ADC file (Braven) | Removed. Separate `wac` gcloud configuration via `CLOUDSDK_ACTIVE_CONFIG_NAME`, Terraform gets `GOOGLE_OAUTH_ACCESS_TOKEN` (Checkpoint 0, How to run it, Task E step 4) |
| 8 | Major | Rollback via `cutover=false` would leave no apex/www records | Checkpoint 0 exports the current records to `cloudflare-records-before.json`; Task H step 5 spells out the manual restore |
| 9 | Major | `pg_restore --no-owner` as `postgres` makes `postgres` own the tables; `dropdb` fails with open connections | Restore as `wac` with `--role=wac`; stop `wac-web` first (Task G step 2, Task H step 2) |
| 10 | Major | SSL mode stays as is until cutover; if Flexible, `gcp.` smoke test fails (VM has no port 80) | Set `ssl = "strict"` from the first apply (Heroku has valid ACM certs); Checkpoint 0 records the old mode; Task F checks Heroku still loads (Task D step 8) |
| 11 | Major | IAP TCP forwarding needs internal IPv4; IPv6-only VM has none | Dropped IAP; serial console behind a Terraform variable is the admin path (Task D steps 4-5, Task F) |
| 12 | Major | AC7 used `n_live_tup` (an estimate) and compared after migrations change rows | Exact `count(*)` per table, compared before migrations run (Task H step 3, AC7) |
| 13 | Minor | Task E didn't say where the env file lives or which uv cache the home-less `wac` user uses | `/etc/wac/env` root:wac 0640; `UV_CACHE_DIR=/var/cache/wac-uv` (Task E step 5) |
| 14 | Minor | Dump may contain hard-coded `s3.amazonaws.com` URLs | Grep the dump before restore; stop for Ali if any (Task G step 2) |
| 15 | Minor | Origin key in metadata is readable by project viewers and VM processes | Documented as accepted risk in `infra/vm/README.md` (Task E step 7) |
| 16 | Minor | AC3 manual check used password reset, which doesn't go through `util.email()` | Added a real `util.email()` merged send to Ali (Task G step 5) |
| 17 | Minor | `gcloud storage ls -r` output includes headers | Count with `ls 'gs://.../media/**'` (Task G step 1) |
| 18 | Minor | `merge_global_data={}` mutable default is mutated; `bcc` is never passed | Copy per call; keep `bcc` behavior unchanged (Task B) |
| 19 | Minor | `startup-script` changes apply only on reboot | Documented in `infra/vm/README.md` (Task E step 7) |

Reviewer confirmed as correct: settings line references, `class_reminder_guardian_one_week` exists and uses `*|first_name|*`, the `unsub_group_id` gate at `_email_base.html:92`, the Slack caller lines, and that Checkpoint 1 tasks own separate files.

Open risks the builder must watch: the serial-console login method on an IPv6-only VM is chosen in Task F. (Resolved 2026-11-23: external IPv6 is free per the network pricing page, and the `IPV6_ONLY` field names are confirmed; see "Facts established" in Read first. AC6 still checks the real bill.)

### Second review (2026-11-24)

A second fresh sub-agent reviewed the plan after staging, CI, Secret Manager and `release.sh --target` were added. **These resolutions are binding and override any task text they contradict.** The lead folds each one into the owning task's brief.

| # | Severity | Finding | Resolution (owner) |
|---|---|---|---|
| R1 | — | Reviewer said `wac-metabase` was still on Heroku | Invalid: `heroku apps --all` (2026-11-24) shows only production-wac, wac-nocodb, wac-robot-hub, wacdrop. Metabase was backed up (`wac-metabase.dump`) and deleted. No action |
| R2 | Blocker | Terraform can't grant Owner to a gmail.com user (`setIamPolicy` refuses; invite must be accepted in the console) | Ali decided: Ali invites daniel.m.conrad@gmail.com as Owner in the console (0a). After he accepts, the lead `terraform import`s that binding into `iam.tf` (Task F). The other two owners stay plain `google_project_iam_member` (Task D) |
| R3 | Blocker (if it applies) | Orgs created on/after 2024-05-03 enforce `iam.allowedPolicyMemberDomains`, which blocks `allUsers` on media buckets and the gmail owner | 0b runs `gcloud resource-manager org-policies describe constraints/iam.allowedPolicyMemberDomains --effective --project=<id>`. If it's enforced, Terraform adds a project-level `google_org_policy_policy` override (`allow_all`). If Ali lacks Org Policy Admin, stop and ask (0b) |
| R4 | Blocker | Task G runs `release.sh --target prod`, which only accepts `main`, but the PR merges only before Task H, so `main` still has broken S3 settings | Rule change: the PR merges **before Checkpoint 4**, after Checkpoint 3 passes. Fixes found in Checkpoints 4–5 go in small follow-up PRs. `release.sh --target prod` stays main-only |
| R5 | Blocker | Only `provision.sh` reaches the VM; units, Caddyfile, `deploy-pull.sh` and `backup-db.sh` don't | Task D's `vm.tf` ships `infra/vm/bootstrap.tgz`, built by a `data "archive_file"` over `infra/vm/`, as a `google_storage_bucket_object` in the deploy bucket. `provision.sh` downloads it with the metadata token and installs every file. Every later release tarball carries `infra/vm/`, and `deploy-pull.sh` reinstalls any changed unit/Caddyfile and runs `systemctl daemon-reload` / `caddy reload` |
| R6 | Blocker | The backup SA has only `objectCreator`, so refresh-staging and AC9 can't read the backup; same-day dumps collide | Add `objectViewer` on the backup bucket (no delete, so it stays write-once). Name dumps `wac-<UTC yyyymmddTHHMMSS>.dump`. `refresh-staging-db.sh` uses a local `pg_dump wac \| pg_restore -d wac_staging` instead of the bucket |
| R7 | Blocker | Redeploying the same SHA is a no-op, so H3's migrations never run and a secret-only change never rolls out | `release.sh --force` writes `<sha>:<nonce>` to the pointer, and `deploy-pull.sh` compares the whole string. H3 runs `release.sh --target prod --force`, then checks `showmigrations` shows no `[ ]` and `systemctl is-active wac-web` |
| R8 | Should-fix | SendGrid suppressions (500+ unsub, 416 bounce, 74 spam) unused; announcements lose their unsubscribe link | Ali decided: import list + add a link. Task B adds an `EmailSuppression(email unique, reason, created_at)` model plus one migration. 0b exports all four SendGrid suppression lists to `heroku-backup-2026-11-23/sendgrid-suppressions.json`. Task G loads them with a `load_suppressions` command. `email()` drops suppressed recipients before the cap check. Announcement templates get a signed (`django.core.signing`) `/unsubscribe/<token>/` link that adds a row. Resend bounce/complaint webhooks are out of scope; Ali checks the Resend dashboard |
| R9 | Should-fix | Any VM replace wipes Postgres (it lives on the boot disk) | `lifecycle { prevent_destroy = true }` on the instance. Before any apply that shows a replace: run `backup-db.sh`, verify the dump restores into a scratch DB, then ask Ali |
| R10 | Should-fix | Staging shares Unix user, DB role, env-file group and SA with prod, so a branch on staging can read prod secrets | Ali decided: trusted refs only + isolate. Staging runs as Unix user `wac-staging` with DB role `wac_staging` (owns only `wac_staging`). `/etc/wac/env-staging` is `root:wac-staging 0640`. A second SA `wac-staging-vm` only has staging media objectAdmin and accessor on `wac-env-staging`. The metadata server hands the VM's (prod) SA token to any local process, so `provision.sh` adds an nftables rule `meta skuid wac-staging ip6 daddr fd20:ce::254 drop` (plus `169.254.169.254` for safety), and staging authenticates with a key for `wac-staging-vm`. Root fetches that key from Secret Manager secret `wac-staging-sa-key` at deploy into `/etc/wac/staging-sa.json` (root:wac-staging 0640, `GOOGLE_APPLICATION_CREDENTIALS`). Task F proves it: `sudo -u wac-staging curl -6 -m5 -H 'Metadata-Flavor: Google' http://metadata.google.internal/` must fail. `release.sh --target staging` refuses refs not reachable from `origin` (no fork PR refs) |
| R11 | Should-fix | The dump has `EXTENSION pg_stat_statements` and its COMMENT; restoring as non-superuser exits non-zero | Every restore uses `pg_restore -l dump \| grep -v -E 'EXTENSION\|COMMENT - EXTENSION' > toc; pg_restore -L toc --role=wac ...` (Task G step 2, H step 2) |
| R12 | Should-fix | The prod dump uploaded to the versioned deploy bucket persists as a noncurrent version | Terraform adds a separate non-versioned private bucket `wac-transfer-<project>` (US-CENTRAL1, lifecycle delete at age 1 day, VM SA objectViewer). Dumps go there, never into the deploy bucket. The lead runs `gcloud storage rm` right after each restore and confirms the bucket is empty |
| R13 | Should-fix | 90 sends inside one request passes gunicorn's 30 s timeout; a retry re-mails the first N | gunicorn `--timeout 120`. Cap stays 90 at 0.6 s (~70 s with latency, under Cloudflare's 100 s). The announce views set `announced_date` **before** sending, so a retry never double-sends. `email()` reports each failed recipient to Sentry, and Ali resends to failures by hand |
| R14 | Should-fix | Leftover `*\|key\|*` tags remain when merge data is partial | After replacing, `re.sub(r"\*\|\w+\|\*", "", body)`; Task B test covers it |
| R15 | Should-fix | Copying the Heroku env carries `DATABASE_URL` (forces ssl_require), `SENDGRID_*`, `PAPERTRAIL_*`, `HEROKU_*`, `WEB_CONCURRENCY` | Build each env only from `env.<target>.example` keys. Explicitly drop those keys; Task G asserts `DATABASE_URL` is absent |
| R16 | Should-fix | Polling every 2 min ≈ 43k Class B ops/month plus endless retry secret reads; bucket locations unset | Poll every 15 min (`OnUnitActiveSec=15min`). Record a failed pointer in `/srv/wac/<target>/failed` and skip it until the pointer changes. Pin every bucket to `US-CENTRAL1` |
| R17 | Should-fix | Missing APIs: `iam`, `cloudresourcemanager`, `cloudbilling`, `orgpolicy` | Add them to `apis.tf` with `depends_on` from their users |
| R18 | Should-fix | Zone-wide `ssl = "strict"` breaks any other proxied origin without a valid cert | 0b exports every zone record and `curl`s each proxied origin with cert verification. Any failure → stop and ask Ali before the first apply |
| R19 | Should-fix | 0b and Task D both write `email.tf`; Resend can't verify before the first apply; a pitfall contradicts both | 0b only creates the Resend domain and writes its DNS records into `terraform.tfvars` (`resend_dns_records`). Task D owns `email.tf`. Verify the domain and create the sending key in Task F after the first apply. Delete the "leave Resend out of Terraform" pitfall |
| R20 | Should-fix | google-auth GCE detection may ping 169.254.169.254 (IPv4) and hang on IPv6-only | Set `GCE_METADATA_HOST=metadata.google.internal` and `GCE_METADATA_IP=metadata.google.internal` in both envs. Task F proves it with `curl -6` for the token, then `google.auth.default()` and a GCS write from the release venv |
| R21 | Should-fix | `source`-ing the env mangles `$`/quotes in secrets | All management commands run via `systemd-run --wait --pipe -p User=<user> -p EnvironmentFile=/etc/wac/env-<target> ...`. A wrapper `/usr/local/bin/wac-manage <target> <args>` does this |
| R22 | Should-fix | Bucket CORS omits `gcp.` and `staging.` | Prod bucket CORS: apex, `www`, `gcp.`; staging bucket: `staging.` |
| R23 | Nit | The copied `LOGGING` attaches console only to `testlogger` | Root logger → `console` at INFO |
| R24 | Nit | Contradictions and stale refs | "Out of scope: CI/CD" removed (Task I is in scope). AC5 reads "every resource except Workspace MX/SPF". Task D vars add `project_owners`, `resend_dns_records`, `staging_basic_auth_hash`. Announcement calls are `old_views.py:728,812` and `views/meetings.py:200,275`; cron template call `cron.py:100`. Drop `.gitignore` `infra/vm/env.prod`. Task G 4b restores from a fresh local `pg_dump wac`, not the deleted rehearsal dump |
| R25 | Nit | Caddy binds :80 for redirects; one deploy unit for both targets; serial-console login | Caddy `auto_https disable_redirects`. Template unit `wac-deploy@.service` and timer `wac-deploy@.timer`. Serial console uses a temporary local password set by `provision.sh` from a metadata key Ali sets, removed after Task F |

Also from Ali (2026-11-24): **export Papertrail archives** before deleting production-wac. Task H step 8 first runs `heroku addons:open papertrail -a production-wac` for Ali, who downloads the archives to `heroku-backup-2026-11-23/papertrail/`. The lead checks that the folder isn't empty before Ali deletes the app.

Defaults the lead applies (not asked): announcements over 90 recipients are split by Ali across days. The GCP org creation date is checked in 0b via R3.

## Progress

### 2026-11-24 — session 1

Checkpoint 0a (lead in Chrome with Ali, who entered passwords and approved each step):

- [x] gcloud config `wac` created; `CLOUDSDK_ACTIVE_CONFIG_NAME=wac gcloud config get account` → `ali@weallcode.org`. The localhost:8085 callback couldn't be reached from Chrome, so login used `--no-launch-browser` (code-paste flow). The default config is still Braven, untouched.
- [x] GCP org `weallcode.org` exists (org ID `511914366769`). Signing in to the console auto-created a stray project `light-router-515716-a2` ("My First Project"); delete it in 0b.
- [x] Billing account "We All Code" `0183FC-3A3638-28092E`, under the org, paid by the existing "We All Code" payments profile (Visa ending 3817, also used for Google Ads). Ali confirmed it is We All Code's card. No projects linked yet. Budget + alerts come from `budget.tf` ($1, 1/50/100%) on the first apply.
- [x] Cloudflare user API token "weallcode Terraform": zone `weallcode.org` only, DNS Edit, Zone Read, Zone Settings Edit, SSL and Certificates Edit, no expiry. Verified active. Stored at `op://homelab/Cloudflare weallcode Terraform/credential`.
- [x] 1Password (decision change): `op` here runs as a service account that only sees vault `homelab`, and the desktop-app integration fails. Ali chose to store We All Code secrets in `homelab`. Every `op://<vault>/...` reference in this plan means `op://homelab/...`.
- [x] Resend: account via Google login as ali@weallcode.org (team "weallcode"), no domains yet. Full-access key "admin full access (Ali)" at `op://homelab/Resend weallcode full access/credential`.
- [x] Sentry: new org "We All Code" `we-all-code-p5` (US region, Google login ali@weallcode.org). Project `production` transferred from the Heroku org `we-all-code` (Ali approved; verified 2026-11-24: the old org now lists only `staging`, which stays behind, per Ali). DSN still to be read from the new org and put into 1Password (0b). Sentry for Good application submitted (Non-Profit / 501c3, org URL https://we-all-code-p5.sentry.io).
- [x] Invite daniel.m.conrad@gmail.com as Owner: invited in session 2, pending his acceptance (see session 2).

Checkpoint 1 — **passed and committed** (lead's own checks):

- `manage.py test coderdojochi.tests.test_storage_settings` → `Ran 5 tests ... OK`. AC2 break test: `default` backend set to `FileSystemStorage` → `FAILED (failures=1)`, reverse edit → `OK`.
- `check --deploy` with `DEBUG=False` → 4 warnings, no ImportError.
- `terraform fmt -check -recursive && terraform validate` → "The configuration is valid." `shellcheck infra/vm/*.sh infra/vm/wac-manage` → clean.
- Ruff: the repo-wide `ruff check .`, `ruff format --check .` and `pre-commit run --all-files` already failed before this work (`util.py` fails format on HEAD; the repo has ~285 lint errors). Changed files: new files clean; `settings.py` errors went from 24 → 18 (all in untouched code). These whole-build checks are scoped to changed files until a separate lint cleanup.
- Spot review: `IPV6_ONLY` unless `enable_ipv4`, e2-micro, 30 GB pd-standard, `prevent_destroy`, 443-only firewall from Cloudflare ranges, no secret versions in Terraform. Grep for tokens/private keys in the tree → none.

**Next (for a fresh session):** (1) Checkpoint 2: dispatch Tasks B (with the R8/R13/R14 widening), C, I in parallel. (2) In parallel, Checkpoint 0b: show Ali the command list, then run it. It covers: project create + billing link to `0183FC-3A3638-28092E`; delete stray project `light-router-515716-a2`; the state bucket; the org-policy checks (R3 plus `iam.disableServiceAccountKeyCreation` and `storage.publicAccessPrevention`); the Cloudflare snapshot + R18 origin curl check; the Resend domain → `resend_dns_records`; the SendGrid export; the config files into `homelab`; Daniel's Owner invite in Chrome. Note: Chrome's Sentry session is now the old Heroku-org account; sign in to `we-all-code-p5` again (Google, ali@weallcode.org) to read the DSN.

### 2026-11-24 — session 2

Checkpoint 0b (Ali approved the full command list; account check `ali@weallcode.org` first):

- [x] Project `wac-website-7bda80` ("We All Code website", org `511914366769`) created, set as the `wac` config's project, billing linked to `0183FC-3A3638-28092E` (`billingEnabled: true`).
- [x] Stray project `light-router-515716-a2` deleted (undeletable for 30 days).
- [x] State bucket `gs://wac-tfstate-wac-website-7bda80`: US-CENTRAL1, UBLA, public access prevention enforced, versioning on.
- [x] Org policies (effective on the project): `iam.allowedPolicyMemberDomains` → `allValues: ALLOW`; `iam.disableServiceAccountKeyCreation`, `storage.publicAccessPrevention`, `iam.managed.allowedPolicyMembers`, `iam.managed.disableServiceAccountKeyCreation`, `storage.uniformBucketLevelAccess` → not enforced. So R3 needs no override (`allow_all_member_domains = false`) and R10's staging SA key is allowed.
- [x] Cloudflare: zone `f0d33de44af0b810eb19359ec4f8eb58`, SSL mode was **`full`** (saved in `meta/cloudflare-ssl-before.json`). All 31 records in `meta/cloudflare-records-all.json`; apex + `www` (proxied CNAMEs to `*.herokudns.com`) in `meta/cloudflare-records-before.json` (all mode 600). R18: apex and `www` pass cert verification against their Heroku origins (`ssl_verify=0`, 200). `donate.weallcode.org` (proxied → `customdomains.causevox.com`) already returns Cloudflare 525 today; Ali no longer uses CauseVox, so strict mode is fine. Follow-up: delete the dead `donate` record (live DNS change; ask Ali). Also seen: two SPF TXT records at the apex (Google + Mailchimp), which is a pre-existing SPF permerror; out of scope, tell Ali.
- [x] Resend domain `weallcode.org` created (id `6950dbb2-c19e-4fd6-9d86-60b11c713768`, us-east-1, `not_started`). Its 4 records (TXT `resend._domainkey`, MX + TXT `send`, CNAME `rsend` → `send.forge.rmta.net`) are in the gitignored `infra/terraform/terraform.tfvars`, with project, billing, zone and media bucket values. `staging_basic_auth_hash` is still a placeholder (Task F). Verify + sending key stay in Task F (R19).
- [x] SendGrid export → `heroku-backup-2026-11-23/sendgrid/` (raw) and `sendgrid-suppressions.json` (the `load_suppressions` input): 705 unsubscribes, 416 bounces, 0 blocks, 74 spam reports, 1 group ("Class Announcements", id 156190) with 86 suppressions; 1,276 unique addresses. Bounce reasons had raw control characters; they were stripped before parsing.
- [x] 1Password `homelab`: Secure Notes "WAC Heroku config <file>.env" for all 5 config files; read back, SHA-256 matches (robot-hub and wacdrop files are empty). Ali may now delete the plaintext `config/` files.
- [x] Sentry: the MCP here is the Braven account, so the DSN was read in Chrome (Ali signed in). Stored at `op://homelab/Sentry weallcode production DSN/credential`. **The DSN host changed** to `o4512487667466240.ingest.us.sentry.io` (has AAAA). Task F's IPv6 check uses that host, not `o161345.ingest.sentry.io`.
- [x] Daniel invited as Owner in the console; IAM shows `roles/resourcemanager.projectOwnerInvitee` for `Daniel.M.Conrad@gmail.com` until he accepts by email. Then import per R2 (Task F).

Recipient counts (Task B prerequisite, prod copy in the planning-session cluster `/tmp/e2micro/pg`, port 55432): active mentors 1,521 (1,001 after suppressions), active guardians 1,730 (1,265 after suppressions). 17 session announcements went out in the last 2 years; meetings none since 2017. So every announcement exceeds Resend's free 100/day and the 90 cap. Built behavior: the announce views refuse over the cap with an admin error, send nothing and leave the announced date unset. **Open for Ali (deferred, "decide later"):** how announcements go out after cutover (send elsewhere vs. a paid plan). GCP has no first-party transactional email service, so that's not an option.

Checkpoint 2 — **passed and committed** (lead's own checks):

- `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests.test_storage_settings coderdojochi.tests.test_email_util coderdojochi.tests.test_slack_notifications` → `Ran 24 tests ... OK`. `makemigrations --check --dry-run` → `No changes detected` (new migration `0041_email_suppression`).
- AC3 break: `fill_merge_fields` loop over `{}` instead of `values` → `FAILED (failures=2)` (per-recipient merge and unsubscribe-link tests); reverse edit → OK. AC4 break: empty-URL `return` → `pass` → `FAILED (failures=1)` (`test_skips_post_when_webhook_url_empty`); reverse edit → OK.
- Ruff on changed/new Python files: new files clean; `util.py` 19 → 13 errors (all pre-existing code), `notifications.py` 1 → 0; `old_views.py`, `meetings.py`, `urls.py`, `models/__init__.py`, `admin.py` counts unchanged. Format check: clean.
- `actionlint .github/workflows/ci.yml` → clean. Pinned tags exist on GitHub (`astral-sh/setup-uv@v10.3.2`, `hashicorp/setup-terraform@v4.0.0`). Task I ran the `django-postgres` job's steps locally on a scratch PG17: migrate, 285 fixture objects, `/ /programs/ /team/ /account/login/ /dj-admin/login/` → 200, `/admin/login/` → 404. The Django admin lives at `/dj-admin/`; `/admin/` is the app's own cdc-admin. Task G's smoke test should check `/dj-admin/login/`.
- No secrets in the tree (grep for Resend/SendGrid keys, private keys, the DSN key → none).

Deviations accepted from sub-agents: R13 "re-raise" replaced by continue + Sentry per failed recipient + one error log of unsent addresses; announce views clear the date and show an error if `email()` raises `ValueError`; SendGrid's own unsubscribe footer shows only on the SendGrid backend; the unsubscribe link text says it stops all We All Code email; rejected-address deactivation no longer raises when no user matches.

**Decided by Ali (session 2):** `group_unsubscribe` and `user_unsubscribe` suppressions block only the announcement templates (`class_announcement_guardian`, `class_announcement_mentor`, `meeting_announcement_mentor`); `bounce`, `block`, `spam_report` and `unsubscribe` (SendGrid global) block all mail. The announcement link text changes to match. Built as a follow-up commit by a sub-agent.

**Decided by Ali (session 2):** delete the dead `donate.weallcode.org` Cloudflare record (exported first to `meta/cloudflare-donate-deleted.json`). Done: record `624cf21c…` deleted via API. Scope follow-up committed: 26 tests OK, `makemigrations --check` clean, no new ruff errors.

PR: with Ali's OK, branch pushed and draft PR https://github.com/WeAllCode/website/pull/1613 opened. `main` had moved on (dependabot bumps), so `main` was merged in (aa8b443): kept main's ranges (`django-anymail[resend] <16`, `django-environ <0.15`), dropped `django-heroku` again, re-locked from main's `uv.lock` (no `psycopg2`; Django 5.2.17, Pillow 13). After the merge: 26 tests OK, `makemigrations --check` clean, `check --deploy` imports.

**Next (for a fresh session):** (1) Confirm CI on the PR is green (it had not reported when session 2 ended); fix failures in a follow-up commit. Keep the PR a draft until Checkpoint 3 passes (R4). (2) Ali's two decisions above. (3) Checkpoint 3 (Task F): generate the staging basic-auth password (1Password `homelab`) + hash into `terraform.tfvars`, `terraform init -backend-config="bucket=wac-tfstate-wac-website-7bda80"`, plan, Ali approves apply, then the Task F checks (Sentry host above), Resend verify + sending key, Daniel's binding import once he accepts.

### 2026-11-24 — session 3 (Checkpoint 3, Task F)

Account check first: `wac` config → `ali@weallcode.org`, project `wac-website-7bda80`. Terraform ran with `GOOGLE_OAUTH_ACCESS_TOKEN` from `gcloud auth print-access-token` and the Cloudflare token from `homelab` (no ADC).

- [x] tfvars: `staging_basic_auth_hash` = bcrypt from `caddy hash-password`, password at `op://homelab/WAC staging basic auth/password` (user `wac`). Temporary serial password at `op://homelab/WAC serial console wacadmin/password`; its `openssl passwd -6` hash was in tfvars only during the checks and is now commented out.
- [x] `terraform init -backend-config=bucket=wac-tfstate-wac-website-7bda80`, plan: 48 to add, 0 change/destroy. Checked in the plan JSON: e2-micro, us-central1-a, `debian-cloud/debian-12`, 30 GB `pd-standard`, `stack_type = IPV6_ONLY`, no `access_config`, zone `ssl = strict`, $1 budget (1/50/100%), 5 buckets in US-CENTRAL1, 3 secrets (no versions), DNS only `gcp.`/`staging.` AAAA (proxied) + 4 Resend records (not proxied), `cutover=false`. No name clashes with the 0b zone export. Ali approved → `Apply complete! Resources: 48 added`.
- [x] Right after the apply: `https://www.weallcode.org` and `https://weallcode.org` → 200 (`ssl_verify_result` 0), `/programs/`, `/team/`, `/account/login/` → 200 on Heroku; Cloudflare API shows `ssl = strict`. No revert needed.
- [x] VM `wac-web`: RUNNING, `IPV6_ONLY`, external IPv6 `2600:1900:4000:9c5b::`. First `provision.sh` run finished in about 6 minutes (`wac-provision: done 2026-11-24T17:32:05Z`), no errors.
- [x] Drift found by the next plan (would have broken AC5), fixed by a sub-agent: (1) the AAAA `content` used GCP's expanded IPv6 form while Cloudflare stores the compressed one, so `dns.tf` now runs `local.vm_ipv6` through `cidrhost("<addr>/128", 0)`; (2) `cloudflare_origin_ca_certificate.hostnames` forced a cert replace because Cloudflare returns the names sorted, so `tls.tf` now uses `sort(tls_cert_request.origin.dns_names)`. After the fix the plan showed only the `vm_ipv6` output change.
- [x] Serial console (Ali approved): apply with `serial_console=true` plus the hash, then `gcloud compute instances reset wac-web`. A reset is needed because `provision.sh` reads `wac-serial-password-hash` only at boot (the second boot logged "wacadmin has the temporary password"). Login as `wacadmin` over `gcloud compute connect-to-serial-port`, driven by `expect`. The check script was fetched from the deploy bucket, and its output was uploaded to the backup bucket and read from there (both objects deleted afterwards). Before disconnecting: `usermod -p '!' wacadmin` → `passwd -S` shows `L`.
- [x] Task F list, all on the VM over IPv6: `curl -6` deb.debian.org 200, pypi.org/simple/ 200, storage.googleapis.com 400, api.resend.com 200, `o4512487667466240.ingest.us.sentry.io` 404, www.google.com/recaptcha/api/siteverify 200, secretmanager.googleapis.com 404, oauth2.googleapis.com 404 (every one connected over IPv6; the status codes are the hosts' own answers to a bare HEAD). github.com fails as expected (no AAAA). `getent hosts metadata.google.internal` → `fd20:ce::254`. `systemctl is-active caddy postgresql wac-deploy@prod.timer wac-deploy@staging.timer wac-backup.timer` → all active. `free -m`: 969 MB total, 389 used, 580 available, swap 1023 MB. `df /`: 30 GB, 3.7 GB used. PostgreSQL 17.12; `wac` owned by `wac`, `wac_staging` owned by `wac_staging`. Listening: only Caddy `*:443` is reachable (sshd, LLMNR and exim are also listening, but the firewall allows only 443 from Cloudflare).
- [x] `systemd-analyze verify` on all `wac-*` units (templates as `@prod`/`@staging`): the only messages are that `/srv/wac/{prod,staging}/current/.venv/bin/gunicorn` doesn't exist yet. That's expected before the first deploy; there are no syntax errors. `caddy validate --config /etc/caddy/Caddyfile` → "Valid configuration". `nft -c -f /etc/wac/nftables-wac.nft` → rc 0.
- [x] R10: `nft list ruleset` has `meta skuid 994` (wac-staging) DNS accepts and drops to `fd20:ce::254` and `169.254.169.254`. `sudo -u wac-staging curl -6 -m5 ... http://metadata.google.internal/` → timeout (rc 28); the same against 169.254.169.254 → rc 28. Control: the same curl as `wac` → 200. wac-staging DNS (`getent ahosts pypi.org`) and egress (`curl -6 pypi.org/simple/` 200) work.
- [x] R20, curl part: metadata token over IPv6 (1024 chars), then a GCS JSON-API upload to the media bucket (`{"size":"12"}`) and a delete (204). Root read `wac-staging-sa-key` from Secret Manager over IPv6 (`type = service_account`). **Deferred to Checkpoint 4:** `google.auth.default()` plus a GCS write from the release venv; no venv exists before the first deploy.
- [x] Through Cloudflare (strict TLS to the Origin CA cert over IPv6): `https://staging.weallcode.org/` → 401 (Caddy basic auth), `https://gcp.weallcode.org/` → 502 (Caddy, no gunicorn yet). Both are expected.
- [x] Serial console off (Ali approved): `serial_console=false`, hash removed. Metadata shows `serial-port-enable=FALSE`.
- [x] Resend: `POST /domains/6950dbb2…/verify`, polled until `verified` (DKIM and the `rsend` CNAME first, `send` MX/TXT about 3 minutes later). Sending-only key "wac-website prod sending (weallcode.org)" (id `93f6a644-9955-4af1-a4c6-943cb3e690b4`, `sending_access`, scoped to the domain) at `op://homelab/Resend weallcode sending key/credential`.
- [x] Staging SA key (R10): `iam.disableServiceAccountKeyCreation` and `iam.managed.disableServiceAccountKeyCreation` are not enforced. Key `709426a9…` was created by piping `keys create /dev/stdout` straight into `gcloud secrets versions add wac-staging-sa-key` (version 1, enabled; it parses as `wac-staging-vm@…`).
- [ ] R2: Daniel has **not accepted** yet (IAM still shows `roles/resourcemanager.projectOwnerInvitee`). Import is pending; `project_owners` unchanged. Do it in Checkpoint 4 or later (README step 8).
- [x] AC5: after the final apply, `terraform plan -detailed-exitcode` → exit 0.
- [x] Stability (Ali asked): Cloud Monitoring CPU was 70% during first-boot provisioning and 2–4% idle since (25% in the reboot window), with no CPU steal. Hypervisor RAM-used is 620–660 MB (this includes page cache; the guest's own `free` showed 580 MB available). The serial log has no OOM, segfault, I/O error, soft lockup or hung task. The deploy timers fire and exit cleanly (pointers absent). The only failing unit is `google-oslogin-cache.service` at boot (NSS cache refresh; harmless, since login is by local user, not OS Login).

Observations for later (not blocking): `nftables.service` is inactive, so the R10 rules are loaded only by `provision.sh` at boot. They're in place now; if the Debian `nftables` service is ever enabled, its default config would flush them. A slip during the checks: one tfvars switch was changed with `sed` instead of Edit (no effect).

**Checkpoint 3 passed.** Per R4, ask Ali whether to mark PR 1613 ready and merge it before Checkpoint 4.

**Next (for a fresh session):** Checkpoint 4 (Task G), after PR 1613 merges: media copy, rehearsal restore via the transfer bucket (R11/R12), env secrets (R15, `GCE_METADATA_*` for R20), `release.sh --target prod`, R20's `google.auth.default()` proof, staging (4b), smoke test on `gcp.weallcode.org` (use `/dj-admin/login/`). Daniel's binding import when he accepts. Two gates in Checkpoint 4:

- R10 boot window (raised, then checked, session 3): already closed. `wac-staging.service` runs `ExecStartPre=+/usr/sbin/nft -f /etc/wac/nftables-wac.nft` (as root) before anything runs as `wac-staging`. `wac-manage` and `deploy-pull.sh` (line 189) also load it before any staging command. The earlier "nftables.service inactive" observation stands only as a caution: don't enable Debian's `nftables.service` without adding the `wac` table to its config. No code change.
- **Memory headroom:** at idle with nothing deployed the guest uses ~390 of 969 MB. The plan's estimate adds ~330 MB for the two gunicorns, leaving ~250 MB available plus 1 GB of swap. Not proven yet: record `free -m` and per-service memory with prod and staging both running (4b) before calling the VM stable under load.

### 2026-11-24 — session 4 (Checkpoint 4, Task G)

Branch `claude/wac-checkpoint-4-4de31f`, based on `origin/main` (`206d930`, PR 1613). Account check first: `wac` config → `ali@weallcode.org`, project `wac-website-7bda80`. Terraform used `GOOGLE_OAUTH_ACCESS_TOKEN` (no ADC). The `wac` gcloud login hit Workspace reauth (`rapt_required`) mid-session; Ali re-ran `gcloud auth login ... --no-launch-browser --force` (a plain login only reused the stale credentials).

- [x] G1 media: `aws s3 sync s3://weallcode/media/` (keys from the backup config) → `gcloud storage rsync` → `gs://wac-media-wac-website-7bda80/media`. S3 lists 1,164 objects (228.8 MB); GCS has 1,163. The one difference is S3's 0-byte `media/` folder marker. Local copy deleted. 4b: same 1,163 rsynced to `gs://wac-staging-media-…/media`.
- [x] G2 dump check: `pg_restore -f - production-wac.dump | grep -c s3.amazonaws.com` → 0 (`amazonaws|herokuapp` → 0). TOC extensions: only `pg_stat_statements` (and its COMMENT), so R11's filter is enough.
- [x] G3 secrets (Ali approved the key names): `wac-env-prod` and `wac-env-staging` built only from `env.<target>.example` keys by a scratch script, piped straight into `gcloud secrets versions add` (no file). Prod reuses Heroku's `SECRET_KEY`, so sessions and reset tokens survive cutover. Gotcha: the backup `.env` double-quotes values and escapes `\`, and systemd `EnvironmentFile` also parses quotes and backslashes. So the script unescapes the backup value and re-quotes it for systemd. On the VM, sha256(`settings.SECRET_KEY`)[:12] = `3a82325211c0`, the same as `heroku config:get SECRET_KEY` (50 chars). Staging has its own `SECRET_KEY`, the console backend, the staging bucket, and no `RESEND_API_KEY`. Both include `GCE_METADATA_HOST`/`GCE_METADATA_IP=metadata.google.internal` (R20). `versions access` → no `DATABASE_URL`, `SENDGRID_*`, `PAPERTRAIL_*`, `HEROKU_*` or `WEB_CONCURRENCY`. Dropped Heroku keys: `SITE_NAME`, `PAYPAL_*`, `AWS_*`, `HEROKU_POSTGRESQL_RED_URL`. Now at v1 + v2 per secret (v2 adds `ALLAUTH_TRUSTED_CLIENT_IP_HEADER`, below).
- [x] Serial console (Ali approved on → work → off): `terraform apply -var serial_console=true -var serial_console_password_hash=…` (passed as `-var`, because tfvars beats `TF_VAR_*`), in place, 0 destroy, then `gcloud compute instances reset wac-web`. Driven by an `expect` script: wait for the ssh banner before sending Ctrl-C (an early Ctrl-C kills gcloud locally), and answer `[sudo] password` prompts (wacadmin's sudo needs the password). Ops script sent through the transfer bucket. At the end: `/root/ops.sh` and `/root/cp4` removed, `usermod -p '!' wacadmin` → `passwd -S` `L`, apply `serial_console=false` → `serial-port-enable=FALSE`. That apply also updated `bootstrap.tgz` (env examples changed); after the first prod deploy the VM ignores it (README).
- [x] G2 rehearsal restore (R11, R12): the dump went to `gs://wac-transfer-…` (never the deploy bucket), then to `/srv/wac/prod/cp4-restore` (the first try in `/root` failed: `wac` can't traverse `/root`). Then `pg_restore -L toc --no-owner --no-acl --role=wac --exit-on-error --single-transaction -d wac` → rc 0, 0 → 50 public tables. Dump shredded on the VM and removed from the bucket; the bucket is empty.
- [x] G4 prod: `release.sh --target prod origin/main` (206d930), `systemctl start wac-deploy@prod` → "wac-web is running … done". `showmigrations` → 0 unapplied (the 11 pending migrations applied on the restored data). `DEBUG False`, `db wac`, Resend backend.
- [x] **R20 proven** from the release venv (`wac-manage prod shell`): `google.auth.default()` → `google.auth.compute_engine.credentials.Credentials`, project `wac-website-7bda80`, in 0.02 s (no IPv4 timeout). A GCS write to `media/r20-proof.txt` took 0.43 s, `exists()` True, then deleted. Django `default_storage.save` → `https://storage.googleapis.com/wac-media-wac-website-7bda80/media/r20-django.txt`, then deleted.
- [x] R8 rehearsal: `load_suppressions` → 1,276 created (unsubscribe 704, bounce 416, group_unsubscribe 82, spam_report 74). JSON sent through the transfer bucket and shredded afterwards. Task H step 3 now re-runs it after the cutover restore.
- [x] 4b staging: `release.sh --target staging origin/main` → deployed. `wac-refresh-staging-db` → done (it needs the staging env, so deploy staging first). `wac-staging` active: `DB_NAME wac_staging`, console backend, staging bucket. Through Cloudflare: no auth → 401; basic auth → 200 on `/ /programs/ /team/ /account/login/ /dj-admin/login/`; `X-Robots-Tag: noindex, nofollow`; media 200 from the staging bucket. Password reset on staging → 302 `/account/password/reset/done/`, and the mail (`Subject: [weallcode.org] Password Reset E-mail`, To ali@weallcode.org) is only in `journalctl -u wac-staging`. Resend's sent list is unchanged. **The staging basic-auth user is `staging`, not `wac`;** the 1Password item's username was corrected.
- [x] **Memory gate** (prod 2 workers + staging 1 worker, after ~30 page loads on each): `free -m` total 969, used 816, available 153, swap used 55 of 1023 (an earlier reading: available 114, swap 23). systemd `MemoryCurrent`: wac-web 236 MiB (cap 450M), wac-staging 149 MiB (cap 200M), postgresql 80 MiB, caddy 34 MiB. Gunicorn RSS: prod workers ~112 MB each + master 68 MB; staging worker ~112 MB + master 76 MB. That is above the plan's estimate (~630 MB used, staging ~110 MB): measured 816 MB used, staging 149 MiB, closest to its cap (~75%). Stable (no OOM, swap barely used), but tight. If prod grows or swap climbs, the first lever is stopping `wac-staging` when it isn't in use.
- [x] G5 smoke test (`https://gcp.weallcode.org`; Heroku is shown for the same path): `/` 200/200, `/programs/` 200/200, `/team/` 200/200, `/account/login/` 200/200, `/dj-admin/login/` 200/200. CSS (`text/css`) and static favicons load from `storage.googleapis.com/wac-media-…/static/…`; uploaded images (`media/associate-board/*.jpg`) are 200 `image/jpeg`. Admin: with Ali's OK, a temporary superuser `cp4-smoke` (pk 10026, password at `op://homelab/WAC gcp rehearsal superuser cp4-smoke`) was created in the rehearsal DB; the cutover restore wipes it. Logged in at `/dj-admin/` and uploaded a JPEG through AssociateBoardMember add, which landed at `gs://wac-media-…/media/associate-board/cp4-smoke.jpg` (200). Then the row and the object were deleted.
- [x] **Bug found and fixed (PR https://github.com/WeAllCode/website/pull/1614, merged as `ac0c60e`, Ali approved merging on green CI):** every allauth POST returned 403. gunicorn on a Unix socket leaves `REMOTE_ADDR` empty, so allauth's rate limiter raised `PermissionDenied("Unable to determine client IP address")`. Fix: `ALLAUTH_TRUSTED_CLIENT_IP_HEADER` read from the env, set to `CF-Connecting-IP` in both env examples and in the secrets' v2 (443 accepts only Cloudflare), plus `coderdojochi/tests/test_client_ip.py` (3 tests; 29 OK in total; break check fails as expected). CI: tests, django-postgres, infra, pre-commit all pass. Redeployed both with `release.sh --force origin/main`: prod and staging run `ac0c60e`, the header is `CF-Connecting-IP` in both, 0 unapplied migrations. After the fix, the prod login POST with a wrong password → 200 with the form error (no 403, no email).
- [x] AC3 email: `coderdojochi.util.email(template_name="class_reminder_guardian_one_week", recipients=["ali@weallcode.org"], merge_data=…)` was sent once from prod; Resend shows it `delivered` to ali@weallcode.org. **Ali (session 4): never send actual emails from here on.** So the prod password-reset email from step 5 was not sent. The reset flow was proven on staging (console backend), and the Resend send path by the `util.email()` message above. Resend's stored copy (`GET /emails/<id>`, full-access key; read only, nothing sent) has 14,389 chars of body, "AliMerged" twice, "TestStudent" once, and 0 `*|`. AC3 passes.
- [x] AC5: after the serial-off apply, `terraform plan -detailed-exitcode` → 0.
- [ ] R2: Daniel still has `roles/resourcemanager.projectOwnerInvitee` (not accepted). Import later (README step 8).

**Checkpoint 4 passed.**

**Next (for a fresh session):** Checkpoint 5 (Task H) when Ali picks a quiet time. Before step 2, note: the rehearsal data (cp4-smoke user, suppressions) is replaced by the cutover restore; re-run `load_suppressions` (Task H step 3). Before cutover, also decide the open announcement-volume question (session 2). Don't send any real email during cutover checks; check Resend's sent list instead.

### 2026-11-24 — session 5 (Checkpoint 5, Task H, cutover)

Started at once on Ali's call (Tue ~4pm CT). Account check first: `wac` config → `ali@weallcode.org`, project `wac-website-7bda80`. Terraform used `GOOGLE_OAUTH_ACCESS_TOKEN` (no ADC), from a fresh worktree on `main` (`9aca9c3`) with the gitignored `terraform.tfvars` copied from the original worktree. Baseline `terraform plan -detailed-exitcode` → 0.

- [x] Prep before maintenance (Ali approved): apply `serial_console=true` + hash (`-var`, in place, 1 change), then `gcloud compute instances reset wac-web`. Same `expect` serial method as session 4. The ops script `cut.sh` was sent through the transfer bucket (sha256 checked on the VM) and the object removed. Heroku baselines saved before maintenance: `/ /programs/ /team/ /account/login/ /dj-admin/login/` → 200 on apex and www, no redirects.
- [x] H1 (Ali approved): `heroku maintenance:on -a production-wac` at **16:22:39 CT** (22:22:39Z). `/account/login/` → 503.
- [x] H2: `pg:backups:capture` → b27918, finished 22:22:44Z (after maintenance on), 6.49 MB. Downloaded to `heroku-backup-2026-11-23/production-wac-cutover-2026-11-24.dump` (mode 600), sha256 `b31ed6ed…89ea21`. Sent via the transfer bucket only. On the VM: stop `wac-deploy@prod.timer`, `wac-deploy@prod.service` and `wac-web`; same sha256; the TOC has 50 TABLE DATA entries (the script aborts before `dropdb` if it has fewer than 40); `dropdb --force wac`, `createdb -O wac wac`, re-grant CONNECT; R11 TOC filter, then `pg_restore --role=wac --exit-on-error --single-transaction` → rc 0, 50 tables. Dump shredded on the VM, removed from the bucket, bucket empty.
- [x] **AC7 passes**: exact `count(*)` per public base table (single `query_to_xml` query), run on a local PG 17 restore of the same dump (same TOC filter) and on the VM before any migration. Saved as `ac7-counts-local.txt` / `ac7-counts-vm.txt`. `diff` → rc 0, `ac7-diff.txt` empty. 50 tables, 72,524 rows. Gotcha: psql opened `less` on the serial tty and hung the console. Piping through `| cat` fixed it, and a small expect script sent `q` to free the console.
- [x] H3: `release.sh --target prod --force origin/main` → pointer `9aca9c3…:20261124T223325Z`; `systemctl start wac-deploy@prod` → "done". `showmigrations` → 0 unapplied (12 applied on the Heroku data), `wac-web` active, timer active, `DEBUG False`, Resend backend, 3,639 users, `cp4-smoke` gone. `load_suppressions` → 1,276 created (unsubscribe 704, bounce 416, group_unsubscribe 82, spam_report 74). The JSON went through the transfer bucket and was shredded on the VM and removed from the bucket. Bucket empty. Cleanup: `/root/cut.sh` removed, `wacadmin` locked (`passwd -S` `L`).
- [x] H4 (Ali approved, one approval for both): deleted the two Heroku CNAMEs from `cloudflare-records-before.json` (`7a2dcf46…` apex → `glacial-crab-…herokudns.com`, `ddfe61a0…` www → `mysterious-bug-…herokudns.com`) via the API. Then immediately ran `terraform apply` of a saved plan with `cutover=true serial_console=false` → "2 added, 1 changed, 0 destroyed" (AAAA apex → `2600:1900:4000:9c5b::` proxied, CNAME www → apex proxied, serial off). **Live on GCP at 16:40:16 CT**, about 13 s after the deletes. Maintenance window ≈ 18 min. `cutover = true` is persisted in this worktree's tfvars and, with Ali's OK, in the `heroku-free-hosting-migration-a21bab` worktree's tfvars, so an apply from either won't remove apex/www.
- [x] **AC1 passes**: apex and www, `/ /programs/ /team/ /account/login/ /dj-admin/login/` → 200, same as the Heroku baseline. Response headers `via: 1.1 Caddy`, `server: cloudflare`. Google login in Chrome on `https://www.weallcode.org` → Google account chooser (redirect_uri `www…/account/google/login/callback/`) → "Successfully signed in" on Ali's existing profile (joined 2013). `/dj-admin/` on www → site admin with real recent actions and the Email suppressions model. The apex has its own session (host-only cookie, no apex→www redirect, same as Heroku).
- [x] **AC2 passes**: home page CSS `…/wac-media-wac-website-7bda80/static/weallcode/css/app.d47ab30dc138.css` → 200 `text/css`; `/team/` image `…/media/staff/ali-karbassi-2.jpg` → 200 `image/jpeg`. The admin upload into GCS was proven in CP4 and not repeated on prod data.
- [x] **AC5 passes**: `terraform plan -detailed-exitcode` → 0 after the cutover apply.
- [x] Sentry `we-all-code-p5`, last hour: the only issue is a `/test-sentry/` ZeroDivisionError from ~47 min before the check (before cutover), so no new errors after cutover. Resend sent list: newest is the CP4 smoke test at 20:00Z. No email was sent during cutover.
- [x] Heroku `production-wac` stays in maintenance mode (`heroku maintenance` → `on`).

Leftovers (not blocking): `/root/f.sh` and `/root/f-out.txt` from an earlier session are still on the VM; delete them at the next serial session. The rollback dump is the cutover dump above; keep it at least until Heroku is deleted.

**Checkpoint 5 passed (AC1, AC2, AC5, AC7).** Follow-ups:

- [ ] **Day 3, 2026-11-27 (AC6):** GCP billing report filtered to `wac-website-7bda80` shows $0.00. If any SKU shows a charge, record it and stop for Ali.
- [ ] **Day 7, 2026-12-01 (AC8):** first `heroku addons:open papertrail -a production-wac`. Ali downloads the archives to `heroku-backup-2026-11-23/papertrail/`, and the lead checks the folder isn't empty. Confirm the Sentry project transfer (done in 0a). Then Ali deletes `production-wac`, `wac-nocodb`, `wac-robot-hub` and `wacdrop` and cancels the Eco dynos plan. `heroku apps` lists none of them.
- [ ] After day 7 (H9): small PR removes `Procfile`, `app.json`, the Heroku `release` task in `tasks.py`, and points the `README.md` deploy notes at `infra/`. CI must pass.
- [ ] H6b: Sentry uptime monitor on `https://www.weallcode.org/` in `we-all-code-p5`, email alerts to Ali (not done this session; the Sentry MCP here is the Braven account, so use Chrome).
- [ ] Day 30, 2026-12-24 (H7b): with Ali's OK, delete `s3://weallcode` after a final `aws s3 ls --summarize` matches GCS, then review AWS billing.
- [ ] R2: import Daniel's Owner binding once he accepts.
- [ ] Open (Ali deferred): announcements over 90 recipients are refused (Resend free tier).

Sub-agent reports (session 4):

- allauth client IP: `settings.py` `ALLAUTH_TRUSTED_CLIENT_IP_HEADER = env(..., default=None)`; env examples set `CF-Connecting-IP`. allauth (`core/internal/httpkit.py:213`) reads only that header when it is set, with no `REMOTE_ADDR` fallback, and reads the setting live, so `override_settings` works in tests. Break checks: setting `None` → test 3 fails; override `None` → test 1 `PermissionDenied`.

Sub-agent reports (session 3):

- Drift fix: `dns.tf` `vm_ipv6` local wrapped in `cidrhost(...)/128`; `tls.tf` `hostnames = sort(tls_cert_request.origin.dns_names)` (first attempt used an explicit list in the wrong order; the lead caught it on the live plan and corrected it). `fmt -check`, `validate` pass; `terraform console`: `cidrhost("2600:1900:4000:9c5b:0:0:0:0/128", 0)` → `"2600:1900:4000:9c5b::"`.

Sub-agent reports (session 2):

- Task B: 21 tests in `test_email_util.py`; migration only adds EmailSuppression; `deliverable_recipients()` / `email_daily_limit()` helpers shared with the announce views; unsubscribe page is GET confirm + POST, bad token → 400; `load_suppressions` reason precedence spam_report > bounce > block > unsubscribe > group_unsubscribe, idempotent. Only the meeting announce view has view tests; the two session announce views follow the same code.
- Task C: early return on empty URL, `timeout=5`, `RequestException` logged; 3 tests.
- Task I: `ci.yml` with `tests`, `django-postgres`, `infra` jobs, `permissions: contents: read`, no secrets; console email backend and `DJANGO_SECURE_SSL_REDIRECT=False` in the Postgres job.

Sub-agent reports (session 1):

- Task A: proof 1 (5 tests OK) and proof 2 (`check --deploy`, 4 warnings, no ImportError) pass. Proof 3 fails repo-wide because of code that was already there: `ruff check coderdojochi` shows 285 errors, and `ruff format --check` wants to reformat `util.py`. Task A's new and changed blocks are clean. The SQLite fallback wasn't needed.
- Task D: `fmt`, `init -backend=false` and `validate` pass. The bootstrap archive is tar.gz (`archive_file`, files at the archive root). Additions: `soft_delete_policy` 0 on the transfer bucket, `*.tfplan` in `.gitignore`, no budget `all_updates_rule`. Risk: secure-by-default org constraints `iam.disableServiceAccountKeyCreation` and `storage.publicAccessPrevention` may also apply; 0b checks them alongside R3.
- Task E: shellcheck and `bash -n` clean. `caddy validate` passes on a scratch copy; the repo copy needs the generated `wac-staging-auth.caddy`. Method: curl + metadata token over IPv6 (no gcloud on the VM). Deviations to review: only prod deploys install infra files, `/etc/wac` is 0711, nftables allows DNS to the metadata IP for staging, `OnBootSec=3min` added to the timer, admin user `wacadmin`.
