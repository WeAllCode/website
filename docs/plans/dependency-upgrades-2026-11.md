# Upgrade every dependency to its latest stable version

Status: **draft, waiting for Ali's approval.** Nothing in this plan has been built, pushed or deployed. Written 2026-11-24 from `main` at `f940d74`.

## Goal and done

**User story.** As the maintainer of weallcode.org, I want every dependency (Python packages, the Python runtime, front-end CDN libraries, GitHub Actions, Terraform providers and pre-commit hooks) on its latest stable version, shipped as small PRs that each go through staging before prod, so the site stays secure and supported without an outage on the 1 GB e2-micro.

**Acceptance criteria.**

1. Every package in the version table below is at its target version, or the table says why not (with Ali's sign-off on that row).
2. The upgrades land as the ordered PRs in Checkpoints 1–8; each PR is green in CI, deployed to staging, smoke-tested with Playwright, then merged and released to prod with Ali's OK.
3. CI runs the **whole** test suite (all of `coderdojochi.tests`, `accounts`, `weallcode`), not 4 named modules, and the 2 tests that fail on `main` today pass.
4. CI proves `sentry_sdk.init()` runs with a DSN set (today it never runs in CI because `SENTRY_DSN` is unset).
5. After each prod release: `/`, `/programs/`, `/team/`, `/account/login/`, `/dj-admin/login/` return 200 through Cloudflare; no new Sentry issues in the hour after; prod gunicorn stays under its 450 MB `MemoryMax`, staging under 200 MB.
6. Every prod release has a written rollback path that was checked before release (previous main sha recorded; DB backup taken when the PR adds migrations).
7. Dead dependencies are removed instead of upgraded (list in Checkpoint 1).

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
| django-cron | 0.6.0 | **remove** with `cron.py` (D4) | | 1 |

### Python (transitive majors worth knowing)

`uv lock --upgrade` inside today's bounds also pulls: python-dateutil 2.9 → **4.0**, faker 37 → **40**, pycparser 2 → **3**, asgiref 3.9 → 3.13, pydantic 2.13 → 2.14, cryptography 50.0.0 → 50.0.2, six removed. faker is only used by factory-boy in tests. All other transitive packages (google-cloud-storage 3.17.2, etc.) are already latest.

### Front-end (CDN, in templates)

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

- **Django 6.0/6.1 (D1):** Python ≥ 3.12. 6.0: `DEFAULT_AUTO_FIELD` default becomes `BigAutoField` (this repo already sets `AutoField` at `coderdojochi/settings.py:361`, so no migrations), positional args to `Model.save()` removed, email internals rewritten, `ADMINS`/`MANAGERS` as tuples deprecated. 6.1: PostgreSQL 15+ (VM and CI run 17), `first()`/`last()` stop ordering by pk after an empty `order_by()`, admin breadcrumbs markup changes, `EMAIL_*` → `MAILERS` deprecation, cache keys change once.
- **sentry-sdk 3.0:** `init()` raises `TypeError` on removed options. This repo passes two: `enable_logs` and `send_default_pii` (`coderdojochi/settings.py:344-357`). `LoggingIntegration` is no longer on by default, so the Sentry Logs from #1623 stop unless it is added explicitly (`LoggingIntegration(level=logging.INFO)`; note the renames: old `sentry_logs_level` is now `level`, old `level` is now `breadcrumb_level`, `event_level` now defaults to `None`). `send_default_pii` is replaced by `data_collection`, which collects more by default. `DjangoIntegration(transaction_style=)` removed (not used here). `last_event_id`, `capture_message`, `new_scope` still exist in 3.0.0 (checked in the wheel's `sentry_sdk/api.py`). The `sentry-sdk[django]` extra is gone (not used here). Span streaming is the only tracing mode: watch staging memory.
- **gunicorn 24–27:** Python ≥ 3.10. **25.1 creates a control socket by default** at `$XDG_RUNTIME_DIR/gunicorn.ctl` or `$HOME/.gunicorn/gunicorn.ctl`. The services run as system users with `HOME=/nonexistent` (`infra/vm/provision.sh:215`), `ProtectHome=true` and `ProtectSystem=full` (`infra/vm/wac-web.service:25-26`), so that path is not writable. Turn it off (see Checkpoint 5). 25.3/27.0 reject malformed requests more strictly (Caddy in front sends clean HTTP/1.1, so expect no effect). No sync-worker default changed.
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
- `.github/workflows/ci.yml:1-163`: the `tests` job runs 4 named modules at lines 31-39; `django-postgres` runs migrate, `makemigrations --check`, fixtures, a gunicorn curl smoke (lines 93-117) and `check --deploy`.
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
- `infra/vm/provision.sh:200-250`: apt packages (`python3.11-venv`), system users, uv installed once from PyPI into `/opt/uv` (never upgraded after first boot).
- `infra/vm/wac-web.service`, `infra/vm/wac-staging.service`: gunicorn flags, `WorkingDirectory=/srv/wac/<target>/current`, `MemoryMax`, sandboxing.
- `infra/vm/release.sh:1-60` and `infra/vm/README.md` sections "Deploy", "Management commands", "Database", "Admin access (serial console)": how releases, rollback, backups and the serial console work. There is **no SSH**; anything on the VM goes through the serial console, which Ali opens.
- `docs/plans/heroku-to-gcp-e2micro.md` Task G step 5 (line 253) and Progress entry G5 (line 520): the smoke test used for the cutover and the temporary-superuser pattern (`cp4-smoke`).

Code to copy:

- Test style: `coderdojochi/tests/test_email_util.py` (uses `override_settings`, `unittest.mock`).
- CI step style: `.github/workflows/ci.yml:119-127` ("Check production settings import").
- Systemd/infra edits: follow the comment-header style in `infra/vm/deploy-pull.sh:1-16`.

## Tasks

Each task owns its files. Within a checkpoint, tasks run in parallel unless marked. Every task's sub-agent: do not run git; report back with (1) files changed, (2) the exact commands run and their last 20 lines of output, (3) anything that didn't match the plan.

### Checkpoint 0 — Pre-flight (lead + Ali, no code)

- 0.1 #1623 (sentry-sdk 2.76.0 + Sentry Logs) is on `main` but not on prod. Ask Ali to release it to prod first (`infra/vm/release.sh --target prod`) so no upgrade PR carries untested changes. Record the prod sha.
- 0.2 `gh pr list --author app/dependabot` — note open Dependabot PRs. Ask Ali whether to close them (this plan supersedes them) and whether to switch `.github/dependabot.yml` from `pip` to the `uv` ecosystem (Checkpoint 2, task 2C). Until then, any Dependabot auto-merge between checkpoints means the next PR must rebase and regenerate `uv.lock`.
- 0.3 Baseline: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode` → expect 43 tests, 2 errors (`test_password_session` import, `test_new_mentor_no_avatar`). Record it.
- 0.4 Build the Playwright smoke script once (see "Playwright smoke" in Proof) in `/tmp/wac-smoke/`, run it against prod (public pages only) and staging to get a baseline of console errors that already exist (so later PRs only fail on new ones).
- 0.5 Ask Ali to open the serial console once and record memory baselines: `systemctl show wac-web wac-staging -p MemoryCurrent,MemoryPeak`, `free -m`, `uv --version`. Also create the temporary staging superuser `upg-smoke` for Playwright (password in 1Password at `op://homelab/WAC staging upg-smoke`): `sudo wac-manage staging shell -c "from accounts.models import CDCUser as U; ..."` (builder: check the real user model name in `accounts/models.py` first). `wac-refresh-staging-db` wipes it, so recreate after any refresh.

### Checkpoint 1 — Safety net and dead dependencies (PR 1)

**1A. Fix the two failing tests and add guard tests.** Files: `coderdojochi/factories.py`, `coderdojochi/tests/test_mentor_updates.py`, new `coderdojochi/tests/test_forms_widgets.py`, new `coderdojochi/tests/test_calendar_view.py`.
- `factories.py`: replace `from pytz import utc` with `from datetime import UTC` (Python 3.11+) and `datetime.now(UTC)`. Ruff `UP017` agrees.
- `test_mentor_updates.py:9`: patch the name the module really calls: `@mock.patch("coderdojochi.signals_handlers.email")`, then fix the assertion to match `email(...)` arguments (read `signals_handlers.py:20-40`).
- `test_forms_widgets.py`: for each form that uses a date widget (`coderdojochi/forms.py:154,271,346` — find the form classes), render the field and assert `'type="date"'` is in the HTML. Guards the django-html5 removal in 1C.
- `test_calendar_view.py`: create a session and a meeting with `coderdojochi/factories.py`, GET `reverse("session-calendar", args=[pk])` and `reverse("meeting-calendar", args=[pk])`, assert 200, `text/calendar` content type, and that `Calendar.from_ical(response.content)` parses with one `VEVENT` whose `SUMMARY` matches. Guards icalendar 7 in Checkpoint 4.
- Pitfall: these views may need a logged-in user or published objects; read `views/calendar.py` first.
- Proof: `DJANGO_SETTINGS_MODULE=coderdojochi.test_settings uv run python manage.py test coderdojochi.tests accounts weallcode` → 0 failures, 0 errors.

**1B. CI runs everything and runs Sentry init.** File: `.github/workflows/ci.yml` only.
- `tests` job: replace the 4 named modules with `coderdojochi.tests accounts weallcode`.
- `django-postgres` job: add a step after "Check production settings import", copying its style: `SENTRY_DSN: https://public@o0.ingest.sentry.io/0` + the same prod env, run `uv run python manage.py check`. A dummy DSN never sends (no network call at init). This is what will catch sentry-sdk 3's `TypeError` in Checkpoint 6.
- Proof: `actionlint .github/workflows/ci.yml` clean (`brew install actionlint` if missing); then green CI on the PR.

**1C. Remove dead dependencies.** Files: `pyproject.toml`, `uv.lock`, `coderdojochi/settings.py` (lines 105, 109 only), `coderdojochi/forms.py`, delete `coderdojochi/cron.py` (D4).
- Before removing each package, grep `.py`, templates and the `LOGGING` dict for its import/app label: `mock` (`^import mock|^from mock`), `django_nose|nose`, `common_helpers|helper`, `fullurl`, `json_logging`, `html5`, `django_cron`. Remove only those with no remaining use; report any hit.
- Remove from `pyproject.toml`: `mock`, `django-nose`, `django-common-helpers`, `django-fullurl`, `json-logging-py`, `django-html5`, `django-cron`. Remove `"html5"` and `"django_nose"` from `INSTALLED_APPS`.
- `forms.py`: replace `html5_widgets.DateInput(attrs={...})` with `forms.DateInput(attrs={..., "type": "date"})` at all three sites, keeping the other attrs; drop the `html5` import. **Pitfall:** Django's `DateInput` defaults to `type="text"`; without `"type": "date"` the browser date picker silently disappears. Also keep the value format ISO (`format="%Y-%m-%d"`) or the browser shows an empty field for existing values.
- Declare `python-dateutil>=2.9,<3` explicitly (it's imported at `forms.py:4`); Checkpoint 4 lifts the bound.
- `uv lock` (no `--upgrade`). Confirm with `git diff --stat uv.lock` that only removals happened.
- Proof: test command from 1A passes; `uv run python manage.py check`; `uv run ruff check .`.
- Parallel with 1A and 1B (no shared files). 1A's widget test passes before and after 1C by design.

### Checkpoint 2 — Tooling: ruff, pre-commit, GitHub Actions (PR 2)

Runs after Checkpoint 1 merges (the reformat touches files 1A/1C edit).

**2A. Ruff and pre-commit config.** Files: `pyproject.toml` (ruff dep + `[tool.ruff*]` + `pre-commit` dev dep), `uv.lock`, `.pre-commit-config.yaml`.
- `ruff>=0.17.6,<0.18`; `pre-commit>=4.7.0`. `uv lock --upgrade-package ruff --upgrade-package pre-commit`.
- Delete `UP038` from `ignore` and from `extend-unsafe-fixes` (rule removed in 0.13; leaving it errors).
- `.pre-commit-config.yaml`: `pre-commit-hooks` rev `v6.0.0`, `ruff-pre-commit` rev `v0.17.6`.
- Run `uv run ruff check .` and list new findings by rule. Fix real ones; for noisy new rules, add them to `ignore` with a one-line comment why. Report the list.
- Commit 1 = config + fixes. Commit 2 = only `uv run ruff format .` output. Then add commit 2's sha to a new `.git-blame-ignore-revs` (file owned by the lead, written after commit 2 exists).
- Proof: `uv run pre-commit run --all-files` passes; test command passes.

**2B. GitHub Actions.** Files: `.github/workflows/ci.yml`, `.github/workflows/pre-commit.yml`.
- Pin exact versions from the Actions table (`actions/checkout@v7.0.1`, `actions/setup-python@v7.1.0`, `actions/cache@v6.1.0`, `astral-sh/setup-uv@v10.4.0`, `hashicorp/setup-terraform@v4.0.1`, `stefanzweifel/git-auto-commit-action@v7.2.1`). Verify each tag exists: `gh api repos/<owner>/<repo>/git/ref/tags/<tag>`.
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

### Checkpoint 4 — Majors without runtime-server risk (PR 4)

**4A.** Files: `pyproject.toml`, `uv.lock`, plus code fixes these force (only in `coderdojochi/views/calendar.py`, `coderdojochi/util.py`, `coderdojochi/signals_handlers.py`, `tasks.py`, `coderdojochi/settings.py` debug-toolbar block).
- django-anymail 15.3 (`<16`), django-debug-toolbar 8.0.0 (`<9`), icalendar 7.3.2 (`<8`), invoke 3.0.3 (`<4`), python-dateutil 4.0 (`<5`, after reading its changelog for `relativedelta`), faker 40 (transitive), pycparser 3 (transitive).
- grep `fail_silently` (anymail 15.1 deprecation) and `UIDGenerator|decoded(` (icalendar 7).
- Check inline images in `signals_handlers.py`: content type matches the file extension (anymail 14 Resend check).
- Proof: tests (incl. `test_calendar_view.py` and `test_email_util.py`); `DEBUG=True uv run python manage.py runserver` locally and load `/` to see the toolbar render (dev only); `uv run invoke --list`.
- Staging can't prove Resend (console email backend). Prod post-release check: trigger a password reset to Ali's own address; confirm it arrives and appears in Resend's sent list. Also run, via serial console, the `coderdojochi.util.email()` check from the cutover plan (Task G step 5) to Ali's address.

### Checkpoint 5 — gunicorn 27 (PR 5)

**5A.** Files: `pyproject.toml`, `uv.lock`, new `gunicorn.conf.py` at the repo root.
- `gunicorn>=27.0.1,<28`; `uv lock --upgrade-package gunicorn`.
- Turn the control socket off **in a file that ships with the release**, so staging tests it: gunicorn loads `./gunicorn.conf.py` from its working directory, which is the release dir (`WorkingDirectory=/srv/wac/<target>/current`). Find the exact setting name with `uv run gunicorn --help | grep -i control` (the CLI flag is `--no-control-socket`); write it in `gunicorn.conf.py` with a comment pointing at gunicorn 25.1. Do **not** edit `infra/vm/wac-*.service`: unit changes install only from prod releases, so staging would never test them.
- Pitfall: a `gunicorn.conf.py` in cwd is also picked up by the CI smoke step (`ci.yml` "Smoke test pages under gunicorn"); that's good — it proves the file parses.
- Proof: CI gunicorn smoke; locally `uv run gunicorn coderdojochi.wsgi --check-config`; on staging, deploy succeeds (if gunicorn fails to start, deploy-pull rolls back and `journalctl -u 'wac-deploy@staging'` shows why — Ali reads it on the serial console).
- Memory: serial console `systemctl show wac-staging -p MemoryCurrent,MemoryPeak` after the Playwright pass; compare with the 0.5 baseline. Fail if > 10% higher.

### Checkpoint 6 — sentry-sdk 3 (PR 6, gated by D3)

**6A.** Files: `pyproject.toml`, `uv.lock`, `coderdojochi/settings.py` (Sentry block only, `:336-357`).
- `sentry-sdk>=3.0.1,<4` (or `>=3.0.0` if Ali waives D3).
- Rewrite init: drop `enable_logs`; add `LoggingIntegration(level=logging.INFO)` to `integrations` (keeps #1623's Sentry Logs at INFO and up; `event_level` stays default `None`, matching 2.x where logging errors were not turned into events by default — builder: confirm 2.76 behaviour and keep it the same); replace `send_default_pii=True` with the 3.x `data_collection` option set to the closest equivalent (read the 3.x docs; keep user id/email on events, as today). Keep `traces_sample_rate` as is.
- Proof: the CI step from 1B (`SENTRY_DSN` set → `manage.py check`) passes — and fails on the old settings (see Proof, mutation). On staging: set `SENTRY_DSN` is already in the staging env? (builder: check `infra/vm/env.staging.example`; if staging has no DSN, this checkpoint's runtime proof is prod-only). After prod release: Sentry shows a log entry from the release and the 404 handler still renders `sentry_event_id` (request a missing page).
- Memory: as in 5A (span streaming).

### Checkpoint 7 — Python 3.13 (two PRs, gated by D1)

The VM has no Python 3.13 package. uv ≥ 0.10.8 downloads CPython from `releases.astral.sh`, which has IPv6 (GitHub doesn't). uv verifies each download's sha256 against its built-in metadata.

**7A. PR 7a — VM can run a uv-managed Python (infra, ships to prod while the app is still on 3.11).** Files: `infra/vm/deploy-pull.sh`, `infra/vm/provision.sh`, `infra/vm/README.md`.
- `provision.sh`: upgrade uv when older than a pinned floor (`/opt/uv/bin/pip install --upgrade 'uv>=0.13.7,<0.14'`), not only when missing. Laptop is 0.13.7; lock format must match.
- `deploy-pull.sh`, before the build: read `$release_dir/.python-version` (validate `^3\.1[1-4]$`, else `die`). If `3.11` → current behaviour (`UV_PYTHON=/usr/bin/python3.11`). Otherwise run as **root** `UV_PYTHON_INSTALL_DIR=/opt/wac-python UV_CACHE_DIR=/var/cache/wac-uv-python uv python install <ver>` (downloads allowed, IPv6), `chmod -R a+rX /opt/wac-python`, then the existing `runuser` sync with `UV_PYTHON=$(UV_PYTHON_INSTALL_DIR=/opt/wac-python uv python find <ver>)` and `UV_PYTHON_DOWNLOADS=never` unchanged. The venv symlinks into `/opt/wac-python`, so never delete an installed version while a kept release uses it.
- Isolation note for the README (R10): a staging release can make root download a CPython build, but only an official one (version regex + uv's sha256 check). Ali must accept this in review.
- Proof: `shellcheck infra/vm/*.sh`; CI `infra` job; prod release of 7a is a no-op (still 3.11): deploy log shows the 3.11 path, site up.

**7B. PR 7b — app on Python 3.13 (Django stays 5.2, which supports 3.13).** Files: `.python-version`, `pyproject.toml` (`requires-python = ">=3.13,<3.14"`, ruff `target-version = "py313"`), `uv.lock`, `.pre-commit-config.yaml` (`default_language_version: python3.13`), `.github/workflows/ci.yml` + `pre-commit.yml` (`python-version: '3.13'`), `Dockerfile` (`FROM python:3.13-slim`, latest 3.13.x tag).
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

### Checkpoint 9 — Front-end CDN libraries (PR 9, independent of Python; can run any time after Checkpoint 1, gated by D2)

**9A. Public site.** File: `weallcode/templates/weallcode/_base.html`.
- jQuery 3.8.0, what-input 5.2.12, Foundation 6.9.0 (JS only; keep the local 6.5.1 CSS), Font Awesome 5.15.4 — all from cdnjs, each with `integrity="sha512-…" crossorigin="anonymous" referrerpolicy="no-referrer"`. Get hashes from `curl -s "https://api.cdnjs.com/libraries/<lib>/<version>?fields=sri" | jq '.sri["<file>"]'`.
- Remove the seamless-scroll-polyfill `<script>`. If `weallcode/static/weallcode/css/app.css` lacks `html { scroll-behavior: smooth; }`, report it (don't edit app.css; it's not this task's file — lead decides).

**9B. Dashboard.** File: `coderdojochi/templates/dashboard/_admin_base.html`.
- jQuery 1.12.4 → 3.8.0 (cdnjs + SRI), Bootstrap 3.3.7 → 3.4.1 CSS and JS (cdnjs `twitter-bootstrap/3.4.1` + SRI — **replace** the old `integrity` on `bootstrap.min.js`, or the browser blocks it), Font Awesome 4.6.3 → 4.7.0 (cdnjs + SRI). Drop the IE8 html5shiv/respond block (`oss.maxcdn.com` is dead).
- Pitfall: grep the dashboard templates and `coderdojochi/static/js/` for jQuery 3 removals (`.load(` on jQuery objects, `.size()`, `.andSelf()`, `.bind(`, `.delegate(`, `$(document).on("ready"`, `.error(`) and for Bootstrap `data-target`/`href` containing HTML, and tooltips/popovers with custom HTML. Report every hit with file:line.

**9C. Welcome page.** File: `coderdojochi/templates/welcome.html` lines 8, 79: js-datepicker 5.18.4 (same paths; add SRI from `https://data.jsdelivr.com/v1/package/npm/js-datepicker@5.18.4` or switch to jsdelivr).

- 9A, 9B, 9C in parallel.
- Proof: Playwright on staging with **zero new console errors** vs the 0.4 baseline and no failed requests (an SRI mismatch shows as a blocked script). Pages: public list + `/admin/` (cdc-admin dashboard, needs staff) + `/welcome/` (needs a logged-in user without a role; use `upg-smoke` or a second temp user) + open a Foundation menu/off-canvas on mobile viewport + open a Bootstrap dropdown on the dashboard + open the datepicker on `/welcome/`.

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
| 9 | Front-end CDN libraries | Playwright zero new console errors | jQuery/Bootstrap CVEs fixed |

## How to run it

Read the whole plan first. Run it as the lead: you write no code.

1. At the start of each checkpoint, give every task that can run in parallel to its own sub-agent, all at once. Each brief names its task, its files and only those, the bar to meet (the task's Proof line), and the report format (files changed; commands + last 20 lines; mismatches). Tell it not to run git.
2. You alone: check the actual files (not the report), run the checkpoint's checks, commit, write the result and evidence into Progress.
3. Anything not in the plan: write it into the plan first, then build it.
4. Per PR, the release runbook (every step needing Ali waits for his explicit OK in this session — never push, merge or release on your own):
   1. Branch `claude/upgrade-cpN-<slug>` from latest `origin/main`. If `main` moved, rebase and **regenerate** `uv.lock` (`git checkout origin/main -- uv.lock && uv lock` + the same `--upgrade-package` list), never hand-merge it.
   2. Ask Ali to push and open the PR (body ends with `🤖 Generated with [Claude Code](https://claude.com/claude-code)`; commits end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`). Wait for CI green.
   3. Ask Ali to run `infra/vm/release.sh --target staging <branch>` (branch must exist on origin). If the staging DB is stale, he runs `sudo wac-refresh-staging-db` first (then recreate `upg-smoke`).
   4. Run the Playwright smoke against staging. For checkpoints with a memory check, ask Ali for the serial-console `systemctl show` numbers.
   5. Ali merges. Record the **previous prod sha** (`gsutil cat gs://wac-deploy-<project>/current-prod` or the last `release.sh` output) in Progress.
   6. If the PR adds migrations (step recorded in the PR body), Ali runs `sudo systemctl start wac-backup` on the serial console and confirms the new object in the backup bucket, and records `sudo wac-manage prod showmigrations | grep -c '\[X\]'`.
   7. Ali runs `infra/vm/release.sh --target prod`. Run the prod smoke (public pages, no login) and the checkpoint's prod-only checks; watch Sentry for an hour.
5. Rollback (any checkpoint): Ali runs `infra/vm/release.sh --target prod <previous-prod-sha>` (it's on `origin/main`, so allowed); add `--force` if that sha is in `/srv/wac/prod/failed`. If the bad release ran migrations, first reverse them on the serial console: `sudo wac-manage prod migrate <app> <previous-migration>`; if that isn't possible, restore the step-6 backup per `infra/vm/README.md` "Database". deploy-pull already auto-rolls back when gunicorn fails to start. Only 3 releases are kept on the VM; the tarballs stay in the deploy bucket, so any older sha can be re-released.
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
| 7 | `grep -E "mock|nose|common-helpers|fullurl|json-logging|html5|django-cron" pyproject.toml` → nothing | Re-add one → grep hits |

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

## Plan review findings

(Filled in by the fresh review sub-agent; see below.)

## Progress

(Empty. The builder writes one entry per checkpoint: date, what was done, check output, evidence, prod sha before/after.)

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
