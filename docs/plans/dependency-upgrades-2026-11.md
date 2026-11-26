# Upgrade every dependency to its latest stable version

Status: **approved by Ali 2026-11-24.** Nothing built, pushed or deployed yet. Written 2026-11-24 from `main` at `f940d74`.

**Ali's decisions (2026-11-24) — these override the recommendations below:**

- D1: Python 3.13 now (Checkpoint 7). Django 6.2 LTS in April 2027 (Checkpoint 8 waits for 6.2 and released Django 6 support in storages/recaptcha).
- D2: front-end latest within each major, as written. **Added by Ali:** vendor all third-party fonts, CSS and JS and host them ourselves (Checkpoint 9).
- D5: replace the dead Universal Analytics snippet (`UA-78618586-1`) with GA4 in Checkpoint 9 (tasks 9B and 9F). The GA4 tag is rendered only when the `GA_MEASUREMENT_ID` setting is set. Ali supplies the `G-…` ID and adds it to `wac-env-prod` only, never staging.
- D3: sentry-sdk 3 waits for 3.0.1+ or 2 weeks after 3.0.0, whichever comes first; until then keep `<3`.
- D4: **keep** `coderdojochi/cron.py` and django-cron. Ali wants the reminders back, and that is a separate task. In 1C, do **not** remove django-cron or delete `cron.py`. Checkpoint 8 gets a precondition: the reminders task must have replaced or fixed django-cron (its models use `index_together`, removed in Django 5.1), or django-cron must have a release that supports Django 6. **Update:** the reminders task opened https://github.com/WeAllCode/website/pull/1625 (a `send_reminders` command plus a prod-only timer, and django-cron removed). **Done 2026-11-24:** #1625 squash-merged as `ee9b6d0` and released to prod. django-cron and `cron.py` are gone from main, so 1C has nothing to remove for them and Checkpoint 8's precondition is met. Start CP1 from a main that includes `ee9b6d0`, and re-check the `settings.py` line numbers 1C cites (they may have shifted). Prod reminders stay off until `/etc/wac/reminders-enabled` exists (Ali's separate OK).

## Goal and done

**User story.** As the maintainer of weallcode.org, I want every dependency (Python packages, the Python runtime, front-end CDN libraries, GitHub Actions, Terraform providers and pre-commit hooks) on its latest stable version, shipped as small PRs that each go through staging before prod, so the site stays secure and supported without an outage on the 1 GB e2-micro.

**Acceptance criteria.**

1. Every package in the version table below is at its target version, or the table says why not (with Ali's sign-off on that row).
2. The upgrades land as the ordered PRs in Checkpoints 1–8; each PR is green in CI, deployed to staging, smoke-tested with Playwright, then merged and released to prod with Ali's OK.
3. CI runs the **whole** test suite (all of `coderdojochi.tests`, `accounts`, `weallcode`), not 4 named modules, and the 2 tests that fail on `main` today pass.
4. CI proves `sentry_sdk.init()` runs with a DSN set (today it never runs in CI because `SENTRY_DSN` is unset).
5. After each prod release: `/`, `/programs/`, `/team/`, `/account/login/`, `/dj-admin/login/` return 200 through Cloudflare; no new Sentry issues in the hour after; staging `MemoryPeak` (and prod's, where checked) is within +10% of the Checkpoint 0 baseline (R14).
6. Every prod release has a written rollback path that was checked before release (previous main sha recorded; DB backup taken when the PR adds migrations).
7. Dead dependencies are removed instead of upgraded (list in Checkpoint 1).
8. Every third-party font, CSS and JS file is vendored under `coderdojochi/static/vendor/` and served from our own static bucket. The only remaining third-party hosts are the services on the Checkpoint 9 allowlist (reCAPTCHA, Google Charts, GA4 gtag).

**Direction (Ali, 2026-11-24):** we want to move away from old front-end code: jQuery, Foundation, and by extension Bootstrap 3, Font Awesome 4/5 and what-input. Checkpoint 9 only upgrades and self-hosts what's there, as a stopgap that fixes the known CVEs and drops third-party CDNs. Replacing these with plain modern JS/CSS is a separate project to plan after this one. Don't add any new jQuery- or Foundation-dependent code in these PRs.

**Out of scope.** Moving the VM to Debian 13 (new boot disk, and Postgres lives on it). Bootstrap 3 → 5, Font Awesome → 6/7, jQuery 4, Foundation 7 ("Yeti"): these are rewrites of the HTML/CSS, not upgrades (see "Front-end scope" below). Replacing the old Google `jsapi` chart loader in `session_stats.html`.

### Decisions Ali must make before Checkpoint 7–8 (asked at hand-over)

- **D1. Django 6 / Python 3.13.** Django 6.0 and 6.1 need Python ≥ 3.12; the VM runs Debian 12's Python 3.11. Django 5.2 is LTS until April 2028; 6.1 is supported only to December 2027; the next LTS, 6.2, ships April 2027. django-storages 1.14.6 and django-recaptcha 4.1.0 have no released Django 6 support yet (only on their main branches). **Recommendation:** do Checkpoint 7 (Python 3.13 on Django 5.2) now, and Django 6.2 LTS as Checkpoint 8 in April 2027 once storages and recaptcha release Django 6 support. Checkpoint 8 is written so it can also be run now for 6.1 if Ali prefers.
- **D2. Front-end scope.** Latest within each major (jQuery 3.8.0, Bootstrap 3.4.1, Font Awesome 4.7.0 / 5.15.4, Foundation JS 6.9.0, what-input 5.2.12). **Recommendation: yes.**
- **D3. sentry-sdk 3.0.0** is a `.0` release that removes options this repo uses. **Recommendation:** ship it (Checkpoint 6) but only once 3.0.1+ exists or after 2 weeks, whichever first; until then pin `<3`.
- **D4. Dead code.** `coderdojochi/cron.py` (`SendReminders`) is never scheduled (no `CRON_CLASSES`, `django_cron` not in `INSTALLED_APPS`, nothing runs `runcrons`), and django-cron's models break on Django ≥ 5.1. **Recommendation:** delete it with django-cron in Checkpoint 1 (git keeps it).

## Version table

Current = `uv.lock` / files at `f940d74`. "Major" = breaking-change notes apply (see "Breaking changes" below). Checkpoint = where it lands.

### Python (direct)

| Package | Current | Target | Major? | CP |
|---|---|---|---|---|
| Python | 3.11 (Debian `/usr/bin/python3.11`) | 3.13 (uv-managed) | yes | 7 |
| django | 5.2.17 | 5.2.19 (6.1.3 / 6.2 gated by D1) | 6.x yes | 3 (8) |
| django-allauth[socialaccount] | 65.19.6 | 65.22.1 | behaviour | 3 |
| psycopg[binary] | 3.2.9 | 3.3.9 | minor | 3 |
| dj-database-url | 3.0.1 | 3.1.2 | | 3 |
| django-storages[google] | 1.14.6 | 1.14.6 (latest) | | — |
| django-recaptcha | 4.1.0 | 4.1.0 (latest) | | — |
| django-loginas | 0.3.11 | 0.3.14 | | 3 |
| django-anymail[resend] | 13.0 | 15.3 | yes | 4 |
| django-bootstrap3 | 25.1 | 26.3 | yes | 3 |
| django-active-link | 0.2.2 | 0.3.0 | minor | 3 |
| django-meta | 2.5.0 | 2.5.1 | | 3 |
| pillow | 13.0.0 | 13.0.0 (latest; raise floor to 13.0) | | 3 |
| django-stdimage | 6.0.2 | 6.0.2 (latest; repo archived) | | — |
| django-cleanup | 9.0.0 | 9.0.0 (latest) | | — |
| arrow | 1.3.0 | 1.4.0 | | 3 |
| icalendar | 6.3.1 | 7.3.2 | yes | 4 |
| django-appconf | 1.1.0 | 1.2.0 | | 3 |
| django-import-export | 4.3.9 | 4.4.6 | behaviour | 3 |
| django-environ | 0.12.0 | 0.14.0 | | 3 |
| django-debug-toolbar | 5.2.0 | 8.0.0 | yes | 4 |
| ruff | 0.12.5 | 0.17.6 | yes | 2 |
| factory-boy | 3.3.3 | 3.3.3 (latest) | | — |
| gunicorn | 23.0.0 | 27.0.1 | yes | 5 |
| sentry-sdk | 2.76.0 | 3.0.x | yes | 6 |
| invoke | 2.2.0 | 3.0.3 | yes | 4 |
| pre-commit (dev) | 4.2.0 | 4.7.0 | | 2 |
| python-dateutil (**used directly** in `coderdojochi/forms.py:4`, not declared) | 2.9.0.post0 (transitive) | 4.0.0, declared | yes | 4 |
| django-html5 | 1.0.0 | **remove** (Django has the widget) | | 1 |
| django-nose | 1.4.7 | **remove** (unused; `nose` imports `imp`, gone in 3.12) | | 1 |
| django-common-helpers | 0.9.2 | **remove** (unused; breaks on import since Django 4) | | 1 |
| django-fullurl | 1.4 | **remove** (unused) | | 1 |
| json-logging-py | 0.2 | **remove** (unused) | | 1 |
| mock | 5.2.0 | **remove** (tests use `unittest.mock`) | | 1 |
| django-cron | 0.6.0 | already removed by #1625 (`ee9b6d0`) | | — |

### Python (transitive majors worth knowing)

`uv lock --upgrade` inside today's bounds also pulls: python-dateutil 2.9 → **4.0**, faker 37 → **40**, pycparser 2 → **3**, asgiref 3.9 → 3.13, pydantic 2.13 → 2.14, cryptography 50.0.0 → 50.0.2, six removed. faker is only used by factory-boy in tests. All other transitive packages (google-cloud-storage 3.17.2, etc.) are already latest.

### Front-end (CDN today; Checkpoint 9 vendors all of these into `coderdojochi/static/vendor/`, plus Google Fonts and the Sentry browser bundle on `500.html`)

| Library | File | Current | Target |
|---|---|---|---|
| jQuery | `weallcode/templates/weallcode/_base.html:73` | 3.4.1 | 3.8.0 |
| what-input | `_base.html:74` | 5.2.1 | 5.2.12 |
| Foundation JS | `_base.html:75` (CSS is local 6.5.1) | 6.5.1 | 6.9.0 |
| Font Awesome | `_base.html:34` | 5.8.2 | 5.15.4 |
| seamless-scroll-polyfill | `_base.html:77` | 1.0.0 | **remove** (2.x dropped the auto-polyfill file; native `scroll-behavior` covers current browsers) |
| jQuery | `coderdojochi/templates/dashboard/_admin_base.html:45` | 1.12.4 | 3.8.0 |
| Bootstrap CSS+JS | `_admin_base.html:14,48` | 3.3.7 | 3.4.1 |
| Font Awesome | `_admin_base.html:13` | 4.6.3 | 4.7.0 |
| js-datepicker | `coderdojochi/templates/welcome.html:8,79` | 5.18.0 | 5.18.4 |

### GitHub Actions

| Action | Where | Current | Target |
|---|---|---|---|
| actions/checkout | ci.yml ×3, pre-commit.yml | v6 | v7.0.1 |
| actions/setup-python | ci.yml ×2 | v6 | v7.1.0 |
| actions/setup-python | pre-commit.yml | v7 | v7.1.0 |
| actions/cache | pre-commit.yml | v6 | v6.1.0 |
| astral-sh/setup-uv | ci.yml ×2 | v10.3.2 | v10.4.0 |
| hashicorp/setup-terraform | ci.yml | v4.0.0 | v4.0.1 |
| stefanzweifel/git-auto-commit-action | pre-commit.yml | v7 | v7.2.1 |
| dependabot/fetch-metadata | dependabot-auto-merge.yml | v3.1.0 | v3.1.0 (latest) |

### Terraform and pre-commit

| Item | Current | Target |
|---|---|---|
| hashicorp/google | `~> 8.11`, lock 8.12.0 | no change (8.12.0 is latest) |
| cloudflare/cloudflare | `~> 5.29`, lock 5.29.0 | no change (latest) |
| hashicorp/tls | `~> 4.0`, lock 4.4.2 | no change (latest) |
| hashicorp/archive | `~> 2.7`, lock 2.8.1 | no change (latest) |
| pre-commit-hooks rev | v5.0.0 | v6.0.0 |
| ruff-pre-commit rev | v0.12.5 | v0.17.6 |

Terraform needs no PR. Re-check `curl -s https://registry.terraform.io/v1/providers/hashicorp/google | jq -r .version` (and the other three) at Checkpoint 2; if a newer one appeared, add it to Checkpoint 2 as `terraform -chdir=infra/terraform init -upgrade -backend=false` + `validate`, and apply only with Ali.

## Breaking changes that touch this repo

Only items that matter here. Full notes: URLs at the bottom.

- **Django 6.0/6.1 (D1):** Python ≥ 3.12. 6.0: `DEFAULT_AUTO_FIELD` default becomes `BigAutoField` (this repo already sets `AutoField` at `coderdojochi/settings.py:360`, so no migrations), positional args to `Model.save()` removed, email internals rewritten, `ADMINS`/`MANAGERS` as tuples deprecated. 6.1: PostgreSQL 15+ (VM and CI run 17), `first()`/`last()` stop ordering by pk after an empty `order_by()`, admin breadcrumbs markup changes, `EMAIL_*` → `MAILERS` deprecation, cache keys change once.
- **sentry-sdk 3.0:** `init()` raises `TypeError` on removed options. This repo passes two: `enable_logs` and `send_default_pii` (`coderdojochi/settings.py:344-357`). `LoggingIntegration` is no longer on by default, so the Sentry Logs from #1623 stop unless it is added explicitly (`LoggingIntegration(level=logging.INFO)`; note the renames: old `sentry_logs_level` is now `level`, old `level` is now `breadcrumb_level`, `event_level` now defaults to `None`). `send_default_pii` is replaced by `data_collection`, which collects more by default. `DjangoIntegration(transaction_style=)` removed (not used here). `last_event_id`, `capture_message`, `new_scope` still exist in 3.0.0 (checked in the wheel's `sentry_sdk/api.py`). The `sentry-sdk[django]` extra is gone (not used here). Span streaming is the only tracing mode: watch staging memory.
- **gunicorn 24–27:** Python ≥ 3.10. **25.1 creates a control socket by default** at `$XDG_RUNTIME_DIR/gunicorn.ctl` or `$HOME/.gunicorn/gunicorn.ctl`. The services run as system users with `HOME=/nonexistent` (`infra/vm/provision.sh:232`), `ProtectHome=true` and `ProtectSystem=full` (`infra/vm/wac-web.service:25-26`), so that path is not writable. Turn it off (see Checkpoint 5). 25.3/27.0 reject malformed requests more strictly (Caddy in front sends clean HTTP/1.1, so expect no effect). No sync-worker default changed.
- **django-anymail 14/15:** Resend raises if an attachment's extension doesn't match its content type (this repo attaches inline images in `coderdojochi/signals_handlers.py` via `MIMEImage`; check). `fail_silently` deprecated in 15.1 (grep it). Needs Django ≥ 5.0.
- **django-debug-toolbar 6–8:** shadow DOM in 7.0, redesign in 8.0. `debug_toolbar.urls` include at `coderdojochi/urls.py:342-346` still works. Dev-only; prod never installs it into `INSTALLED_APPS` (`DEBUG` is False).
- **django-bootstrap3 26:** Python ≥ 3.11, Django ≥ 5.2, new system check `bootstrap3.W001` for unknown `BOOTSTRAP3` keys (this repo has no `BOOTSTRAP3` setting). XSS fix in labels.
- **icalendar 7:** `decoded()` returns `str`; `UIDGenerator` removed; wrong property types raise `TypeError`. Used only in `coderdojochi/views/calendar.py` (`Calendar`, `Event`, `vText`).
- **invoke 3:** only `run(disown=True)` and `Call.make_context()` changed. Used in `tasks.py` (dev tasks).
- **python-dateutil 4.0:** check its changelog for `relativedelta` (used at `coderdojochi/forms.py:4`) before bumping; if anything in `relativedelta` changed, pin `<4` and record why.
- **psycopg 3.3:** Python ≥ 3.10; binary default `gssencmode=disable` (we use the Unix socket; no effect).
- **django-allauth 65.20–65.22:** a recent login no longer counts as reauthentication; social-only accounts without a password are denied reauth-gated views; setting a password needs reauth when `ACCOUNT_REAUTHENTICATION_REQUIRED` is on. Test login, logout, password change, social login (prod only, see Proof).
- **django-import-export 4.4.2+:** rows with an existing pk that the loader didn't match now error instead of overwriting (security fix). Admin import flows in `coderdojochi/admin.py:12-15`.
- **ruff 0.13–0.17:** rule `UP038` removed; selecting or ignoring it by code is now an error — it is in `pyproject.toml` `ignore` and `extend-unsafe-fixes`. 0.15 2026 formatter style reformats code. New stable rules under the selected prefixes (`ASYNC`, `B`, `PL`, `RUF`, `UP`, `TID`, …) will report new findings.
- **pre-commit-hooks v6:** `check-byte-order-marker` and `fix-encoding-pragma` removed (neither used here). **pre-commit 4.7:** needs Python ≥ 3.11 (CI uses 3.11; fine).
- **actions/checkout v7:** refuses fork PR checkout under `pull_request_target`/`workflow_run` (no workflow here uses those). **setup-python v7:** `pip-install` input removed (not used).
- **jQuery 1.12 → 3.8 (dashboard):** strict mode, async ready, `.load()/.size()/.andSelf()/.error()/.unload()` removed, `$("#")` throws, `.data()` dash handling, `htmlPrefilter` no longer expands `<div/>`. Fixes CVE-2015-9251, CVE-2019-11358, CVE-2020-11022, CVE-2020-11023. A grep of templates and `coderdojochi/static/js` found no `.load(`/`.size(` jQuery calls (the hits are `google.charts.load`).
- **Bootstrap 3.3.7 → 3.4.1:** fixes CVE-2016-10735, CVE-2018-14040/14042/20676/20677, CVE-2019-8331. `data-target`/`href` selectors are resolved with `$(document).find`; tooltip/popover HTML is sanitized. 3.x is EOL: CVE-2024-6485 and CVE-2025-1647 stay unfixed (no 3.x fix exists). Bootstrap 3.4.1 JS **throws on jQuery 4**, which is why D2 stops at jQuery 3.8.
- **Font Awesome 5.8.2 → 5.15.4:** removes `fa-nintendo-switch`, `fa-adobe`, `fa-tripadvisor`; renames `fa-haykal` → `fa-bahai`. A grep found none of them in the repo.
- **Foundation JS 6.5.1 → 6.9.0** on the local 6.5.1 CSS: safe to mix (breakpoints read the same way; only 13 new utility classes). Needs jQuery ≥ 3.6 and what-input ≥ 5.2.10, so the three move together. 6.6 renamed `closed.zf.offcanvas` → `close.zf.offcanvas` (not used in `weallcode/static/weallcode/js/app.js`).

## Read first

Builder: read these before any task.

- `pyproject.toml` (whole file): dependency bounds (the upper bounds are why `uv lock --upgrade` stops at gunicorn 26 and sentry 2.76), ruff config (`UP038` in two places), `requires-python`.
- `uv.lock`: never hand-edit; regenerate.
- `.github/workflows/ci.yml:1-163`: the `tests` job runs 5 named modules in step "Run tests" (#1625 added `test_send_reminders`); `django-postgres` runs migrate, `makemigrations --check`, fixtures, a gunicorn curl smoke (lines 93-117) and `check --deploy`.
- `.github/workflows/pre-commit.yml`, `.pre-commit-config.yaml`, `.github/dependabot.yml`, `.github/workflows/dependabot-auto-merge.yml` (Dependabot PRs auto-merge to main; see Pitfalls).
- `coderdojochi/settings.py:80-130` (apps, middleware), `:250-280` (GCS storage), `:330-380` (Sentry init, debug toolbar), `:386-420` (`LOGGING`).
- `coderdojochi/test_settings.py` (whole file): how tests run without Postgres or GCS.
- `coderdojochi/tests/` (all), `accounts/tests.py`, `weallcode/tests.py`.
- `coderdojochi/factories.py:4,51-54`: imports `pytz`, which is not a declared dependency → `test_password_session` fails to import.
- `coderdojochi/tests/test_mentor_updates.py:9`: patches `coderdojochi.signals_handlers.EmailMultiAlternatives`, which no longer exists there (the module now imports `email` from `coderdojochi.util`, `signals_handlers.py:9`).
- `coderdojochi/forms.py:3,154,271,346`: django-html5 `DateInput` widgets.
- `coderdojochi/util.py:5,100-140`: anymail message + `sentry_sdk.new_scope`.
- `weallcode/views/common.py:5-19`: `capture_message`, `last_event_id` in the 404 handler.
- `coderdojochi/views/calendar.py`: icalendar use.
- `infra/vm/deploy-pull.sh` (whole file), especially the uv sync block (`UV_PYTHON=/usr/bin/python3.11`, `UV_PYTHON_DOWNLOADS=never`, `HOME=/nonexistent`) and "Infra files (prod only)": **infra/vm files are installed only from prod releases**, never staging.
- `infra/vm/provision.sh:215-270`: apt packages (`python3.11-venv`), system users, uv installed once from PyPI into `/opt/uv` (never upgraded after first boot).
- `infra/vm/wac-web.service`, `infra/vm/wac-staging.service`: gunicorn flags, `WorkingDirectory=/srv/wac/<target>/current`, `MemoryMax`, sandboxing.
- `infra/vm/release.sh:1-60` and `infra/vm/README.md` sections "Deploy", "Management commands", "Database", "Admin access (serial console)": how releases, rollback, backups and the serial console work. There is **no SSH**; anything on the VM goes through the serial console, which Ali opens.
- `docs/plans/heroku-to-gcp-e2micro.md` Task G step 5 (line 253) and Progress entry G5 (line 520): the smoke test used for the cutover and the temporary-superuser pattern (`cp4-smoke`).

Code to copy:

- Test style: `coderdojochi/tests/test_email_util.py` (uses `override_settings`, `unittest.mock`).
- CI step style: `.github/workflows/ci.yml` step "Check production settings import" (line 126 at `ee9b6d0`).
- Systemd/infra edits: follow the comment-header style in `infra/vm/deploy-pull.sh:1-16`.

## Tasks

Each task owns its files. Within a checkpoint, tasks run in parallel unless marked. Every task's sub-agent: do not run git; report back with (1) files changed, (2) the exact commands run and their last 20 lines of output, (3) anything that didn't match the plan.

### Checkpoint 0 — Pre-flight (lead + Ali, no code)

- 0.1 #1623 (sentry-sdk 2.76.0 + Sentry Logs) is on `main` but not on prod. Ask Ali to release it to prod first (`infra/vm/release.sh --target prod`) so no upgrade PR carries untested changes. Record the prod sha.
- 0.2 `gh pr list --author app/dependabot` — note open Dependabot PRs and ask Ali to close them (this plan supersedes them). Dependabot is paused for the whole window by PR 1 (`open-pull-requests-limit: 0`, R4); 2C turns it back on with the `uv` ecosystem after the last checkpoint.
- 0.3 Baseline: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode` → expect 58 tests (43 + 15 from #1625's `test_send_reminders`), 2 errors (`test_password_session` import, `test_new_mentor_no_avatar`). Record it.
- 0.4 Build the Playwright smoke script once (see "Playwright smoke" in Proof) in `/tmp/wac-smoke/`, run it against prod (public pages only) and staging to get a baseline of console errors that already exist (so later PRs only fail on new ones).
- 0.5 Ask Ali to open the serial console once and record memory baselines: `systemctl show wac-web wac-staging -p MemoryCurrent,MemoryPeak`, `free -m`, `uv --version`, `curl -6 -sI https://releases.astral.sh/` (R9, needed for CP7). Also create the temporary staging superuser `upg-smoke` for Playwright (password in 1Password at `op://homelab/WAC staging upg-smoke`): `sudo wac-manage staging shell -c "from coderdojochi.models import CDCUser as U; ..."` (model at `coderdojochi/models/user.py:8`). `wac-refresh-staging-db` wipes it, so recreate after any refresh.

### Checkpoint 1 — Safety net and dead dependencies (PR 1)

**1A. Fix the two failing tests and add guard tests.** Files: `coderdojochi/factories.py`, `coderdojochi/tests/test_mentor_updates.py`, new `coderdojochi/tests/test_forms_widgets.py`, new `coderdojochi/tests/test_calendar_view.py`.
- `factories.py`: replace `from pytz import utc` with `from datetime import UTC` (Python 3.11+) and `datetime.now(UTC)`. Ruff `UP017` agrees.
- `test_mentor_updates.py:9`: patch the name the module really calls: `@mock.patch("coderdojochi.signals_handlers.email")`, then fix the assertion to match `email(...)` arguments (read `signals_handlers.py:20-46`).
- `test_forms_widgets.py`: for each form that uses a date widget (`coderdojochi/forms.py:154,271,346` — find the form classes), render the field and assert `'type="date"'` is in the HTML. Guards the django-html5 removal in 1C.
- `test_calendar_view.py`: create a session and a meeting with `coderdojochi/factories.py`, GET `reverse("session-calendar", args=[pk])` and `reverse("meeting-calendar", args=[pk])`, assert 200, `text/calendar` content type, and that `Calendar.from_ical(response.content)` parses with one `VEVENT` whose `SUMMARY` matches. Guards icalendar 7 in Checkpoint 4.
- Pitfall: these views may need a logged-in user or published objects; read `views/calendar.py` first.
- Proof: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode` → 0 failures, 0 errors.

**1B. CI runs everything and runs Sentry init.** File: `.github/workflows/ci.yml` only.
- `tests` job: replace the 4 named modules with `coderdojochi.tests accounts weallcode`.
- `django-postgres` job: add a step after "Check production settings import", copying its style: `SENTRY_DSN: http://public@127.0.0.1:9/0` (R18: unroutable, nothing leaves CI) + the same prod env, run `uv run python manage.py check`. This is what will catch sentry-sdk 3's `TypeError` in Checkpoint 6.
- Proof: `actionlint .github/workflows/ci.yml` clean (`brew install actionlint` if missing); then green CI on the PR.

**1C. Remove dead dependencies.** Files: `pyproject.toml`, `uv.lock`, `coderdojochi/settings.py` (lines 105, 109 only), `coderdojochi/forms.py`. (`cron.py` and django-cron are already gone, #1625.)
- Before removing each package, grep `.py`, templates and the `LOGGING` dict for its import/app label: `mock` (`^import mock|^from mock`), `django_nose|nose`, `common_helpers|helper`, `fullurl`, `json_logging`, `html5`. Remove only those with no remaining use; report any hit.
- Remove from `pyproject.toml`: `mock`, `django-nose`, `django-common-helpers`, `django-fullurl`, `json-logging-py`, `django-html5`. Remove `"html5"` and `"django_nose"` from `INSTALLED_APPS`.
- `forms.py`: replace `html5_widgets.DateInput(attrs={...})` with `forms.DateInput(attrs={..., "type": "date"})` at all three sites, keeping the other attrs; drop the `html5` import. **Pitfall:** Django's `DateInput` defaults to `type="text"`; without `"type": "date"` the browser date picker silently disappears. Also keep the value format ISO (`format="%Y-%m-%d"`) or the browser shows an empty field for existing values.
- Declare `python-dateutil>=2.9,<3` explicitly (it's imported at `forms.py:4`); Checkpoint 4 lifts the bound.
- `uv lock` (no `--upgrade`). Confirm with `git diff --stat uv.lock` that only removals happened.
- Proof: test command from 1A passes; `uv run python manage.py check`; `uv run ruff check .`.
- Also (R6, R13): declare `requests` (imported at `coderdojochi/notifications.py:3`); move `ruff`, `factory-boy`, `invoke`, `django-debug-toolbar` into `[dependency-groups] dev`.
- Also (R4): `.github/dependabot.yml` gets `open-pull-requests-limit: 0` on both ecosystems for the upgrade window (lead owns this file in CP1; 2C restores it).
- Parallel with 1A and 1B (no shared files). 1A's widget test passes before and after 1C by design. All CP1 sub-agents run with `UV_NO_SYNC=1` (R11).

**1D. Remove `distutils` (R1, blocks Python 3.12+).** Files: `coderdojochi/admin.py`, new `coderdojochi/tests/test_admin_strtobool.py`.
- Replace `from distutils.util import strtobool` (`admin.py:2`, used ~:378-379) with a small local helper that accepts the same values (`y yes t true on 1` / `n no f false off 0`, case-insensitive, `ValueError` otherwise).
- Test: true/false values and the `ValueError`. Mutation: drop `"on"` from the true set → test fails.
- Parallel with 1A/1B/1C.

### Checkpoint 2 — Tooling: ruff, pre-commit, GitHub Actions (PR 2)

Runs after Checkpoint 1 merges (the reformat touches files 1A/1C edit).

**2A. Ruff and pre-commit config.** Files: `pyproject.toml` (ruff dep + `[tool.ruff*]` + `pre-commit` dev dep), `uv.lock`, `.pre-commit-config.yaml`.
- `ruff>=0.17.6,<0.18`; `pre-commit>=4.7.0`. `uv lock --upgrade-package ruff --upgrade-package pre-commit`.
- Delete `UP038` from `ignore` and from `extend-unsafe-fixes` (rule removed in 0.13; leaving it errors).
- `.pre-commit-config.yaml`: `pre-commit-hooks` rev `v6.0.0`, `ruff-pre-commit` rev `v0.17.6`.
- Run `uv run ruff check .` and list new findings by rule. Fix real ones; for noisy new rules, add them to `ignore` with a one-line comment why. Report the list.
- Commit 1 = config + fixes. Commit 2 = only `uv run ruff format .` output. The repo squash-merges, so `.git-blame-ignore-revs` gets the **post-merge squash sha** as the first commit of PR 3 (R12).
- Proof: `uv run pre-commit run --all-files` passes; test command passes.

**2B. GitHub Actions.** Files: `.github/workflows/ci.yml`, `.github/workflows/pre-commit.yml`.
- Pin exact versions from the Actions table (`actions/checkout@v7.0.1`, `actions/setup-python@v7.1.0`, `actions/cache@v6.1.0`, `astral-sh/setup-uv@v10.4.0`, `hashicorp/setup-terraform@v4.0.1`, `stefanzweifel/git-auto-commit-action@v7.2.1`). Verify each tag exists: `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`.
- `pre-commit.yml` (R15): add `--all-files` to `pre-commit run`, drop the undefined `${{ inputs.extra_args }}` and the git-auto-commit step (Ali confirms in review).
- Proof: `actionlint` clean; CI green on the PR.
- Parallel with 2A.

**2C. Dependabot (only if Ali said yes in 0.2).** File: `.github/dependabot.yml`: `package-ecosystem: "uv"` instead of `"pip"`. Parallel with 2A/2B.

### Checkpoint 3 — Low-risk Python bumps (PR 3)

**3A.** Files: `pyproject.toml`, `uv.lock`.
- Raise floors to the targets in the table for: django 5.2.19, django-allauth 65.22.1, psycopg 3.3.9, dj-database-url 3.1.2, django-loginas 0.3.14, django-bootstrap3 26.3 (bound `<27`), django-active-link 0.3.0, django-meta 2.5.1, pillow 13.0, arrow 1.4.0, django-appconf 1.2.0, django-import-export 4.4.6, django-environ 0.14.0 (bound `<0.15`).
- `uv lock --upgrade-package django --upgrade-package django-allauth ...` naming exactly these (plus `psycopg-binary`), never a bare `--upgrade`. Then `uv lock --upgrade-package` for these transitive non-majors: asgiref, certifi, cryptography, cffi, idna, requests, sqlparse, tzdata, pyjwt, pydantic, pydantic-core, typing-extensions, packaging, charset-normalizer, pyyaml, filelock, platformdirs, anyio, virtualenv, nodeenv, identify, cfgv. Check `git diff uv.lock | grep '^[-+]version'` shows no major bump.
- Third-party migrations: run `uv run python manage.py makemigrations --check --dry-run` and `uv run python manage.py showmigrations allauth account socialaccount import_export | grep '\[ \]'` against a scratch Postgres (copy the `django-postgres` CI job env). Record any new unapplied migrations in the PR body — they trigger the backup step in the release runbook.
- Proof: tests, `check --deploy` (CI step), CI gunicorn smoke.
- Staging Playwright: full list including login, logout, password change (allauth reauth change), `/dj-admin/` import screen opens (import-export).
- 3A also deletes the `"RET503"` line from `[tool.ruff.lint] ignore` in `pyproject.toml` (3A is the only owner of `pyproject.toml`; 3C fixes the code).

**3B. Admin imports call the right hook (added 2026-11-25 from CP2's finding).** Files: `coderdojochi/admin.py` (`GuardianImportResource` and `StudentResource` only), new `coderdojochi/tests/test_admin_import.py`.
- Bug: both resources override `import_obj(self, obj, data, dry_run)`. django-import-export 4.x never calls `import_obj`; it calls `import_instance(instance, row, **kwargs)`. So in real admin imports, the student's guardian lookup, birthday parse and `strtobool` fields, and the guardian's `User` creation, never run. CP2 named only `StudentResource`; `GuardianImportResource` (`admin.py:233`) has the same bug.
- Build against 4.4.6 (3A's target), not 4.3.9: use your own venv (`UV_PROJECT_ENVIRONMENT=<scratch>/venv-3b uv sync` then `uv pip install django-import-export==4.4.6` into it). First read the installed `import_export/resources.py`: `import_row`, `import_instance`, `before_save_instance`, `save_instance`, `get_or_init_instance`, and how `dry_run` reaches them.
- Rewrite each override as `import_instance(self, instance, row, **kwargs)` (call `super()` if the fields still need it). Never call `.save()` inside it; 4.x saves afterwards and handles dry runs with a transaction. The guardian's new `User` must be saved before the `Guardian` is; `before_save_instance` is the likely place, but check the source.
- Test: build a `tablib.Dataset`, call `Resource().import_data(dataset, dry_run=False)`, assert no row errors, and assert the student's guardian, parsed birthday, `photo_release`/`consent` bools and `is_active`; for the guardian, assert a `User` with that email and `role="guardian"` exists and is linked. Also re-import the same rows (the 4.4.2 unmatched-pk change) and assert no error and no duplicate. Also: unknown guardian email → row error.
- Mutation: rename one `import_instance` back to `import_obj` → its test fails.
- Pitfall: `GuardianImportResource.get_or_init_instance` raises `Guardian.DoesNotExist` when a `User` with that email exists but has no `Guardian`. Report it; fix only if the test hits it.

**3C. Explicit returns where views fall through (RET503; added 2026-11-25 from CP2's finding, corrected).** Files: `accounts/views.py` (`AccountHomeView.get`, `.post`), `coderdojochi/views/profile.py` (`DojoMentorView.post`), new or existing test in `accounts/tests.py`.
- Correction to the CP2 note: users with **no** role don't hit this; `AccountHomeView.dispatch` already redirects them to `welcome`. `get`/`post` return `None` (→ 500) only for a `role` value outside `ROLE_CHOICES` (bad data). `DojoMentorView.post` returns `None` when the form is invalid, but `DojoMentorView` has no URL (the `dojo/` route is commented out), so it's dead. Latent bugs, not a live 500.
- Fix: in `AccountHomeView.get`/`post`, after the two role branches, `return redirect("welcome")` (same place `dispatch` sends role-less users). In `DojoMentorView.post`, after the error message, re-render the page with the bound forms (copy `post_for_mentor`'s tail in `accounts/views.py`), or `return redirect("account_home")` if that's simpler; don't delete the view (dead-code removal is out of scope).
- Test: a user with `role="bogus"` (saved with `.update()` to skip choices validation) GETs and POSTs `reverse("account_home")` → 302 to `welcome`, not 500. Mutation: delete the new `return` → test fails.
- Proof: `uv run ruff check --isolated --select RET503 accounts/views.py coderdojochi/views/profile.py` clean; full suite.
- 3A, 3B, 3C run in parallel (no shared files). 3A and 3C use the shared `.venv` with `UV_NO_SYNC=1`; 3A only runs `uv lock`, never `uv sync`. The lead syncs once, then runs the checks and runbook step 0 (migration check on scratch Postgres 17).

### Checkpoint 4 — Majors without runtime-server risk (PR 4)

**4A.** Files: `pyproject.toml`, `uv.lock`, plus code fixes these force (only in `coderdojochi/views/calendar.py`, `coderdojochi/util.py`, `coderdojochi/signals_handlers.py`, `tasks.py`, `coderdojochi/settings.py` debug-toolbar block).
- django-anymail 15.3 (`<16`), django-debug-toolbar 8.0.0 (`<9`), icalendar 7.3.2 (`<8`), invoke 3.0.3 (`<4`), python-dateutil 4.0 (`<5`, after reading its changelog for `relativedelta`), faker 40 (transitive), pycparser 3 (transitive).
- grep `fail_silently` (anymail 15.1 deprecation) and `UIDGenerator|decoded(` (icalendar 7).
- `signals_handlers.py:25`: `MIMEImage(instance.avatar.read())` has no filename; set the filename and subtype from the avatar's extension so anymail 14's Resend check passes (R24); extend `test_mentor_updates` to assert it.
- `views/calendar.py:48`: `event["dtstamp"] = event["dtstart"][:-1]` slices a property; rewrite with a real `datetime` (R23). `test_calendar_view` asserts DTSTAMP parses.
- Proof: tests (incl. `test_calendar_view.py` and `test_email_util.py`); `DEBUG=True uv run python manage.py runserver` locally and load `/` to see the toolbar render (dev only); `uv run invoke --list`.
- Staging can't prove Resend (console email backend). Prod post-release check: trigger a password reset to Ali's own address; confirm it arrives and appears in Resend's sent list. Also run, via serial console, the `coderdojochi.util.email()` check from the cutover plan (Task G step 5) to Ali's address.

### Checkpoint 5 — gunicorn 27 (PR 5)

**5A.** Files: `pyproject.toml`, `uv.lock`, new `gunicorn.conf.py` at the repo root.
- `gunicorn>=27.0.1,<28`; `uv lock --upgrade-package gunicorn`.
- Turn the control socket off **in a file that ships with the release**, so staging tests it: gunicorn loads `./gunicorn.conf.py` from its working directory, which is the release dir (`WorkingDirectory=/srv/wac/<target>/current`). Find the exact setting name with `uv run gunicorn --help | grep -i control` (the CLI flag is `--no-control-socket`); write it in `gunicorn.conf.py` with a comment pointing at gunicorn 25.1. Do **not** edit `infra/vm/wac-*.service`: unit changes install only from prod releases, so staging would never test them.
- Add `[tool.ruff.lint.per-file-ignores] "gunicorn.conf.py" = ["INP001", "N999"]` (R17).
- Pitfall: a `gunicorn.conf.py` in cwd is also picked up by the CI smoke step (`ci.yml` "Smoke test pages under gunicorn"); that's good — it proves the file parses.
- Proof: CI gunicorn smoke; locally `uv run gunicorn coderdojochi.wsgi --check-config`; on staging, deploy succeeds (if gunicorn fails to start, deploy-pull rolls back and `journalctl -u 'wac-deploy@staging'` shows why — Ali reads it on the serial console).
- Memory: serial console `systemctl show wac-staging -p MemoryCurrent,MemoryPeak` after the Playwright pass; compare with the 0.5 baseline. Fail if > 10% higher.

### Checkpoint 6 — sentry-sdk 3 (PR 6, gated by D3)

**6A.** Files: `pyproject.toml`, `uv.lock`, `coderdojochi/settings.py` (Sentry block only, `:336-357`).
- `sentry-sdk>=3.0.1,<4` (or `>=3.0.0` if Ali waives D3).
- Rewrite init: drop `enable_logs`; add `LoggingIntegration(level=logging.INFO)` to `integrations` (keeps #1623's Sentry Logs at INFO and up; `event_level` stays default `None`, matching 2.x where logging errors were not turned into events by default — builder: confirm 2.76 behaviour and keep it the same); replace `send_default_pii=True` with the 3.x `data_collection` option set to the closest equivalent (read the 3.x docs; keep user id/email on events, as today). Keep `traces_sample_rate` as is.
- Proof: the CI step from 1B (`SENTRY_DSN` set → `manage.py check`) passes — and fails on the old settings (see Proof, mutation). Staging has no DSN (`infra/vm/env.staging.example:32`), so before the staging deploy Ali adds a temporary `SENTRY_DSN` + `SENTRY_ENVIRONMENT=staging` secret version and releases with `--force`; remove it after the memory check (R8). After prod release: Sentry shows a log entry from the release and the 404 handler still renders `sentry_event_id` (request a missing page).
- Memory: as in 5A (span streaming).

### Checkpoint 7 — Python 3.13 (two PRs, gated by D1)

The VM has no Python 3.13 package. uv ≥ 0.10.8 downloads CPython from `releases.astral.sh`, which has IPv6 (GitHub doesn't). uv verifies each download's sha256 against its built-in metadata.

**7A. PR 7a — VM can run a uv-managed Python (infra, ships to prod while the app is still on 3.11).** Files: `infra/vm/deploy-pull.sh`, `infra/vm/provision.sh`, `infra/vm/README.md`.
- `provision.sh`: upgrade uv when older than a pinned floor (`/opt/uv/bin/pip install --upgrade 'uv>=0.13.7,<0.14'`), not only when missing. Laptop is 0.13.7; lock format must match.
- `deploy-pull.sh`, before the build: read `$release_dir/.python-version` (validate `^3\.1[1-4]$`, else `die`). If `3.11` → current behaviour (`UV_PYTHON=/usr/bin/python3.11`). Otherwise run as **root**, from cwd `/` and never inside the release dir (R2): `env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/root UV_NO_CONFIG=1 UV_PYTHON_PREFERENCE=only-managed UV_PYTHON_INSTALL_DIR=/opt/wac-python-$target UV_CACHE_DIR=/var/cache/wac-uv-python-$target uv python install <ver>`, `chmod -R a+rX /opt/wac-python-$target`, then the existing `runuser` sync with `UV_PYTHON=$(… same env … uv python find --managed-python <ver>)` and `UV_PYTHON_DOWNLOADS=never` unchanged. Per-target dirs mean a staging release can never place a Python that prod uses. The venv symlinks into that dir, so never delete an installed version while a kept release uses it.
- Isolation note for the README (R10): a staging release can make root download a CPython build into the staging-only dir, only an official one (version regex, no project config, uv's sha256 check). Ali must accept this in review.
- **uv upgrade reaches the VM only via provision (R3):** `--install-files` exits before the uv block, so after the 7a prod release Ali runs `sudo wac-provision` on the serial console and records `uv --version` (≥ 0.13.7) in Progress. 7b waits for that.
- Precondition (R9): 0.5 showed `curl -6 -sI https://releases.astral.sh/` works on the VM. If not, rewrite 7A to a `file://` mirror fetched through GCS before building.
- Proof: `shellcheck infra/vm/*.sh`; CI `infra` job; prod release of 7a is a no-op (still 3.11): deploy log shows the 3.11 path, site up.

**7B. PR 7b — app on Python 3.13 (Django stays 5.2, which supports 3.13).** Files: `.python-version`, `pyproject.toml` (`requires-python = ">=3.13,<3.14"`, ruff `target-version = "py313"`), `uv.lock`, `.pre-commit-config.yaml` (`default_language_version: python3.13`), `.github/workflows/ci.yml` + `pre-commit.yml` (`python-version: '3.13'`), `Dockerfile` (`FROM python:3.13.<latest patch>`, non-slim like today, R16).
- Run after 7a is on prod. `uv lock` (wheels for cp313 exist for psycopg-binary, pillow, cryptography, cffi, pydantic-core: check `uv sync` output for any sdist build — the VM has no compiler toolchain for them).
- `uv run ruff check --fix .` for new `UP` fixes at py313; separate commit if large.
- Proof: tests on 3.13; CI; staging deploy log shows `uv python install 3.13` then sync; Playwright; memory vs baseline.
- Rollback: re-releasing a 3.11 sha works because `/usr/bin/python3.11` stays installed and old releases keep their own venvs.

### Checkpoint 8 — Django 6 (PR 8, gated by D1; default target 6.2 LTS, April 2027)

Pre-conditions (check, don't assume): django-storages and django-recaptcha have **released** versions declaring Django 6 support; Checkpoint 7 done. Re-check the classifiers of django-cleanup, django-stdimage (archived; its `rendervariations` command uses `get_storage_class`, removed in 5.1 — confirm nothing calls it), factory-boy, django-import-export, django-loginas, django-meta, django-active-link, django-anymail, django-bootstrap3.

**8A.** Files: `pyproject.toml`, `uv.lock`, and whatever the deprecation run flags.
- First, on 5.2: `uv run python -W error::DeprecationWarning manage.py test ...` (and `-Wd` on `runserver` + Playwright) to list `RemovedInDjango60Warning`/`61` hits. Fix them in their own commit.
- Then `django>=6.2,<6.3` (or 6.1 if Ali chose that). Read 6.0, 6.1, 6.2 release notes "Backwards incompatible changes" against: email (`coderdojochi/util.py`), `ADMINS`/`MANAGERS` tuples in settings, `Model.save()` positional args (grep `\.save\([^)k]`), admin templates under `coderdojochi/templates/admin/`, `first()`/`last()` after `order_by()`.
- Proof: tests; `makemigrations --check` (contrib apps may ship migrations: record them; triggers backup step); full Playwright incl. `/dj-admin/` change list, change form and import; staging memory.

### Checkpoint 9 — Front-end libraries upgraded and hosted locally (PR 9, independent of Python; can run any time after Checkpoint 1, gated by D2)

Ali (2026-11-24): vendor every third-party font, CSS and JS file into the repo and serve it as our own static files, instead of from cdnjs, unpkg, jsdelivr, maxcdn, ajax.googleapis.com, fonts.googleapis.com or browser.sentry-cdn.com. Static files already go to the GCS bucket through `collectstatic` (`StaticStorage` = `ManifestFilesMixin` + GCS, `coderdojochi/storage_backends.py`; `STATIC_URL` = `https://storage.googleapis.com/<bucket>/static/`, `coderdojochi/settings.py:280`). The bucket's CORS already allows the site origins with `GET` (`infra/terraform/storage.tf:19-24` prod, `:61-66` staging), which cross-origin web fonts need. Manifest hashing gives the files cache-busting names, so no version is needed in the path.

**Stays on third-party hosts (allowlist), with the reason:**
- Google reCAPTCHA (`django_recaptcha` widget): it is a live Google service and must load from Google.
- Google Charts `https://www.gstatic.com/charts/loader.js` (`dashboard/admin.html:19`, `meeting_check_in.html:17`, `session_check_in.html:57`): Google's terms don't allow self-hosting the loader, which also fetches more code at runtime.
- `https://www.google.com/jsapi` (`dashboard/session_stats.html:12`): this is the old Charts loader. Switch it to `gstatic.com/charts/loader.js` with `google.charts.load` in 9C, so there's one allowed host.
- Google Analytics: the dead UA `analytics.js` snippet (`weallcode/templates/weallcode/_base.html:86-94`) is removed, and GA4 `https://www.googletagmanager.com/gtag/js?id=<GA_MEASUREMENT_ID>` replaces it (D5). Google's tag can't be self-hosted, so `www.googletagmanager.com` is on the allowlist. GA4 sends hits to `*.google-analytics.com` from the browser; that's beacon traffic, not an asset.

**Vendored layout (fixed paths, so templates and files can be built in parallel).** Everything goes under `coderdojochi/static/vendor/`, which is served as `{% static 'vendor/…' %}` because `coderdojochi` is an installed app. Each library's license file sits next to it.

| Library | Version | npm package (source) | Files → `vendor/…` |
|---|---|---|---|
| jQuery | 3.8.0 | `jquery` | `jquery/jquery.min.js`, `jquery/jquery.min.map` |
| what-input | 5.2.12 | `what-input` | `what-input/what-input.min.js` |
| Foundation JS | 6.9.0 | `foundation-sites` | `foundation/foundation.min.js` (+ `.map` if referenced) |
| Font Awesome 5 | 5.15.4 | `@fortawesome/fontawesome-free@5.15.4` | `fontawesome5/css/all.min.css`, `fontawesome5/webfonts/*` (all formats the CSS references) |
| Font Awesome 4 | 4.7.0 | `font-awesome` | `fontawesome4/css/font-awesome.min.css`, `fontawesome4/fonts/*` |
| Bootstrap 3 | 3.4.1 | `bootstrap@3.4.1` | `bootstrap3/css/bootstrap.min.css` (+ `.map`), `bootstrap3/js/bootstrap.min.js`, `bootstrap3/fonts/glyphicons-halflings-regular.*` |
| js-datepicker | 5.18.4 | `js-datepicker` | `js-datepicker/datepicker.min.css`, `js-datepicker/datepicker.min.js` |
| Sentry browser bundle | latest 11.x (11.17.0 today) | `@sentry/browser` | `sentry/bundle.min.js` (from `build/bundles/`) |
| Bungee 400; Poppins 400; Open Sans 300/400/700; Quicksand 300/400/700 | latest (5.3.0 today) | `@fontsource/bungee`, `@fontsource/poppins`, `@fontsource/open-sans`, `@fontsource/quicksand` | `fonts/<family>/<weight>.css` + `fonts/<family>/files/*.woff2` (latin + latin-ext subsets only; drop the `.woff` fallbacks and edit the CSS to match) |

**Pitfalls (these will break `collectstatic` on deploy if they're missed):**
- `ManifestFilesMixin` rewrites every `url(...)` in CSS and every `sourceMappingURL` in JS and CSS. If a referenced file is missing, `collectstatic` raises `ValueError` and the deploy fails, though deploy-pull then leaves the old release running. So vendor every font format a CSS file references (FA4/FA5 still reference `.eot`, `.svg`, `.ttf`, `.woff`), and either ship each `.map` or strip its `sourceMappingURL` comment. Task 9E's manifest test catches this before staging.
- Keep each library's directory layout, so relative `url(../webfonts/…)` paths still resolve.
- Font files load cross-origin from `storage.googleapis.com`. If the bucket CORS didn't cover an origin (for example `localhost` in dev with `DEBUG=False`), the fonts would fail silently. In dev, `DEBUG=True` serves them from `/static/`, which is same-origin.
- Fontsource weight CSS uses `font-display: swap` and `unicode-range`. Leave those as they are.

**9A. Vendor the files and a refresh task.** Files: `coderdojochi/static/vendor/**` (new), `coderdojochi/static/vendor/vendor.json` (new), `coderdojochi/static/vendor/README.md` (new), `tasks.py`.
- `vendor.json` lists each package as `{package, version, files: [{from, to}]}`, matching the table.
- Add an invoke task `invoke vendor` to `tasks.py`. For each entry it fetches `https://registry.npmjs.org/<package>/<version>`, downloads `dist.tarball`, checks it against `dist.integrity` (sha512), extracts only the listed files to a temp dir and copies them into place. Use Python stdlib only (`urllib`, `tarfile`, `hashlib`); add no new dependency. Running it twice must leave no diff.
- `README.md`: one line per library with version, npm URL and license, plus "refresh with `uv run invoke vendor`; bump versions in `vendor.json`".
- Proof: `uv run invoke vendor && git status --porcelain coderdojochi/static/vendor` is empty on the second run; `find coderdojochi/static/vendor -type f | wc -l` matches the manifest; total size is under 5 MB (`du -sh`).

**9B. Public site template.** File: `weallcode/templates/weallcode/_base.html`.
- Replace the cdnjs Font Awesome 5, fonts.googleapis, jQuery, what-input and Foundation tags with `{% static 'vendor/…' %}`. Fonts: link `vendor/fonts/bungee/400.css`, `vendor/fonts/poppins/400.css` and `vendor/fonts/open-sans/400.css`, which is today's request (no weights given = 400). Keep the local `weallcode/css/foundation.min.css` (6.5.1 CSS, which is fine with 6.9 JS).
- Remove the seamless-scroll-polyfill `<script>` (it's dead in 2.x; native `scroll-behavior` covers it). If `weallcode/static/weallcode/css/app.css` has no `scroll-behavior: smooth`, report that; don't edit app.css.
- Drop the `<!--[if IE]>` block.
- Replace the UA snippet (`:86-94`) with the standard GA4 gtag snippet inside `{% if GA_MEASUREMENT_ID %}…{% endif %}`, using `{{ GA_MEASUREMENT_ID }}` in both the script URL and `gtag('config', …)`. The context variable comes from 9F.

**9F. GA4 setting.** Files: `coderdojochi/settings.py` (one line near the other `env(...)` reads), `coderdojochi/context_processors.py` (or wherever `SENTRY_DSN` already reaches templates; grep `SENTRY_DSN` in `context_processors`/views first and reuse that path), `infra/vm/env.prod.example` and `infra/vm/env.staging.example` (document the key; staging leaves it empty).
- `GA_MEASUREMENT_ID = env("GA_MEASUREMENT_ID", default="")`. Use a `""` default, never `False` (see the comment at `settings.py:336-338`).
- Test (in 9E's file): with `override_settings(GA_MEASUREMENT_ID="G-TEST123")`, `/` contains `gtag/js?id=G-TEST123`; with `""` it contains no `googletagmanager`. Mutation: drop the `{% if %}` → the empty-ID test fails.
- Prod check after release: once Ali adds the secret version and runs `release.sh --target prod --force <sha>`, GA4 Realtime shows a visit. No GA4 on staging.

**9C. Dashboard templates.** Files: `coderdojochi/templates/dashboard/_admin_base.html`, `coderdojochi/templates/dashboard/session_stats.html`.
- `_admin_base.html`: point Google Fonts (Open Sans 300/400/700, Quicksand 300/400/700), FA 4.7.0, Bootstrap 3.4.1 CSS/JS and jQuery 3.8.0 at the vendored files. Remove the old `integrity`/`crossorigin` attributes, which are wrong for local files. Remove the IE8 html5shiv/respond block (`oss.maxcdn.com` is dead).
- `session_stats.html`: replace `google.com/jsapi` + `google.load("visualization", "1", …)` with `gstatic.com/charts/loader.js` + `google.charts.load('current', {packages: ['corechart']})` + `google.charts.setOnLoadCallback(...)`, copying the pattern in `dashboard/admin.html:19-23`.
- Pitfall: grep the dashboard templates and `coderdojochi/static/js/` for jQuery 3 removals (`.load(` on jQuery objects, `.size()`, `.andSelf()`, `.bind(`, `.delegate(`, `$(document).on("ready"`, `.error(`), for Bootstrap `data-target`/`href` that contain HTML, and for tooltips/popovers with custom HTML. Report every hit with file:line.

**9D. Welcome and error pages.** Files: `coderdojochi/templates/welcome.html`, `coderdojochi/templates/500.html`.
- `welcome.html:8,79`: use the vendored js-datepicker.
- `500.html:26-37`: use the vendored `vendor/sentry/bundle.min.js` (errors only; no tracing or replay on an error page). Update the init for the v11 API. Check that `Sentry.showReportDialog` still exists in 11.x (`grep -c showReportDialog` on the bundle). If it doesn't, use the v11 user-feedback API and report what changed. Note: 500.html is rendered by Django's error handler; `{% static %}` works there as long as the static setup itself isn't what's broken.

**9E. Guard tests.** Files: new `coderdojochi/tests/test_vendored_assets.py`.
- Test 1, no CDN: render `/`, `/programs/`, `/account/login/` and (as a staff user) `/admin/` and `/welcome/` with the test client. Extract every `<script src>` and `<link href>` and assert that each one is either relative/`STATIC_URL` or on the allowlist (`www.google.com/recaptcha`, `www.gstatic.com/charts`, `www.googletagmanager.com`). Also render `500.html` directly with `SENTRY_DSN` and `sentry_event_id` in the context.
- Test 2, the manifest builds: under `override_settings(STORAGES={"staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.ManifestStaticFilesStorage"}, …}, STATIC_ROOT=<tmpdir>)`, run `call_command("collectstatic", "--noinput")` and assert it doesn't raise and that `staticfiles.json` maps `vendor/fontawesome5/css/all.min.css`. This is the same post-processing the GCS `StaticStorage` does, so it catches missing fonts and maps before staging.
- Mutations: put one cdnjs URL back in `_base.html` → test 1 fails; delete one file from `vendor/fontawesome5/webfonts/` → test 2 fails. Undo each with the exact reverse edit, or by restoring the file from the vendor task.

- 9A–9F run in parallel, because the paths are fixed above. 9F's test goes in 9E's file, so 9E writes it from 9F's spec. The lead runs `uv run invoke vendor` once after 9A if a template task needs the files to test.
- Proof: the full test suite, including 9E. On staging, Playwright with **zero new console errors** compared with the 0.4 baseline, **no failed requests**, and **no request to any host outside the allowlist + `storage.googleapis.com` + the site itself** (record every request host per page). Check that font responses come back 200 with `Access-Control-Allow-Origin`, and that the computed `font-family` on `body`/headings is the vendored one (`document.fonts.check('16px Poppins')` is true). Pages: the public list, `/admin/` (cdc-admin dashboard, needs staff), `/welcome/` (needs a logged-in user without a role; use `upg-smoke` or a second temp user). Also open a Foundation menu/off-canvas at mobile width, open a Bootstrap dropdown on the dashboard, open the datepicker on `/welcome/`, and load a session stats page (Google Charts renders).

## Checkpoints

Each checkpoint = one PR (Checkpoint 7 = two). Order: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7a → 7b → 8; 9 slots in any time after 1 (recommended right after 3, to keep Python PRs back to back). Each one delivers a working, released site.

| CP | PR title | Check that proves it | Delivers |
|---|---|---|---|
| 0 | — | Baselines recorded in Progress | Known starting point |
| 1 | Fix broken tests, run the full suite in CI, drop dead dependencies | Full suite 0 failures; CI green incl. new Sentry-init step | A real safety net |
| 2 | Ruff 0.17, pre-commit-hooks v6, latest GitHub Actions | `pre-commit run --all-files`; CI green | Current tooling |
| 3 | Patch/minor Python bumps (Django 5.2.19, allauth, psycopg 3.3, …) | Tests + CI + staging Playwright incl. auth flows | Security fixes |
| 4 | anymail 15, debug-toolbar 8, icalendar 7, invoke 3, dateutil 4 | Tests incl. calendar + email; prod Resend check | Majors with no server risk |
| 5 | gunicorn 27 | Staging deploy + memory ≤ baseline +10% | Current app server |
| 6 | sentry-sdk 3 | CI Sentry-init step; prod Sentry log seen | Current SDK |
| 7a | VM can install uv-managed Python | Prod release is a no-op on 3.11 | Runtime path ready |
| 7b | Python 3.13 | Staging deploy on 3.13 + Playwright + memory | Supported Python to 2029 |
| 8 | Django 6.2 LTS | Tests + full Playwright + migrations recorded | Current Django LTS |
| 9 | Upgrade and self-host front-end libraries and fonts | 9E tests; Playwright: zero new console errors, no requests outside the allowlist | jQuery/Bootstrap CVEs fixed; no third-party CDNs |

## How to run it

Read the whole plan first. Run it as the lead: you write no code.

1. At the start of each checkpoint, give every task that can run in parallel to its own sub-agent, all at once. Each brief names its task, its files and only those, the bar to meet (the task's Proof line), and the report format (files changed; commands + last 20 lines; mismatches). Tell it not to run git.
2. You alone: check the actual files (not the report), run the checkpoint's checks, commit, write the result and evidence into Progress.
3. Anything not in the plan: write it into the plan first, then build it.
4. Per PR, the release runbook (every step needing Ali waits for his explicit OK in this session — never push, merge or release on your own):
   0. Migration check (R7, every Python checkpoint): on a scratch Postgres 17 (env as in the CI `django-postgres` job), check out `origin/main`, `uv sync`, `manage.py migrate`; then switch to the branch, `uv sync`, `manage.py migrate --plan`. Any planned operation ⇒ note it in the PR body and do step 6.
   1. Branch `claude/upgrade-cpN-<slug>` from latest `origin/main`. If `main` moved, rebase and **regenerate** `uv.lock` (`git checkout origin/main -- uv.lock && uv lock` + the same `--upgrade-package` list), never hand-merge it.
   2. Ask Ali to push and open the PR (body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`; commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`). Wait for CI green.
   3. Ask Ali to run `infra/vm/release.sh --target staging <branch>` (branch must exist on origin). If the staging DB is stale, he runs `sudo wac-refresh-staging-db` first (then recreate `upg-smoke`).
   4. Run the Playwright smoke against staging. For checkpoints with a memory check, ask Ali for the serial-console `systemctl show` numbers.
   5. Ali merges. Record the **previous prod sha** (`gcloud storage cat gs://wac-deploy-<project>/current-prod | cut -d: -f1`, R19) in Progress.
   6. If the PR adds migrations (step recorded in the PR body), Ali runs `sudo systemctl start wac-backup` on the serial console and confirms the new object in the backup bucket, and records `sudo wac-manage prod showmigrations | grep -c '\[X\]'`.
   7. Ali runs `infra/vm/release.sh --target prod`. Run the prod smoke (public pages, no login) and the checkpoint's prod-only checks; watch Sentry for an hour.
5. Rollback (any checkpoint): Ali runs `infra/vm/release.sh --target prod <previous-prod-sha>` `--force` (it's on `origin/main`, so allowed; always pass `--force` because the `failed` marker can't be read from the laptop, R10). If the bad release ran migrations, first reverse them on the serial console: `sudo wac-manage prod migrate <app> <previous-migration>`; if that isn't possible, restore the step-6 backup per `infra/vm/README.md` "Database". deploy-pull already auto-rolls back when gunicorn fails to start. Only 3 releases are kept on the VM; the tarballs stay in the deploy bucket, so any older sha can be re-released.
6. After each checkpoint, if your context window is half full, write which checkpoint is next in Progress and stop; a fresh session continues from this plan.

## Proof

### Per acceptance criterion

| # | Test | One-line change that must make it fail |
|---|---|---|
| 1 | `uv tree --outdated --depth 1` shows no outdated direct deps except rows marked "gated"/"latest" | Lower one floor in `pyproject.toml` and `uv lock` → it shows up |
| 2 | Each PR: CI green + Playwright pass log in Progress | — (process) |
| 3 | Full suite in CI (`ci.yml` tests job) | In `factories.py`, put back `from pytz import utc` → `test_password_session` import error |
| 3 | `test_mentor_updates` | Change the patch target back to `signals_handlers.EmailMultiAlternatives` → AttributeError |
| 3 | `test_forms_widgets` | In one `forms.DateInput(...)` drop `"type": "date"` → fails |
| 3 | `test_calendar_view` | In `views/calendar.py` change the `summary` value → fails |
| 4 | CI "Sentry init" step | In `settings.py` add `enable_tracing=True` to `sentry_sdk.init` on sentry-sdk 3 (Checkpoint 6) → `TypeError` → step fails. Before CP6: add `bogus_option=1` → fails on 2.x too |
| 5 | Prod smoke + Sentry + memory numbers in Progress | Point the smoke script at a 404 path → fails |
| 6 | Previous sha + backup recorded in Progress before each prod release | — (process) |
| 7 | `grep -E "mock|nose|common-helpers|fullurl|json-logging|html5" pyproject.toml` → nothing (django-cron already gone, #1625) | Re-add one → grep hits |
| 8 | `test_vendored_assets` (no-CDN test + manifest collectstatic test) | Put a cdnjs URL back in `_base.html` → fails; delete one FA5 webfont → manifest test fails |

After writing each test: make the one-line change, confirm the test fails, undo with the exact reverse edit (never `git checkout`/reset).

### Whole-build commands (every checkpoint)

```bash
uv run ruff check . && uv run ruff format --check .
```

```bash
DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode
```

```bash
uv run pre-commit run --all-files
```

```bash
actionlint .github/workflows/*.yml
```

```bash
shellcheck infra/vm/*.sh infra/vm/wac-manage
```

Plus CI's `django-postgres` job (migrate, `makemigrations --check`, fixtures, gunicorn smoke, `check --deploy`, Sentry init) and `infra` job.

### Playwright smoke

Script lives outside the repo in `/tmp/wac-smoke/` (`.mise.toml` with `node = "22"`, `npm i -D playwright@<latest>`, `npx playwright install chromium`). One file `smoke.mjs`, args `--base <url> [--auth]`:

- Staging: `httpCredentials: { username: "staging", password: <op read "op://homelab/WAC staging basic auth/password"> }`.
- Public pages: `/`, `/programs/`, `/programs/summer-camps/`, `/team/`, `/our-story/`, `/join-us/`, `/credits/`, `/privacy/`, `/account/login/`, `/account/signup/`, `/dj-admin/login/`, a 404 path (expect 404 page renders).
- With `--auth` (staging only, user `upg-smoke`, password via `op read "op://homelab/WAC staging upg-smoke/password"`): log in through `/account/login/`; `/admin/` (cdc-admin); `/dj-admin/` index, one change list, one change form, the import screen of one import-export model; `/welcome/`; a session and a meeting `.../calendar/` download (content type `text/calendar`); password change form; log out.
- For each page: status < 400 (except the 404 check), **no console errors** beyond the 0.4 baseline, no failed requests (catches SRI/CDN 404s), screenshot to `/tmp/wac-smoke/out/<cp>/<page>.png` (desktop 1280 and mobile 390 for the public pages).
- Never submit forms that send email or change real data, except the password change on `upg-smoke`.

### Manual, prod only (staging can't prove these)

- Email (CP4, and any CP touching email): password reset to Ali's address arrives; Resend sent list shows it.
- Social login (CP3, allauth): Ali logs in with Google on prod (staging callback URLs are not registered).
- Sentry (CP6): a log entry and the 404 `sentry_event_id` appear.

Before calling the plan done: use the site through its real entry point (prod, through Cloudflare) as a visitor and as staff, and confirm normal use still works.

## Pitfalls

- Never run a bare `uv lock --upgrade`: inside today's bounds it already pulls gunicorn 26, anymail 15, debug-toolbar 8, icalendar 7, invoke 3, dateutil 4 — majors that belong to later checkpoints.
- Dependabot auto-merges into `main` (`dependabot-auto-merge.yml`). Check `gh pr list --author app/dependabot` at each checkpoint start.
- infra/vm files only install from prod releases. Anything that must be tested on staging has to ship in the app tree (e.g. `gunicorn.conf.py`), not in a unit file.
- The VM has no SSH; Ali opens the serial console (`infra/vm/README.md` "Admin access") and must lock `wacadmin` again afterwards.
- 1 GB RAM: one deploy at a time (flock). uv sync of a fresh Python (CP7b) downloads every wheel again; expect a slower first deploy.
- `wac-refresh-staging-db` wipes `upg-smoke`.
- Cloudflare edge cache (from #1628 / `docs/plans/cloudflare-html-cache.md`, live 2026-11-25): logged-out public HTML on prod is cached for up to 60 s (`cf-cache-status: HIT`). After a prod release, the smoke can see the old release for up to 60 s, and load or memory tests through Cloudflare hit the cache. To reach origin, send a `sessionid=x` cookie or a cache-busting query string, or wait 60 s.
- Terraform: the live Cloudflare cache rule (`cloudflare_ruleset.cache`) is in `infra/terraform/cache.tf`, on main since https://github.com/WeAllCode/website/pull/1631 (`f25adbd`). Apply only from a branch that includes `f25adbd`; an older branch would delete the rule.

## Plan review findings

Fresh review sub-agent, 2026-11-24. Every finding is folded into the plan text above; this table is the record. **These override anything above that contradicts them.**

| # | Sev | Finding | Resolution (now in the plan) |
|---|---|---|---|
| R1 | Blocker | `coderdojochi/admin.py:2` imports `distutils.util.strtobool` (used ~:378-379); distutils is gone in Python 3.12+, so admin (and Django setup) breaks on 3.13 | 1D added: inline `strtobool` helper + test |
| R2 | Blocker | 7A: root `uv python install` for a staging release could read the branch's `[tool.uv]`/`uv.toml` (`python-install-mirror`, `python-downloads-json-url`) and plant a non-official build that prod later uses (breaks R10) | 7A now: `env -i`, `UV_NO_CONFIG=1`, cwd `/`, regex-validated version only, `UV_PYTHON_PREFERENCE=only-managed`, **per-target** install dirs `/opt/wac-python-<target>` |
| R3 | Blocker | The uv upgrade in `provision.sh` never runs on a prod release (`--install-files` exits at provision.sh:195-201, before the uv block at :263 — line numbers as of `ee9b6d0`) | 7A: after the 7a prod release Ali runs `sudo wac-provision` on the serial console and records `uv --version`; 7b is gated on it |
| R4 | Major | Dependabot auto-merge can land untested deps on main mid-upgrade | CP0 0.2: pause Dependabot for the whole window (`open-pull-requests-limit: 0` for both ecosystems, in PR 1); 2C restores it with the `uv` ecosystem |
| R5 | Major | Runbook prod release had no ref → `release.sh` defaults to laptop HEAD | Runbook 4.7: `git fetch && infra/vm/release.sh --target prod <merged-squash-sha>` after confirming `origin/main` = that sha |
| R6 | Major | `requests` is imported directly (`coderdojochi/notifications.py:3`) but undeclared | 1C declares `requests` too |
| R7 | Major | CP3 migration check was wrong (`makemigrations --check` = own models only; `showmigrations` on scratch DB is all-or-nothing) | New method in Runbook 4.1b: migrate a scratch PG at `origin/main`, `uv sync` the branch, `manage.py migrate --plan`; any output ⇒ backup step 6 |
| R8 | Major | Staging has no Sentry DSN (`infra/vm/env.staging.example:32`), so CP6's span-streaming memory risk would first hit prod | CP6: Ali adds a temporary staging DSN (same Sentry project, `environment=staging`) before the staging deploy, removes it after |
| R9 | Major | releases.astral.sh over IPv6 from the VM is unverified | 0.5: `curl -6 -sI https://releases.astral.sh/` on the serial console; if it fails, CP7 falls back to a `file://` mirror fetched by deploy-pull through GCS (rewrite 7A before building) |
| R10 | Major | Rollback "`--force` if sha is in `failed`" can't be read from the laptop | Rollback always uses `--force` (harmless) |
| R11 | Major | CP1 parallel tasks share one `.venv`; `uv run` auto-syncs, so 1C's lock change pulls packages from under 1A | CP1 sub-agents run with `UV_NO_SYNC=1`; the lead runs `uv sync` once before the checkpoint check |
| R12 | Major | Repo squash-merges; 2A's reformat sha won't exist on main | `.git-blame-ignore-revs` added in a follow-up commit (first commit of PR 3) with the post-merge squash sha |
| R13 | Minor | Dev tools (ruff, factory-boy, invoke, debug-toolbar, pre-commit) are prod deps → installed on the VM | 1C moves ruff, factory-boy, invoke, django-debug-toolbar into `[dependency-groups] dev`; check `settings.py` imports debug_toolbar only under `DEBUG` (it does, `:364-372`) and `test_settings.py` filters it |
| R14 | Minor | AC5 "under MemoryMax" is near-tautological | AC5 now compares `MemoryPeak` with the 0.5 baseline (≤ +10%) |
| R15 | Minor | `pre-commit.yml` runs without `--all-files` and auto-commits to the PR branch on failure, so CI green proves nothing | 2B: add `--all-files`, drop the git-auto-commit step (Ali to confirm); until then rely on local `pre-commit run --all-files` |
| R16 | Minor | Dockerfile is `python:3.11.9` (non-slim) | 7B uses `python:3.13.x` non-slim (latest patch tag) |
| R17 | Minor | `gunicorn.conf.py` may trip ruff `N999`/`INP001` | 5A adds `per-file-ignores` for it |
| R18 | Minor | Dummy DSN host is real; startup logs could be POSTed from CI | 1B uses `http://public@127.0.0.1:9/0` |
| R19 | Minor | `gsutil` may be missing; pointer may be `<sha>:<nonce>` | Runbook 4.5: `gcloud storage cat gs://wac-deploy-<project>/current-prod \| cut -d: -f1` |
| R20 | Minor | User model is `CDCUser` at `coderdojochi/models/user.py:8`, not `accounts/models.py` | Fixed in 0.5 |
| R21 | Minor | Line refs drifted (DEFAULT_AUTO_FIELD :360; Sentry init :344-355; ci.yml step lines) | Builders cite **step names** in `ci.yml`; settings refs corrected |
| R22 | Minor | 1A: `email(...)` call in `signals_handlers.py` runs to :46 | 1A reads :20-46 |
| R23 | Minor | `views/calendar.py:48` slices a property (`event["dtstamp"] = event["dtstart"][:-1]`), likely broken by icalendar 7 | 4A names this line; `test_calendar_view` asserts DTSTAMP parses |
| R24 | Minor | `MIMEImage(instance.avatar.read())` (`signals_handlers.py:25`) has no filename; anymail 14 Resend extension check may reject it | 4A sets an explicit filename + subtype from the avatar's extension; `test_mentor_updates` asserts it |

## Progress

(The builder writes one entry per checkpoint: date, what was done, check output, evidence, prod sha before/after.)

### Checkpoint 6 — in progress (2026-11-25)

- Started: code branch `claude/upgrade-cp6-sentry-939993` at `origin/main` `13b7089` (#1637 docs on top of CP5 `b55d652`). Prod is `b55d652`. D3 gate met: sentry-sdk 3.0.0 (2026-11-23) and 3.0.1 (2026-11-25) on PyPI; 3.0.1 is latest. Dependabot open = only #1586 (superseded).
- Built (one sub-agent, 6A): commit `6ac15c2` on local branch `claude/upgrade-cp6-sentry`. **Not pushed.** 3 files: `pyproject.toml` (`sentry-sdk>=3.0.1,<4`), `uv.lock` (only sentry-sdk 2.76.0→3.0.1; deps certifi/urllib3 unchanged), `coderdojochi/settings.py` (`import logging`; Sentry block).
- **Correction to 6A text:** 2.76 *did* create events from ERROR log records (LoggingIntegration was default, `event_level=ERROR`; `integrations/__init__.py:61`, `logging.py:26-27`), and `send_reminders.py:212` relies on it. So the block sets `LoggingIntegration(level=INFO, event_level=ERROR, breadcrumb_level=INFO)` = 2.76 behaviour exactly, not `event_level=None`.
- PII: `data_collection={"user_info": True, "stack_frame_variables": {"mode": "denylist"}}`. User id/email/username + client IP still sent. 3.0.1 removed `EventScrubber`, so without the denylist, frame locals (password, token…) would go raw. Differences vs 2.76: query params now denylist-filtered (less); log `extra`, breadcrumb data, span data no longer scrubbed (more; no 3.x option); `attach_stacktrace` default now True (bigger events, left as default).
- Other APIs used here (`new_scope`, `capture_message`, `last_event_id`, `capture_exception`) all exist in 3.0.1.
- Checks (lead re-ran): `uv lock --check` ok; `ruff check .` all passed; `ruff format --check .` 120 formatted; `Ran 111 tests … OK`; CI "Check Sentry init" reproduced (job + step env, `SENTRY_DSN=http://public@127.0.0.1:9/0`) → `manage.py check` exit 0. Agent: `pre-commit run --all-files` all Passed, no files changed. Runtime: integrations include `logging`, handlers logs INFO / events ERROR / breadcrumbs INFO.
- Mutations (agent, reverted, `cmp` identical): `enable_tracing=True` → `TypeError: Unknown option 'enable_tracing'`; old block → `TypeError: Unknown option 'enable_logs'`; `send_default_pii` alone → TypeError.
- Memory (startup only): `manage.py check` peak RSS 3.0.1 ≈128 MB vs 2.76 ≈129 MB. Runtime/span-streaming memory still needs staging + serial console.
- Runbook step 0 skipped: no Django/app package changed, so no migrations possible.
- 2026-11-25: Ali chose "Push + PR, staging when green" and to keep the 3.x `attach_stacktrace=True` default. Pushed `claude/upgrade-cp6-sentry` (`6ac15c2`), opened https://github.com/WeAllCode/website/pull/1640. CI pending. Staging release is pre-approved once CI is green **and** Ali confirms the temporary staging `SENTRY_DSN` + `SENTRY_ENVIRONMENT=staging` secret version (R8); release with `--force`. Merge and prod still need Ali's OK.
- CI on #1640 all green (tests, pre-commit, django-postgres incl. Sentry-init step, infra; dependabot skipped). Ali confirmed the staging DSN secret version is added. `release.sh --target staging --force origin/claude/upgrade-cp6-sentry` → `current-staging` = `6ac15c2…:20261126T012109Z`. Serial log 01:21:17Z deploying (was `070ee90`), `+ sentry-sdk==3.0.1`, 01:23:19Z gunicorn listening, 01:23:24Z `wac-staging is running 6ac15c2…`, 01:23:29Z `done`, no Traceback/rollback.
- Staging smoke `--cp cp6-staging --basic-auth-op … --baseline out/cp0-staging/report.json`: **PASS 0/24**, same hosts as CP0 (`/tmp/wac-smoke/out/cp6-staging/report.json`).
- **Found, pre-existing (not CP6):** `handler404` is set in `weallcode/urls.py:71`, but Django reads it only from `ROOT_URLCONF` (`coderdojochi.urls`, which just `include`s weallcode.urls). So `page_not_found_view` (the `capture_message`/`last_event_id` 404 handler) never runs, and `404.html` doesn't render `sentry_event_id` anyway (only `500.html` does). The Proof item "404 `sentry_event_id` appears" can't pass on any version. Fix = move `handler404` to `coderdojochi/urls.py` (and decide whether 404s should be Sentry error events at all); follow-up, not CP6.
- **WAC Sentry reachable from the laptop now:** `sentry-cli` 3.8.2 (brew) + Ali's personal token (`sentry-cli login -g`; org `we-all-code-p5`, project `production` id 1227311, region `us.sentry.io`; envs `production`, `staging`). Note `sentry-cli login` without `--auth-token` makes an `org:ci` org token that can't read events (401). Query: `GET /api/0/organizations/we-all-code-p5/events/?project=1227311&dataset=ourlogs|errors|spans&query=environment:staging…`.
- Staging Sentry check **passed**: Sentry Logs with `sdk.version` 3.0.1 since 01:24Z (32 in 3h vs 91 from 2.76.0 earlier): gunicorn access lines (info) and `Not Found: …` (warn) from the smoke run. Errors dataset: 0 staging events in 3h (no ERROR logged). Spans 3h: 8370 on 3.0.1 vs 8430 on 2.76.0, so span volume about the same.
- 2026-11-26: Ali chose "Merge + release prod" (memory check moves to the 0.5 visit, as in CP5). **Prod sha before: `b55d65201fd3b3406222da203c75074d80b16ec3`** (CP5; rollback: `release.sh --target prod --force b55d652`). #1640 squash-merged as `7078ef7` (on top of `5a1c0c3`, #1639: docs + `infra/terraform/storage.tf` + README only, no app code). No migrations, so no backup step.
- `release.sh --target prod 7078ef7cf4714a543baa7e25333e1bba297adcf7` (`origin/main` = that sha): serial log 01:39:05Z `+ sentry-sdk==3.0.1`, 01:40:46Z gunicorn listening, 01:40:51Z `wac-web is running 7078ef7…`, 01:40:55Z `done`, no Traceback/rollback. **Prod sha after: `7078ef7cf4714a543baa7e25333e1bba297adcf7`.** `/etc/wac/reminders-enabled` not touched.
- Prod smoke: `cp6-prod` (01:41:06Z, inside the 60 s edge TTL) PASS 0/24; `cp6-prod-r2` FAIL 1/24 (mobile `/account/signup/`, new host `csp.withgoogle.com` = the flaky reCAPTCHA CSP beacon seen in CP3); `cp6-prod-r3` **PASS 0/24**. Origin `sessionid=x` `/privacy/` 200.
- Prod Sentry (via CLI, 30 min window at ~01:45Z): Logs from `sdk.version` 3.0.1 arriving (34), spans 3.0.1 (130), **0 error events**. 1h watch: re-query at ~02:41Z.
- The plan's prod check "404 `sentry_event_id`" is n/a: the custom 404 handler never runs (see finding above).
- Still open (Ali, 0.5 visit): serial-console `systemctl show wac-web wac-staging -p MemoryCurrent,MemoryPeak` vs baseline; then remove the temporary staging DSN secret version. Also from earlier: the serial-console `systemctl show wac-staging -p MemoryCurrent,MemoryPeak` vs 0.5 baseline; then remove the temporary staging DSN.

### Checkpoint 5 — done, on prod (2026-11-25). Next: Checkpoint 6 (sentry-sdk 3, gated by D3)

- Started: code branch `claude/upgrade-cp5-gunicorn` from `origin/main` `298fa88` (#1635 scanner defense on top of CP4 `51ccada`). Dependabot open = only #1586 (superseded). gunicorn 27.0.1 still latest on PyPI (requires Python ≥ 3.10).
- Built by the lead directly (one 3-file task, no sub-agent). Commit `070ee90`: `pyproject.toml` (`gunicorn>=27.0.1,<28`; per-file-ignores `"gunicorn.conf.py" = ["INP001", "N999"]`), `uv.lock` (only gunicorn 23.0.0→27.0.1), new `gunicorn.conf.py` with `control_socket_disable = True` (setting name from `gunicorn/config.py`; CLI `--no-control-socket`). Unit files untouched.
- Proof of the socket fix: gunicorn with `HOME` = a read-only dir and no `XDG_RUNTIME_DIR`. Without the file (`--config=<empty file>`): `[ERROR] Control server error: [Errno 13] Permission denied: '<home>/.gunicorn'` (non-fatal; pages still served). With `./gunicorn.conf.py`: no error. `gunicorn coderdojochi.wsgi --check-config` rc 0.
- Checks: `uv lock --check` ok; `ruff check .` all passed; `ruff format --check .` 120 formatted; full suite `Ran 111 tests … OK`; `pre-commit run --all-files` all Passed. Runbook step 0 skipped: no Django/app package changed, so no migrations possible.
- 2026-11-25: pushed `claude/upgrade-cp5-gunicorn` (`070ee90`), opened https://github.com/WeAllCode/website/pull/1636. CI pending.
- CI on #1636 all green (pre-commit, tests, django-postgres incl. gunicorn smoke, infra; dependabot skipped).
- Staging: `release.sh --target staging origin/claude/upgrade-cp5-gunicorn` → `current-staging` = `070ee90d914ee9c446c387424c62cf4d47bf863a` (23:21Z). Serial log: 23:23:07Z `Starting gunicorn 27.0.1`, `Listening at: unix:/run/wac-staging/gunicorn.sock`, worker booted, **no `Control server error`**; 23:23:12Z `wac-staging is running 070ee90…`, 23:23:16Z `done`, no rollback/Traceback. (Serial reads need `CLOUDSDK_ACTIVE_CONFIG_NAME=wac`; the default gcloud config is the wrong account.)
- Staging smoke `--cp cp5-staging --basic-auth-op "op://homelab/WAC staging basic auth/password" --baseline out/cp0-staging/report.json`: **PASS 0/24** (`/tmp/wac-smoke/out/cp5-staging/report.json`). **Pitfall found:** a first run without `--basic-auth-op` got 24× 401, which tripped the #1635 Cloudflare rate limit, so the next run's desktop pass got 429 on all 12 pages. Waited until `/privacy/` returned 200, then reran clean. Always pass `--basic-auth-op` for staging.
- Memory check (AC5, ≤ baseline +10%) not done: the 0.5 baseline still doesn't exist, and the serial console needs Ali.
- 2026-11-25: Ali chose "Merge + release prod" (memory check still open). **Prod sha before: `298fa88d61dfd4965b18e2dbc08874a20ae4f6a9`** (#1635; rollback: `release.sh --target prod --force 298fa88`). #1636 squash-merged as `b55d652`. No migrations, so no backup step.
- `release.sh --target prod b55d65201fd3b3406222da203c75074d80b16ec3` (`origin/main` = that sha): serial log 23:33:54Z `deploying b55d652… (was '298fa88…')`, 23:35:53Z `Starting gunicorn 27.0.1`, `Listening at: unix:/run/wac-prod/gunicorn.sock`, no `Control server error`; 23:35:58Z `wac-web is running b55d652…`, 23:36:02Z `done`, no Traceback/rollback. **Prod sha after: `b55d65201fd3b3406222da203c75074d80b16ec3`.**
- Prod smoke `--cp cp5-prod --baseline out/cp0-prod/report.json` (past the 60 s edge TTL): **PASS 0/24**. Origin check `sessionid=x` `/privacy/` 200.
- Not done (Ali): memory numbers vs the 0.5 baseline (`systemctl show wac-web wac-staging -p MemoryCurrent,MemoryPeak`), Sentry 1h watch, `--auth` smoke (needs `upg-smoke`).

### Checkpoint 4 — in progress (2026-11-25)

- Started: code branch `claude/upgrade-cp4-majors` from `origin/main` `25b441c` (#1632 on top of CP3 `7deb61d`). Prod is `7deb61d`.
- Start-of-CP checks: Dependabot open = only #1586 (superseded). All 4A targets still latest on PyPI: anymail 15.3, debug-toolbar 8.0.0, icalendar 7.3.2, invoke 3.0.3, python-dateutil 4.0.0 (requires Python ≥ 3.11, OK), faker 40.63.0, pycparser 3.12. Baseline on `25b441c`: `Ran 108 tests … OK`. Greps for `fail_silently`, `UIDGenerator`, `decoded(`: no hits.
- Plan addition (before building): the calendar subclasses `get_dtstart`/`get_dtend` in `coderdojochi/views/meetings.py:90-108` and `coderdojochi/views/sessions.py:408-430` return strings; 4B may edit those methods if icalendar 7 forces it. 4A is split into 3 parallel sub-agents, each in its own venv with the target versions: 4A lock + `tasks.py` + debug-toolbar settings; 4B calendar; 4C avatar email (`signals_handlers.py`, `test_mentor_updates.py`).
- Built: one commit `2d46745` on `claude/upgrade-cp4-majors`. **Not pushed.** 6 files: `pyproject.toml`, `uv.lock`, `coderdojochi/views/calendar.py`, `coderdojochi/signals_handlers.py`, `coderdojochi/tests/test_calendar_view.py`, `coderdojochi/tests/test_mentor_updates.py`. `tasks.py`, `settings.py`, `urls.py`, `util.py`, `meetings.py`, `sessions.py` unchanged (not needed).
- 4A lock: anymail 13.0→15.3, debug-toolbar 5.2.0→8.0.0, icalendar 6.3.1→7.3.2, invoke 2.2.0→3.0.3, python-dateutil 2.9.0.post0→4.0.0, faker 37.4.2→40.63.0, pycparser 2.22→3.12, six removed. Nothing else moved (gunicorn 23.0.0, sentry-sdk 2.76.0 unchanged). dateutil 4: dependents arrow, icalendar, svix have no `<4` cap; removals (`tz.TZPATHS`, py2 helpers, stricter `isoparse`) unused; `relativedelta(years=N)` unchanged. Only visible change: times inside a DST gap follow PEP 495. invoke 3: `tasks.py` uses neither `disown` nor `make_context`. debug-toolbar 8: existing `DEBUG_TOOLBAR_CONFIG` keys still valid; `"TAG"` / `DEBUG_TOOLBAR_PATCH_SETTINGS` are ignored leftovers (optional cleanup).
- 4B calendar: `event.add("dtstamp", datetime.now(UTC))` replaces the slice. icalendar 7 did **not** break the raw-string DTSTART/DTEND or the slice; the old DTSTAMP was simply wrong (meeting: a digit cut off → unparseable; session: `Z` cut → naive). Test asserts DTSTAMP is an aware UTC datetime and DTSTART parses. Passes on 6.3.1 and 7.3.2. Mutation (old line back) → 2 failures, reverted.
- 4C avatar: `_avatar_attachment()` sets subtype + filename from the stored name (`avatar.png`, `Avatar.JPG`→`avatar.jpg`, no extension → sniffed). **Correction to R24:** under anymail 15.3 the old `filename="avatar"` does not raise (Resend's check skips names with no known extension), so the fix is hardening. **New finding (agent, from anymail 13.0 source):** 13.0's Resend backend rejects any attachment with a Content-ID ("Resend does not support inline content-id"), and `util._send` swallows it, so the avatar-approval email has likely never sent on prod; 15.x adds inline support. Not confirmed in Sentry (the Sentry MCP here is the Braven org; no hits). New test sends through the real Resend backend with `requests` mocked under `assertNoLogs(ERROR)`: passes on 15.3, fails on 13.0 with exactly that error. Mutations: `filename="avatar"` → 4 filename asserts fail; `filename="avatar.jpg"` on PNG → backend raises, test fails; reverted.
- Checks (lead, after `uv sync`): `uv lock --check` ok; `ruff check .` all passed; `ruff format --check .` 118 formatted; full suite `Ran 111 tests … OK` 7 runs in a row (4A saw one transient `test_email_util` unsubscribe-link failure while other agents were editing; not reproduced); `pre-commit run --all-files` all Passed; `invoke --list` ok.
- Runbook step 0: scratch PG 17, `migrate` at `origin/main`, branch `migrate --plan` → **"No planned migration operations."** No backup step.
- Debug toolbar: `DEBUG=True runserver` on scratch PG, `/` 200 with `djDebug` markup, `/static/debug_toolbar/css/toolbar.css` and `js/toolbar.js` 200.
- 2026-11-25: Ali chose "Push, PR, staging when green". Pushed `claude/upgrade-cp4-majors` (`2d46745`), opened https://github.com/WeAllCode/website/pull/1633. CI pending at open. Staging release is pre-approved once CI is green; merge and prod still need Ali's OK.
- CI on #1633 all green (4 passing, dependabot skipped). Ali: "if CI is green, go to staging". `release.sh --target staging origin/claude/upgrade-cp4-majors` → `current-staging` = `2d4674580eeb2e1a56b4021a2a05ec22e4dd3b07`. Serial log 22:58:49Z `wac-staging is running 2d46745…`, 22:58:53Z `done`, no rollback/Traceback.
- Staging smoke `--cp cp4-staging --baseline out/cp0-staging/report.json`: **PASS 0/24** (`/tmp/wac-smoke/out/cp4-staging/report.json`, `out/cp4-staging.log`). Live calendar: `/classes/1/calendar/` 200 `text/calendar`, `DTSTART:20150214T160000Z`, `DTSTAMP:20261125T230003Z` (generation time, UTC). `--auth` still waits on `upg-smoke` (0.5).
- 2026-11-25: Ali chose "Merge + release prod". **Prod sha before: `25b441c52ea2051d32c8c509f3f51fd0351b57b1`** (#1632; rollback: `release.sh --target prod --force 25b441c`). #1633 squash-merged as `51ccada` (on top of `7484e7c`, #1634: docs only). No migrations, so no backup step.
- `release.sh --target prod 51ccada2d43ae4986569b301fc800f02abb64429` (after confirming `origin/main` = that sha): serial log 23:00:57Z `deploying 51ccada… (was '25b441c…')`, 23:03:14Z `wac-web is running 51ccada…`, 23:03:18Z `done`, no Traceback/rollback. **Prod sha after: `51ccada2d43ae4986569b301fc800f02abb64429`.** `/etc/wac/reminders-enabled` not touched.
- Prod smoke `--cp cp4-prod` (started 23:03:36Z, under 60 s after deploy) PASS 0/24; rerun `--cp cp4-prod-r2` at 23:04:14Z (past the edge-cache TTL) **PASS 0/24**. Origin check with `sessionid=x`: `/classes/1/calendar/` 200, `DTSTAMP:20261125T230409Z` (new code live).
- Not done: prod Resend check (password reset to Ali's address arrives and shows in Resend; serial-console `coderdojochi.util.email()` check), ideally one mentor avatar change to confirm the approval email now sends. Sentry 1h watch, `--auth` smoke wait on 0.5.
- 2026-11-25 ~23:15Z, Ali asked the lead to do it via Claude in Chrome: prod `/account/password/reset/` for `ali@weallcode.org` → `/account/password/reset/done/`. Resend Emails list: `ali@weallcode.org` **Delivered** "[weallcode.org] Password Reset E-mail", just now. **Prod Resend check passed on anymail 15.3.** Avatar-change test: Ali chose to skip. (Resend's 15-day list shows no avatar-approval email, consistent with the 13.0 inline-cid failure but not proof.) Serial-console `util.email()` check not run (password reset covers the same path).
- **CP4 done, on prod.** Next: Checkpoint 5 (gunicorn 27).
- Follow-ups (not in CP4): drop ignored `DEBUG_TOOLBAR_CONFIG["TAG"]` / `DEBUG_TOOLBAR_PATCH_SETTINGS`; check WAC Sentry for past "Resend does not support inline content-id" errors. Prod-only checks after release: password reset to Ali's address arrives + shows in Resend; serial-console `coderdojochi.util.email()` check; ideally one avatar change to confirm the approval email now arrives.

### Checkpoint 3 — in progress (2026-11-25)

- Plan branch rebased onto `origin/main` `9ce8c61` (#1628, Cloudflare page cache: `coderdojochi/middleware.py`, `settings.py` +6, `test_cache_headers.py`; no file CP3 owns). Prod is still `dc113b0` per CP2.
- Start-of-CP checks: Dependabot open = only #1586 (superseded). Every 3A target is still the latest on PyPI (django 5.2.19 is the latest 5.2.x; 6.1.3 gated by D1). Baseline on `9ce8c61`: `Ran 93 tests … OK` (django 5.2.17, import-export 4.3.9).
- Added 3B (both import resources use the dead `import_obj` hook) and 3C (RET503; corrected: no live 500 for role-less users, see 3C) to the plan before building.
- Built: branch `claude/upgrade-cp3-python-bumps` from `origin/main` `9ce8c61`, one commit `c891051`. **Not pushed.** 7 files: `pyproject.toml`, `uv.lock`, `coderdojochi/admin.py`, new `coderdojochi/tests/test_admin_import.py`, `accounts/views.py`, `accounts/tests.py`, `coderdojochi/views/profile.py`.
- 3A: all 13 floors raised; lock: django 5.2.19, allauth 65.22.1, psycopg(+binary) 3.3.9, dj-database-url 3.1.2, loginas 0.3.14, bootstrap3 26.3, active-link 0.3.0, meta 2.5.1, arrow 1.4.0, appconf 1.2.0, import-export 4.4.6, environ 0.14.0 (pillow already 13.0.0, floor only). Transitive: anyio, asgiref 3.13, certifi, cffi 2.1.1, cfgv, charset-normalizer, cryptography 50.0.2, filelock, identify, idna, nodeenv, packaging, platformdirs, pydantic 2.14.4, pydantic-core, pyjwt, pyyaml, requests 2.34.2, sqlparse, typing-extensions, tzdata, virtualenv; **unlisted but expected:** typing-inspection 0.4.5 (with pydantic), types-python-dateutil removed (arrow 1.4 dropped it). gunicorn, sentry-sdk, anymail, debug-toolbar, icalendar, invoke, dateutil, faker, pycparser unchanged. `RET503` dropped from ruff ignore.
- 3B: both resources now `import_instance(instance, row, **kwargs)`; `GuardianImportResource.before_save_instance` saves the `User` first (skips only a no-transaction dry run, as `save_instance` does). 7 tests (create, re-import no duplicate, unknown guardian → row error, dry run persists nothing). Mutations: agent renamed each back to `import_obj` → fails; lead added an early `return` in Student `import_instance` → 4 failures; reverted. Not fixed, follow-up: `GuardianImportResource.get_or_init_instance` raises `Guardian.DoesNotExist` when a `User` with that email has no `Guardian` (row error). 4.4.2 pk check doesn't apply (no `id` column).
- 3C: `AccountHomeView.get`/`post` end with `redirect("welcome")`; `DojoMentorView.post` re-renders with bound forms (view still unrouted, untested). 2 tests (role `bogus` → 302 welcome). Mutation (drop the `get` return) → error, reverted.
- Checks (lead, after `uv sync`): `ruff check .` all passed; `ruff format --check .` 118 formatted; `Ran 102 tests … OK` (93 + 7 + 2); `pre-commit run --all-files` all Passed, tree unchanged; `uv lock --check` ok.
- Runbook step 0 (migration check): scratch PG 17, `migrate` at `origin/main` (old venv), then branch venv `migrate --plan` → **"No planned migration operations."** No backup step needed.
- Pre-existing, not new: allauth deprecation warnings for `ACCOUNT_AUTHENTICATION_METHOD`, `ACCOUNT_EMAIL_REQUIRED`, `ACCOUNT_USERNAME_REQUIRED` (`settings.py:317-319`), same 3 on main. Not fatal in `check --deploy`. Follow-up: move to `ACCOUNT_LOGIN_METHODS` / `ACCOUNT_SIGNUP_FIELDS`.
- **Gap:** allauth login/logout/password-change and the `/dj-admin/` import screen are not verified on staging; `--auth` smoke still waits on `upg-smoke` (0.5). CP3 must not be called auth-verified until then.
- Admin path checked: 4.4.6 `ImportExportMixinBase.get_resource_classes` still honours `resource_class` (deprecation warning, returns `[resource_class]`), so `StudentAdmin`/`GuardianAdmin` use the fixed resources. Follow-up: switch both to `resource_classes = [...]`.
- With Ali's OK, pushed and opened https://github.com/WeAllCode/website/pull/1629 (CP3) and https://github.com/WeAllCode/website/pull/1630 (this plan onto main, docs only, so every session reads one copy; Ali chose this). CI pending at open.
- CI on #1629 all green (4 passing, dependabot skipped). With Ali's OK ("Yes, when green"), `release.sh --target staging origin/claude/upgrade-cp3-python-bumps`: `current-staging` `b505447…` → `c891051486f1f689711562bb1c4cf77986817088`. Serial log 17:42:50Z deploying, 17:45:19Z running, 17:45:23Z `done`, no rollback/Traceback.
- Staging smoke `--cp cp3-staging --baseline out/cp0-staging/report.json`: PASS 0/24, same hosts as CP0 (`/tmp/wac-smoke/out/cp3-staging/report.json`, `out/cp3-staging.log`). `--auth` (login/logout/password change, import screen) still waits on `upg-smoke` (0.5).
- 2026-11-25: Ali said "Merge + release prod". **Prod sha before: `9ce8c61a624a724fefc0d4fe892d5969adefbf15`** (#1628, released by the edge-cache session after CP2; rollback: `release.sh --target prod --force 9ce8c61`). #1629 squash-merged as `7deb61d` (on top of `f25adbd`, #1631: Terraform/docs only). No migrations, so no backup step.
- `release.sh --target prod 7deb61de67e9195b4b13ecef7f944dfd35c39dc6`: serial log 17:47:54Z `deploying 7deb61d… (was '9ce8c61…')`, 17:50:20Z `wac-web is running 7deb61d…`, 17:50:25Z `done`, no Traceback/rollback. **Prod sha after: `7deb61de67e9195b4b13ecef7f944dfd35c39dc6`.** `/etc/wac/reminders-enabled` not touched.
- Prod smoke (17:51Z, >60 s after deploy, so past the edge-cache TTL) `--cp cp3-prod --baseline out/cp0-prod/report.json`: FAIL 1/24, mobile `/join-us/` only, one new failed request: `POST csp.withgoogle.com/csp/frame-ancestors/…` `ERR_BLOCKED_BY_ORB`, Google's reCAPTCHA CSP-report beacon, not our code. Rerun `--cp cp3-prod-r2`: **PASS 0/24**, no `csp.withgoogle.com`. Flaky third-party beacon; noted for CP9's host allowlist. Reports `/tmp/wac-smoke/out/cp3-prod{,-r2}/report.json`.
- Not done (wait on 0.5): Sentry 1h watch, `--auth` smoke on staging (login/logout/password change, import screen). Prod-only manual check from Proof: Ali logs in with Google on prod (allauth 65.22).
- **CP3 done, on prod.** Next: Checkpoint 4.
- Follow-ups (not in CP3): `GuardianImportResource.get_or_init_instance` DoesNotExist; switch admins to `resource_classes`; allauth deprecated settings (`settings.py:317-319`).

### Checkpoint 2 — done, on prod (2026-11-25). Next: Checkpoint 3

- 2026-11-25: Ali said merge + release prod. **Prod sha before: `1668ae59790c15fe088ec922ef2ff774f14364f6`** (rollback: `release.sh --target prod --force 1668ae5`). #1627 squash-merged as `dc113b0`. `release.sh --target prod dc113b049ed0fb27213ab3b9c94b5fe90f2af6c7`: serial log 15:23:38Z `deploying dc113b0… (was '1668ae5…')`, 15:25:47Z `wac-web is running dc113b0…`, 15:25:54Z `done`, no Traceback/Error. **Prod sha after: `dc113b049ed0fb27213ab3b9c94b5fe90f2af6c7`.** No migrations, so no backup step. `/etc/wac/reminders-enabled` not touched.
- Prod smoke `--cp cp2-prod --baseline out/cp0-prod/report.json`: PASS 0/24, same hosts as CP0 (`/tmp/wac-smoke/out/cp2-prod/report.json`).
- Sentry 1h watch: not done (only `braven-org` reachable); folded into the 0.5 visit with the others.
- Open: Dependabot #1586 now superseded; Ali decides whether to close it. CP3 also owns the `StudentResource.import_obj` → `import_instance` finding and the RET503 role-less-user 500 (or its own issue).

- With Ali's OK, pushed `c71fef2`. CI on that head: tests, pre-commit, django-postgres, infra all SUCCESS (dependabot skipped). `release.sh --target staging origin/claude/upgrade-cp2-tooling`: `current-staging` `7049da0…` → `c71fef2baaa83efe649a3aebe12056bba566aeb7`; serial log 14:49:38Z deploying, 14:51:41Z running, 14:51:46Z `done`, no rollback. Smoke `--cp cp2b-staging --baseline out/cp0-staging/report.json`: PASS 0/24, same hosts (`/tmp/wac-smoke/out/cp2b-staging/report.json`).

- Ali asked to replace the easy new noqa's with real fixes. Commit `c71fef2` on `claude/upgrade-cp2-tooling` (not pushed): sitemap `timezone.now()`; admin student import `date(*time.strptime(...)[:3])` (ruff 0.17 still flags `datetime.strptime(...).date()` as DTZ007); `is_registered_for_session` → `.filter(...).exists()` (2+ active orders now = registered; old code returned False). New `coderdojochi/tests/test_student.py` (7 tests). Checks: `ruff check .` ok, format ok, `Ran 79 tests … OK`, pre-commit all passed; mutation (drop `is_active=True`) fails a test, reverted. Remaining CP2 noqa: `apps.py` F401 (required), `forms.py` DJ006.
- **Found, not fixed:** `StudentResource.import_obj` (`coderdojochi/admin.py`) is never called by django-import-export 4.x (it calls `import_instance`), so the guardian lookup and birthday parse in it are dead in real admin imports. Fix belongs with CP3 (import-export 4.4) or its own issue.

- CI on #1627 all green (4 passing, dependabot skipped). With Ali's OK ("when CI is green, release to staging"), `release.sh --target staging origin/claude/upgrade-cp2-tooling`: `current-staging` `677141e…` → `7049da05d8753d8494556bee1d1182f786848d35`. Serial log: 14:03:14Z `deploying 7049da0… (was '677141e…')`, 14:05:24Z `wac-staging is running 7049da0…`, 14:05:29Z `done`, no rollback.
- Staging smoke `--cp cp2-staging --baseline out/cp0-staging/report.json`: PASS, 0/24 failing, same hosts as CP0 (`/tmp/wac-smoke/out/cp2-staging/report.json`, `out/cp2-staging.log`). `--auth` still waits on `upg-smoke` (0.5).

- With Ali's OK, pushed `claude/upgrade-cp2-tooling` and opened https://github.com/WeAllCode/website/pull/1627. CI not reported yet at open.

- Branch `claude/upgrade-cp2-tooling` from `origin/main` `1668ae5`, one commit `7049da0`. Not pushed. 19 files: `.github/workflows/{ci,pre-commit}.yml`, `.pre-commit-config.yaml`, `pyproject.toml`, `uv.lock`, `coderdojochi/{admin,apps,custom_storages,forms,mixins}.py`, `coderdojochi/models/{mentor,session,student,user}.py`, `coderdojochi/views/{profile,sessions}.py`, `weallcode/views/{common,programs,sitemap}.py`.
- Start-of-CP checks: Dependabot open = only #1586 (checkout 6→7, superseded by 2B; close after PR 2 merges). Terraform providers unchanged (google 8.12.0, cloudflare 5.29.0, tls 4.4.2, archive 2.8.1) → no Terraform work. ruff 0.17.6, pre-commit 4.7.0, pre-commit-hooks v6.0.0 still latest.
- **2C skipped:** Ali (0.2) wants Dependabot back only after the last checkpoint; `open-pull-requests-limit: 0` stays.
- 2A: ruff 0.17.6 / pre-commit 4.7.0 (lock diff: only those two). UP038 and the then-empty `extend-unsafe-fixes` removed. Hooks v6.0.0 / ruff-pre-commit v0.17.6; `check-json` excludes `.vscode/settings.json`. `apps.py` signals import has `# noqa: F401`. Ruff 0.17.6 on main = 293 findings → 0: safe `--fix` (14× UP008 `super()`, 1× SIM300), hand fixes (B008 `Student.get_age`/`is_within_age_range` default `timezone.now()` frozen at import → `None`, a real bug; B904 `from None`; S324 `md5(usedforsecurity=False)`; T201 stray `print` in 404 view removed), 4 inline noqa (BLE001, DTZ005, DTZ007, DJ006), the rest ignored globally or per-file with a reason each in `pyproject.toml`. No import removed (checked `git diff | grep '^-(import|from)'`).
- **Deviation (R12):** `ruff format .` changed 0 files ("113 files already formatted"), so there is no format-only commit and no `.git-blame-ignore-revs` follow-up for PR 3.
- 2B: pins checkout v7.0.1, setup-python v7.1.0, cache v6.1.0, setup-uv v10.4.0, setup-terraform v4.0.1 (each tag verified via `gh api`, each = latest release). No `pull_request_target`/`workflow_run`/`pip-install` anywhere. `pre-commit.yml`: `--all-files`, `inputs.extra_args` and the git-auto-commit step dropped (R15, **Ali confirms in review**), added `permissions: contents: read`.
- Checks (lead): `ruff check .` all passed; `ruff format --check .` 113 already formatted; full suite `Ran 72 tests … OK`; `pre-commit run --all-files` all 17 hooks Passed, tree unchanged after; `actionlint .github/workflows/*.yml` clean; `uv lock --check` ok.
- Found, not fixed (follow-up issue): RET503 in `accounts/views.py` `get`/`post` and `coderdojochi/views/profile.py` `post` — a role-less user gets `None` → 500.
- Not yet: push/PR/CI (Ali), staging deploy + smoke, merge, prod release. No migrations, no runtime-dep change (migration check 4.0 not needed).

### Checkpoint 1 — done, on prod (2026-11-25). Next: Checkpoint 2

- 2026-11-25: Ali said merge. #1626 squash-merged as `1668ae5`. **Prod sha before: `ee9b6d015faf6b6bfc45bb6a7586e8b3214204a8`** (rollback target: `release.sh --target prod --force ee9b6d0`). With Ali's OK, `release.sh --target prod 1668ae5`: serial log 13:29:28Z `deploying 1668ae5… (was 'ee9b6d0…')`, 13:31:42Z `wac-web is running 1668ae5…`, 13:31:49Z `done`. **Prod sha after: `1668ae59790c15fe088ec922ef2ff774f14364f6`.** `/etc/wac/reminders-enabled` not touched.
- Prod smoke `--cp cp1-prod --baseline out/cp0-prod/report.json`: PASS, 0/24 failing, same hosts as CP0 (`/tmp/wac-smoke/out/cp1-prod/report.json`, `out/cp1-prod.log`). No Traceback/Error in the serial log during the deploy.
- Sentry 1h watch: not done. The only Sentry org reachable is `braven-org`. Ali checks WAC's Sentry, or it's folded into the 0.5 console visit along with the staging delivery check.

- 2026-11-25: CI on #1626 all green (tests, django-postgres, pre-commit, infra; dependabot skipped). With Ali's OK, `release.sh --target staging origin/claude/upgrade-cp1-safety-net`: `current-staging` `4e1b015…` → `677141e7f4b5ffd4a7fd9e17703b6a28c1f888cb`. Serial log: `uv sync` installed requests 2.33.0 etc., `migrate` ran (only the existing GuardianImportResource UserWarnings), 13:21:34Z `wac-deploy[staging]: done: 677141e…`, no rollback.
- Staging smoke `--cp cp1-staging --baseline out/cp0-staging/report.json`: PASS, 0/24 failing, same hosts as CP0. Report `/tmp/wac-smoke/out/cp1-staging/report.json`, log `/tmp/wac-smoke/out/cp1-staging.log`. `--auth` still not run (needs `upg-smoke` from 0.5).
- Sentry: the Sentry MCP here is the Braven org, not WAC's, so staging Sentry wasn't checked. Ali checks WAC's Sentry by hand, or connects WAC's org.
- Remaining staging checks blocked on Ali (2026-11-25): (a) `--auth` smoke: no `upg-smoke` user and no `op://homelab/WAC staging upg-smoke` item yet (0.5). (b) Sentry delivery: the only Sentry org reachable is `braven-org`. Staging has no debug-error route, so a test event needs the serial console. In the staging release dir, run `.venv/bin/python manage.py shell -c "import sentry_sdk; sentry_sdk.capture_message('cp1-staging sentry check'); sentry_sdk.flush()"` as the staging user, then Ali confirms the event in WAC's Sentry. Exact form: `sudo wac-manage staging shell -c "from django.conf import settings; import sentry_sdk; print('dsn set:', bool(settings.SENTRY_DSN)); print('event id:', sentry_sdk.capture_message('cp1-staging sentry check')); sentry_sdk.flush(timeout=10)"`.
- Serial console is off on `wac-web` (`serial-port-enable` not set). Opening it needs Terraform `serial_console = true` plus `wac-serial-password-hash`, then a reboot (prod downtime). **Ali (2026-11-25): defer the Sentry delivery check to the 0.5 console visit.** CP1 counts as staging-verified without it, since CP1 changes neither sentry-sdk nor the Sentry settings. 0.5's console session must also run the command above. The `--auth` smoke also waits on 0.5.
- With Ali's OK, Claude pushed `claude/upgrade-cp1-safety-net` and opened https://github.com/WeAllCode/website/pull/1626. CI hadn't reported any checks yet when it was opened.

- Branch `claude/upgrade-cp1-safety-net` from `origin/main` `ee9b6d0`, one commit `677141e`. Not pushed. 13 files: `.github/dependabot.yml`, `.github/workflows/ci.yml`, `coderdojochi/{admin,factories,forms,settings}.py`, `coderdojochi/tests/test_{admin_strtobool,calendar_view,forms_widgets,mentor_updates,password_session}.py`, `pyproject.toml`, `uv.lock`.
- Process note: this session's edit tools only reach its own worktree, so CP1 was built here by switching this worktree to the CP1 branch; plan commits stay on `claude/dep-upgrades-94f27a`.
- **Added to the plan as 1E (not in the original):** fixing the pytz import exposed more drift in `test_password_session.py` (7 errors: old URL names `session_password`/`session_detail` with date/slug kwargs; now `session-password`/`session-detail` with `pk`). Also factories drift: `factory.DjangoModelFactory` → `factory.django.DjangoModelFactory`, `MentorFactory.active` → `is_active`, dropped `end_date`/`mentor_*_date` (read-only properties on `Session`). Test-only changes, no app code. One assertion only passed by accident before (checked `str(id)` but the view stores int pks); one hit a 404 because a role-less user goes to the guardian view (test now gives the user a guardian role).
- **Deviation (1C):** `invoke` stays a prod dependency: `Procfile:1` still runs `invoke release` (Heroku files not yet removed). Move it to dev when Procfile/app.json go.
- Checks (lead, after `uv sync`):
  - Full suite: `Ran 72 tests … OK` (baseline 58/2 errors; +3 strtobool, +3 calendar/widgets, +1 mentor, test_password_session's 7 now load).
  - `uv lock --check` ok; lock diff = only removals of django-common-helpers, django-fullurl, django-html5, django-nose, json-logging-py, mock, nose (no version changes, per 1C).
  - `grep -E "mock|nose|common-helpers|fullurl|json-logging|html5" pyproject.toml` → nothing.
  - `actionlint .github/workflows/ci.yml` clean. (`pre-commit.yml:35` `inputs.extra_args` error exists on main; 2B removes it.)
  - Simulated new CI step (prod env + `SENTRY_DSN=http://public@127.0.0.1:9/0`) → `manage.py check` exit 0; mutation `bogus_option=1` → `TypeError: Unknown option 'bogus_option'`, reverted.
  - Mutations done and reverted: pytz back → import error; patch target back → AttributeError; calendar summary changed → fail; `"on"` dropped → strtobool fails; `session_password` back → NoReverseMatch. (Widget mutation skipped: forms.py was another task's file.)
  - Ruff, per touched file, branch vs main: no new findings (factories 0/0, forms 11/11, admin 14/14, settings 18/18, test_mentor_updates 0/1, test_password_session 0/25, new tests 0). `ruff format --check coderdojochi/` clean.
- **Baseline fact, not caused by CP1:** `ruff check .` reports 315 errors on main and `pre-commit run --all-files` fails on main (`ruff check`, plus `check-json` on `.vscode/settings.json`, which has comments). CI doesn't run ruff. So "ruff clean / pre-commit passes" can't be a per-checkpoint bar until 2A deals with it; until then the bar is "no new findings in touched files". **Pitfall seen:** `pre-commit run --all-files` applies ruff auto-fixes; here it rewrote `coderdojochi/apps.py` (`import coderdojochi.signals_handlers` → `pass`, which would silently disconnect every signal handler) and `weallcode/views/programs.py`. Both reverted before commit. 2A must add `# noqa: F401` (or `# noqa`) on that import, and builders must check `git status` after any pre-commit run.
- Found, not fixed (for 4A): meeting `.ics` DTSTAMP is broken today (`[:-1]` on a value without `Z` → `20261125T03304`, icalendar records a parse error); session DTSTAMP loses its UTC `Z`; meeting DTSTART/DTEND are UTC values written without `Z`; `DESCRIPTION:None` / `LOCATION:None` when empty.
- Not yet: push/PR/CI (Ali), migration check 4.0 (CP1 has no migrations and no Django version change), staging deploy + Playwright (needs `upg-smoke` from 0.5 for `--auth`), prod release.

### Checkpoint 0 — done except 0.5 (2026-11-24)

0.5 is on Ali, outside this session.

- [x] Rebased plan branch onto `origin/main` = `ee9b6d0` (#1625). `git diff --stat f940d74 origin/main` outside docs touches only: `ci.yml` (+1), `cron.py` (deleted), `send_reminders.py` + test (new), `test_settings.py` (+3), `infra/vm/README.md`, `provision.sh` (+17), `wac-reminders.{service,timer}` (new), `pyproject.toml`/`uv.lock` (django-cron out). Every other cited file is unchanged, so its line refs hold.
- [x] Line refs re-checked. `settings.py` unchanged: `html5` :105, `django_nose` :109, Sentry init :344-357, `DEFAULT_AUTO_FIELD` :360, debug toolbar :370-372, `LOGGING` :386, `STATIC_URL` :280. Drifted and fixed above: `provision.sh` `HOME=/nonexistent` :215→:232, `--install-files` exit :178-184→:195-201, uv block :245→:263 (R3 row updated); `ci.yml` tests job now 5 named modules, refs by step name. `heroku-to-gcp-e2micro.md` +1 line at the end; :253 and :520 still hold.
- [x] 0.1: #1623 (`f940d74`) is an ancestor of `ee9b6d0`, which the D4 note records as released to prod. With Ali's OK, read the pointers: `current-prod` = `ee9b6d015faf6b6bfc45bb6a7586e8b3214204a8` (= `origin/main`), `current-staging` = `4e1b0158adee4f4299783436a6615a94f747c5cc`.
- [x] 0.2: open Dependabot PRs: #1586 (actions/checkout 6→7; superseded by 2B). Ali: leave it open. Ali: 2C re-enables Dependabot with the `uv` ecosystem after the last checkpoint.
- [x] 0.3 baseline (local, Python 3.11.14): `Ran 58 tests`, `FAILED (errors=2)`: `test_password_session` (`ModuleNotFoundError: No module named 'pytz'` from `factories.py:4`) and `test_new_mentor_no_avatar` (`AttributeError: … signals_handlers … does not have the attribute 'EmailMultiAlternatives'`).
- [x] 0.4 Playwright baseline (Ali OK'd read-only runs). Script `/tmp/wac-smoke/smoke.mjs` (playwright 1.65.1, node 22 via mise). Args: `--base <url> --cp <label> [--basic-auth-op <op-ref>] [--auth --auth-user <login>] [--baseline <report.json>]`. Baselines: `/tmp/wac-smoke/out/cp0-prod/report.json` (`https://www.weallcode.org`, no redirect) and `/tmp/wac-smoke/out/cp0-staging/report.json`. Each has 24 runs (12 pages × desktop 1280 / mobile 390) with 24 screenshots. Statuses on both: 22× 200, plus 2× 404 for the 404 path, which renders "Page Not Found (404) | We All Code". Prod and staging are the same apart from the host.
  - Console errors seen today: `net::ERR_CONNECTION_REFUSED` on every page. `/join-us/` and `/account/signup/` also log reCAPTCHA `requestStorageAccess: Permission denied.`. The 404 page also logs its own 404.
  - Failed requests: `static.cloudflareinsights.com/beacon.min.js`, `www.google-analytics.com/analytics.js` (the dead UA snippet) and `embed.double.giving/…`. **All three are sinkholed by the laptop's DNS (`dig` → `0.0.0.0`), not real site failures.** So the baseline is only valid from this machine, and later runs must use `--baseline`. A rerun against the staging baseline passed (0/24 failing).
  - Hosts loaded today: cdn.jsdelivr.net, cdnjs.cloudflare.com, embed.donsplus.com, embed.double.giving, fonts.googleapis.com, fonts.gstatic.com, gravatar.com (`/team/`), static.cloudflareinsights.com, storage.googleapis.com, www.google-analytics.com, www.google.com + www.gstatic.com (reCAPTCHA), and the site itself. **CP9 allowlist gap:** `embed.donsplus.com`, `embed.double.giving` (donation embed), `gravatar.com` and `static.cloudflareinsights.com` (injected by Cloudflare) are not on the CP9 allowlist. CP9 must decide on each of them before 9E's test is written.
  - `--auth` mode is not run yet. The login field is allauth `login` with `ACCOUNT_AUTHENTICATION_METHOD = "email"`, so pass `--auth-user <upg-smoke's email>`. 0.5 must give `upg-smoke` an email address.
- [ ] 0.5 serial-console baselines + `upg-smoke`: Ali does this later; he said to start CP1 meanwhile. 0.5 must be done before CP1's staging `--auth` smoke, CP5's memory check and CP7.

## Sources

- https://github.com/getsentry/sentry-python/blob/master/MIGRATION_GUIDE.md
- https://docs.sentry.io/platforms/python/migration/2.x-to-3.x
- https://gunicorn.org/news/
- https://anymail.dev/en/stable/changelog/
- https://django-debug-toolbar.readthedocs.io/en/latest/changes.html
- https://github.com/zostera/django-bootstrap3/blob/main/CHANGELOG.md
- https://icalendar.readthedocs.io/en/stable/changelog.html
- https://www.pyinvoke.org/changelog.html
- https://psycopg.org/psycopg3/docs/news.html
- https://github.com/django-import-export/django-import-export/blob/main/docs/changelog.rst
- https://codeberg.org/allauth/django-allauth/src/branch/main/ChangeLog.rst
- https://github.com/astral-sh/ruff/blob/main/CHANGELOG.md
- https://docs.djangoproject.com/en/6.0/releases/6.0/
- https://docs.djangoproject.com/en/6.1/releases/6.1/
- https://jquery.com/upgrade-guide/3.0/
- https://jquery.com/upgrade-guide/3.5/
- https://github.com/jquery/jquery/releases/tag/3.8.0
- https://github.com/twbs/bootstrap/releases/tag/v3.4.0
- https://github.com/twbs/bootstrap/releases/tag/v3.4.1
- https://github.com/FortAwesome/Font-Awesome/blob/5.15.4/UPGRADING.md
- https://github.com/foundation/foundation-sites/releases
- https://github.com/ten1seven/what-input/releases
- https://github.com/magic-akari/seamless-scroll-polyfill/blob/master/CHANGELOG.md
- https://github.com/actions/checkout/blob/main/CHANGELOG.md
- https://github.com/actions/setup-python/releases
- https://github.com/pre-commit/pre-commit-hooks/blob/main/CHANGELOG.md
- https://github.com/pre-commit/pre-commit/blob/main/CHANGELOG.md
